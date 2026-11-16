# Filtro de operaciones sobre el modelo de velas (meta-labeling, paso 2.6)

Generado el 2026-11-16 con `filtro.py`. El modelo de velas (LightGBM v2) da la dirección y un clasificador decide si se opera. Para cada año de prueba, el filtro se entrena con años anteriores y elige su umbral con el año inmediatamente anterior. No incluye la muestra final.

Unidades: bps por operación. Los t agrupan por día. Etiqueta: la operación gana más de 2 veces el spread. Fracciones posibles: 50%, 35%, 25%, 15%, 10% de las candidatas.

Variantes probadas hasta ahora: 10 (las 8 anteriores más el filtro en cada horizonte).

## Horizonte de 30 minutos (23 acciones operables)

### De 2020 a 2024

| Competidor | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 201.985 | 50,0% | 0,07 | 1,93 | -1,87 | -11,56 | -3,80 | -23,53 | — |
| B · LightGBM v2 | 44.494 | 51,4% | 1,96 | 1,54 | 0,42 | 0,91 | -1,11 | -2,37 | 9,92 |
| B · LightGBM v2 calibrado | 26.661 | 51,7% | 2,39 | 1,45 | 0,94 | 1,61 | -0,51 | -0,88 | 11,01 |
| B · LightGBM v2 con filtro | 40.763 | 51,3% | 1,69 | 1,48 | 0,21 | 0,47 | -1,27 | -2,85 | 10,26 |

### De 2021 a 2024

| Competidor | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 161.376 | 49,9% | -0,08 | 1,93 | -2,01 | -13,15 | -3,95 | -25,79 | — |
| B · LightGBM v2 | 33.132 | 51,3% | 1,95 | 1,53 | 0,41 | 0,83 | -1,12 | -2,25 | 11,69 |
| B · LightGBM v2 calibrado | 22.653 | 51,5% | 2,13 | 1,47 | 0,66 | 1,04 | -0,81 | -1,27 | 12,14 |
| B · LightGBM v2 con filtro | 26.115 | 51,2% | 1,71 | 1,43 | 0,28 | 0,52 | -1,15 | -2,16 | 11,85 |

### Por año

El AUC mide si el filtro distingue las operaciones que ganan de las que no (0,5 = azar), en el año de prueba.

| Año | Filas de entrenamiento | Candidatas que cumplen la etiqueta | AUC | Fracción elegida | Operaciones | Ganancia neta | Con costo doble | Calibrado, para comparar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 62.744 | 45,6% | 0,534 | 10% | 14.648 | 0,08 | -1,48 | 2,51 (4.008) |
| 2021 | 125.488 | 43,4% | 0,549 | 10% | 2.332 | -0,60 | -1,95 | 0,60 (3.246) |
| 2022 | 188.991 | 46,1% | 0,529 | 10% | 16.297 | 0,64 | -0,85 | 1,52 (12.542) |
| 2023 | 252.494 | 43,8% | 0,538 | 10% | 2.956 | -0,93 | -2,27 | -1,35 (4.618) |
| 2024 | 315.722 | 44,3% | 0,539 | 10% | 4.530 | 0,23 | -1,11 | 0,10 (2.247) |

Trimestres con ganancia neta positiva: 9 de 20.

Variables que más usa el filtro: movimiento esperado frente al spread (47%), predicción frente al spread (13%), volatilidad de SPY (12%), volumen relativo (6%), volatilidad de 20 días (5%), predicción (4%).

### Probabilidad calibrada y resultado, para el tamaño de posición

Operaciones del filtro en quintos de su probabilidad calibrada. Kelly necesita la probabilidad y cuánto se gana y se pierde.

