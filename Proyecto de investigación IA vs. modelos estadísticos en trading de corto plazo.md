# IA para noticias + modelos estadísticos en trading de corto plazo

Proyecto de investigación · @Samir Centeno · versión 3 · 16 de noviembre de 2026

## 1. Resumen

**Objetivo:** construir un sistema de corto plazo que gane dinero después de costos. Cada parte hace lo que mejor sabe hacer: la IA lee noticias y los modelos de árboles trabajan con los números de las velas.

**Pregunta:** ¿la información que una IA saca de las noticias mejora la ganancia neta de un modelo estadístico de corto plazo? ¿Mejora más a medida que crece el modelo de IA?

- **H0:** agregar la IA no aumenta la ganancia neta por operación frente al modelo de velas solo ni frente a la referencia.
- **H1:** el sistema con IA obtiene una ganancia neta por operación mayor, con significancia estadística.

**Alcance:** SPY, QQQ, IWM y 50 acciones líquidas de EE. UU., con velas de 1 minuto. Se investiga con las 53 y se opera solo en las baratas de operar: 39 a 60 minutos y 26 a 30 minutos. Quedan fuera por ahora opciones, cripto, apalancamiento y la Bolsa de Valores de Colombia.

**Naturaleza:** es un proyecto de investigación. El dinero real llega solo si H0 se rechaza.

**Dónde vamos:** Fase 1 (datos) completa: las cinco fuentes están descargadas, comprobadas y se actualizan solas cada noche. Fase 2 en curso: la barrera de costos está medida (paso 2.1), las variables están construidas (paso 2.2), la referencia está programada (paso 2.5), los grupos de acciones y los regímenes de mercado están calculados (pasos 2.3 y 2.4) y hay dos versiones del modelo de velas (paso 2.6): las dos tienen señal, pero ninguna paga los costos. Calibrar la predicción (paso 2.6.c) mejora la segunda: a 60 minutos da 2,07 bps netos por operación y no pierde con el costo doble, pero no se sostiene al revisarla: depende de marzo de 2020, casi un tercio es movimiento del mercado y no selección, y corregida por las 10 variantes probadas no se distingue de cero (SPA de Hansen, p = 0,23). El modelo sí elige bien las acciones (t de 4,6 a 5,3 en la parte de selección), pero gana unos 2,2 a 2,6 bps brutos por operación contra un costo de 1,5 a 1,7. El filtro de operaciones (meta-labeling) se probó y no le gana a la calibración. Al volver a costear las operaciones con el spread de cada época, la ganancia se borra: el modelo opera en días de mucha volatilidad, cuando el spread es más del doble del que se usaba, y la calibrada a 60 minutos baja a 0,51 bps (t 0,57). Desde el 16 de noviembre de 2026 el costo oficial es el spread de cada época y la prueba oficial usa remuestreo por bloques. Con esas reglas se probó un horizonte hasta las 15:55 (idea 5): da 2,87 bps netos por operación (t 2,30) y no pierde con el costo doble, el mejor resultado hasta ahora, pero no llega al t de 2,61 que exigen las 11 variantes probadas (SPA de Hansen, p = 0,083) y sin 2020 baja a 1,24 bps. Las instrucciones para que la IA lea noticias están diseñadas y programadas con un modelo simulado (paso 2.9). Los criterios de éxito (paso 0.4) están confirmados.

## 2. Cómo funciona el sistema

### Reparto del trabajo

| Parte | Qué lee | Qué entrega |
| --- | --- | --- |
| Modelo de árboles (XGBoost/LightGBM) | Velas: precio y volumen de cada minuto | Un orden de las acciones, de la que más va a subir a la que menos |
| IA (LLM) | Noticias y comunicados de la empresa | Variables sobre cada noticia: tono, tipo de evento, sorpresa, relevancia |
| Capa de riesgo | Las predicciones de cualquier competidor | Cuánto apostar en cada operación y cuándo parar |

**El horizonte es de 30 y 60 minutos**, en horario normal de mercado; 15 minutos queda como comparación. Sale de la medición del paso 2.1 (sección 3): a 5 minutos el costo solo deja operar unas 10 acciones, y a 60 minutos deja 39. Sigue siendo corto plazo, pero ya no es una carrera de velocidad, y le da tiempo a un modelo grande de leer la noticia sin llegar tarde.

**No se opera todo.** Solo una de cada seis noticias va seguida de un movimiento grande. El sistema gana si distingue esas; operar tras cada noticia pierde por costos.

**Lo que sale fuera del horario normal** (casi la mitad de las noticias y el 84% de los comunicados) no se opera en el momento, porque ahí el costo es entre 6 y 9 veces mayor. Se usa como señal para la apertura siguiente.

### Los cuatro competidores

Todos operan las mismas acciones, al mismo tiempo y con la misma capa de riesgo. La comparación clave es **D contra B**: si agregar la IA al modelo de velas aumenta la ganancia neta.

| Competidor | Qué usa | Para qué está |
| --- | --- | --- |
| A · Referencia | Cuatro efectos documentados: impulso intradía (la primera media hora predice la última), reversión de corto plazo, deriva después de resultados trimestrales y ruptura del rango de apertura (los primeros 15 minutos) | Piso: si nadie le gana, no hay ventaja |
| B · Modelo de velas | XGBoost/LightGBM con precio y volumen | Lo mejor que se logra sin IA |
| C · IA sola | El LLM lee la noticia y decide | Mide cuánto vale la noticia por sí sola |
| D · IA + velas | Las variables que la IA saca de la noticia, más las de velas, más la reacción del precio frente al tono (noticia buena sin subida, noticia mala sin caída) | Hipótesis principal |

### Diseño por escala

C y D se corren con LLM de distinto tamaño: local pequeño (1–3B), local mediano (7–8B), Claude Haiku y un Claude grande. Si el tamaño importa, la ganancia neta debe subir con el tamaño. Se prueba con una prueba de tendencia sobre el orden de los modelos, porque Anthropic no publica el número de parámetros de Claude. La latencia se registra aparte: un modelo más grande puede entender mejor la noticia pero llegar tarde.

### Regla sobre la IA y el pasado

Un LLM ya vio en su entrenamiento qué pasó después de las noticias viejas, así que evaluarlo con noticias anteriores a su fecha de corte es hacer trampa sin querer.

- Los modelos de velas se entrenan y se filtran con el histórico completo.
- La IA se evalúa solo con noticias posteriores a su fecha de corte, es decir, en vivo.
- El histórico de noticias sirve para variables que no usan IA (cuántas noticias hay, a qué hora, de qué fuente) y para afinar las instrucciones que se le dan a la IA, nunca para medir su desempeño.

## 3. Paso a paso

Cada fase avanza solo si cumple su criterio de salida.

| Fase | Cuándo | Estado | Criterio de salida |
| --- | --- | --- | --- |
| 0 · Preparación | Semana 1 | Completa | Llaves funcionando y criterios de éxito escritos |
| 1 · Datos | Semanas 2–3 | Completa | La base se actualiza sola sin intervención |
| 2 · Investigación histórica | Semanas 4–11 | En curso: la segunda versión calibrada gana a 60 minutos, sin significancia suficiente todavía | Un modelo de velas supera la referencia en ganancia neta fuera de muestra, corregido por comparaciones múltiples |
| 3 · Experimento en vivo (cuenta de papel) | \~5 meses, por confirmar | Por empezar | IA + velas rechaza H0 frente al modelo de velas solo |
| 4 · Dinero real | Después | Por empezar | — |

### Fase 0 · Preparación

- [x] 0.1 Cuenta de papel en Alpaca (100.000 dólares ficticios).
- [x] 0.2 Llaves de API guardadas en `.env`, que no se sube a GitHub.
- [x] 0.3 Entorno de Python (`.venv`) con las dependencias de `requirements.txt`.
- [x] 0.4 Criterios de éxito escritos con números, antes de mirar resultados del modelo. Están en la sección 5.

### Fase 1 · Datos

- [x] 1.1 Velas de 1 minuto, ajustadas: 70,9 millones de velas de los 53 símbolos, 2016–2026. Quedan como copia de comprobación en `datos/minuto_ajustado`.
- [x] 1.2 Velas de 1 minuto, sin ajustar: 70,9 millones de velas en `datos/minuto`, 2,2 GB, sin errores. Son la base de trabajo.
- [x] 1.3 Ajustes corporativos: 1.944 dividendos, 16 splits y 7 escisiones, en `datos/ajustes`.
- [x] 1.4 Ajuste al leer: `precios.py` corrige splits, dividendos y escisiones.
- [x] 1.5 Ajuste comprobado contra la copia ajustada en los 53 símbolos: 49 coinciden con una diferencia máxima de 0,08%. Las otras cuatro tienen escisiones, donde el ajuste es aproximado (ver sección 4).
- [x] 1.6 Noticias: 339.955 noticias de 2016 a hoy, en `datos/noticias`.
- [x] 1.7 Comunicados oficiales 8-K de la SEC: 8.333 comunicados de las 50 acciones (2.342 de resultados trimestrales) y 14.272 documentos de texto, en `datos/sec`.
- [x] 1.8 Cifras financieras de la SEC: las 50 acciones, en `datos/sec/cifras`.
- [x] 1.9 Actualización diaria: `actualizar.py` pone al día las cuatro fuentes en 13 minutos y deja registro en `datos/registros`. Una tarea programada de Windows lo corre cada noche a las 9:00 p. m., si el portátil está encendido; si estaba apagado, corre al encenderlo.

### Fase 2 · Investigación histórica

Plazo máximo: 6–8 semanas. El mejor modelo de velas pasa al experimento en vivo.

**Orden de trabajo:** 2.1 → 2.2 → 2.5 → 2.6 → 2.3 → 2.4 → 2.7 → 2.8 → 2.9. La segmentación y los regímenes (2.3 y 2.4) van después del primer modelo, para medir si agrupar mejora algo frente a un modelo simple, en vez de suponerlo.

