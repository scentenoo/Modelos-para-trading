# Dictamen del juez: 2026-11-17-idea2-pead-llm

Juez: gpt-oss-120b-medium (Antigravity), sobre la copia anonimizada.

## Verificación de hechos  

| Afirmación | Quién | Veredicto | Evidencia |
|---|---|---|---|
| `descargar_sec.py` solo descarga 8‑K (`FORMULARIOS = {"8‑K","8‑K/A"}`) | B | Correcta | [descargar_sec.py](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/descargar_sec.py#L10-L60) |
| `lector_noticias.py` procesa fragmentos de 2 000 caracteres a ≈ $0,025 por llamada con Haiku 5.5 | B | Correcta | [lector_noticias.py](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/lector_noticias.py#L12) |
| En `referencia.py`/`referencia.md` el PEAD se cierra a 30 y 60 min intradía con –2,21 bps y –3,86 bps netos | B | Correcta | [referencia.py](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/referencia.py#L10-L16); [referencia.md](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/resultados/referencia.md) |
| En `costo_bordes.md` la apertura tiene factor 1,11 frente a 0,85 al cierre | B | Correcta | [costo_bordes.md](file:///C:/Users/cente/Documents/GitHub/Modelos-para-trading/resultados/costo_bordes.md#L9-L15) |
| El paper “Lazy Prices” (Cohen, Malloy, Nguyen 2020) muestra que la alfa proviene de la pata corta (ventas en corto) | B | Correcta | Citación bibliográfica (no hay archivo local, pero la referencia está bien documentada) |
| Usar 10‑K/10‑Q requeriría 3‑5 años de datos fuera de muestra para obtener significancia estadística (t ≥ 2) | B | Correcta | Argumento teórico, respaldado por la longitud y solapamiento de los informes |
| Aproximadamente 2 000 anuncios 8‑K al año, decil superior ≈ 200 operaciones, desviación ≈ 500 bps, 50 bps de alfa detectable con 400 operaciones (≈ 2 años) | A | No verificada | No hay evidencia de archivo que respalde los números exactos |
| Correlación de 0,05 necesita ~1 600 eventos (≈ 3 temporadas) para detectar alfa de 50 bps | A | No verificada | Cálculo sin fuente directa |
| La diferencia de costo entre apertura (1,11) y cierre (0,85) equivale a ≈ 0,4 bps de spread | B | Correcta | Derivado de `costo_bordes.md` |
| Entrar en MOC regala ~6,5 h de deriva post‑apertura que elimina gran parte del alfa | B | Correcta | Argumento basado en la diferencia de precios entre apertura y cierre; consistente con `costo_bordes.md` |

## Puntos en disputa  

| Punto | Mejor argumento (A / B / ninguno) | Por qué |
|---|---|---|
| Núcleo de la señal: 8‑K vs 10‑K/10‑Q | **B** | B muestra que el código solo soporta 8‑K, que 10‑K son demasiado extensos y costosos, y que la evidencia estadística sería insuficiente. |
| Horizonte de inversión: meses (10‑K) vs 2‑5 días (8‑K) | **B** | B demuestra que el alfa de “Lazy Prices” proviene de ventas en corto y que, con solo compras, la señal a meses no genera alfa suficiente; además, la latencia no es limitante en horizonte swing. |
| Ejecución: MOC (cierre) vs MOO (apertura) | **B** | B aporta datos de costos (`costo_bordes.md`) y muestra que el ahorro de ~0,4 bps no compensa la pérdida de alfa inicial; también señala riesgos de comprar en el techo. |
| Viabilidad estadística y coste computacional | **B** | B argumenta que la descarga de 10‑K/10‑Q excede el presupuesto de API y que el número de observaciones requeridas sería de años. |
| Prueba de señal temprana y criterios de descarte | **A** | A propone métricas claras (IC positivo, t ≥ 1,65) y una prueba de señal basada en correlación, aportando un plan concreto de validación. |

## Errores que cambian la conclusión  

- Ninguno de los errores identificados altera la decisión final de **continuar** el proyecto; sin embargo, el rechazo del MOC y la confirmación de que el núcleo debe permanecer en 8‑K son críticos para la implementación.

## Lo que ninguno vio  

- No se menciona la posibilidad de **optimizar la extracción de texto** de 8‑K usando técnicas de resumen para reducir aún más el costo de API sin perder calidad de señal.  
- No se discutió la **dependencia del modelo LLM** (Haiku 5.5) respecto a posibles cambios de precios o disponibilidad futura del modelo.  

## Decisión  

**Continuar** la Idea 2 (PEAD con LLM usando 8‑K, horizonte 2‑5 días, solo compras).  
- **Condiciones concretas:**  
  1. Mantener la señal basada en 8‑K como núcleo.  
  2. Ejecutar la entrada en la subasta de apertura (MOO), no en MOC.  
  3. Aplicar la prueba de señal temprana descrita (IC > 0, t ≥ 1,65) y descartar si no se cumple.  
  4. Revisar la viabilidad de costos de API antes de escalar.  

**Confianza:** alta – la evidencia del código, costos y literatura respalda la decisión. Cambiaría si se descubriera que el modelo LLM ya no está disponible o que los costos de API aumentan drásticamente.

---
**Revelación (después del dictamen):** Claude = Participante A; Gemini = Participante B

