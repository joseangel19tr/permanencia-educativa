# Diccionario de datos — Permanencia educativa

Proyecto: permanencia educativa / abandono escolar en México.
Fuentes: SEP, INEGI y CONEVAL (medición de pobreza 2020).
Última actualización: 10 nov 2026 — Sprint 3 (modelo dimensional US-08).
Estado: el dataset analítico y el modelo dimensional están verificados; el
mapeo Renglón → nivel de la SEP cruda sigue sin verificar (Fase 2).

## Convenciones

- `ent`: clave de entidad federativa a 2 dígitos, como texto con cero a la
  izquierda (`"07"` = Chiapas). En pandas se lee con `dtype={'ent': str}`;
  sin eso se convierte a entero y se pierde el cero, aunque los joins
  siguen funcionando porque todas las tablas usan el mismo formato.
- Porcentajes: valores en puntos porcentuales (0–100), no proporciones.
- La pobreza es solo de 2020. No va en el hecho: vive en `Dim_Entidad` y se
  une por `ent`. En el dataset analítico se repite igual en los 8 ciclos y
  los 4 niveles; dejarla en el hecho haría parecer que se midió en cada ciclo.
- Las tasas de abandono negativas se conservan, no se borran ni se ponen en
  cero: indican crecimiento o reingreso neto. Se marcan con
  `flag_tasa_negativa = 1` (66 de 1,024 celdas del hecho).

## 1. Fuentes crudas (solo en local, nunca en GitHub)

| Fuente | Archivo | Filas × columnas | Nota |
|---|---|---|---|
| SEP | Reporte de matrícula | 2,541 × 46 | Encabezados enredados; ciclos desde 1990-1991 en la fila 2; grano ENT × Renglón × ciclo; incluye total nacional (33 valores de ENT). El mapeo Renglón → nivel aún no está verificado. |
| INEGI | Tasas de abandono por entidad y nivel | 142 crudas → 128 limpias, 10 columnas | Encabezados en fila 5, 6 duplicados, 42 entidades con basura; se quitaron 14 filas (total nacional y notas al pie). |
| CONEVAL | `pobreza_municipal_2020.csv` | 315,619 × 74 | **Microdatos a nivel persona, no agregado municipal.** No existe ninguna columna `pp_pobre` ni `pob_pobre`. Columnas clave: `ent`, `pobreza` (binaria 0/1), `pobreza_e`, `pobreza_m`, `factor` (ponderador), `folioviv`, `foliohog`, `ic_rezedu`, `ic_asalud`, `ic_segsoc`. |

La pobreza estatal se calcula ponderando por `factor`:
`pct = 100 * sum(factor * pobreza) / sum(factor)` por entidad.
Pobreza nacional ponderada 2020: **44.46%** (oficial CONEVAL ~43.9%).
Extrema + moderada = total en los 32 estados. Máxima: Chiapas 74.43%,
Guerrero 65.62%, Oaxaca 63.83%. Mínima: Nuevo León 19.70%,
Baja California 23.12%, Coahuila 23.58%.

## 2. Archivos procesados — `data/processed/`

### 2.1 `dataset_analitico_v1.csv` — 128 filas × 16 columnas, 0 NaN en `pct_pobreza_estatal`

Grano: una fila por entidad × nivel educativo (32 × 4). Verificado 9 nov 2026
(commit `50ca1de`, merge `b69012a`).

| Columna | Tipo | Descripción |
|---|---|---|
| `Entidad federativa` | texto | Nombre de la entidad (sin `.title()`; se conservan "Coahuila de Zaragoza", "Ciudad de México", "Michoacán de Ocampo", "Veracruz de Ignacio de la Llave") |
| `Nivel educativo` | texto | Primaria, Secundaria, Media superior, Superior |
| `2000/2001` … `2023/2024` | numérico | Tasa de abandono (%) en cada ciclo: 2000/2001, 2005/2006, 2010/2011, 2015/2016, 2020/2021, 2021/2022, 2022/2023, 2023/2024. Rango −6.7 a 24.4 |
| `ent` | texto, 2 dígitos | Clave de entidad, llave de join con CONEVAL |
| `n_personas` | entero | Personas encuestadas en CONEVAL por entidad (total 315,619) |
| `poblacion_expandida` | numérico | Población expandida 2020 por entidad (total 127,427,694) |
| `pct_pobreza_estatal` | numérico | % de población en pobreza 2020, ponderado por `factor` (19.70–74.43) |
| `pct_pobreza_extrema_estatal` | numérico | % en pobreza extrema 2020 |
| `pct_pobreza_moderada_estatal` | numérico | % en pobreza moderada 2020 |

