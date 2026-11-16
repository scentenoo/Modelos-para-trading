"""
Lee noticias en vivo: cada cierto tiempo pide a Alpaca las noticias nuevas de las acciones del
universo, anota cuándo llegó cada una y la pasa por la IA (Claude Haiku 5.5) con la misma
entrada, validación y base SQLite de `lector_noticias.py`. Es el ensayo en vivo del paso 2.9:
lo que se mide aquí es el retraso real entre la publicación y la decisión.

Regla:
  - Cada `--intervalo` segundos (60 por defecto) pide las noticias publicadas o actualizadas desde
    el final de la consulta anterior menos SOLAPE_MIN minutos (para no perder ninguna). Si la
    consulta falla, la marca no avanza y la siguiente vuelta cubre el hueco.
  - Una noticia es nueva si su (id, updated_at) no está en `llegadas`. Una noticia corregida (mismo
    id, otro updated_at) es una versión nueva y se procesa otra vez.
  - `llegada_utc` es la hora (UTC, con milisegundos) en que este proceso recibió la respuesta de
    Alpaca que traía la noticia; no es la hora de publicación (`created_at`).
  - Se procesa con `lector_noticias.procesar_noticia` (mismas instrucciones, validación,
    reintento único y registro). Las omitidas (sin símbolos del universo, más de 3 símbolos) también
    quedan en `llegadas`, con su motivo.
  - Un error de red de Alpaca o de la base no tumba el proceso: se registra y se reintenta en la
    vuelta siguiente. Un error de Claude queda como respuesta inválida (como siempre) y, si falla
    los dos intentos, como "sin respuesta"; esa versión no se vuelve a enviar.
  - Al arrancar y cada hora se imprime un resumen: noticias del día (UTC) y costo estimado con
    $0,10 por millón de tokens de entrada y $0,50 por millón de salida.

Uso:
    python noticias_vivo.py                                   # sin parar, Claude, cada 60 s
    python noticias_vivo.py --intervalo 30 --horizonte 60
    python noticias_vivo.py --una-vez --simulado --desde "2026-11-16 14:00"   # prueba sin gastar
    python noticias_vivo.py --una-vez --base datos/prueba.sqlite              # una consulta y termina
    --desde "AAAA-MM-DD HH:MM"  UTC; por defecto la última llegada de la base o, si está vacía, hace 10 min

Salida:
    datos/decisiones.sqlite (--base): las tablas de lector_noticias.py más
      llegadas (noticia, version, llegada_utc, created_at, updated_at, symbols, estado, motivo)
        estado: 'omitida' o 'enviada'. version = updated_at en ISO, como en `procesar_noticia`.
    datos/registros/noticias_vivo.log: un archivo por día (rota a medianoche UTC, guarda 30).
      Por vuelta: consultas, noticias nuevas, procesadas, válidas, sin respuesta, latencia, tokens, errores.

Servicio de systemd en Debian (usuario samir; repo en /home/samir/Modelos-para-trading con su .venv).
Crear /etc/systemd/system/noticias-vivo.service con:

    [Unit]
    Description=Lector de noticias en vivo (Claude Haiku 5.5)
    After=network-online.target
    Wants=network-online.target

    [Service]
    Type=simple
    User=samir
    WorkingDirectory=/home/samir/Modelos-para-trading
    Environment=PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
    ExecStart=/home/samir/Modelos-para-trading/.venv/bin/python noticias_vivo.py --intervalo 60
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target

y activarlo con:
    sudo systemctl daemon-reload
    sudo systemctl enable --now noticias-vivo
    systemctl status noticias-vivo          # estado
    journalctl -u noticias-vivo -f          # salida en pantalla
(las claves de Alpaca y de Anthropic se leen de /home/samir/Modelos-para-trading/.env).

Ojo:
  - Alpaca filtra por fecha de actualización: una noticia vieja corregida llega como versión nueva.
  - Si el proceso estuvo parado, al volver arranca desde la última llegada de la base (menos el
    solape): cubre el hueco, pero procesa de golpe todo lo acumulado.
  - Si Claude falla en los dos intentos, la versión queda "sin respuesta" y no se reenvía sola.
"""

import argparse
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from logging.handlers import TimedRotatingFileHandler

import pandas as pd

import lector_noticias as ln
from descargar_datos import RAIZ, UNIVERSO, cargar_env
from descargar_noticias import COLUMNAS

INTERVALO_DEFECTO = 60
SOLAPE_MIN = 5
VENTANA_INICIAL_MIN = 10
PRECIO_ENTRADA = 0.10 / 1e6      # dólares por token de entrada (Haiku 5.5)
PRECIO_SALIDA = 0.50 / 1e6       # dólares por token de salida
CARPETA_LOG = RAIZ / "registros"
RESUMEN_CADA_S = 3600

