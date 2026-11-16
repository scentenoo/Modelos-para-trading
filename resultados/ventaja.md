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