### 2.2 `coneval_estatal.csv` — 32 filas × 6 columnas, 0 NaN

Una fila por entidad. Generado por `src/extraer_resumen_coneval.py` (v2).

| Columna | Tipo | Descripción |
|---|---|---|
| `ent` | texto, 2 dígitos | Clave de entidad |
| `n_personas` | entero | Personas encuestadas por entidad |
| `poblacion_expandida` | numérico | Población expandida 2020 |
| `pct_pobreza_estatal` | numérico | % pobreza total 2020, ponderado por `factor` |
| `pct_pobreza_extrema_estatal` | numérico | % pobreza extrema 2020 |
| `pct_pobreza_moderada_estatal` | numérico | % pobreza moderada 2020 |

### 2.3 `coneval_resumen.json`

Resumen del archivo CONEVAL: modo microdatos, 32 valores únicos de `ent`,
`pobreza` binaria 0/1 (25 nulos en 315,619 filas).

## 3. Modelo dimensional — Sprint 3 (US-08)

Esquema en estrella, generado por `notebooks/04_modelo_dimensional.py`
a partir de `dataset_analitico_v1.csv` y `coneval_estatal.csv`.
Validaciones R1–R6: 0 duplicados en la llave, 0 nulos, 0 huérfanos en los joins.
La SEP queda como segundo hecho (`Fact_Matrícula`) para la Fase 2.

### 3.1 `dim_entidad.csv` — 32 filas

| Columna | Tipo | Descripción |
|---|---|---|
| `ent` | texto, 2 dígitos | Llave primaria |
| `nombre_entidad` | texto | Nombre de la entidad |
| `n_personas` | entero | Personas encuestadas en CONEVAL |
| `poblacion_expandida_2020` | numérico | Población expandida 2020 |
| `pct_pobreza_2020` | numérico | % pobreza total 2020 (ej. Chiapas 74.43) |
| `pct_pobreza_extrema_2020` | numérico | % pobreza extrema 2020 (ej. Chiapas 28.30) |
| `pct_pobreza_moderada_2020` | numérico | % pobreza moderada 2020 (ej. Chiapas 46.14) |

### 3.2 `dim_nivel.csv` — 4 filas

| Columna | Tipo | Descripción |
|---|---|---|
| `id_nivel` | entero | Llave primaria: 1 Primaria, 2 Secundaria, 3 Media superior, 4 Superior |
| `nivel_educativo` | texto | Nombre del nivel |

### 3.3 `dim_tiempo.csv` — 8 filas

| Columna | Tipo | Descripción |
|---|---|---|
| `id_ciclo` | texto | Llave primaria, igual a `ciclo` (ej. `2000/2001`) |
| `ciclo` | texto | Ciclo escolar |
| `anio_inicio` | entero | Año de inicio del ciclo |
| `anio_fin` | entero | Año de fin del ciclo |

Los ciclos no son anuales continuos: hay saltos de 5 años hasta 2015/2016
y luego anuales (2020/2021, 2021/2022, 2022/2023, 2023/2024).

### 3.4 `fact_abandono.csv` — 1,024 filas (32 × 4 × 8)

Grano: una fila por entidad × nivel × ciclo.

| Columna | Tipo | Descripción |
|---|---|---|
| `ent` | texto, 2 dígitos | Llave foránea a `Dim_Entidad` |
| `id_nivel` | entero | Llave foránea a `Dim_Nivel` |
| `id_ciclo` | texto | Llave foránea a `Dim_Tiempo` |
| `tasa_abandono` | numérico | Tasa de abandono (%) en ese ciclo. Rango −6.7 a 24.4 |
| `flag_tasa_negativa` | entero 0/1 | 1 cuando `tasa_abandono < 0` (66 filas); la tasa se conserva |

Ejemplo verificado: Chiapas, Media superior, abandono 13.4% en 2000/2001
y 9.5% en 2023/2024.
