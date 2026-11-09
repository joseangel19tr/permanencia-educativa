import pandas as pd
import numpy as np

print("🔄 Cargando las 3 fuentes de datos...\n")

# ==========================================
# 1. CARGAR SEP
# ==========================================
try:
    df_sep = pd.read_excel('../data/raw/sep/serie_historica_entidades_sep.xlsm', engine='openpyxl', header=2)
    df_sep.columns = df_sep.columns.str.strip()
    print(f"✅ SEP cargado: {df_sep.shape[0]} filas, {df_sep.shape[1]} columnas")
    print(f"   Primeras columnas: {list(df_sep.columns[:5])}")
except Exception as e:
    print(f"❌ Error SEP: {e}")
    df_sep = pd.DataFrame()

# ==========================================
# 2. CARGAR INEGI
# ==========================================
try:
    df_inegi = pd.read_excel('../data/raw/inegi/Educacion_abandono.xlsx', header=4)
    df_inegi.columns = df_inegi.columns.str.strip()
    print(f"\n✅ INEGI cargado: {df_inegi.shape[0]} filas, {df_inegi.shape[1]} columnas")
    print(f"   Primeras columnas: {list(df_inegi.columns[:5])}")
except Exception as e:
    print(f" Error INEGI: {e}")
    df_inegi = pd.DataFrame()

# ==========================================
# 3. CARGAR CONEVAL
# ==========================================
try:
    df_coneval = pd.read_csv('../data/raw/coneval/pobreza_municipal_2020.csv', encoding='utf-8')
    print(f"\n✅ CONEVAL cargado: {df_coneval.shape[0]} filas, {df_coneval.shape[1]} columnas")
except Exception as e:
    print(f"❌ Error CONEVAL: {e}")
    df_coneval = pd.DataFrame()

print("\n" + "="*70)
print(" ANÁLISIS DE CALIDAD DE DATOS")
print("="*70)

# ==========================================
# 4. COMPLETITUD (Valores Nulos)
# ==========================================
print("\n--- 1. COMPLETITUD (Valores Nulos) ---")
if not df_sep.empty:
    print(f"SEP - Total nulos: {df_sep.isnull().sum().sum()}")
if not df_inegi.empty:
    print(f"INEGI - Total nulos: {df_inegi.isnull().sum().sum()}")
if not df_coneval.empty:
    print(f"CONEVAL - Total nulos: {df_coneval.isnull().sum().sum()}")

# ==========================================
# 5. UNICIDAD (Duplicados)
# ==========================================
print("\n--- 2. UNICIDAD (Duplicados) ---")
if not df_sep.empty:
    print(f"SEP - Filas duplicadas: {df_sep.duplicated().sum()}")
if not df_inegi.empty:
    print(f"INEGI - Filas duplicadas: {df_inegi.duplicated().sum()}")
if not df_coneval.empty:
    print(f"CONEVAL - Filas duplicadas: {df_coneval.duplicated().sum()}")

# ==========================================
# 6. CONSISTENCIA (Nombres de Entidades)
# ==========================================
print("\n--- 3. CONSISTENCIA (Nombres de Entidades) ---")

# Buscar columnas que contengan "entidad" o "estado" (usando str() para evitar errores)
col_sep = next((c for c in df_sep.columns if 'entidad' in str(c).lower() or 'estado' in str(c).lower() or 'federativa' in str(c).lower()), None)
col_inegi = next((c for c in df_inegi.columns if 'entidad' in str(c).lower() or 'federativa' in str(c).lower()), None)
col_coneval = next((c for c in df_coneval.columns if 'ent' in str(c).lower() or 'nom_ent' in str(c).lower()), None)

print(f"Columna de entidad en SEP: {col_sep}")
print(f"Columna de entidad en INEGI: {col_inegi}")
print(f"Columna de entidad en CONEVAL: {col_coneval}")

# Comparar nombres únicos entre SEP e INEGI
if col_sep and col_inegi and not df_sep.empty and not df_inegi.empty:
    estados_sep = set(df_sep[col_sep].dropna().astype(str).str.strip().str.lower().unique())
    estados_inegi = set(df_inegi[col_inegi].dropna().astype(str).str.strip().str.lower().unique())
    
    print(f"\nTotal de entidades únicas en SEP: {len(estados_sep)}")
    print(f"Total de entidades únicas en INEGI: {len(estados_inegi)}")
    
    diferencias = estados_sep.symmetric_difference(estados_inegi)
    if diferencias:
        print(f"\n⚠️ Diferencias encontradas ({len(diferencias)}):")
        for diff in list(diferencias)[:15]:
            print(f"  - '{diff}'")
    else:
        print("\n✅ Los nombres de entidades coinciden perfectamente.")

# ==========================================
# 7. RESUMEN FINAL
# ==========================================
print("\n" + "="*70)
print("📊 RESUMEN DE CALIDAD DE DATOS")
print("="*70)

if not df_sep.empty:
    print(f"SEP: {df_sep.shape[0]} filas, {df_sep.shape[1]} columnas")
    print(f"   - Nulos: {df_sep.isnull().sum().sum()}")
    print(f"   - Duplicados: {df_sep.duplicated().sum()}")
    if col_sep:
        print(f"   - Entidades únicas: {df_sep[col_sep].dropna().nunique()}")

if not df_inegi.empty:
    print(f"\nINEGI: {df_inegi.shape[0]} filas, {df_inegi.shape[1]} columnas")
    print(f"   - Nulos: {df_inegi.isnull().sum().sum()}")
    print(f"   - Duplicados: {df_inegi.duplicated().sum()}")
    if col_inegi:
        print(f"   - Entidades únicas: {df_inegi[col_inegi].dropna().nunique()}")

if not df_coneval.empty:
    print(f"\nCONEVAL: {df_coneval.shape[0]} filas, {df_coneval.shape[1]} columnas")
    print(f"   - Nulos: {df_coneval.isnull().sum().sum()}")
    print(f"   - Duplicados: {df_coneval.duplicated().sum()}")

print("\n✅ Análisis de calidad completado. Listo para el ETL del Sprint 3.")