"""ETL corregido — Sprint 2: INEGI + CONEVAL (estatal). v2

Uso (desde la raíz del repo):
    python src/03_etl_integracion.py

Entradas:
    data/raw/sep/serie_historica_entidades_sep.xlsm
    data/raw/inegi/Educacion_abandono.xlsx
    data/raw/coneval/pobreza_municipal_2020.csv   (LOCAL, no se sube)

Salidas:
    data/processed/coneval_estatal.csv
    data/processed/dataset_analitico_v1.csv   (128 filas esperadas)

Correcciones frente a la versión anterior:
  - Sin .str.title(): los nombres se normalizan sin acentos y en
    minúsculas para mapear, así no se pierden Ciudad de México,
    Coahuila de Zaragoza, Michoacán de Ocampo ni Veracruz.
  - Sin filtro por contains('notas:'): solo se conservan las 32
    entidades y los 4 niveles educativos; eso elimina el total
    nacional y las filas de notas al pie.
  - 'ent' normalizado a 2 dígitos en ambos lados.
  - SEP se carga y se reporta, pero no se une aquí: su integración
    es del modelo dimensional (Sprint 3).

v2 — 9 Nov 2026: el CSV real de CONEVAL es MICRODATOS a nivel
persona (315,619 filas, 74 columnas), no el agregado municipal.
No hay 'pp_pobre': hay 'pobreza' / 'pobreza_e' / 'pobreza_m'
binarias y 'factor' como ponderador de expansión. La pobreza
estatal es entonces:
    pct = 100 * sum(factor * pobreza) / sum(factor)   por entidad
Esta versión detecta los dos formatos (microdatos y agregado
municipal con 'pp_pobre' / 'pobtot') y usa el que encuentre.
"""
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

NIVELES = {"primaria", "secundaria", "media superior", "superior"}

# Nombre normalizado (sin acentos, minúsculas) -> código INEGI de 2 dígitos.
ESTADOS = {
    "aguascalientes": "01",
    "baja california": "02",
    "baja california sur": "03",
    "campeche": "04",
    "coahuila": "05",
    "coahuila de zaragoza": "05",
    "colima": "06",
    "chiapas": "07",
    "chihuahua": "08",
    "ciudad de mexico": "09",
    "distrito federal": "09",
    "cdmx": "09",
    "durango": "10",
    "guanajuato": "11",
    "guerrero": "12",
    "hidalgo": "13",
    "jalisco": "14",
    "mexico": "15",
    "estado de mexico": "15",
    "edomex": "15",
    "michoacan": "16",
    "michoacan de ocampo": "16",
    "morelos": "17",
    "nayarit": "18",
    "nuevo leon": "19",
    "oaxaca": "20",
    "puebla": "21",
    "queretaro": "22",
    "quintana roo": "23",
    "san luis potosi": "24",
    "sinaloa": "25",
    "sonora": "26",
    "tabasco": "27",
    "tamaulipas": "28",
    "tlaxcala": "29",
    "veracruz": "30",
    "veracruz de ignacio de la llave": "30",
    "yucatan": "31",
    "zacatecas": "32",
}


def norm(texto):
    """Minúsculas, sin acentos, espacios colapsados. NaN -> ''."""
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    return " ".join(texto.split())


def codigo_ent(valor):
    """Normaliza un código de entidad a string de 2 dígitos ('01'..'32')."""
    if pd.isna(valor):
        return None
    try:
        return f"{int(float(str(valor).strip())):02d}"
    except (TypeError, ValueError):
        return None


def buscar_columna(columnas, candidatos, contiene=None):
    """Busca una columna por nombre exacto (sin acentos) o por substring."""
    bajas = {norm(c): c for c in columnas}
    for cand in candidatos:
        if norm(cand) in bajas:
            return bajas[norm(cand)]
    if contiene:
        for fragmento in contiene:
            for c in columnas:
                if fragmento in norm(c):
                    return c
    return None


