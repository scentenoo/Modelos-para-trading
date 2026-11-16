# Comparaciones múltiples del modelo de velas

Generado el 2026-11-16 con `comparaciones.py`. 11 variantes, 1249 días (2020-01-02 a 2024-12-31), 10.000 remuestreos por bloques de 10 días en promedio. No incluye la muestra final.

La ganancia diaria está en bps por acción operable. El t se calcula con el remuestreo por bloques, así que puede diferir un poco del de los otros informes. Pruebas de una cola: un valor p menor que 0,05 indica que la ganancia se distingue de la base.

## Contra no operar (ganancia cero)

| Variante | Ganancia diaria media | t | p sin corregir | p con Bonferroni | p con Holm |
| --- | --- | --- | --- | --- | --- |
| LightGBM v2 calibrado, hasta el cierre | 1,984 | 2,30 | 0,011 | 0,117 | 0,117 |
| LightGBM v2 calibrado, 60 min | 1,072 | 1,65 | 0,050 | 0,548 | 0,498 |
| LightGBM v2 calibrado, 30 min | 0,771 | 1,41 | 0,079 | 0,865 | 0,708 |
| LightGBM v2 con filtro, 60 min | 0,913 | 1,19 | 0,118 | 1,000 | 0,944 |
| LightGBM v2, 60 min | 1,201 | 1,17 | 0,122 | 1,000 | 0,944 |
| LightGBM v1, 60 min | 1,077 | 1,13 | 0,129 | 1,000 | 0,944 |
| LightGBM v1, 30 min | 0,582 | 0,97 | 0,166 | 1,000 | 0,944 |
| LightGBM v2, 30 min | 0,582 | 0,88 | 0,189 | 1,000 | 0,944 |
| LightGBM v2 con filtro, 30 min | 0,263 | 0,45 | 0,325 | 1,000 | 0,976 |
| Regresión logística, 30 min | -0,006 | -0,05 | 0,521 | 1,000 | 1,000 |
| Regresión logística, 60 min | -0,170 | -0,95 | 0,829 | 1,000 | 1,000 |

**SPA de Hansen** (¿la mejor variante le gana a la base?): p = 0,083. Cota inferior 0,077; cota superior (Reality Check de White) 0,083.

## Contra la referencia (competidor A)

| Variante | Ganancia diaria media | t | p sin corregir | p con Bonferroni | p con Holm |
| --- | --- | --- | --- | --- | --- |
| Regresión logística, 30 min | 11,596 | 11,57 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 calibrado, 30 min | 12,372 | 10,07 | 0,000 | 0,000 | 0,000 |
| LightGBM v1, 30 min | 12,183 | 9,88 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 con filtro, 30 min | 11,864 | 9,67 | 0,000 | 0,000 | 0,000 |
| Regresión logística, 60 min | 8,913 | 9,53 | 0,000 | 0,000 | 0,000 |
| LightGBM v2, 30 min | 12,183 | 9,11 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 calibrado, 60 min | 10,156 | 8,62 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 calibrado, hasta el cierre | 11,067 | 8,47 | 0,000 | 0,000 | 0,000 |
| LightGBM v2 con filtro, 60 min | 9,997 | 7,90 | 0,000 | 0,000 | 0,000 |
| LightGBM v1, 60 min | 10,161 | 7,61 | 0,000 | 0,000 | 0,000 |
| LightGBM v2, 60 min | 10,285 | 7,28 | 0,000 | 0,000 | 0,000 |

**SPA de Hansen** (¿la mejor variante le gana a la base?): p = 0,000. Cota inferior 0,000; cota superior (Reality Check de White) 0,000.
