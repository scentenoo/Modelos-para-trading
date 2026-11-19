# Debate: ventajas, desventajas, viabilidad y alineación de las ideas elegidas

## Tema

Pedido de Samir (17 de noviembre de 2026): "Sobre estas últimas ideas que encontraron, quiero que busquen sus ventajas y desventajas, su viabilidad y qué tan alineadas están con el objetivo principal. Si llegan a surgir nuevas ideas, son bienvenidas, pero sus argumentos deben ser suficientes como para que el juez las considere. El juez tendrá en cuenta también los argumentos de las primeras ideas al momento de seleccionar la o las ideas."

**Las ideas a evaluar** (dictamen de `debate/2026-11-17-ideas-rentables.dictamen.md`):
1. Sorpresa de resultados leída por un LLM (8-K, S&P 500, subasta de apertura, 2 a 5 días).
2. Prima nocturna en SPY y QQQ (comprar al cierre, vender en la apertura).
3. Catalizadores fuera de horario (fusiones, analistas, productos), como extensión de la 1.
4. Spreads de crédito de puts en SPY (reserva).

**Objetivo principal** (documento, sección 1): "construir un sistema de corto plazo que gane dinero después de costos. Cada parte hace lo que mejor sabe hacer: la IA lee noticias y los modelos de árboles trabajan con los números". Restricciones de Samir: cuenta chica, desde Colombia, Alpaca, plan gratuito de datos.

**Formato:**
- **Ronda 1, a ciegas:** para cada idea, ventajas, desventajas, viabilidad (técnica, de capital y de tiempo hasta tener evidencia) y alineación con el objetivo (de 0 a 3, con justificación). Después, las ideas nuevas, si las hay.
- **Ronda 2, a ciegas:** crítica a la evaluación del otro.
- **Ronda 3, a ciegas:** posición final, con la idea o ideas recomendadas, en orden.
- **Juez:** decide considerando este debate y `debate/2026-11-17-ideas-rentables.md`.

## Ronda 1 — Claude (escrita a ciegas)

**Criterio de alineación (0 a 3):** 1 punto si gana después de costos de forma plausible; 1 si es de corto plazo; 1 si la IA hace lo que mejor sabe: leer noticias.

### Idea 1 · Sorpresa de resultados leída por LLM — alineación 3/3
**Ventajas**
- Es la única idea en la que la IA tiene una ventaja estructural: convierte texto en una sorpresa frente al consenso y frente a la guía, un dato que de otra forma es pago.
- Es barata de operar. Haiku cuesta ~0,025 centavos por noticia (documento, línea 141); 500 acciones con varias noticias por anuncio son pocos dólares por temporada.
- Alpaca acepta órdenes para la subasta de apertura y la de cierre, así que no hay que cruzar el spread del pre-mercado (24,6 bps, `barrera_costos.md`).

**Desventajas**
- **El universo actual es de 53 símbolos** (dictamen previo, `descargar_datos.py:66`). Hay que ampliar noticias y 8-K al S&P 500. Velas de minuto no hacen falta: con velas diarias alcanza.
- **No se puede probar en el histórico** por la regla del pasado: la ganancia se sabe en vivo.
- **Cuesta repetirse:** en la prueba del documento, todos los campos coinciden en dos lecturas de la misma noticia solo el 64% de las veces (línea 141). Hay ruido en la propia señal.
- **Compite con fondos que ya leen texto por máquina.** El supuesto de 50 bps por operación no tiene respaldo (dictamen previo).

**Viabilidad:** técnica alta (lo más difícil, el lector, ya existe). Capital: bajo. Tiempo hasta la evidencia: 6 meses para la señal y 12 para la ganancia. Es la desventaja más grande.

### Idea 2 · Prima nocturna en ETF — alineación 1/3
**Ventajas:** se prueba en horas con datos que ya están; regla sin parámetros; costo de ejecución mínimo en SPY.
**Desventajas**
- **No usa IA** ni árboles: no responde a la tesis del proyecto.
- **Evidencia reciente en contra:** NSPY perdió 6,9% contra +22% del S&P 500 antes de cerrar (dictamen previo).
- **Compite por el capital con la idea 1:** si el capital duerme en SPY cada noche, no está libre para las compras en la apertura de la idea 1. O se divide la cuenta chica, o una de las dos queda fuera.
- **Toca la muestra final** (2025–2026). Solo es válido con la regla escrita antes.
- **En el mejor caso iguala el retorno del índice con menos tiempo expuesto.** Para una cuenta chica, el dinero absoluto que agrega es poco.

