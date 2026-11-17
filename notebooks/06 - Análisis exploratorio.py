from pathlib import Path

import pandas as pd

_CANDIDATOS = [Path(__file__).resolve().parents[1], Path.cwd()]
ROOT = next((p for p in _CANDIDATOS if (p / "data" / "processed").is_dir()),
            _CANDIDATOS[0])
PROCESSED = ROOT / "data" / "processed"

NIVELES = {1: "Primaria", 2: "Secundaria", 3: "Media superior", 4: "Superior"}
CICLOS = ["2000/2001", "2005/2006", "2010/2011", "2015/2016",
          "2020/2021", "2021/2022", "2022/2023", "2023/2024"]


def main():
    print("ANÁLISIS EXPLORATORIO (Sprint 5, guía sección 16)...\n")
    fact = pd.read_csv(PROCESSED / "fact_abandono.csv", dtype={"ent": str})
    dim = pd.read_csv(PROCESSED / "dim_entidad.csv", dtype={"ent": str})
    nombres = dict(zip(dim["ent"], dim["nombre_entidad"]))

    # H1 / H2 — tendencia por ciclo y nivel
    t = (fact.pivot_table(index="id_ciclo", columns="id_nivel",
                          values="tasa_abandono", aggfunc="mean")
         .reindex(CICLOS).rename(columns=NIVELES))
    print("H1/H2. Media nacional por ciclo y nivel:")
    print(t.round(2).to_string())
    print("   Media general: "
          f"{t.mean(axis=1).iloc[0]:.2f}% (2000/2001) -> "
          f"{t.mean(axis=1).iloc[-1]:.2f}% (2023/2024)")
    print("   Media superior es la más alta en los 8 ciclos.")

    # H3 — Jalisco por nivel
    j = fact[fact["ent"] == "14"].pivot_table(
        index="id_nivel", columns="id_ciclo", values="tasa_abandono")
    delta = (j["2023/2024"] - j["2020/2021"]).rename(NIVELES)
    print("\nH3. Jalisco, cambio por nivel 2020/2021 -> 2023/2024:")
    print("   " + ", ".join(f"{k} {v:+.1f} pp" for k, v in delta.items()))
    print("   Media superior Jalisco: "
          f"{j.loc[3, '2020/2021']:.1f}% -> {j.loc[3, '2023/2024']:.1f}%")

    # H4 — correlación por nivel
    print("\nH4. Correlación abandono 2023/2024 vs. pobreza 2020, por nivel:")
    for n, nombre in NIVELES.items():
        s = (fact[(fact["id_nivel"] == n) & (fact["id_ciclo"] == "2023/2024")]
             .set_index("ent")["tasa_abandono"])
        dd = dim.set_index("ent").join(s.rename("ab"))
        print(f"   {nombre}: r = "
              f"{dd['ab'].corr(dd['pct_pobreza_2020']):.2f}")
    print("   Chiapas: pobreza 74.43%, abandono medio 2023/2024 "
          f"{fact[(fact['ent'] == '07') & (fact['id_ciclo'] == '2023/2024')]['tasa_abandono'].mean():.2f}%")

    # H5 — negativas
    neg = fact[fact["flag_tasa_negativa"] == 1]
    print("\nH5. Tasas negativas:", len(neg), "en total; por nivel:",
          neg.groupby("id_nivel").size().rename(NIVELES).to_dict())
    print("   Por ciclo:",
          neg.groupby("id_ciclo").size().reindex(CICLOS).fillna(0).astype(int).to_dict())

    # H6 — persistencia
    print("\nH6. Top 5 abandono (media 4 niveles):")
    for c in ["2000/2001", "2023/2024"]:
        m = (fact[fact["id_ciclo"] == c].groupby("ent")["tasa_abandono"]
             .mean().sort_values(ascending=False))
        print(f"   {c}: " + ", ".join(
            f"{nombres[e]} {v:.2f}%" for e, v in m.head(5).items()))

    # Advertencia DAX: media simple vs. ponderada
    print("\nADVERTENCIA DAX: la media simple de los 32 % estatales de "
          f"pobreza es {dim['pct_pobreza_2020'].mean():.2f}%, no la "
          "nacional ponderada de 44.46%. No uses AVERAGE() para el "
          "dato nacional; escríbelo como valor fijo.")


if __name__ == "__main__":
    main()
