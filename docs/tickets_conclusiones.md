# tickets: conclusiones, posibles problemas y cruces con el resto de tablas

Origen: `data/raw/tickets.csv` · Notebook: `notebooks/02_analisis_tickets.ipynb` · Salida: `data/clean/tickets_clean.csv` (se regenera ejecutando el notebook).

Este documento recoge lo que los datos de `tickets` muestran por sí solos y qué habrá que cruzar con las demás tablas para confirmarlo. Es el punto de partida para unir conocimiento entre tablas y documentar los problemas.

## 1. Resumen en una frase

Hay **1.195 localidades con dos entradas vigentes a la vez** (2.390 entradas), todas emitidas con la versión **4.8.0** del emisor de EntradaLink, en **CON-04** (560 localidades) y **CON-06** (635). El inicio de la anomalía en CON-04 coincide con el cambio `CHG-004` a la misma versión. Es una **coincidencia demostrada en las fechas de `tickets`**, no una causa demostrada: falta cruzar con reservas y pagos para confirmar la caducidad.

## 2. El CSV limpio

`tickets_clean.csv`: 176.562 filas · 8 columnas, sin cambios de contenido respecto al original (mismas filas, mismo orden, BOM UTF-8 conservado, fechas ISO 8601 UTC).

| Columna | Contenido | Observación |
|---|---|---|
| `ticket_id` | clave de la entrada | único, formato `TKT-NNNNNNN` |
| `reservation_id` | reserva que la origina | único (cada reserva genera como máximo una entrada) |
| `payment_id` | operación de pago que la respalda | único en este archivo |
| `concert_id` | concierto | 6 conciertos del paquete |
| `seat_id` | butaca `Snn-Rnn-Bnn` | **solo es única dentro de un concierto** |
| `issued_at` | inicio de vigencia | 2026-10-02 10:04 → 2026-10-26 17:46 UTC |
| `voided_at` | fin de vigencia | vacío en **172.997** entradas (vigentes al cierre); 3.565 anuladas |
| `issuer_version` | versión del componente emisor | `4.7.2`, `4.8.0`, `7.3.1` |

## 3. Qué se ha comprobado y está bien

- Ningún nulo fuera de `voided_at`. Ningún duplicado exacto.
- Todos los identificadores cumplen su formato y son únicos (`ticket_id`, `reservation_id`, `payment_id`).
- Ninguna anulación anterior a su emisión.
- Ninguna entrada emitida antes de `sales_open_at` de su concierto.
- Las 3.565 anulaciones son coherentes en el tiempo. Hay 120 localidades vendidas con 4.7.2 y después con 4.8.0 en CON-04: en todas la entrada 4.7.2 se anuló antes de la nueva emisión. Son **reventas legítimas**.
- **Grupo de control:** LT (CON-01, CON-03, CON-05, versión 7.3.1) y CON-02 (EL, 4.7.2) no tienen ningún caso de doble vigencia.

## 4. Anomalía principal: doble vigencia en la versión 4.8.0

| Concierto | Compañía | Localidades con 2 vigentes | Entradas implicadas | Versión |
|---|---|---|---|---|
| CON-04 | EntradaLink | 560 | 1.120 | 4.8.0 |
| CON-06 | EntradaLink | 635 | 1.270 | 4.8.0 |
| **Total** | | **1.195** | **2.390** | 100 % 4.8.0 |

Características:
- Las dos entradas de cada localidad se emiten con **1 a 233 segundos** de diferencia (mediana 85 s). No son reemisiones separadas en el tiempo.
- Solo se solapan entradas que **no** tienen anulación. Mirando intervalos completos `[issued_at, voided_at)`, el resultado es el mismo: 1.195 pares, ninguno con anulación.
- Ninguna de las 2.390 entradas afectadas tiene una anulación previa a su emisión.

### Corte de versión en CON-04

| Versión | Entradas | Vigentes | Primera emisión | Última emisión |
|---|---|---|---|---|
| 4.7.2 | 5.143 | 5.023 | 2026-10-16 10:04:27 | **2026-10-16 10:20:01** |
| 4.8.0 | 26.912 | 26.380 | **2026-10-16 10:20:02** | 2026-10-19 16:55:04 |

- `CHG-004` (EL, `ticket_issuer` 4.8.0, `reservation_validation`: `CURRENT_OWNER_AND_NOT_EXPIRED` → `PAYMENT_REFERENCE_EXISTS`) entra en vigor a las **10:20:00Z**. El corte de versión ocurre a las 10:20:01–10:20:02Z.
- No hay ninguna emisión 4.8.0 anterior al cambio.
- Las primeras duplicadas de CON-04 aparecen a las **10:33** del 16/10, después del cambio.
- En CON-06 (también EL, 4.8.0) las duplicadas empiezan el 23/10 a las 10:12Z, con la venta ya abierta. Esta compañía ya tenía la configuración nueva desde el 16/10.
- Según el diccionario, `PAYMENT_REFERENCE_EXISTS` solo comprueba que exista la referencia de pago; no exige vigencia ni propiedad de la localidad. **Es la hipótesis principal**, aún no verificada.

