"""
Paso 2.1 · Barrera de costos: ¿cuánto se mueve el precio frente a lo que cuesta operar?

Para cada acción, franja del día y horizonte (5, 15, 30 y 60 minutos) calcula:

  - Movimiento: cuánto cambia el precio en ese horizonte, en promedio y sin
    importar la dirección. Se mide dos veces: partiendo de un minuto cualquiera
    y partiendo del minuto en que sale una noticia de esa acción.
  - Costo: el spread medido por muestrear_spread.py. Entrar y salir cruzando el
    mercado cuesta un spread completo (medio al entrar y medio al salir).
  - Acierto mínimo: qué porcentaje de las veces hay que acertar la dirección
    para no perder plata.   acierto mínimo = 50% + costo / (2 x movimiento)

Unidades: bps = centésimas de punto porcentual (1 bps = 0,01%).

Uso:
    python barrera_costos.py                 # usa las velas desde 2023
    python barrera_costos.py --desde 2021

Salida:
    resultados/barrera_costos.csv   una fila por símbolo, franja y horizonte
    resultados/barrera_costos.md    resumen

Cómo leer las columnas de noticias:
  - mov_noticia_bps: se entra al cierre del minuto en que salió la noticia
    (hasta 60 segundos después). Es lo realista para un sistema que primero
    tiene que leerla.
  - mov_noticia_inmediato_bps: se entra justo antes de la noticia. Es un techo:
    incluye el salto del primer minuto, que casi nadie alcanza a capturar.
  - mov_esperado_hora_bps: lo que se mueve un minuto cualquiera a esas mismas
    horas del día. Las noticias se concentran en la apertura, cuando todo se
    mueve más; comparar contra esta cifra separa el efecto de la noticia del
    efecto de la hora.

Supuestos y límites:
  - Solo noticias que mencionan hasta 3 acciones (las que mencionan muchas son
    resúmenes de mercado).
  - Fuera del horario normal hay minutos sin operaciones; ahí el precio se toma
    como quieto, así que el movimiento en pre y post queda subestimado.
  - El acierto mínimo supone que se gana y se pierde lo mismo en promedio.
  - No incluye comisiones ni el deslizamiento por el tamaño de la orden.
"""

import argparse
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

from descargar_datos import RAIZ, UNIVERSO

SALIDA = RAIZ.parent / "resultados"
ZONA = "America/New_York"
HORIZONTES = [5, 15, 30, 60]
MIN0 = 4 * 60  # la rejilla de minutos empieza a las 4:00 de Nueva York
# Franjas en minutos desde las 4:00 (las mismas de muestrear_spread.py).
FRANJAS = {"pre": (180, 330), "sesion": (330, 720), "post": (720, 840)}
MAX_SIMBOLOS_POR_NOTICIA = 3


def rejilla(simbolo: str, desde: int) -> tuple[np.ndarray, pd.DatetimeIndex]:
    """Matriz días x minutos (4:00 a 20:00) con el cierre de cada minuto, arrastrando el último precio del día."""
    archivos = [a for a in sorted((RAIZ / "minuto" / simbolo).glob("*.parquet")) if int(a.stem) >= desde]
    df = pd.concat([pd.read_parquet(a, columns=["timestamp", "close"]) for a in archivos], ignore_index=True)
    local = df["timestamp"].dt.tz_convert(ZONA).dt.tz_localize(None)
    df["dia"] = local.dt.normalize()
    df["minuto"] = local.dt.hour * 60 + local.dt.minute - MIN0
    df = df[(df["minuto"] >= 0) & (df["minuto"] < 960)]
    dias = pd.DatetimeIndex(np.sort(df["dia"].unique()))
    m = np.full((len(dias), 960), np.nan)
    m[dias.get_indexer(df["dia"]), df["minuto"].values] = df["close"].values
    return pd.DataFrame(m).ffill(axis=1).values, dias


