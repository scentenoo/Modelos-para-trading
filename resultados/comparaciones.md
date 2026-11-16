# Comparaciones múltiples del modelo de velas

Generado el 2026-11-16 con `comparaciones.py`. 11 variantes, 1249 días (2020-01-02 a 2024-12-31), 10.000 remuestreos por bloques de 10 días en promedio. No incluye la muestra final.

La ganancia diaria está en bps por acción operable, con el costo de la época en todas las variantes. El t se calcula con el remuestreo por bloques, así que puede diferir un poco del de los otros informes. Pruebas de una cola: un valor p menor que 0,05 indica que la ganancia se distingue de la base.

## Contra no operar (ganancia cero)

| Variante | Ganancia diaria media | t | p sin corregir | p con Bonferroni | p con Holm |
| --- | --- | --- | --- | --- | --- |
| LightGBM v2 calibrado, hasta el cierre | 1,984 | 2,30 | 0,011 | 0,117 | 0,117 |
| LightGBM v2 calibrado, 60 min | 0,519 | 1,15 | 0,125 | 1,000 | 1,000 |
| LightGBM v2 calibrado, 30 min | 0,358 | 1,04 | 0,150 | 1,000 | 1,000 |
| LightGBM v1, 60 min | 0,729 | 1,01 | 0,155 | 1,000 | 1,000 |
| LightGBM v2, 60 min | 0,474 | 0,57 | 0,284 | 1,000 | 1,000 |
| LightGBM v1, 30 min | 0,097 | 0,26 | 0,398 | 1,000 | 1,000 |
| LightGBM v2, 30 min | 0,093 | 0,19 | 0,424 | 1,000 | 1,000 |
| LightGBM v2 con filtro, 60 min | -0,295 | -0,43 | 0,666 | 1,000 | 1,000 |
| Regresión logística, 30 min | -0,064 | -0,81 | 0,791 | 1,000 | 1,000 |
| Regresión logística, 60 min | -0,108 | -0,91 | 0,819 | 1,000 | 1,000 |
| LightGBM v2 con filtro, 30 min | -2,377 | -3,60 | 1,000 | 1,000 | 1,000 |

**SPA de Hansen** (¿la mejor variante le gana a la base?): p = 0,078. Cota inferior 0,062; cota superior (Reality Check de White) 0,082.

## Contra la referencia (competidor A)

| Variante | Ganancia diaria media | t | p sin corregir | p con Bonferroni | p con Holm |
| --- | --- | --- | --- | --- | --- |
| Regresión logística, 30 min | 15,531 | 15,45 | 0,000 | 0,000 | 0,000 |
| LightGBM v1, 30 min | 15,692 | 14,09 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 calibrado, 30 min | 15,954 | 14,00 | 0,000 | 0,000 | 0,000 |
| LightGBM v2, 30 min | 15,689 | 13,13 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 con filtro, 30 min | 13,218 | 10,86 | 0,000 | 0,000 | 0,000 |
| Regresión logística, 60 min | 10,331 | 10,57 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 calibrado, 60 min | 10,959 | 9,83 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 calibrado, hasta el cierre | 12,423 | 8,88 | 0,000 | 0,000 | 0,000 |
| LightGBM v1, 60 min | 11,169 | 8,68 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 con filtro, 60 min | 10,145 | 8,06 | 0,000 | 0,000 | 0,000 |
| LightGBM v2, 60 min | 10,913 | 8,03 | 0,000 | 0,000 | 0,000 |

**SPA de Hansen** (¿la mejor variante le gana a la base?): p = 0,000. Cota inferior 0,000; cota superior (Reality Check de White) 0,000.