- [x] 2.1 **Medir la barrera de costos.** Hecho con `muestrear_spread.py` y `barrera_costos.py`; el detalle por acción está en `resultados/barrera_costos.md`. Ver el resumen abajo.
- [x] 2.2 **Variables por acción:** `variables.py` arma una fila por acción cada 15 minutos en horario normal: 3,6 millones de filas y 41 columnas en `datos/variables` (retornos pasados, volatilidad, posición en el rango del día, volumen relativo, beta, retornos sin la parte del mercado, conteo de noticias, sector y los retornos futuros a 15, 30 y 60 minutos). Se comprobó con 1.800 pruebas que ninguna variable usa información posterior al momento de decisión.
- [x] 2.3 **Segmentar las acciones:** hecho con `segmentos.py`: PCA sobre los retornos y clustering jerárquico sobre la correlación, y K-means sobre las características de cada acción. Ver el resumen abajo.
- [x] 2.4 **Segmentar el tiempo en regímenes:** hecho con `segmentos.py`: mezcla gaussiana sobre volatilidad, tendencia y dispersión, con rasgos conocidos antes de la apertura. No se usa un modelo oculto de Markov, porque sus estados suavizados miran el futuro. Ver el resumen abajo.
- [x] 2.5 **Programar la referencia (competidor A):** `referencia.py` aplica los cuatro efectos documentados con reglas fijas; el detalle está en `resultados/referencia.md`. Ver el resumen abajo.
- [ ] 2.6 **Entrenar los modelos de velas (competidor B):** dos versiones hechas con `modelo_velas.py` y una calibración con `calibracion.py` (ver los resúmenes abajo); falta una versión que pague los costos con significancia. Plan de mejora, en este orden:
  - [x] 2.6.a **Variables comparativas:** el puesto de cada acción frente a las demás en ese momento (retornos, volumen, volatilidad) y su retorno frente al promedio de su sector. El modelo predice un orden, y hasta ahora casi todas sus variables eran de la acción sola.
  - [x] 2.6.b **Búsqueda de hiperparámetros dentro de cada entrenamiento:** para cada año de prueba se eligen con el último año anterior, nunca con el año de prueba, así que no suma variantes por combinación. La idea sale del taller de tidymodels de Freddy Hernández, cambiando la validación cruzada al azar por una que respeta el tiempo.
  - [x] 2.6.c **Calibrar la predicción:** el modelo exagera (en la décima más fuerte predice cerca del doble de lo que ocurre), así que el filtro de costo deja pasar operaciones que no pagan. Se corrige con años anteriores al de prueba. Reutiliza las predicciones guardadas, sin reentrenar. Hecho con `calibracion.py` el 16 de noviembre de 2026, con la regla fijada antes de correr (ver el resumen abajo). Cuenta como una variante por horizonte: con ella van 8 variantes probadas.
  - [ ] 2.6.d Grupos y regímenes como variables (pasos 2.3 y 2.4). Baja de prioridad: el diagnóstico mostró que la señal está en los cuatro regímenes.
  - 2.6.a y 2.6.b se probaron juntas como segunda versión, para gastar una sola variante por horizonte; la corrida completa tarda unos 80 minutos en el portátil. XGBoost/LightGBM como modelo principal, por grupo. Regresión logística como base. MLP/LSTM pequeño solo si le gana a XGBoost fuera de muestra. Se predice el retorno de cada acción relativo al de las demás, y se opera solo cuando la ganancia esperada supera el costo.
- [ ] 2.7 **Controles para comparar:** un modelo global con grupo y régimen como variables, y un modelo multinivel en el que cada grupo tiene sus propios coeficientes pero se acercan a la media general cuando tiene pocos datos.
- [ ] 2.8 **Revisión contra el sobreajuste** antes de aprobar un modelo, con `backtest-expert` y `residual-edge-analyzer`.
- [ ] 2.9 **Montar lo que se dejó para el final:** el PC viejo como servidor, los modelos de IA locales y las instrucciones para que la IA lea noticias.

#### Resultado del paso 2.1

Acierto mínimo: el porcentaje de veces que hay que acertar la dirección para no perder, operando tras una noticia y pagando un spread completo por entrar y salir. Mediana de los 53 símbolos, con velas desde 2023.

| Horizonte | Costo en horario normal | Movimiento tras noticia | Acierto mínimo | Acciones con acierto mínimo de 55% o menos |
| --- | --- | --- | --- | --- |
| 5 min | 2,7 bps | 12,4 bps | 61,8% | 10 de 53 |
| 15 min | 2,7 bps | 21,3 bps | 56,7% | 19 de 53 |
| 30 min | 2,7 bps | 28,4 bps | 55,1% | 26 de 53 |
| 60 min | 2,7 bps | 38,6 bps | 53,7% | 39 de 53 |

(1 bps = 0,01%.)

- **Fuera del horario normal no se puede operar** la mayoría de las acciones: el costo mediano es 24,6 bps en el pre-mercado y 15,5 en el post-mercado, contra 2,7 en horario normal. Solo los ETF y unas pocas acciones muy grandes lo permiten.
- **La noticia promedio mueve poco:** el precio se mueve cerca de un 20% más que a esa misma hora sin noticia. La mayoría de las noticias son ruido: solo el 16% va seguida de un movimiento grande, contra el 10% que se esperaría por azar. El valor de la IA está en distinguir ese 16%.
- **Las más baratas de operar:** QQQ, IWM, SPY, NVDA, INTC, TSLA, NFLX, GOOGL, WMT y AAPL.
- **Si el costo real fuera el doble,** a 60 minutos quedarían 16 acciones y a 5 minutos, 4.
- **Tamaño de muestra de la Fase 3:** con un acierto real de 57% hacen falta entre 2.000 y 4.600 operaciones según el horizonte; con 55%, entre 7.000 y 53.000. Con 53% no alcanza.

Límites de la medición: no incluye comisiones ni el efecto del tamaño de la orden; supone que se gana y se pierde lo mismo en promedio; y un modelo que solo opera cuando está seguro puede necesitar menos acierto que el promedio.

#### Resultado del paso 2.5

Ganancia por operación de la referencia en 2016–2024 (sin la muestra final), con un spread completo de costo.

| Horizonte | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta |
| --- | --- | --- | --- | --- | --- |
| 30 min (26 símbolos) | 362.846 | 50,0% | 0,12 bps | 1,93 bps | −1,81 bps |
| 60 min (39 símbolos) | 330.750 | 49,8% | 0,03 bps | 2,40 bps | −2,37 bps |

- **Ninguno de los cuatro efectos gana después de costos** en estas acciones: antes de costos quedan en cero y el costo se lleva el resto. Pasa en los dos horizontes y en casi todos los años.
- **El piso real es no operar** (ganancia cero). El modelo de velas tiene que dar ganancia neta positiva, no solo perder menos que la referencia.
- **Deriva tras resultados** tiene pocas operaciones (888 a 30 minutos) y su resultado cambia de signo de un año a otro: no se distingue de cero.
- Las reglas son las versiones más simples de cada efecto, fijadas de antemano. No se afinaron para que ganen, porque eso sería ajustar la referencia a los datos.

Límites: el costo usa el spread de los últimos 60 días para toda la historia, y la deriva es una versión dentro del día de un efecto que se documentó a varios días.

#### Resultado del paso 2.6, primera versión

Validación hacia adelante de 2019 a 2024 (cada año se predice con un modelo entrenado con los anteriores), sin la muestra final. LightGBM con parámetros fijados de antemano; opera solo cuando la ganancia esperada supera el costo. El detalle está en `resultados/modelo_velas.md`.

| Horizonte | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30 min (23 acciones) | 36.414 | 51,6% | 1,76 bps | 1,44 bps | 0,32 bps | 0,56 | −1,12 bps |
| 60 min (36 acciones) | 31.147 | 51,3% | 2,93 bps | 1,68 bps | 1,25 bps | 1,29 | −0,44 bps |

- **El modelo sí ordena las acciones mejor que el azar,** y eso no es casualidad (t de 10 a 11 sobre la correlación entre el orden predicho y el real). La referencia no tenía ninguna señal.
- **La señal es pequeña frente al costo.** La décima parte de las predicciones más fuertes acierta por 1,1 a 1,8 bps, y operar cuesta entre 1,4 y 1,7.
- **La ganancia neta no se distingue de cero** (t menor que 2) y es negativa con el costo doble. A 60 minutos casi todo viene de 2020; en 2019 y 2023 pierde.
- **Con este resultado no pasaría los criterios** de la sección 5.
- La regresión logística, la base simple, opera muy poco y no gana.
- Variantes probadas hasta ahora: 4 (dos modelos por dos horizontes).

#### Resultado del paso 2.6, segunda versión

Misma validación, con variables comparativas y búsqueda de hiperparámetros (16 de noviembre de 2026).

| Horizonte | Versión | Correlación de rangos (t) | Operaciones | Ganancia neta | t | Neta con costo doble |
| --- | --- | --- | --- | --- | --- | --- |
| 30 min | Primera | 0,0170 (11,09) | 36.414 | 0,32 bps | 0,56 | −1,12 bps |
| 30 min | Segunda | 0,0190 (13,30) | 49.056 | 0,31 bps | 0,72 | −1,21 bps |
| 60 min | Primera | 0,0198 (9,52) | 31.147 | 1,25 bps | 1,29 | −0,44 bps |
| 60 min | Segunda | 0,0218 (10,99) | 51.847 | 0,99 bps | 1,63 | −0,90 bps |

- **Ordena un poco mejor** (la correlación de rangos sube cerca de un 10%), **pero no gana más:** opera entre 35% y 66% más con casi la misma ganancia por operación.
- **Sigue sin pasar los criterios** de la sección 5: t menor que 2 y ganancia negativa con el costo doble.
- **Depende menos de 2020:** a 60 minutos ese año baja de 8,22 a 4,38 bps. En 2019, 2022 y 2023 sigue perdiendo.
- **Exagera más que la primera:** en la décima más fuerte a 60 minutos predice 3,75 bps y lo real es 1,79.
- **La búsqueda casi siempre elige el máximo** (500 árboles): la rejilla se queda corta por arriba.
- Variantes probadas hasta ahora: 6 (tres modelos por dos horizontes).

#### Resultado del paso 2.6.c, calibración

La predicción de cada año se multiplica por una pendiente calculada con los años de prueba anteriores, y se opera igual que antes. La comparación va de 2020 a 2024, porque 2019 no tiene años anteriores para calibrar; la segunda versión sin calibrar se mide en esos mismos años. El detalle está en `resultados/calibracion.md`.

| Horizonte | Versión | Operaciones | Ganancia neta | t | Neta con costo doble |
| --- | --- | --- | --- | --- | --- |
| 30 min | Segunda | 44.494 | 0,42 bps | 0,91 | −1,11 bps |
| 30 min | Segunda calibrada | 26.661 | 0,94 bps | 1,61 | −0,51 bps |
| 60 min | Segunda | 48.635 | 1,20 bps | 1,88 | −0,71 bps |
| 60 min | Segunda calibrada | 25.272 | 2,07 bps | 2,29 | 0,37 bps |

