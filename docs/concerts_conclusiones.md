# concerts: conclusiones y guía de uso del CSV limpio

Origen: `data/raw/concerts.csv` · Notebook: `notebooks/03_analisis_concerts.ipynb` · Salida: `data/clean/concerts_clean.csv` (se regenera ejecutando el notebook).

## 1. Resumen en una frase

Catálogo de **6 conciertos**, sin nulos ni duplicados, que coincide campo a campo con la cartera del encargo. Su función en el análisis es **asignar cada operación a un proveedor** (LumaTicket o EntradaLink).

## 2. El CSV resultante

`concerts_clean.csv`: 6 filas · 18 columnas. Una fila por concierto, clave `concert_id`.

- **Originales (13), sin modificar:** `concert_id`, `artist`, `tour_name`, `venue`, `city`, `ticketing_company_id`, `ticketing_company_name`, `saleable_capacity`, `sales_open_at`, `doors_open_at`, `concert_start_at`, `timezone`, `snapshot_at`. Fechas en ISO 8601 UTC.
- **Derivadas (5):**

| Columna | Definición |
|---|---|
| `sales_open_local`, `doors_open_local`, `concert_start_local` | fecha convertida a `Europe/Madrid`, formato `YYYY-MM-DD HH:MM`. Solo para presentar; **comparar relojes siempre en UTC** |
| `days_on_sale_at_snapshot` | días entre `sales_open_at` y el cierre de datos (2026-10-28 23:59:59 UTC) |
| `days_to_concert_at_snapshot` | días entre el cierre de datos y `concert_start_at` |

## 3. La cartera

| concert_id | Artista | Ciudad | Proveedor | Aforo comercial | Apertura de ventas (UTC) | Días de venta al cierre |
|---|---|---|---|---|---|---|
| CON-01 | Nébula Norte | Valencia | LumaTicket (LT) | 32.000 | 2026-10-02 | 26,6 |
| CON-02 | Vera Sol | Sevilla | EntradaLink (EL) | 36.000 | 2026-10-03 | 25,6 |
| CON-03 | Atlas Eléctrico | Bilbao | LumaTicket (LT) | 30.000 | 2026-10-16 | 12,6 |
| CON-04 | Mar Abierto | Valencia | EntradaLink (EL) | 40.000 | 2026-10-16 | 12,6 |
| CON-05 | Luna Valdés | Madrid | LumaTicket (LT) | 42.000 | 2026-10-23 | 5,6 |
| CON-06 | Los Días Azules | A Coruña | EntradaLink (EL) | 34.000 | 2026-10-23 | 5,6 |

Todas las ventas abren a las 10:00 UTC (12:00 locales). Puertas a las 18:00 UTC y actuación a las 20:00 UTC (19:00 y 21:00 locales). Las actuaciones van del 6 de febrero al 13 de marzo de 2027, así que ninguna se ha celebrado a fecha de cierre.

## 4. Qué se ha comprobado (todo correcto)

- `concert_id` único y con formato `CON-NN`; sin valores ausentes.
- Capacidades positivas; zona horaria válida.
- Ventas < puertas < inicio en todos los conciertos; ninguna actuación celebrada y ninguna venta abierta después del cierre.
- `snapshot_at` idéntico en todas las filas y igual al cierre del encargo.
- `ticketing_company_id` ↔ `ticketing_company_name` es 1:1 (`LT` = LumaTicket, `EL` = EntradaLink); cada concierto tiene un solo proveedor.
- **Contraste con el encargo:** mismos seis conciertos y 0 diferencias en artista, recinto, ciudad y proveedor. Cada proveedor gestiona tres conciertos.

## 5. Cómo usarlo en la integración

- **Enlace al proveedor:** `reservations.concert_id` → `concerts.concert_id` da `ticketing_company_id`. Con ese campo y el tiempo se une `system_changes` (que se aplica por compañía, no por concierto).
- **Cardinalidad:** `concerts` 1:N `reservations` y 1:N `tickets`. Unir desde reservas o tickets con `validate='many_to_one'`.
- **Los pagos no traen `concert_id`:** se llega por `payment_events.reservation_id` → `reservations` → `concerts` (o mejor, vía `payment_by_reservation.csv`).
- **`saleable_capacity`** es el aforo comercial del montaje, **no** el máximo físico del estadio.
- Si se quiere comparar proveedores, agrupar por `ticketing_company_id`; si se compara por concierto, **normalizar por exposición** (ver §6).

## 6. Pistas para el análisis (no son conclusiones)

1. **Exposición desigual.** CON-01 y CON-02 llevan ~26 días en venta; CON-05 y CON-06, ~6. Un recuento absoluto de incidencias o reservas no es comparable entre conciertos sin normalizar por tiempo de venta o por volumen de reservas.
2. **Comprobación cruzada con pagos.** La primera captura de `payment_events` es del 2026-10-02 10:00:35 UTC, justo después de la apertura de CON-01 (10:00:00). Encaja con que no haya pagos anteriores a la apertura; falta confirmarlo concierto a concierto con `reservations`.

## 7. Lo que este fichero NO permite concluir

- No dice nada sobre incidencias: solo describe la cartera.
- No contiene inventario de butacas: no se puede calcular ocupación solo con este fichero.
- No aporta zona horaria distinta de `Europe/Madrid`; la conversión local asume una sola zona (el notebook lo comprueba con un `assert`).

## 8. Pendiente para la integración

- [ ] Reservas con `created_at` anterior a `sales_open_at` de su concierto (serían registros incoherentes).
- [ ] Entradas vigentes por concierto frente a `saleable_capacity`.
- [ ] Reservas, tickets o pagos con `concert_id` que no exista en este catálogo.
- [ ] Coincidencia entre `tickets.concert_id` y `reservations.concert_id` para la misma reserva.
