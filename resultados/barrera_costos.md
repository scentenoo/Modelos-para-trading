# Barrera de costos (paso 2.1)

Generado el 2026-11-15 con `barrera_costos.py`. Velas y noticias desde 2023; spread de los últimos 60 días de mercado.

Unidades: bps = centésimas de punto porcentual (1 bps = 0,01%). Las cifras son la mediana de los 53 símbolos, salvo donde se indica.

## 1. Cuánto cuesta operar

| Franja (hora de Nueva York) | Spread mediano | Símbolo más barato | Símbolo más caro | Momentos con cotización |
| --- | --- | --- | --- | --- |
| Pre-mercado (7:00–9:30) | 24,6 bps | SPY (0,5) | HON (147,5) | 73% |
| Horario normal (9:30–16:00) | 2,7 bps | SPY (0,3) | HON (7,4) | 100% |
| Post-mercado (16:00–18:00) | 15,5 bps | QQQ (0,7) | HON (324,4) | 40% |

## 2. Cuánto se mueve el precio y qué acierto hace falta

| Franja | Horizonte | Movimiento, minuto cualquiera | Movimiento tras noticia | Esperado por la hora | Acierto mínimo, minuto cualquiera | Acierto mínimo, tras noticia | Símbolos con acierto mínimo ≤ 55% tras noticia |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pre-mercado | 5 min | 6,3 bps | 12,1 bps | 6,6 bps | imposible | imposible | 0 de 53 |
| Pre-mercado | 15 min | 11,5 bps | 21,0 bps | 12,0 bps | imposible | imposible | 2 de 53 |
| Pre-mercado | 30 min | 16,6 bps | 27,7 bps | 17,7 bps | imposible | 88,1% | 3 de 53 |
| Pre-mercado | 60 min | 24,8 bps | 37,3 bps | 25,4 bps | 97,5% | 79,1% | 4 de 53 |
| Horario normal | 5 min | 9,7 bps | 12,4 bps | 11,0 bps | 63,3% | 61,8% | 10 de 53 |
| Horario normal | 15 min | 16,2 bps | 21,3 bps | 17,9 bps | 57,9% | 56,7% | 19 de 53 |
| Horario normal | 30 min | 22,3 bps | 28,4 bps | 24,2 bps | 55,7% | 55,1% | 26 de 53 |
| Horario normal | 60 min | 30,7 bps | 38,6 bps | 32,7 bps | 54,1% | 53,7% | 39 de 53 |
| Post-mercado | 5 min | 3,5 bps | 7,6 bps | 4,0 bps | imposible | imposible | 3 de 52 |
| Post-mercado | 15 min | 6,7 bps | 12,7 bps | 7,0 bps | imposible | imposible | 8 de 52 |
| Post-mercado | 30 min | 9,0 bps | 16,0 bps | 9,8 bps | imposible | 98,7% | 12 de 52 |
| Post-mercado | 60 min | 12,0 bps | 19,2 bps | 12,4 bps | imposible | 97,3% | 14 de 52 |

## 2b. ¿Todas las noticias mueven el precio?

En horario normal. Un movimiento grande es el que solo supera el 10% de los minutos cualesquiera; si las noticias no importaran, el 10% de ellas iría seguido de uno.

| Horizonte | Noticias seguidas de un movimiento grande | Movimiento del 10% más fuerte, minuto cualquiera | Movimiento del 10% más fuerte, tras noticia |
| --- | --- | --- | --- |
| 5 min | 15,8% | 21,0 bps | 27,5 bps |
| 15 min | 16,2% | 35,2 bps | 45,5 bps |
| 30 min | 15,5% | 48,2 bps | 63,1 bps |
| 60 min | 14,8% | 65,9 bps | 82,9 bps |

## 3. Si el costo real fuera el doble

Las pruebas históricas suelen ser optimistas con el costo; esta tabla repite el acierto mínimo tras noticia con dos spreads en vez de uno.

| Franja | Horizonte | Acierto mínimo tras noticia | Símbolos con acierto mínimo ≤ 55% |
| --- | --- | --- | --- |
| Pre-mercado | 5 min | imposible | 0 de 53 |
| Pre-mercado | 15 min | imposible | 0 de 53 |
| Pre-mercado | 30 min | imposible | 0 de 53 |
| Pre-mercado | 60 min | imposible | 2 de 53 |
| Horario normal | 5 min | 73,6% | 4 de 53 |
| Horario normal | 15 min | 63,4% | 6 de 53 |
| Horario normal | 30 min | 60,3% | 10 de 53 |
| Horario normal | 60 min | 57,3% | 16 de 53 |
| Post-mercado | 5 min | imposible | 0 de 52 |
| Post-mercado | 15 min | imposible | 0 de 52 |
| Post-mercado | 30 min | imposible | 2 de 52 |
| Post-mercado | 60 min | imposible | 5 de 52 |

## 4. Cuántas operaciones harían falta en la Fase 3

Operaciones para demostrar una ganancia neta con 5% de significancia y 80% de potencia, en horario normal y operando tras noticia, según el acierto real que logre el sistema. Se calcula solo con los símbolos baratos de operar (acierto mínimo de 55% o menos en ese horizonte), usando sus medianas.

| Horizonte | Símbolos | Acierto 53% | Acierto 55% | Acierto 57% | Acierto 60% |
| --- | --- | --- | --- | --- | --- |
| 5 min | 10 | no gana | 52.813 | 4.580 | 1.081 |
| 15 min | 19 | no gana | 13.025 | 2.768 | 846 |
| 30 min | 26 | 1.042.804 | 7.177 | 1.953 | 662 |
| 60 min | 39 | 7.827.348 | 8.693 | 2.247 | 745 |

