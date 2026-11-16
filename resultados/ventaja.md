# Revisión de la ganancia (paso 2.8)

Generado el 2026-11-16 con `ventaja.py` sobre `datos/modelos/operaciones_calibradas_<h>.parquet`. Es descriptivo: no entrena nada y no cuenta como variante. No incluye la muestra final.

La primera parte usa `residual-edge-analyzer` sobre la ganancia neta de cada día, con bases de comparación fijadas de antemano. Unidades de la segunda parte: bps por operación; los t agrupan por día.

Advertencia del analizador: el universo son empresas que existen hoy (sesgo de supervivencia), así que el resultado no es apto para decidir por sí solo.

## Horizonte de 30 minutos (2020-01-02 a 2024-12-31, 1249 días)

**Veredicto del analizador: ventaja frágil.**

### ¿Ventaja propia o exposición al mercado?

| Base de comparación | Variación explicada (R²) | Ganancia anual sin la base | t | Ventanas de 63 días con ganancia positiva |
| --- | --- | --- | --- | --- |
| SPY | 3,2% | 2,30% | 1,75 | 64% |
| Promedio de las 50 acciones | 3,0% | 2,38% | 1,80 | 66% |
| SPY y la referencia | 3,2% | 2,23% | 1,57 | 68% |

Beta frente a SPY: -0,023 (t -3,53). El analizador pide al menos 60% de ventanas positivas para llamarlo ventaja propia.

Por régimen (cada día se etiqueta con el modelo de regímenes de su propio año de prueba):

| Régimen | Días | Ganancia anual sin la base | Días positivos |
| --- | --- | --- | --- |
| 1 | 320 | -0,78% | 47% |
| 2 | 423 | 4,20% | 53% |
| 3 | 334 | -0,57% | 52% |
| 4 | 172 | 8,92% | 58% |

### ¿Está concentrada?

Ganancia total: 25.025 bps. Los 10 mejores días aportan 18.422 bps (74%); el mejor mes, 2022-04, aporta 7.479. Días con ganancia: 51%.

| Corte | Operaciones | Ganancia neta | t | Neta con costo doble |
| --- | --- | --- | --- | --- |
| Todo el periodo | 26.661 | 0,94 | 1,61 | -0,51 |
| Sin los 10 mejores días | 26.065 | 0,25 | 0,46 | -1,20 |
| Sin 2022, el mejor año | 14.119 | 0,42 | 0,61 | -0,93 |
| Solo compras | 9.149 | 1,66 | 1,51 | 0,14 |
| Solo ventas | 17.512 | 0,56 | 0,65 | -0,86 |

Mejores días: 2022-04-27 (2.643), 2022-05-16 (2.312), 2022-02-18 (1.838), 2022-05-12 (1.791), 2020-06-16 (1.750), 2020-03-03 (1.681).

Por acción: 14 de 23 ganan. Las que más aportan: NVDA (28%), AAPL (26%), TSLA (24%), AMZN (15%), META (11%). Las que más restan: WMT (-7%), NFLX (-6%), WFC (-4%).

### ¿Selección o mercado?

Cada celda: media por operación en bps y, entre paréntesis, su t. La ganancia bruta es la suma de selección y mercado. La última columna es la ganancia neta si cada operación se cubriera con el promedio de las 50 acciones, sin contar el costo de esa cobertura.

| Operaciones | Cantidad | Ganancia bruta | Selección | Mercado | Neta | Neta con cobertura |
| --- | --- | --- | --- | --- | --- | --- |
| Todas | 26.661 | 2,39 (4,06) | 2,17 (5,31) | 0,22 (0,68) | 0,94 (1,61) | 0,72 (1,78) |
| Compras | 9.149 | 3,18 (2,91) | 3,17 (4,40) | 0,01 (0,02) | 1,66 (1,51) | 1,65 (2,29) |
| Ventas | 17.512 | 1,98 (2,29) | 1,65 (3,19) | 0,33 (0,63) | 0,56 (0,65) | 0,23 (0,45) |
| Compras, 2020 | 1.708 | 4,26 (1,53) | 5,98 (2,82) | -1,72 (-0,81) | 2,78 (0,98) | 4,50 (2,13) |
| Compras, 2021 | 1.169 | 4,19 (1,76) | 3,02 (1,62) | 1,17 (1,22) | 2,77 (1,16) | 1,60 (0,86) |
| Compras, 2022 | 4.176 | 2,95 (1,65) | 2,43 (2,47) | 0,52 (0,47) | 1,32 (0,73) | 0,81 (0,82) |
| Compras, 2023 | 1.175 | 4,47 (2,34) | 4,05 (2,73) | 0,42 (0,47) | 3,02 (1,58) | 2,60 (1,76) |
| Compras, 2024 | 921 | -0,67 (-0,21) | 0,40 (0,15) | -1,07 (-1,07) | -2,02 (-0,61) | -0,95 (-0,37) |
| Ventas, 2020 | 2.300 | 3,60 (1,50) | 3,93 (3,16) | -0,33 (-0,16) | 2,30 (0,95) | 2,63 (2,13) |
| Ventas, 2021 | 2.077 | 0,68 (0,37) | 1,54 (1,09) | -0,86 (-1,15) | -0,63 (-0,34) | 0,23 (0,17) |
| Ventas, 2022 | 8.366 | 3,15 (2,14) | 2,04 (2,53) | 1,11 (1,29) | 1,62 (1,09) | 0,51 (0,63) |
| Ventas, 2023 | 3.443 | -1,50 (-1,06) | -0,98 (-0,93) | -0,51 (-0,85) | -2,84 (-2,00) | -2,33 (-2,20) |
| Ventas, 2024 | 1.326 | 2,82 (1,36) | 2,23 (1,20) | 0,59 (1,01) | 1,57 (0,77) | 0,98 (0,53) |

