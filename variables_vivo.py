"""
Fase 3 · Variables en vivo: las 51 entradas del modelo de velas (B) en un momento de decisión.

Hoy las variables se arman por lotes (variables.py guarda el año completo y
modelo_velas.cargar() agrega los puestos p_* y las diferencias con el sector s_*).
Aquí se calculan, en el momento k, solo para ese momento y con lo que se sabe en él.

Regla de oro: solo información anterior a k. En el minuto k (desde las 9:30) se
conocen las velas que empezaron antes de k, es decir, hasta la vela k-1.
  - Velas de 1 minuto del día hasta la vela k-1, más los días anteriores
    (ret_noche, ret_ayer, ret_5d, ret_20d, vol_20d, dolares_20d, volrel_*, beta_60d).
  - Noticias con hora anterior a k (máximo 3 símbolos por noticia, como en variables.py).
  - SPY, para mkt_* y res_*.
  - Los ajustes de precio de precios.py, solo los que ya habían ocurrido a ese día.
La función recorta las velas y las noticias a ese límite por su cuenta, aunque la
fuente traiga más: lo posterior no puede influir.

No se reescribe ninguna fórmula: se llama a variables.py (matrices, tabla_simbolo,
agregar_mercado) con las velas recortadas a una ventana de VENTANA_DIAS días, y los
puestos y diferencias con el sector se calculan entre las 50 acciones, igual que cargar().

La fuente de las velas es una función `fuente(simbolo) -> DataFrame` con las velas
SIN ajustar (columnas de datos/minuto: timestamp UTC, open, high, low, close, volume,
vwap, y `dia`). Hoy lee datos/minuto (velas_de_archivos); la descarga en vivo se
cambia pasando otra función con la misma forma.

Diferencia inevitable con lo histórico: dolares_20d. En variables.py los precios se
ajustan con los dividendos de TODO el historial, incluidos los posteriores al día;
en vivo solo se conocen los anteriores. Para ese día, el monto en dólares de los
días viejos queda unos puntos básicos distinto (el ajuste por dividendos escala el
monto). Ver la prueba.

Uso:
    from variables_vivo import variables_del_momento_en_vivo
    t = variables_del_momento_en_vivo(pd.Timestamp("2024-05-14"), 60)
    python variables_vivo.py --probar 10     # prueba de paridad contra datos/variables

Salida:
    DataFrame con una fila por acción (50, sin ETF): symbol, dia, momento (UTC) y las
    columnas de entrada del modelo, en el orden de modelo_velas.cargar().
"""

import argparse
import functools
import time
import warnings

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

import modelo_velas
import precios
import referencia
import variables
from descargar_datos import RAIZ, SECTOR, UNIVERSO

ACCIONES = [s for s in UNIVERSO if SECTOR[s] != "etf"]
MOMENTOS = [30, 60, 90, 120, 150, 180]
VENTANA_DIAS = 110          # días calendario de historia (~75 sesiones): caben la beta de 60 días y los 20 días de volumen
_CRUDAS: dict[str, pd.DataFrame] = {}
_NOTICIAS: dict[str, np.ndarray] = {}
precios._ajustes = functools.cache(precios._ajustes)    # las tablas de ajustes se leen una vez, no por símbolo


# ---------------------------------------------------------------- fuentes

def velas_de_archivos(simbolo: str) -> pd.DataFrame:
    """Velas de 1 minuto sin ajustar, de datos/minuto (se leen una sola vez por símbolo)."""
    if simbolo not in _CRUDAS:
        _CRUDAS[simbolo] = precios.cargar(simbolo, ajuste=None)
    return _CRUDAS[simbolo]


def noticias_de_archivos() -> dict[str, np.ndarray]:
    """Noticias por símbolo (hora UTC ordenada), con el mismo filtro de variables.py."""
    if not _NOTICIAS:
        _NOTICIAS.update(variables.noticias_por_simbolo())
    return _NOTICIAS


# ---------------------------------------------------------------- cálculo

def columnas_del_modelo() -> list[str]:
    """Columnas de entrada, en el orden de modelo_velas.cargar() (se leen del esquema de la tabla)."""
    esquema = pq.read_schema(variables.CARPETA / "2024.parquet").names
    base = [c for c in esquema if c not in modelo_velas.NO_SON_VARIABLES] + ["sector_n"]
    return base + [f"p_{c}" for c in modelo_velas.CON_PUESTO] + [f"s_{c}" for c in modelo_velas.CON_SECTOR]


