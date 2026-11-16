# Modelo de velas: competidor B (paso 2.6)

Generado el 2026-11-15 con `modelo_velas.py`. Validación hacia adelante: cada año de 2019 a 2024 se predice con un modelo entrenado solo con los años anteriores. No incluye la muestra final.

Unidades: bps por operación (1 bps = 0,01%). Costo: un spread completo por operación. Los estadísticos t agrupan por día; por encima de 2 el resultado se distingue de cero.

Variantes probadas hasta ahora: 4 (dos modelos por dos horizontes), con parámetros fijados de antemano.

## Horizonte de 30 minutos (23 acciones operables)

### ¿El modelo ordena bien las acciones?

Correlación entre el orden predicho y el orden real en cada momento (0 = azar). Mide la señal antes de costos, en las 50 acciones.

| Modelo | Correlación de rangos | t |
| --- | --- | --- |
| LightGBM | 0,0170 | 11,09 |
| Regresión logística (base) | 0,0109 | 6,76 |

### Operando cuando la ganancia esperada supera el costo

| Competidor | Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 242.061 | 1.497 de 1497 | 50,0% | 0,06 | 1,93 | -1,88 | -13,45 | -3,81 | — |
| B · LightGBM | 36.414 | 1.492 de 1497 | 51,6% | 1,76 | 1,44 | 0,32 | 0,56 | -1,12 | 11,49 |
| B · Regresión logística (base) | 2.228 | 864 de 1497 | 52,5% | 0,66 | 0,99 | -0,34 | -0,17 | -1,33 | 13,25 |

Ganancia neta por operación de LightGBM, por año (entre paréntesis, operaciones):

| Año | Ganancia neta | Con costo doble |
| --- | --- | --- |
| 2019 | -1,66 (4.317) | -3,04 |
| 2020 | 1,73 (9.788) | 0,19 |
| 2021 | 1,09 (4.037) | -0,29 |
| 2022 | 0,55 (9.620) | -0,91 |
| 2023 | -1,17 (4.947) | -2,53 |
| 2024 | -0,52 (3.705) | -1,89 |

Si se operara todo sin filtrar por costo, por décimas de la predicción de LightGBM (acciones operables):

| Décima de la predicción | Predicción media | Retorno relativo real |
| --- | --- | --- |
| 1 | -2,30 | -1,25 |
| 2 | -0,88 | -0,38 |
| 3 | -0,48 | -0,36 |
| 4 | -0,28 | -0,12 |
| 5 | -0,15 | 0,08 |
| 6 | -0,04 | 0,01 |
| 7 | 0,08 | 0,14 |
| 8 | 0,22 | 0,23 |
| 9 | 0,46 | 0,41 |
| 10 | 1,77 | 1,12 |

Variables que más usa LightGBM: `sector_n` (7%), `ret_noche` (5%), `beta_60d` (5%), `ret_ayer` (5%), `ret_20d` (5%), `mkt_ret_apertura` (4%), `mkt_ret_60` (4%), `dolares_20d` (4%).

## Horizonte de 60 minutos (36 acciones operables)

### ¿El modelo ordena bien las acciones?

Correlación entre el orden predicho y el orden real en cada momento (0 = azar). Mide la señal antes de costos, en las 50 acciones.

| Modelo | Correlación de rangos | t |
| --- | --- | --- |
| LightGBM | 0,0198 | 9,52 |
| Regresión logística (base) | 0,0101 | 4,91 |

### Operando cuando la ganancia esperada supera el costo

| Competidor | Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 220.726 | 1.497 de 1497 | 49,9% | 0,03 | 2,41 | -2,38 | -10,40 | -4,79 | — |
| B · LightGBM | 31.147 | 1.496 de 1497 | 51,3% | 2,93 | 1,68 | 1,25 | 1,29 | -0,44 | 9,26 |
| B · Regresión logística (base) | 4.826 | 1.208 de 1497 | 49,6% | -1,35 | 1,16 | -2,51 | -1,25 | -3,66 | 9,97 |

Ganancia neta por operación de LightGBM, por año (entre paréntesis, operaciones):

| Año | Ganancia neta | Con costo doble |
| --- | --- | --- |
| 2019 | -2,90 (4.699) | -4,56 |
| 2020 | 8,22 (8.066) | 6,44 |
| 2021 | -0,47 (4.062) | -2,19 |
| 2022 | -0,12 (7.433) | -1,86 |
| 2023 | -3,64 (3.688) | -5,15 |
| 2024 | 0,75 (3.199) | -0,77 |

Si se operara todo sin filtrar por costo, por décimas de la predicción de LightGBM (acciones operables):

| Décima de la predicción | Predicción media | Retorno relativo real |
| --- | --- | --- |
| 1 | -3,05 | -1,85 |
| 2 | -1,33 | -0,30 |
| 3 | -0,83 | -0,49 |
| 4 | -0,55 | -0,20 |
| 5 | -0,33 | -0,19 |
| 6 | -0,13 | 0,05 |
| 7 | 0,08 | 0,11 |
| 8 | 0,34 | 0,27 |
| 9 | 0,71 | 0,56 |
| 10 | 2,37 | 1,28 |

Variables que más usa LightGBM: `sector_n` (8%), `ret_noche` (6%), `beta_60d` (6%), `ret_20d` (6%), `ret_ayer` (6%), `dolares_20d` (5%), `mkt_ret_apertura` (5%), `vol_20d` (5%).
