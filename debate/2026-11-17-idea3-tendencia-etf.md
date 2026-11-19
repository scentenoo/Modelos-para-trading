# Debate de viabilidad · Idea 3: seguimiento de tendencia en ETF

## Tema

Samir pide profundizar en cada idea del debate anterior (`debate/2026-11-17-como-hacerlo-rentable.md`, sección Síntesis), con dos rondas por idea sobre **descartarla o continuarla**, sobre todo por **viabilidad frente al objetivo de rentabilidad**.

**Vara común para las cuatro ideas:** es "rentable" si, fuera de muestra y después de costos, (a) le gana a comprar y mantener SPY en retorno ajustado por riesgo, o (b) da un retorno parecido con una caída máxima claramente menor; y si se puede operar con una cuenta chica desde Colombia (Alpaca, solo compras, plan gratuito de datos, sin la regla PDT). También cuenta el costo de oportunidad: si existe un ETF barato que hace lo mismo, construirlo no agrega rentabilidad.

**La idea:** estar comprado en cada ETF (SPY, QQQ, IWM y, si se agregan, bonos, oro y materias primas) solo cuando su precio de fin de mes supera la media de los últimos 10 meses; si no, en efectivo o letras del Tesoro. Regla fija de la literatura (Faber, 2007), sin optimizar.

## Ronda 1 — Claude

**Mi postura: continuar, pero como base de la cartera, no como proyecto de investigación ni como fuente de "alfa".**

Lo que hay que decir claro sobre su rentabilidad:
1. **No le gana a comprar y mantener en retorno.** En mercados alcistas largos (como 2016–2026) suele quedar algo por debajo: sale tarde y entra tarde. Lo que ofrece es la parte (b) de la vara: evitar las caídas grandes (2008, 2022). Su Sharpe histórico es algo mejor que el del mercado, sobre todo por la menor caída máxima.
2. **Pierde en mercados en V.** En marzo de 2020 sale después de la caída y vuelve a entrar después del rebote: paga las dos cosas. Con 10 años de datos locales hay muy pocas señales (unas pocas por ETF) para validar nada; la evidencia está en un siglo de literatura, no en `datos/`.
3. **Para Samir importa el impuesto.** Cada salida realiza ganancias; desde Colombia eso puede costar más que el spread. Hay que verificarlo con un contador antes de considerarla rentable.

Por qué continuarla igual:
- **Es casi gratis de operar:** de 1 a 4 cambios por ETF al año, sin cortos, sin PDT, con datos diarios gratis y órdenes en la subasta de cierre.
- **Reducir a la mitad la caída máxima es lo que permite seguir invertido** con una cuenta chica: una caída de 50% necesita duplicar para recuperarse.
- **Es la vara mínima:** cualquier sistema con IA tiene que ganarle a esto para justificar su complejidad.

**Pregunta para Gemini:** ¿la ves como "rentable" según la vara, o solo como gestión de riesgo? ¿Qué cambio de diseño, decidido antes de mirar datos, la haría más útil para Samir (más activos, mezcla con comprar y mantener, otra regla)?

## Ronda 1 — Gemini

### Crítica a Claude: la ilusión del "casi gratis" y el costo de oportunidad

El punto más débil de Claude es calificar esta estrategia como "casi gratis de operar" y proponer continuarla como base de cartera, subestimando dos fricciones que invalidan la vara de rentabilidad para Samir:

1. **La fricción tributaria en Colombia anula la menor caída máxima:** Claude despacha el impuesto como una nota al pie, pero es el factor determinante. En Colombia (Estatuto Tributario), liquidar activos en el exterior para ir a efectivo realiza ganancias gravables (renta ordinaria de hasta 39% o ganancia ocasional del 15% si se mantuvieron más de 2 años). Un *comprar y mantener* difiere impuestos indefinidamente; salir ante cruces de 10 meses y volver a entrar tras reversiones en V (como marzo de 2020, documentado en la sección 1 del proyecto y `calibracion.py`) paga peaje fiscal en cada ciclo. Lo que se gana reduciendo el drawdown se pierde en la declaración de renta.
2. **Costo de oportunidad ignorado:** La vara común prohíbe construir lo que ya existe como ETF barato. Productos comerciales como PTLC (*Pacer Trendpilot US Large Cap*, TER ~0,60%) ejecutan seguimiento de tendencia sistemático sobre el S&P 500 dentro del fondo, difiriendo impuestos de forma automática sin que Samir deba vender en Alpaca. Operarlo a mano no agrega alfa y añade ineficiencia impositiva.
3. **Mutilación del diseño original:** Faber (2007) diseñó la regla de 10 meses para una cartera multi-activo global (acciones, bonos, oro, materias primas). Restringirla a SPY, QQQ e IWM (los únicos ETFs en `datos/minuto`, sección 1.1) concentra el riesgo en renta variable estadounidense: en regímenes de alta volatilidad (`segmentos.py`), los tres colapsan en bloque hacia efectivo, perdiendo el carry de bonos o el refugio del oro.

### Veredicto: Descartar del proyecto

Bajo la vara común, **no es una estrategia rentable sino un protocolo defensivo de reducción de varianza**. No genera alfa y, neta de impuestos colombianos, no superará el retorno ajustado por riesgo de comprar y mantener SPY.

Si Samir desea implementarla para su patrimonio personal fuera del repo, el diseño debe corregirse antes de mirar datos:
- **Dual Momentum multi-activo (Antonacci, 2014):** Medir momentum relativo entre clases de activos y filtrar por momentum absoluto contra letras del Tesoro (BIL/SGOV), en lugar de 3 medias aisladas en acciones.
- **Banda de histéresis:** Exigir que el precio supere la media en un 1% o durante dos cierres mensuales consecutivos para filtrar whipsaws y reducir eventos tributarios.

**Pregunta para Claude:** Si un ETF comercial ya empaqueta la regla de tendencia difiriendo los impuestos que a Samir le costarían hasta el 39% en Colombia, ¿qué argumento de rentabilidad neta justifica mantener esta idea abierta dentro del proyecto?

## Ronda 2 — Claude

**Concedo que no es un proyecto de investigación ni una fuente de alfa.** Es gestión de riesgo, y con impuestos colombianos (hay que confirmar las tasas con un contador; ninguno de los dos es asesor tributario) cada salida realiza ganancias que comprar y mantener difiere. El ETF tipo PTLC lo empaqueta dentro del fondo, aunque cobra 0,60% al año, unas 20 veces más que un fondo indexado.

**Pero hay que separar dos preguntas que se mezclaron:**
1. **¿Queda en el proyecto?** No. Se archiva: no tiene nada que investigar con `datos/` (10 años dan muy pocas señales) y no usa la IA.
2. **¿Qué hace Samir con su capital mientras tanto?** Esta es la pregunta de rentabilidad real, y la respuesta más rentable probablemente no sea tendencia sino **comprar y mantener un índice barato**, que difiere impuestos y tiene el mejor retorno esperado a largo plazo. La tendencia solo se justifica si Samir no aguanta una caída de 30% a 50% sin vender en pánico; ahí reduce el daño de comportamiento, que es el costo más grande del inversor minorista.

**Consecuencia práctica para el proyecto:** la vara de todas las ideas debe ser **comprar y mantener SPY**, no la tendencia. Y el capital que no usa una estrategia activa (por ejemplo, entre operaciones de la idea 2) debe estar en ese índice, no en efectivo.

Agrego algo para Colombia que no vimos: los ETF domiciliados en EE. UU. tienen retención de 30% sobre dividendos para no residentes y posible impuesto de sucesiones de EE. UU. Las versiones domiciliadas en Irlanda (UCITS) suelen tener mejor tratamiento. Hay que verificarlo, pero puede pesar más que cualquier diferencia de estrategia.

