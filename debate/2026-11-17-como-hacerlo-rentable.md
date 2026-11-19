# Debate: ¿cómo hacer rentable el proyecto?

## Tema

Pregunta de Samir (17 de noviembre de 2026): "Ya ven los resultados y el procedimiento que se realizó aquí; esperaba mejores resultados. Necesito que surjan nuevas ideas: ¿cómo lo hace la industria? ¿Cómo podríamos hacer esto rentable? ¿Nuevos modelos? ¿Recomendaciones? ¿Algo más?"

Contexto mínimo: documento principal (`Proyecto de investigación IA vs. modelos estadísticos en trading de corto plazo.md`) y `resultados/muestra_final.md`. B (LightGBM con velas, entrada 10:20, salida 15:55) dio −2,75 bps netos en 2025–2026; la selección pasó de +3,5 bps (t 3,8) en desarrollo a −0,96 (t −0,44). La IA (Haiku 5.5) no se evaluó.

## Ronda 1 — Claude

**Diagnóstico: el problema no es el modelo, es dónde se está compitiendo.**

1. **El campo de juego es el más eficiente del mundo.** Son 50 megacaps con velas de 1 minuto y solo precio y volumen: es exactamente lo que miran miles de fondos cuantitativos y creadores de mercado. La señal bruta, de 2 a 5 bps, y el costo, de 1,8 a 2,3 bps, son del mismo tamaño (2.1, idea 5, `muestra_final.md`). En la industria, el corto plazo intradía en megacaps es rentable para quien *cobra* el spread (creadores de mercado, con reembolsos y colocación), no para quien lo *paga* con órdenes de mercado.
2. **La señal que había ya venía muriendo.** 2023 y 2024 ya eran negativos (variante 12) y la selección desapareció en 2025–2026. Es el patrón típico de una anomalía publicada o arbitrada, no de un error de programación.
3. **Se gastó el histórico.** 14 variantes sobre 2016–2024 más la muestra final abierta: hoy no queda ningún dato limpio de esas 50 acciones para probar una idea nueva sin sesgo.

**Propuestas, de mayor a menor convicción:**

- **A · Alargar el horizonte a días o semanas.** El propio proyecto lo mostró: la señal crecía al mantener más tiempo, con el mismo costo (diagnósticos, tabla de duración). A 5–20 días el movimiento típico es de cientos de bps y el spread se vuelve ruido. Es donde vive la mayor parte del dinero cuantitativo que no es de alta frecuencia: impulso, reversión de una semana, deriva tras resultados (PEAD, que en la referencia se probó *dentro del día* cuando está documentada a semanas) y factores de calidad o valor.
- **B · Donde la IA sí tiene ventaja: eventos, a varios días.** Leer un 8-K, un informe de resultados o una transcripción y medir sorpresa o tono es lo que un LLM hace mejor que un árbol. La deriva posterior dura días, así que la latencia deja de importar. La regla del pasado (sección 2) se sigue respetando: se evalúa solo con eventos posteriores a la fecha de corte.
- **C · Datos limpios nuevos: otras acciones.** Las otras ~450 del S&P 500 (o el Russell 1000) en 2016–2024 nunca se miraron. Sirven como réplica fuera de muestra *en el corte transversal* sin esperar meses en vivo. Además, las acciones medianas son menos eficientes; con horizonte de días, su costo mayor importa poco.
- **D · Ejecución en subastas.** Entrar y salir con órdenes de apertura y cierre (MOO/MOC) en vez de cruzar el spread. Una parte grande del volumen de la industria se ejecuta ahí; el costo efectivo es menor que medio spread.
- **E · Construcción de cartera neutral.** Comprar y vender a la vez (largo/corto por sector, ajustado por beta), con riesgo repartido por igual entre posiciones. Hoy cada operación se mide sola y sin cobertura (criterios de la sección 5); eso deja la varianza del mercado adentro y baja el t.

**Lo que no haría:** seguir afinando B a 15:55, agregar redes neuronales (LSTM o transformers sobre velas) ni volver a mirar 2025–2026 para ajustar nada.

**Pregunta para Gemini:** ¿cuál de estas atacarías primero con los datos que ya hay en `datos/`? ¿Ves algún camino que no estoy viendo, por ejemplo opciones, volatilidad o algo propio del perfil de Samir (capital chico, Colombia, plan gratuito)?

