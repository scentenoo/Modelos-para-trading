# Debate de viabilidad · Idea 1: PEAD con sorpresa numérica (sin IA)

## Tema

Samir pide profundizar en cada idea del debate anterior (`debate/2026-11-17-como-hacerlo-rentable.md`, sección Síntesis), con dos rondas por idea sobre **descartarla o continuarla**, sobre todo por **viabilidad frente al objetivo de rentabilidad**.

**Vara común para las cuatro ideas:** es "rentable" si, fuera de muestra y después de costos, (a) le gana a comprar y mantener SPY en retorno ajustado por riesgo, o (b) da un retorno parecido con una caída máxima claramente menor; y si se puede operar con una cuenta chica desde Colombia (Alpaca, solo compras, plan gratuito de datos, sin la regla PDT). También cuenta el costo de oportunidad: si existe un ETF barato que hace lo mismo, construirlo no agrega rentabilidad.

**La idea:** comprar acciones del S&P 500 con sorpresa positiva grande en sus resultados trimestrales (calculada con las cifras de la SEC, `datos/sec/cifras`, frente al mismo trimestre del año anterior) y mantenerlas entre 1 y 20 días o hasta 60. Solo compras.

## Ronda 1 — Claude

**Mi postura: continuar solo como base de comparación de la idea 2, no como fuente de ganancia propia.**

Contra su rentabilidad:
1. **La deriva tras resultados casi desapareció en las acciones grandes.** La literatura reciente (por ejemplo Martineau, 2022, "Rest in Peace Post-Earnings Announcement Drift") encuentra que en las grandes ya no se distingue de cero desde mediados de los 2000; sobrevive en las chicas y poco líquidas. El S&P 500 es justo donde menos queda.
2. **La sorpresa numérica sin consenso es la versión débil.** Comparar con el mismo trimestre del año anterior (paseo al azar estacional) mide peor la sorpresa que el consenso de analistas, que es lo que mueve el precio. Además, las cifras estructuradas de la SEC llegan tarde (sección 4, "Limitaciones anotadas"): días después del comunicado de resultados.
3. **Solo compras le quita la mitad.** La deriva clásica es una cartera de compra y venta; la pata de compras sola, en grandes, es pequeña y se mezcla con el mercado.

A favor de mantenerla:
- **Es barata y hace falta igual:** la idea 2 necesita exactamente esta base para demostrar que la IA aporta (D contra B en otro terreno).
- **Hay una variante con mejor fundamento para solo compras:** la *prima del anuncio de resultados* (las acciones ganan más en los días alrededor del anuncio, Frazzini y Lamont, 2007), que no necesita medir la sorpresa.

**Pregunta para Gemini:** ¿la descartarías como estrategia propia? ¿Y vale la pena ir a acciones medianas y chicas, donde la deriva sobrevive, aunque el costo y la liquidez empeoren?

## Ronda 1 — Gemini

### Crítica a Claude: la contradicción de una base metodológicamente rota

El punto más débil de Claude es defender que la Idea 1 debe **"continuar como base de comparación porque es barata y hace falta igual"**, pasando por alto que él mismo admitió su inviabilidad técnica.

En la sección 4 ("Limitaciones anotadas"), el proyecto documenta que las cifras financieras estructuradas (`datos/sec/cifras`) provienen del 10-Q/10-K y **llegan con una mediana de 7 días de retraso frente al 8-K** (solo el 20% se publica el mismo día). Por lo tanto, simular una estrategia con `cifras` el día del anuncio introduce un **sesgo de anticipación (*lookahead bias*)** flagrante, mientras que operarla en diferido entra cuando el mercado ya absorbió el impacto. Una base viciada por fuga de información no sirve para validar si la IA aporta ventaja neta (viola la higiene fijada en la sección 2). Además, deslizar la "prima del anuncio" (Frazzini y Lamont, 2007) expone a una cuenta chica a saltos nocturnos (*earnings gaps*) de −15% o −20% sin stop-loss ejecutable, dinamitando el control de riesgo.

### Respuestas a Claude y evaluación frente a la vara común

1. **¿Descartarla como estrategia propia? SÍ, categóricamente.**
- **No bate a SPY ni reduce caídas:** Como cita Claude (Martineau, 2022), el PEAD en megacaps se extinguió hace 20 años. En formato solo compras, la cartera absorbe la volatilidad del mercado y el riesgo asimétrico de sorpresas negativas sin cobertura.
- **Sin datos de consenso:** El paseo al azar estacional frente al año previo es un mal predictor de sorpresa; el consenso real exige APIs de pago (sección 4).

2. **¿Ir a medianas y chicas? NO.**
En `resultados/barrera_costos.md` y sección 2.1 comprobamos que un spread de apenas 1,8 a 2,3 bps en megacaps liquidó la ganancia de B. En empresas medianas y pequeñas, el spread en Alpaca escala a 20–60 bps y la liquidez pre-mercado colapsa bajo el plan gratuito. Intentar extraer una anomalía residual de 30 bps pagando 40 bps de fricción destruye el capital.

### Veredicto y solución para la Idea 2

La Idea 1 **queda descartada como estrategia de inversión independiente.**

Para que la Idea 2 conserve un competidor B legítimo a costo cero y libre de *lookahead*, la base no debe ser la contabilidad tardía de la SEC, sino la **deriva por reacción inicial de precio** (la fórmula ya programada en `referencia.py:155`: retorno anormal contra SPY en la primera media hora). Es pública, ejecutable en $t=0$ y no requiere consenso pago.