**Viabilidad:** técnica muy alta, tiempo casi nulo. **Valor:** como prueba de descarte rápida, no como estrategia central.

### Idea 3 · Catalizadores fuera de horario — alineación 3/3, pero más débil que la 1
**Ventajas:** mismo lector, misma ejecución, costo marginal casi cero; usa el capital fuera de las temporadas.
**Desventajas**
- **La evidencia citada no la respalda en grandes ni a pocos días** (Chan 2003: mensual y acciones chicas; dictamen previo).
- **Comparte el riesgo de la idea 1:** si la apertura ya descuenta la noticia, las dos fallan juntas.
- **Clases de eventos heterogéneas** (fusión, analista, producto): cada tipo es una hipótesis y suma comparaciones.

**Viabilidad:** alta si se hace la 1; sin ella no se justifica.

### Idea 4 · Spreads de crédito de puts — alineación 1/3
**Ventajas:** prima de riesgo documentada; riesgo máximo acotado; Alpaca no cobra comisión por contrato (dictamen previo).
**Desventajas:** no usa IA; el respaldo citado (índice PUT de Cboe) es otra estrategia; el put comprado es caro por el sesgo de volatilidad; datos de opciones pagos; acceso desde Colombia sin confirmar.
**Viabilidad:** baja hoy.

### Idea nueva · Unificar la 1 y la 3 en un solo "sistema de eventos" con una sola prueba
**Qué:** en vez de dos estrategias con criterios separados, una sola regla: el LLM puntúa cada noticia o 8-K relevante del S&P 500 publicado fuera de sesión (resultados o no), y se compra el decil superior de la puntuación en la apertura. La prueba es una sola correlación de rangos entre puntuación y retorno, sobre todos los eventos.
**Por qué es mejor que tenerlas separadas:**
1. **Más potencia:** se suman los ~2.000 anuncios de resultados y los eventos fuera de temporada en una sola prueba. El veredicto llega antes que con dos pruebas chicas.
2. **Menos comparaciones:** una hipótesis en vez de dos o más (una por tipo de evento). Es la lección de la Fase 2, donde 14 variantes subieron el t exigido a 2,69.
3. **Resuelve el *cash drag*** sin agregar una estrategia distinta.
4. **El tipo de evento queda como variable** que el LLM ya entrega (`tipo_evento`, sección 2.9), no como filtro elegido después.

**Qué la descartaría:** lo mismo que la idea 1. Correlación de rangos no positiva con t ≥ 1,65 sobre los eventos de 2 temporadas, o no mejor que la base de reacción de precio en los mismos eventos.

### Recomendación preliminar
1. Sistema de eventos (1 + 3 unificadas), como núcleo.
2. Prima nocturna, solo como prueba rápida de una tarde con la regla escrita antes; si no gana en Sharpe, se cierra.
3. Puts, archivada.

## Ronda 1 — Gemini (escrita a ciegas)

### Crítica a la postura final de Claude: el cuello de botella muestral y la inviabilidad de opciones

El punto más débil de Claude (`debate/2026-11-17-ideas-rentables.md`) es asumir que la infraestructura ya cubre el S&P 500 para generar "~200 operaciones al año en 2 temporadas". Como advirtió el juez (`debate/2026-11-17-ideas-rentables.dictamen.md`), `descargar_datos.py:66`, `descargar_sec.py:212` y `noticias_vivo.py:167` solo cubren 53 símbolos (50 acciones). En 50 acciones hay apenas ~200 anuncios anuales en total: el decil superior daría escasas ~20 operaciones al año. Prometer significancia estadística en 6 meses sin antes programar la descarga de 500 acciones es inviable. Asimismo, insistir en opciones (idea 4) ignora que Alpaca no tiene confirmada la apertura de cuentas de opciones para residentes en Colombia y que el *volatility skew* destruye el crédito neto al comprar cobertura fuera del dinero.

### Evaluación sistemática de las 4 ideas

