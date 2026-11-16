"""
Base del paso 2.9: arma lo que se le envía a un LLM por cada noticia, valida su
respuesta JSON y la registra en SQLite. El modelo del experimento es Claude Haiku 5.5
por API (--claude); también funciona con un modelo simulado (pruebas) y con modelos
locales servidos por Ollama (se probaron y quedaron fuera del experimento).

Diseño: "Instrucciones para que la IA lea noticias (paso 2.9), versión 1" en el
documento del proyecto. Las instrucciones van en inglés y no cambian durante el
experimento; si cambian, se sube VERSION_INSTRUCCIONES y empieza una cuenta nueva.

Regla:
  - Una noticia por llamada: titular, resumen, los primeros 2.000 caracteres del
    texto (sin etiquetas HTML), fuente, hora de publicación en Nueva York y, por
    cada símbolo del universo que menciona (sin los ETF), nombre y sector.
  - Sin símbolos del universo, o con más de MAX_SIMBOLOS símbolos en total (como variables.py), la noticia se omite.
  - No recibe precios ni nada posterior a la publicación.
  - La respuesta se valida (JSON, campos, tipos, rangos, un objeto por símbolo
    enviado y ninguno de más). Si es inválida se reintenta UNA vez; si vuelve a
    fallar queda registrada como "sin respuesta" (valido = 0 en el último intento),
    nunca se descarta en silencio.
  - La versión de la noticia es `updated_at`: si se corrige, es otra versión.
  - No se repite la misma noticia, versión, modelo y versión de instrucciones.
  - Con el histórico solo se comprueba formato, repetibilidad, latencia y costo;
    nunca si aciertan (el modelo ya conoce lo que pasó).

Uso:
    python lector_noticias.py --muestra 200                  # prueba con el modelo simulado (base temporal)
    python lector_noticias.py --muestra 200 --invalidas 0.3  # el simulado falla a veces (prueba el reintento)
    python lector_noticias.py --muestra 200 --mes 2025-03
    python lector_noticias.py --ver 62013450                 # instrucciones y entrada exactas de esa noticia
    python lector_noticias.py --probar                       # pruebas de la validación
    python lector_noticias.py --muestra 30 --claude                                     # Claude Haiku 5.5 por API (ANTHROPIC_API_KEY en .env)
    python lector_noticias.py --muestra 50 --ollama llama3.2:1b                          # Ollama en este equipo
    python lector_noticias.py --muestra 50 --ollama llama3.2:1b --url http://IP:11434   # Ollama en otro equipo
    --horizonte 60   minutos que entran en las instrucciones (por defecto 60)

Salida:
    datos/decisiones.sqlite (configurable con `procesar_noticia(..., conexion)`):
      noticias       (id, version, publicada_ny, fuente, titular, simbolos)
      respuestas_ia  (una fila por intento: modelo, tiempos, tokens, texto crudo, válido, motivo)
      evaluaciones_ia (una fila por símbolo con los campos ya leídos)
    `--muestra` usa siempre una base temporal y muestra un resumen en pantalla.

Ojo:
  - El nombre de la empresa no está en ningún dato del repositorio (la SEC se
    descarga por CIK sin nombre): está escrito a mano en NOMBRES. Si cambia el
    universo, hay que actualizarlo.
  - Los sectores se envían en inglés (traducidos de `descargar_datos.SECTOR`).
"""

import argparse
import hashlib
import html
import json
import random
import re
import sqlite3
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from descargar_datos import RAIZ, SECTOR, UNIVERSO

VERSION_INSTRUCCIONES = "v1"
MAX_CARACTERES = 2000
MAX_SIMBOLOS = 3                       # igual que variables.MAX_SIMBOLOS_POR_NOTICIA
HORIZONTE_DEFECTO = 60
BASE_DEFECTO = RAIZ / "decisiones.sqlite"
NY = ZoneInfo("America/New_York")

ETF = {"SPY", "QQQ", "IWM"}
ACCIONES = [s for s in UNIVERSO if s not in ETF]

TIPOS_EVENTO = ["resultados", "guia", "analista", "fusion_adquisicion", "legal_regulatorio",
                "producto_negocio", "directivos", "capital", "macro_sector", "movimiento_precio", "otro"]
DECISIONES = ["comprar", "vender", "nada"]

