# Calibración del modelo de velas (paso 2.6.c)

Generado el 2026-11-16 con `calibracion.py`, sobre las predicciones guardadas de LightGBM v2. La pendiente de cada año se calcula solo con años de prueba anteriores. No incluye la muestra final.

Unidades: bps por operación. Los t agrupan por día. La comparación va de 2020 en adelante, porque 2019 no tiene años anteriores para calibrar.

Variantes probadas hasta ahora: 8 (las 6 de `modelo_velas.py` más la calibrada en cada horizonte).

## Horizonte de 30 minutos (23 acciones operables, 2020–2024)

| Competidor | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 201.985 | 50,0% | 0,07 | 1,93 | -1,87 | -11,56 | -3,80 | -23,53 | — |
| B · LightGBM v2 | 44.494 | 51,4% | 1,96 | 1,54 | 0,42 | 0,91 | -1,11 | -2,37 | 9,92 |
| B · LightGBM v2 calibrado | 26.661 | 51,7% | 2,39 | 1,45 | 0,94 | 1,61 | -0,51 | -0,88 | 11,01 |

Por año (ganancia neta por operación; entre paréntesis, operaciones):

| Año | Pendiente | v2 | v2 calibrado | Calibrado con costo doble |
| --- | --- | --- | --- | --- |
| 2020 | 0,51 | 0,46 (11.362) | 2,51 (4.008) | 1,13 |
| 2021 | 0,83 | 0,34 (4.318) | 0,60 (3.246) | -0,75 |
| 2022 | 0,83 | 1,06 (15.238) | 1,52 (12.542) | -0,05 |
| 2023 | 0,63 | -0,75 (8.517) | -1,35 (4.618) | -2,72 |
| 2024 | 0,58 | 0,49 (5.059) | 0,10 (2.247) | -1,19 |

Trimestres con ganancia neta positiva (calibrado): 11 de 20.

## Horizonte de 60 minutos (36 acciones operables, 2020–2024)

| Competidor | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t con costo doble | t contra la referencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 184.201 | 49,8% | 0,00 | 2,40 | -2,40 | -9,06 | -4,81 | -18,13 | — |
| B · LightGBM v2 | 48.635 | 51,4% | 3,12 | 1,91 | 1,20 | 1,88 | -0,71 | -1,13 | 8,39 |
| B · LightGBM v2 calibrado | 25.272 | 51,4% | 3,76 | 1,70 | 2,07 | 2,29 | 0,37 | 0,41 | 8,92 |

Por año (ganancia neta por operación; entre paréntesis, operaciones):

| Año | Pendiente | v2 | v2 calibrado | Calibrado con costo doble |
| --- | --- | --- | --- | --- |
| 2020 | 0,39 | 4,38 (15.449) | 9,71 (4.574) | 8,08 |
| 2021 | 0,75 | 0,47 (7.142) | 0,16 (4.582) | -1,54 |
| 2022 | 0,74 | -0,20 (13.784) | 0,84 (9.941) | -1,00 |
| 2023 | 0,64 | -1,69 (7.749) | -1,34 (4.229) | -2,89 |
| 2024 | 0,58 | 0,72 (4.511) | 2,25 (1.946) | 0,85 |

Trimestres con ganancia neta positiva (calibrado): 10 de 20.
