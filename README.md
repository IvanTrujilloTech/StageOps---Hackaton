# StageOps---Hackaton

Investigación de incidencias en la venta de entradas (SO-2026-041). Python + pandas.

## Estructura

```
├── data/
│   ├── raw/       # CSV originales: NO se modifican
│   ├── work/      # copias de trabajo
│   └── clean/     # salidas de la limpieza (versionadas; se regeneran ejecutando cada notebook)
├── notebooks/     # notebooks numerados, uno por CSV / análisis
├── src/stageops/  # código reutilizable
├── tests/  docs/  report/  outputs/  enunciado/
└── requirements.txt
```

## Convención para los notebooks

- Nombre: `notebooks/NN_analisis_<csv>.ipynb` (p. ej. `01_analisis_payment_events.ipynb`).
- Usa [01_analisis_payment_events.ipynb](notebooks/01_analisis_payment_events.ipynb) como plantilla de estilo:
  contexto → método → importaciones → inspección → tipado → validaciones → claves/cardinalidades → tablas limpias → `assert` → exportación → reflexión.
  Texto en español, un bloque markdown que explica antes de cada bloque de código y otro que concluye después.
- Entrada: `data/raw/<csv>`. Lectura con `encoding="utf-8-sig"` (los CSV traen BOM).
- Fechas en UTC: `pd.to_datetime(..., utc=True)`.
- No borrar filas sin justificarlo: marcar con una columna (p. ej. `is_retry`) y documentar la decisión de conteo en una celda markdown.
- Salida: `data/clean/<nombre>_clean.csv` con fechas en ISO 8601 UTC (`%Y-%m-%dT%H:%M:%SZ`).
- Debe ejecutarse de arriba abajo con *Restart & Run All*.

## Convención de nombres de columna

El notebook de integración (`07`) audita estas reglas al cargar las tablas y se detiene si alguna no se cumple. Las salidas nuevas de `data/clean/` deberían seguirlas desde el origen:

| Patrón | Significado | Ejemplos |
|---|---|---|
| `snake_case` en inglés | todas las columnas de las tablas de datos | `reservation_id`, `seat_id` |
| `*_id` | identificador, siempre texto | `reservation_id`, `payment_id`, `concert_id` |
| `*_at` | instante en UTC; en CSV, ISO 8601 con `T` y `Z` | `created_at`, `capture_received_at` |
| `*_eur` | importe en euros | `unit_price_eur`, `capture_amount_eur` |
| `<evento>_<campo>` | campo de un evento de pago | `capture_occurred_at`, `refund_amount_eur` |
| `is_*`, `has_*` | indicador verdadero/falso | `is_retry`, `has_refund` |
| `*_s` | segundos | `recv_lag_s` |

Diferencias conocidas entre los CSV actuales, que el notebook 07 neutraliza al cargar (sin modificar los ficheros): `reservations_clean.csv` usa fechas `2026-10-16 10:00:10+00:00` en vez de `…T…Z`; solo `customers_clean.csv` y `tickets_clean.csv` conservan el BOM; y `payment_by_reservation.csv` nombra `captured_at`/`captured_eur`/`refunded_at`/`refunded_eur`, que el notebook 07 renombra a `capture_occurred_at`/`capture_amount_eur`/`refund_occurred_at`/`refund_amount_eur`.

## Trabajo en equipo

- Una rama por persona; cada uno edita solo sus notebooks.
- Antes de commitear, limpiar las salidas del notebook (*Clear All Outputs*).

## Reparto

| CSV | Notebook | Responsable |
|---|---|---|
| payment_events | `01_analisis_payment_events.ipynb` | _(Daniel)_ |
| tickets | `02_analisis_tickets.ipynb` | |
| system_changes | `04_analisis_system_changes.ipynb` | _(Daniel)_ |
| concerts | `03_analisis_concerts.ipynb` | _(Daniel)_ |
| reservations | `05_analisis_reservations.ipynb` | |
| customers | `06_analisis_customers.ipynb` | |
| **integración** | `07_analisis_integracion.ipynb` | rama `integracion` |

El notebook de integración lee `data/clean/` y las guías de `docs/*_conclusiones.md`, y deja sus evidencias en `outputs/`.