## Horizonte de 60 minutos (2020-01-02 a 2024-12-31, 1249 días)

**Veredicto del analizador: ventaja frágil.**

### ¿Ventaja propia o exposición al mercado?

| Base de comparación | Variación explicada (R²) | Ganancia anual sin la base | t | Ventanas de 63 días con ganancia positiva |
| --- | --- | --- | --- | --- |
| SPY | 1,9% | 2,97% | 2,10 | 56% |
| Promedio de las 50 acciones | 1,7% | 3,02% | 2,15 | 57% |
| SPY y la referencia | 2,3% | 2,31% | 1,98 | 60% |

Beta frente a SPY: -0,017 (t -2,12). El analizador pide al menos 60% de ventanas positivas para llamarlo ventaja propia.

Por régimen (cada día se etiqueta con el modelo de regímenes de su propio año de prueba):

| Régimen | Días | Ganancia anual sin la base | Días positivos |
| --- | --- | --- | --- |
| 1 | 320 | -0,23% | 47% |
| 2 | 423 | 4,63% | 53% |
| 3 | 334 | -3,22% | 50% |
| 4 | 172 | 16,88% | 61% |

### ¿Está concentrada?

Ganancia total: 52.234 bps. Los 10 mejores días aportan 40.307 bps (77%); el mejor mes, 2020-03, aporta 25.532. Días con ganancia: 51%.

| Corte | Operaciones | Ganancia neta | t | Neta con costo doble |
| --- | --- | --- | --- | --- |
| Todo el periodo | 25.272 | 2,07 | 2,29 | 0,37 |
| Sin los 10 mejores días | 24.717 | 0,48 | 0,65 | -1,21 |
| Sin 2020, el mejor año | 20.698 | 0,38 | 0,43 | -1,33 |
| Solo compras | 9.152 | 4,68 | 2,74 | 2,96 |
| Solo ventas | 16.120 | 0,59 | 0,48 | -1,10 |

Mejores días: 2020-03-17 (7.610), 2020-03-12 (5.121), 2022-05-12 (4.530), 2022-05-06 (4.197), 2020-03-19 (3.552), 2020-03-20 (3.410).

Por acción: 23 de 36 ganan. Las que más aportan: NVDA (28%), AAPL (16%), TSLA (10%), GOOGL (8%), META (8%). Las que más restan: WMT (-4%), CRM (-3%), AVGO (-3%).

### ¿Selección o mercado?

Cada celda: media por operación en bps y, entre paréntesis, su t. La ganancia bruta es la suma de selección y mercado. La última columna es la ganancia neta si cada operación se cubriera con el promedio de las 50 acciones, sin contar el costo de esa cobertura.

| Operaciones | Cantidad | Ganancia bruta | Selección | Mercado | Neta | Neta con cobertura |
| --- | --- | --- | --- | --- | --- | --- |
| Todas | 25.272 | 3,76 (4,15) | 2,59 (4,64) | 1,17 (2,22) | 2,07 (2,29) | 0,90 (1,61) |
| Compras | 9.152 | 6,39 (3,73) | 3,79 (4,29) | 2,59 (2,07) | 4,68 (2,74) | 2,08 (2,37) |
| Ventas | 16.120 | 2,27 (1,84) | 1,91 (2,83) | 0,36 (0,44) | 0,59 (0,48) | 0,22 (0,33) |
| Compras, 2020 | 1.981 | 18,23 (3,13) | 9,14 (3,48) | 9,10 (1,92) | 16,47 (2,84) | 7,38 (2,84) |
| Compras, 2021 | 1.643 | 5,83 (2,73) | 4,04 (2,54) | 1,79 (1,76) | 4,21 (1,98) | 2,42 (1,53) |
| Compras, 2022 | 3.558 | 0,92 (0,37) | 0,60 (0,45) | 0,33 (0,20) | -0,89 (-0,36) | -1,22 (-0,93) |
| Compras, 2023 | 1.167 | 5,66 (2,17) | 4,27 (2,31) | 1,38 (0,96) | 4,06 (1,55) | 2,67 (1,44) |
| Compras, 2024 | 803 | 3,56 (1,05) | 3,56 (1,36) | -0,00 (-0,00) | 2,09 (0,61) | 2,09 (0,79) |
| Ventas, 2020 | 2.593 | 6,06 (1,95) | 4,62 (2,94) | 1,44 (0,54) | 4,54 (1,47) | 3,10 (1,99) |
| Ventas, 2021 | 2.939 | -0,35 (-0,19) | 0,43 (0,36) | -0,78 (-0,71) | -2,10 (-1,17) | -1,32 (-1,10) |
| Ventas, 2022 | 6.383 | 3,67 (1,51) | 2,35 (1,92) | 1,31 (0,82) | 1,81 (0,74) | 0,49 (0,40) |
| Ventas, 2023 | 3.062 | -1,86 (-0,84) | -0,72 (-0,51) | -1,14 (-1,01) | -3,39 (-1,52) | -2,25 (-1,59) |
| Ventas, 2024 | 1.143 | 3,71 (1,13) | 4,13 (1,54) | -0,41 (-0,42) | 2,37 (0,72) | 2,78 (1,04) |
