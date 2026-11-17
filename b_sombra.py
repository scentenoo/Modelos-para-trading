"""
Paso 3.3 · B en modo sombra: decide y registra lo que haría, sin enviar ninguna orden.

Corre en el PC viejo (Debian) como servicio de larga duración. Con el modelo guardado por
modelo_final.py (datos/modelos/final/), la variante 12: decide a los minutos k = 30, 60, ..., 180
desde las 9:30 de Nueva York (10:00 a 12:30) con las velas hasta k-1, entra 20 minutos después
(minuto k+20), sale al cierre de la vela 384 (15:55), una operación por acción y día (la del
primer momento cuya predicción calibrada supera el costo esperado), solo en las acciones operables.

Regla de oro: solo información anterior a k. Tres cerrojos, uno encima del otro:
  1. La petición a Alpaca termina un segundo antes de la apertura de la vela k (end = k - 1 s):
     las velas desde k ni se descargan.
  2. variables_vivo recorta por su cuenta las velas y las noticias a lo anterior a k.
  3. Las variables de los días anteriores salen de los archivos (días cerrados) y las de hoy de lo descargado.
  La prueba (--paridad) corrompe las velas desde k y comprueba que nada cambia.

Cada día de sesión (datos/calendario.parquet; los medios días no se operan, como en lo histórico):
  - A la hora k + 20 + 1 minuto (hora de Nueva York): pide a Alpaca (SIP, 15 minutos de retraso) las
    velas de 1 minuto de hoy de SPY y las 50 acciones, y comprueba que llegan hasta la vela k-1. Se
    exige que SPY la tenga y que la tengan al menos el 90% de los símbolos y todas las operables
    (una acción puede no negociar un minuto; todas a la vez es un hueco de datos). Si no, registra el
    problema y reintenta cada 30 s durante 25 minutos; pasado ese tiempo el momento se salta y se
    registra. Con velas completas calcula las variables (variables_vivo, con una fuente que une los
    archivos de días anteriores con las velas de hoy), predice, multiplica por la pendiente fija,
    calcula el costo esperado y decide.
  - Después de las 16:20 (a las 16:21): con las velas del día completa cada operación: precio de entrada
    (cierre de la vela k+20), de salida (cierre de la vela 384), retorno bruto en bps (logarítmico, en la
    dirección operada), costo pagado (la regla de la época: spread del trimestre en curso corregido por
    la volatilidad de ese día), neto, y escribe el resumen del día en el registro.
  - Costo esperado: recostear.costo_de(atras=1): spread mediano del trimestre anterior corregido por la
    volatilidad del día anterior con la elasticidad de 2016-2024 (datos/modelos/final/costos_b.json).
    Las medianas de 2016-2024 salen de datos/modelos/final/costos_b.parquet (se crea con
    --preparar-costos en el PC donde está datos/referencia/cierres.npz); las de 2025 en adelante se
    recalculan cada día con datos/spread_reciente y la volatilidad sacada de las velas de datos/minuto.
    Si el trimestre en curso no tiene medición suficiente (menos de 4 muestras) se usa la regla de
    recostear (mediana del año del símbolo); si no tiene ninguna, la mediana del año o, a falta de
    ella, el último trimestre medido. El origen del costo queda en `costo_origen`.

Qué se guarda (datos/decisiones.sqlite, junto a las tablas de noticias_vivo.py):
  b_sombra_decisiones   una fila por acción operable y momento: día, k, símbolo, predicción (bps, del
                        modelo), predicción calibrada, costo esperado, entra (|calibrada| > costo),
                        dirección (signo de la calibrada), elegida (es la operación del día),
                        hora de cálculo (UTC), versión del modelo (fecha de entrenamiento del json), modo.
  b_sombra_operaciones  la operación elegida de cada acción y día (primer momento que entra), con los
                        precios, el bruto, el costo pagado y el neto cuando se completa al cierre.
  b_sombra_momentos     qué se hizo en cada momento y cierre: hecho, o saltado con el motivo.
  modo: 'vivo' (Alpaca), 'repeticion' (--repetir, solo archivos) o 'simulacion' (prueba de paridad).
datos/registros/b_sombra.log: un archivo por día (rota a medianoche UTC, guarda 60).

Uso:
    python b_sombra.py                                  # sin parar: espera la siguiente hora programada
    python b_sombra.py --una-vez                        # espera y corre solo la próxima tarea
    python b_sombra.py --dia 2024-05-14 --repetir       # repite un día pasado con solo archivos (sin Alpaca)
    python b_sombra.py --paridad 2024-03-12 2024-06-18 2024-10-02    # prueba de paridad con el cálculo por lotes
    python b_sombra.py --preparar-costos                # una vez, o al reentrenar: costos_b.parquet y costos_b.json
    --base RUTA   otra base SQLite (por defecto datos/decisiones.sqlite)

Servicio de systemd en Debian (usuario samir; repo en /home/samir/Modelos-para-trading con su .venv).
Crear /etc/systemd/system/b-sombra.service con:

    [Unit]
    Description=B en modo sombra (decide y registra, sin ordenes)
    After=network-online.target
    Wants=network-online.target

    [Service]
    Type=simple
    User=samir
    WorkingDirectory=/home/samir/Modelos-para-trading
    Environment=PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
    ExecStart=/home/samir/Modelos-para-trading/.venv/bin/python b_sombra.py
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target

y activarlo con:
    sudo systemctl daemon-reload
    sudo systemctl enable --now b-sombra
    systemctl status b-sombra
    journalctl -u b-sombra -f
(las llaves de Alpaca se leen de /home/samir/Modelos-para-trading/.env; el PC puede estar en
America/Bogota: las horas se manejan en America/New_York y el registro va en UTC).

Ojo:
  - El cálculo ocurre a k+21, un minuto después de la hora nominal de entrada (k+20): la operación real
    tendría que ejecutarse en ese momento y el precio de entrada de la sombra (cierre de la vela k+20)
    no es exactamente el que se habría obtenido.
  - dolares_20d en vivo usa solo los dividendos ya conocidos (ver variables_vivo.py): puede mover un poco las predicciones.
  - Si los archivos de datos/minuto no traen algún día anterior, se piden a Alpaca antes de calcular.
  - Se necesitan datos/ajustes, datos/noticias, datos/spread_reciente, datos/calendario.parquet y
    datos/modelos/final/ (con costos_b.*) al día en el PC viejo.
  - Una sola instancia: dos procesos escribirían las mismas filas.
"""

import argparse
import json
import logging
import sqlite3
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

