# Conclusiones - Limpieza y auditoría de customers.csv

**Proyecto:** StageOps SO-2026-041  
**Archivo auditado:** `data/raw/customers.csv`  
**Script ejecutado:** `test.py`, `tests/comprobar_errores_customers.py`, `tests/limpiar_customers.py`  
**Fecha:** 2026-11-04  
**Modificaciones al CSV original:** Ninguna (solo lectura)  
**Archivo limpio generado:** `data/clean/customers_clean.csv` (idéntico al original: 0 celdas diferentes)

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
| `customer_id` con formato válido (`CLI-######`) | 59,932 / 59,932 | ✅ OK |
| `customer_id` vacío | 0 | ✅ OK |
| `customer_id` duplicado (clave primaria) | 0 | ✅ OK |
| `customer_id` longitud de sufijo consistente | 6 dígitos en todas las filas | ✅ OK |
| `customer_id` secuencia incremental sin gaps | ⚠️ 40.068 entradas faltantes (rango 1-100.000, 59.932 presentes) | ⚠️ Propiedad del identificador, no error |
| `first_name` vacío | 0 | ✅ OK |
| `last_name` vacío | 0 | ✅ OK |
| `email` con formato válido | 59,932 / 59,932 | ✅ OK |
| `email` vacío | 0 | ✅ OK |
| `email` dominio `@example.com` | 59,932 / 59,932 | ✅ OK |
| `email` duplicado | 0 | ✅ OK |

### Hallazgo adicional: gaps en `customer_id`
Los identificadores van de `CLI-000001` a `CLI-100000` (100.000 valores esperados), pero solo están presentes 59.932. Faltan 40.068 números intermedios (primeros ausentes: 3, 4, 5, 6, 7, 8, 11, 18, 19, 20...). Esto **no invalida la clave primaria** (no hay duplicados ni vacíos), pero confirma que `customer_id` no es un incremental continuo sin huecos. Es una propiedad del fichero fuente, no un error que deba corregirse.

---

## 4. Métricas de calidad

| Dimensión | Valor | Estado |
|---|---|---|
| Completitud (todas las columnas) | 100.0% | ✅ OK |
| Unicidad de `customer_id` | 100.0% | ✅ OK |

---

## 5. Advertencia (no es un error)

Se detectaron **41,198 registros con homónimos** (mismo `first_name` + `last_name`, distinto `customer_id`), repartidos en **16.730 grupos** de mismo nombre+apellido. Esto es **esperado y permitido** según el anexo técnico ("puede haber homónimos").

**Recomendación:** nunca usar `nombre + apellido` como clave de unión con otros archivos; siempre utilizar `customer_id`, que es la clave primaria única y válida.

---

## 6. Scripts y notebooks asociados

| Archivo | Propósito |
|---|---|
| `tests/comprobar_errores_customers.py` | Auditoría exhaustiva con sistema de comprobantes (formato, vacío, duplicados, gaps, homónimos, email) |
| `tests/limpiar_customers.py` | Limpieza con sistema de comprobantes (comprobante final 8: completado con éxito) |
| `notebooks/05_analisis_customers.ipynb` | Notebook completo con todo el análisis documentado, siguiendo el estilo de los demás notebooks del proyecto |
| `data/clean/customers_clean.csv` | Archivo limpio (idéntico al original: 0 celdas diferentes, 59.932 filas, 4 columnas) |

---

## 7. Conclusión final

`customers.csv` está **limpio y validado**. No se requieren correcciones ni limpiezas adicionales: el archivo limpio `customers_clean.csv` es idéntico al original (0 celdas diferentes), ya que no hubo errores que corregir. Puede integrarse directamente en el paquete de análisis de StageOps como fuente de compradores.

Única nota para la integración: `customer_id` tiene gaps en su secuencia incremental (no es continuo), por lo que no debe suponerse que existe una fila para cada número entre 1 y 100.000.
