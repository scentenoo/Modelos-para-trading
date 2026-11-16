"""
Variables del competidor D sacadas de las respuestas de Claude Haiku 5.5 a cada noticia (paso 2.9).
Calcula, para un momento de decisión y una lista de acciones, las seis variables definidas en
"Instrucciones para que la IA lea noticias (paso 2.9), versión 1", párrafo "Variables para D", a partir de
`datos/decisiones.sqlite` (tablas de lector_noticias.py: respuestas_ia y evaluaciones_ia).

Regla:
  - Una respuesta cuenta desde la hora en que LLEGÓ (`recibida_utc` del intento válido), no desde la hora de
    la noticia. Si llegó después del momento, no se usa (se usará en el siguiente). Una respuesta que llega
    justo en el momento (recibida_utc <= momento) sí cuenta.
  - Solo evaluaciones de respuestas válidas (valido = 1), del modelo y la versión de instrucciones pedidos
    (por defecto claude-haiku-5-5 y v1). Si una noticia tiene varias versiones (se corrigió), cuenta la más
    reciente (por `version`, es decir `updated_at`) de las que ya habían llegado antes del momento.
  - Ventana de "última hora": respuestas llegadas en (momento - 60 min, momento].
  - "Noche": respuestas llegadas en (cierre de la sesión anterior, momento]; el cierre sale de
    `datos/calendario.parquet` (último `cierre` <= momento; con medios días usa la hora real de cierre).
    Si no hay sesión anterior en el calendario, se usan 10.000 minutos hacia atrás.
  - Variables (por acción; sin noticias: 0, `ia_min_desde_relevante` = 10.000 y `ia_reaccion` = 0):
      ia_tono_60m             suma de tono * relevancia / 2 de las noticias con novedad = 1 de la última hora.
      ia_sorpresa_60m         mayor sorpresa entre las de relevancia 2 de la última hora (con cualquier novedad).
      ia_relevantes_60m       cuántas noticias con relevancia 2 en la última hora (con cualquier novedad).
      ia_tono_noche           como ia_tono_60m, con las respuestas desde el cierre anterior.
      ia_reaccion             signo(tono) * retorno relativo desde la llegada de esa respuesta hasta el momento.
        La noticia que se usa: la de llegada más reciente entre las de la última hora con relevancia 2 y
        novedad = 1 (la relevancia 1 es menor y no se toma como "la noticia"). signo(tono) es -1, 0 o 1.
        Retorno relativo = (cierre_momento / cierre_llegada - 1) de la acción menos el promedio de ese
        mismo retorno en las 50 acciones (no los ETF), en fracción (0,01 = 1%). Negativo es "noticia
        buena y el precio no subió". Sin noticia así: 0. Sin `precios` (o sin precio): NaN.
      ia_min_desde_relevante  minutos desde la llegada de la última respuesta con relevancia 2 (cualquier
                              novedad), tope 10.000 (igual que `min_desde_noticia` de variables.py).
  - `precios(momento_utc)` debe devolver una pd.Series indexada por símbolo con el último cierre de cada
    acción en ese minuto o antes (momento_utc es un pd.Timestamp en UTC). Se llama una vez por cada hora de
    llegada distinta y una vez para el momento.

Uso:
    from variables_ia import variables_ia
    df = variables_ia(con, pd.Timestamp("2026-11-17 15:00", tz="UTC"), ACCIONES, precios=mi_funcion)
    python variables_ia.py --probar                       # pruebas con una base pequeña en memoria
    python variables_ia.py --resumen datos/decisiones.sqlite   # último día con datos, 10:00 a 12:30 (NY), sin precios

Salida:
    pd.DataFrame indexado por símbolo con las seis columnas anteriores (--probar y --resumen escriben en pantalla).
"""

import argparse
import sqlite3
import sys

import numpy as np
import pandas as pd

from descargar_datos import RAIZ
from lector_noticias import ACCIONES, NY, VERSION_INSTRUCCIONES, abrir_base

