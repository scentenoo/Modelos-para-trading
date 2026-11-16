# Sensibilidad al costo: el spread de cada época

Generado el 2026-11-16 con `recostear.py`. Vuelve a costear las operaciones guardadas con el spread del trimestre en que ocurrieron, medido con cotizaciones de ese trimestre. No entrena nada y no incluye la muestra final.

## 1. Cuánto costaba operar cada año

Mediana, entre símbolos, del spread de cada año en horario normal, y el mismo dato frente al spread que se usa hoy para toda la historia.

| Año | Spread mediano | Frente al de hoy | Símbolo que más cambia |
| --- | --- | --- | --- |
| 2016 | 1,89 bps | 0,64 veces | GOOGL (4,5 veces) |
| 2017 | 1,80 bps | 0,56 veces | GOOGL (3,6 veces) |
| 2018 | 2,21 bps | 0,75 veces | GOOGL (4,8 veces) |
| 2019 | 1,92 bps | 0,68 veces | GOOGL (3,9 veces) |
| 2020 | 2,79 bps | 0,95 veces | GOOGL (6,2 veces) |
| 2021 | 1,84 bps | 0,79 veces | GOOGL (5,9 veces) |
| 2022 | 2,35 bps | 0,99 veces | NFLX (4,9 veces) |
| 2023 | 1,98 bps | 0,84 veces | AVGO (4,3 veces) |
| 2024 | 2,24 bps | 0,99 veces | NFLX (4,9 veces) |

Primer trimestre de 2020: el spread mediano fue 0,94 veces el de hoy. Solo en marzo de 2020 (144 muestras): 2,13 veces.

**Spread y volatilidad del día:** cuando la volatilidad del día sube 1%, el spread sube 0,42% (t 37,2, con 15.108 muestras; explica el 9% de la variación dentro de cada símbolo y trimestre). Con esa elasticidad se corrige el spread de cada operación.

## Horizonte de 30 minutos (2020–2024)

| Competidor | Operaciones | Costo de hoy | Neta | t | Costo de la época | Neta | t | Neta con el doble | t |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 201.985 | 1,93 | -1,87 | -11,56 | 2,57 | -2,51 | -15,51 | -5,08 | -31,09 |
| B · v2, mismas operaciones | 44.494 | 1,54 | 0,42 | 0,91 | 3,41 | -1,45 | -3,07 | -4,85 | -9,91 |
| B · v2 calibrada, mismas operaciones | 26.661 | 1,45 | 0,94 | 1,61 | 3,49 | -1,10 | -1,89 | -4,60 | -7,71 |
| B · v2 con filtro, mismas operaciones | 40.763 | 1,48 | 0,21 | 0,47 | 3,58 | -1,89 | -4,22 | -5,48 | -11,30 |
| B · v2, volviendo a decidir | 37.023 | — | — | — | 1,80 | 0,08 | 0,20 | -1,72 | -4,16 |
| B · v2 calibrada, volviendo a decidir | 20.661 | — | — | — | 1,72 | 0,56 | 0,99 | -1,16 | -2,04 |

Versión calibrada, por año (ganancia neta por operación; entre paréntesis, operaciones):

| Año | Costo de hoy | Costo de la época | Neta con el costo de hoy | Mismas operaciones, costo de la época | Volviendo a decidir |
| --- | --- | --- | --- | --- | --- |
| 2020 | 1,38 | 4,82 | 2,51 (4.008) | -0,93 | 3,74 (1.408) |
| 2021 | 1,34 | 3,49 | 0,60 (3.246) | -1,55 | -0,91 (2.380) |
| 2022 | 1,57 | 3,62 | 1,52 (12.542) | -0,53 | 0,94 (9.740) |
| 2023 | 1,37 | 2,35 | -1,35 (4.618) | -2,33 | 0,15 (5.281) |
| 2024 | 1,29 | 2,79 | 0,10 (2.247) | -1,40 | -0,74 (1.852) |

Marzo de 2020, versión calibrada: 1.069 operaciones; costo de hoy 1,45 bps y de la época 5,56; ganancia total 953 bps con el costo de hoy y -3.443 con el de la época.

## Horizonte de 60 minutos (2020–2024)

| Competidor | Operaciones | Costo de hoy | Neta | t | Costo de la época | Neta | t | Neta con el doble | t |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · Referencia | 184.201 | 2,40 | -2,40 | -9,06 | 2,76 | -2,76 | -10,38 | -5,52 | -20,63 |
| B · v2, mismas operaciones | 48.635 | 1,91 | 1,20 | 1,88 | 3,19 | -0,07 | -0,11 | -3,26 | -5,31 |
| B · v2 calibrada, mismas operaciones | 25.272 | 1,70 | 2,07 | 2,29 | 3,26 | 0,51 | 0,57 | -2,75 | -3,13 |
| B · v2 con filtro, mismas operaciones | 38.167 | 1,87 | 1,17 | 1,58 | 3,41 | -0,38 | -0,52 | -3,79 | -5,25 |
| B · v2, volviendo a decidir | 49.671 | — | — | — | 2,08 | 0,46 | 0,85 | -1,61 | -2,99 |
| B · v2 calibrada, volviendo a decidir | 25.344 | — | — | — | 1,84 | 1,00 | 1,40 | -0,85 | -1,18 |

Versión calibrada, por año (ganancia neta por operación; entre paréntesis, operaciones):

| Año | Costo de hoy | Costo de la época | Neta con el costo de hoy | Mismas operaciones, costo de la época | Volviendo a decidir |
| --- | --- | --- | --- | --- | --- |
| 2020 | 1,62 | 4,34 | 9,71 (4.574) | 6,99 | 9,58 (2.882) |
| 2021 | 1,70 | 3,08 | 0,16 (4.582) | -1,22 | -0,15 (5.468) |
| 2022 | 1,84 | 3,32 | 0,84 (9.941) | -0,63 | 0,24 (9.258) |
| 2023 | 1,55 | 2,34 | -1,34 (4.229) | -2,12 | -1,03 (5.598) |
| 2024 | 1,40 | 2,78 | 2,25 (1.946) | 0,87 | 0,96 (2.138) |

Marzo de 2020, versión calibrada: 974 operaciones; costo de hoy 1,78 bps y de la época 5,24; ganancia total 25.532 bps con el costo de hoy y 22.171 con el de la época.
