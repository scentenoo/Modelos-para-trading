# Proyecto de investigación: IA vs. modelos estadísticos en trading de corto plazo

Nov 15, 2026 · @Samir Centeno

## Objetivo y pregunta de investigación

Pregunta: ¿la capacidad de una IA grande (más parámetros, más procesamiento) le da ventaja en operaciones de corto plazo frente a modelos estadísticos clásicos y a una referencia simple? ¿El desempeño mejora a medida que crece el modelo?

- **H0:** la IA no tiene ventaja sobre la referencia ni sobre los modelos clásicos.
- **H1:** la IA obtiene una expectativa por operación mayor, con significancia estadística.
- **Alcance:** acciones y ETF líquidos de EE. UU. (SPY, QQQ y unas 50 acciones), velas de 5 a 15 minutos.
- **Fuera de alcance por ahora:** opciones, cripto, apalancamiento, Bolsa de Valores de Colombia.
- **Naturaleza:** proyecto de investigación. El dinero real llega solo si H0 se rechaza.

**Diseño por escala (dosis-respuesta):** el mismo insumo se le da a LLM de distinto tamaño — local pequeño (1–3B), local mediano (7–8B), Claude Haiku y un Claude grande. Si el tamaño importa, el desempeño neto debe subir con los parámetros; se prueba con una regresión del desempeño sobre el log del número de parámetros, o una prueba de tendencia. Los modelos clásicos y la referencia quedan como piso. La latencia se registra aparte: un modelo más grande puede predecir mejor pero llegar tarde.

## Infraestructura

El PC viejo queda como servidor 24/7 en la red local; el portátil hace desarrollo y análisis.

| Componente | Rol | Notas |
| --- | --- | --- |
| PC viejo (Linux, \~4 GB) | Descarga datos, guarda, programa tareas, registra decisiones | Sin entorno gráfico, SSH con llaves, IP fija, cable de red si es posible |
| Portátil (Celeron N5095, 16 GB) | Desarrollo, entrenamiento de modelos clásicos, modelos locales pequeños | Agregar un segundo módulo DDR4 para doble canal |
| Claude por API | Decisiones de la IA en tiempo real | Se paga aparte del plan Pro |
| Google Drive | Respaldo nocturno con rclone | No se trabaja directo desde Drive |
| Kaggle / Colab | GPU gratis para redes neuronales más grandes | Solo si hace falta |

Pendiente: salida del comando de diagnóstico del PC viejo para decidir si se reinstala o se limpia.

## Datos

Fuente principal: Alpaca, plan gratuito ($0). Histórico del mercado completo desde 2016 (sin los últimos 15 minutos), tiempo real de IEX y cuenta de papel.

- **Histórico (una sola descarga):** velas de 1 minuto 2016–2026 para SPY, QQQ y \~50 acciones líquidas. Se agregan a 5 y 15 minutos.
- **En vivo (continuo):** velas nuevas cada 5–15 minutos y el registro de cada decisión.
- **Formato:** Parquet particionado por fecha; SQLite para el registro de decisiones.
- **Tamaño esperado:** cientos de MB por año; cabe en el PC viejo.
- **Pagos opcionales:** Alpaca $99/mes (tiempo real completo, solo al operar con dinero real); Massive $29–$199/mes (más historia); FirstRate Data, pago único desde USD 399,95 (incluye acciones que dejaron de cotizar).

Uso de los datos: el histórico entrena y filtra los modelos clásicos; los datos en vivo alimentan a todos los competidores y miden quién gana. La IA no se evalúa con el histórico porque ya lo vio en su entrenamiento.

