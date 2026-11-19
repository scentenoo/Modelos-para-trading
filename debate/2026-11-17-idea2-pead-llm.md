# Debate de viabilidad · Idea 2: sorpresa de resultados leída por un LLM

## Tema

Samir pide profundizar en cada idea del debate anterior (`debate/2026-11-17-como-hacerlo-rentable.md`, sección Síntesis), con dos rondas por idea sobre **descartarla o continuarla**, sobre todo por **viabilidad frente al objetivo de rentabilidad**.

**Vara común para las cuatro ideas:** es "rentable" si, fuera de muestra y después de costos, (a) le gana a comprar y mantener SPY en retorno ajustado por riesgo, o (b) da un retorno parecido con una caída máxima claramente menor; y si se puede operar con una cuenta chica desde Colombia (Alpaca, solo compras, plan gratuito de datos, sin la regla PDT). También cuenta el costo de oportunidad: si existe un ETF barato que hace lo mismo, construirlo no agrega rentabilidad.

**La idea:** un LLM (Haiku 5.5, ya en `lector_noticias.py`) lee las noticias y el comunicado 8-K de resultados de las ~500 del S&P 500, extrae la sorpresa frente al consenso y a la guía anterior, y se compra el decil más positivo en la apertura siguiente, manteniendo de 2 a 5 días. Solo compras. Debe ganarle a la idea 1 en los mismos eventos.

## Ronda 1 — Claude

**Mi postura: continuar, pero cambiando dónde se aplica, porque así como está apunta al lugar más competido.**

Contra su rentabilidad tal como está:
1. **La sorpresa de resultados de las grandes ya la leen máquinas.** Los fondos procesan texto de noticias desde hace más de una década (proveedores como RavenPack) y hoy también con LLM. El titular "supera la estimación por X centavos" se descuenta en minutos, antes de nuestra entrada en la apertura siguiente.
2. **La evidencia académica con LLM apunta a otro lado.** El trabajo más citado (López-Lira y Tang, 2023) encuentra que el tono de los titulares leído por ChatGPT predice el retorno del día siguiente, pero sobre todo en las acciones chicas, y que el efecto se achica a medida que más gente usa estas herramientas.
3. **La prueba en vivo es lenta:** por la regla del pasado (sección 2), lo limpio empieza ahora. Con resultados concentrados en 4 temporadas, el primer veredicto serio necesita 2 a 4 temporadas (6 a 12 meses).

**Dónde sí veo ventaja para un LLM: información lenta, no rápida.** Documentos largos que casi nadie lee completos: los cambios de texto entre un 10-K o 10-Q y el anterior (riesgos nuevos, cambios en la discusión de la gerencia). Hay evidencia de que esos cambios predicen retornos durante *meses* ("Lazy Prices", Cohen, Malloy y Nguyen, 2020), porque el mercado tarda en incorporarlos. Encaja con solo compras (evitar o vender las que empeoran), con horizonte largo (costo despreciable) y con lo que un LLM hace mejor: comparar dos textos largos. Además, horizonte de meses reduce la desventaja de la latencia y del plan gratuito.

**Pregunta para Gemini:** ¿reemplazarías la sorpresa rápida de los 8-K por los cambios lentos de los 10-K/10-Q como núcleo de la IA? ¿Qué problema ves en esa versión?

## Ronda 1 — Gemini

### Crítica a Claude: la fuga a los 10-K y la trampa del horizonte largo

El punto más débil de Claude es proponer **reemplazar 8-K por 10-K/10-Q**, huyendo a documentos largos sin advertir tres contradicciones fatales con el repo y las restricciones del proyecto:

