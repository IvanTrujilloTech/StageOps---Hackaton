# payment_events: conclusiones y guía de uso de los CSV limpios

Origen: `data/raw/payment_events.csv` · Notebook: `notebooks/01_analisis_payment_events.ipynb` · Salidas en `data/clean/` (se regeneran ejecutando el notebook).

## 1. Resumen en una frase

El fichero está formalmente limpio (sin nulos ni duplicados de clave), pero **una fila no es un cobro**: 4.463 filas son reenvíos. Hay que elegir bien la tabla según lo que se quiera contar.

## 2. Qué CSV usar

| CSV | Una fila por | Filas | Úsalo para | No lo uses para |
|---|---|---|---|---|
| `payment_by_reservation.csv` | reserva (`reservation_id`) | 178.043 | **Unir con `reservations` y `tickets`** | auditar reenvíos |
| `payment_movements.csv` | movimiento (`provider_event_id`) | 183.089 | Sumar cobros y devoluciones | unir con tickets (ver §5) |
| `payment_events_clean.csv` | entrega (`payment_event_id`) | 187.552 | Auditar reenvíos y latencias | **cualquier suma de dinero** |

Regla práctica: **dinero → movimientos o reservas, nunca entregas.**

### Columnas

**`payment_by_reservation.csv`**: `reservation_id`, `payment_id`, `captured_eur`, `captured_at`, `capture_received_at` (primera recepción), `capture_last_received_at` (última, la del reenvío si lo hubo), `capture_n_deliveries`, `refunded_eur`, `refunded_at`, `refund_received_at`, `refund_n_deliveries`, `has_refund`, `net_eur`.

**`payment_movements.csv`**: `provider_event_id`, `payment_id`, `reservation_id`, `event_type`, `amount_eur`, `occurred_at`, `first_received_at`, `last_received_at`, `n_deliveries`, `recv_lag_s`.

**`payment_events_clean.csv`**: las 9 columnas originales + `recv_lag_s` y `is_retry`.

Fechas en ISO 8601 UTC (`2026-10-02T10:21:46Z`). Al leerlas: `pd.read_csv(..., parse_dates=[...])` y `utc=True`.

### Nulos que NO son un defecto

En `payment_by_reservation.csv`, las columnas `refunded_*` y `refund_*` son nulas cuando la reserva **no tiene devolución** (172.997 de 178.043). Es ausencia real, no falta de datos. `has_refund` lo resume.

## 3. Cifras de referencia (definidas)

| Indicador | Definición | Valor |
|---|---|---|
| Entregas | filas del CSV original | 187.552 |
| Reenvíos | entregas con `delivery_attempt` > 1 | 4.463 |
| Movimientos | `provider_event_id` distintos | 183.089 |
| Capturas / Devoluciones | movimientos por `event_type` | 178.043 / 5.046 |
| Entregas de capturas | capturas + sus reenvíos (178.043 + 4.463) | 182.506 |
| Reservas con pago | `reservation_id` distintos | 178.043 |
| Cobrado | suma de capturas sin reenvíos | 15.341.969 EUR |
| Devuelto | suma de devoluciones sin reenvíos | 435.070 EUR |
| Neto | cobrado − devuelto (dato contable, **no pérdida**) | 14.906.899 EUR |
| Cobrado inflado (error) | suma de capturas contando reenvíos | 15.727.930 EUR |

Diferencia por contar reenvíos: 385.961 EUR que no existen.

## 4. Qué se ha comprobado (todo con resultado correcto)

**Por fila:** fechas legibles; importes > 0; `event_type` ∈ {CAPTURED, REFUNDED}; `delivery_attempt` ≥ 1; `received_at` ≥ `occurred_at` y ≤ cierre de datos (2026-10-28 23:59:59 UTC); sin `payment_event_id` ni filas duplicadas; formato de IDs; sufijo `CAP`/`REF` coherente con `event_type`.

**Entre registros del fichero:**
- Los reenvíos son copias fieles (mismo importe, instante, reserva, pago y tipo). Solo cambian `payment_event_id`, `received_at` y `delivery_attempt`.
- Todos los reenvíos son de capturas. Llegan 10–180 s (mediana ~94 s) después de la primera entrega.
- Cada reserva tiene exactamente una captura y como máximo una devolución; ninguna devolución sin captura.
- Una reserva ↔ un `payment_id` (sin cruces).
- Toda devolución es del mismo pago, por el mismo importe y posterior a la captura.

**Entre las tres tablas (`assert`):** claves únicas, filas de más = reenvíos, entregas por movimiento suman el original, cobrado/devuelto/neto cuadran entre movimientos y reservas, toda reserva tiene captura y ninguna se recibe antes de producirse. Se demuestra además que unir con las entregas hace fallar la validación.

## 5. Cómo unir sin romper los recuentos

- Unir `reservations` (o `tickets`) con **`payment_by_reservation`** por `reservation_id`, con `validate='one_to_one'` / `'many_to_one'` según el lado.
- Unir con `payment_events_clean.csv` multiplica filas: 178.043 reservas pasarían a 182.506 filas.
- Para la regla de emisión («la reserva sigue vigente al **recibirse** la confirmación») comparar `capture_received_at` con `[created_at, expires_at)`. Es la primera recepción; `capture_last_received_at` es la del reenvío. Conviene comprobar si el resultado cambia según cuál se use.
- Captura bancaria (`captured_at`) y recepción por ticketing (`capture_received_at`) son momentos distintos: no intercambiarlos.

## 6. Pistas para el análisis (hipótesis, NO demostradas)

1. **Devoluciones bimodales.** Hay devoluciones a los ~9 min y otras a las horas o días (mediana ~37 h, máx. ~72 h). Las rápidas encajan con «confirmación recibida con la reserva caducada → devolver sin emitir». Las tardías podrían ser anulaciones de entradas u otra causa. Contrastar con `expires_at` y `voided_at`.
2. **Retraso largo de confirmación.** `recv_lag_s` llega hasta ~19 min (mediana ~3 min) y el bloqueo dura 10. Algunas confirmaciones pueden llegar con la reserva ya caducada. Medir cuántas, y por proveedor y periodo.
3. **Reenvío como posible disparador.** Un reenvío puede llegar después del vencimiento aunque la primera entrega llegara a tiempo. Comprobar si hay tickets emitidos en ese caso.
4. **Devoluciones sin entrega anulada** o **tickets con captura pero sin devolución tras caducidad**: candidatos a regularización. No presentarlos como pérdidas sin confirmarlos.

## 7. Lo que este fichero NO permite concluir

- Que una captura o una devolución sean *correctas*: depende de la reserva y de la entrada.
- Qué compañía o concierto está afectado: este CSV no trae `concert_id`; hay que ir por `reservation_id` → `reservations` → `concerts`.
- Si existen reservas sin pago: aquí todas las reservas tienen captura; `reservations.csv` podría tener más.
- Cualquier causa: la coincidencia de fechas con `system_changes` no prueba causalidad.

## 8. Pendiente para la integración

- [ ] Cada `reservation_id` de pagos existe en `reservations` (y cuántas reservas no tienen pago).
- [ ] `payment_id` y `reservation_id` coinciden con los de `tickets`.
- [ ] Confirmación dentro/fuera de `[created_at, expires_at)`, con primera y última recepción.
- [ ] Tickets emitidos tras captura recibida con reserva caducada.
- [ ] Devoluciones frente a la caducidad y a `voided_at`.