- **Opera cerca de la mitad y gana más por operación.** La pendiente sale entre 0,39 y 0,83: el modelo exageraba entre un 20% y un 60%.
- **A 60 minutos es el mejor resultado hasta ahora:** por primera vez la ganancia no es negativa con el costo doble y el t pasa de 2.
- **No alcanza para darlo por bueno.** Con 8 variantes el t exigido es 2,50 y da 2,29; con el costo doble la ganancia no se distingue de cero (t 0,41); y solo 10 de 20 trimestres son positivos.
- **Sigue dependiendo de 2020:** a 60 minutos ese año da 9,71 bps por operación, 2021 y 2022 quedan cerca de cero y 2023 pierde 1,34.
- **A 30 minutos** mejora menos y sigue negativa con el costo doble.
- La calibración queda como parte fija del modelo de velas. Estos números son del periodo de desarrollo; los criterios de la sección 5 se miden en la muestra final.
- Variantes probadas hasta ahora: 8.

#### Resultado del filtro de operaciones (meta-labeling)

Hecho con `filtro.py` el 16 de noviembre de 2026, con el diseño anotado en "Ideas en reserva". El detalle está en `resultados/filtro.md`.

| Horizonte | Periodo | Versión | Operaciones | Ganancia neta | t | Neta con costo doble |
| --- | --- | --- | --- | --- | --- | --- |
| 30 min | 2020–2024 | Calibrada | 26.661 | 0,94 bps | 1,61 | −0,51 bps |
| 30 min | 2020–2024 | Con filtro | 40.763 | 0,21 bps | 0,47 | −1,27 bps |
| 60 min | 2020–2024 | Calibrada | 25.272 | 2,07 bps | 2,29 | 0,37 bps |
| 60 min | 2020–2024 | Con filtro | 38.167 | 1,17 bps | 1,58 | −0,71 bps |
| 60 min | 2021–2024 | Calibrada | 20.698 | 0,38 bps | 0,43 | −1,33 bps |
| 60 min | 2021–2024 | Con filtro | 23.463 | 0,36 bps | 0,46 | −1,35 bps |

- **No le gana a la calibración** en ningún horizonte. Se descarta con este diseño.
- **Aprendió a detectar volatilidad, no aciertos.** Su variable principal es el movimiento esperado frente al spread (37% a 47% del peso): con mucha volatilidad, cualquier operación tiene cerca de 50% de probabilidad de superar dos spreads, acierte o no la dirección.
- **Distingue poco:** AUC de 0,52 a 0,55, y la probabilidad calibrada casi no sale de 48% a 52%. No sirve como entrada para Kelly.
- **El umbral no se traslada bien de un año a otro:** elegido como el 10% más alto en un año tranquilo, en 2020 y 2022 deja pasar el 20% de las candidatas.
- **A favor:** a 60 minutos tiene 13 de 20 trimestres positivos (la calibrada, 10) y gana en 2023. No alcanza para preferirlo.
- Si se retoma, el filtro tendría que predecir la ganancia medida en unidades de volatilidad, no una etiqueta de sí o no. Sería otra variante.
- Variantes probadas hasta ahora: 10. Con Bonferroni, el t exigido es 2,58.

#### Revisión de la ganancia de la versión calibrada a 60 minutos

Adelanto del paso 2.8, hecho el 16 de noviembre de 2026 con `ventaja.py`, que usa `residual-edge-analyzer` sobre la ganancia neta diaria de 2020–2024. Es descriptivo y no cuenta como variante. El detalle de los dos horizontes está en `resultados/ventaja.md`.

- **No es exposición al mercado:** SPY explica el 2% de la variación diaria y la beta es −0,02. Con el promedio de las 50 acciones, o sumando la referencia, la conclusión no cambia.
- **Está concentrada en pocos días:** los 10 mejores días aportan 40.307 de los 52.234 bps de ganancia total (77%). Marzo de 2020 solo aporta 25.532.
- **Sin esos días no queda ventaja medible:** sin los 10 mejores días da 0,48 bps por operación (t 0,65); sin 2020 da 0,38 bps (t 0,43) y −1,33 con el costo doble.
- **Las compras ganan más que las ventas:** 4,68 bps contra 0,59, y solo el 36% de las operaciones son compras.
- **Por acción:** 23 de 36 ganan; NVDA aporta el 28% y AAPL el 16%.
- **Selección y mercado:** al partir la ganancia bruta de cada operación entre lo que la acción hizo frente al promedio de las 50 (selección) y lo que hizo ese promedio (mercado), a 60 minutos salen 2,59 bps de selección (t 4,64) y 1,17 de mercado (t 2,22). El mercado viene casi todo de las compras de 2020 (9,10 bps por operación). Si cada operación se cubriera con el promedio de las 50, la ganancia neta bajaría de 2,07 a 0,90 bps (t 1,61), sin contar el costo de la cobertura. A 30 minutos el mercado casi no pesa: 2,17 de selección (t 5,31) y 0,22 de mercado.
- **La selección es real en compras y en ventas,** pero mayor en las compras (3,79 contra 1,91 bps a 60 minutos).
- **Veredicto de la herramienta:** ventaja frágil, porque la ganancia es positiva en muy pocas de las ventanas de 63 días.
- **A 30 minutos pasa lo mismo:** los 10 mejores días aportan el 74% de la ganancia, casi todos de 2022, y sin ellos quedan 0,25 bps por operación (t 0,46).
- **Consecuencia:** la ganancia a 60 minutos descansa en marzo de 2020, que es donde el costo está peor medido (el spread de AAPL ese mes era unas 5 veces el de hoy). Por eso se está midiendo el spread de cada época.

#### Diagnósticos de la señal: noticias y horizonte

Hechos con `diagnosticos.py` el 16 de noviembre de 2026, sobre las predicciones de la segunda versión y las operaciones de la calibrada, 2020–2024. Son descriptivos y no cuentan como variantes. El detalle está en `resultados/diagnosticos.md`. "Selección" es el retorno de la acción frente al promedio de las 50, en la dirección que predijo el modelo, antes de costos.

**¿El modelo elige mejor después de una noticia?** No de forma clara.

| Momentos | Parte de las filas | Selección a 30 min (t) | Selección a 60 min (t) |
| --- | --- | --- | --- |
| Sin noticias desde el cierre de ayer | 46% y 54% | 0,24 bps (2,76) | 0,50 bps (3,01) |
| Con noticias hoy, ninguna en la última hora | 39% y 33% | 0,58 bps (5,63) | 0,92 bps (4,62) |
| Con noticia en la última hora | 15% y 13% | 0,69 bps (3,40) | 1,20 bps (3,36) |
| Con 3 o más noticias en la última hora | 1% | 2,75 bps (2,53) | 3,61 bps (1,74) |

- La selección es algo mayor con noticia, pero casi todo es porque esas acciones se mueven más: como porcentaje del movimiento típico, la última hora con noticia no supera a los días con noticias más viejas.
- Dentro de una misma acción no hay diferencia: la selección es mayor con noticia en 13 de 23 acciones a 30 minutos y en 14 de 34 a 60.
- Con 3 o más noticias en una hora sí hay más para ganar, pero es el 1% de los momentos y el t ronda 2.
- Lectura: la señal del modelo de velas no viene de las noticias. Lo que la IA sume en la Fase 3 sería información nueva, no un refuerzo de lo que ya hay.

**¿Cuánto dura la señal?** Sigue creciendo mucho más allá del horizonte para el que se entrenó. Operaciones de la versión calibrada, sobre las mismas entradas (hasta las 12:54, donde caben todas las duraciones):

| Se mantiene | Modelo de 30 min: selección (t) | Menos el costo (t) | Modelo de 60 min: selección (t) | Menos el costo (t) |
| --- | --- | --- | --- | --- |
| 30 min | 1,79 bps (3,18) | 0,32 (0,57) | 1,48 bps (2,57) | −0,22 (−0,39) |
| 60 min | 3,61 bps (4,09) | 2,14 (2,44) | 2,42 bps (3,20) | 0,72 (0,95) |
| 120 min | 5,07 bps (3,87) | 3,61 (2,76) | 2,62 bps (2,51) | 0,92 (0,88) |
| 180 min | 6,38 bps (3,97) | 4,92 (3,07) | 3,87 bps (2,98) | 2,17 (1,68) |
| Hasta el cierre | 6,83 bps (3,24) | 5,37 (2,55) | 4,78 bps (2,80) | 3,08 (1,81) |

- Con el modelo de 30 minutos, mantener 3 horas da 4,92 bps después del costo, contra 0,32 al cerrar a los 30 minutos. El costo es el mismo.
- Es coherente con lo que el modelo usa: sus variables principales son de escala diaria (sector, retorno de la noche, de ayer, de 20 días). Predice una deriva del día, no un movimiento de media hora.
- **Todavía no es un resultado.** Es una exploración con 12 miradas (6 duraciones por 2 modelos) sobre el periodo de desarrollo; "menos el costo" usa solo la selección (supone la parte de mercado cubierta y no cuenta ese costo); solo incluye entradas de la mañana; mantener 3 horas entrando cada 30 minutos encima posiciones en la misma acción; y los t suponen días independientes.
- La prueba honesta es la idea 5 de las ideas en reserva.

#### Comparaciones múltiples

Hecho con `comparaciones.py` el 16 de noviembre de 2026, sobre la ganancia neta diaria de las 10 variantes en 2020–2024. Usa remuestreo por bloques de 10 días en promedio, porque los días cercanos no son independientes. El detalle está en `resultados/comparaciones.md`.

- **Contra no operar, ninguna variante pasa.** SPA de Hansen: p = 0,227. La mejor, la calibrada a 60 minutos, tiene p = 0,050 sin corregir y 0,498 con Bonferroni.
- **Contra la referencia, todas pasan** (p = 0,000), pero eso solo dice que pierden menos que una regla que pierde siempre.
- **El t de 2,29 de la calibrada a 60 minutos estaba inflado.** Los días buenos vienen en racha (marzo de 2020). Con el remuestreo por bloques el t baja a 1,65; con Newey-West queda entre 1,6 y 1,9 según los rezagos.
- Los t de los demás informes agrupan por día pero suponen días independientes; para decidir vale el de este informe.
- Cada variante nueva que se pruebe se agrega a la lista de `comparaciones.py`, también si se descarta.

#### Sensibilidad al costo: el spread de cada época

Hecho con `recostear.py` el 16 de noviembre de 2026, con el spread muestreado por `muestrear_spread.py --historico` (8 momentos por símbolo y trimestre, 53 símbolos, 2016–2024). No entrena nada y no cuenta como variante. El detalle está en `resultados/costo_historico.md`.

Cada operación se cobra con el spread mediano de su símbolo en ese trimestre, corregido por la volatilidad de su día. Hay dos lecturas: las mismas operaciones con el costo de la época, y volviendo a decidir, donde el modelo opera solo si la ganancia esperada supera el spread del trimestre anterior (lo que se sabía entonces) y paga el del trimestre en curso.