#### 1. Sorpresa de resultados con LLM (8-K, 2–5 días, MOO)
- **Ventajas:** aprovecha la infraestructura existente (`lector_noticias.py` con Haiku 5.5 a 2,1 s; `descargar_sec.py`). Anomalía PEAD sólida en la literatura (Bernard y Thomas, 1989).
- **Desventajas:** con 50 acciones rinde apenas ~20 ops/año. Exige ampliar la descarga a 500 acciones antes de enero de 2027. La subasta de apertura (MOO) en acciones sueltas tiene un costo no medido (`resultados/barrera_costos.md:12` solo midió spread continuo de 2,7 bps).
- **Viabilidad:** técnica media (ampliar la descarga de la SEC a 500 símbolos). Capital: alta (swing sin regla PDT en cuenta chica). Tiempo a evidencia: lenta (2 a 4 temporadas en vivo, 6–12 meses).
- **Alineación con el objetivo:** **3/3**. Cumple exactamente la premisa del proyecto (sección 1): IA extrayendo alfa de texto que los árboles no pueden leer, sin pagar datos en tiempo real.

#### 2. Prima nocturna en SPY y QQQ (cierre a apertura)
- **Ventajas:** prueba inmediata con velas existentes (`datos/minuto`, `descargar_datos.py:68`). Regla fija sin parámetros. Spread mínimo en SPY (0,3 bps, `resultados/barrera_costos.md:12`). Cero *cash drag*.
- **Desventajas:** cero IA. Fricción de 504 órdenes anuales (tasas regulatorias y deslizamiento en la subasta). Fondos comerciales (*NightShares*) cerraron en 2023 por mal desempeño. Probar en 2025–2026 sin congelar la regla antes violaría la regla de la muestra final.
- **Viabilidad:** técnica inmediata. Capital: alta. Tiempo a evidencia: inmediata en histórico; 3 meses en sombra.
- **Alineación con el objetivo:** **1/3**. Aporta retorno pasivo, pero abdica de la IA y del análisis fundamental.

#### 3. Catalizadores fuera de horario (fusiones, analistas, productos)
- **Ventajas:** combate el *cash drag* de la idea 1 entre temporadas (cubre los 330 días restantes con `noticias_vivo.py`). Respaldada por Chan (2003) y Womack (1996). Costo marginal cero: reutiliza el clasificador LLM.
- **Desventajas:** mayor dispersión y ruido que en los 8-K formales. Comparte el riesgo de ser arbitrada en la apertura.
- **Viabilidad:** técnica alta (`noticias_vivo.py` ya corre 24/7 en Debian). Capital: alta. Tiempo a evidencia: media (3 a 6 meses en vivo por mayor frecuencia).
- **Alineación con el objetivo:** **3/3**. Plena: IA leyendo información no estructurada fuera de sesión.

#### 4. Spreads de crédito de puts en SPY (reserva)
- **Ventajas:** prima de riesgo estructural documentada (volatilidad implícita mayor que la realizada).
- **Desventajas:** bloqueo regulatorio para Colombia en Alpaca. Sin datos en el repo. Cero IA. El *skew* encarece el put comprado de cobertura.
- **Viabilidad:** técnica nula (sin datos OPRA). Capital: baja (inmoviliza colateral escaso). Tiempo a evidencia: lenta (más de 6 meses en papel).
- **Alineación con el objetivo:** **0/3**. Sin IA, derivados excluidos por diseño (sección 1) e inviable en la práctica.

### Idea nueva: sistema híbrido PEAD (LLM para la selección y árboles para la salida)
- **Propuesta:** reintegrar los árboles de decisión a la idea 1 para cumplir la promesa fundacional: *"la IA lee noticias y los modelos de árboles trabajan con los números"* (sección 1). Haiku 5.5 selecciona el decil de sorpresa en el 8-K; un modelo LightGBM evalúa el volumen relativo de la subasta de apertura y la volatilidad inicial para calibrar la salida dinámica (entre 2 y 5 días) o abortar trampas de apertura (*open traps*).
- **Fundamento y viabilidad:** en `resultados/referencia.md:37`, el PEAD con salida fija a 60 min dio −3,86 bps; la salida dinámica con árboles protege la ganancia frente al decaimiento de volatilidad. Viabilidad técnica alta (`variables.py` y `modelo_final.py` ya tienen la base).
- **Alineación:** **3/3**.

## Ronda 2 — Claude (crítica a la ronda 1 de Gemini, escrita sin ver su ronda 2)

**Coincidimos en lo central:** las ideas 1 y 3 tienen la alineación máxima, la 2 tiene 1/3 y la 4 está en el fondo. También concedo la crítica inicial: el S&P 500 no está descargado, y cualquier plazo depende de ampliar primero el universo.

