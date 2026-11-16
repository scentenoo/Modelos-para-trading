# Revisión contra el sobreajuste: horizonte hasta el cierre (paso 2.8)

Generado el 2026-11-16 con `revision_cierre.py` sobre lo guardado por `horizonte_largo.py`, 2020–2024. Es descriptivo: no reentrena, no cuenta como variante y ninguna versión de aquí se adopta. Unidades: bps por operación; el t usa el remuestreo por bloques de `comparaciones.py`.

## 1. Umbral de entrada

Se opera si la predicción calibrada supera k veces el costo esperado; se paga el costo de la época sin multiplicar.

| Versión | Operaciones | Bruta | Costo | Neta | t por bloques |
| --- | --- | --- | --- | --- | --- |
| k = 0,50 | 41.832 | 4,57 | 2,60 | 1,98 | 1,71 |
| k = 0,75 | 37.881 | 5,12 | 2,44 | 2,69 | 2,27 |
| k = 1,00 (diseño) | 33.692 | 5,16 | 2,29 | 2,87 | 2,30 |
| k = 1,25 | 29.635 | 5,14 | 2,17 | 2,97 | 2,26 |
| k = 1,50 | 26.040 | 5,56 | 2,07 | 3,49 | 2,29 |
| k = 2,00 | 19.897 | 6,91 | 1,90 | 5,00 | 2,83 |

## 2. Hora de salida

Las mismas operaciones del diseño, cambiando solo la hora de salida.

| Versión | Operaciones | Bruta | Costo | Neta | t por bloques |
| --- | --- | --- | --- | --- | --- |
| 14:55 | 33.692 | 4,04 | 2,29 | 1,75 | 1,66 |
| 15:25 | 33.692 | 4,03 | 2,29 | 1,73 | 1,65 |
| 15:40 | 33.692 | 4,37 | 2,29 | 2,07 | 1,95 |
| 15:55 (diseño) | 33.692 | 5,16 | 2,29 | 2,87 | 2,30 |
| 15:59 | 33.692 | 5,30 | 2,29 | 3,00 | 2,36 |

## 3. Costo

| Versión | Operaciones | Bruta | Costo | Neta | t por bloques |
| --- | --- | --- | --- | --- | --- |
| 1,0 veces el costo de la época | 33.692 | 5,16 | 2,29 | 2,87 | 2,30 |
| 1,5 veces el costo de la época | 33.692 | 5,16 | 3,44 | 1,72 | 1,40 |
| 2,0 veces el costo de la época | 33.692 | 5,16 | 4,59 | 0,57 | 0,47 |

## 4. Concentración y mercado (2020-01-02 a 2024-12-31, 1249 días)

**Veredicto del analizador: ventaja propia.**

### ¿Ventaja propia o exposición al mercado?

| Base de comparación | Variación explicada (R²) | Ganancia anual sin la base | t | Ventanas de 63 días con ganancia positiva |
| --- | --- | --- | --- | --- |
| SPY | 0,1% | 4,88% | 2,42 | 71% |
| Promedio de las 50 acciones | 0,3% | 4,76% | 2,39 | 76% |
| SPY y la referencia | 1,7% | 7,44% | 3,43 | 74% |

Beta frente a SPY: 0,008 (t 0,28). El analizador pide al menos 60% de ventanas positivas para llamarlo ventaja propia.

Por régimen (cada día se etiqueta con el modelo de regímenes de su propio año de prueba):

| Régimen | Días | Ganancia anual sin la base | Días positivos |
| --- | --- | --- | --- |
| 1 | 320 | 1,51% | 51% |
| 2 | 423 | 6,17% | 53% |
| 3 | 334 | -4,47% | 48% |
| 4 | 172 | 26,13% | 58% |

### ¿Está concentrada?

Ganancia total: 96.620 bps. Los 10 mejores días aportan 62.306 bps (64%); el mejor mes, 2020-03, aporta 27.502. Días con ganancia: 52%.

| Corte | Operaciones | Ganancia neta | t | Neta con costo doble |
| --- | --- | --- | --- | --- |
| Todo el periodo | 33.692 | 2,87 | 2,30 | 0,57 |
| Sin los 10 mejores días | 33.412 | 1,03 | 0,95 | -1,25 |
| Sin 2020, el mejor año | 26.636 | 1,24 | 1,03 | -0,92 |
| Solo compras | 14.097 | 3,77 | 1,20 | 1,41 |
| Solo ventas | 19.595 | 2,22 | 0,92 | -0,02 |

Mejores días: 2020-03-17 (12.900), 2022-02-24 (8.364), 2020-03-19 (7.080), 2020-03-24 (6.408), 2020-03-03 (5.153), 2022-02-11 (4.638).

Por acción: 26 de 36 ganan. Las que más aportan: NVDA (19%), TSLA (14%), AMD (14%), NKE (6%), DIS (6%). Las que más restan: ORCL (-6%), UPS (-4%), MCD (-3%).

## 5. Cifras para la lista de backtest-expert

- Operaciones: 33.692 en 1.249 días (2020–2024).
- Acierto neto: 50,2%. Ganancia media de las que ganan: 0,968%; pérdida media de las que pierden: 0,919%.
- Caída máxima de la curva diaria (una unidad de capital por acción operable): 6,88%. Retorno anual medio: 5,00%.
- Parámetros elegidos a mano: momentos de decisión, hora de salida, umbral (k = 1) y lista de acciones; los hiperparámetros se eligen dentro de cada año.