MODELO_DEFECTO = "claude-haiku-5-5"
TOPE_MIN = 10_000
COLUMNAS = ["ia_tono_60m", "ia_sorpresa_60m", "ia_relevantes_60m", "ia_tono_noche", "ia_reaccion", "ia_min_desde_relevante"]
CALENDARIO = RAIZ / "calendario.parquet"


def _utc(t) -> pd.Timestamp:
    t = pd.Timestamp(t)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def _cierre_anterior(momento: pd.Timestamp, calendario: pd.DataFrame | None = None) -> pd.Timestamp:
    """Último cierre de sesión <= momento, en UTC; sin dato, momento - TOPE_MIN minutos."""
    if calendario is None:
        calendario = pd.read_parquet(CALENDARIO)
    cierres = calendario["cierre"].dt.tz_localize(NY).dt.tz_convert("UTC")
    previos = cierres[cierres <= momento]
    return previos.max() if len(previos) else momento - pd.Timedelta(minutes=TOPE_MIN)


def _respuestas(con, momento: pd.Timestamp, modelo: str, version_instr: str) -> pd.DataFrame:
    """Evaluaciones de respuestas válidas llegadas en (momento - TOPE_MIN, momento], una por
    (noticia, símbolo): la versión más reciente de las ya llegadas. Columna `llego` en UTC."""
    q = """SELECT r.noticia, r.version_noticia AS version, MIN(r.recibida_utc) AS llego, e.simbolo,
                  e.relevancia, e.tono, e.novedad, e.sorpresa
           FROM respuestas_ia r JOIN evaluaciones_ia e
             ON e.noticia = r.noticia AND e.version_noticia = r.version_noticia
            AND e.modelo = r.modelo AND e.version_instrucciones = r.version_instrucciones
           WHERE r.valido = 1 AND r.modelo = ? AND r.version_instrucciones = ?
           GROUP BY r.noticia, r.version_noticia, e.simbolo"""
    d = pd.read_sql(q, con, params=(modelo, version_instr))
    if d.empty:
        return d.assign(version_ts=pd.NaT)
    d["llego"] = pd.to_datetime(d["llego"], utc=True, format="ISO8601")
    d["version_ts"] = pd.to_datetime(d["version"], utc=True, format="ISO8601")
    d = d[(d["llego"] <= momento) & (d["llego"] > momento - pd.Timedelta(minutes=TOPE_MIN))]
    # varias versiones de la misma noticia: la más reciente entre las que ya habían llegado
    d = d.sort_values("version_ts").drop_duplicates(["noticia", "simbolo"], keep="last")
    return d


def _tono(d: pd.DataFrame) -> pd.Series:
    n = d[d["novedad"] == 1]
    return (n["tono"] * n["relevancia"] / 2).groupby(n["simbolo"]).sum()