**Sobre la idea nueva de Gemini (árboles para la salida): no la sostendría, por cuatro razones.**
1. **El fundamento no se sigue de la evidencia.** El −3,86 bps de `referencia.md:37` no muestra que una salida *fija* sea el problema: la regla salía a los 60 minutos, cuando la deriva dura días. El arreglo es alargar el horizonte, que ya está en la idea 1. No muestra que haga falta una salida *dinámica*.
2. **Choca con la regla PDT.** "Abortar trampas de apertura" significa vender el mismo día de la compra, y eso es una operación dentro del día. Con una cuenta chica, son las operaciones que la regla limita. La ventaja de la idea 1 era justamente evitarlas.
3. **El plan gratuito no lo permite.** El volumen de la subasta y la volatilidad inicial se conocen a las 9:30 y llegan con 15 minutos de retraso (documento, línea 489). La decisión de salida llegaría tarde, en el momento más caro del día (`costo_bordes.md`: la apertura cuesta 1,11 veces el horario normal).
4. **Repite la lección de B.** Los árboles sobre precio y volumen no mostraron ventaja fuera de muestra (`muestra_final.md`: selección −0,96, t −0,44), y cada regla de salida nueva es una variante más. Fijar 3 días de antemano no tiene parámetros que sobreajustar.

**Le reconozco una cosa:** es la única propuesta que devuelve los árboles a la tesis ("la IA lee noticias y los árboles trabajan con los números"). Una forma más sana de hacerlo es la que ya tiene el proyecto: **la base de reacción de precio puede ser un modelo de árboles entrenado en el histórico** (no usa LLM, así que se puede probar con 2016–2024 en las 500 acciones) y la IA tiene que sumarle algo. Es el diseño D contra B de la Fase 3, trasladado a eventos de varios días.

**Afirmaciones de Gemini que el dictamen previo ya había corregido y que vuelven a aparecer:**
- **"Bloqueo regulatorio para Colombia" en opciones:** el juez la marcó como *no verificada*, no como bloqueo.
- **"Derivados excluidos por diseño":** el juez la marcó como *exagerada* ("por ahora"). Coincido en el 0 o el 1 de alineación, pero por la falta de IA, no por una prohibición.
- **Chan (2003) y Womack (1996) como respaldo de la idea 3:** el juez señaló que Chan es mensual y de acciones chicas. Esa idea sigue sin respaldo directo en grandes a pocos días.
- **La idea 2 como "cero cash drag":** es cierto para la idea 2 sola, pero compite por el mismo capital con la idea 1 (comprar en la apertura exige no tener todo el capital en SPY). Gemini no lo trata.

**Lo que falta en las dos evaluaciones:** ninguno dijo *cuánto dinero* es esto para una cuenta chica. Con 10.000 dólares, un 5% anual por encima del efectivo son 500 dólares al año, antes de impuestos. La viabilidad depende también de que el tiempo de desarrollo valga eso. Es un argumento a favor de unificar 1 y 3 (un solo sistema, una sola prueba) y en contra de abrir más frentes.

## Ronda 2 — Gemini (crítica a la ronda 1 de Claude, escrita sin ver su ronda 2)

### Crítica al punto más débil de Claude: la falacia de agregación y el abandono de los árboles

El punto más débil de Claude es unificar resultados (8-K) y catalizadores de prensa en un "sistema de eventos". Venderlo como ganancia de potencia estadística es un grave error econométrico:

1. **Heterogeneidad destructiva:** un 8-K (ítem 2.02) reporta sorpresas contables cuantitativas con deriva documentada (Bernard y Thomas, 1989). En contraste, las noticias de prensa fuera de sesión no muestran deriva a corto plazo en megacaps (Chan, 2003, citado en `debate/2026-11-17-ideas-rentables.dictamen.md`, solo halló persistencia mensual en acciones ilíquidas; Tetlock, 2007, observó reversión rápida). Si Haiku coincide en todos los campos solo el 64% de las veces (documento principal, línea 141), mezclar relaciones públicas corporativas con resultados contables contamina el decil superior. Si las noticias tienen alfa nulo o negativo, agregarlas en una sola correlación de Spearman no suma potencia: **diluye el alfa del PEAD y precipita el descarte espurio de ambas (t < 1,65)**.
2. **Abandono de la tesis central:** Claude puntúa 3/3 prescindiendo por completo de los árboles. El objetivo principal (documento principal, línea 7) exige que *"la IA lee noticias y los modelos de árboles trabajan con los números"*; la hipótesis principal siempre fue D (IA + árboles, línea 44). Dejar a la IA sola decidiendo entradas a ciegas repite el error del competidor C y olvida que la selección pura intradía cayó a t −0,44 (`resultados/muestra_final.md:60`). Los árboles son necesarios para gestionar la salida dinámica y filtrar el desbalance de apertura.

