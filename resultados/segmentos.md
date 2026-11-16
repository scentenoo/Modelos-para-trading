# Segmentos: grupos de acciones y regímenes de mercado (pasos 2.3 y 2.4)

Generado el 2026-11-16 con `segmentos.py`. Para cada año de prueba, de 2019 a 2024, los grupos y los regímenes se calculan solo con días anteriores a ese año. No incluye la muestra final.

## 1. Grupos de acciones

Con los 3 años anteriores a cada año de prueba. La silueta va de −1 a 1: cerca de 0, los grupos se confunden entre sí. El parecido va de 0 (como al azar) a 1 (idénticos).

| Año de prueba | Grupos por correlación | Silueta | Parecido con los sectores | Parecido con el año anterior | Grupos por características | Silueta | Parecido con el año anterior |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | 10 | 0,09 | 0,37 | — | 5 | 0,38 | — |
| 2020 | 10 | 0,10 | 0,30 | 0,67 | 4 | 0,39 | 0,85 |
| 2021 | 4 | 0,11 | 0,35 | 0,49 | 5 | 0,39 | 0,45 |
| 2022 | 8 | 0,12 | 0,49 | 0,63 | 4 | 0,40 | 0,65 |
| 2023 | 5 | 0,12 | 0,38 | 0,73 | 5 | 0,42 | 0,84 |
| 2024 | 6 | 0,12 | 0,35 | 0,74 | 5 | 0,38 | 0,69 |

En la ventana de 2024, el primer componente principal (el mercado) explica el 34% de la variación de los retornos diarios; los cuatro siguientes, 9%, 8%, 3%, 3%.

### Grupos por correlación en la ventana de 2024

| Grupo | Acciones |
| --- | --- |
| 1 | AAPL (tecnologia), MSFT (tecnologia), NVDA (tecnologia), GOOGL (tecnologia), AMZN (tecnologia), META (tecnologia), AVGO (tecnologia), AMD (tecnologia), CRM (tecnologia), ADBE (tecnologia), INTC (tecnologia), NKE (consumo), TSLA (consumo), DIS (comunicaciones), NFLX (comunicaciones) |
| 4 | JNJ (salud), UNH (salud), PFE (salud), MRK (salud), ABBV (salud), LLY (salud), PG (consumo), KO (consumo), PEP (consumo), MCD (consumo), NEE (servicios_publicos), DUK (servicios_publicos), SO (servicios_publicos), T (comunicaciones), VZ (comunicaciones) |
| 5 | WMT (consumo), COST (consumo), HD (consumo), UPS (industrial) |
| 8 | JPM (financiero), BAC (financiero), GS (financiero), MS (financiero), WFC (financiero), XOM (energia), CVX (energia), COP (energia), CAT (industrial), BA (industrial), GE (industrial), HON (industrial), LIN (materiales) |
| 12 | V (financiero), MA (financiero) |
| 16 | ORCL (tecnologia) |

### Grupos por características en la ventana de 2024

| Grupo | Acciones | Volatilidad diaria | Monto diario (millones de dólares) | Beta | Noticias por día |
| --- | --- | --- | --- | --- | --- |
| 1 | AVGO, ORCL, CRM, ADBE, INTC, JPM, BAC, GS, MS, WFC, V, MA, LLY, NKE, HD, XOM, CVX, COP, CAT, BA, GE, UPS, DIS | 1,82% | 823 | 1,03 | 0,7 |
| 2 | JNJ, UNH, PFE, MRK, ABBV, WMT, COST, PG, KO, PEP, MCD, HON, NEE, DUK, SO, T, VZ, LIN | 1,23% | 512 | 0,51 | 0,6 |
| 3 | NVDA, META, AMD, NFLX | 2,91% | 4.867 | 1,69 | 1,5 |
| 5 | AAPL, MSFT, GOOGL, AMZN | 1,86% | 6.187 | 1,30 | 4,4 |
| 7 | TSLA | 3,54% | 21.844 | 1,88 | 12,3 |

## 2. Regímenes de mercado

Se numeran del más calmado (1) al más volátil. El número de regímenes lo elige el BIC en cada ventana, entre 2 y 4.

### Cómo es cada régimen en la ventana de 2024 (días de entrenamiento)

| Régimen | Días | Volatilidad anual de SPY | Volatilidad de 5 días frente a 20 | Tendencia de 20 días | Dispersión entre acciones |
| --- | --- | --- | --- | --- | --- |
| 1 | 22% | 6,3% | 1,13 veces | 0,75 | 122 bps |
| 2 | 29% | 7,9% | 0,83 veces | 1,40 | 131 bps |
| 3 | 26% | 14,1% | 1,11 veces | -0,43 | 152 bps |
| 4 | 23% | 14,3% | 0,89 veces | 0,35 | 165 bps |

