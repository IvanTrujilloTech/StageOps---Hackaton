# system_changes: conclusiones y guía de uso del CSV limpio

Origen: `data/raw/system_changes.csv` · Notebook: `notebooks/04_analisis_system_changes.ipynb` · Salida: `data/clean/system_changes_clean.csv` (versionado en git; se regenera ejecutando el notebook).

## 1. Resumen en una frase

Historial de **6 cambios de configuración** (3 por compañía), sin nulos inesperados ni cadenas rotas. Hay **un único cambio de la regla de validación de reservas**: `CHG-004`, en EntradaLink. Es una pista para comparar, **no una causa demostrada**.

## 2. El CSV resultante

`system_changes_clean.csv`: 6 filas · 13 columnas, una fila por cambio, clave `change_id`, ordenado por `effective_at`.

- **Originales (9):** `change_id`, `ticketing_company_id`, `effective_at`, `component`, `version`, `setting_name`, `old_value`, `new_value`, `description`. Fechas en ISO 8601 UTC.
- **Derivadas (4):**

| Columna | Definición |
|---|---|
| `valid_from` | igual que `effective_at` (inicio **incluido**) |
| `valid_to` | `effective_at` del siguiente cambio del mismo compañía+componente+parámetro (fin **excluido**); vacío si sigue vigente al cierre |
| `is_initial` | `old_value` vacío: estado inicial documentado |
| `is_current_at_snapshot` | la configuración sigue vigente al cierre de datos |

## 3. El historial

| change_id | Compañía | Componente | Versión | Parámetro | Antes → Después | Desde (UTC) |
|---|---|---|---|---|---|---|
| CHG-001 | LT | ticket_issuer | 7.3.1 | reservation_validation | (inicial) → CURRENT_OWNER_AND_NOT_EXPIRED | 2026-09-28 06:00 |
| CHG-002 | EL | ticket_issuer | 4.7.2 | reservation_validation | (inicial) → CURRENT_OWNER_AND_NOT_EXPIRED | 2026-09-28 06:00 |
| CHG-003 | LT | web | 7.3.2 | cache_ttl_seconds | 60 → 45 | 2026-10-14 05:00 |
| **CHG-004** | **EL** | **ticket_issuer** | **4.8.0** | **reservation_validation** | **CURRENT_OWNER_AND_NOT_EXPIRED → PAYMENT_REFERENCE_EXISTS** | **2026-10-16 10:20** |
| CHG-005 | LT | payments | 7.3.1 | callback_retry_seconds | 30 → 20 | 2026-10-20 06:00 |
| CHG-006 | EL | web | 4.8.1 | cache_ttl_seconds | 60 → 45 | 2026-10-22 05:30 |

Qué significan los valores de `reservation_validation` (diccionario de datos):
- `CURRENT_OWNER_AND_NOT_EXPIRED`: exige que la reserva siga vigente y que el comprador sea el propietario actual de la localidad.
- `PAYMENT_REFERENCE_EXISTS`: solo comprueba que exista la referencia de pago.

## 4. Qué se ha comprobado (todo correcto)

`change_id` único y con formato `CHG-NNN`; fechas legibles y no posteriores al cierre; compañías existentes en `concerts.csv`; versiones con formato `X.Y.Z`; ningún cambio sin efecto (`old_value` = `new_value`); ningún par de cambios del mismo parámetro en el mismo instante; **cadena coherente**: el `old_value` de cada cambio es el `new_value` del anterior del mismo parámetro; intervalos con fin posterior al inicio y exactamente una configuración vigente por parámetro al cierre.

## 5. Particularidades de los datos

- **Nulos que no son defecto:** `old_value` vacío en `CHG-001` y `CHG-002` = estado inicial documentado. `valid_to` vacío = sigue vigente.
- **Solo `reservation_validation` tiene estado inicial fechado.** En `cache_ttl_seconds` y `callback_retry_seconds` no hay fila inicial: el primer cambio trae un `old_value` (60 y 30) sin fecha de entrada en vigor. Una consulta anterior al primer cambio de esos parámetros devolvería vacío.
- **Las versiones son por componente, no globales.** En LT, `payments` está en 7.3.1 mientras `web` está en 7.3.2. No se puede ordenar la «versión de la compañía».
- Los textos y valores se leen como `string`: mezclan números y nombres de regla.

## 6. Cómo usarlo en la integración

**Nunca unir por compañía a secas**: cada operación se multiplicaría por todos los cambios de esa compañía. La configuración se determina por **compañía, componente, parámetro y tiempo**: el último cambio con `effective_at` ≤ instante analizado.

El notebook incluye la función lista para copiar, que usa `pd.merge_asof` y devuelve **exactamente una fila por instante**, respetando `[inicio, fin)`:

```python
configuracion_vigente(df_cambios, instantes, 'ticket_issuer', 'reservation_validation')
# instantes: DataFrame con 'ticketing_company_id' e 'instante' (UTC)
# devuelve: valor_vigente, version_vigente, change_id_vigente
```

Comprobado en los bordes: un segundo antes de `CHG-004` devuelve la regla antigua; en el segundo exacto, la nueva.

- Instante a usar según la pregunta: `issued_at` del ticket para saber con qué configuración se emitió; la recepción de la confirmación (`capture_received_at`) para la regla de caducidad.
- La compañía de cada operación se obtiene vía `concerts` (`concert_id` → `ticketing_company_id`).

## 7. Pistas para el análisis (hipótesis, NO demostradas)

1. **`CHG-004` es el único cambio que toca la validación de reservas.** Que EntradaLink pase de exigir vigencia y propiedad a exigir solo referencia de pago es compatible con que se emitan entradas con la reserva caducada o ya cedida. Hay que comprobarlo en los datos, no darlo por hecho.
2. **LumaTicket es el grupo de comparación.** No cambia esa regla en todo el periodo: si aparecen en LumaTicket los mismos problemas que en EntradaLink, el cambio no los explica.
3. **Comparar antes y después** de 2026-10-16 10:20 UTC dentro de EntradaLink, y frente a LumaTicket en las mismas fechas. El cambio queda 20 minutos después de la apertura de ventas de CON-04 (2026-10-16 10:00 UTC), un detalle a vigilar: hay que separar el efecto del cambio del efecto de una apertura de ventas.
4. **Cambios de `web` y `payments`** (CHG-003, -005, -006): no tienen relación evidente con la validación de reservas; no usarlos como explicación sin evidencia.

## 8. Lo que este fichero NO permite concluir

- Que ningún cambio causa ninguna incidencia: no contiene ni una operación. «Un cambio temporalmente próximo no demuestra por sí mismo la causa de una incidencia» (diccionario de datos).
- Qué conciertos se ven afectados: cada cambio se aplica a **todos** los conciertos de la compañía.
- El estado inicial de `cache_ttl_seconds` y `callback_retry_seconds` más allá de su `old_value`.

## 9. Pendiente para la integración

- [ ] Tickets emitidos en EntradaLink antes y después de `CHG-004`, frente a LumaTicket en las mismas fechas.
- [ ] Contrastar `issuer_version` de `tickets.csv` con las versiones de `ticket_issuer` (EL: 4.7.2 y 4.8.0; LT: 7.3.1).
- [ ] Comprobar si hay incidencias en LumaTicket sin ningún cambio de configuración.
- [ ] Confirmar con ticketing qué ocurre exactamente con `PAYMENT_REFERENCE_EXISTS` (información adicional que pide el encargo).
