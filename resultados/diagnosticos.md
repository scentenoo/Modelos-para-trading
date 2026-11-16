# Diagnósticos de la señal del modelo de velas

Generado el 2026-11-16 con `diagnosticos.py`, sobre las predicciones de LightGBM v2 y las operaciones de su versión calibrada, 2020–2024. Es descriptivo: no entrena nada y no cuenta como variante. No incluye la muestra final.

Selección: retorno de la acción frente al promedio de las 50, en la dirección que predijo el modelo, antes de costos. La última columna de cada tabla sí usa el retorno completo o descuenta el costo, según se indica.

## 1. ¿El modelo elige mejor después de una noticia?

### Horizonte de 30 minutos

Selección y ganancia en bps por fila; entre paréntesis, el t. La selección relativa es un porcentaje del movimiento típico de la acción en ese momento, para no confundir "elige mejor" con "se mueve más".

| Momentos | Filas | Movimiento típico | Selección, todas las filas | Selección relativa | Operadas | Selección, operadas | Ganancia neta, operadas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Sin noticias desde el cierre de ayer | 146.184 (46%) | 14,8 | 0,24 (2,76) | 0,63 (2,48) | 6.242 | 2,87 (4,21) | 1,65 (1,73) |
| Con noticias hoy, ninguna en la última hora | 121.991 (39%) | 15,2 | 0,58 (5,63) | 1,44 (5,62) | 12.682 | 1,77 (3,35) | 0,26 (0,36) |
| Con noticia en la última hora | 47.800 (15%) | 17,4 | 0,69 (3,40) | 1,15 (2,72) | 7.737 | 2,27 (3,13) | 1,47 (1,59) |
| Con 3 o más noticias en la última hora | 2.444 (1%) | 23,8 | 2,75 (2,53) | 4,10 (2,27) | 717 | 4,00 (1,47) | 3,83 (1,24) |
| Todos los momentos | 315.975 (100%) | 15,3 | 0,44 (6,26) | 1,03 (5,75) | 26.661 | 2,17 (5,31) | 0,94 (1,61) |

Las noticias se concentran: TSLA (13%), AAPL (10%), AMZN (10%), MSFT (8%), DIS (6%) suman el 47% de los momentos con noticia. Dentro de una misma acción, la selección es mayor con noticia que sin ella en 13 de 23 acciones (las que tienen al menos 200 momentos con noticia); la diferencia mediana es 0,10 bps.

### Horizonte de 60 minutos

Selección y ganancia en bps por fila; entre paréntesis, el t. La selección relativa es un porcentaje del movimiento típico de la acción en ese momento, para no confundir "elige mejor" con "se mueve más".

| Momentos | Filas | Movimiento típico | Selección, todas las filas | Selección relativa | Operadas | Selección, operadas | Ganancia neta, operadas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Sin noticias desde el cierre de ayer | 120.998 (54%) | 21,2 | 0,50 (3,01) | 0,77 (2,29) | 8.275 | 3,23 (3,83) | 3,69 (2,80) |
| Con noticias hoy, ninguna en la última hora | 74.364 (33%) | 21,5 | 0,92 (4,62) | 1,55 (4,24) | 10.833 | 1,91 (2,65) | 1,08 (1,03) |
| Con noticia en la última hora | 29.443 (13%) | 24,7 | 1,20 (3,36) | 0,96 (1,76) | 6.164 | 2,94 (2,80) | 1,63 (1,18) |
| Con 3 o más noticias en la última hora | 1.486 (1%) | 35,4 | 3,61 (1,74) | 5,45 (2,20) | 542 | 4,63 (1,25) | 2,92 (0,71) |
| Todos los momentos | 224.805 (100%) | 21,7 | 0,73 (5,39) | 1,07 (4,23) | 25.272 | 2,59 (4,64) | 2,07 (2,29) |

Las noticias se concentran: TSLA (10%), AAPL (8%), AMZN (7%), MSFT (6%), BA (5%) suman el 36% de los momentos con noticia. Dentro de una misma acción, la selección es mayor con noticia que sin ella en 14 de 34 acciones (las que tienen al menos 200 momentos con noticia); la diferencia mediana es -0,19 bps.

## 2. ¿Cuánto dura la señal?

La "neta con el mismo costo" es la selección menos el spread: supone que la parte de mercado se cubre o se compensa, y no cuenta el costo de esa cobertura.

### Predicciones del modelo de 30 minutos

Selección en bps por operación; entre paréntesis, el t. Las columnas "mismas entradas" usan solo las entradas hasta las 12:54, en las que caben todas las duraciones, para comparar sobre las mismas operaciones. El costo medio de las operadas es 1,45 bps y no cambia con la duración. (Control: la selección recalculada a 30 minutos coincide con la guardada, correlación 1,000.)

| Se mantiene | Todas las filas | Todas, mismas entradas | Operadas | Operadas, mismas entradas | Operadas: neta con el mismo costo |
| --- | --- | --- | --- | --- | --- |
| 15 min | 0,17 (3,10) | 0,18 (2,15) | 0,88 (2,87) | 0,77 (1,83) | -0,69 (-1,64) |
| 30 min | 0,44 (6,26) | 0,49 (4,44) | 2,17 (5,31) | 1,79 (3,18) | 0,32 (0,57) |
| 60 min | 0,67 (5,36) | 0,80 (4,56) | 3,45 (4,94) | 3,61 (4,09) | 2,14 (2,44) |
| 120 min | 0,90 (4,15) | 1,01 (3,94) | 5,06 (4,30) | 5,07 (3,87) | 3,61 (2,76) |
| 180 min | 1,20 (3,77) | 1,20 (3,77) | 6,38 (3,97) | 6,38 (3,97) | 4,92 (3,07) |
| Hasta el cierre | 1,16 (3,87) | 1,50 (3,48) | 5,67 (3,49) | 6,83 (3,24) | 5,37 (2,55) |

### Predicciones del modelo de 60 minutos

Selección en bps por operación; entre paréntesis, el t. Las columnas "mismas entradas" usan solo las entradas hasta las 12:54, en las que caben todas las duraciones, para comparar sobre las mismas operaciones. El costo medio de las operadas es 1,70 bps y no cambia con la duración. (Control: la selección recalculada a 60 minutos coincide con la guardada, correlación 1,000.)

| Se mantiene | Todas las filas | Todas, mismas entradas | Operadas | Operadas, mismas entradas | Operadas: neta con el mismo costo |
| --- | --- | --- | --- | --- | --- |
| 15 min | 0,19 (2,57) | 0,23 (2,13) | 0,47 (1,49) | 0,42 (0,97) | -1,28 (-2,93) |
| 30 min | 0,44 (4,55) | 0,60 (4,16) | 1,47 (3,55) | 1,48 (2,57) | -0,22 (-0,39) |
| 60 min | 0,73 (5,39) | 0,87 (4,31) | 2,59 (4,64) | 2,42 (3,20) | 0,72 (0,95) |
| 120 min | 0,89 (3,95) | 0,96 (3,48) | 3,05 (3,33) | 2,62 (2,51) | 0,92 (0,88) |
| 180 min | 1,20 (3,70) | 1,20 (3,70) | 3,87 (2,98) | 3,87 (2,98) | 2,17 (1,68) |
| Hasta el cierre | 1,29 (4,21) | 1,49 (3,55) | 4,21 (3,17) | 4,78 (2,80) | 3,08 (1,81) |
