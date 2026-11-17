# Muestra final: evaluación de B

Generado el 2026-11-16 con `muestra_final.py`. Protocolo fijado el 16 de noviembre de 2026 antes de abrirla (documento del proyecto, sección 5). Periodo: 2025-01-01 a 2026-11-13, 466 días de mercado sin medios días. Modelo: `datos/modelos/final/` (entrenado 2026-11-16T16:36:24 con 2016-2024, pendiente 0,782), sin reentrenar. Variante 12: decisiones de 10:00 a 12:30 cada 30 minutos, entrada 20 minutos después, salida a las 15:55, una operación por acción y día, 36 acciones operables. Costo: el de la época (spread del trimestre corregido por la volatilidad del día; decide con el trimestre y el día anteriores y paga el del trimestre en curso); elasticidad 0,422 tomada solo de 2016-2024.

Unidades: bps por operación (1 bps = 0,01%).

## Conclusión

**B NO PASA la Fase 2** (3 de 5 criterios). No se sigue a la Fase 3 con este modelo.

| Criterio | Valor | Resultado |
| --- | --- | --- |
| 1. Ganancia neta por operación de al menos 1 bps | -2,75 bps | no pasa |
| 2. Mayor que la referencia (A) con t por bloques de al menos 1,65 | B -0,707 contra A -9,859 bps por acción operable y día; diferencia 9,152, t 5,78 | pasa |
| 3. Neta no negativa con el costo doble | -4,58 bps | no pasa |
| 4. Al menos 2.000 operaciones | 4.673 operaciones | pasa |
| 5. Neta positiva en al menos la mitad de los trimestres | 5 de 8 trimestres | pasa |

## Resultado de B

| Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | Neta con costo doble |
| --- | --- | --- | --- | --- | --- | --- |
| 4.673 | 466 de 466 | 49,6% | -0,92 | 1,83 | -2,75 | -4,58 |

## Referencia (A) de 60 minutos con el costo de la época

Mismas operaciones de las reglas fijas de `referencia.py` con 60 minutos; costo de la época (atras=0). Ganancia neta diaria en bps por acción operable (suma por día entre 39 acciones operables a 60 minutos; días sin operaciones valen 0). t por bloques de la diferencia B - A con el remuestreo de `comparaciones.py` (bloques de 10 días, 10.000 remuestreos, semilla 7); una cola, 5%: t >= 1,65.

| | Operaciones | Neta por operación | Neta diaria por acción operable |
| --- | --- | --- | --- |
| A · referencia 60 min | 68.569 | -2,61 | -9,859 |
| B | 4.673 | -2,75 | -0,707 |
| B - A | | | 9,152 (t por bloques 5,78) |

## Información adicional (no decide)

### Contra cero

Neta -2,75 bps por operación; t por bloques -0,96 (ganancia neta diaria, suma por día, días sin operaciones valen 0; t por días -0,88). Con costo doble: neta -4,58, t por bloques -1,58.

### Por trimestre

| Trimestre | Operaciones | Costo medio | Neta por operación | Ganancia neta total (bps) | Neta con costo doble |
| --- | --- | --- | --- | --- | --- |
| 2025Q1 | 575 | 2,07 | 8,07 | 4.642 | 6,01 |
| 2025Q2 | 551 | 1,98 | -17,64 | -9.720 | -19,62 |
| 2025Q3 | 509 | 1,44 | -2,46 | -1.253 | -3,91 |
| 2025Q4 | 607 | 1,62 | 6,67 | 4.046 | 5,05 |
| 2026Q1 | 644 | 1,57 | 0,64 | 414 | -0,93 |
| 2026Q2 | 742 | 1,99 | -16,81 | -12.471 | -18,80 |
| 2026Q3 | 676 | 1,96 | 0,77 | 519 | -1,19 |
| 2026Q4 | 369 | 2,00 | 2,66 | 981 | 0,66 |

### Selección y mercado

Ganancia bruta = selección (dirección por el retorno relativo) + mercado (el resto).

| Parte | Media por operación | t por días |
| --- | --- | --- |
| Selección | -0,96 | -0,44 |
| Mercado | 0,04 | 0,02 |

### Por momento de entrada

| Entrada | Operaciones | Neta por operación |
| --- | --- | --- |
| 10:20 | 3.375 | -2,53 |
| 10:50 | 523 | 4,34 |
| 11:20 | 320 | -1,85 |
| 11:50 | 204 | -11,71 |
| 12:20 | 122 | -15,96 |
| 12:50 | 129 | -12,86 |

### Costo corregido por los bordes

Razones medianas de apertura y cierre por símbolo, de las muestras de 2016-2024 (`datos/spread_bordes`); mismas operaciones, solo cambia lo que se paga: 0,5 x costo x R(apertura) + 0,5 x costo x R(cierre). Símbolos operados con razones: 33 de 33.

| Costo | Operaciones | Costo medio | Ganancia neta | t por bloques | Neta con costo doble | t por bloques (doble) |
| --- | --- | --- | --- | --- | --- | --- |
| De la época | 4.673 | 1,83 | -2,75 | -0,96 | -4,58 | -1,58 |
| Corregido por los bordes | 4.673 | 1,79 | -2,71 | -0,94 | -4,51 | -1,56 |

Regla del control de bordes: neta corregida positiva y t por bloques de al menos 1,65. Aquí es solo información.

Tiempo de la corrida: 0.2 minutos.
