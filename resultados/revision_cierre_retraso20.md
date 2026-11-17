# Revisión contra el sobreajuste: B final, entrada 20 minutos después (variante 12, paso 2.8)

Generado el 2026-11-16 con `revision_cierre.py --retraso 20` sobre lo guardado por `horizonte_largo.py`, 2020–2024. Es descriptivo: no reentrena, no cuenta como variante y ninguna versión de aquí se adopta. Unidades: bps por operación; el t usa el remuestreo por bloques de `comparaciones.py`.

## 1. Umbral de entrada

Se opera si la predicción calibrada supera k veces el costo esperado; se paga el costo de la época sin multiplicar.

| Versión | Operaciones | Bruta | Costo | Neta | t por bloques |
| --- | --- | --- | --- | --- | --- |
| k = 0,50 | 34.749 | 3,72 | 2,41 | 1,32 | 1,17 |
| k = 0,75 | 28.821 | 4,65 | 2,27 | 2,39 | 1,69 |
| k = 1,00 (diseño) | 23.932 | 5,22 | 2,15 | 3,07 | 2,15 |
| k = 1,25 | 19.791 | 5,71 | 2,04 | 3,67 | 2,21 |
| k = 1,50 | 16.456 | 6,07 | 1,95 | 4,12 | 2,28 |
| k = 2,00 | 11.673 | 6,62 | 1,82 | 4,81 | 2,30 |

## 2. Hora de salida

Las mismas operaciones del diseño, cambiando solo la hora de salida.

| Versión | Operaciones | Bruta | Costo | Neta | t por bloques |
| --- | --- | --- | --- | --- | --- |
| 14:55 | 23.932 | 3,56 | 2,15 | 1,42 | 1,22 |
| 15:25 | 23.932 | 3,92 | 2,15 | 1,78 | 1,45 |
| 15:40 | 23.932 | 4,30 | 2,15 | 2,15 | 1,73 |
| 15:55 (diseño) | 23.932 | 5,22 | 2,15 | 3,07 | 2,15 |
| 15:59 | 23.932 | 5,58 | 2,15 | 3,44 | 2,31 |

## 3. Costo

| Versión | Operaciones | Bruta | Costo | Neta | t por bloques |
| --- | --- | --- | --- | --- | --- |
| 1,0 veces el costo de la época | 23.932 | 5,22 | 2,15 | 3,07 | 2,15 |
| 1,5 veces el costo de la época | 23.932 | 5,22 | 3,22 | 1,99 | 1,41 |
| 2,0 veces el costo de la época | 23.932 | 5,22 | 4,29 | 0,92 | 0,66 |

## 4. Concentración y mercado (2020-01-02 a 2024-12-31, 1249 días)

**Veredicto del analizador: ventaja propia.**

### ¿Ventaja propia o exposición al mercado?

| Base de comparación | Variación explicada (R²) | Ganancia anual sin la base | t | Ventanas de 63 días con ganancia positiva |
| --- | --- | --- | --- | --- |
| SPY | 0,2% | 3,67% | 2,32 | 65% |
| Promedio de las 50 acciones | 0,4% | 3,58% | 2,27 | 67% |
| SPY y la referencia | 1,0% | 5,08% | 2,96 | 68% |

Beta frente a SPY: 0,008 (t 0,35). El analizador pide al menos 60% de ventanas positivas para llamarlo ventaja propia.

Por régimen (cada día se etiqueta con el modelo de regímenes de su propio año de prueba):

| Régimen | Días | Ganancia anual sin la base | Días positivos |
| --- | --- | --- | --- |
| 1 | 320 | 0,69% | 48% |
| 2 | 423 | 5,44% | 53% |
| 3 | 334 | -4,96% | 47% |
| 4 | 172 | 21,64% | 55% |

### ¿Está concentrada?

Ganancia total: 73.436 bps. Los 10 mejores días aportan 48.947 bps (67%); el mejor mes, 2020-03, aporta 23.734. Días con ganancia: 50%.

| Corte | Operaciones | Ganancia neta | t | Neta con costo doble |
| --- | --- | --- | --- | --- |
| Todo el periodo | 23.932 | 3,07 | 2,23 | 0,92 |
| Sin los 10 mejores días | 23.695 | 1,03 | 0,87 | -1,10 |
| Sin 2020, el mejor año | 18.833 | 0,74 | 0,54 | -1,30 |
| Solo compras | 9.420 | 2,59 | 0,73 | 0,35 |
| Solo ventas | 14.512 | 3,38 | 1,33 | 1,29 |

Mejores días: 2020-03-17 (10.848), 2022-02-24 (7.519), 2020-03-13 (5.074), 2020-03-19 (4.369), 2020-10-06 (4.143), 2022-02-11 (4.039).

Por acción: 25 de 36 ganan. Las que más aportan: NVDA (18%), COP (13%), TSLA (10%), AMD (10%), INTC (9%). Las que más restan: ORCL (-3%), DIS (-2%), BAC (-1%).

## 5. Cifras para la lista de backtest-expert

- Operaciones: 23.932 en 1.249 días (2020–2024).
- Acierto neto: 50,5%. Ganancia media de las que ganan: 0,927%; pérdida media de las que pierden: 0,883%.
- Caída máxima de la curva diaria (una unidad de capital por acción operable): 5,80%. Retorno anual medio: 3,80%.
- Parámetros elegidos a mano: momentos de decisión, hora de salida, umbral (k = 1) y lista de acciones; los hiperparámetros se eligen dentro de cada año.
