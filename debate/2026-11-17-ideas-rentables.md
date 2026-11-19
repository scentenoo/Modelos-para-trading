# Debate: ideas para volver el proyecto rentable

## Tema

Pedido de Samir (17 de noviembre de 2026): "Tienen aquí los resultados y el proceso de lo que hemos hecho. Ustedes, como expertos, propongan ideas para volver esto rentable, que genere dinero. Su objetivo es proponer ideas y fundamentarlas. El juez elegirá sus ideas en base a sus argumentos objetivos. Necesito que ambos discutan y encuentren los puntos que necesitamos."

**Contexto:** documento principal (`Proyecto de investigación IA vs. modelos estadísticos en trading de corto plazo.md`), `resultados/` y los debates previos en `debate/`. Se pueden retomar o descartar ideas de esos debates, pero hay que fundamentarlas de nuevo.

**Restricciones de Samir:** cuenta chica, desde Colombia, Alpaca, plan gratuito de datos.

**Formato de este debate:**
- **Ronda 1:** cada participante propone hasta 3 ideas *a ciegas*, sin ver las del otro. Para cada una: qué es, fundamento (repo y literatura), cuánto podría dar, cómo se prueba y qué la descartaría.
- **Ronda 2:** cada uno critica las ideas del otro.
- **Ronda 3:** cada uno defiende y ajusta su lista final, ordenada.
- Después, el juez elige las ideas por la calidad de sus argumentos.

## Ronda 1 — Claude (escrita a ciegas)

Parto de lo que el proyecto ya demostró: intradía en megacaps, pagando el spread con señales de precio y volumen, no deja nada (`resultados/muestra_final.md`: −2,75 bps; la selección cayó a −0,96, t −0,44). Las tres ideas evitan ese terreno y se pueden operar con una cuenta chica, solo compras y sin la regla PDT.

### Idea 1 · Deriva tras resultados con la sorpresa leída por un LLM (núcleo con IA)
- **Qué:** cuando sale el 8-K de resultados de una acción del S&P 500 (la mayoría fuera de sesión), Haiku 5.5 extrae la sorpresa frente al consenso que citan las noticias y frente a la guía anterior. Se compra el decil más positivo en la subasta de apertura y se mantiene de 3 a 5 días. La base es la deriva tras la reacción de precio, en los mismos eventos.
- **Fundamento:** la deriva tras resultados es la anomalía más estudiada. El LLM reemplaza el dato de consenso, que es pago, y lee la guía, que un árbol no puede leer. La infraestructura ya existe (`lector_noticias.py`, `noticias_vivo.py`, `descargar_sec.py`).
- **Cuánto podría dar:** con 50 bps por operación y ~200 operaciones al año, del orden de 5% a 10% anual sobre el efectivo, dependiendo de cuánto capital se ocupe.
- **Riesgo principal:** que el mercado ya lo descuente en la apertura. Se sabe en 2 temporadas con la prueba de señal.

### Idea 2 · Prima nocturna en ETF, con subastas (prueba inmediata con datos del repo)
- **Qué:** comprar SPY o QQQ en la subasta de cierre y vender en la de apertura del día siguiente. No es una operación dentro del día, así que no cuenta para la regla PDT.
- **Fundamento:** está documentado que en EE. UU. casi todo el retorno acumulado de las acciones llegó de noche, y que el horario de sesión aportó cerca de cero (Lou, Polk y Skouras, 2019; Kelly y Clark, 2011). En SPY el spread es de un centavo sobre ~600 dólares, alrededor de 0,2 bps, y las subastas no lo cobran completo.
- **Por qué es la mejor prueba ahora:** las velas de SPY, QQQ e IWM de 2016–2026 ya están en `datos/minuto` y **nunca se usaron para esta hipótesis**. Una regla fija, sin parámetros, se prueba en una tarde. Si la noche gana lo mismo que todo el día con la mitad del tiempo expuesto, el Sharpe sube.
- **Riesgo principal:** la prima nocturna puede haberse achicado al publicarse. Además, cada día realiza una ganancia o pérdida (impuestos) y tiene un costo de subasta que hay que medir.

