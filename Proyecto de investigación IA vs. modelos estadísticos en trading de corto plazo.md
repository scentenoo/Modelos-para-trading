# IA para noticias + modelos estadísticos en trading de corto plazo

Proyecto de investigación · @Samir Centeno · versión 3 · 15 de noviembre de 2026

## 1. Resumen

**Objetivo:** construir un sistema de corto plazo que gane dinero después de costos. Cada parte hace lo que mejor sabe hacer: la IA lee noticias y los modelos de árboles trabajan con los números de las velas.

**Pregunta:** ¿la información que una IA saca de las noticias mejora la ganancia neta de un modelo estadístico de corto plazo? ¿Mejora más a medida que crece el modelo de IA?

- **H0:** agregar la IA no aumenta la ganancia neta por operación frente al modelo de velas solo ni frente a la referencia.
- **H1:** el sistema con IA obtiene una ganancia neta por operación mayor, con significancia estadística.

**Alcance:** SPY, QQQ, IWM y 50 acciones líquidas de EE. UU., con velas de 1 minuto agregadas a 5 y 15 minutos. Quedan fuera por ahora opciones, cripto, apalancamiento y la Bolsa de Valores de Colombia.

**Naturaleza:** es un proyecto de investigación. El dinero real llega solo si H0 se rechaza.

**Dónde vamos:** Fase 1 (datos) casi terminada. Las velas ajustadas, los ajustes corporativos y las noticias ya están descargados; falta que termine la descarga de velas sin ajustar y sumar las dos fuentes de la SEC.

## 2. Cómo funciona el sistema

### Reparto del trabajo

| Parte | Qué lee | Qué entrega |
| --- | --- | --- |
| Modelo de árboles (XGBoost/LightGBM) | Velas: precio y volumen de cada minuto | Un orden de las acciones, de la que más va a subir a la que menos |
| IA (LLM) | Noticias y comunicados de la empresa | Variables sobre cada noticia: tono, tipo de evento, sorpresa, relevancia |
| Capa de riesgo | Las predicciones de cualquier competidor | Cuánto apostar en cada operación y cuándo parar |

**El horizonte es corto.** La ventaja de la IA es leer y procesar rápido, así que se opera en los minutos siguientes a una noticia. Eso además ayuda con los costos: tras una noticia el precio se mueve más que en un minuto cualquiera, y operar cuesta lo mismo. El horizonte exacto (5, 15 o 30 minutos) se decide midiendo, no por intuición (paso 2.1).

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
| 0 · Preparación | Semana 1 | Falta escribir los criterios de éxito | Llaves funcionando y criterios de éxito escritos |
| 1 · Datos | Semanas 2–3 | En curso | La base se actualiza sola sin intervención |
| 2 · Investigación histórica | Semanas 4–11 | Por empezar | Un modelo de velas supera la referencia en ganancia neta fuera de muestra, corregido por comparaciones múltiples |
| 3 · Experimento en vivo (cuenta de papel) | \~5 meses, por confirmar | Por empezar | IA + velas rechaza H0 frente al modelo de velas solo |
| 4 · Dinero real | Después | Por empezar | — |

### Fase 0 · Preparación

- [x] 0.1 Cuenta de papel en Alpaca (100.000 dólares ficticios).
- [x] 0.2 Llaves de API guardadas en `.env`, que no se sube a GitHub.
- [x] 0.3 Entorno de Python (`.venv`) con las dependencias de `requirements.txt`.
- [ ] 0.4 Escribir los criterios de éxito con números, antes de mirar resultados. Depende del paso 2.1.

### Fase 1 · Datos