def a_binario(serie):
    """Convierte un indicador de pobreza a 0/1.

    Acepta {0, 1} tal cual y {1, 2} como 1=pobre, 2=no pobre.
    Devuelve None si los valores no son binarios reconocibles.
    """
    vals = set(pd.to_numeric(serie, errors="coerce").dropna().unique())
    if vals <= {0, 1}:
        return pd.to_numeric(serie, errors="coerce")
    if vals <= {1, 2}:
        return pd.to_numeric(serie, errors="coerce").map({1: 1, 2: 0})
    return None


def agregar_coneval(df_coneval):
    """Agrega CONEVAL a nivel estatal. Devuelve (agg, modo).

    Microdatos: pct = 100 * sum(factor*pobreza) / sum(factor).
    Municipal: pct = sum(pp_pobre * pobtot) / sum(pobtot).
    """
    col_ent = buscar_columna(
        df_coneval.columns, ["ent", "cve_ent", "CVE_ENT", "clave_entidad"])
    if col_ent is None:
        print("ERROR: no se encontró columna de entidad ('ent' / 'cve_ent').")
        print("Columnas disponibles:", list(df_coneval.columns))
        sys.exit(1)

    df = df_coneval.copy()
    df["ent"] = df[col_ent].map(codigo_ent)

    if "pobreza" in [norm(c) for c in df.columns]:
        modo = "microdatos"
        col_factor = buscar_columna(df.columns, ["factor"])
        if col_factor is None:
            print("ERROR microdatos: falta 'factor' para ponderar.")
            sys.exit(1)
        print(f"Formato CONEVAL: microdatos, ponderador '{col_factor}'")
        agg_rows = []
        for ent, g in df.dropna(subset=["ent"]).groupby("ent"):
            w = pd.to_numeric(g[col_factor], errors="coerce")
            fila = {"ent": ent, "n_personas": int(len(g)),
                    "poblacion_expandida": float(w.sum())}
            for col, salida in [("pobreza", "pct_pobreza_estatal"),
                                ("pobreza_e", "pct_pobreza_extrema_estatal"),
                                ("pobreza_m", "pct_pobreza_moderada_estatal")]:
                real = buscar_columna(df.columns, [col])
                if real is None:
                    continue
                b = a_binario(g[real])
                if b is None:
                    print(f"ERROR: '{real}' no es binaria 0/1 ni 1/2, "
                          f"valores: {sorted(g[real].dropna().unique()[:10])}")
                    sys.exit(1)
                fila[salida] = float(100 * (w * b.fillna(0)).sum() / w.sum())
            agg_rows.append(fila)
        return pd.DataFrame(agg_rows).sort_values("ent"), modo

    # Formato agregado municipal (por si el archivo cambia).
    modo = "municipal"
    col_pobreza = buscar_columna(
        df.columns, ["pp_pobre", "pct_pobreza", "porcentaje_pobreza"],
        contiene=["pp_pobre", "pct_pobreza", "porcentaje_pobreza"])
    if col_pobreza is None:
        print("ERROR: no se encontró columna de pobreza ('pobreza' "
              "ni 'pp_pobre').")
        print("Columnas con 'pob' o 'porc':",
              [c for c in df.columns
               if "pob" in norm(c) or "porc" in norm(c)])
        sys.exit(1)
    col_pob = buscar_columna(
        df.columns, ["pobtot", "pob_total", "poblacion", "pob"],
        contiene=["pobtot", "pob_total"])
    print(f"Formato CONEVAL: municipal, pobreza '{col_pobreza}', "
          f"población '{col_pob}'")
    if col_pob is not None:
        tmp = df.dropna(subset=["ent", col_pobreza, col_pob]).copy()
        tmp["_pond"] = tmp[col_pobreza] * tmp[col_pob]
        agg = tmp.groupby("ent").agg(
            pct_pobreza_estatal=("_pond", "sum"),
            _pob=(col_pob, "sum"),
            n_municipios=(col_pobreza, "size"),
        ).reset_index()
        agg["pct_pobreza_estatal"] /= agg["_pob"]
        return agg.drop(columns=["_pob"]), modo
    agg = (df.dropna(subset=["ent", col_pobreza])
           .groupby("ent")[col_pobreza]
           .agg(pct_pobreza_estatal="mean", n_municipios="size")
           .reset_index())
    return agg, modo


