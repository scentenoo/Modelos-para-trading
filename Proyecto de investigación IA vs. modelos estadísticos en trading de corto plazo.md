# IA para noticias + modelos estadísticos en trading de corto plazo

Proyecto de investigación · @Samir Centeno · versión 3 · 16 de noviembre de 2026

## 1. Resumen

**Objetivo:** construir un sistema de corto plazo que gane dinero después de costos. Cada parte hace lo que mejor sabe hacer: la IA lee noticias y los modelos de árboles trabajan con los números de las velas.

**Pregunta:** ¿la información que una IA saca de las noticias mejora la ganancia neta de un modelo estadístico de corto plazo? ¿Mejora más a medida que crece el modelo de IA?

- **H0:** agregar la IA no aumenta la ganancia neta por operación frente al modelo de velas solo ni frente a la referencia.
- **H1:** el sistema con IA obtiene una ganancia neta por operación mayor, con significancia estadística.

**Alcance:** SPY, QQQ, IWM y 50 acciones líquidas de EE. UU., con velas de 1 minuto. Se investiga con las 53 y se opera solo en las baratas de operar: 39 a 60 minutos y 26 a 30 minutos. Quedan fuera por ahora opciones, cripto, apalancamiento y la Bolsa de Valores de Colombia.

**Naturaleza:** es un proyecto de investigación. El dinero real llega solo si H0 se rechaza.

**Dónde vamos:** Fase 1 (datos) completa: las cinco fuentes están descargadas, comprobadas y se actualizan solas cada noche. Fase 2 en curso: la barrera de costos está medida (paso 2.1), las variables están construidas (paso 2.2), la referencia está programada (paso 2.5), los grupos de acciones y los regímenes de mercado están calculados (pasos 2.3 y 2.4) y hay dos versiones del modelo de velas (paso 2.6): las dos tienen señal, pero ninguna paga los costos. Lo siguiente es calibrar la predicción antes de compararla con el costo. Los criterios de éxito (paso 0.4) están confirmados.

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
| 2 · Investigación histórica | Semanas 4–11 | En curso: dos versiones del modelo de velas, que aún no pagan los costos | Un modelo de velas supera la referencia en ganancia neta fuera de muestra, corregido por comparaciones múltiples |
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
- [ ] 2.6 **Entrenar los modelos de velas (competidor B):** dos versiones hechas con `modelo_velas.py` (ver los resúmenes abajo); falta una versión que pague los costos. Plan de mejora, en este orden:
  - [x] 2.6.a **Variables comparativas:** el puesto de cada acción frente a las demás en ese momento (retornos, volumen, volatilidad) y su retorno frente al promedio de su sector. El modelo predice un orden, y hasta ahora casi todas sus variables eran de la acción sola.
  - [x] 2.6.b **Búsqueda de hiperparámetros dentro de cada entrenamiento:** para cada año de prueba se eligen con el último año anterior, nunca con el año de prueba, así que no suma variantes por combinación. La idea sale del taller de tidymodels de Freddy Hernández, cambiando la validación cruzada al azar por una que respeta el tiempo.
  - [ ] 2.6.c **Calibrar la predicción:** el modelo exagera (en la décima más fuerte predice cerca del doble de lo que ocurre), así que el filtro de costo deja pasar operaciones que no pagan. Se corrige con años anteriores al de prueba. Reutiliza las predicciones guardadas, sin reentrenar.
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

#### Resultado de los pasos 2.3 y 2.4

Todo se calcula por ventana, solo con días anteriores a cada año de prueba. El detalle está en `resultados/segmentos.md`.

