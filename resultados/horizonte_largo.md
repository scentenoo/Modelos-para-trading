# Horizonte hasta el cierre (idea 5)

Generado el 2026-11-16 con `horizonte_largo.py`. Validación hacia adelante: cada año de 2020 a 2024 se predice con un modelo entrenado solo con los años anteriores. Comparación de 2020 a 2024. No incluye la muestra final.

Unidades: bps por operación (1 bps = 0,01%). El modelo predice el retorno hasta las 15:55 (minuto 384) menos el promedio de las acciones; se decide cada 30 minutos de 10:00 a 12:30, con una operación por acción y por día como máximo (la del primer momento que supera el costo). Costo: el spread de la época, un spread completo por operación. 36 acciones operables (las de 60 minutos). Sin cobertura.

Comprobación del objetivo: con la misma función, el retorno a 60 minutos coincide con `obj_60` guardado (diferencia máxima 0,001303 bps en 2.342.231 filas).

Base de comparación conocida: la calibrada a 60 minutos con costo de la época, volviendo a decidir, dio 1,00 bps (t 1,40 por días).

Variantes probadas hasta ahora: 11 (t exigido con Bonferroni 2,61).

## Resultado

| Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t por días | t por bloques | Neta con costo doble | t por bloques (doble) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 33.692 | 1.249 de 1249 | 51,0% | 5,16 | 2,29 | 2,87 | 2,30 | 2,30 | 0,57 | 0,47 |

El t por bloques usa la ganancia neta diaria (suma por día; los días sin operaciones valen 0) y el remuestreo de `comparaciones.py` (bloques de 10 días, 10.000 remuestreos, semilla 7).

## Por año

| Año | Ganancia neta | Operaciones | Neta con costo doble | Pendiente de calibración | Elección de la búsqueda |
| --- | --- | --- | --- | --- | --- |
| 2020 | 9,03 | 7.056 | 6,20 | 0,63 | 127 hojas, 500 árboles |
| 2021 | 1,46 | 6.492 | -0,56 | 0,84 | 31 hojas, 500 árboles |
| 2022 | 4,34 | 6.536 | 1,83 | 0,88 | 31 hojas, 500 árboles |
| 2023 | -1,06 | 7.116 | -3,03 | 0,81 | 127 hojas, 500 árboles |
| 2024 | 0,40 | 6.492 | -1,71 | 0,74 | 127 hojas, 500 árboles |

Sin 2020: neta 1,24 bps por operación, t por bloques 1,03.

Trimestres con ganancia neta positiva: 11 de 20.

## Selección y mercado

Ganancia bruta = selección (dirección por el retorno relativo) + mercado (el resto).

| Parte | Media por operación | t por días |
| --- | --- | --- |
| Selección | 4,00 | 4,73 |
| Mercado | 1,16 | 1,44 |

## ¿El modelo ordena bien las acciones?

Correlación de rangos media entre la predicción sin calibrar y el retorno relativo real, por momento y promediada por día (50 acciones): 0,0317 (t 6,16).

## Operaciones por momento de entrada

| Entrada | Operaciones | Neta por operación |
| --- | --- | --- |
| 10:00 | 23.680 | 3,62 |
| 10:30 | 4.334 | 5,46 |
| 11:00 | 2.483 | -3,36 |
| 11:30 | 1.464 | -2,51 |
| 12:00 | 1.028 | -0,45 |
| 12:30 | 703 | -0,52 |

Tiempo de la corrida: 12.6 minutos.