**Pregunta para Claude:** Si sustituimos la sorpresa contable por la reacción de precio de `referencia.py` como base para evaluar la IA, ¿queda algún motivo técnico para no archivar la Idea 1 hoy mismo?

## Ronda 2 — Claude

**Acepto el descarte y acepto el cambio de base.** Tenés razón en lo central: con las cifras de la SEC llegando una mediana de 7 días después del comunicado (sección 4, "Limitaciones anotadas"), la sorpresa contable o se calcula con información del futuro o llega tarde. Como base de la idea 2 no sirve.

**La reacción de precio como base es mejor de lo que parece, y la literatura la respalda:** la deriva tras el *retorno anormal del anuncio* (Brandt y otros, 2008, "earnings announcement return") resiste mejor que la de la sorpresa contable, justamente porque el precio ya resume consenso, guía y tono. Pero no usaría la ventana de 30 minutos de `referencia.py`: para una estrategia de varios días, la reacción tiene que medirse en el día del anuncio completo (del cierre previo al cierre del día de reacción, contra SPY) y entrar al cierre de ese día o en la apertura siguiente. Así la base es comparable con la IA.

**Dos correcciones menores:**
- En medianas y chicas el problema no es "pagar 40 bps para ganar 30". La deriva de varios días en chicas se mide en cientos de bps; el spread se paga una vez por operación, no por día. El argumento correcto para descartarlas es otro: liquidez, datos que no tenemos y que con una cuenta chica sobra universo en el S&P 500.
- La prima del anuncio tiene riesgo de salto, pero diversificado entre decenas de anuncios por semana; no es el argumento decisivo. El decisivo es que es una prima chica y conocida.

**Veredicto que propongo:** la idea 1 se **archiva como estrategia** y se **reconvierte en la base de la idea 2**: deriva tras la reacción de precio del día del anuncio, en los mismos eventos y con la misma ejecución que la IA. La IA tiene que ganarle a eso.

**Pregunta para Gemini, para cerrar:** ¿estás de acuerdo con medir la reacción en el día completo y no en 30 minutos? Dame tu veredicto final en una línea y el criterio exacto de descarte de la base.

## Ronda 2 — Gemini

### Crítica a Claude: la fantasía de la diversificación y el descalce de ejecución

El punto más débil de Claude es descartar el riesgo de salto nocturno aduciendo que está *"diversificado entre decenas de anuncios por semana"*. En una cuenta chica retail en Alpaca (la vara común fijada por Samir):
1. **Fricción operativa real:** Diversificar en decenas de posiciones exige comprar fracciones de acciones que no admiten órdenes de subasta (MOO/MOC) y sufren peor ejecución. Además, los resultados no se distribuyen de forma pareja: se concentran en tres semanas pico por trimestre, dejando semanas vacías y forzando concentración. El riesgo de cola de un salto de −20% en cuenta chica no se diluye en papel.
2. **Descalce temporal con la IA:** Si la base exige el cierre completo del día del evento (T) para calcular el retorno anormal, entra en T+1. Pero el 84% de los 8-K sale fuera de sesión (sección 4, "A qué hora sale la información"). Si la IA entrara en la apertura de T y la base en T+1, se destruiría la comparabilidad ("mismos eventos y misma ejecución"). Para que la base sea válida, **ambos modelos deben compartir exactamente la misma ventana de ejecución**.

---

### Reacción de día completo vs. 30 minutos

**Acepto el día completo**, bajo una condición estricta:
- Medir del cierre previo al cierre del día de reacción (contra SPY) elimina la carga computacional de 70 millones de velas de 1 minuto (`datos/minuto`), neutraliza los 20 minutos de desfase del plan gratuito y mide la absorción institucional completa.
- **Condición innegociable:** La IA (Idea 2) debe evaluarse en esa misma ventana de entrada (al cierre de T o en la apertura T+1 vía MOO, horizonte 2–5 días). Así se aísla con rigor la hipótesis: si el texto del 8-K añade alfa sobre lo que el mercado ya descontó en el precio del día del evento.

---

### Veredicto y criterio de descarte

**Veredicto:** La Idea 1 queda **archivada como estrategia independiente** y **reconvertida en la base de referencia (benchmark B) de retorno anormal de precio** para validar la Idea 2.

**Criterio exacto de descarte de la base:**
Se descarta la base (y la anomalía de deriva de precio en megacaps) si en la simulación diaria 2016–2024 del S&P 500 (con composición histórica para evitar sesgo de supervivencia, `debate/2026-11-17-como-hacerlo-rentable.md`):
1. **Ganancia neta:** $\le 0\text{ bps}$ tras descontar el spread de la época (sección 5).
2. **Significancia estadística:** $t < 2,0$ con remuestreo por bloques agrupados por temporada de resultados (bloques de 10 días, como en `comparaciones.py`).
3. **Control de ruina:** Caída máxima (*Max Drawdown*) superior a la de comprar y mantener SPY en el mismo periodo.

## Veredicto (Claude)

**Archivada como estrategia. Reconvertida en la base de la idea 2.**
- Base: deriva tras el retorno anormal del día del anuncio (del cierre previo al cierre del día de reacción, contra SPY), en el S&P 500 con su composición histórica. No se usan las cifras de la SEC, porque llegan una mediana de 7 días tarde.
- Criterio de la base, tomado de Gemini: en 2016–2024, neta ≤ 0 tras costo de la época o t por bloques < 2 → la anomalía no existe en grandes y la idea 2 tiene que ganarle a cero.
- Sobre la ventana de ejecución, ver el veredicto de la idea 2: la base solo puede entrar al cierre del día de reacción, porque necesita ver ese día completo.
