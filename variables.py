"""
Paso 2.2 · Variables: arma la tabla con la que se entrenan y evalúan los modelos.

Una fila por acción y por momento de decisión. Los momentos de decisión son
cada 15 minutos en horario normal, de 9:45 a 15:45 de Nueva York.

Regla de oro: cada variable usa solo información anterior al momento de
decisión. En el momento t se conocen las velas que empezaron antes de t.
Se entra un minuto después (al cierre de la vela que empieza en t) y se sale
h minutos más tarde; ese retorno es el objetivo que el modelo intenta predecir.

Uso:
    python variables.py                    # los 53 símbolos, todos los años
    python variables.py --desde 2020

Salida:
    datos/variables/AAAA.parquet   (un archivo por año, todas las acciones)

Columnas
  Identificación: symbol, sector, es_etf, momento (UTC), dia, minuto (desde las 9:30), dia_semana
  Retornos pasados: ret_5, ret_15, ret_30, ret_60 (minutos), ret_apertura (desde la
      apertura), ret_noche (cierre de ayer a apertura de hoy), ret_ayer, ret_5d, ret_20d
  Volatilidad: vol_30, vol_60 (de los retornos de 1 minuto), vol_20d (diaria),
      rango_dia (máximo menos mínimo del día, sobre el precio)
  Posición: pos_rango (0 = mínimo del día, 1 = máximo), dist_vwap (precio frente al
      precio promedio ponderado del día)
  Volumen: volrel_15 y volrel_dia (volumen frente al de las mismas horas en los
      20 días anteriores), dolares_20d (logaritmo del monto diario negociado)
  Mercado: beta_60d (frente a SPY), mkt_ret_15, mkt_ret_60, mkt_ret_apertura,
      y los retornos propios sin la parte del mercado: res_15, res_60, res_apertura
  Noticias (solo conteos, sin IA): not_60m (últimos 60 minutos), not_desde_cierre
      (desde las 16:00 del día anterior), min_desde_noticia
  Objetivos: obj_15, obj_30, obj_60 (retorno futuro) y rel_15, rel_30, rel_60 (el
      mismo retorno menos el promedio de las acciones en ese momento)

Los retornos son logarítmicos. Los precios vienen ajustados por splits,
dividendos y escisiones (precios.py), así que los retornos entre días son correctos.
"""

import argparse
import warnings

import numpy as np
import pandas as pd

import precios
from descargar_datos import RAIZ, SECTOR, UNIVERSO

CARPETA = RAIZ / "variables"
ZONA = "America/New_York"
APERTURA = 9 * 60 + 30
MINUTOS = 390                       # 9:30 a 16:00
REJILLA = list(range(15, MINUTOS, 15))   # momentos de decisión: 9:45, 10:00, ..., 15:45
HORIZONTES = [15, 30, 60]
MAX_SIMBOLOS_POR_NOTICIA = 3


def matrices(simbolo: str, df: pd.DataFrame | None = None) -> dict:
    """Matrices días x 390 minutos del horario normal: cierre, máximo, mínimo, volumen y monto.
    `df` (opcional): velas ya cargadas y ajustadas; si no se da, se leen de precios.cargar."""
    df = precios.cargar(simbolo) if df is None else df.copy()
    local = df["timestamp"].dt.tz_convert(ZONA)
    df["minuto"] = local.dt.hour * 60 + local.dt.minute - APERTURA
    df = df[(df["minuto"] >= 0) & (df["minuto"] < MINUTOS)]
    dias = pd.DatetimeIndex(np.sort(df["dia"].unique()))
    f, c = dias.get_indexer(df["dia"]), df["minuto"].values

    def matriz(columna, relleno=np.nan):
        m = np.full((len(dias), MINUTOS), relleno)
        m[f, c] = df[columna].values
        return m

    cierre_crudo = matriz("close")
    return dict(dias=dias, C=pd.DataFrame(cierre_crudo).ffill(axis=1).values, O=matriz("open"), H=matriz("high"), L=matriz("low"),
                V=matriz("volume", 0.0), PV=np.nan_to_num(matriz("vwap") * matriz("volume")))