### Objeciones a la viabilidad y a la prima nocturna
- **Subasta de apertura (MOO) sin medir:** Claude asume que MOO evita el spread de 24,6 bps (`resultados/barrera_costos.md:11`), pero ignora la advertencia expresa del juez (dictamen previo): *nadie midió el costo de la subasta a las 9:30 en acciones sueltas*. En noticias de alto impacto, el desbalance de órdenes (*order imbalance*) puede devorar el margen.
- **Inconsistencia en la prima nocturna:** Claude le otorga 1/3 de alineación y advierte que compite por capital con la idea 1, pero la coloca segunda en su recomendación. Si canibaliza el capital escaso de Samir, debe ser solo un test rápido de descarte en una tarde, no una estrategia troncal.

## Ronda 3 — Claude (posición final, escrita sin ver la ronda 3 de Gemini)

**Concedo las dos críticas principales de Gemini y cambio mi propuesta.**

1. **Agregación:** tiene razón. Si las noticias que no son de resultados tienen alfa nulo, mezclarlas en una sola correlación diluye la señal de los resultados y puede hacer fallar a las dos. Retiro la prueba única. Queda así: **una sola infraestructura, dos pruebas escritas antes**. La principal, solo con los anuncios de resultados. La secundaria, con los catalizadores, con su propio criterio y corrección por dos pruebas (t exigido 1,96 en vez de 1,65). El costo de desarrollo sigue siendo uno solo.
2. **Los árboles:** tiene razón en que mi evaluación los dejaba fuera de la tesis. Pero no para la salida, por lo que dije en la ronda 2 (regla PDT, datos con 15 minutos de retraso y una variante más), sino **donde el proyecto ya los quería: como competidor B en el mismo terreno**. Cabe notar que en el debate de la idea 4 Gemini rechazó meter variables de precio en la base "para preservar la parsimonia"; ahora pide árboles. Esta propuesta concilia las dos cosas, porque los árboles van en la base y no en un filtro elegido después:
   - **B de eventos:** LightGBM entrenado con 2016–2024 en los anuncios de resultados del S&P 500, solo con números: reacción del precio el día del anuncio, volumen relativo, tamaño, volatilidad e impulso previo. Usa velas **diarias**, que se descargan rápido, y **no tiene LLM, así que se puede probar en el histórico** sin violar la regla del pasado. Es la primera evidencia que puede llegar en semanas y no en meses.
   - **D de eventos:** las mismas variables más las del LLM (sorpresa frente al consenso y la guía, tono, novedad), en vivo desde enero de 2027.
   - **La prueba es D contra B**, exactamente la hipótesis H1 del documento (sección 1), en un horizonte donde el costo ya no se come la señal.
3. **Subasta de apertura sin medir:** de acuerdo. Hay que medirla antes de comprometer dinero: en modo sombra, comparar el precio de la subasta con el punto medio de las cotizaciones de los primeros minutos (el plan gratuito da cotizaciones de IEX en vivo). Hasta tenerlo, se usa el doble del costo de la época como supuesto.
4. **Prima nocturna:** coincidimos: es solo una prueba de descarte de una tarde. La dejo tercera.

**Lista final, en orden**

| # | Idea | Alineación | Primer paso | Primera evidencia | Qué la descarta |
| --- | --- | --- | --- | --- | --- |
| 1 | **Eventos de resultados: B (árboles, histórico) contra D (árboles + LLM, en vivo)** | 3/3: es H1 tal cual | Ampliar velas diarias, 8-K y fechas de resultados al S&P 500 con su composición histórica; entrenar B en 2016–2024 | B: semanas, en el histórico. D contra B: 2 temporadas | B: neta ≤ 0 tras costos o t por bloques < 2 en 2016–2024. D: correlación de rangos no mayor que la de B con t ≥ 1,65 |
| 2 | **Catalizadores fuera de horario**, como prueba secundaria con la misma infraestructura | 3/3 | Fijar de antemano los tipos de evento y el criterio | 6 meses en vivo | Neta ≤ 0 o t < 1,96 |
| 3 | **Prima nocturna en SPY y QQQ**, como prueba de descarte | 1/3 | Regla y criterios escritos antes; una tarde de cálculo | Inmediata | Sharpe no mayor que comprar y mantener |
| — | Spreads de crédito de puts | 0–1/3 | Archivada | — | — |
| — | Árboles para la salida (idea nueva de Gemini) | — | Descartada: regla PDT, datos con retraso, variante extra | — | — |