- **Grupos por correlación: débiles e inestables.** Silueta de 0,09 a 0,12 y entre 4 y 10 grupos según el año. No se usan.
- **Grupos por características** (volatilidad, monto, beta, noticias): más claros, con silueta de 0,38 a 0,42 y 4 o 5 grupos. En 2024: defensivas, cíclicas, tecnológicas volátiles, las cuatro gigantes y TSLA sola.
- **Regímenes:** el BIC elige cuatro en todas las ventanas. Dos son de volatilidad baja y dos de volatilidad alta; a estos los separan la tendencia y si la volatilidad sube o cede.
- **La señal de la primera versión está en los cuatro regímenes** (t de 3 a 7); lo que cambia es si alcanza a pagar el costo. A 60 minutos gana en el régimen volátil que cede (7,35 bps, t 2,31) y pierde en el volátil que cae (−2,98 bps, t −2,45). El primero es sobre todo 2020.
- **No da para una regla:** con ocho casillas, un t de 2,3 no es evidencia fuerte, y operar solo en los regímenes buenos sería una variante nueva.
- **Las operaciones están concentradas** en las tecnológicas volátiles: a 30 minutos, 15.737 de 36.414.

Hipótesis de trabajo: modelar por grupo predice mejor que un modelo único para todas las acciones. Se prueba, no se asume.

Regla anti-anticipación: los grupos y regímenes se recalculan en cada ventana de la validación hacia adelante, solo con datos del pasado.

### Fase 3 · Experimento en vivo (cuenta de papel)

- [ ] 3.1 Los scripts calculan las variables de velas cada 5–15 minutos y reciben las noticias apenas salen.
- [ ] 3.2 Cuando llega una noticia de una acción del universo, cada LLM responde en JSON: tono, tipo de evento, sorpresa, relevancia y, para el competidor C, comprar / vender / nada con retorno esperado y confianza.
- [ ] 3.3 Se registra todo en SQLite: noticia, respuesta y razonamiento del LLM, latencia, decisión, precio de entrada y salida, costo.
- [ ] 3.4 Ejecución en la cuenta de papel de Alpaca, restando costos realistas: la cuenta de papel llena órdenes que en la vida real no se habrían llenado a ese precio.
- [ ] 3.5 Revisión posterior de cada señal: acierto, falso positivo, oportunidad perdida.
- [ ] 3.6 Al cierre, la prueba de H0: D contra B, con la muestra final que no se tocó.

Horario del mercado en Colombia: 9:30 a. m.–4:00 p. m. en invierno de EE. UU.; una hora antes desde marzo.

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

Un comunicado 8-K suele salir antes que la nota de prensa que lo resume, así que le da a la IA el texto original y más temprano. Con las cifras de resultados, la "sorpresa" de un trimestre se calcula con números en vez de pedírsela a la IA. La SEC solo trae lo que la empresa reportó, no lo que esperaban los analistas (ese dato es de pago), así que la sorpresa se mide contra el mismo trimestre del año anterior.

Cada comunicado trae la hora exacta en que quedó público (verificada en UTC) y el tema que trata; el tema 2.02 marca los resultados trimestrales.

### Limitaciones anotadas

- **Sesgo de supervivencia:** el universo son empresas que existen hoy.
- **LIN** tiene datos solo desde 2018, cuando empezó a cotizar con ese símbolo.
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
- **Costo:** un spread completo por operación, con el spread de cada acción medido en el paso 2.1. Todo resultado se repite con el costo doble.
- **Prueba:** sobre la ganancia neta de cada día, no de cada operación, porque las operaciones de un mismo día no son independientes. Una cola, 5% de significancia.
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
| `muestrear_spread.py` | Mide el costo de operar cada acción con cotizaciones reales de compra y venta |
| `barrera_costos.py` | Compara el movimiento del precio con el costo y calcula el acierto mínimo; escribe `resultados/barrera_costos.md` |
| `variables.py` | Arma la tabla de variables y retornos futuros para los modelos, sin usar información del futuro |
| `referencia.py` | Aplica los cuatro efectos de la referencia (competidor A) y calcula su ganancia neta; escribe `resultados/referencia.md`. No usa la muestra final salvo con `--muestra-final` |
| `modelo_velas.py` | Entrena el modelo de velas (competidor B) con validación hacia adelante y lo compara con la referencia; escribe `resultados/modelo_velas.md` |
| `segmentos.py` | Calcula los grupos de acciones y los regímenes de mercado por ventana de validación, y mide si la señal del modelo de velas cambia según el segmento; escribe `resultados/segmentos.md` |
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