def main():
    print("INICIANDO PROCESO ETL (versión corregida v2)...\n")

    # 1. SEP: solo se carga y se reporta (integración en Sprint 3).
    df_sep = pd.read_excel(
        RAW / "sep" / "serie_historica_entidades_sep.xlsm",
        engine="openpyxl", header=3,
    )
    df_sep.columns = df_sep.columns.str.strip()
    df_sep = df_sep.dropna(how="all")
    print(f"SEP cargado (solo reporte): {df_sep.shape[0]} filas, "
          f"{df_sep.shape[1]} columnas")

    # 2. INEGI: encabezado real en fila 5, limpieza por lista blanca.
    df_inegi = pd.read_excel(
        RAW / "inegi" / "Educacion_abandono.xlsx", header=5,
    )
    df_inegi.columns = df_inegi.columns.str.strip()
    df_inegi = df_inegi.drop_duplicates()
    print(f"INEGI cargado: {df_inegi.shape[0]} filas, "
          f"{df_inegi.shape[1]} columnas")

    df_inegi["ent"] = df_inegi["Entidad federativa"].map(
        lambda x: ESTADOS.get(norm(x))
    )
    df_inegi["_nivel"] = df_inegi["Nivel educativo"].map(norm)
    antes = len(df_inegi)
    df_inegi = df_inegi[
        df_inegi["ent"].notna() & df_inegi["_nivel"].isin(NIVELES)
    ].copy()
    df_inegi = df_inegi.drop(columns=["_nivel"])
    print(f"INEGI limpio: {len(df_inegi)} filas "
          f"(se quitaron {antes - len(df_inegi)}: total nacional y notas al pie)")
    print(f"INEGI estados distintos: {df_inegi['ent'].nunique()} "
          f"(esperado: 32)")

    # 3. CONEVAL: debe existir en local; si no, fallar con mensaje claro.
    ruta_coneval = RAW / "coneval" / "pobreza_municipal_2020.csv"
    if not ruta_coneval.exists():
        print(f"\nERROR: no existe {ruta_coneval}")
        print("Corre primero src/01_convertir_coneval.py con el .dta "
              "en local, o coloca el CSV ahí. No se genera ningún dataset.")
        sys.exit(1)

    df_coneval = pd.read_csv(ruta_coneval, encoding="utf-8")
    print(f"\nCONEVAL cargado: {df_coneval.shape[0]} filas, "
          f"{df_coneval.shape[1]} columnas")

    agg, modo = agregar_coneval(df_coneval)
    print(f"CONEVAL estatal ({modo}): {len(agg)} estados (esperado: 32)")
    print(agg.head(10).to_string(index=False))

    # 4. Merge INEGI + CONEVAL estatal por 'ent'.
    df_analitico = pd.merge(df_inegi, agg, on="ent", how="left")
    nulos = int(df_analitico["pct_pobreza_estatal"].isna().sum())
    print(f"\nDataset analítico: {df_analitico.shape[0]} filas, "
          f"{df_analitico.shape[1]} columnas")
    print(f"Filas con pct_pobreza_estatal en NaN: {nulos} (esperado: 0)")
    if nulos:
        faltan = sorted(
            df_analitico.loc[
                df_analitico["pct_pobreza_estatal"].isna(), "ent"
            ].unique().tolist()
        )
        print(f"Estados sin pobreza: {faltan}")
        sys.exit(1)
    if len(df_analitico) != 128 or len(agg) != 32:
        print("AVISO: los conteos no son 128 / 32. Revisa el reporte "
              "antes de dar el sprint por terminado.")
        sys.exit(1)

    # 5. Guardar.
    PROCESSED.mkdir(parents=True, exist_ok=True)
    agg.to_csv(PROCESSED / "coneval_estatal.csv",
               index=False, encoding="utf-8")
    df_analitico.to_csv(
        PROCESSED / "dataset_analitico_v1.csv", index=False, encoding="utf-8"
    )
    print("\nETL completado.")
    print(f"  - {PROCESSED / 'coneval_estatal.csv'}")
    print(f"  - {PROCESSED / 'dataset_analitico_v1.csv'}")
    print("\nPrimeras 5 filas:")
    print(df_analitico.head().to_string(index=False))


if __name__ == "__main__":
    main()