## 5. Por símbolo: horario normal, 15 minutos, tras noticia

| Símbolo | Spread | Movimiento tras noticia | Esperado por la hora | Noticias | Acierto mínimo |
| --- | --- | --- | --- | --- | --- |
| QQQ | 0,3 bps | 14,8 bps | 12,7 bps | 349 | 51,0% |
| IWM | 0,4 bps | 16,8 bps | 14,1 bps | 61 | 51,1% |
| SPY | 0,3 bps | 11,1 bps | 9,3 bps | 15.610 | 51,2% |
| NVDA | 0,9 bps | 31,0 bps | 30,4 bps | 3.341 | 51,4% |
| INTC | 1,6 bps | 45,3 bps | 35,9 bps | 1.021 | 51,8% |
| TSLA | 1,6 bps | 37,1 bps | 35,5 bps | 2.875 | 52,1% |
| NFLX | 1,4 bps | 27,4 bps | 22,3 bps | 1.170 | 52,6% |
| GOOGL | 1,1 bps | 21,4 bps | 19,3 bps | 2.180 | 52,7% |
| WMT | 0,9 bps | 17,2 bps | 14,6 bps | 1.074 | 52,8% |
| AAPL | 1,1 bps | 20,0 bps | 16,9 bps | 2.782 | 52,9% |
| NEE | 1,3 bps | 19,6 bps | 18,3 bps | 319 | 53,2% |
| AVGO | 2,2 bps | 32,0 bps | 29,3 bps | 799 | 53,4% |
| AMZN | 1,6 bps | 22,5 bps | 21,1 bps | 2.826 | 53,5% |
| KO | 1,1 bps | 14,2 bps | 11,8 bps | 363 | 53,9% |
| BAC | 1,8 bps | 21,3 bps | 18,4 bps | 741 | 54,2% |
| MSFT | 1,6 bps | 17,8 bps | 16,5 bps | 3.059 | 54,5% |
| ORCL | 3,7 bps | 39,2 bps | 26,8 bps | 1.002 | 54,7% |
| META | 2,7 bps | 28,2 bps | 24,3 bps | 2.421 | 54,9% |
| WFC | 2,3 bps | 24,0 bps | 20,3 bps | 675 | 54,9% |
| DIS | 1,9 bps | 18,7 bps | 16,3 bps | 1.166 | 55,0% |
| AMD | 4,6 bps | 45,0 bps | 36,4 bps | 1.136 | 55,1% |
| NKE | 2,7 bps | 24,4 bps | 19,4 bps | 679 | 55,5% |
| PEP | 2,0 bps | 18,1 bps | 15,3 bps | 407 | 55,6% |
| VZ | 2,2 bps | 17,9 bps | 16,5 bps | 506 | 56,0% |
| XOM | 2,4 bps | 19,7 bps | 17,7 bps | 771 | 56,2% |
| CVX | 2,3 bps | 17,9 bps | 16,0 bps | 663 | 56,5% |
| PG | 2,0 bps | 15,1 bps | 13,7 bps | 349 | 56,7% |
| SO | 2,3 bps | 16,4 bps | 14,4 bps | 203 | 56,9% |
| V | 2,3 bps | 15,7 bps | 14,4 bps | 644 | 57,3% |
| JPM | 2,9 bps | 19,8 bps | 16,7 bps | 1.136 | 57,3% |
| DUK | 2,5 bps | 16,6 bps | 15,2 bps | 231 | 57,5% |
| ADBE | 4,2 bps | 27,8 bps | 22,6 bps | 683 | 57,5% |
| COP | 2,9 bps | 19,4 bps | 20,6 bps | 380 | 57,6% |
| BA | 5,0 bps | 32,6 bps | 23,3 bps | 1.700 | 57,7% |
| UPS | 4,0 bps | 25,4 bps | 17,5 bps | 370 | 57,9% |
| GE | 4,1 bps | 24,2 bps | 21,3 bps | 469 | 58,4% |
| MCD | 2,8 bps | 16,5 bps | 13,4 bps | 625 | 58,4% |
| CRM | 5,3 bps | 31,5 bps | 23,7 bps | 882 | 58,4% |
| HD | 3,2 bps | 18,4 bps | 16,6 bps | 565 | 58,6% |
| PFE | 3,5 bps | 20,0 bps | 17,0 bps | 826 | 58,9% |
| T | 4,1 bps | 22,8 bps | 18,4 bps | 557 | 58,9% |
| UNH | 4,4 bps | 23,6 bps | 19,8 bps | 776 | 59,4% |
| MRK | 4,2 bps | 21,8 bps | 17,9 bps | 725 | 59,6% |
| MS | 4,9 bps | 24,3 bps | 20,9 bps | 737 | 60,1% |
| GS | 6,1 bps | 26,6 bps | 21,7 bps | 984 | 61,4% |
| JNJ | 3,7 bps | 15,9 bps | 13,7 bps | 749 | 61,5% |
| CAT | 6,6 bps | 26,8 bps | 21,8 bps | 470 | 62,4% |
| ABBV | 6,0 bps | 24,0 bps | 19,0 bps | 591 | 62,5% |
| COST | 4,7 bps | 18,7 bps | 15,3 bps | 697 | 62,5% |
| MA | 4,2 bps | 16,6 bps | 15,1 bps | 649 | 62,6% |
| LLY | 7,1 bps | 27,1 bps | 23,9 bps | 1.197 | 63,2% |
| LIN | 4,3 bps | 16,1 bps | 14,5 bps | 179 | 63,4% |
| HON | 7,4 bps | 22,1 bps | 17,4 bps | 333 | 66,8% |