def variables_ia(con, momento_utc, simbolos, precios=None, modelo: str = MODELO_DEFECTO,
                 version_instrucciones: str = VERSION_INSTRUCCIONES, calendario: pd.DataFrame | None = None) -> pd.DataFrame:
    """Las seis variables de D por símbolo en `momento_utc` (ver el docstring del módulo)."""
    momento = _utc(momento_utc)
    simbolos = list(simbolos)
    d = _respuestas(con, momento, modelo, version_instrucciones)
    hora = d[d["llego"] > momento - pd.Timedelta(minutes=60)]
    noche = d[d["llego"] > _cierre_anterior(momento, calendario)]
    rel = hora[hora["relevancia"] == 2]
    out = pd.DataFrame(index=pd.Index(simbolos, name="simbolo"))
    out["ia_tono_60m"] = _tono(hora).reindex(simbolos).fillna(0.0)
    out["ia_sorpresa_60m"] = rel.groupby("simbolo")["sorpresa"].max().reindex(simbolos).fillna(0).astype(int)
    out["ia_relevantes_60m"] = rel.groupby("simbolo").size().reindex(simbolos).fillna(0).astype(int)
    out["ia_tono_noche"] = _tono(noche).reindex(simbolos).fillna(0.0)

    # minutos desde la llegada de la última respuesta con relevancia 2 (de las ya llegadas, de cualquier edad)
    ultima = d[d["relevancia"] == 2].groupby("simbolo")["llego"].max().reindex(simbolos)
    minutos = (momento - ultima).dt.total_seconds() / 60
    out["ia_min_desde_relevante"] = minutos.fillna(TOPE_MIN).clip(upper=TOPE_MIN)

    # ia_reaccion: noticia de relevancia 2 y novedad 1 de la última hora con llegada más reciente
    base = rel[rel["novedad"] == 1].sort_values("llego").drop_duplicates("simbolo", keep="last").set_index("simbolo")
    sin_noticia = [s for s in simbolos if s not in base.index]
    if precios is None:
        out["ia_reaccion"] = np.nan
    else:
        out["ia_reaccion"] = 0.0
        p1 = precios(momento)
        cache: dict = {}
        for s in base.index.intersection(simbolos):
            t0 = base.at[s, "llego"]
            if t0 not in cache:
                p0 = precios(t0)
                r = (p1 / p0 - 1).replace([np.inf, -np.inf], np.nan)
                cache[t0] = r - r.reindex(ACCIONES).mean()
            rr = cache[t0].get(s, np.nan)
            out.at[s, "ia_reaccion"] = np.sign(base.at[s, "tono"]) * rr if pd.notna(rr) else np.nan
        out.loc[sin_noticia, "ia_reaccion"] = 0.0
    return out[COLUMNAS]


# ---------------------------------------------------------------- pruebas

