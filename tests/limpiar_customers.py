# -*- coding: utf-8 -*-
"""
tests/limpiar_customers.py

Limpieza de customers.csv usando el sistema de comprobantes (estilo del script de referencia).
Lee data/raw/customers.csv, aplica validaciones y limpieza, y guarda el resultado en
data/clean/customers.clean.

Solo lectura del CSV original; el archivo limpio se escribe en data/clean/.
"""
from pathlib import Path
import pandas as pd
import re

CSV_ORIGINAL = Path("data/raw/customers.csv")
CSV_LIMPIO = Path("data/clean/customers.clean")

# ---------------------------------------------------------------------------
# Carga inicial (como el reference: dtype declarado)
# ---------------------------------------------------------------------------
df = pd.read_csv(
    CSV_ORIGINAL,
    dtype={
        "customer_id": str,
        "first_name": str,
        "last_name": str,
        "email": str,
    },
    encoding="utf-8-sig",
    keep_default_na=False,
    na_values=[""],
)

df_original = df.copy()

# ---------------------------------------------------------------------------
# Inspección inicial
# ---------------------------------------------------------------------------
def initial_inspection():
    print("------------describe------------")
    print(df.describe(include=["string"]))
    print("------------dtypes------------")
    print(df.dtypes)

# ---------------------------------------------------------------------------
# Métrica de completitud
# ---------------------------------------------------------------------------
def calcular_completitud(df_analizar, momento):
    print(f"\n--- Métrica de Completitud ({momento}) ---")
    filas_totales = len(df_analizar)
    for col in df_analizar.columns:
        valores_presentes = df_analizar[col].notna().sum()
        completitud = (valores_presentes / filas_totales) * 100
        print(f"Columna {col}: {completitud:.2f}%")

# ---------------------------------------------------------------------------
# Tabla de calidad (original vs limpio)
# ---------------------------------------------------------------------------
def calcular_tabla_calidad(df_original, df_limpio):
    tot_orig = len(df_original)
    comp_orig = (df_original.notna().sum().sum() / (tot_orig * len(df_original.columns))) * 100
    dupl_orig = int(df_original["customer_id"].duplicated().sum())
    unic_orig = ((tot_orig - dupl_orig) / tot_orig) * 100

    tot_limp = len(df_limpio)
    comp_limp = (df_limpio.notna().sum().sum() / (tot_limp * len(df_limpio.columns))) * 100
    dupl_limp = int(df_limpio["customer_id"].duplicated().sum())
    unic_limp = ((tot_limp - dupl_limp) / tot_limp) * 100

    print("\n" + "=" * 62)
    print(f"{'Dimensión':<20} | {'Dataset original':<18} | {'Dataset limpio':<18}")
    print("=" * 62)
    print(f"{'Completitud':<20} | {comp_orig:>16.1f}% | {comp_limp:>16.1f}%")
    print(f"{'Unicidad customer_id':<20} | {unic_orig:>16.1f}% | {unic_limp:>16.1f}%")
    print("=" * 62)

