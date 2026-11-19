# Dictamen del juez: 2026-11-17-evaluacion-ideas

Juez: claude-opus-5-5 (sesión independiente de Claude Code, sin acceso a la conversación del debate), sobre la copia anonimizada.

## Dictamen

### Verificación de hechos

| Afirmación | Quién | Veredicto | Evidencia |
|---|---|---|---|
| "El universo actual es de 53 símbolos (dictamen previo, `descargar_datos.py:66`)" | Ronda 1 — A (también Ronda 1 — B) | Correcta | `descargar_datos.py:66` `UNIVERSO = [`; `:65` "Ojo: son empresas que existen hoy -> hay sesgo de supervivencia"; `descargar_sec.py:212` `default=[s for s in UNIVERSO if s not in ETF]`; `noticias_vivo.py:167` `df = consulta(UNIVERSO, inicio, _ahora())` |
| "Haiku cuesta ~0,025 centavos por noticia (documento, línea 141)" y "todos los campos coinciden en dos lecturas de la misma noticia solo el 64%" | Ronda 1 — A | Correcta | Documento:141: "unos 0,025 centavos de dólar por noticia" … "todos los campos a la vez, 64%" |
| "En 50 acciones hay apenas ~200 anuncios anuales en total" | Ronda 1 — B | Correcta | Documento:85: "8.333 comunicados de las 50 acciones (2.342 de resultados trimestrales)", unos 215 por año en 2016–2026 |
| El spread del pre-mercado es de 24,6 bps y el del horario normal, de 2,7 bps (SPY 0,3) | A y B | Correcta | `barrera_costos.md:11` "Pre-mercado (7:00–9:30) \| 24,6 bps"; `:12` "Horario normal (9:30–16:00) \| 2,7 bps \| SPY (0,3)" |
| "Alpaca acepta órdenes para la subasta de apertura y la de cierre" | Ronda 1 — A | Correcta | El changelog de Alpaca lista `opg` y `cls`. Pero en la cuenta de papel las `opg` se simulan como órdenes de mercado (foro de Alpaca) |
| "el PEAD con salida fija a 60 min dio −3,86 bps" | Ronda 1 — B | Correcta | `referencia.md:37` "Deriva tras resultados \| 1.376 \| 806 \| 50,1% \| -1,42 \| 2,45 \| -3,86" |
| "selección −0,96, t −0,44" | Ronda 2 — A; Ronda 3 — B | Correcta | `muestra_final.md:60` "\| Selección \| -0,96 \| -0,44 \|" |
| "llegan con 15 minutos de retraso (documento, línea 489)" | Ronda 2 — A | Correcta | Documento:489: "Las velas del mercado completo (SIP) del plan gratuito llegan con 15 minutos de retraso" |
| "`costo_bordes.md`: la apertura cuesta 1,11 veces el horario normal", usado como el costo de "el momento más caro del día" | Ronda 2 — A | Exagerada o fuera de contexto | `costo_bordes.md:13` "apertura \| 5.181 \| 1,114". Esa franja es 10:00–10:35 (documento:371: "en la apertura (10:00–10:35…)"). No mide las 9:30 ni la subasta |
| "14 variantes subieron el t exigido a 2,69" | Ronda 1 — A | Correcta | Documento:111: "van 14 variantes (t exigido con Bonferroni 2,69)" |
| Con dos pruebas, "t exigido 1,96 en vez de 1,65" | Ronda 3 — A | Correcta | Bonferroni: 5% repartido en dos pruebas da 2,5% de una cola, que es z = 1,96 |
| "NSPY perdió 6,9% contra +22% del S&P 500 antes de cerrar" | Ronda 1 — A | Correcta, aunque otras fuentes dan otras cifras | [WealthManagement/Bloomberg](https://www.wealthmanagement.com/etfs/night-effect-etfs-shut-down-overnight-stock-returns-elusive). [ETF Strategy](https://www.etfstrategy.com/night-effect-etfs-to-close-10339) da −4,72%. El fondo cerró con 3,7 millones de dólares en activos ([etf.com](https://www.etf.com/sections/news/2-nightshares-etfs-close-after-struggling-gain-traction)) |
| "Chan 2003: mensual y acciones chicas" | Ronda 1 — A | Correcta | [Chan 2003, JFE](https://econpapers.repec.org/RePEc:eee:jfinec:v:70:y:2003:i:2:p:223-260): retornos mensuales, deriva fuerte después de malas noticias, sobre todo en acciones chicas y poco líquidas |
| "Respaldada por Chan (2003) y Womack (1996)" (idea 3) | Ronda 1 — B | Exagerada | Chan, como arriba. [Womack 1996](https://econpapers.repec.org/RePEc:bla:jfinan:v:51:y:1996:i:1:p:137-67): la deriva tras una recomendación de compra es "modest (+2.4%) and short-lived". Ninguno de los dos estudia catalizadores fuera de horario en grandes a 3 días |
| "Tetlock, 2007, observó reversión rápida" | Ronda 2 — B | Fuera de contexto | [Tetlock 2007](https://econpapers.repec.org/RePEc:bla:jfinan:v:62:y:2007:i:3:p:1139-1168): el pesimismo de una columna del WSJ predice presión sobre el mercado y luego reversión. Es a nivel de mercado, no de comunicados de una acción |
| "Choca con la regla PDT" | Ronda 2 — A (B lo concede en Ronda 3) | Exagerada o desactualizada | La SEC aprobó eliminar la regla PDT y el mínimo de 25.000 dólares el 14 de abril de 2026 ([FINRA RN 26-10](https://www.finra.org/rules-guidance/notices/26-10)). La adopción por los brókeres va por etapas hasta 2027. Para Alpaca: no verificada |
| "Alpaca no cobra comisión por contrato" | Ronda 1 — A | Correcta | [Alpaca](https://alpaca.markets/support/what-are-the-fees-associated-with-options-trading): sin comisión; cobra las tasas regulatorias y de la OCC |
| "bloqueo regulatorio para Colombia en Alpaca" (opciones) | Ronda 1 — B | No verificada | Documento:845: "la página de Alpaca no lista países y pide escribir a soporte". No está confirmado ni para acciones |
| "el plan gratuito da cotizaciones de IEX en vivo" | Ronda 3 — A | Correcta, con una salvedad | [Alpaca docs](https://docs.alpaca.markets/docs/about-market-data-api): en tiempo real el plan gratuito solo da IEX. Personal de Alpaca dice que IEX no debería usarse para decisiones en vivo |
| A "descalifica el uso de árboles … pero … propone resucitar a B" | Ronda 3 — B | Incorrecta | Una base de comparación no necesita tener ventaja propia. A usa velas diarias ("Usa velas **diarias**", Ronda 3 — A), así que "ni siquiera tenemos velas de 1 minuto" no viene al caso |
| A argumenta que "500 dólares al año es poco" | Ronda 3 — B | Exagerada | Esa frase no está en el debate. A escribió: "Con 10.000 dólares, un 5% anual por encima del efectivo son 500 dólares al año" (Ronda 2 — A) |

### Puntos en disputa

| Punto | Mejor argumento (A / B / ninguno) | Por qué |
|---|---|---|
| Unificar las ideas 1 y 3 en una sola prueba | B | La dilución es lógica: si los catalizadores tienen ventaja nula, la prueba única puede tumbar las dos. A lo concedió ("Retiro la prueba única", Ronda 3 — A). |
| Árboles para la salida dinámica (idea nueva de B) | A | Con 15 minutos de retraso (documento:489) y una variante más, la propuesta no es viable. B la retiró ("la salida debe ser fija a 3 días", Ronda 3 — B). El argumento de la regla PDT de A está desactualizado, pero no hacía falta. |
| Orden: probar primero la base en el histórico | A | "B: semanas, en el histórico" (Ronda 3 — A) da evidencia antes de gastar 6 meses en vivo, y es lo acordado en `previo_3.md` (2016–2024, "neta ≤ 0 … o t por bloques < 2"). La lista final de B no incluye ese paso. |
| Qué base: LightGBM con varias variables o reacción de precio sola | B | La reacción de precio sola ya da esa evidencia temprana. Meter impulso y otras variables en la base reabre lo que A aceptó en `previo_6.md` ("Acepto la crítica de parsimonia"). "Alinearse con la tesis" no es un argumento nuevo sobre la evidencia. El razonamiento de B en la Ronda 3 tiene errores, pero su posición final ("no superar a la reacción de precio") respeta lo decidido. |
| Costo de la subasta de apertura | B la señala, A la convierte en plan | Los dos coinciden en que no está medida (Ronda 2 — B; Ronda 3 — A). El plan de A (sombra contra IEX) es débil por lo que se ve más abajo. |
| Catalizadores: prueba secundaria paralela o fase que depende de la idea 1 | A | El criterio de A es concreto ("Neta ≤ 0 o t < 1,96"). El de B ("Dilución del Sharpe de la cartera…") no se puede medir, y su baja de 3/3 a 2/3 no se justifica. Ninguno tiene respaldo de literatura para grandes a 3 días. |
| Prima nocturna | B, por poco | Los dos la dejan como prueba de descarte de una tarde. B limita la prueba a "2016–2024", que cumple la regla de no tocar 2025–2026. A solo pide "Regla y criterios escritos antes". |
| Canibalización de capital entre las ideas 1 y 2 | A | A la planteó primero (Ronda 1 — A). B se la atribuye como falla de A en la Ronda 3, aunque A ya había bajado la idea 2 a prueba de descarte. |
| Puts | Empate | Los dos la archivan. B corrigió "derivados excluidos" ("fue temporal ('por ahora')", Ronda 3 — B). |

### Errores que cambian la conclusión
- **La base LightGBM de A (Ronda 3):** reabre una decisión cerrada sin un argumento nuevo y suma variantes. Además, D "las mismas variables más las del LLM" no se puede entrenar en el histórico. El documento:472 dice: "D se ajusta en vivo: los primeros meses en la cuenta de papel ajustan una capa pequeña". Con ese diseño, las "2 temporadas" para D contra B no alcanzan: primero hay que entrenar D y después medirlo.
- **El costo de la apertura que se cita (1,11×) no es el de la subasta de las 9:30.** Ninguna cifra del repo respalda el costo de ejecución de las ideas 1 a 3.

### Lo que ninguno vio
- **El costo de la subasta se puede medir ya en el histórico, sin esperar la sombra y sin violar la regla del pasado.** Es un costo, no un acierto del LLM. El plan gratuito da todo el SIP con más de 15 minutos de antigüedad ([Alpaca docs](https://docs.alpaca.markets/docs/about-market-data-api)). Se compara el precio de la subasta de apertura con el punto medio del SIP cerca de las 9:30, en 2016–2024, para los mismos eventos. La sombra no sirve para esto por dos razones: la cuenta de papel simula las `opg` como órdenes de mercado, y personal de Alpaca dice que IEX no es representativo.
- **D tiene que medirse sin entrenamiento.** La prueba debe ser la correlación de rangos de la puntuación del LLM, fijada de antemano, con el retorno en exceso sobre lo que predice la base. Así se evita el mes o los meses de ajuste en vivo.
- **Las condiciones previas a operar dinero siguen sin confirmar:** que Alpaca abra cuentas a residentes de Colombia (documento:845) y si Alpaca ya aplicó el fin de la regla PDT.

### Decisión
**Reformular la idea 1 y continuar con ella (eventos de resultados del S&P 500, con su composición histórica, 3 días fijos).**
1. Probar primero en el histórico, 2016–2024, la base acordada en `previo_3.md`: deriva tras la reacción de precio del día del anuncio, con su criterio ("neta ≤ 0 … o t por bloques < 2"). Medir a la vez el costo de la subasta de apertura con el SIP histórico. Si la neta, con ese costo, es ≤ 0, se para antes de la prueba en vivo.
2. Si la base pasa, la IA se mide en vivo desde enero de 2027 con la puntuación del LLM, sin entrenar, contra la base y en los mismos eventos. El criterio es el de `previo_4.md` (correlación de rangos positiva con t por bloques ≥ 1,65 y mayor que la de la base).
3. Los catalizadores van como segunda prueba con la misma infraestructura, con t ≥ 1,96, solo si no suman trabajo aparte.
4. La prima nocturna, como descarte de una tarde solo en 2016–2024. Los puts y los árboles para la salida quedan descartados.

El debate no tiene un veredicto escrito al final. Las dos listas finales coinciden en el orden, y yo también. Me aparto de la Ronda 3 de A en la base (LightGBM) y en cómo se entrena D, y de la de B en que deja fuera la prueba histórica de la base y la medición del costo antes de ir a vivo.

**Confianza: media.** La cambiaría:
- un costo de subasta histórico mayor a unos 10 bps en acciones sueltas, que haría caer la idea;
- una base con neta claramente positiva en 2016–2024, que haría más urgente probar la IA;
- la confirmación de que Alpaca no abre cuentas desde Colombia, que obligaría a cambiar de bróker antes de seguir.

Fuentes: [WealthManagement/Bloomberg](https://www.wealthmanagement.com/etfs/night-effect-etfs-shut-down-overnight-stock-returns-elusive), [etf.com](https://www.etf.com/sections/news/2-nightshares-etfs-close-after-struggling-gain-traction), [ETF Strategy](https://www.etfstrategy.com/night-effect-etfs-to-close-10339), [Chan 2003](https://econpapers.repec.org/RePEc:eee:jfinec:v:70:y:2003:i:2:p:223-260), [Tetlock 2007](https://econpapers.repec.org/RePEc:bla:jfinan:v:62:y:2007:i:3:p:1139-1168), [Womack 1996](https://econpapers.repec.org/RePEc:bla:jfinan:v:51:y:1996:i:1:p:137-67), [FINRA RN 26-10](https://www.finra.org/rules-guidance/notices/26-10), [Alpaca: tipos de vigencia de órdenes](https://docs.alpaca.markets/us/changelog/2026-05-05-tif-38d668f), [Foro de Alpaca: órdenes OPG](https://forum.alpaca.markets/t/opg-orders-not-filled-at-open-price-live-trading/14672), [Alpaca: datos de mercado](https://docs.alpaca.markets/docs/about-market-data-api), [Alpaca: tarifas de opciones](https://alpaca.markets/support/what-are-the-fees-associated-with-options-trading).

---
**Revelación (después del dictamen):** Claude = Participante A; Gemini = Participante B

