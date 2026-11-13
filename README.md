#  Índice de Prioridad para Permanencia Educativa

## Descripción del Proyecto
Proyecto de BI (Inteligencia de negocios) que analiza datos educativos de la SEP, datos del INEGI y CONEVAL para identificar qué entidades y municipios requieren intervención prioritaria.

##  Pregunta Ejecutiva Central
**¿Qué entidades o municipios presentan condiciones que justifican priorizar políticas para permanencia educativa?**

##  Equipo Scrum
- **Scrum Master:** Angel Lozano
- **Development Team:** Angel Lozano, Gaby Perez, Ivan, Naim, Fernando


## Fuentes de datos

- **SEP**: matrícula por entidad, 2,541 filas. Archivo crudo solo en local.
- **INEGI**: tasas de abandono por entidad y nivel, 128 filas limpias
  (32 entidades × 4 niveles, 8 ciclos de 2000/2001 a 2023/2024).
- **CONEVAL (medición de pobreza 2020)**: microdatos a nivel persona,
  315,619 registros. La pobreza estatal se calcula ponderando por `factor`:
  `pct = 100 * sum(factor * pobreza) / sum(factor)`. Pobreza nacional
  ponderada: 44.46%. Los datos crudos de CONEVAL son solo locales y están
  en el `.gitignore`; en GitHub solo están los resúmenes pequeños
  (`coneval_estatal.csv`, 32 filas, y `coneval_resumen.json`).

## Modelo dimensional (Sprint 3, US-08)

Esquema en estrella en `data/processed/`, generado por
`notebooks/04_modelo_dimensional.py`:

- `dim_entidad.csv` (32), `dim_nivel.csv` (4), `dim_tiempo.csv` (8)
- `fact_abandono.csv` (1,024 filas: 32 entidades × 4 niveles × 8 ciclos)

La pobreza 2020 vive solo en `Dim_Entidad`, no en el hecho. Las 66 tasas
de abandono negativas se conservan con `flag_tasa_negativa = 1`.
Diccionario completo en `docs/diccionario_de_datos.md`.