### Días de cada año de prueba en cada régimen

Cada año se etiqueta con el modelo ajustado solo con los años anteriores.

| Año | Regímenes | Régimen 1 | Régimen 2 | Régimen 3 | Régimen 4 |
| --- | --- | --- | --- | --- | --- |
| 2019 | 4 | 18% | 29% | 43% | 11% |
| 2020 | 4 | 13% | 16% | 28% | 43% |
| 2021 | 4 | 56% | 28% | 15% | 0% |
| 2022 | 4 | 0% | 37% | 43% | 20% |
| 2023 | 4 | 30% | 38% | 32% | 0% |
| 2024 | 4 | 29% | 50% | 16% | 5% |

## 3. ¿La señal del modelo de velas cambia según el régimen o el grupo?

Con las predicciones guardadas de LightGBM (primera versión) en los años que cubren los segmentos. Es descriptivo: no se entrenó nada con grupos ni regímenes, y operar solo en el régimen o el grupo que mejor salió sería una variante nueva. Unidades: bps; los t agrupan por día.

### Horizonte de 30 minutos

Por régimen (cada día se etiqueta con el modelo de regímenes de su propio año de prueba):

| Régimen | Días | Correlación de rangos | t | Operaciones | Ganancia bruta | Ganancia neta | t |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 362 | 0,0126 | 4,00 | 5.051 | 0,90 | -0,47 | -0,50 |
| 2 | 494 | 0,0178 | 6,78 | 11.500 | 2,45 | 1,01 | 1,00 |
| 3 | 442 | 0,0179 | 6,18 | 11.400 | 0,54 | -0,88 | -1,03 |
| 4 | 199 | 0,0210 | 5,18 | 8.463 | 2,99 | 1,48 | 0,92 |

Por grupo de características (el número de cada grupo se mantiene de un año a otro cuando el grupo se parece):

| Grupo | Retorno relativo siguiendo la predicción, sin filtrar | t | Operaciones | Ganancia bruta | Ganancia neta | t |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0,30 | 5,19 | 7.290 | 2,65 | 0,84 | 0,73 |
| 2 | 0,15 | 3,06 | 4.012 | 1,43 | -0,06 | -0,05 |
| 3 | 0,63 | 3,44 | 15.737 | 1,44 | 0,19 | 0,30 |
| 4 | 0,07 | 0,09 | 90 | -3,41 | -8,03 | -1,14 |
| 5 | 0,51 | 4,40 | 5.681 | 2,51 | 1,18 | 1,38 |
| 6 | 2,61 | 2,81 | 1.020 | 4,19 | 2,60 | 1,00 |
| 7 | 0,30 | 0,44 | 2.584 | -0,66 | -2,24 | -1,65 |

### Horizonte de 60 minutos

Por régimen (cada día se etiqueta con el modelo de regímenes de su propio año de prueba):

| Régimen | Días | Correlación de rangos | t | Operaciones | Ganancia bruta | Ganancia neta | t |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 362 | 0,0138 | 3,27 | 4.825 | -0,46 | -2,03 | -1,68 |
| 2 | 494 | 0,0220 | 6,16 | 9.573 | 4,54 | 2,87 | 1,79 |
| 3 | 442 | 0,0208 | 5,26 | 9.869 | -1,30 | -2,98 | -2,45 |
| 4 | 199 | 0,0232 | 4,19 | 6.880 | 9,14 | 7,35 | 2,31 |

Por grupo de características (el número de cada grupo se mantiene de un año a otro cuando el grupo se parece):

| Grupo | Retorno relativo siguiendo la predicción, sin filtrar | t | Operaciones | Ganancia bruta | Ganancia neta | t |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0,46 | 4,40 | 8.687 | 4,38 | 2,20 | 1,39 |
| 2 | 0,32 | 3,35 | 5.161 | 5,60 | 3,97 | 2,30 |
| 3 | 0,89 | 2,64 | 10.252 | 1,52 | 0,08 | 0,07 |
| 4 | 1,83 | 1,13 | 147 | 7,40 | 2,78 | 0,39 |
| 5 | 0,58 | 2,86 | 4.873 | 1,79 | 0,46 | 0,38 |
| 6 | 2,58 | 1,42 | 606 | 1,76 | 0,17 | 0,05 |
| 7 | 0,47 | 0,38 | 1.421 | -1,47 | -3,06 | -1,18 |
