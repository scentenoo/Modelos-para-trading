# Variante 13: LightGBM v2 con rasgos de régimen (entrada retrasada 20 minutos)

Generado el 2026-11-16 con `variantes_b.py`. Validación hacia adelante: cada año de 2020 a 2024 se predice con un modelo entrenado solo con los años anteriores. Comparación de 2020 a 2024. No incluye la muestra final.

Unidades: bps por operación (1 bps = 0,01%). El modelo predice el retorno hasta las 15:55 (minuto 384) menos el promedio de las acciones; se decide cada 30 minutos de 10:00 a 12:30, con una operación por acción y por día como máximo (la del primer momento que supera el costo). Costo: el spread de la época, un spread completo por operación. 36 acciones operables (las de 60 minutos). Sin cobertura.

Comprobación del objetivo: con la misma función, el retorno a 60 minutos coincide con `obj_60` guardado (diferencia máxima 0,001303 bps en 2.342.231 filas).

Entrada retrasada 20 minutos: el modelo decide en los mismos momentos y con las mismas variables, pero entra en el minuto k + 20 y el objetivo es el retorno desde esa entrada hasta las 15:55, menos el promedio de las acciones. Base de comparación conocida: la idea 5 sin retraso, 2,87 bps (t por bloques 2,30).

Variantes probadas hasta ahora: 14 (t exigido con Bonferroni 2,69).

## Resultado

| Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t por días | t por bloques | Neta con costo doble | t por bloques (doble) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 24.251 | 1.249 de 1249 | 51,1% | 4,06 | 2,03 | 2,04 | 1,52 | 1,65 | 0,01 | 0,01 |

El t por bloques usa la ganancia neta diaria (suma por día; los días sin operaciones valen 0) y el remuestreo de `comparaciones.py` (bloques de 10 días, 10.000 remuestreos, semilla 7).

## Por año

| Año | Ganancia neta | Operaciones | Neta con costo doble | Pendiente de calibración | Elección de la búsqueda |
| --- | --- | --- | --- | --- | --- |
| 2020 | 10,00 | 4.412 | 7,57 | 0,49 | 127 hojas, 300 árboles |
| 2021 | 1,75 | 3.530 | 0,09 | 0,75 | 7 hojas, 500 árboles |
| 2022 | -1,55 | 4.865 | -3,84 | 0,83 | 31 hojas, 300 árboles |
| 2023 | 1,39 | 5.893 | -0,39 | 0,79 | 127 hojas, 300 árboles |
| 2024 | -0,27 | 5.551 | -2,25 | 0,78 | 127 hojas, 300 árboles |

Sin 2020: neta 0,27 bps por operación, t por bloques 0,21.

Trimestres con ganancia neta positiva: 13 de 20.

## Selección y mercado

Ganancia bruta = selección (dirección por el retorno relativo) + mercado (el resto).

| Parte | Media por operación | t por días |
| --- | --- | --- |
| Selección | 3,48 | 3,86 |
| Mercado | 0,58 | 0,65 |

## ¿El modelo ordena bien las acciones?

Correlación de rangos media entre la predicción sin calibrar y el retorno relativo real, por momento y promediada por día (50 acciones): 0,0275 (t 4,99).

## Operaciones por momento de entrada

| Entrada | Operaciones | Neta por operación |
| --- | --- | --- |
| 10:20 | 17.687 | 2,58 |
| 10:50 | 2.727 | 2,59 |
| 11:20 | 1.546 | 0,17 |
| 11:50 | 1.032 | -2,41 |
| 12:20 | 726 | 0,64 |
| 12:50 | 533 | -2,83 |

Tiempo de la corrida: 19.9 minutos.

## Comparación con B (variante 12)

Diferencia de ganancia neta diaria (variante menos B, suma por día en bps; B = `operaciones_cierre_retraso20.parquet`; mismos 1249 días de 2020 a 2024, los días sin operaciones valen 0). t por bloques con `horizonte_largo.t_bloques`.

| Ganancia neta diaria, variante | Ganancia neta diaria, B | Diferencia | t por bloques |
| --- | --- | --- | --- |
| 39,53 | 58,80 | -19,26 | -1,16 |

Regla del documento: "reemplaza a B" si t >= 1,65 y la diferencia es positiva; si no, "B queda como está".