| Horizonte | Versión | Costo de hoy | Neta (t) | Costo de la época | Mismas operaciones: neta (t) | Volviendo a decidir: neta (t) |
| --- | --- | --- | --- | --- | --- | --- |
| 30 min | Segunda | 1,54 bps | 0,42 (0,91) | 3,41 bps | −1,45 (−3,07) | 0,08 (0,20) |
| 30 min | Segunda calibrada | 1,45 bps | 0,94 (1,61) | 3,49 bps | −1,10 (−1,89) | 0,56 (0,99) |
| 60 min | Segunda | 1,91 bps | 1,20 (1,88) | 3,19 bps | −0,07 (−0,11) | 0,46 (0,85) |
| 60 min | Segunda calibrada | 1,70 bps | 2,07 (2,29) | 3,26 bps | 0,51 (0,57) | 1,00 (1,40) |

- **Con el costo de la época ninguna versión se distingue de cero,** y con el costo doble todas pierden. El filtro de operaciones también queda negativo (−1,89 y −0,38 bps). La referencia pierde más (−2,51 y −2,76).
- **El spread de cada año no explica la caída.** La mediana entre símbolos estuvo entre 0,56 y 0,99 veces la de hoy en todos los años de 2016 a 2024. Las acciones que hicieron split sí costaban mucho más antes (GOOGL entre 3,6 y 6,2 veces).
- **Lo que la explica es cuándo opera el modelo.** El spread sube 0,42% por cada 1% de volatilidad del día (t 37,2, con 15.108 muestras), y el modelo opera sobre todo en días de mucha volatilidad. Por eso sus operaciones cuestan más del doble que con el spread de hoy. En marzo de 2020 el spread fue 2,13 veces el de hoy.
- **Volviendo a decidir se recupera algo, porque el modelo opera menos en épocas caras,** pero tampoco alcanza: la calibrada a 60 minutos queda en 1,00 bps (t 1,40) y en −0,85 con el costo doble.
- **2020 sigue sosteniendo el resultado a 60 minutos.** Con el costo de la época ese año da 6,99 bps por operación (marzo de 2020 suma 22.171 bps, contra 25.532 con el costo de hoy). De 2021 a 2023 queda negativa y 2024 da 0,87.
- **Consecuencia:** el costo de hoy subestima lo que pagan las operaciones del modelo, y la ventaja medida hasta ahora dependía de eso. Cualquier versión nueva, incluido un horizonte más largo, tendría que pagar el costo de la época.

#### Resultado de la idea 5: horizonte hasta el cierre

Hecho con `horizonte_largo.py` el 16 de noviembre de 2026, con el diseño fijado antes de programarlo (ver "Notas de las otras ideas"). Validación hacia adelante de 2019 a 2024, comparación de 2020 a 2024, costo de la época, 36 acciones, sin cobertura. El detalle está en `resultados/horizonte_largo.md`.

| Versión | Operaciones | Costo | Ganancia neta | t por bloques | Neta con costo doble | t por bloques (doble) |
| --- | --- | --- | --- | --- | --- | --- |
| Calibrada a 60 min, volviendo a decidir (base) | 25.344 | 1,84 bps | 1,00 bps | — (1,40 por días) | −0,85 bps | — |
| Calibrada hasta el cierre | 33.692 | 2,29 bps | 2,87 bps | 2,30 | 0,57 bps | 0,47 |

- **Es el mejor resultado hasta ahora, y ya con el costo de la época:** casi el triple de la base, y la ganancia no es negativa con el costo doble.
- **No pasa la corrección por comparaciones múltiples.** Con 11 variantes el t exigido es 2,61 y da 2,30. En `comparaciones.py`: p = 0,011 sin corregir, 0,117 con Bonferroni y 0,083 con el SPA de Hansen. Las otras 10 variantes de esa prueba siguen con el costo de hoy, que las favorece, así que la comparación es conservadora para esta.
- **La señal es más fuerte que a 30 y 60 minutos.** La correlación de rangos sube a 0,032 (t 6,16) y la selección da 4,00 bps por operación (t 4,73). El mercado aporta 1,16 (t 1,44).
- **Sigue dependiendo de 2020.** Ese año da 9,03 bps por operación; sin él quedan 1,24 (t por bloques 1,03). 2022 da 4,34, 2021 da 1,46, 2024 da 0,40 y 2023 pierde 1,06. Son 11 de 20 trimestres positivos.
- **El 70% de las operaciones entra a las 10:00** (3,62 bps netos) y las de 10:30 ganan 5,46; las de 11:00 en adelante pierden. Operar solo a primera hora sería otra variante elegida después de ver este resultado, así que no se adopta sin una prueba nueva.
- **Lectura:** alargar el horizonte es la dirección correcta: el modelo predice una deriva del día, y a 15:55 la selección pesa más que el costo. Pero la ventaja todavía no se distingue del azar después de corregir por las variantes probadas, y sin 2020 se debilita.
- Variantes probadas hasta ahora: 11.

**Todas las variantes con el costo de la época.** `recostear_variantes.py` volvió a costear las otras 10 variantes y la referencia: las que deciden con el costo (logit, v1, v2 y calibrada) vuelven a decidir con el spread del trimestre anterior; el filtro y la referencia mantienen sus operaciones. Las cifras coinciden con `resultados/costo_historico.md`. Con eso `comparaciones.py` da SPA de Hansen p = 0,078 contra no operar (antes 0,083). La de hasta el cierre sigue siendo la mejor (p = 0,011 sin corregir, 0,117 con Bonferroni); la segunda, la calibrada a 60 minutos, baja a t 1,15. Contra la referencia todas siguen ganando.

#### Revisión contra el sobreajuste de la idea 5 (paso 2.8)

Hecha con `revision_cierre.py` el 16 de noviembre de 2026, sobre lo guardado por `horizonte_largo.py`, con la lista de `backtest-expert` y `residual-edge-analyzer`. Es descriptiva, no cuenta como variante y ninguna versión de aquí se adopta. El detalle está en `resultados/revision_cierre.md`.

| Prueba | Resultado |
| --- | --- |
| Umbral de entrada (k veces el costo esperado, de 0,5 a 2) | Meseta: t entre 2,26 y 2,30 de k = 0,75 a 1,5. Con k = 0,5 baja a 1,71; con k = 2 sube a 2,83 (5,00 bps netos) |
| Hora de salida, mismas operaciones | 14:55: 1,75 bps (t 1,66); 15:25: 1,73 (1,65); 15:40: 2,07 (1,95); 15:55: 2,87 (2,30) |
| Costo 1,5 y 2 veces el de la época | 1,72 bps (t 1,40) y 0,57 (t 0,47) |
| Mercado (`residual-edge-analyzer`) | Ventaja propia: beta 0,008 frente a SPY, R² 0,1%, 71% de las ventanas de 63 días positivas |
| Concentración | Los 10 mejores días aportan el 64%; sin ellos, 1,03 bps (t 0,95). NVDA, TSLA y AMD aportan el 47% |
| Por régimen | Gana en tres de cuatro; pierde en el régimen 3 (−4,47% anual) |
| Evaluador de `backtest-expert` | REFINAR, 67 de 100: muestra y realismo de ejecución completos; la expectativa por operación (0,028%, factor de ganancia 1,06) es la parte débil |

- **El umbral no está sobreajustado:** el resultado se mantiene parejo alrededor del valor elegido. Que k = 2 dé más es una pista para una prueba nueva, no algo que se pueda adoptar ahora.
- **Más de una quinta parte de la ganancia bruta llega en la última media hora:** saliendo a las 15:25 la bruta es 4,03 bps y a las 15:55, 5,16. Es coherente con el impulso intradía documentado (la primera media hora predice la última, uno de los efectos de la referencia), pero hace que el resultado dependa de poder salir cerca del cierre, donde el spread puede ser distinto del medido en horario normal.
- **No es exposición al mercado,** pero sí depende de pocos días (marzo de 2020 y febrero de 2022) y de las acciones más volátiles.
- **Conclusión:** la idea 5 es la mejor base para B y su señal es real (la selección tiene t 4,73), pero el margen después de costos es fino: con un costo 50% mayor el t baja a 1,40. Antes de la muestra final hace falta saber cuánto cuesta salir a las 15:55.

**Control del costo en los bordes, regla fijada el 16 de noviembre de 2026 antes de medir.** `muestrear_spread.py --bordes` mide el spread de las 36 acciones de 2016 a 2024 en la apertura (10:00–10:35, donde entra el 70% de las operaciones) y en el cierre (15:45–15:59, donde salen), con 4 momentos por franja y trimestre.
- **Costo corregido:** cada operación paga medio spread al entrar y medio al salir. Cada mitad es el costo de la época de esa acción (horario normal, trimestre en curso, volatilidad del día) multiplicado por la razón de su franja: la mediana, entre las muestras de esa acción en esa franja, del spread medido dividido por el de horario normal de su trimestre corregido por la volatilidad de su día.
- **Mismas operaciones:** la regla de entrada no cambia, solo lo que se paga. No suma variantes.
- **Decisión del horizonte:** si con el costo corregido la ganancia neta sigue positiva con t por bloques de al menos 1,65 (5% de una cola, sin corregir), la salida a las 15:55 queda como horizonte de B. Si no, no se elige otra hora mirando estos resultados: salir antes (por ejemplo, a las 15:25) sería una variante nueva, la 12.ª, con su propia prueba.

#### Resultado de los pasos 2.3 y 2.4

Todo se calcula por ventana, solo con días anteriores a cada año de prueba. El detalle está en `resultados/segmentos.md`.

- **Grupos por correlación: débiles e inestables.** Silueta de 0,09 a 0,12 y entre 4 y 10 grupos según el año. No se usan.
- **Grupos por características** (volatilidad, monto, beta, noticias): más claros, con silueta de 0,38 a 0,42 y 4 o 5 grupos. En 2024: defensivas, cíclicas, tecnológicas volátiles, las cuatro gigantes y TSLA sola.
- **Regímenes:** el BIC elige cuatro en todas las ventanas. Dos son de volatilidad baja y dos de volatilidad alta; a estos los separan la tendencia y si la volatilidad sube o cede.
- **La señal de la primera versión está en los cuatro regímenes** (t de 3 a 7); lo que cambia es si alcanza a pagar el costo. A 60 minutos gana en el régimen volátil que cede (7,35 bps, t 2,31) y pierde en el volátil que cae (−2,98 bps, t −2,45). El primero es sobre todo 2020.
- **No da para una regla:** con ocho casillas, un t de 2,3 no es evidencia fuerte, y operar solo en los regímenes buenos sería una variante nueva.
- **Las operaciones están concentradas** en las tecnológicas volátiles: a 30 minutos, 15.737 de 36.414.