log = logging.getLogger("noticias_vivo")

ESQUEMA_LLEGADAS = """
CREATE TABLE IF NOT EXISTS llegadas (
    noticia INTEGER, version TEXT, llegada_utc TEXT, created_at TEXT, updated_at TEXT, symbols TEXT,
    estado TEXT, motivo TEXT,
    PRIMARY KEY (noticia, version));
"""


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat(timespec="milliseconds")


def configurar_log() -> None:
    CARPETA_LOG.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fmt.converter = time.gmtime
    archivo = TimedRotatingFileHandler(CARPETA_LOG / "noticias_vivo.log", when="midnight", utc=True,
                                       backupCount=30, encoding="utf-8")
    pantalla = logging.StreamHandler(sys.stdout)
    for h in (archivo, pantalla):
        h.setFormatter(fmt)
        log.addHandler(h)
    log.setLevel(logging.INFO)


def abrir(ruta) -> sqlite3.Connection:
    con = ln.abrir_base(ruta)
    con.executescript(ESQUEMA_LLEGADAS)
    return con


# ---------------------------------------------------------------- consulta a Alpaca

def crear_consulta():
    """Devuelve consulta(simbolos, inicio, fin) -> DataFrame de noticias (puede lanzar excepciones de red)."""
    from alpaca.data.historical.news import NewsClient
    from alpaca.data.requests import NewsRequest
    cargar_env()
    llave, secreto = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not llave or not secreto:
        sys.exit("Faltan APCA_API_KEY_ID y APCA_API_SECRET_KEY (ver descargar_datos.py).")
    cli = NewsClient(llave, secreto)

    def consulta(simbolos, inicio, fin) -> pd.DataFrame:
        req = NewsRequest(symbols=",".join(simbolos), start=inicio, end=fin, include_content=True, sort="asc")
        noticias = cli.get_news(req).data.get("news", [])
        if not noticias:
            return pd.DataFrame(columns=COLUMNAS)
        df = pd.DataFrame([n.model_dump(mode="json", include=set(COLUMNAS)) for n in noticias])[COLUMNAS]
        for col in ("created_at", "updated_at"):
            df[col] = pd.to_datetime(df[col], utc=True)
        return df

    return consulta


# ---------------------------------------------------------------- una vuelta

def ciclo(con, modelo, consulta, inicio: datetime, horizonte: int) -> tuple[bool, dict]:
    """Una consulta + procesamiento. Devuelve (consulta_ok, estadísticas). No lanza excepciones."""
    est = {"consultas": 1, "traidas": 0, "nuevas": 0, "omitidas": 0, "procesadas": 0, "validas": 0,
           "sin_respuesta": 0, "errores": 0}
    t_inicio = _iso(_ahora())
    try:
        df = consulta(UNIVERSO, inicio, _ahora())
    except Exception as e:  # noqa: BLE001
        log.error("Alpaca: la consulta falló (%s: %s); se reintenta en la próxima vuelta", type(e).__name__, e)
        est["errores"] += 1
        return False, est
    llegada = _iso(_ahora())
    df = df.drop_duplicates(subset=["id", "updated_at"]).sort_values("created_at", ignore_index=True)
    est["traidas"] = len(df)
    for _, fila in df.iterrows():
        version = pd.Timestamp(fila["updated_at"]).isoformat()
        try:
            if con.execute("SELECT 1 FROM llegadas WHERE noticia=? AND version=?", (int(fila["id"]), version)).fetchone():
                continue
            est["nuevas"] += 1
            r = ln.procesar_noticia(con, modelo, fila, horizonte)
            omitida = r["estado"] == "omitida"
            con.execute("INSERT OR IGNORE INTO llegadas VALUES (?,?,?,?,?,?,?,?)",
                        (int(fila["id"]), version, llegada, pd.Timestamp(fila["created_at"]).isoformat(), version,
                         ",".join(fila["symbols"]), "omitida" if omitida else "enviada", r.get("motivo")))
            con.commit()
            if omitida:
                est["omitidas"] += 1
            elif r["estado"] != "repetida":
                est["procesadas"] += 1
                if r["estado"] == "sin_respuesta":
                    est["sin_respuesta"] += 1
                else:
                    est["validas"] += 1
        except Exception as e:  # noqa: BLE001
            est["errores"] += 1
            log.error("noticia %s: error al procesar (%s: %s); se reintenta en la próxima vuelta",
                      fila["id"], type(e).__name__, e)
            try:
                con.rollback()
            except sqlite3.Error:
                pass
    lat = con.execute("SELECT COUNT(*), AVG(latencia_ms), MAX(latencia_ms), COALESCE(SUM(tokens_entrada),0), "
                      "COALESCE(SUM(tokens_salida),0) FROM respuestas_ia WHERE enviada_utc >= ?", (t_inicio,)).fetchone()
    est["intentos"], est["lat_media"], est["lat_max"], est["tok_in"], est["tok_out"] = lat
    log.info("consultas=%d traidas=%d nuevas=%d omitidas=%d procesadas=%d validas=%d sin_respuesta=%d errores=%d "
             "intentos=%d latencia_media_ms=%s latencia_max_ms=%s tokens_entrada=%d tokens_salida=%d",
             est["consultas"], est["traidas"], est["nuevas"], est["omitidas"], est["procesadas"], est["validas"],
             est["sin_respuesta"], est["errores"], est["intentos"],
             "-" if est["lat_media"] is None else round(est["lat_media"]), est["lat_max"] if est["lat_max"] is not None else "-",
             est["tok_in"], est["tok_out"])
    return True, est