## Ronda 1 — Gemini

### Crítica a Claude: el sesgo institucional y la trampa del overnight

El punto más débil de Claude es proponer **cartera neutral (E)** y **horizonte a semanas (A)** ignorando la realidad de una cuenta chica en Colombia (sección 1) y los propios datos del repo:

1. **La cartera neutral destruye la cuenta chica.** En retail con Alpaca y sin apalancamiento (sección 1), vender en corto exige cuenta de margen ($25k por PDT), paga tasas de préstamo (*borrow fees*) y doble spread. Además, en `ventaja.py` (sección 2.6.c) cubrir cada operación con el promedio redujo la ganancia neta de 2,07 a 0,90 bps (t 1,61) *antes de pagar el costo de la cobertura*. Con beta casi nula (0,008 en `revision_cierre.md`), pagar dos patas para neutralizar mercado es regalar dinero en comisiones.
2. **Extrapolación errónea del horizonte:** Claude cita la tabla de duración de `diagnosticos.py` para saltar a semanas. Pero esa tabla midió exclusivamente derivas *dentro del día* hasta las 15:55. Pasar a semanas asume el riesgo nocturno (*overnight gap*), donde ocurre el 84% de los comunicados y el spread fuera de horario escala a 15–25 bps (sección 2.1).
3. **Incoherencia con los datos:** Claude pregunta qué atacar primero con lo que hay en `datos/`, pero propone 450 acciones nuevas (C) que no están descargadas (solo hay 53, sección 1.1), y un LLM para eventos (B) que en vivo daría apenas ~200 resultados al año en 50 acciones: estadísticamente raquítico frente a las miles de operaciones que exige la significancia (sección 2.1).

### Propuesta: Swing EOD Long-Only sobre lo ya construido

El retail cuantitativo no compite contra creadores de mercado pagando spread en velas de 1 minuto; compite en datos diarios (EOD) donde la latencia no importa:

1. **Colapsar `datos/minuto` a barras diarias (EOD).** En `datos/` ya existen 9 años de precios limpios y ajustados (`precios.py`). A 3–10 días, el spread (~2 bps) pasa de ser el 66% de la ganancia bruta (`muestra_final.md`) a menos del 1% de un movimiento swing de 300 bps.
2. **Estrategia Long-Only transversal:** Sin ventas en corto (cero costo de préstamo ni margen; respeta sección 1). Se ordenan las 50 acciones por momentum relativo y compresión de volatilidad; se entra al cierre sin sufrir los 20 minutos de desfase del plan gratuito.
3. **IA para PEAD real:** Usar Haiku en vivo (respetando la regla del pasado, sección 2) para medir sorpresa en 8-K y sostener 3–5 días (deriva post-resultados documentada), no dentro de la sesión.

**Pregunta para Claude:** Si colapsamos a diario para eliminar la fricción del plan gratuito y el spread intradía, ¿qué factor transversal simple proponés para evitar el sobreajuste que liquidó a B en 2025–2026?

## Ronda 2 — Claude

**Concedo dos cosas:** la cartera neutral (E) no es para una cuenta chica, y el LLM sobre eventos da pocas observaciones por año en 50 acciones. E queda descartada para empezar.

**Pero hay tres errores en la crítica, y uno es grave para el proyecto entero:**

1. **Mantener de un día para otro no obliga a operar fuera de horario.** Se compra y se vende en horario normal o en las subastas de apertura y cierre; el spread de 15–25 bps del pre-mercado (2.1) no se paga. El salto nocturno es riesgo (varianza), no costo. Y está documentado que en EE. UU. gran parte del retorno de las acciones llega de noche: quedarse fuera de la noche, como hace B, es renunciar a él.
2. **La regla PDT afecta más a B que a cualquier otra cosa.** B hace unas 27 operaciones *dentro del día* por jornada (cálculo de la Fase 3). Con una cuenta de margen menor a 25.000 dólares, eso no se puede hacer en EE. UU. (hay que verificar si el cambio de esa regla que propuso FINRA ya rige). Una estrategia de días la esquiva por diseño. Es otro argumento contra el intradía, no contra los días.
3. **Bajar a diario no resuelve el sobreajuste si se sigue usando las mismas 50 acciones.** Esos precios ya se miraron 14 veces. Y la amplitud es poca: con 50 acciones, una cartera de factor transversal tiene unos 10 nombres por lado y muchísimo ruido (el rendimiento ajustado por riesgo crece con la raíz de las apuestas independientes). Descargar más acciones diarias no es incoherente: con Alpaca son minutos, no los 70 millones de velas de 1 minuto.

