# Modelo de velas: competidor B (paso 2.6)

Generado el 2026-11-16 con `modelo_velas.py`. Validación hacia adelante: cada año de 2019 a 2024 se predice con un modelo entrenado solo con los años anteriores. No incluye la muestra final.

Unidades: bps por operación (1 bps = 0,01%). Costo: un spread completo por operación. Los estadísticos t agrupan por día; por encima de 2 el resultado se distingue de cero.

Variantes probadas hasta ahora: 6 (tres modelos por dos horizontes). La búsqueda de hiperparámetros de la v2 no suma variantes porque elige con años anteriores al de prueba.

## Horizonte de 30 minutos (23 acciones operables)

### ¿El modelo ordena bien las acciones?

Correlación entre el orden predicho y el orden real en cada momento (0 = azar). Mide la señal antes de costos, en las 50 acciones.

| Modelo | Correlación de rangos | t |
| --- | --- | --- |
| LightGBM | 0,0170 | 11,09 |
| LightGBM v2 (comparativas y búsqueda) | 0,0190 | 13,30 |
| Regresión logística (base) | 0,0109 | 6,76 |

### Operando cuando la ganancia esperada supera el costo

| Competidor | Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 242.061 | 1.497 de 1497 | 50,0% | 0,06 | 1,93 | -1,88 | -13,45 | -3,81 | — |
| B · LightGBM | 36.414 | 1.492 de 1497 | 51,6% | 1,76 | 1,44 | 0,32 | 0,56 | -1,12 | 11,49 |
| B · LightGBM v2 (comparativas y búsqueda) | 49.056 | 1.495 de 1497 | 51,4% | 1,83 | 1,52 | 0,31 | 0,72 | -1,21 | 11,48 |
| B · Regresión logística (base) | 2.228 | 864 de 1497 | 52,5% | 0,66 | 0,99 | -0,34 | -0,17 | -1,33 | 13,25 |

Ganancia neta por operación, por año (entre paréntesis, operaciones):

| Año | LightGBM | LightGBM v2 | v2 con costo doble | Elección de la búsqueda (v2) |
| --- | --- | --- | --- | --- |
| 2019 | -1,66 (4.317) | -0,81 (4.562) | -2,20 | 31 hojas, 300 árboles |
| 2020 | 1,73 (9.788) | 0,46 (11.362) | -1,09 | 31 hojas, 500 árboles |
| 2021 | 1,09 (4.037) | 0,34 (4.318) | -1,04 | 31 hojas, 300 árboles |
| 2022 | 0,55 (9.620) | 1,06 (15.238) | -0,56 | 127 hojas, 500 árboles |
| 2023 | -1,17 (4.947) | -0,75 (8.517) | -2,25 | 127 hojas, 500 árboles |
| 2024 | -0,52 (3.705) | 0,49 (5.059) | -0,95 | 31 hojas, 500 árboles |

Si se operara todo sin filtrar por costo, por décimas de la predicción de LightGBM v2 (acciones operables):

| Décima de la predicción | Predicción media | Retorno relativo real |
| --- | --- | --- |
| 1 | -2,99 | -1,68 |
| 2 | -1,09 | -0,51 |
| 3 | -0,59 | -0,27 |
| 4 | -0,33 | -0,19 |
| 5 | -0,16 | 0,14 |
| 6 | -0,02 | 0,04 |
| 7 | 0,13 | 0,12 |
| 8 | 0,32 | 0,39 |
| 9 | 0,65 | 0,49 |
| 10 | 2,32 | 1,36 |

Variables que más usa LightGBM v2: `sector_n` (5%), `beta_60d` (3%), `mkt_ret_60` (3%), `ret_noche` (3%), `ret_20d` (3%), `mkt_ret_apertura` (3%), `dolares_20d` (3%), `ret_ayer` (3%).

## Horizonte de 60 minutos (36 acciones operables)

### ¿El modelo ordena bien las acciones?

Correlación entre el orden predicho y el orden real en cada momento (0 = azar). Mide la señal antes de costos, en las 50 acciones.

| Modelo | Correlación de rangos | t |
| --- | --- | --- |
| LightGBM | 0,0198 | 9,52 |
| LightGBM v2 (comparativas y búsqueda) | 0,0218 | 10,99 |
| Regresión logística (base) | 0,0101 | 4,91 |

### Operando cuando la ganancia esperada supera el costo

| Competidor | Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 220.726 | 1.497 de 1497 | 49,9% | 0,03 | 2,41 | -2,38 | -10,40 | -4,79 | — |
| B · LightGBM | 31.147 | 1.496 de 1497 | 51,3% | 2,93 | 1,68 | 1,25 | 1,29 | -0,44 | 9,26 |
| B · LightGBM v2 (comparativas y búsqueda) | 51.847 | 1.497 de 1497 | 51,4% | 2,87 | 1,89 | 0,99 | 1,63 | -0,90 | 9,40 |
| B · Regresión logística (base) | 4.826 | 1.208 de 1497 | 49,6% | -1,35 | 1,16 | -2,51 | -1,25 | -3,66 | 9,97 |

Ganancia neta por operación, por año (entre paréntesis, operaciones):

| Año | LightGBM | LightGBM v2 | v2 con costo doble | Elección de la búsqueda (v2) |
| --- | --- | --- | --- | --- |
| 2019 | -2,90 (4.699) | -2,29 (3.212) | -3,79 | 7 hojas, 500 árboles |
| 2020 | 8,22 (8.066) | 4,38 (15.449) | 2,33 | 127 hojas, 500 árboles |
| 2021 | -0,47 (4.062) | 0,47 (7.142) | -1,38 | 127 hojas, 300 árboles |
| 2022 | -0,12 (7.433) | -0,20 (13.784) | -2,18 | 127 hojas, 500 árboles |
| 2023 | -3,64 (3.688) | -1,69 (7.749) | -3,43 | 127 hojas, 500 árboles |
| 2024 | 0,75 (3.199) | 0,72 (4.511) | -0,91 | 31 hojas, 500 árboles |

Si se operara todo sin filtrar por costo, por décimas de la predicción de LightGBM v2 (acciones operables):

| Décima de la predicción | Predicción media | Retorno relativo real |
| --- | --- | --- |
| 1 | -4,63 | -2,28 |
| 2 | -1,81 | -0,80 |
| 3 | -1,06 | -0,32 |
| 4 | -0,64 | -0,17 |
| 5 | -0,34 | -0,22 |
| 6 | -0,07 | 0,04 |
| 7 | 0,21 | 0,33 |
| 8 | 0,56 | 0,39 |
| 9 | 1,14 | 0,47 |
| 10 | 3,75 | 1,79 |

Variables que más usa LightGBM v2: `sector_n` (6%), `beta_60d` (4%), `ret_20d` (4%), `ret_noche` (4%), `ret_ayer` (4%), `dolares_20d` (4%), `p_ret_20d` (3%), `p_ret_ayer` (3%).