- [x] 1.1 Velas de 1 minuto, ajustadas: 70,9 millones de velas de los 53 símbolos, 2016–2026. Quedan como copia de comprobación en `datos/minuto_ajustado`.
- [ ] 1.2 Velas de 1 minuto, sin ajustar: descarga en curso hacia `datos/minuto`. Son la base de trabajo.
- [x] 1.3 Ajustes corporativos: 1.916 dividendos, 16 splits y 7 escisiones, en `datos/ajustes`.
- [x] 1.4 Ajuste al leer: `precios.py` corrige splits y dividendos. Coincide con el ajuste de Alpaca con una diferencia máxima de 0,012% en NVDA y KO.
- [ ] 1.5 Comprobar el ajuste contra la copia ajustada en los 53 símbolos, cuando termine 1.2.
- [x] 1.6 Noticias: 339.955 noticias de 2016 a hoy, en `datos/noticias`.
- [ ] 1.7 Comunicados oficiales 8-K de la SEC.
- [ ] 1.8 Cifras de resultados trimestrales de la SEC.
- [ ] 1.9 Actualización diaria automática de velas, ajustes y noticias.

### Fase 2 · Investigación histórica

Plazo máximo: 6–8 semanas. El mejor modelo de velas pasa al experimento en vivo.

- [ ] 2.1 **Medir la barrera de costos.** Para cada acción, cuánto se mueve el precio en 5, 15, 30 y 60 minutos, en un minuto cualquiera y justo después de una noticia, comparado con el costo de entrar y salir. De aquí salen el horizonte, las acciones que vale la pena operar y el tamaño de muestra de la Fase 3.
- [ ] 2.2 **Variables por acción:** retornos, volatilidad, liquidez (volumen, diferencial entre compra y venta), beta y sector.
- [ ] 2.3 **Segmentar las acciones:** PCA sobre los retornos, clustering jerárquico sobre la distancia de correlación, y K-means o mezclas gaussianas sobre las variables.
- [ ] 2.4 **Segmentar el tiempo en regímenes:** calma, pánico, tendencia, lateralidad. Modelo oculto de Markov o mezcla gaussiana sobre la volatilidad.
- [ ] 2.5 **Programar la referencia (competidor A):** los cuatro efectos documentados.
- [ ] 2.6 **Entrenar los modelos de velas (competidor B):** XGBoost/LightGBM como modelo principal, por grupo. Regresión logística como base. MLP/LSTM pequeño solo si le gana a XGBoost fuera de muestra. Se predice el retorno de cada acción relativo al de las demás, y se opera solo cuando la ganancia esperada supera el costo.
- [ ] 2.7 **Controles para comparar:** un modelo global con grupo y régimen como variables, y un modelo multinivel en el que cada grupo tiene sus propios coeficientes pero se acercan a la media general cuando tiene pocos datos.
- [ ] 2.8 **Revisión contra el sobreajuste** antes de aprobar un modelo, con `backtest-expert` y `residual-edge-analyzer`.
- [ ] 2.9 **Montar lo que se dejó para el final:** el PC viejo como servidor, los modelos de IA locales y las instrucciones para que la IA lea noticias.

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
| Comunicados oficiales (SEC) | Formularios 8-K: lo que la empresa informa por obligación legal | Por hacer | Por hacer |
| Cifras de resultados (SEC) | Ingresos, utilidad y ganancia por acción de cada trimestre | Por hacer | Por hacer |

Formato: Parquet, un archivo por símbolo y año para las velas y uno por mes para las noticias. SQLite para el registro de decisiones.

### Por qué precios sin ajustar

Un split o un dividendo cambia el precio de una acción sin que la empresa valga más ni menos. Si el modelo ve esos saltos, aprende caídas que nunca existieron.

- Se guardan los precios a los que realmente se negoció, que nunca cambian y son los que verán los competidores en vivo.
- `precios.py` los corrige al leerlos, con la tabla de ajustes.
- Las escisiones no se corrigen, porque el factor depende del precio de la empresa nueva. Son 7 en 11 años (GE, HON, PFE y T); esos días se excluyen.

### Lo que se sabe de las noticias

- El volumen crece de unas 18.000 al año en 2016 a unas 38.000 desde 2022.
- Cerca de la mitad trae texto completo; entre 2018 y 2020 baja a menos del 30% y el resto solo tiene titular.
- El reparto es desigual: SPY tiene 82.000 y Tesla 39.000, mientras las de servicios públicos y LIN tienen alrededor de mil cada una.
- Si una noticia fue corregida después de publicarse, el texto guardado es el corregido. Para no usar información del futuro se trata como disponible desde la fecha de corrección.

