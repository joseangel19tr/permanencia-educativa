"""Genera el resumen ligero de CONEVAL (lo único que hay que subir). v2

Uso (desde la raíz del repo, en tu computadora):
    python src/extraer_resumen_coneval.py

Busca, en este orden:
  1. data/raw/coneval/pobreza_municipal_2020.csv
  2. data/coneval/Pobreza_municipal_2020_VCORTA/.../pobreza_20.dta
     (entonces lo convierte a CSV en local con pyreadstat)

Genera (archivos pequeños, sí se pueden subir al chat / a GitHub):
    data/processed/coneval_resumen.json   (columnas, tipos, conteos)
    data/processed/coneval_estatal.csv    (32 filas, pobreza por estado)

El archivo grande de CONEVAL nunca se sube.

v2 — 9 Nov 2026: el CSV real NO es el agregado municipal con
'pp_pobre', es microdatos a nivel persona: 315,619 filas, 74 columnas,
con 'pobreza' / 'pobreza_e' / 'pobreza_m' binarias y 'factor' como
ponderador de expansión. Por eso la v1 no encontraba la columna y
decía que faltaba. Esta versión detecta los dos formatos:
  - microdatos: 'pobreza' (0/1) ponderada por 'factor' -> % estatal
  - agregado municipal: 'pp_pobre' ponderado por 'pobtot'
"""
import json
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def norm(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    return " ".join(texto.split())


def codigo_ent(valor):
    if pd.isna(valor):
        return None
    try:
        return f"{int(float(str(valor).strip())):02d}"
    except (TypeError, ValueError):
        return None


def buscar_columna(columnas, candidatos, contiene=None):
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


def main():
    ruta_csv = ROOT / "data" / "raw" / "coneval" / "pobreza_municipal_2020.csv"
    ruta_dta = (
        ROOT / "data" / "coneval" / "Pobreza_municipal_2020_VCORTA"
        / "MunEBPH_2020" / "datos" / "entradas" / "06_bases_pobreza"
        / "pobreza_20.dta"
    )

    if ruta_csv.exists():
        print(f"Leyendo CSV: {ruta_csv}")
        df = pd.read_csv(ruta_csv, encoding="utf-8")
    elif ruta_dta.exists():
        print(f"Leyendo DTA: {ruta_dta}")
        import pyreadstat
        df, _meta = pyreadstat.read_dta(str(ruta_dta))
        ruta_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(ruta_csv, index=False, encoding="utf-8")
        print(f"CSV guardado en local (no subir): {ruta_csv}")
    else:
        print("ERROR: no encontré el archivo de CONEVAL.")
        print(f"  Esperaba: {ruta_csv}")
        print(f"  o bien:   {ruta_dta}")
        sys.exit(1)

    print(f"CONEVAL: {df.shape[0]} filas, {df.shape[1]} columnas")
    print("Primeras 25 columnas:", list(df.columns[:25]))
    print("Columnas con 'pob' o 'porc':",
          [c for c in df.columns if "pob" in norm(c) or "porc" in norm(c)])

    col_ent = buscar_columna(
        df.columns, ["ent", "cve_ent", "CVE_ENT", "clave_entidad"])

    # Detectar formato: microdatos o agregado municipal.
    if "pobreza" in [norm(c) for c in df.columns]:
        modo = "microdatos"
        col_pobreza = buscar_columna(df.columns, ["pobreza"])
        col_factor = buscar_columna(df.columns, ["factor"])
    else:
        modo = "municipal"
        col_pobreza = buscar_columna(
            df.columns, ["pp_pobre", "pct_pobreza", "porcentaje_pobreza"],
            contiene=["pp_pobre", "pct_pobreza", "porcentaje_pobreza"])
        col_factor = buscar_columna(
            df.columns, ["pobtot", "pob_total", "poblacion", "pob"],
            contiene=["pobtot", "pob_total"])
    print(f"Formato detectado: {modo}")
    print(f"Columna entidad: {col_ent} | pobreza: {col_pobreza} | "
          f"ponderador: {col_factor}")

    resumen = {
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
        "modo": modo,
        "primeras_25_columnas": [str(c) for c in df.columns[:25]],
        "columnas_pob_porc": [str(c) for c in df.columns
                              if "pob" in norm(c) or "porc" in norm(c)],
        "col_ent_detectada": col_ent,
        "col_pobreza_detectada": col_pobreza,
        "col_ponderador_detectada": col_factor,
        "ent_unicos": None,
        "ent_tipo": None,
    }
    if col_ent is not None:
        resumen["ent_unicos"] = int(df[col_ent].nunique())
        resumen["ent_tipo"] = str(df[col_ent].dtype)
        resumen["ent_ejemplos"] = [str(v) for v in
                                   df[col_ent].dropna().unique()[:10]]
    for col in ["pobreza", "pobreza_e", "pobreza_m"]:
        real = buscar_columna(df.columns, [col])
        if real is not None:
            resumen[f"{col}_valores"] = sorted(
                str(v) for v in df[real].dropna().unique()[:10])
            resumen[f"{col}_nulos"] = int(df[real].isna().sum())

    PROCESSED.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED / "coneval_resumen.json", "w",
              encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    print(f"\nResumen guardado: {PROCESSED / 'coneval_resumen.json'}")

    if col_ent is None or col_pobreza is None:
        print("No se pudo hacer el agregado estatal: falta 'ent' "
              "o la columna de pobreza. Revisa el resumen JSON.")
        return

    df["ent"] = df[col_ent].map(codigo_ent)

    if modo == "microdatos":
        if col_factor is None:
            print("ERROR microdatos: falta 'factor' para ponderar.")
            return
        # Pobreza ponderada por factor, en %: 100 * sum(factor*pobre) / sum(factor)
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
                    print(f"AVISO: '{real}' no es binaria 0/1 ni 1/2, "
                          f"valores: {sorted(g[real].dropna().unique()[:10])}")
                    continue
                fila[salida] = float(100 * (w * b.fillna(0)).sum() / w.sum())
            agg_rows.append(fila)
        agg = pd.DataFrame(agg_rows).sort_values("ent")
    else:
        tmp = df.dropna(subset=["ent", col_pobreza, col_factor]).copy()
        tmp["_pond"] = tmp[col_pobreza] * tmp[col_factor]
        agg = tmp.groupby("ent").agg(
            pct_pobreza_estatal=("_pond", "sum"),
            _pob=(col_factor, "sum"),
            n_municipios=(col_pobreza, "size"),
        ).reset_index()
        agg["pct_pobreza_estatal"] /= agg["_pob"]
        agg = agg.drop(columns=["_pob"])

    agg.to_csv(PROCESSED / "coneval_estatal.csv",
               index=False, encoding="utf-8")
    print(f"Agregado estatal guardado ({len(agg)} estados): "
          f"{PROCESSED / 'coneval_estatal.csv'}")
    print(f"Pobreza estatal NaN: "
          f"{int(agg['pct_pobreza_estatal'].isna().sum())}")
    print(agg.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