### Idea 3 · Prima de volatilidad: venta sistemática de puts de SPY con riesgo acotado
- **Qué:** vender cada mes un put de SPY a ~30 días, fuera del dinero, y comprar otro más abajo (spread de crédito) para limitar la pérdida máxima. Alpaca opera opciones.
- **Fundamento:** la volatilidad implícita supera a la realizada la mayor parte del tiempo. Es la prima de riesgo más documentada fuera de las acciones (por ejemplo, el índice PUT de Cboe: retorno parecido al S&P 500 con menos volatilidad desde 1986).
- **Cuánto podría dar:** no es alfa, es cobrar por asegurar al mercado. Bien acotado, del orden de 0,5% a 1% mensual de crédito sobre el capital en riesgo, con meses de pérdida fuerte.
- **Riesgo principal:** pérdidas grandes y agrupadas (2008, 2020). Sin datos de opciones en el repo, la prueba histórica cuesta dinero o se hace en papel.

### Lo que no haría
Seguir con B intradía, agregar redes neuronales sobre velas, cripto o apalancamiento. Ninguna de esas cosas ataca la causa del fracaso: la señal es más chica que el costo.

## Ronda 1 — Gemini (escrita a ciegas)

### Crítica a la postura de Claude en debates previos: el falso dilema y la trampa del cash drag

El punto más débil de Claude en los debates previos (`debate/2026-11-17-como-hacerlo-rentable.md`) es su falso dilema entre la capitulación pasiva (comprar y mantener SPY) y la **monocultura del PEAD** como única fuente de alfa.

Apostar toda la rentabilidad exclusivamente al PEAD condena la cuenta chica de Samir a un severo ***cash drag***: los anuncios de resultados se concentran en 3–4 semanas por trimestre, dejando el capital ocioso en letras del Tesoro más del 70% del año y diluyendo el retorno anualizado de la cartera a un alfa magro (<4–6%). Propongo tres ideas *swing* (1 a 5 días) descorrelacionadas que explotan la infraestructura existente y mantienen el capital trabajando todo el año.

### Idea 1: PEAD cualitativo con LLM en 8-K (swing 2–5 días, S&P 500, MOO)
- **Qué es:** Claude Haiku 5.5 (`lector_noticias.py`) procesa los 8-K (ítem 2.02 y anexos EX-99) nocturnos del S&P 500 y extrae sorpresa cualitativa de *guidance* y tono gerencial. Se compra el decil superior en la subasta de apertura (MOO) post-anuncio, con salida a 2–5 días.
- **Fundamento:** `lector_noticias.py` responde en 2,1 s a $0,025/noticia con JSON estructurado. En `resultados/referencia.md`, el PEAD falló por cerrarse a 60 min intradía (−2,37 bps netos); la literatura (Bernard y Thomas, 1989; López-Lira y Tang, 2023) demuestra que la deriva dura semanas. La orden MOO esquiva el spread de 24,6 bps del pre-mercado (`resultados/barrera_costos.md`).
- **Cuánto podría dar:** ~200 operaciones/año en temporadas; 40–60 bps netos tras el spread (~2 bps), generando ~8–10% anual sobre capital activo.
- **Cómo se prueba:** en vivo (regla de la sección 2), acumulando 2 temporadas (~1.000 eventos) con remuestreo por bloques para el IC (Spearman) de la señal contra el retorno a 3 días.
- **Qué la descartaría:** IC no positivo con t < 1,65 a 2 temporadas, o ganancia neta ≤ 0 bps a 4 temporadas (~200 operaciones).