**Respuesta a tu pregunta:** no elegiría *un* factor buscando el que mejor funcione, porque eso es volver a hacer lo de B. Prerregistraría, con reglas fijas de la literatura y sin afinar:
- **Impulso 12-1 meses** con rebalanceo mensual, solo compras, entre las ~500 del S&P 500.
- **Seguimiento de tendencia por serie de tiempo** en un puñado de ETF (SPY, QQQ, IWM, más bonos, oro y materias primas si se agregan): estar comprado si el precio supera su media de 10 meses, si no en efectivo. Es la estrategia cuantitativa más robusta para una cuenta chica: pocas operaciones al año, sin cortos, sin PDT, y protege de las caídas grandes.
- **PEAD a 1–60 días** con la sorpresa *numérica* de las cifras de la SEC (ya en `datos/sec/cifras`), sin LLM, para tener historia; la IA se suma después, en vivo, como mejora.

Las tres se validan en acciones o periodos no tocados, con la regla de decisión escrita antes.

**Pregunta para Gemini:** ¿hay un camino donde la IA sea el centro y no un adorno, compatible con la regla del pasado y con potencia estadística?

## Ronda 2 — Gemini

### Crítica a Claude: capitulación del objetivo y confusión de riesgos

El punto más débil de Claude es **rendirse en el objetivo central del proyecto** y maquillar el riesgo nocturno:

1. **Capitulación:** Proponer medias móviles de 10 meses en ETFs y momentum 12-1 sin IA no responde a la pregunta de Samir ni resuelve el proyecto; lo reemplaza por gestión pasiva indexada tradicional. Relegar la IA a "un adorno posterior en vivo" evade la hipótesis central fijada en el documento (sección 1): *¿aporta la IA ventaja neta frente a los modelos estadísticos?*
2. **Confusión entre índice y acciones:** Claude cita la prima nocturna documentada para justificar el *overnight*. Pero esa anomalía existe en el índice agregado (SPY); en acciones individuales sin cobertura sectorial ni cortos (descartados en la ronda 1 para cuenta chica), el gap nocturno no es "retorno con varianza", sino riesgo asimétrico de cola ante sorpresas de resultados o eventos corporativos (sección 2.1).

### Propuesta: La IA como motor de alfa en eventos Swing (2 a 5 días)

Respondiendo a Claude: **sí hay un camino donde la IA es el centro, respeta la regla del pasado y tiene potencia estadística.**

1. **La ventaja del LLM es la información blanda (*soft information*):** Las cifras numéricas de la SEC (`datos/sec/cifras`) ya las descuenta el mercado cuantitativo en milisegundos. El verdadero valor de Claude Haiku 5.5 (ya operativo en `lector_noticias.py`, respondiendo en 2,1 s a $0,025 por noticia) es procesar el tono, la sorpresa del *guidance* y los factores de riesgo en el texto de los 8-K.
2. **Potencia estadística ampliando el universo a EOD:** En las 50 acciones del proyecto hay apenas ~200 resultados al año. Pero ampliando el universo a las 500 del S&P 500 en datos diarios (que en Alpaca toma minutos y elimina las fricciones de velas de 1 minuto), se obtienen ~2.000 eventos de resultados anuales.
3. **Respeto estricto a la regla del pasado (sección 2):** Se toma la fecha de corte (*knowledge cutoff*) de Haiku 5.5. Todo el período posterior al corte es genuinamente fuera de muestra. Con 2.000 eventos anuales post-corte, se logra significancia estadística ($t \ge 2$) en meses de datos limpios, no en una década.
4. **Ejecución swing:** Entrada en subasta de apertura (MOO) post-evento para el decil superior de sorpresa no descontada en el pre-mercado; salida a 3–5 días. Cero PDT, spread despreciable frente a un movimiento swing de 300 bps, y la IA como motor del 100% de la selección.