# Nombre de cada empresa, escrito a mano (no hay fuente en los datos descargados).
NOMBRES: dict[str, str] = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "GOOGL": "Alphabet (Google)", "AMZN": "Amazon",
    "META": "Meta Platforms", "AVGO": "Broadcom", "AMD": "Advanced Micro Devices", "ORCL": "Oracle", "CRM": "Salesforce",
    "ADBE": "Adobe", "INTC": "Intel", "JPM": "JPMorgan Chase", "BAC": "Bank of America", "GS": "Goldman Sachs",
    "MS": "Morgan Stanley", "WFC": "Wells Fargo", "V": "Visa", "MA": "Mastercard", "JNJ": "Johnson & Johnson",
    "UNH": "UnitedHealth Group", "PFE": "Pfizer", "MRK": "Merck & Co.", "ABBV": "AbbVie", "LLY": "Eli Lilly",
    "WMT": "Walmart", "COST": "Costco", "PG": "Procter & Gamble", "KO": "Coca-Cola", "PEP": "PepsiCo",
    "MCD": "McDonald's", "NKE": "Nike", "HD": "Home Depot", "TSLA": "Tesla", "XOM": "Exxon Mobil",
    "CVX": "Chevron", "COP": "ConocoPhillips", "CAT": "Caterpillar", "BA": "Boeing", "GE": "GE Aerospace",
    "HON": "Honeywell", "UPS": "United Parcel Service", "NEE": "NextEra Energy", "DUK": "Duke Energy",
    "SO": "Southern Company", "DIS": "Walt Disney", "NFLX": "Netflix", "T": "AT&T", "VZ": "Verizon", "LIN": "Linde",
}

SECTOR_EN = {"tecnologia": "technology", "financiero": "financials", "salud": "health care",
             "consumo": "consumer", "energia": "energy", "industrial": "industrials",
             "servicios_publicos": "utilities", "comunicaciones": "communication services",
             "materiales": "materials"}

INSTRUCCIONES = """You read one financial news item and rate its likely effect on the stock of each listed company over the next {horizonte} minutes of regular trading.
Use only the text given. Do not use any knowledge of what happened after the publication time. Judge each company separately.

For each company return an object with:
- "simbolo": the ticker.
- "relevancia": 0 = only mentioned in passing or in a list; 1 = about the company but minor; 2 = directly about something material for the company.
- "tono": integer from -2 (very negative) to 2 (very positive) for this company's stock; 0 if neutral or mixed.
- "tipo_evento": one of resultados (earnings), guia (guidance), analista (analyst rating or price target), fusion_adquisicion (M&A), legal_regulatorio (legal or regulatory), producto_negocio (products, contracts, operations), directivos (management changes), capital (buybacks, dividends, offerings, debt), macro_sector (macro or industry news), movimiento_precio (commentary on a price move that already happened), otro.
- "novedad": 1 if the item brings new information; 0 if it recaps known information or only comments on a price move.
- "sorpresa": 0 = expected or routine; 1 = somewhat unexpected; 2 = very unexpected.
- "decision": "comprar", "vender" or "nada" for the next {horizonte} minutes, after a trading cost of about 3 basis points.
- "retorno_esperado_bps": integer, expected return of the stock relative to the market over the next {horizonte} minutes, in basis points.
- "confianza": number from 0 to 1.
- "razon": one sentence, at most 20 words.

Answer only with JSON, no other text: {{"evaluaciones": [ ... one object per company ... ]}}"""


def instrucciones(horizonte: int = HORIZONTE_DEFECTO) -> str:
    return INSTRUCCIONES.format(horizonte=horizonte)


# ---------------------------------------------------------------- entrada por noticia

