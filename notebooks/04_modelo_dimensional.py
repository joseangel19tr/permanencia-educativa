
from pathlib import Path

import pandas as pd

_CANDIDATOS = [Path(__file__).resolve().parents[1], Path.cwd()]
ROOT = next((p for p in _CANDIDATOS if (p / "data" / "processed").is_dir()),
            _CANDIDATOS[0])
PROCESSED = ROOT / "data" / "processed"

CICLOS = ["2000/2001", "2005/2006", "2010/2011", "2015/2016",
          "2020/2021", "2021/2022", "2022/2023", "2023/2024"]
NIVELES = {"Primaria": 1, "Secundaria": 2, "Media superior": 3, "Superior": 4}


def main():
    print("CONSTRUYENDO MODELO DIMENSIONAL (Sprint 3, US-08)...\n")

    dataset = pd.read_csv(PROCESSED / "dataset_analitico_v1.csv")
    coneval = pd.read_csv(PROCESSED / "coneval_estatal.csv")
    print(f"Dataset analítico: {dataset.shape[0]} filas")
    print(f"CONEVAL estatal: {coneval.shape[0]} filas")

    nombres = (dataset[["ent", "Entidad federativa"]]
               .drop_duplicates()
               .rename(columns={"Entidad federativa": "nombre_entidad"}))
    nombres["ent"] = nombres["ent"].astype(int).map("{:02d}".format)
    coneval = coneval.copy()
    coneval["ent"] = coneval["ent"].astype(int).map("{:02d}".format)
    dim_entidad = nombres.merge(
        coneval[["ent", "n_personas", "poblacion_expandida",
                  "pct_pobreza_estatal", "pct_pobreza_extrema_estatal",
                  "pct_pobreza_moderada_estatal"]],
        on="ent", how="left", validate="one_to_one",
    ).rename(columns={
        "pct_pobreza_estatal": "pct_pobreza_2020",
        "pct_pobreza_extrema_estatal": "pct_pobreza_extrema_2020",
        "pct_pobreza_moderada_estatal": "pct_pobreza_moderada_2020",
        "poblacion_expandida": "poblacion_expandida_2020",
    }).sort_values("ent").reset_index(drop=True)

    dim_nivel = pd.DataFrame(
        [{"id_nivel": v, "nivel_educativo": k} for k, v in NIVELES.items()]
    ).sort_values("id_nivel").reset_index(drop=True)


    dim_tiempo = pd.DataFrame([{
        "id_ciclo": c,
        "ciclo": c,
        "anio_inicio": int(c.split("/")[0]),
        "anio_fin": int(c.split("/")[1]),
    } for c in CICLOS])

    fact = dataset.melt(
        id_vars=["ent", "Nivel educativo"],
        value_vars=CICLOS,
        var_name="id_ciclo",
        value_name="tasa_abandono",
    )
    fact["ent"] = fact["ent"].astype(int).map("{:02d}".format)
    fact["id_nivel"] = fact["Nivel educativo"].map(NIVELES)
    fact["flag_tasa_negativa"] = (fact["tasa_abandono"] < 0).astype(int)
    fact = (fact[["ent", "id_nivel", "id_ciclo", "tasa_abandono",
                  "flag_tasa_negativa"]]
            .sort_values(["ent", "id_nivel", "id_ciclo"])
            .reset_index(drop=True))
    
    errores = []
    if len(dim_entidad) != 32:
        errores.append(f"Dim_Entidad: {len(dim_entidad)} filas, se esperaban 32")
    if len(dim_nivel) != 4:
        errores.append(f"Dim_Nivel: {len(dim_nivel)} filas, se esperaban 4")
    if len(dim_tiempo) != 8:
        errores.append(f"Dim_Tiempo: {len(dim_tiempo)} filas, se esperaban 8")
    if len(fact) != 1024:
        errores.append(f"Fact_Abandono: {len(fact)} filas, se esperaban 1,024")
    if fact.duplicated(["ent", "id_nivel", "id_ciclo"]).any():
        errores.append("Fact_Abandono: hay duplicados en la llave (ent, nivel, ciclo)")
    for col in ["ent", "id_nivel", "id_ciclo", "tasa_abandono"]:
        if fact[col].isna().any():
            errores.append(f"Fact_Abandono: nulos en {col}")
    if dim_entidad.isna().any().any():
        errores.append("Dim_Entidad: hay nulos")
    huerfanos_ent = set(fact["ent"]) - set(dim_entidad["ent"])
    huerfanos_niv = set(fact["id_nivel"]) - set(dim_nivel["id_nivel"])
    huerfanos_cic = set(fact["id_ciclo"]) - set(dim_tiempo["id_ciclo"])
    if huerfanos_ent or huerfanos_niv or huerfanos_cic:
        errores.append(f"Huérfanos en el hecho: ent={huerfanos_ent}, "
                       f"nivel={huerfanos_niv}, ciclo={huerfanos_cic}")

    n_neg = int(fact["flag_tasa_negativa"].sum())
    print(f"\nDim_Entidad: {len(dim_entidad)} filas")
    print(f"Dim_Nivel: {len(dim_nivel)} filas")
    print(f"Dim_Tiempo: {len(dim_tiempo)} filas")
    print(f"Fact_Abandono: {len(fact)} filas")
    print(f"Tasa de abandono: {fact['tasa_abandono'].min():.1f} a "
          f"{fact['tasa_abandono'].max():.1f} %; "
          f"negativas con flag: {n_neg} de {len(fact)}")

    if errores:
        print("\nERRORES DE VALIDACIÓN:")
        for e in errores:
            print(" -", e)
        raise SystemExit(1)

    dim_entidad.to_csv(PROCESSED / "dim_entidad.csv", index=False)
    dim_nivel.to_csv(PROCESSED / "dim_nivel.csv", index=False)
    dim_tiempo.to_csv(PROCESSED / "dim_tiempo.csv", index=False)
    fact.to_csv(PROCESSED / "fact_abandono.csv", index=False)
    print("\nArchivos escritos en data/processed/:")
    print(" - dim_entidad.csv, dim_nivel.csv, dim_tiempo.csv, fact_abandono.csv")
    print("Validaciones R1-R6: OK")


if __name__ == "__main__":
    main()
