# -*- coding: utf-8 -*-
"""
tests/comprobar_errores_customers.py

Auditoría de calidad de datos de customers.csv usando el sistema de comprobantes.
Solo lectura: no modifica el CSV original.

Arquitectura inspirada en el script de referencia:
  - Carga inicial con dtype declarado.
  - Inspección inicial (describe / dtypes).
  - Métrica de completitud antes de la auditoría.
  - Validaciones paso a paso con variable 'comprobante' que avanza solo si pasa.
  - Tabla de calidad final (original vs estado auditado).
"""
from pathlib import Path
import pandas as pd
import re

CSV_PATH = Path("data/raw/customers.csv")

# ---------------------------------------------------------------------------
# Carga inicial (solo lectura)
# ---------------------------------------------------------------------------
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
total_filas = len(df)
columnas = list(df.columns)

print(f"Archivo: {CSV_PATH.resolve()}")
print(f"Filas totales: {total_filas:,}")
print(f"Columnas: {columnas}\n")

errores = []
advertencias = []

def registrar(tipo, mensaje):
    if tipo == "error":
        errores.append(mensaje)
        print(f"[ERROR] {mensaje}")
    else:
        advertencias.append(mensaje)
        print(f"[AVISO] {mensaje}")

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
# Validaciones con sistema de comprobantes
# ---------------------------------------------------------------------------
def validar_customer_id():
    comprobante = 0
    print("\n--- Validación: customer_id ---")

    cid = df["customer_id"].astype(str).str.strip()

    # 1. Vacíos
    n_vacios = int((cid == "").sum())
    if n_vacios > 0:
        registrar("error", f"customer_id vacío: {n_vacios} filas")
    else:
        print("  customer_id sin celdas vacías: OK")
        comprobante = 1

    # 2. Formato consistente CLI-<números>
    if comprobante == 1:
        patron = cid.str.extract(r"^CLI-(\d+)$")[0]
        valido_formato = patron.notna()
        n_formato_invalido = int((~valido_formato).sum())
        if n_formato_invalido > 0:
            filas_invalidas = df.loc[~valido_formato, "customer_id"].head(10).tolist()
            registrar("error", f"customer_id con formato inválido (no es CLI-<números>): {n_formato_invalido} filas. Ejemplos: {filas_invalidas}")
        else:
            print("  customer_id con formato CLI-<números>: OK")
            comprobante = 2

    # 3. Longitud de sufijo consistente
    if comprobante == 2:
        longitudes = patron[valido_formato].str.len()
        long_unica = longitudes.unique()
        if len(long_unica) > 1:
            contador_long = longitudes.value_counts().to_dict()
            registrar("error", f"customer_id con longitudes de sufijo inconsistentes: {contador_long}")
        else:
            print(f"  Longitud de sufijo numérico consistente: {long_unica[0]} dígitos: OK")
            comprobante = 3

    # 4. Sin duplicados (clave primaria)
    if comprobante == 3:
        n_dup = int(cid.duplicated(keep=False).sum())
        if n_dup > 0:
            registrar("error", f"customer_id duplicado: {n_dup} filas")
        else:
            print("  customer_id sin duplicados (clave primaria): OK")
            comprobante = 4

    # 5. Secuencia incremental y gaps
    if comprobante == 4:
        numeros = patron.astype(int)
        min_n = int(numeros.min())
        max_n = int(numeros.max())
        esperado = set(range(min_n, max_n + 1))
        presentes = set(numeros.tolist())
        faltantes = sorted(esperado - presentes)
        print(f"  Rango incremental: {min_n} a {max_n} (esperados: {max_n - min_n + 1:,}, presentes: {len(presentes):,})")
        if faltantes:
            registrar("error", f"Gaps en secuencia incremental customer_id: {len(faltantes)} entradas faltantes. Primeros 10: {faltantes[:10]}")
        else:
            print("  Secuencia incremental sin gaps: OK")
            comprobante = 5

    return comprobante, len(errores), len(advertencias)


