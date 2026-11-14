"""
Entradas (data/processed/):
    fact_abandono.csv   (1,024 filas)
    dim_entidad.csv     (32 filas, con pobreza 2020)
    dim_nivel.csv       (4 filas)

Salidas (data/processed/):
    kpis_indice_prioridad.csv  (32 filas: una por entidad)

Uso (desde la raíz del repo):
    python notebooks/05_kpis.py

KPI 1. Tasa de abandono 2023/2024 (media de los 4 niveles por entidad).
KPI 2. Cambio del abandono 2020/2021 -> 2023/2024 (puntos porcentuales).
KPI 3. Tasa de abandono en Media superior, 2023/2024.
KPI 4. Relación abandono vs. pobreza 2020 (correlación de Pearson).
KPI 5. Índice de prioridad en 3 niveles (Alta / Media / Baja).

Índice de prioridad (KPI 5):
    indice = (norm(abandono 2023/2024) + norm(pobreza 2020)) / 2
    donde norm(x) = 100 * (x - min) / (max - min) sobre las 32 entidades.
    Niveles por terciles del índice: Alta >= 56.5, Media 39.9-56.5, Baja < 39.9.
    (Los cortes se calculan desde los datos; no son umbrales oficiales.)
"""
from pathlib import Path

import pandas as pd

_CANDIDATOS = [Path(__file__).resolve().parents[1], Path.cwd()]
ROOT = next((p for p in _CANDIDATOS if (p / "data" / "processed").is_dir()),
            _CANDIDATOS[0])
PROCESSED = ROOT / "data" / "processed"

NIVELES = {1: "Primaria", 2: "Secundaria", 3: "Media superior", 4: "Superior"}


def norm(s):
    return 100 * (s - s.min()) / (s.max() - s.min())


def main():
    print("CALCULANDO KPIs (Sprint 4, US-09)...\n")
    fact = pd.read_csv(PROCESSED / "fact_abandono.csv", dtype={"ent": str})
    dim = pd.read_csv(PROCESSED / "dim_entidad.csv", dtype={"ent": str})
    nombres = dict(zip(dim["ent"], dim["nombre_entidad"]))

    # ---------- KPI 1 ----------
    k1 = fact[fact["id_ciclo"] == "2023/2024"]
    print("KPI 1. Abandono 2023/2024 por nivel (media nacional, 32 entidades):")
    for nid, nombre in NIVELES.items():
        print(f"   {nombre}: {k1[k1['id_nivel'] == nid]['tasa_abandono'].mean():.2f}%")
    print(f"   Media general: {k1['tasa_abandono'].mean():.2f}%")

    # ---------- KPI 2 ----------
    m20 = fact[fact["id_ciclo"] == "2020/2021"].groupby("ent")["tasa_abandono"].mean()
    m23 = fact[fact["id_ciclo"] == "2023/2024"].groupby("ent")["tasa_abandono"].mean()
    cambio = (m23 - m20).sort_values(ascending=False)
    print(f"\nKPI 2. Cambio 2020/2021 -> 2023/2024 (media nacional): "
          f"{m20.mean():.2f}% -> {m23.mean():.2f}% = {m23.mean() - m20.mean():+.2f} pp")
    print("   Mayores aumentos: " + ", ".join(
        f"{nombres[e]} {v:+.2f}" for e, v in cambio.head(3).items()))
    print("   Mayores bajas: " + ", ".join(
        f"{nombres[e]} {v:+.2f}" for e, v in cambio.tail(3).items()))

    # ---------- KPI 3 ----------
    ms = fact[(fact["id_nivel"] == 3) & (fact["id_ciclo"] == "2023/2024")].copy()
    ms["nombre_entidad"] = ms["ent"].map(nombres)
    ms = ms.sort_values("tasa_abandono", ascending=False)
    print(f"\nKPI 3. Media superior 2023/2024: media {ms['tasa_abandono'].mean():.2f}%, "
          f"rango {ms['tasa_abandono'].min():.1f} a {ms['tasa_abandono'].max():.1f}%")
    print("   Más altas: " + ", ".join(
        f"{r.nombre_entidad} {r.tasa_abandono:.1f}%" for r in ms.head(3).itertuples()))

    # ---------- KPI 4 ----------
    for ciclo in ["2020/2021", "2023/2024"]:
        media = fact[fact["id_ciclo"] == ciclo].groupby("ent")["tasa_abandono"].mean()
        dd = dim.set_index("ent").join(media.rename("abandono"))
        r = dd["abandono"].corr(dd["pct_pobreza_2020"])
        print(f"KPI 4. Correlación abandono vs. pobreza 2020 ({ciclo}): r = {r:.2f}")

    # ---------- KPI 5 ----------
    idx = pd.DataFrame({
        "ent": m23.index,
        "nombre_entidad": m23.index.map(nombres),
        "abandono_2023_2024": m23.values,
        "pct_pobreza_2020": dim.set_index("ent").loc[m23.index, "pct_pobreza_2020"].values,
    })
    idx["indice_prioridad"] = (norm(idx["abandono_2023_2024"])
                               + norm(idx["pct_pobreza_2020"])) / 2
    idx["nivel_prioridad"] = pd.qcut(idx["indice_prioridad"], 3,
                                     labels=["Baja", "Media", "Alta"])
    idx = idx.sort_values("indice_prioridad", ascending=False).reset_index(drop=True)
    print("\nKPI 5. Índice de prioridad (terciles):")
    print(idx["nivel_prioridad"].value_counts().to_string())
    print("   Top 5 (Alta): " + ", ".join(
        f"{r.nombre_entidad} {r.indice_prioridad:.1f}"
        for r in idx.head(5).itertuples()))

    idx.to_csv(PROCESSED / "kpis_indice_prioridad.csv", index=False)
    print("\nArchivo escrito: data/processed/kpis_indice_prioridad.csv (32 filas)")


if __name__ == "__main__":
    main()