### Para qué la SEC

Un comunicado 8-K suele salir antes que la nota de prensa que lo resume, así que le da a la IA el texto original y más temprano. Con las cifras de resultados, la "sorpresa" de un trimestre se calcula con números en vez de pedírsela a la IA.

### Limitaciones anotadas

- **Sesgo de supervivencia:** el universo son empresas que existen hoy.
- **LIN** tiene datos solo desde 2018, cuando empezó a cotizar con ese símbolo.

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
- **Tamaño de muestra:** se calcula después del paso 2.1, con la variabilidad real de la ganancia neta por operación.
- **Muestra efectiva:** los datos de minutos están autocorrelacionados, y varias acciones reaccionan a la misma noticia; millones de filas no equivalen a millones de observaciones independientes.

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
| `descargar_ajustes.py` | Baja splits, dividendos y escisiones |
| `descargar_noticias.py` | Baja las noticias, un archivo por mes |
| `precios.py` | Lee las velas y las corrige por splits y dividendos: `cargar("NVDA")` |

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

Pendiente: salida del comando de diagnóstico del PC viejo para decidir si se reinstala o se limpia.

## 9. Reglas y decisiones

### Reglas de enfoque

- Ninguna fase avanza sin cumplir su criterio de salida.
- Nada nuevo entra (activos, técnicas, mercados) sin cerrar la fase actual.
- Todo resultado se reporta, también los negativos.
- Los criterios de éxito se escriben antes de mirar los datos.

### Decisiones abiertas

- [ ] Capital máximo de riesgo.
- [ ] Bróker definitivo (Alpaca o Interactive Brokers), confirmando que acepte residentes en Colombia.
- [ ] Regla de "pattern day trader" de EE. UU.: el repositorio day-trader-skill afirma que FINRA eliminó el mínimo de 25.000 dólares en junio de 2026 (aviso 26-10) y que los brókers tienen hasta octubre de 2027 para aplicarlo. Confirmar con FINRA y con Alpaca antes de darlo por hecho.
- [ ] Horizonte principal: sale del paso 2.1.
- [ ] Modelo local a probar en el portátil.
- [ ] Compra del segundo módulo de RAM.

### Decisiones cerradas

- [x] Universo: SPY, QQQ, IWM y 50 acciones (lista en `descargar_datos.py`).
- [x] Precios sin ajustar, con splits y dividendos aplicados al leer.
- [x] La IA lee noticias; los modelos de árboles leen velas.
- [x] El éxito se mide en ganancia neta, no en acierto.
- [x] El horizonte sigue siendo corto.
- [x] El PC viejo y los modelos de IA se configuran al final.

## 10. Historial de cambios

| Tema | Versión 1 | Versión actual | Por qué |
| --- | --- | --- | --- |
| Papel de la IA | Competía contra los modelos clásicos con los mismos números | Lee noticias; los árboles leen velas; se suman | Con números puros un LLM no tiene ventaja sobre XGBoost y es mucho más lento y caro |
| Criterio de éxito | Tasa de acierto (53% contra 50%) | Ganancia neta por operación | A 5 minutos, 53% de acierto no alcanza a pagar los costos |
| Qué se predice | Si cada acción sube o baja | El orden de las acciones, de mejor a peor | Quita el ruido del mercado general y da más observaciones por día |
| Referencia | Regla fija o azar | Cuatro efectos documentados | Ganarle al azar no demuestra nada |
| Escala de la IA | Regresión sobre el número de parámetros | Prueba de tendencia sobre el orden de tamaño | Claude no publica sus parámetros |
| Tamaño de muestra | 2.200 operaciones | Por calcular en el paso 2.1 | La cifra era para acierto, que ya no es el criterio |
| Precios | Ajustados | Sin ajustar, con corrección al leer | Los ajustados cambian con cada split o dividendo nuevo |
| Fuentes de texto | Ninguna | Noticias de Alpaca y comunicados de la SEC | Es lo que lee la IA |