def noticias_por_simbolo(desde: int) -> pd.DataFrame:
    archivos = [a for a in sorted((RAIZ / "noticias").glob("*.parquet")) if int(a.stem[:4]) >= desde]
    n = pd.concat([pd.read_parquet(a, columns=["id", "created_at", "symbols"]) for a in archivos], ignore_index=True)
    n = n.drop_duplicates("id")
    n = n[n["symbols"].str.len() <= MAX_SIMBOLOS_POR_NOTICIA].explode("symbols").rename(columns={"symbols": "symbol"})
    local = n["created_at"].dt.tz_convert(ZONA).dt.tz_localize(None)
    n["dia"] = local.dt.normalize()
    n["minuto"] = local.dt.hour * 60 + local.dt.minute - MIN0
    return n[["symbol", "dia", "minuto"]].drop_duplicates()


def spreads() -> pd.DataFrame:
    archivos = sorted((RAIZ / "spread").glob("*.parquet"))
    if not archivos:
        raise SystemExit("Faltan las muestras de spread: correr primero muestrear_spread.py.")
    s = pd.concat([pd.read_parquet(a) for a in archivos], ignore_index=True)
    return s.groupby(["symbol", "franja"]).agg(
        spread_bps=("spread_bps", "median"), spread_p75_bps=("spread_bps", lambda x: x.quantile(0.75)),
        momentos_con_cotizacion=("cotizaciones", lambda x: float((x > 0).mean()))).reset_index()


