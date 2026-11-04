# Conclusiones - Limpieza y auditoría de customers.csv

**Proyecto:** StageOps SO-2026-041  
**Archivo auditado:** `data/raw/customers.csv`  
**Script ejecutado:** `test.py`  
**Fecha:** 2026-11-04  
**Modificaciones al CSV original:** Ninguna (solo lectura)

---

## 1. Resumen ejecutivo

El archivo `customers.csv` ha sido auditado por completo y **no presenta errores importantes**. Todos los campos críticos superaron las validaciones de formato, completitud y unicidad. El archivo está listo para ser usado como catálogo de compradores en el análisis de incidencias de StageOps.

---

## 2. Datos del archivo

| Métrica | Valor |
|---|---|
| Filas totales | 59,932 |
| Columnas | `customer_id`, `first_name`, `last_name`, `email` |
| Encodificación | UTF-8 con BOM (`utf-8-sig`) |
| Separador | Coma |

---

## 3. Resultado de validaciones

| Comprobación | Resultado | Estado |
|---|---|---|
| `customer_id` con formato válido (`CLI-#####` / `CLI-######`) | 59,932 / 59,932 | ✅ OK |
| `customer_id` vacío | 0 | ✅ OK |
| `customer_id` duplicado (clave primaria) | 0 | ✅ OK |
| `first_name` vacío | 0 | ✅ OK |
| `last_name` vacío | 0 | ✅ OK |
| `email` con formato válido | 59,932 / 59,932 | ✅ OK |
| `email` vacío | 0 | ✅ OK |
| `email` dominio `@example.com` | 59,932 / 59,932 | ✅ OK |
| `email` duplicado | 0 | ✅ OK |

---

## 4. Métricas de calidad

| Dimensión | Valor | Estado |
|---|---|---|
| Completitud (todas las columnas) | 100.0% | ✅ OK |
| Unicidad de `customer_id` | 100.0% | ✅ OK |

---

## 5. Advertencia (no es un error)

Se detectaron **41,198 registros con homónimos** (mismo `first_name` + `last_name`, distinto `customer_id`). Esto es **esperado y permitido** según el anexo técnico ("puede haber homónimos").

**Recomendación:** nunca usar `nombre + apellido` como clave de unión con otros archivos; siempre utilizar `customer_id`, que es la clave primaria única y válida.

---

## 6. Conclusión final

`customers.csv` está **limpio y validado**. No se requieren correcciones ni limpiezas adicionales. Puede integrarse directamente en el paquete de análisis de StageOps como fuente de compradores.
