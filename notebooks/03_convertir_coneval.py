import pandas as pd

print(" INSPECCIÓN DE ENCABEZADOS\n" + "="*60)

# SEP - Ver primeras 10 filas sin header
df_sep_raw = pd.read_excel('../data/raw/sep/serie_historica_entidades_sep.xlsm', engine='openpyxl', header=None)
print("\n📄 SEP - Primeras 10 filas:")
print(df_sep_raw.head(10).iloc[:, :6])

# INEGI - Ver primeras 10 filas sin header
df_inegi_raw = pd.read_excel('../data/raw/inegi/Educacion_abandono.xlsx', header=None)
print("\n📄 INEGI - Primeras 10 filas:")
print(df_inegi_raw.head(10).iloc[:, :6])