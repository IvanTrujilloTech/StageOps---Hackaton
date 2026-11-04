# reservations.csv: Conclusiones y guía de uso del CSV limpio

Origen: `data/raw/reservations.csv` · Salidas en `data/clean/reservations_clean.csv` (versionadas en git).

## 1. Resumen en una frase

El fichero de reservas está formalmente impecable (188.788 registros íntegros, sin nulos ni duplicados), cumpliendo de forma estricta y absoluta la regla de bloqueo de 10 minutos exactos entre `created_at` y `expires_at`.

## 2. Qué se ha comprobado (Resultados de la auditoría)

* **Volumen y estructura:** 188.788 registros procesados sin valores nulos ni campos vacíos.
* **Unicidad de claves:** Cero duplicados en `reservation_id`.
* **Consistencia relacional:** Integridad cruzada confirmada con `concerts.csv`, `customers.csv` y `payment_events.csv` (sin registros huérfanos).
* **Validación temporal:** El 100% de las reservas respetan de forma milimétrica la ventana exacta de 10 minutos de expiración (`expires_at - created_at = 10 min`).

## 3. Tipado y persistencia

* Las columnas temporales (`created_at` y `expires_at`) han sido convertidas formalmente a tipo `datetime64[us, UTC]`.
* El dataset limpio se encuentra exportado, versionado e integrado en la ruta definitiva `data/clean/reservations_clean.csv`, asegurando que no se modificaron los fuentes originales.

## 4. Cifras de referencia

| Indicador | Definición | Valor |
|---|---|---|
| Total de registros | Filas del CSV original y limpio | 188.788 |
| Valores nulos | Celdas vacías en campos clave | 0 |
| Duplicados | Coincidencias en `reservation_id` | 0 |
| Desviaciones temporales | Reservas fuera de la ventana de 10 min | 0 |

## 5. Próximos pasos para la integración

- [ ] Cruzar `reservations_clean.csv` con `payment_by_reservation.csv` mediante `reservation_id` para verificar la correspondencia de pagos.
- [ ] Validar la emisión de entradas en `tickets.csv` frente a las marcas temporales de creación y expiración.