# ---------------------------------------------------------------------------
# Limpieza paso a paso con comprobantes
# ---------------------------------------------------------------------------
def limpiar_variables():
    comprobante = 0
    print("\n--- Limpieza: variables de customers.csv ---")

    # 1. customer_id: verificar formato CLI-<números> y blindar como string
    print("\n[Paso 1] customer_id")
    cid = df["customer_id"].astype(str).str.strip()
    es_valido = cid.str.match(r"^CLI-\d+$", na=False)
    ids_limpios = cid.where(es_valido, pd.NA)

    if pd.api.types.is_object_dtype(ids_limpios) or pd.api.types.is_string_dtype(ids_limpios):
        print("  customer_id verificado como texto limpio")
        comprobante = 1
    else:
        print("  Error: customer_id no se ha podido verificar")
        comprobante = 0

    if comprobante == 1:
        df["customer_id"] = ids_limpios.astype("string")
        if pd.api.types.is_string_dtype(df["customer_id"]):
            print("  customer_id validado y guardado como String con éxito")
            comprobante = 2
        else:
            print("  Error: Falló la asignación de tipo string a customer_id.")
            comprobante = 0
    else:
        print("  Error: customer_id no pudo ser blindado como String")
        comprobante = 0

    # 2. Duplicados de customer_id -> NaN
    if comprobante == 2:
        condicion_duplicado = df["customer_id"].duplicated(keep="first") & (df["customer_id"] != "<NA>")
        df.loc[condicion_duplicado, "customer_id"] = pd.NA
        quedan_dup = int((df["customer_id"].duplicated(keep="first") & (df["customer_id"] != "<NA>")).sum())
        if quedan_dup == 0:
            print("  customer_id duplicados convertidos a NA con éxito")
            comprobante = 3
        else:
            print("  Error: Aún quedan IDs duplicados en el dataset.")
            comprobante = 0
    else:
        print("  Error: No se pudo proceder con el filtrado de duplicados.")
        comprobante = 0

    # 3. first_name y last_name: rellenar, limpiar, validar
    if comprobante == 3:
        print("\n[Paso 3] first_name y last_name")
        for col in ["first_name", "last_name"]:
            df[col] = df[col].fillna("N/A")
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].str.replace(r"\s+", " ", regex=True)
            df[col] = df[col].str.replace(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s'\-\.]+", "", regex=True)
            df.loc[df[col] == "", col] = "N/A"
            df[col] = df[col].str.title()
            df[col] = df[col].astype("string")

            if df[col].isna().sum() == 0 and pd.api.types.is_string_dtype(df[col]):
                print(f"  {col} limpiado, rellenado y guardado como string con éxito")
            else:
                print(f"  Error: {col} contiene nulos o tipo incorrecto.")
                comprobante = 0
                break
        if comprobante == 3:
            comprobante = 4
    else:
        print("  Error: No se pudo proceder con la limpieza de nombres.")
        comprobante = 0

    # 4. email: verificar, limpiar, dominio example.com
    if comprobante == 4:
        print("\n[Paso 4] email")
        email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        df["email"] = df["email"].fillna("N/A")
        df["email"] = df["email"].astype(str).str.strip()
        df["email"] = df["email"].str.replace(r"\s+", " ", regex=True)

        valido_fmt = df["email"].str.match(email_re, na=False)
        df.loc[~valido_fmt, "email"] = pd.NA
        n_fmt_invalido = int(df["email"].isna().sum())
        print(f"  Emails con formato inválido convertidos a NA: {n_fmt_invalido}")

        # Dominio example.com
        dominio_email = df["email"].str.split("@").str[1].str.lower()
        es_example = dominio_email == "example.com"
        df.loc[~es_example, "email"] = pd.NA
        n_dom_invalido = int(df["email"].isna().sum()) - n_fmt_invalido
        print(f"  Emails con dominio != @example.com convertidos a NA: {n_dom_invalido}")

        if df["email"].isna().sum() == 0 and pd.api.types.is_string_dtype(df["email"]):
            print("  email validado y guardado como string con éxito")
            comprobante = 5
        else:
            print("  Error: email contiene nulos o tipo incorrecto.")
            comprobante = 0
    else:
        print("  Error: No se pudo proceder con la limpieza de email.")
        comprobante = 0

    # 5. Eliminar filas con customer_id NA (clave primaria rota)
    if comprobante == 5:
        print("\n[Paso 5] Filas con customer_id NA")
        filas_na = df[df["customer_id"].isna()]
        print(f"  Filas con customer_id NA: {len(filas_na)}")
        df.drop(filas_na.index, inplace=True)
        if df["customer_id"].isna().sum() == 0:
            print("  Filas con customer_id NA eliminadas con éxito")
            comprobante = 6
        else:
            print("  Error: No se pudieron borrar las filas con customer_id NA.")
            comprobante = 0
    else:
        print("  Error: No se pudo acceder a las filas con customer_id NA.")
        comprobante = 0

    # 6. Eliminar filas con email NA
    if comprobante == 6:
        print("\n[Paso 6] Filas con email NA")
        filas_na = df[df["email"].isna()]
        print(f"  Filas con email NA: {len(filas_na)}")
        df.drop(filas_na.index, inplace=True)
        if df["email"].isna().sum() == 0:
            print("  Filas con email NA eliminadas con éxito")
            comprobante = 7
        else:
            print("  Error: No se pudieron borrar las filas con email NA.")
            comprobante = 0
    else:
        print("  Error: No se pudo acceder a las filas con email NA.")
        comprobante = 0

    # 7. Verificar unicidad final de customer_id y email
    if comprobante == 7:
        print("\n[Paso 7] Verificación final de unicidad")
        n_dup_id = int(df["customer_id"].duplicated().sum())
        n_dup_email = int(df["email"].duplicated().sum())
        print(f"  customer_id duplicados restantes: {n_dup_id}")
        print(f"  email duplicados restantes: {n_dup_email}")
        if n_dup_id == 0 and n_dup_email == 0:
            print("  Unicidad verificada: customer_id y email sin duplicados")
            comprobante = 8
        else:
            print("  Error: Quedan duplicados tras la limpieza.")
            comprobante = 0
    else:
        print("  Error: No se pudo proceder con la verificación final.")
        comprobante = 0

    return comprobante

# ---------------------------------------------------------------------------
# Ejecución en secuencia
# ---------------------------------------------------------------------------
df_original_sucio = df.copy()
calcular_completitud(df_original_sucio, "Antes de la limpieza")

initial_inspection()

comprobante_final = limpiar_variables()

df_limpio = df.copy()

calcular_completitud(df_limpio, "Después de la limpieza")
calcular_tabla_calidad(df_original_sucio, df_limpio)

# Guardar CSV limpio
CSV_LIMPIO.parent.mkdir(parents=True, exist_ok=True)
df_limpio.to_csv(CSV_LIMPIO, index=False, encoding="utf-8-sig")
print(f"\nArchivo guardado: {CSV_LIMPIO.resolve()}")

print("\n--- TIPOS DE DATOS EN CSV LIMPIO AL VOLVER A CARGAR ---")
df_desde_csv = pd.read_csv(CSV_LIMPIO, dtype=str, encoding="utf-8-sig", keep_default_na=False, na_values=[""])
print(df_desde_csv.dtypes)

print(f"\nComprobante final: {comprobante_final}")
if comprobante_final == 8:
    print("Limpieza completada con éxito.")
else:
    print("La limpieza se detuvo antes de completarse.")

print("\nNota: el CSV original no se modificó.")