def probar() -> None:
    """Base pequeña en memoria con casos hechos a mano; momento = 2024-01-09 10:00 en Nueva York (15:00 UTC)."""
    con = abrir_base(":memory:")
    momento = pd.Timestamp("2024-01-09 15:00", tz="UTC")
    calendario = pd.DataFrame({"cierre": pd.to_datetime(["2024-01-08 16:00", "2024-01-09 16:00"])})   # cierre en hora de NY
    n = [0]

    def noticia(simbolo, llego, tono=1, rel=2, nov=1, sorp=0, version="2024-01-09T09:00:00-05:00",
                valido=1, modelo=MODELO_DEFECTO, instr=VERSION_INSTRUCCIONES, evaluacion=True, id_=None):
        n[0] += 1
        i = id_ or n[0]
        con.execute("INSERT INTO respuestas_ia (noticia, version_noticia, modelo, version_instrucciones, intento, "
                    "recibida_utc, valido) VALUES (?,?,?,?,?,?,?)",
                    (i, version, modelo, instr, 1, llego, valido))
        if evaluacion:
            con.execute("INSERT OR REPLACE INTO evaluaciones_ia (noticia, version_noticia, modelo, version_instrucciones, "
                        "simbolo, relevancia, tono, novedad, sorpresa) VALUES (?,?,?,?,?,?,?,?,?)",
                        (i, version, modelo, instr, simbolo, rel, tono, nov, sorp))
        return i

    # AAPL: llega justo antes (cuenta) y justo después (no cuenta) del momento
    noticia("AAPL", "2024-01-09T14:30:00.000+00:00", tono=2, sorp=1)
    noticia("AAPL", "2024-01-09T14:59:00.000+00:00", tono=1, sorp=1)
    noticia("AAPL", "2024-01-09T15:00:01.000+00:00", tono=-2, sorp=2)
    # MSFT: novedad 0 (no suma tono, pero sí es relevante y sorprendente)
    noticia("MSFT", "2024-01-09T14:40:00.000+00:00", tono=2, nov=0, sorp=2)
    # NVDA: dos versiones de la misma noticia; la 2 sustituye a la 1; la 3 llega después del momento
    i = noticia("NVDA", "2024-01-09T14:20:00.000+00:00", tono=2, version="2024-01-09T09:00:00-05:00")
    noticia("NVDA", "2024-01-09T14:50:00.000+00:00", tono=-1, version="2024-01-09T09:45:00-05:00", id_=i)
    noticia("NVDA", "2024-01-09T15:05:00.000+00:00", tono=2, version="2024-01-09T10:01:00-05:00", id_=i)
    # AMZN: primer intento inválido, segundo válido (cuenta desde la llegada del válido)
    i = noticia("AMZN", "2024-01-09T14:30:00.000+00:00", valido=0, evaluacion=False)
    con.execute("INSERT INTO respuestas_ia (noticia, version_noticia, modelo, version_instrucciones, intento, recibida_utc, valido) "
                "VALUES (?,?,?,?,?,?,?)", (i, "2024-01-09T09:00:00-05:00", MODELO_DEFECTO, VERSION_INSTRUCCIONES, 2,
                                           "2024-01-09T14:45:00.000+00:00", 1))
    con.execute("INSERT INTO evaluaciones_ia (noticia, version_noticia, modelo, version_instrucciones, simbolo, relevancia, tono, novedad, sorpresa) "
                "VALUES (?,?,?,?,?,?,?,?,?)", (i, "2024-01-09T09:00:00-05:00", MODELO_DEFECTO, VERSION_INSTRUCCIONES, "AMZN", 2, 2, 1, 0))
    # GOOGL: solo respuestas inválidas (aunque haya una evaluación registrada, no cuenta)
    noticia("GOOGL", "2024-01-09T14:50:00.000+00:00", tono=2, valido=0)
    # META: una noticia nocturna (después del cierre anterior) y otra de antes del cierre
    noticia("META", "2024-01-08T22:00:00.000+00:00", tono=-2, sorp=2)
    noticia("META", "2024-01-08T20:00:00.000+00:00", tono=2)
    # AMD: llegó hace 61 minutos: fuera de la hora, dentro de la noche; relevancia 1
    noticia("AMD", "2024-01-09T13:59:00.000+00:00", tono=2, rel=1)
    # JPM: otro modelo y otra versión de instrucciones: se ignoran
    noticia("JPM", "2024-01-09T14:50:00.000+00:00", modelo="otro-modelo")
    noticia("JPM", "2024-01-09T14:51:00.000+00:00", instr="v2")
    # TSLA: sin noticias
    con.commit()

    def precios(t):          # todas valen 100; AAPL sube a 101 desde las 15:00
        p = pd.Series(100.0, index=ACCIONES)
        if t >= momento:
            p["AAPL"] = 101.0
        return p

    simbolos = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AMD", "JPM", "TSLA"]
    v = variables_ia(con, momento, simbolos, precios, calendario=calendario)
    print(v.to_string())

    def igual(s, col, esperado):
        x = v.at[s, col]
        assert abs(x - esperado) < 1e-9, (s, col, x, esperado)

    # AAPL: (2*2 + 1*2)/2 = 3; la que llega 1 s tarde no entra; sorpresa máx 1; 2 relevantes; última hace 1 min
    igual("AAPL", "ia_tono_60m", 3); igual("AAPL", "ia_sorpresa_60m", 1); igual("AAPL", "ia_relevantes_60m", 2)
    igual("AAPL", "ia_tono_noche", 3); igual("AAPL", "ia_min_desde_relevante", 1)
    igual("AAPL", "ia_reaccion", 0.01 - 0.0002)                    # tono +1; AAPL +1%, promedio de las 50 +0,02%
    # MSFT: novedad 0 -> tono 0 y sin reacción, pero cuenta como relevante con sorpresa 2
    igual("MSFT", "ia_tono_60m", 0); igual("MSFT", "ia_sorpresa_60m", 2); igual("MSFT", "ia_relevantes_60m", 1)
    igual("MSFT", "ia_min_desde_relevante", 20); igual("MSFT", "ia_reaccion", 0)
    # NVDA: manda la versión 2 (tono -1, llegó hace 10 min); la 3 llega después
    igual("NVDA", "ia_tono_60m", -1); igual("NVDA", "ia_relevantes_60m", 1); igual("NVDA", "ia_min_desde_relevante", 10)
    igual("NVDA", "ia_reaccion", 0.0002)                           # signo -1 por (0 - 0,0002)
    # AMZN: el intento válido llegó a las 14:45
    igual("AMZN", "ia_tono_60m", 2); igual("AMZN", "ia_min_desde_relevante", 15)
    # GOOGL: nada (respuesta inválida)
    for c, e in [("ia_tono_60m", 0), ("ia_relevantes_60m", 0), ("ia_tono_noche", 0), ("ia_min_desde_relevante", TOPE_MIN), ("ia_reaccion", 0)]:
        igual("GOOGL", c, e)
    # META: la nocturna cuenta en la noche (tono -2), la anterior al cierre no; nada en la última hora
    igual("META", "ia_tono_noche", -2); igual("META", "ia_tono_60m", 0); igual("META", "ia_relevantes_60m", 0)
    igual("META", "ia_min_desde_relevante", 17 * 60)               # de 22:00 a 15:00 del día siguiente
    # AMD: fuera de la hora; relevancia 1 y tono 2 * 1 / 2 = 1 en la noche
    igual("AMD", "ia_tono_60m", 0); igual("AMD", "ia_tono_noche", 1); igual("AMD", "ia_min_desde_relevante", TOPE_MIN)
    # JPM y TSLA: sin noticias que cuenten
    for s in ("JPM", "TSLA"):
        for c, e in [("ia_tono_60m", 0), ("ia_sorpresa_60m", 0), ("ia_relevantes_60m", 0), ("ia_tono_noche", 0),
                     ("ia_min_desde_relevante", TOPE_MIN), ("ia_reaccion", 0)]:
            igual(s, c, e)
    # sin precios: ia_reaccion es NaN y lo demás no cambia
    w = variables_ia(con, momento, simbolos, calendario=calendario)
    assert w["ia_reaccion"].isna().all() and w.drop(columns="ia_reaccion").equals(v.drop(columns="ia_reaccion"))
    # un momento posterior (la respuesta que llegó 1 s tarde ya cuenta)
    x = variables_ia(con, momento + pd.Timedelta(minutes=1), ["AAPL"], calendario=calendario)
    assert x.at["AAPL", "ia_tono_60m"] == 3 - 2 * 2 / 2 and x.at["AAPL", "ia_sorpresa_60m"] == 2, x
    print("Pruebas de variables_ia: OK")