def _hacia_atras(serie: np.ndarray, ventana: int, funcion: str) -> np.ndarray:
    """Estadístico de los `ventana` días anteriores, sin incluir el día actual."""
    s = pd.DataFrame(serie) if serie.ndim == 2 else pd.Series(serie)
    return getattr(s.rolling(ventana, min_periods=ventana // 2), funcion)().shift(1).values


def variables_del_dia(m: dict) -> dict:
    """Variables que valen igual para todo el día: se conocen antes de la apertura o en ella."""
    cierre = m["C"][:, -1]
    apertura = pd.DataFrame(m["O"]).bfill(axis=1).values[:, 0]
    ayer = np.roll(cierre, 1); ayer[0] = np.nan
    ret_diario = np.log(cierre / ayer)                        # retorno de cada día, cierre a cierre
    def atras(n):                                             # cierre de hace n días
        x = np.roll(cierre, n).astype(float); x[:n] = np.nan
        return x
    monto = (m["PV"]).sum(axis=1)
    return dict(apertura=apertura, ret_diario=ret_diario,
                ret_noche=np.log(apertura / ayer), ret_ayer=np.log(ayer / atras(2)),
                ret_5d=np.log(ayer / atras(6)), ret_20d=np.log(ayer / atras(21)),
                vol_20d=_hacia_atras(ret_diario, 20, "std"),
                dolares_20d=np.log(_hacia_atras(monto, 20, "mean")))


def variables_del_momento(m: dict, k: int, apertura: np.ndarray) -> dict:
    """Variables en el minuto k: solo usan las velas 0 .. k-1 del día."""
    C, H, L, V, PV = m["C"], m["H"], m["L"], m["V"], m["PV"]
    c = C[:, k - 1]                                           # último precio conocido
    v = {f"ret_{h}": np.log(c / C[:, k - 1 - h]) if k - 1 - h >= 0 else np.full(len(c), np.nan) for h in (5, 15, 30, 60)}
    v["ret_apertura"] = np.log(c / apertura)

    r1 = np.diff(np.log(C[:, :k]), axis=1)                    # retornos de 1 minuto hasta ahora
    for n in (30, 60):
        v[f"vol_{n}"] = np.sqrt(np.nanmean(r1[:, -n:] ** 2, axis=1)) if r1.shape[1] >= n else np.full(len(c), np.nan)

    alto, bajo = np.nanmax(H[:, :k], axis=1), np.nanmin(L[:, :k], axis=1)
    v["rango_dia"] = (alto - bajo) / c
    v["pos_rango"] = np.where(alto > bajo, (c - bajo) / (alto - bajo), 0.5)
    vol_acum = V[:, :k].sum(axis=1)
    v["dist_vwap"] = c / (PV[:, :k].sum(axis=1) / np.where(vol_acum > 0, vol_acum, np.nan)) - 1

    vol_15 = V[:, k - 15:k].sum(axis=1)
    v["volrel_15"] = vol_15 / _hacia_atras(vol_15, 20, "mean")
    v["volrel_dia"] = vol_acum / _hacia_atras(vol_acum, 20, "mean")
    return v


def objetivos(m: dict, k: int) -> dict:
    """Retorno futuro: se entra al cierre de la vela k y se sale h minutos después, dentro del mismo día."""
    C = m["C"]
    return {f"obj_{h}": np.log(C[:, k + h] / C[:, k]) if k + h < MINUTOS else np.full(len(C), np.nan) for h in HORIZONTES}


def conteo_noticias(momentos_utc: np.ndarray, cierre_previo_utc: np.ndarray, noticias_utc: np.ndarray) -> dict:
    """Cuántas noticias había antes de cada momento. `noticias_utc` debe venir ordenado."""
    hasta = np.searchsorted(noticias_utc, momentos_utc, side="left")       # noticias anteriores al momento
    hora = np.timedelta64(60, "m")
    desde_60 = np.searchsorted(noticias_utc, momentos_utc - hora, side="left")
    desde_cierre = np.searchsorted(noticias_utc, cierre_previo_utc, side="left")
    if len(noticias_utc):
        ultima = np.where(hasta > 0, noticias_utc[np.maximum(hasta - 1, 0)], np.datetime64("NaT"))
    else:                                                                   # símbolo sin noticias (SPY, GOOGL en vivo)
        ultima = np.full(len(momentos_utc), np.datetime64("NaT"), dtype="datetime64[ns]")
    minutos = (momentos_utc - ultima) / np.timedelta64(1, "m")
    return dict(not_60m=hasta - desde_60, not_desde_cierre=np.maximum(hasta - desde_cierre, 0),
                min_desde_noticia=np.where(hasta > 0, np.minimum(minutos, 10_000), 10_000))


def tabla_simbolo(simbolo: str, noticias_utc: np.ndarray, m: dict | None = None) -> pd.DataFrame:
    m = matrices(simbolo) if m is None else m
    dias, n = m["dias"], len(m["dias"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # días sin operaciones al comienzo de la sesión
        del_dia = variables_del_dia(m)
        apertura_utc = (dias + pd.Timedelta(minutes=APERTURA)).tz_localize(ZONA).tz_convert("UTC").tz_localize(None).values
        cierre_utc = apertura_utc + np.timedelta64(MINUTOS, "m")
        cierre_previo = np.roll(cierre_utc, 1); cierre_previo[0] = cierre_utc[0] - np.timedelta64(1, "D")
        trozos = []
        for k in REJILLA:
            momento = apertura_utc + np.timedelta64(k, "m")
            fila = dict(symbol=simbolo, momento=momento, dia=dias.values, minuto=k)
            fila.update(variables_del_momento(m, k, del_dia["apertura"]))
            fila.update({c: del_dia[c] for c in ("ret_noche", "ret_ayer", "ret_5d", "ret_20d", "vol_20d", "dolares_20d", "ret_diario")})
            fila.update(conteo_noticias(momento, cierre_previo, noticias_utc))
            fila.update(objetivos(m, k))
            trozos.append(pd.DataFrame(fila))
    t = pd.concat(trozos, ignore_index=True)
    return t[np.isfinite(t["ret_apertura"])]   # sin precio todavía ese día: no hay nada que decidir


def noticias_por_simbolo() -> dict[str, np.ndarray]:
    n = pd.concat([pd.read_parquet(a, columns=["id", "created_at", "symbols"]) for a in sorted((RAIZ / "noticias").glob("*.parquet"))])
    n = n.drop_duplicates("id")
    n = n[n["symbols"].str.len() <= MAX_SIMBOLOS_POR_NOTICIA].explode("symbols")
    n["utc"] = n["created_at"].dt.tz_localize(None).astype("datetime64[ns]")
    return {s: np.sort(g["utc"].values) for s, g in n.groupby("symbols")}


def agregar_mercado(t: pd.DataFrame) -> pd.DataFrame:
    """Suma las variables del mercado (SPY), la beta y los retornos sin la parte del mercado."""
    spy = t.loc[t["symbol"] == "SPY", ["dia", "minuto", "ret_15", "ret_60", "ret_apertura", "ret_diario"]]
    spy = spy.rename(columns={"ret_15": "mkt_ret_15", "ret_60": "mkt_ret_60", "ret_apertura": "mkt_ret_apertura", "ret_diario": "mkt_diario"})
    t = t.merge(spy, on=["dia", "minuto"], how="left")

    # Beta: con los retornos diarios de los 60 días anteriores.
    d = t.drop_duplicates(["symbol", "dia"])[["symbol", "dia", "ret_diario", "mkt_diario"]].sort_values(["symbol", "dia"])
    g = d.groupby("symbol", sort=False)
    cov = g.apply(lambda x: x["ret_diario"].rolling(60, min_periods=30).cov(x["mkt_diario"]).shift(1), include_groups=False)
    var = g["mkt_diario"].transform(lambda x: x.rolling(60, min_periods=30).var().shift(1))
    d["beta_60d"] = cov.values / var.values
    t = t.merge(d[["symbol", "dia", "beta_60d"]], on=["symbol", "dia"], how="left")

    for c in ("15", "60", "apertura"):
        t[f"res_{c}"] = t[f"ret_{c}"] - t["beta_60d"].fillna(1.0) * t[f"mkt_ret_{c}"]
    return t.drop(columns=["ret_diario", "mkt_diario"])


def agregar_relativos(t: pd.DataFrame) -> pd.DataFrame:
    """Objetivo relativo: el retorno futuro menos el promedio de las acciones (sin ETF) en ese momento."""
    acciones = t[~t["es_etf"]]
    for h in HORIZONTES:
        media = acciones.groupby("momento")[f"obj_{h}"].mean().rename("media")
        t[f"rel_{h}"] = t[f"obj_{h}"] - t["momento"].map(media)
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description="Arma la tabla de variables para los modelos.")
    ap.add_argument("--desde", type=int, default=2016, help="Primer año a guardar (por defecto 2016)")
    ap.add_argument("--simbolos", nargs="+", default=UNIVERSO, help="Lista de símbolos (SPY siempre se incluye)")
    args = ap.parse_args()

    simbolos = list(dict.fromkeys(["SPY", *args.simbolos]))
    noticias = noticias_por_simbolo()
    partes = []
    for i, s in enumerate(simbolos, 1):
        partes.append(tabla_simbolo(s, noticias.get(s, np.array([], dtype="datetime64[ns]"))))
        print(f"[{i}/{len(simbolos)}] {s}: {len(partes[-1]):,} filas")

    t = pd.concat(partes, ignore_index=True)
    t["sector"] = t["symbol"].map(SECTOR)
    t["es_etf"] = t["sector"] == "etf"
    t["dia_semana"] = pd.DatetimeIndex(t["dia"]).dayofweek.astype("int8")
    t = agregar_relativos(agregar_mercado(t))
    t["momento"] = pd.DatetimeIndex(t["momento"]).tz_localize("UTC")
    numericas = t.select_dtypes("float64").columns
    t[numericas] = t[numericas].astype("float32")
    t[["minuto", "not_60m", "not_desde_cierre"]] = t[["minuto", "not_60m", "not_desde_cierre"]].astype("int32")

    CARPETA.mkdir(parents=True, exist_ok=True)
    anios = pd.DatetimeIndex(t["dia"]).year
    for anio in sorted(set(anios[anios >= args.desde])):
        trozo = t[anios == anio].sort_values(["momento", "symbol"], ignore_index=True)
        temporal = CARPETA / f"{anio}.parquet.tmp"
        trozo.to_parquet(temporal, index=False)
        temporal.replace(CARPETA / f"{anio}.parquet")
        print(f"   {anio}: {len(trozo):,} filas")
    print(f"\nListo. {len(t.columns)} columnas en {CARPETA}")


if __name__ == "__main__":
    main()