def _ajustar(crudas: pd.DataFrame, simbolo: str) -> pd.DataFrame:
    """Mismo ajuste que precios.cargar(ajuste='total'), pero con las velas ya recortadas:
    solo cuentan los splits y dividendos con fecha hasta el último día que hay."""
    df = crudas.copy()
    local = df["timestamp"].dt.tz_convert(precios.ZONA)
    minuto = local.dt.hour * 60 + local.dt.minute
    regular = (minuto >= 9 * 60 + 30) & (minuto < 16 * 60)
    cierres = df.loc[regular].groupby("dia")["close"].last()
    cierres = cierres.reindex(np.sort(df["dia"].unique())).ffill().bfill()
    f = precios.factores(simbolo, cierres)
    f_splits = df["dia"].map(f["splits"]).values
    f_precio = f_splits * df["dia"].map(f["dividendos"] * f["escisiones"]).values
    df[precios.COLUMNAS_PRECIO] = df[precios.COLUMNAS_PRECIO].mul(f_precio, axis=0)
    df["volume"] = df["volume"] / f_splits
    return df


def variables_del_momento_en_vivo(dia: pd.Timestamp, k: int, fuente=velas_de_archivos, noticias=None) -> pd.DataFrame:
    """Las columnas de entrada del modelo para las 50 acciones, en el minuto k (desde las 9:30) de `dia`."""
    dia = pd.Timestamp(dia).normalize()
    if k not in variables.REJILLA:
        raise ValueError(f"k debe estar en {variables.REJILLA}, no {k}")
    momento = (dia + pd.Timedelta(minutes=variables.APERTURA + k)).tz_localize(variables.ZONA).tz_convert("UTC")
    noticias = noticias_de_archivos() if noticias is None else noticias
    vacias = np.array([], dtype="datetime64[ns]")
    momento_naive = momento.tz_localize(None).to_datetime64()

    tablas = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for s in ["SPY", *ACCIONES]:
            crudas = fuente(s)
            ts = crudas["timestamp"].values                                         # ordenadas por hora
            fin = np.searchsorted(ts, momento.tz_convert("UTC").tz_localize(None).to_datetime64(), side="left")
            ini = np.searchsorted(crudas["dia"].values, (dia - pd.Timedelta(days=VENTANA_DIAS)).to_datetime64(), side="left")
            crudas = crudas.iloc[ini:fin]                                           # nada desde el minuto k en adelante
            if crudas.empty or crudas["dia"].iloc[-1] != dia:
                continue
            m = variables.matrices(s, _ajustar(crudas, s))
            n = noticias.get(s, vacias)
            n = n[n < momento_naive]                                                # solo noticias anteriores a k
            t = variables.tabla_simbolo(s, n, m)
            t = t[(t["dia"] < dia) | (t["minuto"] <= k)]                            # las filas posteriores a k no son reales
            tablas.append(t)
        t = pd.concat(tablas, ignore_index=True)
        t = variables.agregar_mercado(t)

    t = t[(t["dia"] == dia) & (t["minuto"] == k) & (t["symbol"] != "SPY")].copy()
    t["sector"] = t["symbol"].map(SECTOR)
    t["dia_semana"] = pd.DatetimeIndex(t["dia"]).day_of_week.astype("int8")
    t["momento"] = pd.DatetimeIndex(t["momento"]).tz_localize("UTC")
    numericas = t.select_dtypes("float64").columns
    t[numericas] = t[numericas].astype("float32")
    t[["minuto", "not_60m", "not_desde_cierre"]] = t[["minuto", "not_60m", "not_desde_cierre"]].astype("int32")
    return _agregar_comparativas(t.reset_index(drop=True))


def _agregar_comparativas(t: pd.DataFrame) -> pd.DataFrame:
    """sector_n, p_* y s_*: igual que modelo_velas.cargar(), entre las acciones de este momento."""
    t = t.sort_values("symbol", ignore_index=True)       # mismo orden que la tabla histórica (suma en float32 idéntica)
    t["sector_n"] = t["sector"].map({s: i for i, s in enumerate(sorted(set(SECTOR[a] for a in ACCIONES)))}).astype("int8")
    puestos = t.groupby("momento")[modelo_velas.CON_PUESTO].rank(pct=True).astype("float32")
    t[[f"p_{c}" for c in modelo_velas.CON_PUESTO]] = puestos.values
    del_sector = t.groupby(["momento", "sector_n"])[modelo_velas.CON_SECTOR].transform("mean")
    t[[f"s_{c}" for c in modelo_velas.CON_SECTOR]] = (t[modelo_velas.CON_SECTOR] - del_sector).values
    return t[["symbol", "dia", "momento", *columnas_del_modelo()]]


# ---------------------------------------------------------------- prueba de paridad

def _historica(anio: int, dias: list) -> pd.DataFrame:
    """Filas históricas de esos días con la lógica de cargar(), sin su filtro de años."""
    t = pd.read_parquet(variables.CARPETA / f"{anio}.parquet")
    t = t[~t["es_etf"] & t["dia"].isin(dias)].reset_index(drop=True)
    return _agregar_comparativas(t).set_index(["symbol", "dia", "minuto"], drop=False)