import precios
import recostear
import variables
import variables_vivo as vv
from descargar_datos import RAIZ, SECTOR, UNIVERSO, cargar_env

ZONA = "America/New_York"
CARPETA_MODELO = RAIZ / "modelos" / "final"
BASE_DEFECTO = RAIZ / "decisiones.sqlite"
CARPETA_LOG = RAIZ / "registros"
CALENDARIO = RAIZ / "calendario.parquet"
RECIENTE = RAIZ / "spread_reciente"
SIMBOLOS = ["SPY", *vv.ACCIONES]                    # los 51 que usa el modelo
MARGEN_MIN = 1                                      # minutos después de k+20 para que lleguen las velas
CIERRE_MIN = 16 * 60 + 21                           # a partir de las 16:21 de Nueva York
LIMITE_MOMENTO_MIN = 25                             # tiempo de reintentos de un momento antes de saltarlo
LIMITE_CIERRE_DIAS = 3
REINTENTO_S = 30
ANTICIPO_MIN = 8                                    # se prepara el día (archivos, costos) antes del primer momento
MINIMO_SIN_VELA = 0.10                              # fracción de símbolos que puede no tener la vela k-1
MINIMO_MUESTRAS = recostear.MINIMO_MUESTRAS
log = logging.getLogger("b_sombra")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS b_sombra_decisiones (
    dia TEXT, k INTEGER, symbol TEXT, prediccion REAL, prediccion_calibrada REAL, costo_esperado REAL,
    entra INTEGER, direccion INTEGER, elegida INTEGER, hora_calculo TEXT, version_modelo TEXT, modo TEXT,
    PRIMARY KEY (dia, k, symbol, modo));
CREATE TABLE IF NOT EXISTS b_sombra_operaciones (
    dia TEXT, symbol TEXT, k INTEGER, entrada_min INTEGER, direccion INTEGER, prediccion_calibrada REAL,
    costo_esperado REAL, hora_calculo TEXT, version_modelo TEXT, modo TEXT,
    precio_entrada REAL, precio_salida REAL, bruto_bps REAL, costo_bps REAL, costo_origen TEXT, neto_bps REAL,
    completada_utc TEXT,
    PRIMARY KEY (dia, symbol, modo));
CREATE TABLE IF NOT EXISTS b_sombra_momentos (
    dia TEXT, tipo TEXT, k INTEGER, estado TEXT, detalle TEXT, hora_utc TEXT, modo TEXT,
    PRIMARY KEY (dia, tipo, k, modo));
