# -*- coding: utf-8 -*-
"""
test.py - Auditoría de calidad de datos de customers.csv
StageOps SO-2026-041

Arquitectura inspirada en el script de referencia (carga inicial con dtype,
inspección, métricas de completitud, validaciones paso a paso con comprobante,
y tabla de calidad final).

Solo lectura: no se modifica el CSV original.
"""
import pandas as pd
import re

CSV_PATH = "data/raw/customers.csv"

# Carga inicial con tipos declarados (como el reference)
df = pd.read_csv(
    CSV_PATH,
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
# Validaciones paso a paso (solo lectura, estilo comprobante del reference)
# ---------------------------------------------------------------------------
def validar_customer_id():
    comprobante = 0
    print("\n--- Validación: customer_id ---")

    es_numero_puro = df["customer_id"].str.match(r"^CLI-\d{5,}$", na=False)
    n_invalido = int((~es_numero_puro).sum())
    print(f"customer_id con formato inválido: {n_invalido}")
    if n_invalido == 0:
        print("customer_id verificado como texto limpio (CLI-##### / CLI-######)")
        comprobante = 1
    else:
        print("Error: customer_id tiene formatos inválidos")
        comprobante = 0

    if comprobante == 1:
        n_vacios = int((df["customer_id"] == "").sum())
        print(f"customer_id vacío: {n_vacios}")
        if n_vacios == 0:
            print("customer_id sin celdas vacías")
            comprobante = 2
        else:
            print("Error: customer_id con celdas vacías")
            comprobante = 0

    if comprobante == 2:
        n_duplicados = int(df["customer_id"].duplicated(keep="first").sum())
        print(f"customer_id duplicados: {n_duplicados}")
        if n_duplicados == 0:
            print("customer_id sin duplicados (clave primaria OK)")
            comprobante = 3
        else:
            print("Error: customer_id duplicados encontrados")
            comprobante = 0

    return comprobante, n_invalido


def validar_nombres():
    comprobante = 0
    print("\n--- Validación: first_name y last_name ---")

    n_fn_vacio = int((df["first_name"] == "").sum())
    n_ln_vacio = int((df["last_name"] == "").sum())
    print(f"first_name vacío: {n_fn_vacio}")
    print(f"last_name vacío: {n_ln_vacio}")
    if n_fn_vacio == 0 and n_ln_vacio == 0:
        print("Nombres sin celdas vacías")
        comprobante = 1
    else:
        print("Error: first_name o last_name con celdas vacías")
        comprobante = 0

    return comprobante, n_fn_vacio, n_ln_vacio


def validar_email():
    comprobante = 0
    print("\n--- Validación: email ---")

    email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    es_valido = df["email"].str.match(email_re, na=False)
    n_formato = int((~es_valido & (df["email"] != "")).sum())
    n_vacio = int((df["email"] == "").sum())
    print(f"email con formato inválido: {n_formato}")
    print(f"email vacío: {n_vacio}")
    if n_formato == 0 and n_vacio == 0:
        print("email con formato válido")
        comprobante = 1
    else:
        print("Error: email con formato inválido o vacío")
        comprobante = 0

    if comprobante == 1:
        dominio_valido = df["email"].str.split("@").str[1].str.lower().eq("example.com")
        n_dominio = int((~dominio_valido & (df["email"] != "")).sum())
        print(f"email con dominio distinto a @example.com: {n_dominio}")
        if n_dominio == 0:
            print("email con dominio @example.com correcto")
            comprobante = 2
        else:
            print("Error: email con dominio no esperado")
            comprobante = 0

    if comprobante == 2:
        n_duplicados = int(df["email"].duplicated(keep="first").sum())
        print(f"email duplicados: {n_duplicados}")
        if n_duplicados == 0:
            print("email sin duplicados")
            comprobante = 3
        else:
            print("Error: email duplicados encontrados")
            comprobante = 0

    return comprobante, n_formato, n_vacio, n_duplicados if comprobante == 3 else 0


def detectar_homonimos():
    print("\n--- Detección: homónimos (advertencia) ---")
    nombre_completo = (
        df["first_name"].str.strip().str.lower()
        + " | "
        + df["last_name"].str.strip().str.lower()
    )
    mascara = nombre_completo.duplicated(keep=False) & (df["first_name"] != "") & (df["last_name"] != "")
    n_homonimos = int(mascara.sum())
    print(f"Registros con homónimos (mismo nombre+apellido, distinto customer_id): {n_homonimos}")
    print("Nota: el anexo permite homónimos; no usar nombre+apellido como clave de unión.")
    return n_homonimos

# ---------------------------------------------------------------------------
# Tabla de calidad (sobre el original, como no hay limpieza que modifique)
# ---------------------------------------------------------------------------
def calcular_tabla_calidad(df_original):
    tot = len(df_original)
    comp = (df_original.notna().sum().sum() / (tot * len(df_original.columns))) * 100

    dupl_id = int(df_original["customer_id"].duplicated().sum())
    unic = ((tot - dupl_id) / tot) * 100

    print("\n" + "=" * 58)
    print(f"{'Dimensión':<20} | {'Dataset original':<18} | {'Estado':<12}")
    print("=" * 58)
    print(f"{'Completitud':<20} | {comp:>16.1f}% | {'OK' if comp >= 99 else 'REVISAR':<12}")
    print(f"{'Unicidad customer_id':<20} | {unic:>16.1f}% | {'OK' if unic == 100 else 'REVISAR':<12}")
    print("=" * 58)

# ---------------------------------------------------------------------------
# Ejecución en secuencia (como el reference)
# ---------------------------------------------------------------------------
calcular_completitud(df_original, "Antes de la auditoría")

initial_inspection()

c1, err_id = validar_customer_id()
c2, err_fn, err_ln = validar_nombres()
c3, err_email_fmt, err_email_vac, err_email_dup = validar_email()
n_hom = detectar_homonimos()

calcular_tabla_calidad(df_original)

# Resumen final de errores importantes
print("\n================ RESUMEN DE ERRORES IMPORTANTES ================")
resumen = [
    ("customer_id formato inválido", err_id),
    ("customer_id vacío", int((df["customer_id"] == "").sum())),
    ("customer_id duplicado", int(df["customer_id"].duplicated().sum())),
    ("first_name vacío", err_fn),
    ("last_name vacío", err_ln),
    ("email formato inválido", err_email_fmt),
    ("email vacío", err_email_vac),
    ("email dominio != @example.com", int((~df["email"].str.split("@").str[1].str.lower().eq("example.com") & (df["email"] != "")).sum())),
    ("email duplicado", err_email_dup),
    ("Homónimos (advertencia, no error)", n_hom),
]
for nombre, cantidad in resumen:
    marca = " <--- IMPORTANTE" if cantidad > 0 and "Homónimos" not in nombre else ""
    print(f"  {nombre:<45} {cantidad:>6,}{marca}")

print("\nNota: el CSV original no se modificó.")