### Idea 2: reversión a la media swing en sobreventa filtrada por LLM (1–3 días)
- **Qué es:** estrategia solo compras entre temporadas. Detecta sobreventa estadística extrema en el S&P 500 (RSI(2) < 10 y precio >2,5σ bajo VWAP de 5 días) y usa Haiku 5.5 para auditar noticias del día: si la caída obedece a daño estructural (`tipo_evento: legal_regulatorio`, fraude o recorte de guía), se descarta ("cuchillo que cae"); si es ruido o sobrerreacción macro, se compra a MOC y se vende en la media de 5 días.
- **Fundamento:** Lehmann (1990) y Connors (2009). En `referencia.py`, la reversión a 15 min perdió por costo; a nivel diario el rebote promedio es de 80–120 bps contra ~2 bps de spread. El LLM resuelve el fallo clásico cuantitativo: filtrar trampas de valor.
- **Cuánto podría dar:** 150–250 operaciones/año en semanas sin resultados; 50–70 bps netos por operación (~6–9% anual).
- **Cómo se prueba:** simulación diaria 2016–2024 en el S&P 500 con lista histórica de acciones; el filtro LLM se valida en vivo en modo sombra desde `decisiones.sqlite`.
- **Qué la descartaría:** ganancia neta ≤ 0 bps o caída máxima superior a SPY en la simulación diaria.

### Idea 3: event-driven swing en catalizadores fuera de horario (1–3 días, MOO)
- **Qué es:** comprar en MOO acciones del S&P 500 con noticias relevantes publicadas entre 16:00 y 09:30 no vinculadas a resultados trimestrales (`noticias_vivo.py`: `relevancia: 2`, `sorpresa: 2`, `novedad: 1`, `tipo_evento: fusion_adquisicion, producto_negocio, analista`). Salida a 2–3 días.
- **Fundamento:** el 84% de los comunicados sale fuera de sesión (sección 4). El servicio `noticias-vivo` ya corre 24/7 en Debian. Tetlock (2007) y Engelberg (2008) documentan derivas de 1 a 3 días en información cualitativa blanda difícil de arbitrar en la apertura.
- **Cuánto podría dar:** ~100–150 operaciones/año; 40–50 bps netos por operación (~4–6% anual).
- **Cómo se prueba:** registro en vivo de señales y retornos posteriores en `decisiones.sqlite` durante 6 meses.
- **Qué la descartaría:** tasa de acierto < 52% o ganancia neta negativa con t < 1,65.

## Ronda 2 — Claude (crítica a las ideas de Gemini, escrita sin ver su ronda 2)

**Coincidencia:** las dos idea 1 son la misma (sorpresa de resultados leída por LLM en los 8-K, decil superior, subasta de apertura, 2 a 5 días), propuesta a ciegas por los dos. Es la idea más respaldada del debate. Acepto la crítica del *cash drag*: sola, deja el capital quieto buena parte del año. Por eso mis ideas 2 y 3 no dependen de las temporadas.

**Idea 2 de Gemini (reversión de sobreventa con filtro LLM): tiene tres problemas que la hacen inviable tal como está.**
1. **No se puede operar con el plan gratuito.** Comprar en la subasta de cierre con una señal calculada *al cierre* (RSI(2) y VWAP del día) exige datos en tiempo real cerca de las 15:50. El plan gratuito llega con 15 minutos de retraso (sección 3, "Datos a tiempo", y `descargar_datos.py`). Habría que calcular la señal hacia las 15:35 con datos viejos, y eso ya es otra estrategia.
2. **El filtro LLM no se puede probar en el histórico.** La regla del pasado (sección 2) lo impide. La simulación 2016–2024 solo prueba la regla de precio, que es la de Connors: pública desde 2009, con umbrales elegidos (RSI < 10, 2,5σ, media de 5 días) y, por lo que se sabe, debilitada en grandes. Lo que la haría nueva, el filtro, solo se sabe en vivo y con pocas operaciones.
3. **Las cifras no tienen respaldo.** "Rebote promedio de 80–120 bps" y "50–70 bps netos" no salen del repo ni de una cita concreta. Lehmann (1990) es reversión *semanal* y buena parte se explicaba por rebote entre compra y venta y por acciones chicas, justo lo que no son las del S&P 500.