**Pregunta para Claude:** Si la IA evalúa únicamente el período posterior a su fecha de corte sobre 500 acciones a nivel diario, ¿qué objeción metodológica queda para no hacer de la sorpresa textual en 8-K el núcleo del nuevo sistema?

## Ronda 3 — Claude

**Acepto el núcleo:** sorpresa textual de resultados, S&P 500, 2–5 días (o más), con la IA en el centro. Es la mejor idea del debate y la adopto. Pero "capitulación" no es justo: Samir preguntó cómo hacerlo *rentable*, y la tendencia en ETF es el piso que cualquier sistema con IA tiene que superar, como lo fue A para B. Y la prima nocturna también está documentada en el corte transversal de acciones, no solo en el índice; el riesgo de cola sí es real y se maneja con tamaño de posición.

**Quedan cuatro objeciones, y todas tienen arreglo:**

1. **El período posterior al corte de Haiku 5.5 casi no existe todavía.** Es un modelo reciente: lo limpio son pocos meses, y además en vivo. **Arreglo:** la hipótesis es "un LLM lee sorpresa en el texto", no "Haiku 5.5 en particular". Se puede usar un modelo con fecha de corte anterior a 2025 y evaluarlo con los eventos de 2025–2026 del S&P 500 (las 450 acciones fuera de las 50 nunca se miraron). Hay que verificar el corte del modelo elegido y comprobar que no "sabe" el resultado: preguntarle por el precio posterior a eventos conocidos.
2. **2.000 eventos no son 2.000 observaciones independientes.** Los resultados se agrupan en cuatro temporadas, y los de una misma semana se mueven juntos. La potencia real se mide por semanas de temporada, con remuestreo por bloques, como ya hace el proyecto.
3. **"Sorpresa" necesita una expectativa.** El consenso de analistas es un dato pago. **Aquí la IA aporta algo que ningún árbol puede:** las noticias de Benzinga ya traen "supera la estimación por X centavos" y el cambio de la guía. Que el LLM *extraiga* sorpresa frente al consenso y frente a la guía anterior desde el texto reemplaza un dato que cuesta miles de dólares al año.
4. **Base de comparación obligatoria:** PEAD con la sorpresa numérica (sin LLM) en los mismos eventos. Si la IA no le gana a esa base, no aporta. Es la pregunta original del proyecto (D contra B), trasladada a donde sí puede ganar.

**Pregunta para Gemini, para cerrar:** de estas cuatro, ¿cuál considerás que no se resuelve? Y dame tu ranking final de las ideas del debate.

## Ronda 3 — Gemini

### Crítica a Claude: la ilusión del "control de contaminación"

El punto más débil de Claude es su arreglo para la **objeción 1**: proponer un modelo con fecha de corte anterior a 2025 y "comprobar que no sabe el resultado preguntándole el precio".

Esto es metodológicamente insostenible y vulnera la **Regla sobre la IA y el pasado (sección 2)**:
1. **La memoria del LLM no es episódica:** Que un modelo no recuerde el precio exacto de una acción tras un evento no demuestra ausencia de fuga (*data leakage*). La exposición a resúmenes corporativos, noticias y ajustes por RLHF en el preentrenamiento altera el espacio latente y las probabilidades de los tokens, sesgando la interpretación del tono y la sorpresa.
2. **Rompe la higiene del repo:** La regla de la sección 2 ("evaluarlo con noticias anteriores a su corte es hacer trampa sin querer") se fijó para blindar el proyecto contra este autoengaño. La objeción 1 **no se resuelve mirando al pasado con modelos viejos**; se resuelve aceptando que la IA debe evaluarse **en vivo** acumulando temporadas de resultados en el S&P 500, o admitirás un sesgo de anticipación peor que el sobreajuste de B.

### La objeción que no se resuelve

De las cuatro, **la 1 es la que no tiene arreglo en histórico.** Forzar un backtest retrospectivo con LLMs es comprar un falso positivo. Las otras tres tienen solución rigurosa: la **2** se neutraliza con remuestreo por bloques por temporada de resultados; la **3** se resuelve instruyendo a Haiku en `lector_noticias.py` para extraer la sorpresa frente a la guía previa en el propio texto del 8-K; y la **4** es obligatoria (benchmark contra la sorpresa numérica de `datos/sec/cifras`).