"""


# ---------------------------------------------------------------- tiempo y calendario

def hora_ny(dia, minutos: int) -> pd.Timestamp:
    """Hora de pared de Nueva York: `minutos` desde la medianoche de `dia`."""
    return (pd.Timestamp(dia).normalize() + pd.Timedelta(minutes=minutos)).tz_localize(ZONA)


def ahora_ny() -> pd.Timestamp:
    return pd.Timestamp.now(tz=ZONA)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cargar_calendario() -> pd.DataFrame:
    c = pd.read_parquet(CALENDARIO)
    c["dia"] = pd.DatetimeIndex(c["dia"]).astype("datetime64[ns]")
    return c


def configurar_log(archivo: bool = True) -> None:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fmt.converter = time.gmtime
    manejadores = [logging.StreamHandler(sys.stdout)]
    if archivo:
        CARPETA_LOG.mkdir(parents=True, exist_ok=True)
        manejadores.append(TimedRotatingFileHandler(CARPETA_LOG / "b_sombra.log", when="midnight", utc=True,
                                                    backupCount=60, encoding="utf-8"))
    log.handlers.clear()
    for h in manejadores:
        h.setFormatter(fmt)
        log.addHandler(h)
    log.setLevel(logging.INFO)


# ---------------------------------------------------------------- volatilidad y costos

def volatilidad_por_dia(velas: pd.DataFrame) -> pd.Series:
    """Volatilidad de cada día de las velas: la fórmula de recostear.volatilidad_diaria() (raíz de la suma de los
    cuadrados de los retornos logarítmicos de 1 minuto del horario normal, sobre cierres de float32 con relleno)."""
    m = variables.matrices("", velas)
    with np.errstate(invalid="ignore", divide="ignore"):
        r1 = np.diff(np.log(m["C"].astype("float32").astype("float64")), axis=1)
    rv = np.sqrt(np.nansum(r1 ** 2, axis=1))
    return pd.Series(np.where(rv > 0, rv, np.nan), index=m["dias"])


def preparar_costos() -> None:
    """Guarda la tabla de spread por trimestre de 2016-2024 y la elasticidad (hace falta cierres.npz)."""
    rv = recostear.volatilidad_diaria()
    q, muestras, e = recostear.spreads_por_trimestre(rv)
    ok = muestras.dropna(subset=["log_spread", "log_rv"])
    q = q.join(ok.groupby(["symbol", "trimestre"]).size().rename("n"))
    q = q[q.index.get_level_values("trimestre") < pd.Period("2025Q1")].reset_index()
    q["trimestre"] = q["trimestre"].astype(str)
    CARPETA_MODELO.mkdir(parents=True, exist_ok=True)
    q.to_parquet(CARPETA_MODELO / "costos_b.parquet", index=False)
    meta = dict(beta=float(e["beta"]), t=float(e["t"]), n=int(e["n"]), datos="2016-2024",
                creado=pd.Timestamp.now().isoformat(timespec="seconds"))
    (CARPETA_MODELO / "costos_b.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"costos_b: {len(q)} filas (símbolo, trimestre), elasticidad {e['beta']:.4f} (t {e['t']:.1f}, {e['n']:,} muestras)")


class Costos:
    """Spread por símbolo y trimestre (spread, ref, n, origen) y la elasticidad; completa lo que falte con la regla de pocas muestras."""

    def __init__(self, con_reciente: bool, rv_reciente: pd.DataFrame | None = None):
        archivo = CARPETA_MODELO / "costos_b.parquet"
        if not archivo.exists():
            raise FileNotFoundError(f"Falta {archivo}: correr `python b_sombra.py --preparar-costos` donde esté datos/referencia/cierres.npz")
        self.beta = json.loads((CARPETA_MODELO / "costos_b.json").read_text(encoding="utf-8"))["beta"]
        h = pd.read_parquet(archivo)
        h["trimestre"] = pd.PeriodIndex(h["trimestre"], freq="Q")
        partes = [h.set_index(["symbol", "trimestre"])]
        self.anual = pd.DataFrame(columns=["mediana", "ref"], index=pd.MultiIndex.from_arrays([[], []], names=["symbol", "anio"]))
        if con_reciente:
            q, t, _ = recostear.spreads_por_trimestre(rv_reciente, RECIENTE)
            q = q[q.index.get_level_values("trimestre") >= pd.Period("2025Q1")]    # las muestras de 2024 ya están en la histórica
            ok = t.dropna(subset=["log_spread", "log_rv"])
            partes.append(q.join(ok.groupby(["symbol", "trimestre"]).size().rename("n")))
            self.anual = ok.groupby(["symbol", "anio"]).agg(mediana=("spread_bps", "median"), ref=("log_rv", "mean"))
        self.tabla = pd.concat(partes)
        self.tabla["origen"] = np.where(self.tabla["n"] >= MINIMO_MUESTRAS, "trimestre", "pocas muestras: mediana del año")

    def _asegurar(self, simbolos, dia, atras: int) -> None:
        """Agrega, con la regla de pocas muestras, las filas de los símbolos que no tienen el trimestre."""
        q = pd.Timestamp(dia).to_period("Q") - atras
        for s in set(simbolos):
            if (s, q) in self.tabla.index:
                continue
            if (s, q.year) in self.anual.index:
                v, r, origen = *self.anual.loc[(s, q.year), ["mediana", "ref"]], "sin muestras del trimestre: mediana del año"
            else:
                previos = self.tabla.loc[s][self.tabla.loc[s].index < q] if s in self.tabla.index.get_level_values(0) else self.tabla.iloc[:0]
                if previos.empty:
                    v, r, origen = np.nan, np.nan, "sin medición"
                else:
                    v, r, origen = previos["spread"].iloc[-1], previos["ref"].iloc[-1], "sin muestras del año: último trimestre medido"
            fila = pd.DataFrame({"spread": [v], "ref": [r], "n": [0], "origen": [origen]},
                                index=pd.MultiIndex.from_tuples([(s, q)], names=["symbol", "trimestre"]))
            self.tabla = pd.concat([self.tabla, fila])
            log.warning("costo: %s no tiene muestras de %s; se usa %s", s, q, origen)

    def costo(self, simbolos, dia, rv: pd.DataFrame, atras: int) -> tuple[np.ndarray, list[str]]:
        """Costo (bps) de cada símbolo con recostear.costo_de, y de dónde salió el spread."""
        self._asegurar(simbolos, dia, atras)
        o = pd.DataFrame({"symbol": list(simbolos), "dia": pd.Timestamp(dia)})
        c = recostear.costo_de(o, self.tabla, rv, self.beta, atras)
        llave = pd.MultiIndex.from_arrays([o["symbol"], o["dia"].dt.to_period("Q") - atras])
        return c, self.tabla["origen"].reindex(llave).fillna("sin medición").tolist()


# ---------------------------------------------------------------- Alpaca

COLUMNAS_VELAS = ["symbol", "timestamp", "open", "high", "low", "close", "volume", "trade_count", "vwap"]


def crear_descargador():
    """bajar(simbolos, inicio_utc, fin_utc) -> velas de 1 minuto (SIP, sin ajustar) en las columnas de datos/minuto."""
    import os
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    cargar_env()
    llave, secreto = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not llave or not secreto:
        sys.exit("Faltan APCA_API_KEY_ID y APCA_API_SECRET_KEY (ver descargar_datos.py).")
    cli = StockHistoricalDataClient(llave, secreto)

    def bajar(simbolos, inicio, fin) -> pd.DataFrame:
        req = StockBarsRequest(symbol_or_symbols=list(simbolos), timeframe=TimeFrame.Minute, start=inicio.to_pydatetime(),
                               end=fin.to_pydatetime(), feed=DataFeed.SIP, adjustment=Adjustment.RAW)
        df = cli.get_stock_bars(req).df
        if df.empty:
            return pd.DataFrame(columns=COLUMNAS_VELAS)
        df = df.reset_index()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df[COLUMNAS_VELAS]
    return bajar


def crear_consulta_noticias():
    """consulta(simbolos, inicio_utc, fin_utc) -> noticias (id, created_at, symbols); puede lanzar excepciones de red."""
    import os
    from alpaca.data.historical.news import NewsClient
    from alpaca.data.requests import NewsRequest
    cargar_env()
    cli = NewsClient(os.environ["APCA_API_KEY_ID"], os.environ["APCA_API_SECRET_KEY"])

    def consulta(simbolos, inicio, fin) -> pd.DataFrame:
        req = NewsRequest(symbols=",".join(simbolos), start=inicio.to_pydatetime(), end=fin.to_pydatetime(), include_content=False, sort="asc")
        noticias = cli.get_news(req).data.get("news", [])
        if not noticias:
            return pd.DataFrame(columns=["id", "created_at", "symbols"])
        df = pd.DataFrame([n.model_dump(mode="json", include={"id", "created_at", "symbols"}) for n in noticias])
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
        return df
    return consulta


def con_dia(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega `dia` (sesión en hora de Nueva York) como precios.cargar."""
    df = df.sort_values("timestamp", ignore_index=True)
    df["dia"] = df["timestamp"].dt.tz_convert(ZONA).dt.tz_localize(None).dt.normalize()
    return df