Fuentes: [Alpaca – Market Data](https://alpaca.markets/docs/market-data) · [Massive – Pricing](https://massive.com/pricing) · [FirstRate Data](https://firstratedata.com/)

## Fase histórica: segmentación y modelos por grupo

Hipótesis de trabajo: modelar por grupo predice mejor que un modelo único para todas las acciones. Se prueba, no se asume.

1. **Variables por acción:** retornos, volatilidad, liquidez (volumen, spread), beta y sector.
2. **Segmentación por acción:**
   - PCA sobre los retornos para extraer factores.
   - Clustering jerárquico sobre la distancia de correlación.
   - K-means o mezclas gaussianas sobre las variables.
3. **Segmentación en el tiempo (regímenes):** calma, pánico, tendencia, lateralidad. Modelo oculto de Markov o mezcla gaussiana sobre la volatilidad.
4. **Modelos por grupo (enfoque principal):** logística, XGBoost/LightGBM y MLP/LSTM pequeño en cada grupo.
5. **Controles para comparar:**
   - Modelo global con grupo y régimen como variables.
   - Modelo multinivel (partial pooling): cada grupo tiene sus propios coeficientes, pero se acercan a la media general cuando el grupo tiene pocos datos.
6. **Regla anti-anticipación:** los grupos y regímenes se recalculan en cada ventana del walk-forward, solo con datos del pasado.

Plazo máximo: 6–8 semanas. Lo que salga compite contra la IA.

## Competidores y experimento en vivo

Todos reciben el mismo insumo al mismo tiempo; cada uno responde con dirección, retorno esperado y confianza.

| Competidor | Qué es | Para qué está |
| --- | --- | --- |
| Referencia simple | Regla fija o entradas al azar | Si la IA no le gana, no tiene ventaja |
| Regresión logística | Modelo lineal por grupo | Base estadística |
| XGBoost / LightGBM | Árboles por grupo | El rival fuerte |
| MLP / LSTM pequeño | Red neuronal por grupo | Entra solo si le gana a XGBoost fuera de muestra |
| Claude (API) | LLM en la nube | Hipótesis principal |
| Modelo local | LLM en el portátil | Comparar nube vs. local |

1. Los scripts calculan los indicadores cada 5–15 minutos.
2. Cada competidor responde en JSON: comprar / vender / nada, retorno esperado, confianza.
3. Se registra todo: decisión, razonamiento (LLM), latencia, precio de entrada y salida, costo.
4. Ejecución en la cuenta de papel de Alpaca desde el día 1.
5. Horario del mercado en Colombia: 9:30 a. m.–4:00 p. m. en invierno de EE. UU.; una hora antes desde marzo.

## Evaluación estadística

Las métricas y el umbral de éxito se fijan por escrito antes de ver resultados.

- **Métricas de predicción:** precisión, AUC, log-loss, calibración de la confianza.
- **Métricas de trading (netas de costos):** expectativa por operación, tasa de acierto, Sharpe, drawdown máximo.
- **Validación:** walk-forward y una muestra final que no se toca hasta el cierre.
- **Comparaciones múltiples:** el R² ajustado penaliza variables dentro de un modelo, pero no corrige elegir el mejor entre muchos. Se usa:
  - Reality Check de White o test SPA de Hansen.
  - Deflated Sharpe ratio.
  - Romano-Wolf o Bonferroni para varias hipótesis.
- **Tamaño de muestra:** detectar 53% vs. 50% de acierto (α = 0,05, potencia 80%) exige unas 2.200 operaciones; \~5 meses a 20 operaciones por día.
- **Muestra efectiva:** los datos de minutos están autocorrelacionados; millones de filas no equivalen a millones de observaciones independientes.

## Riesgo, tamaño de posición y ejecución

Una capa común decide cuánto apostar, igual para todos los competidores; así se compara solo la calidad de la predicción.

- **Tamaño de posición:** Kelly fraccional o volatilidad objetivo, según retorno esperado y confianza.
- **Riesgo:** límite de pérdida diaria, exposición máxima por acción y por grupo correlacionado.
- **Ejecución:** órdenes límite cuando sea posible; registrar slippage real contra el precio esperado.
- **Monitoreo:** si un competidor se degrada frente a su desempeño histórico, se apaga.
- **Regla de apagado del sistema:** pérdida máxima fijada de antemano antes de operar con dinero real.

## Cronograma por fases

&#91;embedded content: hoja de ruta · 5 fases, 4 criterios de salida\]

Son unos 8 meses hasta poner dinero real; la Fase 3 es el núcleo del estudio.

## Reglas de enfoque y decisiones abiertas

Reglas:

- Ninguna fase avanza sin cumplir su criterio de salida.
- Nada nuevo entra (activos, técnicas, mercados) sin cerrar la fase actual.
- Todo resultado se reporta, también los negativos.
- Los criterios de éxito se escriben antes de mirar los datos.

Decisiones abiertas:

- [ ] Capital máximo de riesgo
- [ ] Broker definitivo (Alpaca vs. Interactive Brokers, confirmar que acepta residentes en Colombia)
- [ ] Lista final de las \~50 acciones
- [ ] Temporalidad principal: 5 o 15 minutos
- [ ] Modelo local a probar en el portátil
- [ ] Compra del segundo módulo de RAM