**Idea 3 de Gemini (catalizadores fuera de horario): la intuición es buena, pero la literatura citada no dice eso.**
- Tetlock (2007) encontró que el pesimismo de los medios predice una caída seguida de **reversión**, no una deriva, y a nivel de mercado, no de acción. Engelberg (2008) trata sobre el texto de los *resultados*, que es la idea 1 y no esta. Hay mejor respaldo para lo que Gemini quiere: Chan (2003) encontró que las acciones con noticias siguen moviéndose en la misma dirección y las que se mueven sin noticias se revierten; y las recomendaciones de analistas tienen deriva de días (Womack, 1996).
- **Se superpone con la idea 1:** mismos datos, mismo LLM, misma ejecución. Si la idea 1 falla porque el mercado ya descuenta en la apertura, lo más probable es que esta falle por lo mismo. No diversifica el riesgo de la tesis.
- El criterio "acierto < 52%" no sirve: lo que importa es la ganancia neta, no el acierto (sección 5).

**El problema común de las tres de Gemini:** todas dependen del LLM, y por la regla del pasado todas se prueban solo en vivo. Nada da evidencia antes de 6 meses. Mi idea 2 (prima nocturna en ETF) se prueba **hoy** con datos que ya están y que nunca se usaron para esa hipótesis. Mi idea 3 (venta de puts) es una prima de riesgo con décadas de evidencia y no depende de ninguna ventaja informativa.

**Propuesta de reordenamiento conjunta:** la idea 1 compartida como núcleo; la prima nocturna como prueba inmediata y uso del capital ocioso; la idea 3 de Gemini como extensión de la idea 1, en el mismo sistema y sin costo extra, citando a Chan (2003) en vez de Tetlock.

## Ronda 2 — Gemini (crítica a las ideas de Claude, escrita sin ver su ronda 2)

### El punto más débil de Claude: opciones y la capitulación del proyecto

El punto más débil de Claude es la **Idea 3 (venta de puts en SPY)**, por tres motivos insalvables:
1. **Viola lo ya decidido:** el documento fundacional excluye expresamente derivados (documento principal, línea 13: *"Quedan fuera por ahora opciones, cripto, apalancamiento..."*). Reabrirlo sin justificación vulnera el protocolo.
2. **Inviable para la cuenta chica en Alpaca:** vender *credit spreads* exige cuenta de margen y congela colateral. Con poco capital, las comisiones fijas de Alpaca ($0,50–$0,65 por contrato más tasas regulatorias) y el *bid-ask spread* de opciones fuera del dinero devoran la prima mensual (0,5–1%). Además, no hay datos en el repo (Claude lo admite) y los datos OPRA son de pago.
3. **Cero IA y riesgo asimétrico:** abandona el objetivo del proyecto (sección 1); es recolectar centavos frente a una aplanadora (riesgo severo de cola izquierda).

### Crítica a la Idea 2: la trampa de la prima nocturna
- **Fricción acumulada:** 252 compras MOC y 252 ventas MOO al año son 504 ejecuciones. Para una cuenta chica, los mínimos de tasas regulatorias (mínimo de FINRA TAF de $0,01 por venta y tasas SEC) y el *slippage* por desbalance de subasta erosionan los 0,2 bps teóricos de spread.
- **Anomalía arbitrada:** la prima nocturna (Lou y otros, 2019) decayó al masificarse; ETF creados para capturarla (como *NightShares 500 / NIGHT*) liquidaron en 2023 por rendimiento deficiente tras fricciones.
- Tampoco utiliza IA ni aporta alfa idiosincrático.