#### Ideas en reserva para el modelo de velas

Anotadas el 16 de noviembre de 2026. La idea 1 ya se probó ese mismo día y no le ganó a la calibración (ver el resultado arriba); su diseño se deja aquí como registro. Las ideas 2 a 4 están diseñadas pero no programadas ni corridas, así que no cuentan como variantes.

| Idea | Qué es | Qué existe ya | Costo | Variantes que suma |
| --- | --- | --- | --- | --- |
| 1 · Filtro de operaciones (meta-labeling), **probada y descartada** | Un segundo modelo decide si se opera; el primero solo da la dirección | Las predicciones fuera de muestra del primero y los regímenes | Bajo: no reentrena el primero, salvo un año | 2 |
| 2 · Objetivo sin mercado ni sector | El primero predice el retorno sin la parte de SPY (con la beta de cada acción) y sin la de su sector | El objetivo ya descuenta el promedio de las 50 acciones; `beta_60d` | Una corrida completa (80 minutos) | 2, junto con la idea 3 |
| 3 · Reacción a la noticia | Variables de cuánto se movió el precio y el volumen desde la última noticia o comunicado 8-K | Conteos de noticias, `volrel_15`, hora exacta de los 8-K | Rehacer `variables.py` y la misma corrida de la idea 2 | — |
| 4 · Sorpresa contable | Cambio de ingresos y ganancia por acción frente al mismo trimestre del año anterior | Cifras de la SEC | Aplazada: ver abajo | — |
| 5 · Horizonte largo, **probada: la mejor hasta ahora, sin significancia corregida** | Entrenar y operar con un objetivo hasta las 15:55 y seis decisiones al día | El diagnóstico de duración de la señal | Una corrida completa; reabre la decisión del horizonte | 1 |

**Diseño del filtro de operaciones (idea 1)**

- **Filas:** solo las operaciones candidatas (acciones operables en los momentos de decisión de cada horizonte).
- **Etiqueta:** 1 si el retorno en la dirección del primero supera 2 veces el spread. Se fija en 2 y no se prueba 1,5: coincide con el criterio de no perder con el costo doble.
- **Variables:** la predicción del primero (valor, valor absoluto, puesto entre las acciones de ese momento y tamaño frente al spread), el movimiento esperado frente al spread, el minuto del día, `volrel_15`, `not_60m`, la volatilidad de SPY, el régimen, el grupo por características y `vol_20d`.
- **Para cada año de prueba A:** el filtro se entrena con las predicciones de los años de prueba hasta A−2; con el año A−1 se calibra la probabilidad y se elige el umbral (el de mayor ganancia neta con costo doble, entre cinco valores fijos y con un mínimo de 1.500 operaciones); se opera el año A.
- **Años de prueba:** 2021–2024 con lo guardado. Para incluir 2020 hay que agregar un entrenamiento del primero para 2018, con solo dos años de historia. Se reportan los dos periodos, porque 2020 pesa mucho.
- **Base de comparación:** la calibración (2.6.c) es el caso más simple de este filtro. Si el filtro no le gana, no se justifica.
- **Tamaño de posición:** la probabilidad sola no alcanza para Kelly; se guarda también la ganancia y la pérdida media por tramo de probabilidad.
- **Advertencia:** el movimiento típico a 30 minutos (unos 22 bps) es mucho mayor que el spread (1,5 bps), así que la etiqueta casi equivale a "acertó la dirección". Lo que el filtro puede aportar es elegir los momentos en que el mismo acierto vale más.

**Notas de las otras ideas**

- **Idea 2, con menos prioridad:** la revisión de la ganancia mostró que la parte de mercado está en cómo se mide la ganancia (retorno sin cobertura), no en el objetivo del entrenamiento. Cambiar el objetivo importaría poco; cubrir las operaciones baja la ganancia en vez de subirla. Si se hace, el promedio del sector debe excluir a la propia acción, porque hay sectores de tres acciones y uno de una (LIN). Se espera poca mejora: el promedio de las 50 ya quita casi todo el mercado. La ganancia se sigue midiendo con el retorno sin cobertura, como dicen los criterios.
- **Idea 3:** variables continuas (retorno desde la noticia frente a la volatilidad esperada, volumen relativo desde la noticia, minutos desde el último 8-K), sin cortes fijos; el árbol los encuentra.
- **Idea 5, la más prometedora:** el diagnóstico mostró que la selección crece al mantener la operación más tiempo, con el mismo costo. Habría que fijar de antemano un solo diseño (objetivo, momentos de decisión y si las posiciones pueden encimarse) y decidir si la ganancia se mide con o sin cobertura. Reabre la decisión cerrada del horizonte de 30 y 60 minutos, que salió de la barrera de costos; esa misma lógica favorece horizontes más largos. Ya está el costo histórico: si se prueba, se mide con el spread de cada época, que es el costo oficial.
- **Diseño de la idea 5, fijado el 16 de noviembre de 2026 antes de programarla:**
  - **Objetivo:** el retorno de cada acción desde la entrada hasta las 15:55 (minuto 384, el cierre de la referencia), menos el promedio de las 50 acciones en ese momento.
  - **Momentos de decisión:** cada 30 minutos de 10:00 a 12:30 (seis al día). El modelo se entrena y predice con esas mismas filas.
  - **Sin encimar:** cada acción tiene como máximo una posición al día, la del primer momento en que la predicción pasa el costo; sale a las 15:55.
  - **Modelo:** LightGBM v2 (las mismas variables y la búsqueda de hiperparámetros) con la calibración del paso 2.6.c. Validación hacia adelante de 2019 a 2024; la comparación va de 2020 a 2024.
  - **Costo:** el de cada época (sección 5). Decide con el spread del trimestre anterior y la volatilidad del día anterior; paga el del trimestre en curso con la volatilidad de su día.
  - **Acciones:** las operables a 60 minutos: 36 acciones (las 39 de esa lista menos SPY, QQQ e IWM, que el modelo de velas no opera). Un horizonte más largo permitiría más, pero se fija la lista de antemano para no volver a medirla.
  - **Ganancia:** sin cobertura, como dicen los criterios. Se informan también la parte de selección y la de mercado.
  - **Se reporta:** ganancia neta, costo doble, por año, sin 2020, trimestres positivos y el t por bloques. Suma 1 variante: con ella van 11 (t exigido con Bonferroni 2,61). Se agrega a `comparaciones.py` aunque se descarte.
  - **Base de comparación:** la calibrada a 60 minutos con el costo de la época, volviendo a decidir (1,00 bps, t 1,40).
- **Idea 4, aplazada:** las cifras estructuradas llegan tarde (ver "Limitaciones anotadas" en la sección 4). Solo serviría como variable de varios días a partir del informe trimestral, no como señal de minutos.

Con la idea 1 ya van 10 variantes. Con las ideas 2 y 3 el total llegaría a 12, y con Bonferroni el t exigido subiría de 2,58 a 2,64.

Hipótesis de trabajo: modelar por grupo predice mejor que un modelo único para todas las acciones. Se prueba, no se asume.

Regla anti-anticipación: los grupos y regímenes se recalculan en cada ventana de la validación hacia adelante, solo con datos del pasado.

#### Instrucciones para que la IA lea noticias (paso 2.9), versión 1

Diseño del 16 de noviembre de 2026. Las instrucciones y el formato se fijan antes de la Fase 3 y no cambian durante el experimento; si cambian, la versión nueva empieza su propia cuenta.

**Qué recibe la IA:** una noticia por llamada, con titular, resumen, los primeros 2.000 caracteres del texto, fuente, hora de publicación (Nueva York) y, por cada símbolo del universo que menciona (máximo 3, como en `variables.py`), el nombre de la empresa y su sector. No recibe precios: la reacción del precio la calcula el sistema aparte. Las instrucciones van en inglés, porque las noticias están en inglés y los modelos pequeños responden mejor así; las claves del JSON van en español.

**Qué responde,** en JSON, una evaluación por símbolo:

| Campo | Valores | Para qué |
| --- | --- | --- |
| `simbolo` | El símbolo | — |
| `relevancia` | 0 = solo se menciona; 1 = trata de la empresa, pero es menor; 2 = trata directamente de algo importante para la empresa | D |
| `tono` | −2 a 2, para el precio de esa acción | D |
| `tipo_evento` | resultados, guia, analista, fusion_adquisicion, legal_regulatorio, producto_negocio, directivos, capital, macro_sector, movimiento_precio, otro | D y revisión |
| `novedad` | 0 = repite algo ya conocido o comenta un movimiento de precio; 1 = información nueva | D |
| `sorpresa` | 0 = esperado o rutinario; 1 = algo inesperado; 2 = muy inesperado | D |
| `decision` | comprar, vender, nada | C |
| `retorno_esperado_bps` | Entero: retorno de la acción frente al mercado hasta el horizonte | C |
| `confianza` | 0 a 1 | C y tamaño de posición |
| `razon` | Una frase de hasta 20 palabras | Revisión (paso 3.5) |

- **Por qué estas escalas:** valores pocos y enteros, para que un modelo de 1–3B los pueda dar de forma estable; los mismos para todos los tamaños, para que la comparación por escala sea justa.
- **`novedad` es nueva frente al plan:** buena parte de las notas de Benzinga son resúmenes de "acciones que se mueven hoy". Sin ese campo, la IA le daría tono a un movimiento que ya ocurrió.
- **Parámetros fijos:** temperatura 0, el mismo texto de instrucciones para todos los modelos, y el horizonte como dato de las instrucciones (queda el que salga de la decisión abierta).

**Cuándo cuenta una respuesta:** desde la hora en que llegó la respuesta, no desde la hora de la noticia. Si llega después del momento de decisión, se usa en el siguiente. Así la latencia de cada modelo entra sola en su resultado.

**Qué se registra en SQLite (paso 3.3):** la noticia y su versión (si se corrige, la corrección es una noticia nueva), el modelo y su identificador exacto, la versión de las instrucciones, la hora de envío y de llegada, los tokens, el JSON tal como llegó, si fue válido y los campos ya leídos. Una respuesta inválida se reintenta una vez; si vuelve a fallar, cuenta como "sin respuesta", no se descarta en silencio.

**Variables para D,** calculadas en cada momento de decisión con las respuestas ya llegadas, por acción:
- `ia_tono_60m`: suma de tono × relevancia / 2 de las noticias nuevas (`novedad` = 1) de la última hora.
- `ia_sorpresa_60m`: la mayor sorpresa de la última hora entre las noticias con relevancia 2.
- `ia_relevantes_60m`: cuántas noticias con relevancia 2 hubo en la última hora.
- `ia_tono_noche`: lo mismo que `ia_tono_60m`, con las noticias desde el cierre anterior (lo que sale fuera de sesión es señal para la apertura).
- `ia_reaccion`: el signo del tono por el retorno relativo de la acción desde la noticia. Negativo es "noticia buena y el precio no subió" (sección 7).
- `ia_min_desde_relevante`: minutos desde la última noticia con relevancia 2.