**Pregunta para Gemini, para cerrar:** ¿coincidís en archivarla del proyecto y fijar comprar y mantener como vara y como destino del capital ocioso? Veredicto final en una línea.

## Ronda 2 — Gemini

### Crítica a Claude: la contradicción del capital ocioso y la inviabilidad de UCITS

El punto más débil de Claude es proponer que **el capital ocioso de las estrategias activas (como la Idea 2) se mantenga en SPY**:

1. **Destrucción fiscal y operativa del "diferimiento":** Si el capital no asignado está en SPY, cada señal swing de PEAD (2 a 5 días) obligaría a vender SPY para fondear la acción y recomprar SPY al cerrar la posición. Esta rotación constante liquida el diferimiento impositivo que Claude defendía en el párrafo anterior, acumulando eventos tributarios de renta ordinaria y pagando doble spread de entrada y salida. El capital táctico ocioso no puede estar en renta variable volátil; debe estar en cuasi-efectivo (SGOV, BIL o el *cash sweep* de Alpaca) para ofrecer liquidez inmediata sin fricción fiscal ni riesgo de mercado.
2. **Contaminación del alfa:** En evaluación cuantitativa (sección 2, criterios de comparación), el capital no desplegado debe devengar la tasa libre de riesgo ($R_f$). Flotar el efectivo a beta 1 en SPY contamina la medición: el retorno de la estrategia activa quedaría dominado por la varianza del mercado durante los días sin señal, ocultando si el LLM realmente genera alfa.
3. **Inviabilidad de UCITS en Alpaca:** Claude sugiere ETFs domiciliados en Irlanda para eludir la retención de dividendos del 30%. Sin embargo, la cuenta de Samir está en Alpaca (sección 1), un broker regulado por SEC/FINRA que lista exclusivamente activos de EE. UU.; los UCITS europeos no están disponibles allí. La limitación de retención debe asumirse con ETFs estadounidenses (como VOO o SPY).

### Respuesta a las preguntas de cierre

- **¿Archivar del proyecto?** Sí. No aporta alfa, no explota la infraestructura de datos del repo (`datos/minuto`) y como producto empaquetado ya existe con mejor eficiencia impositiva (PTLC).
- **¿Fijar comprar y mantener como vara?** Sí. Cualquier modelo activo con IA (Idea 2) debe superar a comprar y mantener SPY en retorno neto ajustado por riesgo e impuestos.
- **¿Destino del capital ocioso?** En el patrimonio personal de Samir, SPY; en la operativa táctica del sistema (Idea 2), letras del Tesoro o efectivo remunerado.

**Veredicto final:** Se descarta la Idea 3 del proyecto; la vara del sistema es comprar y mantener SPY, con el capital táctico ocioso en letras del Tesoro.

## Veredicto (Claude)

**Archivada del proyecto.** Es gestión de riesgo, no rentabilidad, y existe empaquetada.

Lo que queda de este hilo, y vale para todas las ideas:
- **La vara del proyecto es comprar y mantener SPY**, no la tendencia.
- **Capital de la estrategia activa sin usar:** en letras del Tesoro o efectivo remunerado, no en SPY. Concedo el punto de Gemini: rotar SPY en cada señal genera impuestos y además ensucia la medición del alfa.
- **Patrimonio personal de Samir, fuera del proyecto:** índice barato, comprar y mantener. La tendencia solo vale si una caída de 30% a 50% lo haría vender en pánico.
- **Verificar con un contador colombiano:** las tasas (renta ordinaria o ganancia ocasional), la retención de 30% de EE. UU. sobre dividendos y el impuesto de sucesiones de EE. UU. Según Gemini, Alpaca no ofrece ETF UCITS; habría que confirmarlo y, si importa, evaluar otro bróker para el patrimonio de largo plazo.
