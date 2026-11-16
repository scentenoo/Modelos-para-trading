# Control del costo en los bordes (idea 5)

Operaciones: `datos/modelos/operaciones_cierre_retraso20.parquet`.

Generado el 2026-11-16 con `costo_bordes.py`. Aplica la regla fijada el 16 de noviembre de 2026, antes de medir (documento del proyecto, "Control del costo en los bordes"). Mismas operaciones de `horizonte_largo.py`; solo cambia lo que se paga: 0,5 x costo de la época x R(apertura) + 0,5 x costo de la época x R(cierre), con R la mediana, por símbolo y franja, del spread medido dividido por el de horario normal de su trimestre corregido por la volatilidad de su día. Sin muestra final.

Símbolos operados por la idea 5 con muestras de bordes: 36 de 36. Están todos.

Entradas fuera de la franja de apertura medida (10:00-10:35): 6.814 de 23.932 operaciones (28,5%); a ellas se les aplica igual la razón de la apertura (regla, punto 3).

## Razón mediana por franja (todas las acciones medidas)

| Franja | Muestras válidas | Razón mediana (todas las muestras) | Mediana de las razones por símbolo |
| --- | --- | --- | --- |
| apertura | 5.181 | 1,114 | 1,127 |
| cierre | 5.141 | 0,854 | 0,781 |

Muestras sin razón (sin denominador o sin spread): 46 de 10.368.

## Razón por símbolo

| Símbolo | R apertura | Muestras apertura | R cierre | Muestras cierre |
| --- | --- | --- | --- | --- |
| AAPL | 1,080 | 144 | 0,986 | 143 |
| ADBE | 1,387 | 144 | 0,531 | 143 |
| AMD | 1,049 | 144 | 0,970 | 144 |
| AMZN | 1,129 | 144 | 0,769 | 143 |
| AVGO | 1,330 | 144 | 0,475 | 144 |
| BA | 1,338 | 144 | 0,526 | 143 |
| BAC | 1,010 | 144 | 1,022 | 143 |
| COP | 1,084 | 144 | 0,903 | 144 |
| CRM | 1,508 | 144 | 0,550 | 143 |
| CVX | 1,424 | 144 | 0,708 | 143 |
| DIS | 1,116 | 144 | 0,694 | 143 |
| DUK | 1,175 | 144 | 0,575 | 143 |
| GE | 1,048 | 144 | 0,937 | 140 |
| GOOGL | 1,125 | 144 | 0,779 | 144 |
| HD | 1,487 | 144 | 0,583 | 143 |
| INTC | 1,001 | 144 | 1,002 | 144 |
| JPM | 1,081 | 144 | 0,940 | 143 |
| KO | 1,019 | 144 | 0,998 | 142 |
| MCD | 1,374 | 144 | 0,541 | 143 |
| META | 1,186 | 144 | 0,783 | 144 |
| MSFT | 1,107 | 144 | 1,000 | 144 |
| NEE | 1,305 | 144 | 0,571 | 142 |
| NFLX | 1,208 | 144 | 0,564 | 142 |
| NKE | 1,161 | 143 | 0,769 | 141 |
| NVDA | 1,235 | 144 | 0,621 | 143 |
| ORCL | 1,048 | 143 | 0,932 | 143 |
| PEP | 1,349 | 144 | 0,803 | 143 |
| PG | 1,063 | 144 | 0,920 | 140 |
| SO | 1,049 | 144 | 0,985 | 143 |
| TSLA | 1,168 | 144 | 0,599 | 142 |
| UPS | 1,405 | 143 | 0,531 | 142 |
| V | 1,246 | 144 | 0,690 | 142 |
| VZ | 1,018 | 144 | 1,014 | 142 |
| WFC | 1,019 | 144 | 0,996 | 144 |
| WMT | 1,100 | 144 | 0,872 | 143 |
| XOM | 1,023 | 144 | 0,980 | 143 |

## Razón por año (mediana entre muestras)

| Año | Apertura | Muestras | Cierre | Muestras |
| --- | --- | --- | --- | --- |
| 2016 | 1,063 | 575 | 0,929 | 575 |
| 2017 | 1,060 | 576 | 0,946 | 572 |
| 2018 | 1,066 | 578 | 0,880 | 569 |
| 2019 | 1,107 | 574 | 0,867 | 569 |
| 2020 | 1,150 | 578 | 0,833 | 575 |
| 2021 | 1,144 | 572 | 0,859 | 569 |
| 2022 | 1,213 | 576 | 0,713 | 571 |
| 2023 | 1,148 | 576 | 0,701 | 573 |
| 2024 | 1,235 | 576 | 0,777 | 568 |

## Resultado de la idea 5

Mismas operaciones en las dos filas (símbolos con muestras de bordes). t por bloques sobre la ganancia neta diaria (días desde 2020 y antes de la muestra final, sin medios días; días sin operaciones valen 0; `horizonte_largo.t_bloques`).

| Costo | Operaciones | Costo medio | Ganancia neta | t por bloques | Neta con costo doble | t por bloques (doble) |
| --- | --- | --- | --- | --- | --- | --- |
| De la época (antes) | 23.932 | 2,15 | 3,07 | 2,15 | 0,92 | 0,66 |
| Corregido por los bordes | 23.932 | 2,09 | 3,12 | 2,18 | 1,03 | 0,74 |

### Por año

| Año | Operaciones | Costo época | Neta época | Costo corregido | Neta corregida | t por bloques (corregida) | Neta corregida con costo doble |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 5.099 | 2,56 | 11,69 | 2,50 | 11,75 | 3,21 | 9,25 |
| 2021 | 6.304 | 2,00 | 1,12 | 1,95 | 1,17 | 0,66 | -0,78 |
| 2022 | 6.805 | 2,53 | 1,81 | 2,46 | 1,89 | 0,67 | -0,57 |
| 2023 | 3.577 | 1,48 | -0,16 | 1,45 | -0,13 | -0,05 | -1,57 |
| 2024 | 2.147 | 1,49 | -2,32 | 1,46 | -2,29 | -0,97 | -3,75 |

## Decisión (regla del documento)

Neta corregida 3,12 bps, t por bloques 2,18 (se exige neta positiva y t de al menos 1,65, una cola, sin corregir).

**La salida a las 15:55 queda como horizonte de B.**
