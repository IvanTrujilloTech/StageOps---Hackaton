# StageOps---Hackaton

Investigación de incidencias en la venta de entradas (SO-2026-041). Python + pandas.

## Estructura

```
├── concerts.csv, customers.csv, payment_events.csv,
│   reservations.csv, system_changes.csv, tickets.csv   # CSV originales: NO se modifican
├── notebooks_limpieza/    # un notebook por CSV
└── data/clean/            # salidas de los notebooks (ignorado por git, se regenera)
```

## Convención para los notebooks de limpieza

- Un notebook por CSV: `notebooks_limpieza/<nombre_del_csv>.ipynb` (p. ej. `payment_events.ipynb`).
- Usa [payment_events.ipynb](notebooks_limpieza/payment_events.ipynb) como plantilla:
  cargar → inspeccionar → tipar → validar → exportar.
- Lectura con `encoding="utf-8-sig"` (los CSV traen BOM).
- Fechas en UTC: `pd.to_datetime(..., utc=True)`.
- No borrar filas sin justificarlo: marcar con una columna (p. ej. `is_retry`) y documentar la decisión de conteo en una celda markdown.
- Exportar a `data/clean/<nombre>_clean.csv` con fechas en ISO 8601 UTC (`%Y-%m-%dT%H:%M:%SZ`).
- Debe ejecutarse de arriba abajo con *Restart & Run All*.

## Trabajo en equipo

- Cada persona edita solo su notebook, para evitar conflictos de merge.
- Antes de commitear, limpiar las salidas del notebook (*Clear All Outputs*).

## Reparto

| CSV | Notebook | Responsable |
|---|---|---|
| payment_events | `payment_events.ipynb` | _(Daniel)_ |
| reservations | `reservations.ipynb` | |
| tickets | `tickets.ipynb` | |
| system_changes | `system_changes.ipynb` | |
| concerts + customers | `concerts_customers.ipynb` | |