def validar_nombres():
    comprobante = 0
    print("\n--- Validación: first_name y last_name ---")

    for col in ["first_name", "last_name"]:
        s = df[col].astype(str).str.strip()
        n_vac = int((s == "").sum())
        if n_vac > 0:
            registrar("error", f"{col} vacío: {n_vac} filas")
        else:
            print(f"  {col} sin celdas vacías: OK")

    if comprobante == 0:
        comprobante = 1

    # caracteres inusuales
    for col in ["first_name", "last_name"]:
        s = df[col].astype(str).str.strip()
        mascara_rara = ~s.str.match(r"^[\wáéíóúÁÉÍÓÚñÑ\s'\-\.]+$", na=False)
        n_rara = int(mascara_rara.sum())
        if n_rara > 0:
            ejemplos = df.loc[mascara_rara, col].head(10).tolist()
            registrar("advertencia", f"{col} con caracteres inusuales: {n_rara} filas. Ejemplos: {ejemplos}")

    comprobante = 2

    # Homónimos
    nombre_completo = (
        df["first_name"].str.strip().str.lower()
        + " | "
        + df["last_name"].str.strip().str.lower()
    )
    mascara_hom = nombre_completo.duplicated(keep=False) & (df["first_name"] != "") & (df["last_name"] != "")
    n_hom = int(mascara_hom.sum())
    if n_hom > 0:
        n_grupos_hom = int(nombre_completo[mascara_hom].nunique())
        registrar("advertencia", f"Homónimos: {n_hom} filas en {n_grupos_hom} grupos (mismo nombre+apellido, distinto customer_id). El anexo permite homónimos.")
    else:
        print("  Sin homónimos: OK")

    return comprobante, n_hom if 'n_hom' in locals() else 0


def validar_email():
    comprobante = 0
    print("\n--- Validación: email ---")

    email = df["email"].astype(str).str.strip()

    # 1. Vacíos
    n_vac = int((email == "").sum())
    if n_vac > 0:
        registrar("error", f"email vacío: {n_vac} filas")
    else:
        print("  email sin celdas vacías: OK")
        comprobante = 1

    # 2. Formato válido
    if comprobante == 1:
        email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        valido_fmt = email.str.match(email_re)
        n_fmt = int((~valido_fmt & (email != "")).sum())
        if n_fmt > 0:
            ejemplos = email.loc[~valido_fmt & (email != "")].head(10).tolist()
            registrar("error", f"email con formato inválido: {n_fmt} filas. Ejemplos: {ejemplos}")
        else:
            print("  email con formato válido: OK")
            comprobante = 2

    # 3. Dominio @example.com
    if comprobante == 2:
        dominio = email.str.split("@").str[1].str.lower()
        n_dom = int((dominio != "example.com").sum())
        if n_dom > 0:
            ejemplos = email.loc[dominio != "example.com"].head(10).tolist()
            registrar("error", f"email con dominio distinto a @example.com: {n_dom} filas. Ejemplos: {ejemplos}")
        else:
            print("  email con dominio @example.com: OK")
            comprobante = 3

    # 4. Sin duplicados
    if comprobante == 3:
        n_dup_email = int(email.duplicated(keep=False).sum())
        if n_dup_email > 0:
            registrar("error", f"email duplicado: {n_dup_email} filas")
        else:
            print("  email sin duplicados: OK")
            comprobante = 4

    return comprobante


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
# Ejecución en secuencia
# ---------------------------------------------------------------------------
calcular_completitud(df_original, "Antes de la auditoría")
initial_inspection()

c1, _, _ = validar_customer_id()
c2, _ = validar_nombres()
c3 = validar_email()

calcular_tabla_calidad(df_original)

print("\n" + "=" * 70)
print("RESUMEN FINAL DE AUDITORÍA")
print("=" * 70)
print(f"  Total errores: {len(errores)}")
print(f"  Total advertencias: {len(advertencias)}")

if errores:
    print("\nERRORES ENCONTRADOS:")
    for e in errores:
        print(f"  - {e}")
else:
    print("\nNo se encontraron errores importantes.")

if advertencias:
    print("\nADVERTENCIAS:")
    for a in advertencias:
        print(f"  - {a}")

print(f"\nComprobantes finales: customer_id={c1}, nombres={c2}, email={c3}")
print("\nNota: el CSV original no se modificó.")