def por_simbolo(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {s: con_dia(g.reset_index(drop=True)) for s, g in df.groupby("symbol")}


# ---------------------------------------------------------------- tareas

@dataclass(frozen=True)
class Tarea:
    dia: pd.Timestamp
    tipo: str                 # "momento" o "cierre"
    k: int
    hora: pd.Timestamp
    limite: pd.Timestamp      # pasado este instante, si no se pudo, se salta


class Sombra:
    def __init__(self, ruta_base, modo: str = "vivo", bajar=None, consulta_noticias=None):
        self.modo, self.bajar, self.consulta_noticias = modo, bajar, consulta_noticias
        Path(ruta_base).parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(ruta_base, timeout=60)
        self.con.executescript(ESQUEMA)
        self.modelo = lgb.Booster(model_file=str(CARPETA_MODELO / "modelo_b.txt"))
        self.meta = json.loads((CARPETA_MODELO / "modelo_b.json").read_text(encoding="utf-8"))
        esperado = {int(c): s for c, s in self.meta["sector_n"].items()}
        propio = {i: s for i, s in enumerate(sorted(set(SECTOR[a] for a in vv.ACCIONES)))}
        if esperado != propio:
            raise ValueError(f"la codificación del sector del modelo {esperado} no es la de variables_vivo {propio}")
        if self.meta["columnas"] != vv.columnas_del_modelo():
            raise ValueError("las columnas del modelo no coinciden con las de variables_vivo")
        self.operables = list(self.meta["operables"])
        self.version = self.meta["entrenado"]
        self.momentos = list(self.meta["momentos"])
        self.retraso, self.salida = int(self.meta["retraso_min"]), int(self.meta["salida_min"])
        self.calendario = cargar_calendario()
        self.dia_preparado = None
        self.intentos: dict = {}

    # ------------------------------------------------------------ preparación del día

    def preparar(self, dia: pd.Timestamp, archivos: bool) -> None:
        """Deja listo el día: velas de días anteriores, volatilidad de ayer, tabla de costos y noticias.

        archivos=True (--repetir): todo sale de datos/minuto, sin recortar (variables_vivo recorta por k).
        """
        t0 = time.time()
        dia = pd.Timestamp(dia).normalize()
        previos = self.calendario["dia"][self.calendario["dia"] < dia]
        self.previo = previos.max()
        reciente = dia >= pd.Timestamp("2025-01-01")
        rv_reciente = {}
        self.base = {}
        if not archivos:
            vv._NOTICIAS.clear()
        simbolos = list(dict.fromkeys(SIMBOLOS + ([p.stem for p in RECIENTE.glob("*.parquet")] if reciente else [])))
        for s in simbolos:
            crudas = vv.velas_de_archivos(s) if archivos and s in SIMBOLOS else precios.cargar(s, ajuste=None)
            if reciente:
                rv_reciente[s] = volatilidad_por_dia(crudas[crudas["dia"] >= pd.Timestamp("2025-01-01")])
            if not archivos and s in SIMBOLOS:
                inicio = dia - pd.Timedelta(days=vv.VENTANA_DIAS)
                self.base[s] = crudas[(crudas["dia"] >= inicio) & (crudas["dia"] < dia)].reset_index(drop=True)
        if not archivos:
            self._completar_base(dia)
        fuente = vv.velas_de_archivos if archivos else (lambda s: self.base[s])
        rv_prev = {}
        for s in SIMBOLOS:
            c = fuente(s)
            x = c[c["dia"] == self.previo]
            rv_prev[s] = volatilidad_por_dia(x).iloc[0] if len(x) else np.nan
        self.rv_prev = pd.Series(rv_prev).reindex(UNIVERSO)
        if self.rv_prev.reindex(self.operables).isna().any():
            log.warning("sin volatilidad del día anterior (%s) para: %s; el costo no se corrige por volatilidad",
                        self.previo.date(), self.rv_prev.reindex(self.operables)[lambda x: x.isna()].index.tolist())
        rvr = pd.DataFrame(rv_reciente).reindex(columns=sorted(rv_reciente)) if reciente else None
        self.costos = Costos(reciente, rvr)
        self.dia_preparado = dia
        log.info("día %s preparado en %.1f s (día anterior %s, %d símbolos con velas)", dia.date(), time.time() - t0, self.previo.date(), len(self.base) or len(SIMBOLOS))

    def _completar_base(self, dia: pd.Timestamp) -> None:
        """Si los archivos no traen alguna sesión anterior, la pide a Alpaca."""
        ultimo = self.base["SPY"]["dia"].max() if len(self.base["SPY"]) else pd.Timestamp("1900-01-01")
        faltan = self.calendario["dia"][(self.calendario["dia"] > ultimo) & (self.calendario["dia"] < dia)]
        if faltan.empty:
            return
        log.warning("a los archivos de velas les faltan %d sesiones (%s a %s): se piden a Alpaca",
                    len(faltan), faltan.min().date(), faltan.max().date())
        if self.bajar is None:
            raise RuntimeError("faltan sesiones anteriores y no hay descargador")
        ini, fin = hora_ny(faltan.min(), 4 * 60).tz_convert("UTC"), hora_ny(faltan.max(), 20 * 60).tz_convert("UTC")
        nuevas = por_simbolo(self.bajar(SIMBOLOS, ini, fin))
        for s in SIMBOLOS:
            if s in nuevas:
                n = nuevas[s].astype(self.base[s].dtypes.to_dict()) if len(self.base[s]) else nuevas[s]
                self.base[s] = pd.concat([self.base[s], n[n["dia"] < dia]], ignore_index=True)
        if "SPY" not in nuevas:
            raise RuntimeError("Alpaca no devolvió velas de SPY para las sesiones que faltan")

    def rv_frame(self, dia: pd.Timestamp, rv_hoy: pd.Series | None = None) -> pd.DataFrame:
        f = pd.DataFrame(np.nan, index=pd.DatetimeIndex([self.previo, dia]), columns=UNIVERSO)
        f.loc[self.previo] = self.rv_prev
        if rv_hoy is not None:
            f.loc[dia] = rv_hoy.reindex(UNIVERSO)
        return f

    # ------------------------------------------------------------ cálculo de un momento

    def calcular(self, dia: pd.Timestamp, k: int, fuente, noticias=None) -> pd.DataFrame:
        """Predicción, costo esperado y decisión de las acciones operables en el minuto k. Sin escribir nada."""
        dia = pd.Timestamp(dia).normalize()
        t = vv.variables_del_momento_en_vivo(dia, k, fuente=fuente, noticias=noticias)
        t = t[t["symbol"].isin(self.operables)].reset_index(drop=True)
        ausentes = sorted(set(self.operables) - set(t["symbol"]))
        if ausentes:
            log.warning("%s k=%d: sin variables de %s", dia.date(), k, ausentes)
        faltan = [c for c in self.meta["columnas"] if c not in t.columns]
        if faltan:
            raise ValueError(f"faltan variables del modelo: {faltan}")
        pred = self.modelo.predict(t[self.meta["columnas"]])
        cal = pred * self.meta["pendiente"]
        costo, _ = self.costos.costo(t["symbol"], dia, self.rv_frame(dia), atras=1)
        entra = np.abs(cal) > costo                                  # con costo NaN no entra
        return pd.DataFrame({"symbol": t["symbol"].values, "prediccion": pred, "prediccion_calibrada": cal, "costo_esperado": costo,
                             "entra": entra, "direccion": np.sign(cal).astype(int)}).sort_values("symbol", ignore_index=True)

    def registrar(self, dia: pd.Timestamp, k: int, r: pd.DataFrame) -> int:
        """Guarda las decisiones del momento y las operaciones nuevas. Devuelve cuántas operaciones abre."""
        d, hora, nuevas = f"{dia:%Y-%m-%d}", _utc_iso(), 0
        ya = {s for (s,) in self.con.execute("SELECT symbol FROM b_sombra_operaciones WHERE dia=? AND modo=?", (d, self.modo))}
        with self.con:
            for x in r.itertuples():
                elegida = bool(x.entra) and x.symbol not in ya
                costo = None if not np.isfinite(x.costo_esperado) else float(x.costo_esperado)
                self.con.execute("INSERT OR REPLACE INTO b_sombra_decisiones VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                 (d, k, x.symbol, float(x.prediccion), float(x.prediccion_calibrada), costo, int(x.entra), int(x.direccion),
                                  int(elegida), hora, self.version, self.modo))
                if elegida:
                    self.con.execute("INSERT OR IGNORE INTO b_sombra_operaciones (dia, symbol, k, entrada_min, direccion, prediccion_calibrada, "
                                     "costo_esperado, hora_calculo, version_modelo, modo) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                     (d, x.symbol, k, k + self.retraso, int(x.direccion), float(x.prediccion_calibrada), costo, hora, self.version, self.modo))
                    ya.add(x.symbol); nuevas += 1
        return nuevas

    def marcar(self, dia, tipo: str, k: int, estado: str, detalle: str = "") -> None:
        with self.con:
            self.con.execute("INSERT OR REPLACE INTO b_sombra_momentos VALUES (?,?,?,?,?,?,?)",
                             (f"{dia:%Y-%m-%d}", tipo, k, estado, detalle, _utc_iso(), self.modo))

    def hecha(self, dia, tipo: str, k: int) -> bool:
        return self.con.execute("SELECT 1 FROM b_sombra_momentos WHERE dia=? AND tipo=? AND k=? AND modo=?",
                                (f"{dia:%Y-%m-%d}", tipo, k, self.modo)).fetchone() is not None

    # ------------------------------------------------------------ en vivo

    def _fuente_con_hoy(self, hoy: dict[str, pd.DataFrame]):
        def fuente(s: str) -> pd.DataFrame:
            b, h = self.base[s], hoy.get(s)
            if h is None or h.empty:
                return b
            h = h.astype({c: b[c].dtype for c in h.columns if c in b.columns}) if len(b) else h
            return pd.concat([b, h], ignore_index=True)
        return fuente

    def _noticias(self, dia: pd.Timestamp, k: int):
        """Noticias de los archivos más las que Alpaca trae después de la última del archivo, hasta k (sin incluirlo)."""
        base = vv.noticias_de_archivos()
        if self.consulta_noticias is None:
            return base
        ultima = max(a[-1] for a in base.values() if len(a))
        ini = pd.Timestamp(ultima).tz_localize("UTC")
        fin = hora_ny(dia, 570 + k).tz_convert("UTC") - pd.Timedelta(seconds=1)
        if ini >= fin:                       # el archivo ya llega hasta k (por ejemplo, al repetir un día pasado)
            return base
        n = self.consulta_noticias(SIMBOLOS, ini, fin)
        if n.empty:
            return base
        n = n.drop_duplicates("id")
        n = n[n["symbols"].str.len() <= variables.MAX_SIMBOLOS_POR_NOTICIA].explode("symbols")
        n["utc"] = n["created_at"].dt.tz_localize(None).astype("datetime64[ns]")
        n = n[n["utc"] > ultima]
        nuevo = {s: np.sort(g["utc"].values) for s, g in n.groupby("symbols")}
        return {s: np.concatenate([base.get(s, np.array([], dtype="datetime64[ns]")), nuevo.get(s, np.array([], dtype="datetime64[ns]"))]) for s in set(base) | set(nuevo)}

    def _revisar_completas(self, hoy: dict[str, pd.DataFrame], dia: pd.Timestamp, k: int) -> str | None:
        """None si las velas llegan hasta la vela k-1; si no, el problema."""
        necesaria = hora_ny(dia, 570 + k - 1).tz_convert("UTC")
        ultima = {s: (hoy[s]["timestamp"].max() if s in hoy and len(hoy[s]) else None) for s in SIMBOLOS}
        sin = [s for s, u in ultima.items() if u is None or u < necesaria]
        sin_nada = [s for s, u in ultima.items() if u is None]
        detalle = ", ".join(f"{s} ({'sin velas' if ultima[s] is None else ultima[s].tz_convert(ZONA).strftime('%H:%M')})" for s in sin)
        if sin_nada and set(sin_nada) & ({"SPY"} | set(self.operables)):
            return f"sin ninguna vela de hoy: {sin_nada}"
        if "SPY" in sin:
            return f"SPY no llega a la vela k-1 ({necesaria.tz_convert(ZONA):%H:%M}): {detalle}"
        if len(sin) > MINIMO_SIN_VELA * len(SIMBOLOS):
            return f"{len(sin)} de {len(SIMBOLOS)} símbolos sin la vela k-1 ({necesaria.tz_convert(ZONA):%H:%M}): {detalle}"
        if sin:
            log.warning("%s k=%d: sin la vela k-1 (probablemente sin operaciones ese minuto): %s", dia.date(), k, detalle)
        return None

    def momento_vivo(self, dia: pd.Timestamp, k: int) -> tuple[str, str]:
        """Un momento con Alpaca. Devuelve (estado, detalle): 'hecho' o 'reintentar'."""
        if self.dia_preparado != dia:
            self.preparar(dia, archivos=False)
        t0 = time.time()
        fin = hora_ny(dia, 570 + k).tz_convert("UTC") - pd.Timedelta(seconds=1)       # nada desde la vela k
        df = self.bajar(SIMBOLOS, hora_ny(dia, 4 * 60).tz_convert("UTC"), fin)
        hoy = por_simbolo(df[df["timestamp"] <= fin]) if len(df) else {}
        problema = self._revisar_completas(hoy, dia, k)
        if problema:
            return "reintentar", problema
        t1 = time.time()
        r = self.calcular(dia, k, self._fuente_con_hoy(hoy), self._noticias(dia, k))
        abiertas = self.registrar(dia, k, r)
        log.info("%s k=%d (%s): %d acciones, %d entran, %d operaciones nuevas; descarga %.1f s, cálculo %.1f s",
                 dia.date(), k, hora_ny(dia, 570 + k).strftime("%H:%M"), len(r), int(r["entra"].sum()), abiertas, t1 - t0, time.time() - t1)
        return "hecho", f"{len(r)} acciones, {abiertas} operaciones"

    def cerrar(self, dia: pd.Timestamp, velas: dict[str, pd.DataFrame]) -> str:
        """Completa las operaciones del día con sus velas. Devuelve el resumen."""
        d = f"{dia:%Y-%m-%d}"
        ops = pd.read_sql_query("SELECT * FROM b_sombra_operaciones WHERE dia=? AND modo=? AND precio_salida IS NULL ORDER BY symbol",
                                self.con, params=(d, self.modo))
        if ops.empty:
            return f"{d}: sin operaciones que cerrar"
        C, rv_hoy = {}, {}
        for s in ops["symbol"]:
            x = velas[s]
            x = x[x["dia"] == dia]
            C[s] = variables.matrices(s, x)["C"][0]
            rv_hoy[s] = volatilidad_por_dia(x).iloc[0]
        entrada = np.array([C[s][int(e)] for s, e in zip(ops["symbol"], ops["entrada_min"])], dtype="float32").astype("float64")
        salida = np.array([C[s][self.salida] for s in ops["symbol"]], dtype="float32").astype("float64")
        with np.errstate(invalid="ignore", divide="ignore"):
            bruto = ops["direccion"].to_numpy() * np.log(salida / entrada) * 1e4
        costo, origen = self.costos.costo(ops["symbol"], dia, self.rv_frame(dia, pd.Series(rv_hoy)), atras=0)
        neto = bruto - costo
        hora = _utc_iso()
        with self.con:
            for i, x in enumerate(ops.itertuples()):
                f = lambda v: float(v) if np.isfinite(v) else None
                self.con.execute("UPDATE b_sombra_operaciones SET precio_entrada=?, precio_salida=?, bruto_bps=?, costo_bps=?, costo_origen=?, "
                                 "neto_bps=?, completada_utc=? WHERE dia=? AND symbol=? AND modo=?",
                                 (f(entrada[i]), f(salida[i]), f(bruto[i]), f(costo[i]), origen[i], f(neto[i]), hora, d, x.symbol, self.modo))
        pocas = sorted({o for o in origen if o != "trimestre"})
        return (f"{d}: {len(ops)} operaciones, bruto {np.nanmean(bruto):.2f} bps, costo {np.nanmean(costo):.2f}, neto {np.nanmean(neto):.2f} por operación, "
                f"neto total {np.nansum(neto):.1f} bps, acierto {np.nanmean(bruto > 0) * 100:.0f}%"
                + (f"; costo con regla de pocas muestras ({', '.join(pocas)})" if pocas else ""))

    def cierre_vivo(self, dia: pd.Timestamp) -> tuple[str, str]:
        if self.dia_preparado != dia:
            self.preparar(dia, archivos=False)
        simbolos = pd.read_sql_query("SELECT DISTINCT symbol FROM b_sombra_operaciones WHERE dia=? AND modo=?", self.con,
                                     params=(f"{dia:%Y-%m-%d}", self.modo))["symbol"].tolist()
        if simbolos:
            fin = hora_ny(dia, 16 * 60).tz_convert("UTC") - pd.Timedelta(seconds=1)
            df = self.bajar(simbolos + ["SPY"], hora_ny(dia, 4 * 60).tz_convert("UTC"), fin)
            velas = por_simbolo(df[df["timestamp"] <= fin]) if len(df) else {}
            necesaria = hora_ny(dia, 570 + self.salida).tz_convert("UTC")
            if "SPY" not in velas or velas["SPY"]["timestamp"].max() < necesaria:
                return "reintentar", f"las velas de SPY no llegan a la vela {self.salida}"
            faltan = [s for s in simbolos if s not in velas]
            if faltan:
                return "reintentar", f"sin velas de {faltan}"
        else:
            velas = {}
        resumen = self._resumen_del_dia(dia, self.cerrar(dia, velas))
        log.info("RESUMEN %s", resumen)
        return "hecho", resumen

    def _resumen_del_dia(self, dia, texto: str) -> str:
        m = pd.read_sql_query("SELECT estado, COUNT(*) n FROM b_sombra_momentos WHERE dia=? AND tipo='momento' AND modo=? GROUP BY estado",
                              self.con, params=(f"{dia:%Y-%m-%d}", self.modo)).set_index("estado")["n"].to_dict()
        return f"{texto}; momentos {m or 'ninguno registrado'}"

    # ------------------------------------------------------------ repetir un día con archivos

    def repetir_dia(self, dia: pd.Timestamp, fuente=None, noticias=None) -> dict:
        """Repite un día pasado con solo archivos: todos los momentos y el cierre. Devuelve los tiempos por momento."""
        dia = pd.Timestamp(dia).normalize()
        if not (self.calendario["dia"] == dia).any() or self.calendario.loc[self.calendario["dia"] == dia, "medio_dia"].iloc[0]:
            raise ValueError(f"{dia.date()} no es un día de sesión completo")
        d = f"{dia:%Y-%m-%d}"
        with self.con:
            for tabla in ("b_sombra_decisiones", "b_sombra_operaciones", "b_sombra_momentos"):
                self.con.execute(f"DELETE FROM {tabla} WHERE dia=? AND modo=?", (d, self.modo))
        self.preparar(dia, archivos=True)
        fuente = fuente or vv.velas_de_archivos
        tiempos = []
        for k in self.momentos:
            t0 = time.time()
            r = self.calcular(dia, k, fuente, noticias)
            abiertas = self.registrar(dia, k, r)
            tiempos.append(time.time() - t0)
            self.marcar(dia, "momento", k, "hecho", f"{len(r)} acciones, {abiertas} operaciones")
            log.info("%s k=%d (repetición): %d acciones, %d entran, %d operaciones nuevas, %.1f s", d, k, len(r), int(r["entra"].sum()), abiertas, tiempos[-1])
        velas = {s: vv.velas_de_archivos(s) for s in SIMBOLOS}
        texto = self._resumen_del_dia(dia, self.cerrar(dia, velas))
        self.marcar(dia, "cierre", 0, "hecho", texto)
        log.info("RESUMEN %s", texto)
        return dict(tiempos=tiempos)

    # ------------------------------------------------------------ bucle

    def tareas(self, dia: pd.Timestamp) -> list[Tarea]:
        fila = self.calendario[self.calendario["dia"] == dia]
        if fila.empty or fila["medio_dia"].iloc[0]:
            return []
        t = [Tarea(dia, "momento", k, hora_ny(dia, 570 + k + self.retraso + MARGEN_MIN),
                   hora_ny(dia, 570 + k + self.retraso + MARGEN_MIN + LIMITE_MOMENTO_MIN)) for k in self.momentos]
        cierre = hora_ny(dia, CIERRE_MIN)
        return t + [Tarea(dia, "cierre", 0, cierre, cierre + pd.Timedelta(days=LIMITE_CIERRE_DIAS))]

    def proxima_tarea(self, ahora: pd.Timestamp) -> Tarea:
        hoy = ahora.tz_localize(None).normalize()
        pendientes = pd.read_sql_query("SELECT DISTINCT dia FROM b_sombra_operaciones WHERE modo=? AND precio_salida IS NULL AND dia < ?",
                                       self.con, params=(self.modo, f"{hoy:%Y-%m-%d}"))["dia"]
        candidatos = []
        for d in [pd.Timestamp(x) for x in pendientes] + list(pd.date_range(hoy, hoy + pd.Timedelta(days=14))):
            for t in self.tareas(d):
                if self.hecha(t.dia, t.tipo, t.k):
                    continue
                if t.limite < ahora:                              # el proceso no estaba: se registra y se sigue
                    self.marcar(t.dia, t.tipo, t.k, "saltado", "pasó el tiempo límite sin correr (proceso detenido)")
                    log.warning("%s %s k=%d saltado: pasó el límite sin correr", t.dia.date(), t.tipo, t.k)
                    continue
                candidatos.append(t)
        return min(candidatos, key=lambda t: t.hora)

    def ejecutar(self, t: Tarea) -> str:
        clave = (t.dia, t.tipo, t.k)
        try:
            estado, detalle = self.momento_vivo(t.dia, t.k) if t.tipo == "momento" else self.cierre_vivo(t.dia)
        except Exception as e:  # noqa: BLE001  (red, base o datos: se registra y se reintenta)
            log.error("%s %s k=%d: %s: %s", t.dia.date(), t.tipo, t.k, type(e).__name__, e, exc_info=not isinstance(e, OSError))
            estado, detalle = "reintentar", f"{type(e).__name__}: {e}"
        if estado == "hecho":
            self.marcar(t.dia, t.tipo, t.k, "hecho", detalle)
            self.intentos.pop(clave, None)
            return "hecho"
        self.intentos[clave] = self.intentos.get(clave, 0) + 1
        if ahora_ny() > t.limite:
            self.marcar(t.dia, t.tipo, t.k, "saltado", f"{detalle} (tras {self.intentos[clave]} intentos)")
            log.error("%s %s k=%d SALTADO: %s", t.dia.date(), t.tipo, t.k, detalle)
            return "saltado"
        if self.intentos[clave] == 1 or self.intentos[clave] % 10 == 0:
            log.warning("%s %s k=%d no se pudo (intento %d): %s", t.dia.date(), t.tipo, t.k, self.intentos[clave], detalle)
        time.sleep(REINTENTO_S)
        return "reintentar"

    def correr(self, una_vez: bool) -> None:
        log.info("Arranca b_sombra: modelo entrenado %s, %d acciones operables, momentos %s, entrada +%d min, salida minuto %d",
                 self.version, len(self.operables), self.momentos, self.retraso, self.salida)
        while True:
            try:
                ahora = ahora_ny()
                t = self.proxima_tarea(ahora)
                espera = (t.hora - ahora).total_seconds()
                if self.dia_preparado != t.dia and espera <= ANTICIPO_MIN * 60 and t.tipo == "momento":
                    try:
                        self.preparar(t.dia, archivos=False)
                    except Exception as e:  # noqa: BLE001
                        log.error("no se pudo preparar el día %s: %s: %s", t.dia.date(), type(e).__name__, e)
                        time.sleep(REINTENTO_S)
                    continue
                if espera > 0:
                    time.sleep(min(espera, 60))
                    continue
                if self.ejecutar(t) != "reintentar" and una_vez:
                    return
            except Exception as e:  # noqa: BLE001  (nada tumba el bucle)
                log.error("error en el bucle: %s: %s", type(e).__name__, e, exc_info=True)
                time.sleep(REINTENTO_S)


# ---------------------------------------------------------------- prueba de paridad

def paridad(dias: list[pd.Timestamp]) -> None:
    """Compara b_sombra (repetición con archivos y simulación del camino en vivo) con el cálculo por lotes."""
    import horizonte_largo as hl
    import muestra_final as mf
    import referencia
    if any(d >= referencia.CORTE for d in dias):
        sys.exit(f"--paridad no usa días desde {referencia.CORTE.date()} (muestra final)")

    # Cálculo por lotes: filas de datos/variables (lógica de modelo_velas.cargar), modelo guardado, hl.operar con retraso 20.
    modelo, meta = mf.cargar_modelo()
    p = referencia.cargar_precios()
    medios = pd.DatetimeIndex(p["dias"][p["medio_dia"]])
    t = mf.filas(min(dias), max(dias), meta, medios)
    t = t[t["dia"].isin(dias)].reset_index(drop=True)
    pred = mf.predicciones(t, p, modelo, meta)
    rv = recostear.volatilidad_diaria()
    tabla, beta, _ = mf.tabla_de_costos(rv)
    costo = lambda x, atras=0: recostear.costo_de(x, tabla, rv, beta, atras)
    operables = set(meta["operables"])
    o = hl.operar(pred, hl.MODELO, operables, costo, meta["retraso_min"])
    lote = pred[pred["symbol"].isin(operables) & pred["minuto"].isin(hl.MOMENTOS)].copy()
    lote["costo_lote"] = costo(lote, atras=1)
    lote["entra_lote"] = np.abs(lote[hl.MODELO].values) > lote["costo_lote"].values
    print(f"Lotes: {len(lote):,} decisiones y {len(o)} operaciones en {len(dias)} días ({', '.join(f'{d:%Y-%m-%d}' for d in dias)})")

    carpeta = Path(tempfile.mkdtemp(prefix="b_sombra_paridad_"))

    def fuente_archivos_simulando_alpaca(s_, ini, fin):
        partes = []
        for s in s_:
            v = vv.velas_de_archivos(s)
            partes.append(v[(v["timestamp"] >= ini) & (v["timestamp"] <= fin)][COLUMNAS_VELAS])
        return pd.concat(partes, ignore_index=True)

    resultados = {}
    for modo in ("repeticion", "simulacion"):
        ruta = carpeta / f"{modo}.sqlite"
        s = Sombra(ruta, modo=modo, bajar=fuente_archivos_simulando_alpaca if modo == "simulacion" else None)
        tiempos = []
        for d in dias:
            if modo == "repeticion":
                tiempos += s.repetir_dia(d)["tiempos"]
            else:
                tiempos += _simular_dia_vivo(s, d)
        dec = pd.read_sql_query("SELECT * FROM b_sombra_decisiones WHERE modo=?", s.con, params=(modo,))
        ops = pd.read_sql_query("SELECT * FROM b_sombra_operaciones WHERE modo=?", s.con, params=(modo,))
        resultados[modo] = (dec, ops, tiempos)

    # Prueba de fuga: velas desde k corrompidas en la fuente, mismas decisiones.
    s = Sombra(carpeta / "fuga.sqlite", modo="repeticion")
    s.preparar(dias[0], archivos=True)
    k = 90
    limite = hora_ny(dias[0], 570 + k).tz_convert("UTC")
    def corrupta(sim):
        v = vv.velas_de_archivos(sim).copy()
        despues = (v["timestamp"] >= limite) & (v["dia"] == dias[0])
        v.loc[despues, ["open", "high", "low", "close", "vwap"]] *= 7.0
        v.loc[despues, "volume"] *= 50.0
        return v
    limpia, sucia = s.calcular(dias[0], k, vv.velas_de_archivos), s.calcular(dias[0], k, corrupta)
    print(f"\nPrueba de fuga (velas desde k={k} de {dias[0]:%Y-%m-%d} multiplicadas por 7): "
          f"{'sin cambios' if limpia.equals(sucia) else 'CAMBIA: HAY FUGA'}")

    for modo, (dec, ops, tiempos) in resultados.items():
        print(f"\n=== {modo} contra lotes ===")
        dec = dec.assign(dia=pd.to_datetime(dec["dia"]), minuto=dec["k"])
        m = dec.merge(lote, on=["symbol", "dia", "minuto"], how="outer", indicator=True)
        solo_sombra, solo_lote = int((m["_merge"] == "left_only").sum()), int((m["_merge"] == "right_only").sum())
        c = m[m["_merge"] == "both"]
        dif = (c["prediccion_calibrada"] - c[hl.MODELO]).abs()
        dc = (c["costo_esperado"] - c["costo_lote"]).abs()
        cambian = int((c["entra"].astype(bool) != c["entra_lote"]).sum())
        print(f"Decisiones: {len(c):,} comparadas ({solo_sombra} solo en b_sombra, {solo_lote} solo en lotes).")
        print(f"Predicción calibrada: diferencia máxima {dif.max():.4g} bps, media {dif.mean():.3g} bps; "
              f"mediana de |pred| {c[hl.MODELO].abs().median():.2f} bps. Diferencia relativa máxima {(dif / c[hl.MODELO].abs().clip(lower=1e-9)).max():.3g}.")
        print(f"Costo esperado: diferencia máxima {dc.max():.4g} bps.")
        print(f"Decisiones de entrar que cambian: {cambian} de {len(c):,}.")
        ops = ops.assign(dia=pd.to_datetime(ops["dia"]), entrada=ops["entrada_min"])
        mo = ops.merge(o, on=["symbol", "dia"], how="outer", indicator=True, suffixes=("", "_lote"))
        ambas = mo[mo["_merge"] == "both"]
        print(f"Operaciones: b_sombra {len(ops)}, lotes {len(o)}; en ambas {len(ambas)}, solo b_sombra {int((mo['_merge'] == 'left_only').sum())}, "
              f"solo lotes {int((mo['_merge'] == 'right_only').sum())}.")
        if len(ambas):
            print(f"  mismo momento de entrada: {int((ambas['entrada'] == ambas['entrada_lote']).sum())} de {len(ambas)}; "
                  f"misma dirección: {int((ambas['direccion'] == ambas['direccion_lote']).sum())}; "
                  f"bruto (diferencia máxima) {(ambas['bruto_bps'] - ambas['bruto_bps_lote']).abs().max():.4g} bps; "
                  f"costo pagado {(ambas['costo_bps'] - ambas['costo_bps_lote']).abs().max():.4g}; "
                  f"neto {(ambas['neto_bps'] - ambas['neto_bps_lote']).abs().max():.4g}")
        if mo["_merge"].ne("both").any():
            print(mo[mo["_merge"] != "both"][["dia", "symbol", "k", "entrada", "entrada_lote", "_merge"]].to_string())
        print(f"Tiempo por momento (con archivos ya leídos): media {np.mean(tiempos):.2f} s, máximo {np.max(tiempos):.2f} s ({len(tiempos)} momentos)")
    print(f"\nBases de la prueba en {carpeta}")


def _simular_dia_vivo(s: Sombra, dia: pd.Timestamp) -> list[float]:
    """Camino en vivo (descarga, revisión, fuente combinada, cierre) con un descargador que lee los archivos."""
    d = f"{dia:%Y-%m-%d}"
    s.dia_preparado = None
    s.preparar(dia, archivos=False)
    tiempos = []
    for k in s.momentos:
        t0 = time.time()
        estado, detalle = s.momento_vivo(dia, k)
        tiempos.append(time.time() - t0)
        if estado != "hecho":
            raise RuntimeError(f"{d} k={k}: {detalle}")
        s.marcar(dia, "momento", k, "hecho", detalle)
    estado, detalle = s.cierre_vivo(dia)
    if estado != "hecho":
        raise RuntimeError(f"{d} cierre: {detalle}")
    s.marcar(dia, "cierre", 0, "hecho", detalle)
    return tiempos


def main() -> None:
    ap = argparse.ArgumentParser(description="B en modo sombra: decide y registra, sin órdenes.")
    ap.add_argument("--base", default=str(BASE_DEFECTO), help="ruta de la base SQLite")
    ap.add_argument("--una-vez", action="store_true", help="espera y corre solo la próxima tarea")
    ap.add_argument("--dia", type=pd.Timestamp, metavar="AAAA-MM-DD", help="día a repetir (con --repetir)")
    ap.add_argument("--repetir", action="store_true", help="repite --dia con solo archivos, sin Alpaca")
    ap.add_argument("--paridad", nargs="+", type=pd.Timestamp, metavar="AAAA-MM-DD", help="prueba de paridad en esos días (anteriores a 2025)")
    ap.add_argument("--preparar-costos", action="store_true", help="guarda datos/modelos/final/costos_b.parquet y costos_b.json")
    args = ap.parse_args()
    if args.preparar_costos:
        preparar_costos()
    elif args.paridad:
        configurar_log(archivo=False)
        paridad([d.normalize() for d in args.paridad])
    elif args.repetir:
        if args.dia is None:
            sys.exit("--repetir necesita --dia AAAA-MM-DD")
        configurar_log()
        Sombra(args.base, modo="repeticion").repetir_dia(args.dia)
    else:
        configurar_log()
        Sombra(args.base, modo="vivo", bajar=crear_descargador(), consulta_noticias=crear_consulta_noticias()).correr(args.una_vez)


if __name__ == "__main__":
    main()
