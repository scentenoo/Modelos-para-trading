# Protocolo de debate Claude ↔ Gemini

Objetivo: generar y filtrar **ideas** para el proyecto, no ejecutar código.
Samir pone el tema y decide; las IAs proponen, critican y sintetizan.

## Participantes
- **Claude** (Claude Code, Opus) — orquesta: abre el hilo, llama a Gemini, escribe la síntesis.
- **Gemini** (Antigravity CLI `agy`, modelo `gemini-3.8-flash-high`, modo `plan`, solo lectura).

## Formato del hilo
Un archivo por debate: `debate/AAAA-MM-DD-tema.md`, con estas secciones:

1. `## Tema` — la pregunta concreta de Samir.
2. `## Ronda N — Claude` / `## Ronda N — Gemini` — turnos alternados (2–3 rondas).
3. `## Síntesis` — acuerdos, desacuerdos que siguen abiertos, y lista de ideas
   ordenadas por (valor esperado × facilidad de probar), cada una con
   **cómo se probaría** y **qué resultado la descartaría**.

## Reglas
- **Criticar obligatoriamente**: cada turno empieza señalando el punto más débil del turno anterior. Prohibido el acuerdo de cortesía.
- **Anclar en el repo**: toda afirmación sobre el proyecto cita archivo o resultado (`archivo.py`, `resultados/...`, sección del documento). Si es una suposición, se dice.
- **Respetar lo ya decidido**: no reabrir decisiones del documento salvo con un argumento nuevo y explícito.
- **Cuidar los datos**: ninguna idea debe proponer volver a mirar la muestra final de la Fase 2 para ajustar algo; eso la contamina.
- **Solo lectura**: ninguna IA modifica código ni datos durante el debate. Lo que se decida implementar se hace después, aparte.
- Turnos breves: máximo ~400 palabras.

## Cómo se llama a Gemini
```powershell
.\debate\gemini.ps1 debate\2026-11-17-tema.md
```
El script le pide a Gemini que lea el protocolo y el hilo, y devuelve su turno; Claude lo agrega al archivo.

## Juez
Juez único: **una sesión independiente de Claude Opus 5.5** (`claude -p`), sin acceso a la conversación del debate, que solo puede leer archivos y buscar en la web. Su decisión es la que se adopta, sin revisión de los participantes: elige, punto por punto, la posición con los mejores argumentos. Instrucciones en `debate/JUEZ.md`.
```powershell
.\debate\juez.ps1 debate\<hilo>.md
```
1. Anonimiza el debate: Claude y Gemini pasan a "Participante A/B", asignados al azar. El mapa queda fuera del repo (`%LOCALAPPDATA%\debate-mapas`).
2. Copia el documento, `resultados/`, el código y el debate anonimizado a una carpeta aislada fuera del repo, para que el juez no pueda abrir el original. Ahí solo puede leer archivos.
3. Guarda el dictamen como `debate/<hilo>.dictamen.md` y recién al final revela quién era quién.