## 5. Posibles problemas (por verificar)

| # | Problema | Cómo se confirmaría | Estado |
|---|---|---|---|
| P1 | Entradas emitidas con reserva **caducada** cuando llega la confirmación | `issued_at` (y/o `received_at` de la confirmación) > `expires_at` de la reserva | **Pendiente**: requiere `reservations` |
| P2 | Entradas emitidas sobre una localidad **ya ocupada** por otra reserva vigente | Cruce de reservas por `concert_id + seat_id` con ventanas `[created_at, expires_at)` | **Pendiente**: requiere `reservations` |
| P3 | Entradas emitidas **sin captura** (`CAPTURED`) de su `payment_id` | Presencia de `payment_id` en `payment_events` con `event_type = CAPTURED` | **Pendiente**: requiere `payment_events` |
| P4 | Cobros **sin entrada** o con devolución (`REFUNDED`) pendiente de regularizar | Capturas sin entrada vigente y reservas caducadas con captura | **Pendiente**: requiere `payment_events` |
| P5 | Reenvíos de notificación que se cuentan como nuevos cobros | Mismo `provider_event_id` con `delivery_attempt` > 1 | **Pendiente**: requiere `payment_events` |
| P6 | Efecto de `CHG-004` en el tiempo | Comparar emisiones 4.8.0 y 4.7.2 antes y después del cambio, y con un grupo de control (LT 7.3.1) | Parcial: solo cronología de `tickets` |

## 6. Cómo se mezcla con las demás tablas

| Desde `tickets` | Hacia | Clave | Cardinalidad | Precaución |
|---|---|---|---|---|
| `reservation_id` | `reservations` | `reservation_id` | 1 : 0..1 | Una reserva puede no tener entrada (caducada o sin confirmar). Trae `expires_at`, `customer_id`, `order_id`, `unit_price_eur`. |
| `payment_id` | `payment_events` | `payment_id` | 1 : N | Una entrada tiene una captura, puede tener una devolución y reenvíos. **Unir sin filtrar multiplica filas.** Filtrar primero por `event_type` y por `provider_event_id` único. |
| `concert_id` | `concerts` | `concert_id` | N : 1 | Aporta `ticketing_company_id` (EL/LT) y `sales_open_at`. Necesario para la comparación por proveedor. |
| `concert_id` + `seat_id` | `reservations` | ambas | N : M en el tiempo | `seat_id` solo identifica una localidad dentro de su concierto. Una misma localidad tiene varias reservas en momentos distintos. |
| `issuer_version`, `issued_at` | `system_changes` | compañía + componente (`ticket_issuer`) + tiempo | N : 1 por instante | Usar la configuración vigente en `issued_at` con `merge_asof`, nunca unir por compañía a secas. Ver `docs/system_changes_conclusiones.md`. |
| `reservation_id` → `customer_id` | `customers` | `customer_id` | N : 1 | Para contar compradores distintos. `customers` no identifica a todos los acompañantes. |

Reglas de unión que conviene fijar antes de cruzar:
1. La unidad de análisis de `tickets` es **la entrada**. Cualquier cifra en euros o en compradores debe pasar por la unidad correcta (`reservation`, `order`, `customer`), no por filas de `payment_events`.
2. Cada cifra debe declarar su denominador (entradas, reservas, pedidos o compradores) para no duplicar personas ni dinero.
3. `payment_id` identifica una operación bancaria, no un pedido.

## 7. Qué falta para cerrar el análisis

1. Cruzar `tickets` con `reservations` (P1, P2) y calcular cuántas de las 2.390 entradas en conflicto tienen `issued_at` posterior a `expires_at`.
2. Cruzar con `payment_events` (P3, P4, P5) y separar cobros, devoluciones e importes a regularizar.
3. Reconstruir al menos un caso completo con identificadores: reserva → confirmación → emisión, con horas de `created_at`, `expires_at`, `occurred_at`, `received_at` e `issued_at`.
4. Definir los indicadores de alcance (localidades, entradas, reservas, pedidos, compradores, importes) con sus denominadores.
5. Confirmar o descartar la hipótesis de `PAYMENT_REFERENCE_EXISTS` comparando con los grupos correctos (LT 7.3.1 y CON-02 4.7.2).

## 8. Límites de estas conclusiones

- Las fechas coinciden con `CHG-004`, pero eso no demuestra causalidad. Hay que comprobar la caducidad real de las reservas antes de atribuir el problema al cambio.
- Los conciertos aún no se han celebrado: no hay evidencia de acceso al recinto. El alcance se limita a emisión y asignación.
- El paquete no incluye el inventario completo de butacas: no se puede afirmar que las localidades no solicitadas estén libres o no.