# ---------------------------------------------------------------- resumen

def resumen(ruta: str) -> None:
    con = sqlite3.connect(ruta)
    llegadas = pd.read_sql("SELECT recibida_utc FROM respuestas_ia WHERE valido = 1", con)
    if llegadas.empty:
        sys.exit("La base no tiene respuestas válidas.")
    ultimo = pd.to_datetime(llegadas["recibida_utc"], utc=True, format="ISO8601").max().tz_convert(NY).normalize()
    print(f"Último día con respuestas válidas: {ultimo:%Y-%m-%d}  (sin precios: ia_reaccion = NaN)")
    cal = pd.read_parquet(CALENDARIO)
    filas = []
    for m in pd.date_range(ultimo + pd.Timedelta(hours=10), ultimo + pd.Timedelta(hours=12, minutes=30), freq="30min"):
        v = variables_ia(con, m.tz_convert("UTC"), ACCIONES, calendario=cal)
        f = {"hora NY": f"{m:%H:%M}"}
        for c in COLUMNAS:
            f[c] = int((v[c] < TOPE_MIN).sum()) if c == "ia_min_desde_relevante" else int(v[c].fillna(0).ne(0).sum())
        filas.append(f)
    print(f"Acciones (de {len(ACCIONES)}) con la variable distinta de cero (ia_min_desde_relevante: con valor < {TOPE_MIN:,}):")
    print(pd.DataFrame(filas).set_index("hora NY").to_string())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--probar", action="store_true", help="pruebas con una base pequeña en memoria")
    ap.add_argument("--resumen", metavar="RUTA_BASE", help="acciones con cada variable distinta de cero, último día, 10:00 a 12:30 NY")
    a = ap.parse_args()
    if a.probar:
        probar()
    elif a.resumen:
        resumen(a.resumen)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