def _comparar(vivo: pd.DataFrame, hist: pd.DataFrame, acumulado: dict) -> None:
    v = vivo.set_index(["symbol", "dia", "minuto"], drop=False).sort_index()
    h = hist.loc[v.index]
    for c in columnas_del_modelo():
        a, b = v[c].to_numpy("float64"), h[c].to_numpy("float64")
        nan = np.isnan(a) != np.isnan(b)
        ok = ~np.isnan(a) & ~np.isnan(b)
        dif = np.abs(a - b)
        malas = nan | (ok & (dif > 1e-6 * np.maximum(np.abs(a), np.abs(b)) + 1e-30) & (dif > 0))
        e = acumulado.setdefault(c, dict(max=0.0, filas=0, malas=0, nan=0, dia_peor=None))
        e["filas"] += len(a); e["malas"] += int(malas.sum()); e["nan"] += int(nan.sum())
        if ok.any() and np.nanmax(dif[ok]) > e["max"]:
            e["max"] = float(np.nanmax(dif[ok])); e["dia_peor"] = str(v.index.get_level_values("dia")[ok][np.argmax(dif[ok])].date())


def probar(n: int) -> None:
    z = np.load(referencia.CARPETA / "cierres.npz")
    medios = set(pd.DatetimeIndex(z["dias"][z["medio_dia"]]))
    rng = np.random.default_rng(7)
    elegidos = []
    for anio in (2023, 2024, 2026):
        d = pd.DatetimeIndex(pd.read_parquet(variables.CARPETA / f"{anio}.parquet", columns=["dia"])["dia"].unique())
        d = [x for x in d if x not in medios]
        elegidos += [(anio, x) for x in rng.choice(np.array(d, dtype="datetime64[ns]"), size=n, replace=False)]
    elegidos = [(a, pd.Timestamp(x)) for a, x in elegidos]
    print(f"{len(elegidos)} días ({n} por año en 2023, 2024 y 2026), momentos {MOMENTOS}")

    historicas = {a: _historica(a, [d for aa, d in elegidos if aa == a]) for a in (2023, 2024, 2026)}
    acumulado, tiempos = {}, []
    for anio, dia in elegidos:
        for k in MOMENTOS:
            t0 = time.time()
            vivo = variables_del_momento_en_vivo(dia, k)
            tiempos.append(time.time() - t0)
            _comparar(vivo, historicas[anio], acumulado)
        print(f"  {dia.date()} listo")

    # Prueba de fuga: una fuente cuyas velas desde el minuto k están corrompidas no debe cambiar nada.
    anio, dia = elegidos[0]; k = 90
    limite = (dia + pd.Timedelta(minutes=variables.APERTURA + k)).tz_localize(variables.ZONA).tz_convert("UTC")
    def corrupta(s):
        d = velas_de_archivos(s).copy()
        despues = d["timestamp"] >= limite
        d.loc[despues & (d["dia"] == dia), ["open", "high", "low", "close", "vwap"]] *= 7.0
        d.loc[despues & (d["dia"] == dia), "volume"] *= 50.0
        return d
    base, sucia = variables_del_momento_en_vivo(dia, k), variables_del_momento_en_vivo(dia, k, fuente=corrupta)
    fuga = base.equals(sucia)

    print(f"\n{'columna':<20}{'dif. máx':>12}{'filas malas':>13}{'NaN distinto':>14}  día de la dif. máx")
    for c, e in acumulado.items():
        print(f"{c:<20}{e['max']:>12.3g}{e['malas']:>9}/{e['filas']:<5}{e['nan']:>9}  {e['dia_peor'] or ''}")
    tot = next(iter(acumulado.values()))["filas"]
    print(f"\nFilas comparadas por columna: {tot}. Columnas con filas malas: "
          f"{[c for c, e in acumulado.items() if e['malas']] or 'ninguna'}")
    print(f"Prueba de fuga (velas posteriores a k multiplicadas por 7): {'sin cambios' if fuga else 'CAMBIA, hay fuga'}")
    print(f"Tiempo por momento (50 acciones): media {np.mean(tiempos):.2f} s, máximo {np.max(tiempos):.2f} s "
          f"(la primera vez incluye leer los archivos: {tiempos[0]:.1f} s)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Variables del modelo de velas en un momento, solo con lo conocido.")
    ap.add_argument("--probar", type=int, metavar="N", help="Paridad con la tabla histórica en N días por año")
    ap.add_argument("--dia", help="Día AAAA-MM-DD a calcular")
    ap.add_argument("--k", type=int, default=60, help="Minuto desde las 9:30 (por defecto 60 = 10:30)")
    args = ap.parse_args()
    if args.probar:
        probar(args.probar)
    elif args.dia:
        print(variables_del_momento_en_vivo(pd.Timestamp(args.dia), args.k).to_string())
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