| Quinto | Probabilidad media | Cumplen la etiqueta | Ganancia media cuando gana | Pérdida media cuando pierde | Ganancia neta |
| --- | --- | --- | --- | --- | --- |
| 1 | 48,2% | 48,8% | 46,8 | -47,7 | -0,41 |
| 2 | 49,3% | 48,8% | 50,9 | -52,2 | -0,39 |
| 3 | 49,9% | 49,4% | 44,1 | -44,7 | 0,41 |
| 4 | 50,5% | 49,0% | 45,6 | -44,4 | 0,73 |
| 5 | 51,7% | 49,2% | 52,5 | -51,6 | 0,70 |

## Horizonte de 60 minutos (36 acciones operables)

### De 2020 a 2024

| Competidor | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 184.201 | 49,8% | 0,00 | 2,40 | -2,40 | -9,06 | -4,81 | -18,13 | — |
| B · LightGBM v2 | 48.635 | 51,4% | 3,12 | 1,91 | 1,20 | 1,88 | -0,71 | -1,13 | 8,39 |
| B · LightGBM v2 calibrado | 25.272 | 51,4% | 3,76 | 1,70 | 2,07 | 2,29 | 0,37 | 0,41 | 8,92 |
| B · LightGBM v2 con filtro | 38.167 | 51,6% | 3,04 | 1,87 | 1,17 | 1,58 | -0,71 | -0,97 | 8,51 |

### De 2021 a 2024

| Competidor | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 147.145 | 49,6% | -0,22 | 2,40 | -2,62 | -10,98 | -5,02 | -21,04 | — |
| B · LightGBM v2 | 33.186 | 50,8% | 1,57 | 1,85 | -0,28 | -0,42 | -2,13 | -3,25 | 9,14 |
| B · LightGBM v2 calibrado | 20.698 | 50,8% | 2,09 | 1,71 | 0,38 | 0,43 | -1,33 | -1,50 | 9,79 |
| B · LightGBM v2 con filtro | 23.463 | 51,6% | 2,06 | 1,70 | 0,36 | 0,46 | -1,35 | -1,72 | 9,90 |

### Por año

El AUC mide si el filtro distingue las operaciones que ganan de las que no (0,5 = azar), en el año de prueba.

| Año | Filas de entrenamiento | Candidatas que cumplen la etiqueta | AUC | Fracción elegida | Operaciones | Ganancia neta | Con costo doble | Calibrado, para comparar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 44.640 | 47,3% | 0,528 | 10% | 14.704 | 2,46 | 0,31 | 9,71 (4.574) |
| 2021 | 89.280 | 44,5% | 0,545 | 35% | 7.490 | 0,36 | -1,40 | 0,16 (4.582) |
| 2022 | 134.460 | 46,3% | 0,524 | 10% | 10.935 | -0,57 | -2,36 | 0,84 (9.941) |
| 2023 | 179.640 | 44,9% | 0,541 | 10% | 1.608 | 3,87 | 2,40 | -1,34 (4.229) |
| 2024 | 224.625 | 44,6% | 0,540 | 10% | 3.430 | 1,65 | 0,25 | 2,25 (1.946) |

Trimestres con ganancia neta positiva: 13 de 20.

Variables que más usa el filtro: movimiento esperado frente al spread (37%), volatilidad de SPY (17%), predicción frente al spread (13%), predicción (9%), volumen relativo (6%), puesto entre las acciones del momento (5%).

### Probabilidad calibrada y resultado, para el tamaño de posición

Operaciones del filtro en quintos de su probabilidad calibrada. Kelly necesita la probabilidad y cuánto se gana y se pierde.

| Quinto | Probabilidad media | Cumplen la etiqueta | Ganancia media cuando gana | Pérdida media cuando pierde | Ganancia neta |
| --- | --- | --- | --- | --- | --- |
| 1 | 49,1% | 49,3% | 48,3 | -49,9 | -0,21 |
| 2 | 49,2% | 48,4% | 53,4 | -53,3 | -0,19 |
| 3 | 49,5% | 50,8% | 86,7 | -81,3 | 5,15 |
| 4 | 49,6% | 49,2% | 58,7 | -57,5 | 1,24 |
| 5 | 50,8% | 49,3% | 50,4 | -51,4 | -0,17 |