**Qué se puede hacer con el histórico de noticias:** comprobar que las respuestas son JSON válido, que se repiten igual con la misma noticia, cuánto tardan y cuánto cuestan. Nunca medir si aciertan (sección 2, "Regla sobre la IA y el pasado").

**Cómo se entrena D:** no hay historia limpia de las variables de la IA (con noticias viejas el LLM ya sabe qué pasó), así que D se ajusta en vivo: los primeros meses en la cuenta de papel ajustan una capa pequeña que combina la predicción de B con las seis variables, y D contra B se compara en los meses siguientes. Ver "Decisiones cerradas".

### Fase 3 · Experimento en vivo (cuenta de papel)

- [ ] 3.1 Los scripts calculan las variables de velas cada 5–15 minutos y reciben las noticias apenas salen.
- [ ] 3.2 Cuando llega una noticia de una acción del universo, cada LLM responde en JSON: tono, tipo de evento, sorpresa, relevancia y, para el competidor C, comprar / vender / nada con retorno esperado y confianza.
- [ ] 3.3 Se registra todo en SQLite: noticia, respuesta y razonamiento del LLM, latencia, decisión, precio de entrada y salida, costo.
- [ ] 3.4 Ejecución en la cuenta de papel de Alpaca, restando costos realistas: la cuenta de papel llena órdenes que en la vida real no se habrían llenado a ese precio.
- [ ] 3.5 Revisión posterior de cada señal: acierto, falso positivo, oportunidad perdida.
- [ ] 3.6 Al cierre, la prueba de H0: D contra B, con la muestra final que no se tocó.

Horario del mercado en Colombia: 9:30 a. m.–4:00 p. m. en invierno de EE. UU.; una hora antes desde marzo.

#### Cuánto tiene que durar la Fase 3 (cálculo del 16 de noviembre de 2026)

Con las operaciones de la idea 5 como B (2020–2024): 27 operaciones al día, desviación de 137 bps por operación (107 bps en la parte de selección). D solo cambia las operaciones de las acciones con noticias; si cambia una fracción f de las operaciones y en ellas gana δ bps más que B, los días necesarios para detectarlo con 80% de probabilidad (una cola, 5%) son z² σ² / (δ² f N), con z = 2,49:

| Fracción con noticias (f) | δ = 5 bps | δ = 10 bps | δ = 20 bps |
| --- | --- | --- | --- |
| 10% | 82 meses | 21 meses | 5,2 meses |
| 15% | 55 meses | 14 meses | 3,4 meses |
| 25% | 33 meses | 8,2 meses | 2,1 meses |

- **Supuestos:** f entre 15% y 25% sale de los diagnósticos (13% a 15% de los momentos tienen noticia en la última hora; un tercio, noticias del día). δ = 5 bps por operación afectada ya sería casi el doble de la ganancia neta de B.
- **Puede ser peor:** la desviación diaria real de B (1.187 bps) es mayor que la que darían operaciones independientes (714), porque las operaciones de un mismo día se mueven juntas. Si eso pasa también con la diferencia entre D y B, los meses se multiplican hasta por 2,8.
- **Con los cuatro tamaños de LLM** y corrección de Bonferroni, z sube a 3,08: hace falta un 50% más de tiempo.
- **Conclusión:** con efectos realistas (5 a 10 bps en el 15% a 25% de las operaciones), 5 meses no alcanzan; harían falta entre 8 meses y varios años. Un ajuste inicial de 2 a 3 meses empeora el problema.

**Formas de ganar potencia, por decidir antes de empezar:**
1. **Un solo LLM como prueba principal** (el que se elija en el paso 2.9) y los demás tamaños como análisis secundario: evita la corrección por cuatro.
2. **Medir D contra B en la parte de selección** (con la parte de mercado cubierta): baja la desviación de 137 a 107 bps y ahorra cerca de 40% del tiempo. Cambia el criterio de la sección 5, que mide sin cobertura.
3. **Una prueba de señal además de la de ganancia:** comparar el orden predicho por D y por B en todas las acciones y momentos, operen o no (300 observaciones al día en vez de 27). No reemplaza la ganancia neta como criterio, pero dice antes si la IA aporta.
4. **Ajuste inicial corto:** una capa de unos 7 coeficientes con penalización se puede ajustar con un mes de datos.


### Fase 4 · Dinero real

- [ ] 4.1 Solo si H0 se rechaza.
- [ ] 4.2 Empezar con el 10–20% del capital de riesgo.
- [ ] 4.3 Órdenes con aprobación manual al comienzo.
- [ ] 4.4 Escalar solo si los resultados reales se parecen a los de papel.

## 4. Datos

Fuente principal: Alpaca, plan gratuito ($0). Todo sale con las mismas llaves de la cuenta de papel.

| Dato | Qué es | Dónde está | Script |
| --- | --- | --- | --- |
| Velas de 1 minuto, sin ajustar | Precio y volumen de cada minuto, 2016–2026, mercado completo (sin los últimos 15 minutos). Incluye pre-mercado y post-mercado | `datos/minuto` | `descargar_datos.py` |
| Velas de 1 minuto, ajustadas | Lo mismo, ajustado por Alpaca a la fecha de descarga. Solo para comprobar | `datos/minuto_ajustado` | `descargar_datos.py --ajuste all` |
| Ajustes corporativos | Splits, dividendos y escisiones: sirven solo para corregir saltos falsos de precio, no para decidir | `datos/ajustes` | `descargar_ajustes.py` |
| Noticias | Titular, resumen, texto, símbolos y hora al segundo, desde 2016 | `datos/noticias` | `descargar_noticias.py` |
| Comunicados oficiales (SEC) | Formularios 8-K y sus anexos de prensa: lo que la empresa informa por obligación legal, con hora de publicación y tema | `datos/sec/comunicados` e índice en `datos/sec/comunicados_indice.parquet` | `descargar_sec.py` |
| Cifras financieras (SEC) | Todo lo que la empresa reporta en formato estructurado: ingresos, utilidad, ganancia por acción y demás | `datos/sec/cifras` | `descargar_sec.py` |

Formato: Parquet, un archivo por símbolo y año para las velas y uno por mes para las noticias. SQLite para el registro de decisiones.

### Por qué precios sin ajustar

Un split o un dividendo cambia el precio de una acción sin que la empresa valga más ni menos. Si el modelo ve esos saltos, aprende caídas que nunca existieron.

- Se guardan los precios a los que realmente se negoció, que nunca cambian y son los que verán los competidores en vivo.
- `precios.py` los corrige al leerlos, con la tabla de ajustes.
- Las escisiones también se corrigen, pero de forma aproximada: el factor depende del precio al que abrió la empresa nueva en su primer día. Son 7 en 11 años (GE, HON, PFE y T).
- Frente al ajuste de Alpaca, esas cuatro acciones difieren: T 0,7%, GE 1%, HON 4% y PFE 5%. En PFE la diferencia es porque Alpaca no ajusta la escisión de Viatris de 2020 y aquí sí. En las otras, por el precio que se toma de la empresa nueva.
- Alpaca entrega los dividendos por fecha de pago, no por fecha ex-dividendo; por eso `descargar_ajustes.py` pide seis meses hacia adelante.

### Lo que se sabe de las noticias

- El volumen crece de unas 18.000 al año en 2016 a unas 38.000 desde 2022.
- Cerca de la mitad trae texto completo; entre 2018 y 2020 baja a menos del 30% y el resto solo tiene titular.
- El reparto es desigual: SPY tiene 82.000 y Tesla 39.000, mientras las de servicios públicos y LIN tienen alrededor de mil cada una.
- Si una noticia fue corregida después de publicarse, el texto guardado es el corregido. Para no usar información del futuro se trata como disponible desde la fecha de corrección.

### A qué hora sale la información

| Fuente | Antes de la apertura | En horario de mercado | Después del cierre | Fin de semana |
| --- | --- | --- | --- | --- |
| Noticias | 33% | 53% | 11% | 3% |
| Comunicados 8-K | 30% | 16% | 54% | — |

La mitad de las noticias sale con el mercado abierto, que es donde se puede operar en los minutos siguientes. Los comunicados oficiales, y sobre todo los resultados trimestrales, salen casi siempre fuera de sesión: ahí hay poco volumen y operar cuesta más. El paso 2.1 debe medir los costos por separado en los tres momentos.

### Para qué la SEC

Un comunicado 8-K suele salir antes que la nota de prensa que lo resume, así que le da a la IA el texto original y más temprano. Con las cifras de resultados, la "sorpresa" de un trimestre se calcula con números en vez de pedírsela a la IA, aunque esas cifras llegan varios días después del comunicado (ver "Limitaciones anotadas"). La SEC solo trae lo que la empresa reportó, no lo que esperaban los analistas (ese dato es de pago), así que la sorpresa se mide contra el mismo trimestre del año anterior.

Cada comunicado trae la hora exacta en que quedó público (verificada en UTC) y el tema que trata; el tema 2.02 marca los resultados trimestrales.

### Limitaciones anotadas

- **Sesgo de supervivencia:** el universo son empresas que existen hoy.
- **LIN** tiene datos solo desde 2018, cuando empezó a cotizar con ese símbolo.
- **Las cifras de la SEC llegan después del comunicado de resultados.** Vienen del informe trimestral (10-Q o 10-K), no del 8-K. De 1.893 comunicados de resultados de 2016 a 2024, solo en el 20% las cifras estaban disponibles ese mismo día; la mediana es 7 días después. Usarlas el día del comunicado sería usar información del futuro. Visa no reporta ganancia por acción en estos datos.
- **El costo usa el spread de hoy para toda la historia:** el spread de cada acción se midió con los últimos 60 días de mercado y es un solo número por símbolo. Alpaca sí entrega cotizaciones de años anteriores, así que `muestrear_spread.py --historico` tomó una muestra por trimestre de 2016 a 2024 para los 53 símbolos (en `datos/spread_historico`), y `recostear.py` volvió a costear las operaciones guardadas. El spread típico de cada año era parecido o menor que el de hoy, pero el de las operaciones del modelo es más del doble, porque opera en días volátiles; las acciones que hicieron split (GOOGL, AMZN) costaban entre 4 y 7 bps antes de 2022, contra 0,7 hoy. Con ese costo la ventaja desaparece (ver "Sensibilidad al costo"). Se adoptó como costo oficial el 16 de noviembre de 2026 (sección 5).
- **Empresas reorganizadas:** Exxon (2026), Disney (2019) y Broadcom (2018) pasaron a una sociedad nueva y la SEC les dio otro número de registro. `descargar_sec.py` tiene una tabla con los registros anteriores; si otra empresa se reorganiza, hay que agregarla ahí.