**Por qué este orden maximiza la rentabilidad esperada:** la idea 1 es la única con una ventaja informativa plausible *y* con una parte que se puede probar ya (B de eventos). Si B de eventos no gana nada en el histórico, se sabe en semanas que el terreno de los resultados en grandes está agotado, y se evita gastar 6 meses en vivo. Si gana, hay una estrategia operable desde enero, aunque la IA no sume nada, y la IA se mide contra ella.

## Ronda 3 — Gemini (posición final, escrita sin ver la ronda 3 de Claude)

### Crítica a Claude: contradicción en los árboles y falacia del volumen de capital

El punto más débil de Claude en la ronda 2 es una contradicción metodológica: descalifica el uso de árboles por el fracaso fuera de muestra de B (`resultados/muestra_final.md:60`, selección −0,96, t −0,44), pero en el párrafo siguiente propone resucitar a B entrenando un modelo de árboles sobre 500 acciones como base histórica contra la cual medir a D. Si los árboles sobre precio carecen de alfa de selección frente a los costos, utilizarlos de referencia en 500 acciones (donde ni siquiera tenemos velas de 1 minuto descargadas, `descargar_datos.py:66`) solo añade sobreajuste y complejidad innecesaria.

Asimismo, Claude argumenta que "500 dólares al año es poco" para forzar la agregación de 8-K con noticias de prensa (ideas 1 y 3). Es un error conceptual: cuando una cuenta chica tiene poco capital, forzar eventos ruidosos y sin deriva documentada en megacaps no crea rentabilidad; solo infla la rotación y destruye la cuenta en comisiones y deslizamiento. Tampoco resuelve la canibalización: si el capital duerme en SPY cada noche (idea 2), no hay efectivo disponible para las órdenes MOO de la apertura de la idea 1 en T+1 sin incurrir en apalancamiento, expresamente restringido para Samir (documento principal, línea 13).

### Concesiones y defensa metodológica
1. **PDT y datos retrasados:** concedo la objeción sobre abortar intradía: con la latencia de 15 minutos del plan gratuito (documento principal, línea 489) y las limitaciones PDT de una cuenta chica, una salida dinámica intradía es inviable. La corrijo: **la salida debe ser fija a 3 días en la subasta de cierre (MOC)**, sin parámetros que sobreajustar y sin tocar el intradía.
2. **Derivados:** acepto el dictamen del juez; la exclusión de opciones (documento principal, línea 13) fue temporal ("por ahora"). Sin embargo, con 0/3 de alineación, sin datos OPRA en el repo y sin IA, la idea 4 queda archivada.

### Posición final recomendada

| Idea | Alineación | Primer paso | Primera evidencia | Qué la descarta |
| :--- | :---: | :--- | :--- | :--- |
| **1. PEAD con LLM en 8-K** (swing 3 días, MOO a MOC) | **3/3** | Ampliar `descargar_sec.py:212` y `noticias_vivo.py:167` a 500 acciones del S&P 500. | Medir en el histórico qué fracción de anuncios tiene consenso antes de las 9:30; correlación de rangos en vivo en el primer trimestre de 2027. | Correlación no positiva con t < 1,65 tras 2 temporadas, o no superar a la reacción de precio. |
| **2. Catalizadores fuera de sesión** (fase 2 contingente) | **2/3** | Clasificar comunicados con Haiku fuera de temporada solo si la idea 1 valida el canal MOO. | Retorno a 3 días superior al spread de apertura medido en acciones individuales. | Dilución del Sharpe de la cartera o reversión en la apertura (Tetlock, 2007). |
| **3. Prima nocturna en ETF** (test de descarte) | **1/3** | Congelar la regla fija y correrla en `datos/minuto` (`descargar_datos.py:68`) en una tarde. | Sharpe neto superior a comprar y mantener en 2016–2024. | Sharpe inferior al índice o retorno neto ≤ 0. |
| **4. Spreads de puts en SPY** | **0/3** | Archivada. | N/A | Falta de datos en el repo, sin IA y bloqueo de colateral escaso. |