**Conclusión: B queda como está.**


# Variante 14: Ridge multinivel por grupo (entrada retrasada 20 minutos)

Generado el 2026-11-16 con `variantes_b.py`. Validación hacia adelante: cada año de 2020 a 2024 se predice con un modelo entrenado solo con los años anteriores. Comparación de 2020 a 2024. No incluye la muestra final.

Unidades: bps por operación (1 bps = 0,01%). El modelo predice el retorno hasta las 15:55 (minuto 384) menos el promedio de las acciones; se decide cada 30 minutos de 10:00 a 12:30, con una operación por acción y por día como máximo (la del primer momento que supera el costo). Costo: el spread de la época, un spread completo por operación. 36 acciones operables (las de 60 minutos). Sin cobertura.

Comprobación del objetivo: con la misma función, el retorno a 60 minutos coincide con `obj_60` guardado (diferencia máxima 0,001303 bps en 2.342.231 filas).

Entrada retrasada 20 minutos: el modelo decide en los mismos momentos y con las mismas variables, pero entra en el minuto k + 20 y el objetivo es el retorno desde esa entrada hasta las 15:55, menos el promedio de las acciones. Base de comparación conocida: la idea 5 sin retraso, 2,87 bps (t por bloques 2,30).

Variantes probadas hasta ahora: 14 (t exigido con Bonferroni 2,69).

## Resultado

| Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t por días | t por bloques | Neta con costo doble | t por bloques (doble) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 33.429 | 1.249 de 1249 | 50,8% | 2,77 | 2,37 | 0,40 | 0,37 | 0,38 | -1,97 | -1,88 |

El t por bloques usa la ganancia neta diaria (suma por día; los días sin operaciones valen 0) y el remuestreo de `comparaciones.py` (bloques de 10 días, 10.000 remuestreos, semilla 7).

## Por año

| Año | Ganancia neta | Operaciones | Neta con costo doble | Pendiente de calibración | Elección de la búsqueda |
| --- | --- | --- | --- | --- | --- |
| 2020 | 1,05 | 7.216 | -1,92 | 0,96 | λ = 100, 4 grupos |
| 2021 | 0,87 | 7.992 | -1,44 | 1,01 | λ = 1000, 5 grupos |
| 2022 | 0,25 | 7.451 | -2,33 | 0,82 | λ = 100, 4 grupos |
| 2023 | -1,42 | 5.905 | -3,28 | 0,60 | λ = 1000, 5 grupos |
| 2024 | 1,11 | 4.865 | -0,79 | 0,51 | λ = 100, 5 grupos |

Sin 2020: neta 0,22 bps por operación, t por bloques 0,22.

Trimestres con ganancia neta positiva: 11 de 20.

## Selección y mercado

Ganancia bruta = selección (dirección por el retorno relativo) + mercado (el resto).

| Parte | Media por operación | t por días |
| --- | --- | --- |
| Selección | 3,28 | 3,89 |
| Mercado | -0,51 | -0,79 |

## ¿El modelo ordena bien las acciones?

Correlación de rangos media entre la predicción sin calibrar y el retorno relativo real, por momento y promediada por día (50 acciones): 0,0170 (t 3,02).

## Operaciones por momento de entrada

| Entrada | Operaciones | Neta por operación |
| --- | --- | --- |
| 10:20 | 21.984 | 1,64 |
| 10:50 | 4.680 | -1,98 |
| 11:20 | 3.093 | -0,50 |
| 11:50 | 1.738 | -3,83 |
| 12:20 | 1.130 | -2,60 |
| 12:50 | 804 | -2,83 |

Tiempo de la corrida: 3.5 minutos.

## Comparación con B (variante 12)

Diferencia de ganancia neta diaria (variante menos B, suma por día en bps; B = `operaciones_cierre_retraso20.parquet`; mismos 1249 días de 2020 a 2024, los días sin operaciones valen 0). t por bloques con `horizonte_largo.t_bloques`.

| Ganancia neta diaria, variante | Ganancia neta diaria, B | Diferencia | t por bloques |
| --- | --- | --- | --- |
| 10,68 | 58,80 | -48,11 | -1,27 |

Regla del documento: "reemplaza a B" si t >= 1,65 y la diferencia es positiva; si no, "B queda como está".

**Conclusión: B queda como está.**