### Pagos opcionales

Alpaca $99/mes (tiempo real completo, solo al operar con dinero real); Massive $29–$199/mes (más historia); FirstRate Data, pago único desde USD 399,95 (incluye acciones que dejaron de cotizar).

Fuentes: [Alpaca – Market Data](https://alpaca.markets/docs/market-data) · [Massive – Pricing](https://massive.com/pricing) · [FirstRate Data](https://firstratedata.com/)

## 5. Evaluación estadística

Las métricas y el umbral de éxito se fijan por escrito antes de ver resultados.

- **Métrica principal:** ganancia neta por operación, después de diferencial, deslizamiento y comisiones.
- **Métricas de apoyo:** Sharpe, caída máxima, ganancia total, tasa de acierto, calibración de la confianza.
- **Validación:** hacia adelante (walk-forward) y una muestra final que no se toca hasta el cierre.
- **Comparaciones múltiples:** se prueban varios competidores y varios tamaños de LLM; elegir el mejor entre muchos infla el resultado. Se usa el Reality Check de White o el test SPA de Hansen, el Deflated Sharpe ratio, y Romano-Wolf o Bonferroni para varias hipótesis.
- **Ventaja propia:** se separa la ganancia que viene de estar expuesto al mercado de la que es ventaja real, con `residual-edge-analyzer`.
- **Tamaño de muestra:** según el paso 2.1, entre 2.000 y 4.600 operaciones si el acierto real es de 57%, y muchas más si es menor. Se fija al elegir el horizonte.
- **Muestra efectiva:** los datos de minutos están autocorrelacionados, y varias acciones reaccionan a la misma noticia; millones de filas no equivalen a millones de observaciones independientes.

### Criterios de éxito (paso 0.4)

**Confirmados el 15 de noviembre de 2026.** Se escribieron antes de correr la referencia y se confirmaron antes de entrenar el modelo de velas. Cualquier cambio se anota en el historial con su razón.

**Reglas comunes**

- **Muestra final:** del 1 de enero de 2025 en adelante. No se mira hasta el cierre de la Fase 2, y se usa una sola vez. Todo el desarrollo se hace con 2016–2024, con validación hacia adelante.
- **Costo:** un spread completo por operación, con el spread de la época: la mediana del spread de esa acción en el trimestre de la operación, corregida por la volatilidad de su día (como en `recostear.py`). Para decidir si se opera, el modelo usa solo lo que se sabía entonces: el spread del trimestre anterior y la volatilidad del día anterior. Todo resultado se repite con el costo doble. Cambiado el 16 de noviembre de 2026; antes era el spread de los últimos 60 días para toda la historia (ver el historial). La muestra final se costea igual: sus trimestres se muestrean al abrirla, con la misma regla.
- **Prueba:** sobre la ganancia neta de cada día, no de cada operación, porque las operaciones de un mismo día no son independientes. Una cola, 5% de significancia. El error se mide con remuestreo por bloques de días seguidos (bootstrap estacionario, bloques de 10 días en promedio, 10.000 remuestreos, como en `comparaciones.py`), porque los días buenos vienen en racha. Cambiado el 16 de noviembre de 2026; antes suponía días independientes.
- **Comparaciones múltiples:** el 5% se corrige por el número de variantes que llegaron a probarse (SPA de Hansen o Bonferroni). Se lleva la cuenta de todas, también de las descartadas.

**Fase 2: el modelo de velas (B) pasa si, en la muestra final, cumple todo esto**

1. Ganancia neta por operación de al menos 1 bps.
2. Ganancia neta diaria mayor que la de la referencia (A), con significancia.
3. Ganancia neta por operación que no es negativa con el costo doble.
4. Al menos 2.000 operaciones.
5. Ganancia neta positiva en al menos la mitad de los trimestres de la muestra final.

Si no pasa, se reporta y no se sigue a la Fase 3 con ese modelo.

**Fase 3: H0 se rechaza si, en vivo, IA + velas (D) cumple todo esto**

1. Ganancia neta diaria mayor que la del modelo de velas (B), con significancia, sobre los mismos días.
2. Ganancia neta por operación positiva.
3. Al menos 2.000 operaciones de D. Si a los 8 meses no se llega, se cierra y H0 no se rechaza.

La prueba de tendencia por tamaño de LLM es secundaria: se reporta, pero no decide.

**Fase 4: además, para pasar a dinero real**

- La ganancia neta de D no es negativa con el costo doble.
- La caída máxima en la cuenta de papel no supera el límite que se fije con el capital de riesgo (decisión abierta).

## 6. Riesgo, tamaño de posición y ejecución

Una capa común decide cuánto apostar, igual para todos los competidores; así se compara solo la calidad de la predicción.

- **Tamaño de posición:** Kelly fraccional o volatilidad objetivo, según retorno esperado y confianza.
- **Límites:** pérdida máxima por operación y por día, número de operaciones por día, exposición máxima por acción y por grupo correlacionado, cierre de todo a las 3:55 p. m.
- **Bloqueo tras pérdidas:** no se abren operaciones nuevas tras superar el límite diario o semanal, o tras una racha de pérdidas.
- **Ejecución:** órdenes límite cuando sea posible; registrar el deslizamiento real contra el precio esperado.
- **Monitoreo:** si un competidor se degrada frente a su desempeño histórico, se apaga.
- **Regla de apagado del sistema:** pérdida máxima fijada de antemano antes de operar con dinero real.

## 7. Herramientas

### Scripts del proyecto

| Archivo | Qué hace |
| --- | --- |
| `descargar_datos.py` | Baja las velas de 1 minuto. Sin ajustar por defecto; `--ajuste all` para ajustadas; `--forzar` para volver a bajar todo. Si se interrumpe, retoma donde iba |
| `descargar_ajustes.py` | Baja splits, dividendos y escisiones, con el precio de apertura de cada empresa escindida |
| `descargar_noticias.py` | Baja las noticias, un archivo por mes |
| `descargar_sec.py` | Baja de la SEC el índice de comunicados 8-K, las cifras financieras y los textos. Necesita `SEC_USER_AGENT` en `.env` |
| `actualizar.py` | Corre los cuatro scripts de descarga en orden y deja un registro por día |
| `muestrear_spread.py` | Mide el costo de operar cada acción con cotizaciones reales de compra y venta. Con `--historico` toma una muestra por trimestre de 2016 a 2024 |
| `barrera_costos.py` | Compara el movimiento del precio con el costo y calcula el acierto mínimo; escribe `resultados/barrera_costos.md` |
| `variables.py` | Arma la tabla de variables y retornos futuros para los modelos, sin usar información del futuro |
| `referencia.py` | Aplica los cuatro efectos de la referencia (competidor A) y calcula su ganancia neta; escribe `resultados/referencia.md`. No usa la muestra final salvo con `--muestra-final` |
| `modelo_velas.py` | Entrena el modelo de velas (competidor B) con validación hacia adelante y lo compara con la referencia; escribe `resultados/modelo_velas.md` |
| `segmentos.py` | Calcula los grupos de acciones y los regímenes de mercado por ventana de validación, y mide si la señal del modelo de velas cambia según el segmento; escribe `resultados/segmentos.md` |
| `ventaja.py` | Revisa de dónde sale la ganancia de un archivo de operaciones: si es ventaja propia o exposición al mercado, cuánto depende de pocos días, de un año o de pocas acciones, y cuánto es selección y cuánto mercado; escribe `resultados/ventaja.md` |
| `diagnosticos.py` | Mide si la señal del modelo de velas es mayor después de una noticia y cuánto dura si la operación se mantiene más tiempo; escribe `resultados/diagnosticos.md` |
| `comparaciones.py` | Corrige por el número de variantes probadas (Bonferroni, Holm y SPA de Hansen con remuestreo por bloques); escribe `resultados/comparaciones.md` |
| `recostear.py` | Vuelve a costear las operaciones guardadas con el spread del trimestre en que ocurrieron, corregido por la volatilidad del día; escribe `resultados/costo_historico.md` |
| `horizonte_largo.py` | Idea 5: modelo de velas con salida a las 15:55, seis decisiones al día y costo de la época; escribe `resultados/horizonte_largo.md`. Con `--rapido` prueba solo 2024 |
| `recostear_variantes.py` | Guarda las operaciones de las 10 variantes anteriores y de la referencia con el costo de la época (`operaciones_epoca_<h>.parquet`), que usa `comparaciones.py` |
| `revision_cierre.py` | Revisión contra el sobreajuste de la idea 5: umbral, hora de salida, costo, mercado y concentración; escribe `resultados/revision_cierre.md` |
| `lector_noticias.py` | Arma la entrada de cada noticia para la IA, valida su respuesta JSON y la registra en SQLite (paso 2.9). Por ahora solo con un modelo simulado |
| `filtro.py` | Filtro de operaciones (meta-labeling): un clasificador decide cuáles operaciones del modelo de velas se hacen; escribe `resultados/filtro.md` |
| `calibracion.py` | Corrige cuánto exagera el modelo de velas con las predicciones de años anteriores y vuelve a operar; escribe `resultados/calibracion.md` |
| `precios.py` | Lee las velas y las corrige por splits, dividendos y escisiones: `cargar("NVDA")` |

### Habilidades instaladas en `.claude/skills/`

Corren solas, sin llaves ni conexión a internet. Se leyeron y se probaron antes de instalarlas.

| Habilidad | Para qué se usa aquí | Fase | Origen |
| --- | --- | --- | --- |
| `backtest-expert` | Lista de chequeo y calificación de cada prueba histórica: muestra, costos, sobreajuste, robustez | 2 | A |
| `residual-edge-analyzer` | Separa la ganancia que viene del mercado de la ventaja propia; es la prueba de D contra B | 2 y 3 | A |
| `position-sizer` | Número de acciones por operación según riesgo fijo, volatilidad o Kelly | 3 y 4 | A |
| `statistics-fundamentals` | Regresión con pruebas t, covarianza con contracción, bootstrap para intervalos de confianza | 2 y 3 | B |
| `volatility-modeling` | EWMA y GARCH(1,1) para medir volatilidad y detectar regímenes | 2 | B |
| `historical-risk` | Estimadores de volatilidad con máximo y mínimo de la vela, caída máxima, VaR histórico | 2 y 3 | B |
| `performance-metrics` | Sharpe, Sortino, Calmar y razón de información para comparar competidores | 2 y 3 | B |
| `bet-sizing` | Kelly fraccional, escalado por volatilidad y topes por liquidez | 3 y 4 | B |
| `factor-investing` | Regresión con varios factores para saber si una ganancia es ventaja propia o exposición a factores conocidos | 2 y 3 | B |

Origen A: [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills), licencia MIT, versión `d5b11b7`. Origen B: [JoelLewis/finance_skills](https://github.com/JoelLewis/finance_skills), licencia MIT, versión `5c498ea`.

**Cuidado al aplicar las de origen B:** están escritas para datos diarios o mensuales. Con velas de minutos cambian la anualización (no es raíz de 252), la volatilidad tiene un patrón dentro del día (alta en la apertura y el cierre) y el bootstrap debe ser por bloques, porque los retornos de minutos no son independientes.

### Ideas tomadas de otros repositorios

No se instalaron porque dependen de otra fuente de datos o de otro horizonte; se reescriben sobre los datos de Alpaca.

| Idea | De dónde | Dónde entra |
| --- | --- | --- |
| "Salió una noticia buena y el precio no subió" es información por sí misma | claude-trading-skills | Variable del competidor D |
| Deriva después de resultados trimestrales | claude-trading-skills | Competidor A |
| Bloquear operaciones nuevas tras pérdidas o rachas | claude-trading-skills | Capa de riesgo |
| Revisar cada señal después | claude-trading-skills | Paso 3.5 |
| Ruptura del rango de apertura de 15 minutos | day-trader-skill | Competidor A |
| Leer los comunicados 8-K y las cifras de resultados directo de la SEC | day-trader-skill | Pasos 1.7 y 1.8 |
| Límites por operación y por día, y cierre a las 3:55 p. m. | day-trader-skill | Capa de riesgo |
| Orden con aprobación manual | day-trader-skill | Paso 4.3 |
| Buscar hiperparámetros con remuestreo y calcular el preprocesamiento solo con el entrenamiento | [Taller de tidymodels](https://freddy-hb-tidymodels-latinr.share.connect.posit.cloud/) de Freddy Hernández (R) | Paso 2.6; se reescribe en Python y con validación hacia adelante en vez de pliegues al azar |

### Revisado y descartado

- **Cuatro habilidades de finance_skills**, por aportar poco aquí: `return-calculations`, `trade-execution`, `corporate-actions` y `order-lifecycle`.
- **anthropics/financial-services:** es para el trabajo de oficina de bancos y fondos, con datos de pago. Solo sirve como guía para las instrucciones de la IA cuando lea resultados trimestrales (paso 2.9).
- **himself65/finance-skills:** sus lectores de redes sociales pueden poner en riesgo las cuentas personales y no dan historia. Las redes sociales quedan como idea para después de la Fase 3.

## 8. Infraestructura

El PC viejo queda como servidor 24/7 en la red local; el portátil hace desarrollo y análisis. La configuración del PC viejo y de los modelos de IA se deja para el final de la Fase 2; mientras tanto todo corre en el portátil.

| Componente | Rol | Notas |
| --- | --- | --- |
| PC viejo (Linux, \~4 GB) | Descarga datos, guarda, programa tareas, registra decisiones | Sin entorno gráfico, SSH con llaves, IP fija, cable de red si es posible |
| Portátil (Celeron N5095, 16 GB) | Desarrollo, entrenamiento de modelos de árboles, modelos locales pequeños | Agregar un segundo módulo DDR4 para doble canal |
| Claude por API | Lectura de noticias en tiempo real | Se paga aparte del plan Pro |
| Google Drive | Respaldo nocturno con rclone | No se trabaja directo desde Drive |
| Kaggle / Colab | GPU gratis para redes neuronales más grandes | Solo si hace falta |

### Quién entrena y quién opera

El portátil entrena y el PC viejo solo opera. Un modelo entrenado es un archivo de pocos megas y para usarlo no hace falta la historia con la que aprendió.

| | Portátil | PC viejo |
| --- | --- | --- |
| Tarea | Entrenar, analizar y reentrenar | Bajar datos nuevos, correr el modelo, registrar decisiones |
| Datos que necesita | Todo el histórico (4,3 GB) | El año en curso |
| Exigencia | Alta, de vez en cuando | Baja, todos los días |

- **El PC viejo no descarga el histórico.** Baja solo el año en curso (unos 8 minutos), que alcanza para las variables que miran hacia atrás, como la volatilidad de los últimos 20 días.
- **Reentrenamiento:** cada mes o cada trimestre, en el portátil. Se le copian los datos nuevos que acumuló el PC viejo, se reentrena y se devuelve el archivo del modelo.
- **Si hiciera falta el histórico en el PC viejo, se copia** por la red local o una memoria USB; no se vuelve a descargar. Los scripts detectan lo que ya existe y solo bajan lo que falta.
- **Modelos de IA locales:** uno mediano (7–8B) no cabe en los 4 GB del PC viejo. O corre en el portátil, o el experimento se queda con el modelo pequeño y Claude por API. Se decide en el paso 2.9.

Pendiente: salida del comando de diagnóstico del PC viejo para decidir si se reinstala o se limpia.

## 9. Reglas y decisiones

### Reglas de enfoque

- Ninguna fase avanza sin cumplir su criterio de salida.
- Nada nuevo entra (activos, técnicas, mercados) sin cerrar la fase actual.
- Todo resultado se reporta, también los negativos.
- Los criterios de éxito se escriben antes de mirar los datos.

### Decisiones abiertas

- [ ] Capital máximo de riesgo.
- [ ] Bróker definitivo (Alpaca o Interactive Brokers). Revisado el 16 de noviembre de 2026: la página de Alpaca no lista países y pide escribir a soporte; Interactive Brokers acepta residentes en Colombia según guías de terceros, con el plan Pro (unos 0,005 dólares por acción, mínimo 1 dólar por orden). Esa comisión no está en el costo que usa el proyecto. Falta confirmarlo con cada bróker.
- [ ] Regla de "pattern day trader": falta saber si el bróker elegido ya aplica el cambio de FINRA o mantiene un mínimo propio.
- [ ] Horizonte: se reabrió la decisión de 30 y 60 minutos y se probó uno hasta las 15:55 (idea 5). Es el mejor resultado, pero sin significancia corregida. Queda como horizonte de B si sobrevive al control del costo en los bordes, con la regla fijada antes de medir (ver "Revisión contra el sobreajuste de la idea 5").
- [ ] Modelo local a probar en el portátil.
- [ ] Compra del segundo módulo de RAM.

### Decisiones cerradas

- [x] Universo: SPY, QQQ, IWM y 50 acciones (lista en `descargar_datos.py`).
- [x] Precios sin ajustar, con splits, dividendos y escisiones aplicados al leer.
- [x] La IA lee noticias; los modelos de árboles leen velas.
- [x] El éxito se mide en ganancia neta, no en acierto.
- [x] Horizonte: 30 y 60 minutos en horario normal; 15 minutos como comparación.
- [x] Lo que sale fuera del horario normal no se opera en el momento; es señal para la apertura siguiente.
- [x] Se opera solo en las acciones baratas de operar (acierto mínimo de 55% o menos según el paso 2.1).
- [x] Criterios de éxito y muestra final (de 2025 en adelante), en la sección 5.
- [x] Costo oficial: el spread de cada época, corregido por la volatilidad del día (16 de noviembre de 2026). El de hoy resultó optimista: el modelo opera en días volátiles, cuando el spread es más del doble (`resultados/costo_historico.md`).
- [x] Prueba oficial de significancia: remuestreo por bloques de días seguidos (16 de noviembre de 2026), porque los días buenos vienen en racha.
- [x] Cómo se entrena D (16 de noviembre de 2026): los primeros meses en la cuenta de papel sirven para ajustar una capa pequeña, con pocos coeficientes, que combina la predicción de B con las seis variables de la IA. La comparación D contra B se hace en los meses siguientes, y la capa se reajusta cada mes solo con lo anterior. Se descartó entrenar con noticias históricas, porque el LLM ya sabe qué pasó después, y una regla fija sin entrenar. Falta fijar cuántos meses dura el ajuste inicial y qué forma tiene la capa.
- [x] El portátil entrena y el PC viejo opera.
- [x] El PC viejo y los modelos de IA se configuran al final.
- [x] Regla de "pattern day trader": el [aviso 26-10 de FINRA](https://www.finra.org/rules-guidance/notices/26-10) eliminó el conteo de operaciones y el mínimo de 25.000 dólares desde el 4 de junio de 2026. Los brókers pueden aplicarlo por etapas hasta el 20 de octubre de 2027. Queda el piso general de 2.000 dólares de una cuenta de margen.

## 10. Historial de cambios

| Tema | Versión 1 | Versión actual | Por qué |
| --- | --- | --- | --- |
| Horizonte | 5 a 15 minutos | 30 y 60 minutos | A 5 minutos el costo exige acertar el 62% de las veces; a 60, el 54% |
| Qué se opera | Todas las acciones, a cualquier hora | Las baratas de operar, en horario normal | Fuera de sesión el costo es entre 6 y 9 veces mayor |
| Papel de la IA | Competía contra los modelos clásicos con los mismos números | Lee noticias; los árboles leen velas; se suman | Con números puros un LLM no tiene ventaja sobre XGBoost y es mucho más lento y caro |
| Criterio de éxito | Tasa de acierto (53% contra 50%) | Ganancia neta por operación | A 5 minutos, 53% de acierto no alcanza a pagar los costos |
| Qué se predice | Si cada acción sube o baja | El orden de las acciones, de mejor a peor | Quita el ruido del mercado general y da más observaciones por día |
| Referencia | Regla fija o azar | Cuatro efectos documentados | Ganarle al azar no demuestra nada |
| Escala de la IA | Regresión sobre el número de parámetros | Prueba de tendencia sobre el orden de tamaño | Claude no publica sus parámetros |
| Tamaño de muestra | 2.200 operaciones | Por calcular en el paso 2.1 | La cifra era para acierto, que ya no es el criterio |
| Precios | Ajustados | Sin ajustar, con corrección al leer | Los ajustados cambian con cada split o dividendo nuevo |
| Fuentes de texto | Ninguna | Noticias de Alpaca y comunicados de la SEC | Es lo que lee la IA |
| Costo | Spread de los últimos 60 días para toda la historia | Spread del trimestre de cada operación, corregido por la volatilidad del día | El modelo opera en días volátiles; con el spread de hoy sus operaciones costaban menos de la mitad de lo real |
| Prueba de significancia | t sobre la ganancia diaria, con días independientes | t con remuestreo por bloques de días | Los días buenos vienen en racha; con bloques el t de la calibrada a 60 minutos bajó de 2,29 a 1,65 |