class _QuitaEtiquetas(HTMLParser):
    """Convierte HTML en texto plano con la biblioteca estándar."""
    BLOQUES = {"p", "div", "br", "h1", "h2", "h3", "h4", "li", "tr", "blockquote", "figure"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self._ignorar = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._ignorar += 1
        elif tag in self.BLOQUES:
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._ignorar = max(0, self._ignorar - 1)
        elif tag in self.BLOQUES:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self._ignorar:
            self.partes.append(data)


def texto_plano(contenido) -> str:
    """Quita etiquetas HTML, entidades y espacios repetidos."""
    if not isinstance(contenido, str) or not contenido:
        return ""
    p = _QuitaEtiquetas()
    p.feed(contenido)
    p.close()
    t = html.unescape("".join(p.partes)).replace("\xa0", " ")
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    return re.sub(r"\s*\n\s*", "\n", t).strip()


def simbolos_del_universo(simbolos) -> list[str]:
    """Símbolos de la noticia que están en el universo (sin ETF), en el orden del universo."""
    mencionados = set(simbolos) if simbolos is not None else set()
    return [s for s in ACCIONES if s in mencionados]


def armar_entrada(fila) -> tuple[str | None, list[str], str | None]:
    """De una fila de noticias devuelve (texto de entrada, símbolos enviados, motivo de omisión)."""
    simbolos = simbolos_del_universo(fila["symbols"])
    if not simbolos:
        return None, [], "sin símbolos del universo"
    # Igual que variables.py: cuenta todos los símbolos de la noticia, no solo los del universo.
    if len(fila["symbols"]) > MAX_SIMBOLOS:
        return None, simbolos, f"más de {MAX_SIMBOLOS} símbolos"
    publicada = pd.Timestamp(fila["created_at"]).tz_convert(NY).strftime("%Y-%m-%d %H:%M (New York)")
    cuerpo = texto_plano(fila["content"])[:MAX_CARACTERES]
    lineas = [f"Published: {publicada}",
              f"Source: {fila['source'] or 'unknown'}",
              f"Headline: {(fila['headline'] or '').strip()}",
              f"Summary: {texto_plano(fila['summary'])}",
              f"Text (first {MAX_CARACTERES} characters): {cuerpo}",
              "Companies:"]
    for s in simbolos:
        nombre = NOMBRES.get(s)
        lineas.append(f"- {s}" + (f" | {nombre}" if nombre else "") + f" | sector: {SECTOR_EN[SECTOR[s]]}")
    return "\n".join(lineas), simbolos, None


# ---------------------------------------------------------------- validación

def extraer_json(texto: str):
    """Primer objeto JSON con la clave 'evaluaciones', aunque venga entre texto o bloques ```."""
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", texto or ""):
        try:
            obj, _ = dec.raw_decode(texto[m.start():])
        except ValueError:
            continue
        if isinstance(obj, dict) and "evaluaciones" in obj:
            return obj
    return None


def _entero(v, lo=None, hi=None):
    """Entero (acepta 1.0, no bool ni texto) dentro de [lo, hi]; None si no cumple."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    if isinstance(v, float) and not v.is_integer():
        return None
    v = int(v)
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        return None
    return v


def validar_respuesta(texto: str, simbolos: list[str]) -> tuple[bool, list[dict], str]:
    """(válido, evaluaciones normalizadas, motivo del error). Un objeto por símbolo enviado."""
    obj = extraer_json(texto)
    if obj is None:
        return False, [], "no hay un JSON con la clave 'evaluaciones'"
    evs = obj["evaluaciones"]
    if not isinstance(evs, list):
        return False, [], "'evaluaciones' no es una lista"
    salida, vistos = [], set()
    for i, e in enumerate(evs):
        if not isinstance(e, dict):
            return False, [], f"evaluación {i} no es un objeto"
        s = e.get("simbolo")
        if not isinstance(s, str):
            return False, [], f"evaluación {i} sin 'simbolo'"
        s = s.strip().upper()
        if s not in simbolos:
            return False, [], f"símbolo extra: {s}"
        if s in vistos:
            return False, [], f"símbolo repetido: {s}"
        vistos.add(s)
        n = {"simbolo": s}
        for campo, lo, hi in [("relevancia", 0, 2), ("tono", -2, 2), ("novedad", 0, 1),
                              ("sorpresa", 0, 2), ("retorno_esperado_bps", None, None)]:
            if campo not in e:
                return False, [], f"{s}: falta '{campo}'"
            v = _entero(e[campo], lo, hi)
            if v is None:
                return False, [], f"{s}: '{campo}' inválido ({e[campo]!r})"
            n[campo] = v
        if e.get("tipo_evento") not in TIPOS_EVENTO:
            return False, [], f"{s}: 'tipo_evento' inválido ({e.get('tipo_evento')!r})"
        n["tipo_evento"] = e["tipo_evento"]
        if e.get("decision") not in DECISIONES:
            return False, [], f"{s}: 'decision' inválida ({e.get('decision')!r})"
        n["decision"] = e["decision"]
        c = e.get("confianza")
        if isinstance(c, bool) or not isinstance(c, (int, float)) or not 0 <= c <= 1:
            return False, [], f"{s}: 'confianza' inválida ({c!r})"
        n["confianza"] = float(c)
        r = e.get("razon")
        if not isinstance(r, str) or not r.strip():
            return False, [], f"{s}: 'razon' inválida"
        n["razon"] = " ".join(r.split()[:20])        # más de 20 palabras: se recorta, no se rechaza
        salida.append(n)
    faltan = [s for s in simbolos if s not in vistos]
    if faltan:
        return False, [], f"faltan símbolos: {', '.join(faltan)}"
    return True, salida, ""


# ---------------------------------------------------------------- modelos

class Modelo:
    """Interfaz de un modelo. `identificador` es la versión exacta (se registra en SQLite).
    Temperatura 0 y las mismas instrucciones para todos (parámetros fijos del diseño)."""
    nombre: str = ""
    identificador: str = ""

    def responder(self, instrucciones: str, entrada: str) -> tuple[str, int, int]:
        """Devuelve (texto de la respuesta, tokens de entrada, tokens de salida)."""
        raise NotImplementedError


MODELO_CLAUDE = "claude-haiku-5-5"
ESFUERZO_CLAUDE = "low"        # clasificar una noticia no necesita razonamiento largo; menos costo y latencia


def esquema_claude(simbolos: list[str]) -> dict:
    """El mismo esquema, con los rangos como listas de valores (la salida estructurada de la API
    no admite minimum/maximum ni minItems/maxItems). La validación de siempre revisa el resto."""
    e = esquema_respuesta(simbolos)
    obj = e["properties"]["evaluaciones"]["items"]
    for campo, (a, b) in {"relevancia": (0, 2), "tono": (-2, 2), "novedad": (0, 1), "sorpresa": (0, 2)}.items():
        obj["properties"][campo] = {"type": "integer", "enum": list(range(a, b + 1))}
    obj["properties"]["confianza"] = {"type": "number"}
    e["properties"]["evaluaciones"] = {"type": "array", "items": obj}
    return e


class ModeloClaude(Modelo):
    """Claude por la API de Anthropic (el modelo del experimento: Claude Haiku 5.5), con salida
    estructurada (esquema JSON) y esfuerzo bajo. La API ya no acepta temperatura, así que la
    repetibilidad se mide. Un error de la API, una negativa o una respuesta cortada cuentan como
    respuesta inválida: se reintenta y, si vuelve a fallar, queda como "sin respuesta"."""

    def __init__(self, modelo: str = MODELO_CLAUDE, esfuerzo: str = ESFUERZO_CLAUDE):
        import anthropic                       # solo hace falta si se usa Claude
        from descargar_datos import cargar_env
        cargar_env()                           # ANTHROPIC_API_KEY desde .env
        self._anthropic = anthropic
        self.cliente = anthropic.Anthropic(max_retries=2)
        self.nombre, self.esfuerzo = modelo, esfuerzo
        self.identificador = f"{modelo}@{esfuerzo}"

    def responder(self, instrucciones: str, entrada: str) -> tuple[str, int, int]:
        try:
            r = self.cliente.messages.create(
                model=self.nombre, max_tokens=2048, system=instrucciones,
                messages=[{"role": "user", "content": entrada}],
                output_config={"effort": self.esfuerzo,
                               "format": {"type": "json_schema", "schema": esquema_claude(simbolos_de_entrada(entrada))}})
        except self._anthropic.APIStatusError as e:
            return f"ERROR de la API de Claude ({e.status_code}): {e.message}", 0, 0
        except self._anthropic.APIConnectionError as e:
            return f"ERROR de conexión con Claude: {e}", 0, 0
        if r.model and r.model != self.nombre:
            self.identificador = f"{r.model}@{self.esfuerzo}"
        texto = next((b.text for b in r.content if b.type == "text"), "")
        if r.stop_reason in ("refusal", "max_tokens"):
            texto = f"ERROR: la respuesta terminó por {r.stop_reason}. {texto}"
        return texto, r.usage.input_tokens, r.usage.output_tokens

def simbolos_de_entrada(entrada: str) -> list[str]:
    """Los símbolos que armar_entrada puso después de 'Companies:'."""
    return re.findall(r"^- ([A-Z.]+)", entrada.rsplit("\nCompanies:\n", 1)[-1], flags=re.M)


def esquema_respuesta(simbolos: list[str]) -> dict:
    """Esquema JSON de la respuesta: el modelo solo puede devolver una lista con un objeto por
    símbolo enviado, con los valores permitidos. No cambia las instrucciones; evita respuestas
    mal formadas. La validación de siempre se sigue aplicando después."""
    entero = lambda a, b: {"type": "integer", "minimum": a, "maximum": b}
    objeto = {"type": "object", "additionalProperties": False,
              "properties": {"simbolo": {"type": "string", "enum": simbolos}, "relevancia": entero(0, 2),
                             "tono": entero(-2, 2), "tipo_evento": {"type": "string", "enum": TIPOS_EVENTO},
                             "novedad": entero(0, 1), "sorpresa": entero(0, 2),
                             "decision": {"type": "string", "enum": DECISIONES},
                             "retorno_esperado_bps": {"type": "integer"}, "confianza": {"type": "number", "minimum": 0, "maximum": 1},
                             "razon": {"type": "string"}},
              "required": ["simbolo", "relevancia", "tono", "tipo_evento", "novedad", "sorpresa", "decision",
                           "retorno_esperado_bps", "confianza", "razon"]}
    return {"type": "object", "additionalProperties": False, "required": ["evaluaciones"],
            "properties": {"evaluaciones": {"type": "array", "items": objeto, "minItems": len(simbolos), "maxItems": len(simbolos)}}}


class ModeloOllama(Modelo):
    """Modelo local servido por Ollama (API HTTP, por defecto en el puerto 11434).
    Pide salida con el esquema JSON de la respuesta (`format`), temperatura 0 y semilla fija. Un error de red o
    de tiempo cuenta como respuesta inválida: se reintenta y, si vuelve a fallar, queda
    como "sin respuesta"."""

    def __init__(self, modelo: str, url: str = "http://localhost:11434", tiempo_max: float = 300.0):
        self.nombre, self.url, self.tiempo_max = modelo, url.rstrip("/"), tiempo_max
        self.identificador = modelo
        try:      # la versión exacta: el resumen (digest) del modelo descargado
            etiquetas = self._pedir("/api/tags", None, 10.0)
            digest = next((m.get("digest", "") for m in etiquetas.get("models", []) if m.get("name") == modelo), "")
            if digest:
                self.identificador = f"{modelo}@{digest[:12]}"
        except Exception:  # noqa: BLE001
            pass

    def _pedir(self, ruta: str, cuerpo: dict | None, tiempo: float) -> dict:
        datos = None if cuerpo is None else json.dumps(cuerpo).encode()
        req = urllib.request.Request(self.url + ruta, data=datos, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=tiempo) as r:
            return json.loads(r.read().decode())

    def responder(self, instrucciones: str, entrada: str) -> tuple[str, int, int]:
        simbolos = simbolos_de_entrada(entrada)
        cuerpo = {"model": self.nombre, "stream": False, "format": esquema_respuesta(simbolos),
                  "options": {"temperature": 0, "seed": 7},
                  "messages": [{"role": "system", "content": instrucciones}, {"role": "user", "content": entrada}]}
        try:
            r = self._pedir("/api/chat", cuerpo, self.tiempo_max)
        except Exception as e:  # noqa: BLE001
            return f"ERROR de conexión con Ollama: {e}", 0, 0
        return r.get("message", {}).get("content", ""), int(r.get("prompt_eval_count", 0)), int(r.get("eval_count", 0))


class ModeloSimulado(Modelo):
    """Respuestas deterministas a partir de la noticia. Con `prob_invalida` > 0 a veces
    devuelve basura, para probar el reintento (también de forma determinista)."""
    nombre = "simulado"
    identificador = "simulado-1"

    def __init__(self, prob_invalida: float = 0.0):
        self.prob_invalida = prob_invalida
        self._llamadas: dict[str, int] = {}

    def responder(self, instrucciones: str, entrada: str) -> tuple[str, int, int]:
        n = self._llamadas.get(entrada, 0)
        self._llamadas[entrada] = n + 1
        semilla = int(hashlib.sha256(entrada.encode()).hexdigest(), 16)
        simbolos = simbolos_de_entrada(entrada)
        if random.Random(f"{semilla}-{n}-inv").random() < self.prob_invalida:
            texto = random.Random(f"{semilla}-{n}-tipo").choice([
                "Sorry, I cannot rate this news.",
                '{"evaluaciones": [{"simbolo": "' + (simbolos[0] if simbolos else "X") + '", "tono": 7}]}',
                'Here is the answer: {"evaluaciones": [ ',          # JSON cortado
            ])
        else:
            evs = []
            for s in simbolos:
                r = random.Random(f"{semilla}-{s}")             # no depende del intento
                tono = r.randint(-2, 2)
                evs.append({"simbolo": s, "relevancia": r.randint(0, 2), "tono": tono,
                            "tipo_evento": r.choice(TIPOS_EVENTO), "novedad": r.randint(0, 1),
                            "sorpresa": r.randint(0, 2),
                            "decision": "comprar" if tono > 0 else "vender" if tono < 0 else "nada",
                            "retorno_esperado_bps": tono * r.randint(2, 8),
                            "confianza": round(r.random(), 2), "razon": "Respuesta simulada."})
            texto = "```json\n" + json.dumps({"evaluaciones": evs}) + "\n```"
        return texto, (len(instrucciones) + len(entrada)) // 4, len(texto) // 4


# ---------------------------------------------------------------- SQLite

ESQUEMA = """
CREATE TABLE IF NOT EXISTS noticias (
    id INTEGER, version TEXT, publicada_ny TEXT, fuente TEXT, titular TEXT, simbolos TEXT,
    PRIMARY KEY (id, version));
CREATE TABLE IF NOT EXISTS respuestas_ia (
    noticia INTEGER, version_noticia TEXT, modelo TEXT, identificador_modelo TEXT,
    version_instrucciones TEXT, horizonte_min INTEGER, intento INTEGER,
    enviada_utc TEXT, recibida_utc TEXT, latencia_ms INTEGER,
    tokens_entrada INTEGER, tokens_salida INTEGER, texto_crudo TEXT, valido INTEGER, motivo_error TEXT,
    PRIMARY KEY (noticia, version_noticia, modelo, version_instrucciones, intento));
CREATE TABLE IF NOT EXISTS evaluaciones_ia (
    noticia INTEGER, version_noticia TEXT, modelo TEXT, version_instrucciones TEXT, simbolo TEXT,
    relevancia INTEGER, tono INTEGER, tipo_evento TEXT, novedad INTEGER, sorpresa INTEGER,
    decision TEXT, retorno_esperado_bps INTEGER, confianza REAL, razon TEXT,
    PRIMARY KEY (noticia, version_noticia, modelo, version_instrucciones, simbolo));
"""


def abrir_base(ruta=BASE_DEFECTO) -> sqlite3.Connection:
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    con.executescript(ESQUEMA)
    return con


def _ahora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def procesar_noticia(con, modelo: Modelo, fila, horizonte: int = HORIZONTE_DEFECTO) -> dict:
    """Envía, mide, valida, reintenta una vez y registra. Devuelve un dict con `estado`:
    'omitida', 'repetida', 'primer_intento', 'reintento' o 'sin_respuesta'."""
    entrada, simbolos, motivo = armar_entrada(fila)
    if entrada is None:
        return {"estado": "omitida", "motivo": motivo, "caracteres": 0}
    version = pd.Timestamp(fila["updated_at"]).isoformat()
    clave = (int(fila["id"]), version, modelo.nombre, VERSION_INSTRUCCIONES)
    if con.execute("SELECT 1 FROM respuestas_ia WHERE noticia=? AND version_noticia=? AND modelo=? "
                   "AND version_instrucciones=? LIMIT 1", clave).fetchone():
        return {"estado": "repetida", "caracteres": len(entrada)}
    con.execute("INSERT OR IGNORE INTO noticias VALUES (?,?,?,?,?,?)",
                (int(fila["id"]), version, pd.Timestamp(fila["created_at"]).tz_convert(NY).isoformat(),
                 fila["source"], fila["headline"], ",".join(simbolos)))
    texto_instr = instrucciones(horizonte)
    estado = "sin_respuesta"
    for intento in (1, 2):
        enviada = _ahora_utc()
        t0 = time.perf_counter()
        texto, tok_in, tok_out = modelo.responder(texto_instr, entrada)
        latencia = round((time.perf_counter() - t0) * 1000)
        recibida = _ahora_utc()
        valido, evs, error = validar_respuesta(texto, simbolos)
        con.execute("INSERT INTO respuestas_ia VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (*clave[:3], modelo.identificador, VERSION_INSTRUCCIONES, horizonte, intento,
                     enviada, recibida, latencia, tok_in, tok_out, texto, int(valido), error))
        if valido:
            for e in evs:
                con.execute("INSERT OR REPLACE INTO evaluaciones_ia VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (*clave[:3], VERSION_INSTRUCCIONES, e["simbolo"], e["relevancia"], e["tono"],
                             e["tipo_evento"], e["novedad"], e["sorpresa"], e["decision"],
                             e["retorno_esperado_bps"], e["confianza"], e["razon"]))
            estado = "primer_intento" if intento == 1 else "reintento"
            break
    con.commit()
    return {"estado": estado, "caracteres": len(entrada)}


# ---------------------------------------------------------------- línea de comandos

def cargar_mes(mes: str | None) -> pd.DataFrame:
    archivos = sorted((RAIZ / "noticias").glob("*.parquet"))
    a = (RAIZ / "noticias" / f"{mes}.parquet") if mes else archivos[-1]
    if not a.exists():
        sys.exit(f"No existe {a}")
    print(f"Mes: {a.stem}")
    return pd.read_parquet(a).drop_duplicates("id")


def repetibilidad(filas: pd.DataFrame, modelo: Modelo, horizonte: int) -> None:
    """Procesa cada noticia dos veces (en bases distintas) y cuenta cuántas evaluaciones coinciden, campo por campo."""
    campos = ["relevancia", "tono", "tipo_evento", "novedad", "sorpresa", "decision", "retorno_esperado_bps"]
    vueltas = []
    with tempfile.TemporaryDirectory() as carpeta:
        for i in (1, 2):
            con = abrir_base(Path(carpeta) / f"vuelta{i}.sqlite")
            for _, f in filas.iterrows():
                procesar_noticia(con, modelo, f, horizonte)
            vueltas.append(pd.read_sql(f"SELECT noticia, simbolo, {', '.join(campos)}, confianza FROM evaluaciones_ia", con))
            con.close()
    x = vueltas[0].merge(vueltas[1], on=["noticia", "simbolo"], suffixes=("_1", "_2"))
    if x.empty:
        print("Repetibilidad: sin evaluaciones válidas en las dos vueltas.")
        return
    iguales = {c: (x[f"{c}_1"] == x[f"{c}_2"]).mean() for c in campos}
    todo = (x[[f"{c}_1" for c in campos]].values == x[[f"{c}_2" for c in campos]].values).all(axis=1).mean()
    print(f"Repetibilidad ({len(x)} evaluaciones procesadas dos veces): todos los campos iguales en {100 * todo:.0f}%")
    print("  " + ", ".join(f"{c} {100 * v:.0f}%" for c, v in iguales.items())
          + f"; confianza: diferencia media {(x['confianza_1'] - x['confianza_2']).abs().mean():.2f}")


def muestra(n: int, mes: str | None, horizonte: int, prob_invalida: float, modelo: Modelo | None = None,
            repetir: bool = False) -> None:
    noticias = cargar_mes(mes)
    idx = random.Random(42).sample(range(len(noticias)), min(n, len(noticias)))
    filas = noticias.iloc[idx]
    modelo = modelo or ModeloSimulado(prob_invalida)
    with tempfile.TemporaryDirectory() as carpeta:
        con = abrir_base(Path(carpeta) / "prueba.sqlite")
        res = [procesar_noticia(con, modelo, f, horizonte) for _, f in filas.iterrows()]
        n_resp = con.execute("SELECT COUNT(*) FROM respuestas_ia").fetchone()[0]
        n_eval = con.execute("SELECT COUNT(*) FROM evaluaciones_ia").fetchone()[0]
        lat = pd.read_sql("SELECT latencia_ms, tokens_entrada, tokens_salida, valido, motivo_error, texto_crudo FROM respuestas_ia", con)
        con.close()
    df = pd.DataFrame(res)
    omitidas = df[df["estado"] == "omitida"]
    enviadas = df[df["estado"] != "omitida"]
    print(f"Noticias de la muestra: {len(df)}  (modelo {modelo.identificador}, prob. inválida {prob_invalida})")
    print(f"Omitidas: {len(omitidas)}")
    for motivo, c in (omitidas["motivo"].value_counts().items() if len(omitidas) else []):
        print(f"  - {motivo}: {c}")
    if len(enviadas):
        car = enviadas["caracteres"].mean()
        print(f"Procesadas: {len(enviadas)}")
        print(f"Caracteres medios de la entrada: {car:.0f}  (tokens estimados ~{car / 4:.0f}; "
              f"más las instrucciones ~{len(instrucciones(horizonte)) / 4:.0f})")
        print(f"Válidas al primer intento: {(enviadas['estado'] == 'primer_intento').sum()}")
        print(f"Válidas tras reintentar:   {(enviadas['estado'] == 'reintento').sum()}")
        print(f"Sin respuesta:             {(enviadas['estado'] == 'sin_respuesta').sum()}")
    print(f"Filas en la base temporal: respuestas_ia {n_resp}, evaluaciones_ia {n_eval}")
    if len(lat):
        q = lat["latencia_ms"].quantile([0.5, 0.9]).values / 1000
        print(f"Latencia por intento: mediana {q[0]:.1f} s, 90% {q[1]:.1f} s, máxima {lat['latencia_ms'].max() / 1000:.1f} s; "
              f"tokens medios: entrada {lat['tokens_entrada'].mean():.0f}, salida {lat['tokens_salida'].mean():.0f}")
        malas = lat[lat["valido"] == 0]
        conexion = malas["texto_crudo"].str.startswith("ERROR")
        if conexion.any():
            print(f"  ¡{conexion.sum()} intentos con error del modelo o de conexión! Ejemplo: {malas.loc[conexion, 'texto_crudo'].iloc[0][:200]}")
        for motivo, c in malas.loc[~conexion, "motivo_error"].value_counts().head(5).items():
            print(f"  error: {motivo} ({c})")
        if (~conexion).any():
            print(f"  Ejemplo de respuesta inválida: {malas.loc[~conexion, 'texto_crudo'].iloc[0][:300]!r}")
    if repetir:
        repetibilidad(filas, modelo, horizonte)


def ver(id_noticia: int, horizonte: int) -> None:
    for a in sorted((RAIZ / "noticias").glob("*.parquet")):
        n = pd.read_parquet(a)
        f = n[n["id"] == id_noticia]
        if len(f):
            fila = f.iloc[0]
            entrada, simbolos, motivo = armar_entrada(fila)
            if entrada is None:
                sys.exit(f"Noticia {id_noticia} ({a.stem}) omitida: {motivo}")
            print(f"=== INSTRUCCIONES ({VERSION_INSTRUCCIONES}, horizonte {horizonte}) ===")
            print(instrucciones(horizonte))
            print(f"\n=== ENTRADA (noticia {id_noticia}, {a.stem}, versión {pd.Timestamp(fila['updated_at']).isoformat()}) ===")
            print(entrada)
            return
    sys.exit(f"No encontré la noticia {id_noticia}")


def probar() -> None:
    """Pruebas mínimas de la validación y del proceso."""
    ev = lambda s, **k: {"simbolo": s, "relevancia": 2, "tono": 1, "tipo_evento": "resultados", "novedad": 1,
                         "sorpresa": 0, "decision": "comprar", "retorno_esperado_bps": 5,
                         "confianza": 0.7, "razon": "Beat.", **k}
    js = lambda *e: json.dumps({"evaluaciones": list(e)})
    ok, evs, _ = validar_respuesta("Claro:\n```json\n" + js(ev("AAPL")) + "\n```\nListo.", ["AAPL"])
    assert ok and evs[0]["simbolo"] == "AAPL", "JSON rodeado de texto"
    for malo, simbolos, parte in [
        (js(ev("AAPL", tono=3)), ["AAPL"], "tono"),
        (js(ev("AAPL", confianza=1.5)), ["AAPL"], "confianza"),
        (js(ev("AAPL", relevancia=1.5)), ["AAPL"], "relevancia"),
        (js(ev("AAPL", tipo_evento="rumor")), ["AAPL"], "tipo_evento"),
        (js(ev("AAPL"), ev("MSFT")), ["AAPL"], "extra"),
        (js(ev("AAPL")), ["AAPL", "MSFT"], "faltan"),
        ("no es json", ["AAPL"], "JSON"),
    ]:
        ok, _, motivo = validar_respuesta(malo, simbolos)
        assert not ok and parte in motivo, (parte, motivo)
    # proceso completo: con prob. 1 siempre falla (sin respuesta); con 0 siempre acierta
    fila = pd.Series({"id": 1, "created_at": pd.Timestamp("2024-01-02 15:00", tz="UTC"),
                      "updated_at": pd.Timestamp("2024-01-02 15:00", tz="UTC"), "headline": "Apple up",
                      "summary": "s", "content": "<p>Hola &amp; <b>adiós</b></p>", "source": "x",
                      "symbols": ["AAPL", "SPY"]})
    assert "Hola & adiós" in armar_entrada(fila)[0] and "SPY" not in armar_entrada(fila)[0].split("Companies:")[1]
    con = abrir_base(":memory:")
    assert procesar_noticia(con, ModeloSimulado(1.0), fila)["estado"] == "sin_respuesta"
    assert con.execute("SELECT COUNT(*) FROM respuestas_ia").fetchone()[0] == 2
    fila["id"] = 2
    assert procesar_noticia(con, ModeloSimulado(0.0), fila)["estado"] == "primer_intento"
    assert procesar_noticia(con, ModeloSimulado(0.0), fila)["estado"] == "repetida"
    print("Pruebas de validación y proceso: OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--muestra", type=int, help="procesa N noticias al azar con el modelo simulado")
    ap.add_argument("--mes", help="mes de la muestra, AAAA-MM (por defecto el último archivo)")
    ap.add_argument("--ver", type=int, help="id de la noticia: imprime instrucciones y entrada")
    ap.add_argument("--horizonte", type=int, default=HORIZONTE_DEFECTO, help="minutos del horizonte")
    ap.add_argument("--invalidas", type=float, default=0.0, help="prob. de que el simulado responda mal")
    ap.add_argument("--probar", action="store_true", help="ejecuta las pruebas de la validación")
    ap.add_argument("--ollama", help="modelo de Ollama para --muestra en vez del simulado, por ejemplo llama3.2:1b")
    ap.add_argument("--url", default="http://localhost:11434", help="dirección del servidor de Ollama")
    ap.add_argument("--claude", action="store_true", help=f"usa Claude por API ({MODELO_CLAUDE}) en --muestra")
    ap.add_argument("--repetir", action="store_true", help="en --muestra, procesa cada noticia dos veces más y mide si coinciden")
    a = ap.parse_args()
    if a.probar:
        probar()
    elif a.ver is not None:
        ver(a.ver, a.horizonte)
    elif a.muestra:
        modelo = ModeloClaude() if a.claude else ModeloOllama(a.ollama, a.url) if a.ollama else None
        muestra(a.muestra, a.mes, a.horizonte, a.invalidas, modelo, a.repetir)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