1. **La anomalía de Cohen ("Lazy Prices") no sirve para "solo compras":** En Cohen, Malloy y Nguyen (2020), prácticamente todo el alfa anormal proviene de la **pata corta** (vender las empresas que modifican sustancialmente su sección de factores de riesgo o MD&A, que caen ~100 bps/mes). Las firmas que no cambian su texto no superan al mercado de forma significativa. En una cuenta chica desde Colombia sin ventas en corto (sección 1), limitarse a excluir o comprar las que no cambian no le gana a SPY y pierde por costo de oportunidad contra un ETF pasivo.
2. **Destruye la potencia estadística:** Claude critica que 8-K requiere 6–12 meses para validarse, pero evaluar 10-K/10-Q con retornos a meses exige observaciones trimestrales fuertemente solapadas: requeriría de 3 a 5 **años** de datos fuera de muestra para acumular grados de libertad independientes y lograr significancia estadística ($t \ge 2$), liquidando la viabilidad del proyecto.
3. **Inviabilidad técnica y de presupuesto:** En [descargar_sec.py](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/descargar_sec.py#L10-L60) el repositorio descarga exclusivamente 8-K (`FORMULARIOS = {"8-K", "8-K/A"}`); no existe código para 10-K ni 10-Q. Además, un 10-K supera las 50.000 palabras; comparar dos informes completos por empresa pulveriza el presupuesto de API de [lector_noticias.py](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/lector_noticias.py#L12), diseñado para fragmentos de 2.000 caracteres a ~$0,025 por llamada con Haiku 5.5.

### Mi postura: Continuar con 8-K, pero a horizonte Swing (2 a 5 días)

No reemplazo los 8-K. La razón por la que PEAD fracasó en el repo no es que la sorpresa esté arbitrada, sino que se midió mal: en [referencia.py](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/referencia.py#L13-L16) y [referencia.md](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/resultados/referencia.md), la "deriva tras resultados" se cerró a 30 y 60 minutos intradía (dando −2,21 y −3,86 bps netos). El PEAD académico dura días o semanas; cerrarlo en 60 minutos es pagar el spread en el pico de volatilidad sin darle tiempo a desplegarse.

El LLM no busca ganarle en milisegundos a las máquinas en el número de EPS. Su ventaja sobre 8-K (en particular los comunicados de prensa EX-99 que `descargar_sec.py` ya extrae) es evaluar la información cualitativa: credibilidad de la guía (*guidance*), tono de la gerencia y matices que los algoritmos de baja latencia no descuentan en la apertura. Con compras en la apertura (MOO) post-evento y salida a 2–5 días, el spread es irrelevante frente al movimiento swing y se esquiva el PDT.

**Pregunta para Claude:** Dado que la literatura de *Lazy Prices* depende de ventas en corto que no podemos ejecutar, ¿cómo pretendés generar alfa positivo neto frente a SPY solo comprando acciones que "no cambian" sus 10-K?

## Ronda 2 — Claude

**Concedo los dos golpes principales:** si el alfa de "Lazy Prices" viene sobre todo de la pata vendida, solo compras deja poco, y con horizonte de meses la potencia estadística se va a años. Los 10-K quedan fuera del núcleo. (Sobre el costo, una corrección: con precios de Haiku, comparar dos 10-K de 500 empresas al año son cientos de dólares, no un problema. Y hay algo peor para la idea: esa anomalía se mide con similitud de texto simple, sin LLM. Si no necesita IA, no responde la pregunta del proyecto.)

**Me quedo con tu versión: 8-K de resultados, 2 a 5 días.** Pero hay que hacer las cuentas de viabilidad antes de comprometerse, porque ahí está el riesgo real:

1. **Cuánto tiempo tarda en dar un veredicto.** ~2.000 anuncios al año en el S&P 500; si se compra el decil más positivo, son ~200 operaciones al año. El retorno a 3 días después de un anuncio tiene una desviación de unos 500 bps. Para detectar una ventaja de 50 bps con t = 2 hacen falta (2 × 500 / 50)² = 400 operaciones: **dos años en vivo**, más si los eventos de la misma semana se mueven juntos. Solución: además de la ganancia, una **prueba de señal** sobre los 2.000 eventos (correlación entre la puntuación del LLM y el retorno siguiente, como se decidió para D en la Fase 3). Con una correlación de 0,05 hacen falta ~1.600 eventos: unas 3 temporadas, **9 a 12 meses**.
2. **Cuánto gana si funciona.** 200 operaciones × 50 bps = 100 puntos porcentuales "operación por operación". Con 10 posiciones simultáneas de 3 días, eso es ~10% anual sobre el mercado *solo si el resto del tiempo el capital está en SPY*. Es una cifra atractiva y deja margen: aun con la mitad sigue valiendo la pena.
3. **Ejecución:** la apertura del día siguiente al anuncio es el momento más caro y volátil (`costo_bordes.md`: la apertura cuesta 1,11 veces el horario normal en las 36 megacaps, y más en las otras). Mejor entrar en la subasta de cierre del día de reacción (MOC): ya se vio la reacción y la orden la llena la subasta.

**Pregunta para Gemini, para cerrar:** ¿aceptás la prueba de señal como criterio temprano y la entrada al cierre del día de reacción? Dame tu veredicto final y el criterio de descarte exacto.

## Ronda 2 — Gemini

### Crítica a Claude: el error de ejecución MOC y el espejismo del ahorro de spread

El punto más débil de Claude es proponer **entrar en la subasta de cierre (MOC) del día de reacción**:

1. **Ahorro marginal vs. alfa sacrificado:** En [costo_bordes.md](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/resultados/costo_bordes.md#L9-L15), la apertura tiene una razón de 1,11 frente a 0,85 al cierre. Sobre un spread normal de 1,5 a 2 bps en megacaps, la diferencia es de apenas **~0,4 bps**. Retrasar la entrada hasta las 15:59 regala 6,5 horas de deriva post-apertura donde el mercado procesa la sorpresa cualitativa. Sacrificar decenas de bps de tendencia inicial por ahorrar 0,4 bps de fricción es un pésimo intercambio.
2. **Riesgo de comprar en el techo:** El 84% de los 8-K se publican fuera de horario (sección 2.1). En un resultado extraordinario, entrar a MOC tras un rally intradía del +4% o +6% expone a comprar el agotamiento intradiario o la reversión de corto plazo documentada en [referencia.py](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/referencia.py#L10-L16). La entrada rigurosa es la subasta de apertura (**MOO**, 9:30): cruza al precio oficial de equilibrio con máxima liquidez y esquiva los spreads anchos del pre-mercado (15–25 bps, sección 2.1).
3. **Falsa linealidad de capital:** Claude asume 10 posiciones simultáneas constantes, pero los resultados se concentran en ~4 semanas pico por trimestre. En días con 25 señales simultáneas en el decil superior, una cuenta chica sin margen sufre racionamiento severo de capital; ese agrupamiento diluye el retorno proyectado del 10%.

### Veredicto final: CONTINUAR

Acepto la prueba de señal como filtro temprano, pero **rechazo MOC**; la ejecución debe ser **MOO**.

**Veredicto:** **Continuar la Idea 2** (PEAD con LLM, S&P 500, 2 a 5 días, solo compras). Es el único camino donde la IA aporta una ventaja estructural insustituible (extraer sorpresa cualitativa de guías sin pagar suscripciones de consenso de miles de dólares) esquivando el PDT y el spread intradía.

### Criterio de descarte exacto

1. **Descarte temprano de señal (a 2 temporadas / ~6 meses en vivo, ~1.000 anuncios):**
   - Se calcula el Information Coefficient (correlación de Spearman) de la señal frente al retorno neto a 3 días, evaluado con remuestreo por bloques de temporada (sección 5).
   - **Se descarta si:** El IC medio del LLM no es estrictamente positivo con $t \ge 1,65$, o no supera al IC del PEAD numérico de [cifras](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/datos/sec/cifras) en los mismos eventos.
2. **Descarte definitivo de rentabilidad (a 4 temporadas / 1 año en vivo, ~200 operaciones):**
   - **Se descarta si:** Tras costos reales de apertura MOO, la estrategia no supera a comprar y mantener SPY en retorno ajustado por riesgo (Sharpe), o la ganancia media neta por operación es $\le 0$ bps con $t < 2$.

## Veredicto (Claude)

**CONTINUAR. Es la única idea que sigue viva como fuente de rentabilidad.**

**Desacuerdo de ejecución (MOO o MOC), resuelto separando dos preguntas:**
- **¿La IA es rentable?** La IA lee el 8-K de noche (la mayoría sale fuera de sesión) y puede entrar en la **subasta de apertura** del día de reacción. Es su ventaja natural; la base de precio no puede hacerlo, porque necesita ver el día. Esta es la prueba principal de ganancia, contra comprar y mantener SPY.
- **¿La IA aporta algo que el precio no dice?** Las dos entran al **cierre** del día de reacción y se comparan en los mismos eventos. Es la prueba de señal contra la base.

**Corrección:** el criterio de Gemini compara con "el PEAD numérico de `cifras`", pero en el hilo de la idea 1 se acordó que la base es la reacción de precio. Vale esa.

**Criterios de descarte, fijados antes de empezar:**
1. **Temprano (2 temporadas, ~1.000 anuncios):** se descarta si la correlación de rangos entre la puntuación del LLM y el retorno a 3 días no es positiva con t por bloques ≥ 1,65, o si no supera a la de la base en los mismos eventos.
2. **Definitivo (4 temporadas, ~1 año, ~200 operaciones):** se descarta si, con costos reales de la subasta de apertura, la ganancia neta por operación es ≤ 0 o el Sharpe no supera al de comprar y mantener SPY.

**Viabilidad:** si funciona con 50 bps por operación, ~200 operaciones al año dan del orden de 10% anual por encima del capital en efectivo (no es lineal: los anuncios se amontonan en 3 o 4 semanas por trimestre y el capital se raciona). El primer veredicto llega en 6 meses; el definitivo, en un año.

**Abierto para Samir:** si además se hace una prueba histórica con un modelo cuya fecha de corte sea anterior a 2025 (ver el debate anterior). No cambiaría estos criterios, porque solo la prueba en vivo cuenta.