def analizar(simbolo: str, precios: np.ndarray, dias: pd.DatetimeIndex, noticias: pd.DataFrame) -> list[dict]:
    filas = []
    fila_dia = dias.get_indexer(noticias["dia"])
    noticias = noticias.assign(fila=fila_dia)[fila_dia >= 0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # medias de minutos sin ningún precio
        logp = np.log(precios)
        for franja, (ini, fin) in FRANJAS.items():
            nf = noticias[(noticias["minuto"] >= ini) & (noticias["minuto"] < fin)]
            for h in HORIZONTES:
                if fin - ini <= h:
                    continue
                # Minuto cualquiera: entrar en t y salir en t+h, todo dentro de la franja.
                r = 1e4 * (logp[:, ini + h:fin] - logp[:, ini:fin - h])
                por_minuto = np.nanmean(np.abs(r), axis=0)  # movimiento típico a cada hora del día
                fila = dict(symbol=simbolo, franja=franja, horizonte=h, n_cualquiera=int(np.isfinite(r).sum()),
                            mov_cualquiera_bps=np.nanmean(np.abs(r)), mov_mediana_bps=np.nanmedian(np.abs(r)),
                            mov_p90_cualquiera_bps=np.nanpercentile(np.abs(r), 90), desv_bps=np.sqrt(np.nanmean(r ** 2)))
                # Tras noticia: solo las que dejan h minutos antes de que acabe la franja.
                n = nf[nf["minuto"] + h < fin]
                f, m = n["fila"].values, n["minuto"].values
                tras = 1e4 * (logp[f, m + h] - logp[f, m])
                antes = 1e4 * (logp[f, m + h] - logp[f, np.maximum(m - 1, 0)])
                ok = np.isfinite(tras)
                fila.update(n_noticias=int(ok.sum()),
                            mov_noticia_bps=np.nanmean(np.abs(tras)) if ok.any() else np.nan,
                            mov_p90_noticia_bps=np.nanpercentile(np.abs(tras), 90) if ok.any() else np.nan,
                            # Cuántas noticias van seguidas de un movimiento grande (mayor al que solo supera el 10% de los minutos).
                            noticias_mov_grande=float(np.nanmean(np.abs(tras[ok]) > fila["mov_p90_cualquiera_bps"])) if ok.any() else np.nan,
                            mov_noticia_inmediato_bps=np.nanmean(np.abs(antes)) if ok.any() else np.nan,
                            mov_esperado_hora_bps=np.nanmean(por_minuto[m[ok] - ini]) if ok.any() else np.nan,
                            desv_noticia_bps=np.sqrt(np.nanmean(tras ** 2)) if ok.any() else np.nan)
                filas.append(fila)
    return filas


def acierto_minimo(costo: pd.Series, movimiento: pd.Series) -> pd.Series:
    return (0.5 + costo / (2 * movimiento)).clip(upper=1.0)


def operaciones_necesarias(acierto: float, movimiento: float, costo: float, desviacion: float) -> float:
    """Operaciones para detectar la ganancia neta con 5% de significancia (una cola) y 80% de potencia."""
    ganancia = (2 * acierto - 1) * movimiento - costo
    return np.inf if ganancia <= 0 else ((1.645 + 0.842) * desviacion / ganancia) ** 2


def resumen(t: pd.DataFrame, desde: int) -> str:
    def num(x, d=1):
        return "—" if not np.isfinite(x) else f"{x:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")

    def pct(x):
        return "imposible" if x >= 1 else "—" if not np.isfinite(x) else num(100 * x) + "%"

    L = [f"# Barrera de costos (paso 2.1)", "",
         f"Generado el {datetime.now():%Y-%m-%d} con `barrera_costos.py`. Velas y noticias desde {desde}; spread de los últimos 60 días de mercado.",
         "", "Unidades: bps = centésimas de punto porcentual (1 bps = 0,01%). Las cifras son la mediana de los 53 símbolos, salvo donde se indica.", ""]

    L += ["## 1. Cuánto cuesta operar", "",
          "| Franja (hora de Nueva York) | Spread mediano | Símbolo más barato | Símbolo más caro | Momentos con cotización |",
          "| --- | --- | --- | --- | --- |"]
    nombres = {"pre": "Pre-mercado (7:00–9:30)", "sesion": "Horario normal (9:30–16:00)", "post": "Post-mercado (16:00–18:00)"}
    for f in FRANJAS:
        s = t[(t.franja == f) & (t.horizonte == 5)].set_index("symbol")
        L.append(f"| {nombres[f]} | {num(s.spread_bps.median())} bps | {s.spread_bps.idxmin()} ({num(s.spread_bps.min())}) | "
                 f"{s.spread_bps.idxmax()} ({num(s.spread_bps.max())}) | {num(100 * s.momentos_con_cotizacion.median(), 0)}% |")

    L += ["", "## 2. Cuánto se mueve el precio y qué acierto hace falta", "",
          "| Franja | Horizonte | Movimiento, minuto cualquiera | Movimiento tras noticia | Esperado por la hora | Acierto mínimo, minuto cualquiera | Acierto mínimo, tras noticia | Símbolos con acierto mínimo ≤ 55% tras noticia |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for f in FRANJAS:
        for h in HORIZONTES:
            s = t[(t.franja == f) & (t.horizonte == h)]
            if s.empty:
                continue
            L.append(f"| {nombres[f].split(' (')[0]} | {h} min | {num(s.mov_cualquiera_bps.median())} bps | {num(s.mov_noticia_bps.median())} bps | "
                     f"{num(s.mov_esperado_hora_bps.median())} bps | {pct(s.acierto_min_cualquiera.median())} | {pct(s.acierto_min_noticia.median())} | "
                     f"{int((s.acierto_min_noticia <= 0.55).sum())} de {int(s.acierto_min_noticia.notna().sum())} |")

    L += ["", "## 2b. ¿Todas las noticias mueven el precio?", "",
          "En horario normal. Un movimiento grande es el que solo supera el 10% de los minutos cualesquiera; si las noticias no importaran, el 10% de ellas iría seguido de uno.", "",
          "| Horizonte | Noticias seguidas de un movimiento grande | Movimiento del 10% más fuerte, minuto cualquiera | Movimiento del 10% más fuerte, tras noticia |",
          "| --- | --- | --- | --- |"]
    for h in HORIZONTES:
        s = t[(t.franja == "sesion") & (t.horizonte == h)]
        L.append(f"| {h} min | {num(100 * s.noticias_mov_grande.median())}% | {num(s.mov_p90_cualquiera_bps.median())} bps | {num(s.mov_p90_noticia_bps.median())} bps |")

    L += ["", "## 3. Si el costo real fuera el doble", "",
          "Las pruebas históricas suelen ser optimistas con el costo; esta tabla repite el acierto mínimo tras noticia con dos spreads en vez de uno.", "",
          "| Franja | Horizonte | Acierto mínimo tras noticia | Símbolos con acierto mínimo ≤ 55% |", "| --- | --- | --- | --- |"]
    for f in FRANJAS:
        for h in HORIZONTES:
            s = t[(t.franja == f) & (t.horizonte == h)]
            if s.empty:
                continue
            a = acierto_minimo(2 * s.spread_bps, s.mov_noticia_bps)
            L.append(f"| {nombres[f].split(' (')[0]} | {h} min | {pct(a.median())} | {int((a <= 0.55).sum())} de {int(a.notna().sum())} |")

    L += ["", "## 4. Cuántas operaciones harían falta en la Fase 3", "",
          "Operaciones para demostrar una ganancia neta con 5% de significancia y 80% de potencia, en horario normal y operando tras noticia, según el acierto real que logre el sistema. "
          "Se calcula solo con los símbolos baratos de operar (acierto mínimo de 55% o menos en ese horizonte), usando sus medianas.", "",
          "| Horizonte | Símbolos | Acierto 53% | Acierto 55% | Acierto 57% | Acierto 60% |", "| --- | --- | --- | --- | --- | --- |"]
    for h in HORIZONTES:
        s = t[(t.franja == "sesion") & (t.horizonte == h) & (t.acierto_min_noticia <= 0.55)]
        mov, costo, desv = s.mov_noticia_bps.median(), s.spread_bps.median(), s.desv_noticia_bps.median()
        celdas = []
        for a in (0.53, 0.55, 0.57, 0.60):
            n = operaciones_necesarias(a, mov, costo, desv) if len(s) else np.inf
            celdas.append("no gana" if not np.isfinite(n) else num(n, 0))
        L.append(f"| {h} min | {len(s)} | " + " | ".join(celdas) + " |")

    L += ["", "## 5. Por símbolo: horario normal, 15 minutos, tras noticia", "",
          "| Símbolo | Spread | Movimiento tras noticia | Esperado por la hora | Noticias | Acierto mínimo |", "| --- | --- | --- | --- | --- | --- |"]
    s = t[(t.franja == "sesion") & (t.horizonte == 15)].sort_values("acierto_min_noticia")
    for r in s.itertuples():
        L.append(f"| {r.symbol} | {num(r.spread_bps)} bps | {num(r.mov_noticia_bps)} bps | {num(r.mov_esperado_hora_bps)} bps | {num(r.n_noticias, 0)} | {pct(r.acierto_min_noticia)} |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Mide el movimiento del precio frente al costo de operar.")
    ap.add_argument("--desde", type=int, default=2023, help="Primer año de velas y noticias a usar (por defecto 2023)")
    ap.add_argument("--simbolos", nargs="+", default=UNIVERSO, help="Lista de símbolos")
    args = ap.parse_args()

    noticias = noticias_por_simbolo(args.desde)
    filas = []
    for i, simbolo in enumerate(args.simbolos, 1):
        precios, dias = rejilla(simbolo, args.desde)
        filas += analizar(simbolo, precios, dias, noticias[noticias["symbol"] == simbolo])
        print(f"[{i}/{len(args.simbolos)}] {simbolo}: {len(dias)} días")

    t = pd.DataFrame(filas).merge(spreads(), on=["symbol", "franja"], how="left")
    t["acierto_min_cualquiera"] = acierto_minimo(t["spread_bps"], t["mov_cualquiera_bps"])
    t["acierto_min_noticia"] = acierto_minimo(t["spread_bps"], t["mov_noticia_bps"])

    SALIDA.mkdir(exist_ok=True)
    t.round(4).to_csv(SALIDA / "barrera_costos.csv", index=False)
    (SALIDA / "barrera_costos.md").write_text(resumen(t, args.desde), encoding="utf-8")
    print(f"\nListo. Resultados en {SALIDA}")


if __name__ == "__main__":
    main()
