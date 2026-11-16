# Horizonte hasta el cierre (idea 5), entrada retrasada 20 minutos (variante 12)

Generado el 2026-11-16 con `horizonte_largo.py`. Validación hacia adelante: cada año de 2020 a 2024 se predice con un modelo entrenado solo con los años anteriores. Comparación de 2020 a 2024. No incluye la muestra final.

Unidades: bps por operación (1 bps = 0,01%). El modelo predice el retorno hasta las 15:55 (minuto 384) menos el promedio de las acciones; se decide cada 30 minutos de 10:00 a 12:30, con una operación por acción y por día como máximo (la del primer momento que supera el costo). Costo: el spread de la época, un spread completo por operación. 36 acciones operables (las de 60 minutos). Sin cobertura.

Comprobación del objetivo: con la misma función, el retorno a 60 minutos coincide con `obj_60` guardado (diferencia máxima 0,001303 bps en 2.342.231 filas).

Entrada retrasada 20 minutos: el modelo decide en los mismos momentos y con las mismas variables, pero entra en el minuto k + 20 y el objetivo es el retorno desde esa entrada hasta las 15:55, menos el promedio de las acciones. Base de comparación conocida: la idea 5 sin retraso, 2,87 bps (t por bloques 2,30).

Variantes probadas hasta ahora: 12 (t exigido con Bonferroni 2,64).

## Resultado

| Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t por días | t por bloques | Neta con costo doble | t por bloques (doble) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 23.932 | 1.249 de 1249 | 51,3% | 5,22 | 2,15 | 3,07 | 2,23 | 2,15 | 0,92 | 0,66 |

El t por bloques usa la ganancia neta diaria (suma por día; los días sin operaciones valen 0) y el remuestreo de `comparaciones.py` (bloques de 10 días, 10.000 remuestreos, semilla 7).

## Por año

| Año | Ganancia neta | Operaciones | Neta con costo doble | Pendiente de calibración | Elección de la búsqueda |
| --- | --- | --- | --- | --- | --- |
| 2020 | 11,69 | 5.099 | 9,13 | 0,56 | 127 hojas, 300 árboles |
| 2021 | 1,12 | 6.304 | -0,88 | 0,89 | 31 hojas, 500 árboles |
| 2022 | 1,81 | 6.805 | -0,72 | 0,90 | 127 hojas, 300 árboles |
| 2023 | -0,16 | 3.577 | -1,63 | 0,80 | 127 hojas, 100 árboles |
| 2024 | -2,32 | 2.147 | -3,81 | 0,80 | 31 hojas, 100 árboles |

Sin 2020: neta 0,74 bps por operación, t por bloques 0,54.

Trimestres con ganancia neta positiva: 11 de 20.

## Selección y mercado

Ganancia bruta = selección (dirección por el retorno relativo) + mercado (el resto).

| Parte | Media por operación | t por días |
| --- | --- | --- |
| Selección | 3,54 | 3,83 |
| Mercado | 1,68 | 1,82 |

## ¿El modelo ordena bien las acciones?

Correlación de rangos media entre la predicción sin calibrar y el retorno relativo real, por momento y promediada por día (50 acciones): 0,0281 (t 5,53).

## Operaciones por momento de entrada

| Entrada | Operaciones | Neta por operación |
| --- | --- | --- |
| 10:20 | 17.118 | 4,29 |
| 10:50 | 2.955 | 2,21 |
| 11:20 | 1.540 | 1,16 |
| 11:50 | 1.007 | -7,49 |
| 12:20 | 753 | 0,50 |
| 12:50 | 559 | -2,16 |

Tiempo de la corrida: 13.1 minutos.