def resumen(con) -> None:
    """Noticias del día (UTC) y costo estimado."""
    dia = _ahora().strftime("%Y-%m-%d")
    n, omit = con.execute("SELECT COUNT(*), COALESCE(SUM(estado='omitida'),0) FROM llegadas WHERE llegada_utc >= ?", (dia,)).fetchone()
    ti, to, nr = con.execute("SELECT COALESCE(SUM(tokens_entrada),0), COALESCE(SUM(tokens_salida),0), COUNT(*) "
                             "FROM respuestas_ia WHERE enviada_utc >= ?", (dia,)).fetchone()
    costo = ti * PRECIO_ENTRADA + to * PRECIO_SALIDA
    log.info("RESUMEN %s UTC: noticias %d (omitidas %d), llamadas al modelo %d, tokens %d entrada / %d salida, "
             "costo estimado $%.4f", dia, n, omit, nr, ti, to, costo)


def desde_defecto(con) -> datetime:
    ultima = con.execute("SELECT MAX(llegada_utc) FROM llegadas").fetchone()[0]
    if ultima:
        return pd.Timestamp(ultima).to_pydatetime()
    return _ahora() - timedelta(minutes=VENTANA_INICIAL_MIN)


def correr(con, modelo, consulta, desde: datetime, intervalo: int, horizonte: int, una_vez: bool,
           solape_primera: bool = True) -> None:
    resumen(con)
    proximo_resumen = time.monotonic() + RESUMEN_CADA_S
    marca = desde                                       # hasta dónde se cubrió con una consulta que salió bien
    solape = timedelta(minutes=SOLAPE_MIN)
    primera = True
    while True:
        t0 = time.monotonic()
        fin = _ahora()
        inicio = marca - (solape if (not primera or solape_primera) else timedelta(0))
        try:
            ok, _ = ciclo(con, modelo, consulta, inicio, horizonte)
            if ok:
                marca = fin
        except Exception as e:  # noqa: BLE001
            log.error("vuelta fallida (%s: %s); se reintenta", type(e).__name__, e)
        primera = False
        if una_vez:
            return
        if time.monotonic() >= proximo_resumen:
            resumen(con)
            proximo_resumen += RESUMEN_CADA_S
        time.sleep(max(0.0, intervalo - (time.monotonic() - t0)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--intervalo", type=int, default=INTERVALO_DEFECTO, help="segundos entre consultas")
    ap.add_argument("--horizonte", type=int, default=ln.HORIZONTE_DEFECTO, help="minutos del horizonte")
    ap.add_argument("--base", default=str(ln.BASE_DEFECTO), help="ruta de la base SQLite")
    ap.add_argument("--una-vez", action="store_true", help="una sola consulta y termina")
    ap.add_argument("--desde", help='UTC "AAAA-MM-DD HH:MM" (por defecto la última llegada o hace 10 min)')
    ap.add_argument("--simulado", action="store_true", help="usa ModeloSimulado en vez de Claude")
    a = ap.parse_args()

    configurar_log()
    con = abrir(a.base)
    modelo = ln.ModeloSimulado() if a.simulado else ln.ModeloClaude()
    consulta = crear_consulta()
    if a.desde:
        desde = pd.Timestamp(a.desde, tz="UTC").to_pydatetime()
    else:
        desde = desde_defecto(con)
    log.info("inicio: modelo=%s base=%s desde=%s UTC intervalo=%ds horizonte=%d min",
             modelo.identificador or modelo.nombre, a.base, _iso(desde), a.intervalo, a.horizonte)
    try:
        correr(con, modelo, consulta, desde, a.intervalo, a.horizonte, a.una_vez, solape_primera=not a.desde)
    except KeyboardInterrupt:
        log.info("detenido por el usuario")


if __name__ == "__main__":
    main()