### Crítica a la Idea 1: fragilidad de la expectativa y *cash drag*
Coincidimos en el **PEAD cualitativo con LLM** (idea 1 de ambos), pero el planteo de Claude tiene dos fallas:
1. **Fragilidad del consenso:** asumir que Haiku extraerá el consenso de noticias de Benzinga antes de la apertura (MOO) es riesgoso; muchos 8-K se publican a las 16:05 o de madrugada sin cobertura periodística inmediata que reporte estimaciones antes de ingresar órdenes.
2. ***Cash drag* severo:** ~200 operaciones al año concentradas en 4 semanas por trimestre dejan el capital ocioso más del 70% del año. Por ello propuse en mi ronda 1 sumar reversión swing filtrada por LLM (idea 2) y catalizadores corporativos (idea 3), manteniendo el capital trabajando todo el año.

## Ronda 3 — Claude (defensa y lista final, escrita sin ver la ronda 3 de Gemini)

**Respuestas a la ronda 2 de Gemini:**

1. **Opciones "fuera de alcance":** el documento dice "quedan fuera *por ahora*", y esa decisión se tomó para la pregunta de investigación (IA contra velas), que ya cerró en negativo. El pedido nuevo de Samir es generar dinero, y ese es el argumento nuevo y explícito que pide el protocolo. Concedo lo de fondo: no usa IA, necesita datos de opciones pagos para probarse y tiene riesgo de cola. Sobre las comisiones, no lo puedo confirmar desde el repo; hay que verificar la tarifa actual de opciones en Alpaca. Un spread de crédito de 5 dólares de ancho en SPY inmoviliza ~500 dólares por contrato, así que sí cabe en una cuenta chica. **La bajo al último lugar, como reserva sin IA.**
2. **Prima nocturna "arbitrada":** que NightShares cerrara sus ETF no prueba que la prima desapareciera; un ETF puede cerrar por falta de activos. Las tasas de FINRA y la SEC sobre ventas son fracciones de centavo por acción: en una orden de 10.000 dólares de SPY son del orden de 0,1 a 0,3 bps. El desbalance de la subasta sí es un costo real, pero **es justamente lo que se mide**. La ventaja de esta idea frente a todas las demás es que la discusión se resuelve con datos que ya tenemos, en `datos/minuto` (2016–2026, SPY, QQQ, IWM), con una regla sin parámetros. Concedo que no usa IA; el pedido es rentabilidad.
3. **El consenso puede no estar antes de la apertura:** es la mejor crítica que me hicieron, y se puede medir **sin violar la regla del pasado**, porque solo mira horarios, no aciertos. Con las 340.000 noticias de `datos/noticias` y los 2.342 comunicados de resultados de `datos/sec`, se cuenta en qué porcentaje de los anuncios hay, antes de las 9:30, un titular de Benzinga con la estimación ("beats/misses ... estimate"). Si es bajo, la idea 1 tiene que leer el comunicado solo frente a la guía anterior, o entrar más tarde.
4. **Cash drag:** de acuerdo. Mi respuesta es que el capital fuera de temporada trabaja en la idea 2 (si pasa) y en la extensión de catalizadores (abajo).

**Lista final, ordenada:**

| # | Idea | Primer paso | Cuándo hay evidencia | Qué la descarta |
| --- | --- | --- | --- | --- |
| 1 | **Sorpresa de resultados leída por LLM** (compartida con Gemini) | Medir la disponibilidad del consenso antes de las 9:30 con las noticias del repo; después, el lector en vivo para todo el S&P 500 antes de la temporada de enero de 2027 | Señal: 2 temporadas (~6 meses). Ganancia: 4 temporadas | Correlación de rangos no positiva con t ≥ 1,65 o no mejor que la base de reacción de precio; neta ≤ 0 al año |
| 2 | **Prima nocturna en ETF con subastas** | Regla fija: comprar al cierre y vender en la apertura en SPY y QQQ, 2016–2026, con el costo de subasta medido en las velas del cierre y la apertura | Días (datos ya en el repo) | Sharpe de la noche no mayor que el de comprar y mantener, o neta ≤ 0 en 2023–2026 |
| 3 | **Catalizadores fuera de horario** (idea 3 de Gemini, como extensión de la 1) | Mismo lector y misma ejecución; tipos de evento fijados antes: analista, fusión, producto | 6 meses en vivo | Neta ≤ 0 con t < 1,65; no gana sola fuera de las temporadas |
| 4 | **Spreads de crédito de puts en SPY** (reserva, sin IA) | Verificar costos de opciones en Alpaca; probar en papel | 6 a 12 meses en papel | Crédito neto de costos no mayor que la pérdida esperada en los meses malos |

