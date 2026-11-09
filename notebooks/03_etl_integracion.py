import pandas as pd
import numpy as np

print("INICIANDO PROCESO ETL...\n")

# 1. Cargar y limpiar SEP
df_sep = pd.read_excel('../data/raw/sep/serie_historica_entidades_sep.xlsm', engine='openpyxl', header=3)
df_sep.columns = df_sep.columns.str.strip()
df_sep = df_sep.dropna(how='all')
print(f"SEP cargado: {df_sep.shape[0]} filas, {df_sep.shape[1]} columnas")

# 2. Cargar y limpiar INEGI
df_inegi = pd.read_excel('../data/raw/inegi/Educacion_abandono.xlsx', header=5)
df_inegi.columns = df_inegi.columns.str.strip()
df_inegi = df_inegi.drop_duplicates()
# Filtrar filas basura
df_inegi = df_inegi[~df_inegi['Entidad federativa'].str.contains('Estados Unidos Mexicanos|notas:', na=False)]
print(f"INEGI cargado: {df_inegi.shape[0]} filas, {df_inegi.shape[1]} columnas")

# 3. Cargar CONEVAL
df_coneval = pd.read_csv('../data/raw/coneval/pobreza_municipal_2020.csv', encoding='utf-8')
print(f"CONEVAL cargado: {df_coneval.shape[0]} filas, {df_coneval.shape[1]} columnas")

# 4. Mapeo de nombres de estado a códigos de 2 dígitos (Estándar INEGI/CONEVAL)
mapeo_estados = {
    'Aguascalientes': '01', 'Baja California': '02', 'Baja California Sur': '03',
    'Campeche': '04', 'Coahuila de Zaragoza': '05', 'Coahuila': '05',
    'Colima': '06', 'Chiapas': '07', 'Chihuahua': '08', 
    'Ciudad de México': '09', 'Distrito Federal': '09', 'Cdmx': '09', 'Cdmx': '09',
    'Durango': '10', 'Guanajuato': '11', 'Guerrero': '12', 'Hidalgo': '13',
    'Jalisco': '14', 'México': '15', 'Estado de México': '15', 'Edomex': '15',
    'Michoacán de Ocampo': '16', 'Michoacán': '16', 'Morelos': '17', 'Nayarit': '18',
    'Nuevo León': '19', 'Oaxaca': '20', 'Puebla': '21', 'Querétaro': '22',
    'Quintana Roo': '23', 'San Luis Potosí': '24', 'Sinaloa': '25', 'Sonora': '26',
    'Tabasco': '27', 'Tamaulipas': '28', 'Tlaxcala': '29', 
    'Veracruz de Ignacio de la Llave': '30', 'Veracruz': '30',
    'Yucatán': '31', 'Zacatecas': '32'
}

# Limpiar nombres en INEGI y aplicar el mapeo para crear la columna 'ent'
df_inegi['Entidad federativa'] = df_inegi['Entidad federativa'].str.strip().str.title()
df_inegi['ent'] = df_inegi['Entidad federativa'].map(mapeo_estados)

# 5. Preparar CONEVAL (Agrupar a nivel estatal)
# Buscar la columna de porcentaje de pobreza en CONEVAL
col_pobreza = next((c for c in df_coneval.columns if 'pp_pobre' in c.lower() or 'pct_pobreza' in c.lower()), None)

if col_pobreza:
    print(f"Columna de pobreza detectada: '{col_pobreza}'")
    # Agrupamos por entidad ('ent') para obtener el promedio estatal de pobreza
    df_coneval_estatal = df_coneval.groupby('ent')[col_pobreza].mean().reset_index()
    df_coneval_estatal.rename(columns={col_pobreza: 'pct_pobreza_estatal'}, inplace=True)
else:
    print("Advertencia: No se encontró columna de pobreza. Se omitirá esta unión.")
    df_coneval_estatal = pd.DataFrame(columns=['ent', 'pct_pobreza_estatal'])

# 6. Unir INEGI con CONEVAL (ahora sí por código 'ent')
df_analitico = pd.merge(df_inegi, df_coneval_estatal, on='ent', how='left')

print(f"\nDataset analítico creado: {df_analitico.shape[0]} filas, {df_analitico.shape[1]} columnas")

# 7. Guardar resultado
df_analitico.to_csv('../data/processed/dataset_analitico_v1.csv', index=False, encoding='utf-8')
print("ETL completado. Archivo guardado en: ../data/processed/dataset_analitico_v1.csv")

print("\nPrimeras 5 filas del dataset analítico:")
print(df_analitico.head())