### Ranking final de ideas

1. **PEAD swing con LLM en 8-K (S&P 500, 2–5 días, solo compras).** Se prueba en vivo (post-corte) sobre temporadas de resultados, contra el PEAD numérico puro. Se descarta si la IA no supera a la sorpresa numérica tras costos en 2 temporadas (t < 2).
2. **Piso sistemático: tendencia en ETF (media de 10 meses).** Simulación diaria 2016–2026 sin reoptimizar. Se descarta si el Sharpe no supera al de comprar y mantener o si la caída máxima pasa de 20%.
3. **Impulso transversal 12-1 (S&P 500).** Factor clásico; requiere descargar 450 símbolos y sufre rotaciones bruscas.
4. **Afinar B intradía o cartera neutral: descartadas.**

## Síntesis (Claude)

### Acuerdos
- **Dejar el intradía en megacaps.** Ahí la señal (2–5 bps) es del tamaño del costo, compite contra quien cobra el spread, y su ventaja ya se gastó (`muestra_final.md`). B no se sigue afinando.
- **Pasar a horizonte de días con datos diarios**, en horario normal o subastas: el spread deja de importar y desaparece el problema de la regla PDT (B hace ~27 operaciones dentro del día por jornada).
- **Solo compras y sin cartera neutral** mientras la cuenta sea chica.
- **Ampliar el universo al S&P 500** por amplitud estadística; las ~450 acciones nuevas además son datos no tocados.
- **La IA va en el centro, sobre resultados trimestrales:** extraer del texto la sorpresa frente al consenso y frente a la guía anterior, que es justo el dato pago que no se tiene.
- **Base obligatoria:** PEAD con sorpresa numérica, sin LLM, en los mismos eventos. Es la pregunta original (D contra B) en un terreno donde la IA puede ganar.

### Desacuerdo abierto
- **¿Se puede probar la IA en histórico con un modelo cuya fecha de corte sea anterior al periodo?** Gemini dice que no: cualquier exposición contamina. Claude sostiene que si el corte es real, el modelo no pudo ver eventos posteriores, y el riesgo es que el corte declarado sea falso, no la "memoria latente". Es la decisión clave de diseño: define si la primera respuesta llega en semanas (histórico) o en 6 meses o más (vivo). **Decide Samir.** Una salida intermedia: hacer las dos cosas y que solo la prueba en vivo cuente para operar dinero.

### Ideas ordenadas (valor esperado × facilidad de probar)

| # | Idea | Cómo se prueba | Qué la descarta |
| --- | --- | --- | --- |
| 1 | **PEAD numérico (sin IA)**, S&P 500, 1–20 días, solo compras | Histórico 2016–2026 con `datos/sec/cifras` ampliado a 500 acciones; regla fija de la literatura escrita antes | Neta ≤ 0 tras costos o t por bloques (por temporada) < 2 |
| 2 | **PEAD con sorpresa leída por LLM** | En vivo desde la próxima temporada (enero de 2027) y, si Samir lo aprueba, en histórico con un modelo de corte anterior | No le gana a la idea 1 en los mismos eventos |
| 3 | **Tendencia en ETF** (media de 10 meses) | Regla fija sin optimizar; es el piso. La muestra local (2016–2026) da pocas operaciones, así que pesa la evidencia de la literatura | Caída máxima no menor que la de comprar y mantener |
| 4 | **Impulso 12-1** en el S&P 500 | Regla fija, rebalanceo mensual | Neta no mejor que el promedio del universo |
| — | Afinar B, redes sobre velas, cartera neutral | No se hacen | — |

### Primer paso propuesto
Descargar velas **diarias** y fechas de resultados (8-K, ítem 2.02) de las ~500 del S&P 500, y escribir el protocolo de la idea 1 *antes* de correrla. Es barato, no toca datos usados y da la base contra la que la IA tendrá que competir.

**Cuidado que ninguno de los dos mencionó en el debate:** usar la lista *actual* del S&P 500 para 2016–2026 mete sesgo de supervivencia (solo quedan las que sobrevivieron y subieron). Hay que usar la composición histórica del índice en cada fecha, o al menos marcar ese sesgo como limitación.
