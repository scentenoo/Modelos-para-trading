# Dictamen del juez: 2026-11-17-ideas-rentables

Juez: claude-opus-5-5 (sesión independiente de Claude Code, sin acceso a la conversación del debate), sobre la copia anonimizada.

## Dictamen

El debate no trae un veredicto escrito al final: `debate.md` termina en la lista final de Participante B (línea 147). No hay un veredicto previo con el que comparar esta decisión.

### Verificación de hechos

| Afirmación | Quién | Veredicto | Evidencia |
| --- | --- | --- | --- |
| "−2,75 bps; la selección cayó a −0,96, t −0,44" (Ronda 1 — A) | A | **Correcta** | `resultados/muestra_final.md:13`: "Ganancia neta por operación de al menos 1 bps \| -2,75 bps \| no pasa"; `:60`: "Selección \| -0,96 \| -0,44" |
| "el PEAD falló por cerrarse a 60 min intradía (−2,37 bps netos)" (Ronda 1 — B) | B | **Incorrecta** | −2,37 es el total de los cuatro efectos. La deriva a 60 min dio −3,86: `resultados/referencia.md:37`: "Deriva tras resultados \| 1.376 \| 806 \| 50,1% \| -1,42 \| 2,45 \| -3,86"; `:39`: "**A · los cuatro** \| 330.750 \| ... \| -2,37" |
| "`lector_noticias.py` responde en 2,1 s a $0,025/noticia" (Ronda 1 — B) | B | **Incorrecta** (el costo está 100 veces inflado; no cambia nada) | Documento principal, línea 141: "latencia mediana 2,1 s ... unos 0,025 centavos de dólar por noticia" |
| "spread de 24,6 bps del pre-mercado" (Ronda 1 — B) | B | **Correcta** | `resultados/barrera_costos.md:11`: "Pre-mercado (7:00–9:30) \| 24,6 bps" |
| "el 84% de los comunicados sale fuera de sesión (sección 4)" (Ronda 1 — B) | B | **Correcta**, pero la sección citada es otra (la 2) | Documento principal, línea 33: "(casi la mitad de las noticias y el 84% de los comunicados)" |
| "El plan gratuito llega con 15 minutos de retraso (sección 3, 'Datos a tiempo')" (Ronda 2 — A) | A | **Correcta** | Documento principal, línea 489: "Las velas del mercado completo (SIP) del plan gratuito llegan con 15 minutos de retraso" |
| "las velas de SPY, QQQ e IWM de 2016–2026 ya están en `datos/minuto`" (Ronda 1 — A) | A | **Correcta** | Documento principal, línea 80: "70,9 millones de velas en `datos/minuto`, 2,2 GB"; `descargar_datos.py:68`: `"SPY", "QQQ", "IWM",` |
| "las 340.000 noticias de `datos/noticias` y los 2.342 comunicados de resultados de `datos/sec`" (Ronda 3 — A) | A | **Correcta** | Documento principal, línea 84: "339.955 noticias"; línea 85: "8.333 comunicados de las 50 acciones (2.342 de resultados trimestrales)" |
| "La infraestructura ya existe" para el S&P 500 (Ronda 1 — A; también Ronda 1 — B) | A y B | **Exagerada** | El universo tiene 53 símbolos. `descargar_datos.py:66`: `UNIVERSO = [`; `descargar_sec.py:212`: `default=[s for s in UNIVERSO if s not in ETF]`; `noticias_vivo.py:167`: `df = consulta(UNIVERSO, inicio, _ahora())` |
| "En SPY el spread es de un centavo ... alrededor de 0,2 bps" (Ronda 1 — A) | A | **Correcta en lo esencial** | `resultados/barrera_costos.md:12`: "Horario normal (9:30–16:00) \| 2,7 bps \| SPY (0,3)" |
| El documento "excluye expresamente derivados" (Ronda 2 — B) | B | **Exagerada o fuera de contexto** | Documento principal, línea 13: "Quedan fuera **por ahora** opciones, cripto, apalancamiento". A da un argumento nuevo y explícito: el objetivo cambió a generar dinero. |
| Comisiones de Alpaca de "$0,50–$0,65 por contrato" (Ronda 2 — B) | B | **Incorrecta** | Alpaca no cobra comisión en opciones para clientes minoristas; solo cobra tasas de FINRA, ORF y OCC de céntimos por contrato ([Alpaca, comisiones](https://alpaca.markets/support/what-are-the-commission-fees-per-option-contract), [Alpaca, tasas](https://alpaca.markets/support/what-are-the-fees-associated-with-options-trading)) |
| NightShares "liquidó en 2023 por retornos negativos tras fricciones de subasta" (Ronda 3 — B) | B | **Exagerada** | NSPY cerró en agosto de 2023 con unos 3,7 millones de dólares en activos, por falta de tracción. Sí había quedado muy por detrás del S&P 500, pero ninguna fuente culpa a las subastas ([etf.com](https://www.etf.com/sections/news/2-nightshares-etfs-close-after-struggling-gain-traction), [WealthManagement/Bloomberg](https://www.wealthmanagement.com/etfs/night-effect-etfs-shut-down-overnight-stock-returns-elusive), [SEC 497](https://www.sec.gov/Archives/edgar/data/1199046/000158064223003676/nightshares497s.htm)) |
| "un ETF puede cerrar por falta de activos" (Ronda 3 — A) | A | **Correcta**, aunque incompleta (el ETF también rindió mal) | Mismas fuentes |
| Prima nocturna: "casi todo el retorno acumulado ... llegó de noche" (Lou, Polk y Skouras, 2019; Kelly y Clark, 2011) (Ronda 1 — A) | A | **Exagerada o fuera de contexto** | Las dos citas existen. Kelly y Clark (2011) comparan los retornos dentro y fuera de sesión ([RePEc](https://ideas.repec.org/a/pal/assmgt/v12y2011i2d10.1057_jam.2011.2.html)). Lou, Polk y Skouras tratan sobre todo de 14 estrategias de corte transversal, no del retorno del índice ([LSE](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)). El "casi todo" para SPY no quedó confirmado. |
| Índice PUT de Cboe: "retorno parecido al S&P 500 con menos volatilidad desde 1986" (Ronda 1 — A) | A | **Correcta, pero fuera de contexto** | Hasta agosto de 2023: 9,40% contra 9,91% anual, con volatilidad de 10,26% contra 15,38% ([Cboe](https://www.cboe.com/insights/posts/generating-income-and-managing-risk-cash-secured-put-writing-in-a-low-equity-return-environment)). Pero el índice PUT vende puts con efectivo de garantía, no spreads de crédito. El put que se compra como protección es caro por el sesgo de volatilidad, así que el respaldo no se traslada. |
| Tetlock (2007): "caída seguida de reversión, no una deriva, y a nivel de mercado" (Ronda 2 — A) | A | **Correcta** | "high pessimism is followed by downward pressure on prices and then a return to fundamentals", sobre una columna del WSJ y a nivel de mercado ([SSRN](https://papers.ssrn.com/abstract=685145)) |
| Chan (2003): las acciones con noticias siguen la dirección y las que se mueven sin noticias se revierten (Ronda 2 — A; aceptado en Ronda 3 — B) | A y B | **Correcta, pero fuera de contexto** | Son retornos mensuales y el efecto se ve "mainly ... in smaller, more illiquid stocks" ([RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:70:y:2003:i:2:p:223-260)). No respalda derivas de 1 a 3 días en el S&P 500. |
| Lehmann (1990): "buena parte se explicaba por rebote entre compra y venta y por acciones chicas" (Ronda 2 — A) | A | **Exagerada** | El resumen del artículo dice que las ganancias persisten "after corrections for ... thin trading and bid-ask spreads" ([NBER](https://www.nber.org/papers/w2533)) |
| "Rebote promedio de 80–120 bps", "50–70 bps netos" (Ronda 1 — B) | B | **No verificada** | No sale del repo ni de ninguna cita concreta. A lo señaló y B no respondió. |
| "50 bps por operación" (Ronda 1 — A) y "40–60 bps netos" (Ronda 1 — B) en la deriva tras resultados | A y B | **No verificada** | Es un supuesto de los dos. En el repo la única versión probada, dentro del día, no se distingue de cero (`referencia.md:37`). |
| Womack (1996): deriva de días tras recomendaciones de analistas (Ronda 2 — A) | A | **No verificada** | No se buscó con fuente en esta revisión |

### Puntos en disputa

| Punto | Mejor argumento (A / B / ninguno) | Por qué |
| --- | --- | --- |
| Idea 1 compartida: sorpresa de resultados leída por un LLM | **A** (en la forma final) | Los dos la proponen. A tomó la mejor crítica de B ("muchos 8-K se publican a las 16:05 o de madrugada sin cobertura periodística", Ronda 2 — B) y la convirtió en una medición que la regla del pasado permite, porque solo mira horarios. Además, su criterio de descarte exige ganarle a "la base de reacción de precio". La versión de B ("Haiku procesa directamente el anexo EX-99", Ronda 3 — B) es una respuesta válida, pero su fundamento cita mal el −2,37. |
| Prima nocturna en ETF | **A** | Es la única idea que se prueba con datos que ya están y con una regla sin parámetros. Las tasas que B objeta son marginales, y la crítica de NightShares está exagerada, aunque el mal rendimiento del ETF en 2022–2023 es una advertencia legítima. |
| Venta de puts y spreads de crédito | **Ninguno** | B se equivoca en las comisiones y en que el documento prohíba las opciones de forma definitiva. A respalda los spreads con un índice que no es esa estrategia. A la dejó al final como reserva, que es lo razonable. |
| Reversión de sobreventa con filtro LLM (idea 2 de B) | **A** | Las cifras no tienen respaldo y el filtro LLM no se puede probar en el histórico. El arreglo de B ("se entra en MOO al día siguiente", Ronda 3 — B) resuelve el problema del retraso de datos, pero cambia la estrategia: el rebote nocturno queda fuera (ver abajo). |
| Catalizadores fuera de horario: ¿diversifican? | **A** | A acierta en que comparten el riesgo central ("si la idea 1 falla porque el mercado ya descuenta en la apertura, ... esta falle por lo mismo", Ronda 2 — A). B responde sobre el calendario, no sobre ese riesgo. Los dos la terminan aceptando como extensión. |
| Cash drag | **B** | A lo aceptó ("Acepto la crítica del *cash drag*", Ronda 2 — A). El "más del 70% del año" es una estimación sin fuente, pero es razonable. |

### Errores que cambian la conclusión

1. **El universo no es el S&P 500.** Los dos dan por hecho que la infraestructura ya cubre el S&P 500, pero `descargar_datos.py:66` define 53 símbolos, y las noticias en vivo (`noticias_vivo.py:167`) y la SEC (`descargar_sec.py:212`) usan esa misma lista. Con 50 acciones hay unos 200 anuncios al año, y el decil superior da unas 20 operaciones al año, no 200. Las cifras de "~200 operaciones" y de "2 temporadas" (Ronda 3 — A) solo valen si antes se amplía la descarga a unas 500 acciones. B, además, se contradice: escribe "~1.000 eventos" en la Ronda 1 y "~50 ops" en la Ronda 3.
2. **La prueba de A en 2016–2026 toca la muestra final.** El documento dice, en la línea 643, que la muestra final "se usa una sola vez", y ya se usó con B (línea 665). El criterio de A ("neta ≤ 0 en 2023–2026", Ronda 3 — A) no ajusta nada, porque la regla no tiene parámetros, pero solo es legítimo si la regla, los símbolos y los criterios quedan escritos antes de calcular, y si un mal resultado en 2025–2026 no da pie a una variante nueva.

### Lo que ninguno vio

- **La reversión de corto plazo se gana de noche.** Lou, Polk y Skouras, el mismo artículo que cita A, encuentran que la ganancia de la reversión "earned entirely overnight" ([LSE](https://researchonline.lse.ac.uk/id/eprint/87481)). Comprar en la apertura del día siguiente, que es el arreglo de B en la Ronda 3, deja fuera justamente esa parte. Esto confirma el descarte de la idea 2 de B.
- **Nadie midió el costo de la subasta de apertura en acciones sueltas.** El repo midió el spread entre las 10:00 y las 10:35, no la subasta de las 9:30: documento principal, línea 371: "en la apertura (10:00–10:35, donde entra el 70% de las operaciones)". Las ideas 1 y 3 de los dos dependen de comprar en esa subasta.
- **No está confirmado que Alpaca abra cuentas de opciones a residentes de Colombia.** Alpaca anunció opciones para clientes internacionales ([Alpaca](https://alpaca.markets/blog/alpaca-launches-us-options-trading-to-global-investors-and-algo-traders/)), pero no encontré confirmación para Colombia: **no verificada**. Esto afecta solo a la reserva.

### Decisión

**Reformular y continuar, con la lista final de Participante A** en este orden: (1) sorpresa de resultados leída por LLM, (2) prima nocturna en SPY y QQQ, (3) catalizadores fuera de horario como extensión de la 1, (4) spreads de crédito de puts como reserva. Se descarta la reversión de sobreventa.

Condiciones concretas:
- **Idea 1:** antes de enero de 2027, ampliar las noticias y los 8-K a todo el S&P 500. Medir en el histórico, solo por horarios, cuántos anuncios tienen el consenso publicado antes de las 9:30. Después, registrar en vivo y en modo sombra con los criterios de descarte de A: correlación de rangos no positiva con t ≥ 1,65, o no mejor que la base de reacción de precio.
- **Idea 2:** escribir la regla, los símbolos y los criterios antes de correr la prueba. El costo de las subastas se mide en las velas de apertura y cierre. Si falla, no se prueban variantes nuevas.
- **Todas:** sin dinero real hasta que alguna pase su criterio, y sin tocar 2025–2026 para ajustar nada.

Confianza: **media**. La cambiaría alguna de estas evidencias:
- Que el consenso casi nunca esté publicado antes de la apertura: la idea 1 pierde su principal ventaja.
- Que la prueba de la prima nocturna no gane en Sharpe a comprar y mantener: la idea 2 se descarta.
- Que el costo medido de la subasta de apertura en acciones sueltas sea alto: se debilitan las ideas 1 y 3.

Fuentes: [etf.com](https://www.etf.com/sections/news/2-nightshares-etfs-close-after-struggling-gain-traction) · [WealthManagement](https://www.wealthmanagement.com/etfs/night-effect-etfs-shut-down-overnight-stock-returns-elusive) · [SEC 497 NightShares](https://www.sec.gov/Archives/edgar/data/1199046/000158064223003676/nightshares497s.htm) · [Alpaca, comisiones de opciones](https://alpaca.markets/support/what-are-the-commission-fees-per-option-contract) · [Alpaca, tasas](https://alpaca.markets/support/what-are-the-fees-associated-with-options-trading) · [Alpaca, opciones globales](https://alpaca.markets/blog/alpaca-launches-us-options-trading-to-global-investors-and-algo-traders/) · [Tetlock 2007](https://papers.ssrn.com/abstract=685145) · [Chan 2003](https://econpapers.repec.org/RePEc:eee:jfinec:v:70:y:2003:i:2:p:223-260) · [Lehmann 1990](https://www.nber.org/papers/w2533) · [Lou, Polk y Skouras](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf) · [Kelly y Clark 2011](https://ideas.repec.org/a/pal/assmgt/v12y2011i2d10.1057_jam.2011.2.html) · [Cboe PUT](https://www.cboe.com/insights/posts/generating-income-and-managing-risk-cash-secured-put-writing-in-a-low-equity-return-environment)

---
**Revelación (después del dictamen):** Claude = Participante A; Gemini = Participante B