**Descarto** la reversión de sobreventa (idea 2 de Gemini) por lo dicho en la ronda 2: no se puede ejecutar con el plan gratuito al cierre, su regla de precio es pública desde 2009 y el filtro LLM no se puede probar en el histórico.

## Ronda 3 — Gemini (defensa y lista final, escrita sin ver la ronda 3 de Claude)

### Crítica a Claude: el espejismo del "se prueba hoy" y el abandono de la tesis

El punto más débil de Claude en la ronda 2 es descalificar la evaluación en vivo por tardar meses y refugiarse en que la prima nocturna "se prueba hoy con datos del repo".

Claude confunde facilidad de cálculo con ventaja económica. Medir retornos nocturnos en una tarde sobre `datos/minuto` repite el vicio de la Fase 2: minería sobre velas sin ventaja informativa ni IA. La prima de Lou y otros (2019) está arbitrada; el ETF comercial que intentó capturarla (*NightShares 500 / NIGHT*) liquidó en 2023 por retornos negativos tras fricciones de subasta. Además, criticar que la IA exige prueba en vivo ignora que el protocolo (sección 2) prohíbe el backtest en LLMs por contaminación previa. La prueba en vivo no es demora: es rigor metodológico frente al sobreajuste.

### Defensas y ajustes
1. **Idea 1 (PEAD con 8-K):** consenso del debate. Para evitar noticias periodísticas tardías, Haiku procesa directamente el anexo EX-99 del 8-K en `datos/sec/`.
2. **Idea 3 (catalizadores fuera de hora):** defiendo que **no se superpone** con la idea 1: PEAD opera 4 semanas al año; esta cubre los otros 330 días en fusiones, alianzas y contratos (`noticias_vivo.py`), combatiendo el *cash drag*. Acepto el respaldo de Chan (2003) y Womack (1996) propuesto por Claude, y corrijo el descarte: ganancia neta ≤ 0 bps con remuestreo por bloques (sección 5), suprimiendo la tasa de acierto.
3. **Idea 2 (reversión diaria filtrada por LLM):** para sortear los 15 min de retraso de Alpaca, la señal se calcula con velas diarias a las 16:00 (gratuitas y completas); Haiku audita la caída fuera de sesión y se entra en MOO al día siguiente. Pasa a tercer lugar por ser accesoria.

### Lista final ordenada de Gemini

| Orden | Idea | Primer paso | Cuándo hay evidencia | Qué la descarta |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **PEAD cualitativo 8-K (LLM)** | Conectar `descargar_sec.py` con `lector_noticias.py` para ítems 2.02. | 2 temporadas en vivo (~50 ops). | Ganancia neta ≤ 0 bps o IC no positivo (t < 1,65). |
| **2** | **Catalizadores fuera de hora (Chan, 2003)** | Filtrar en `noticias_vivo.py` eventos mayores de 16:00 a 09:30. | 4–6 meses en vivo (~100 ops). | Ganancia neta ≤ 0 bps con remuestreo por bloques. |
| **3** | **Reversión diaria con filtro LLM (MOO)** | Evaluar RSI(2) a las 16:00 y auditar caídas con Haiku. | Simulación de precio + 3 meses sombra. | Ganancia neta ≤ 0 bps o caída máxima > SPY. |