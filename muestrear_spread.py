"""
Mide el costo de cruzar el mercado: la diferencia entre el precio de compra y
el de venta (spread) de cada acción, con cotizaciones reales de Alpaca.

Bajar todas las cotizaciones sería enorme, así que se toma una muestra: para
cada símbolo se eligen momentos al azar de los últimos 60 días de mercado, en
tres franjas (hora de Nueva York):

    pre      7:00 –  9:30   15 momentos
    sesion   9:30 – 16:00   40 momentos
    post    16:00 – 18:00   15 momentos

En cada momento se piden las cotizaciones del minuto siguiente y se guarda la
mediana del spread en ese minuto.

Uso:
    python muestrear_spread.py
    python muestrear_spread.py --simbolos SPY AAPL
    python muestrear_spread.py --forzar          # repite aunque ya exista
    python muestrear_spread.py --historico       # muestra por trimestre, de 2016 a 2024

Con --historico se mide el spread de años anteriores, solo en horario normal:
8 momentos al azar por símbolo y por trimestre. Sirve para saber cuánto costaba
operar en cada época, porque el spread cambia mucho (en marzo de 2020 fue varias
veces el de hoy). No toma nada de la muestra final (2025 en adelante).

Con --bordes se mide, de 2016 a 2024, el spread en los dos extremos de la idea 5
(horizonte_largo.py): la apertura, 10:00–10:35, donde entra la mayoría de sus
operaciones, y el cierre, 15:45–15:59, donde sale. 4 momentos por franja, símbolo
y trimestre. Se compara con el de horario normal del mismo trimestre.

Estructura de salida:
    datos/spread/SIMBOLO.parquet             (una fila por momento muestreado)
    datos/spread_historico/SIMBOLO.parquet   (lo mismo, con --historico)
    datos/spread_bordes/SIMBOLO.parquet      (lo mismo, con --bordes)

Columnas: momento (UTC), franja, cotizaciones (cuántas hubo en el minuto),
spread_bps (en centésimas de punto porcentual: 1 bps = 0,01%), spread_usd,
precio_medio, tam_compra y tam_venta (acciones ofrecidas en la punta).
Si en el minuto no hubo cotizaciones, las cifras quedan vacías.

La muestra es reproducible: usa una semilla fija por símbolo.
"""

import argparse
import sys
import time
import zlib
from datetime import timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from alpaca.common.exceptions import APIError
from alpaca.data.enums import DataFeed
from alpaca.data.requests import StockQuotesRequest

from descargar_datos import RAIZ, UNIVERSO, cliente

CARPETA = RAIZ / "spread"
NY = ZoneInfo("America/New_York")
FRANJAS = {"pre": (7 * 60, 9 * 60 + 30, 15), "sesion": (9 * 60 + 30, 16 * 60, 40), "post": (16 * 60, 18 * 60, 15)}
DIAS = 60
PAUSA = 0.35  # segundos entre peticiones, para no agotar el límite de Alpaca
CARPETA_HISTORICO = RAIZ / "spread_historico"
ANIOS_HISTORICO = range(2016, 2025)   # hasta 2024: la muestra final no se toca
POR_TRIMESTRE = 8
# --bordes: los dos extremos de la idea 5 (entradas desde las 10:00, salida a las 15:55).
CARPETA_BORDES = RAIZ / "spread_bordes"
FRANJAS_BORDES = {"apertura": (10 * 60, 10 * 60 + 35), "cierre": (15 * 60 + 45, 15 * 60 + 59)}
POR_TRIMESTRE_BORDES = 4


def dias_de_mercado(simbolo: str) -> list:
    """Últimos días con velas del símbolo, sin contar el más reciente (puede estar incompleto)."""
    archivos = sorted((RAIZ / "minuto" / simbolo).glob("*.parquet"))[-2:]
    if not archivos:
        sys.exit(f"No hay velas de {simbolo}: correr primero descargar_datos.py.")
    ts = pd.concat([pd.read_parquet(a, columns=["timestamp"]) for a in archivos])["timestamp"]
    dias = sorted(ts.dt.tz_convert(NY).dt.date.unique())
    return dias[-(DIAS + 1):-1]


def momentos(simbolo: str) -> list[tuple[pd.Timestamp, str]]:
    azar = np.random.default_rng(zlib.crc32(simbolo.encode()))
    dias = dias_de_mercado(simbolo)
    salida = []
    for franja, (desde, hasta, cuantos) in FRANJAS.items():
        for _ in range(cuantos):
            dia = dias[azar.integers(len(dias))]
            minuto = int(azar.integers(desde, hasta - 1))
            local = pd.Timestamp(dia, tz=NY) + timedelta(minutes=minuto, seconds=int(azar.integers(60)))
            salida.append((local.tz_convert("UTC"), franja))
    return salida


def momentos_historicos(simbolo: str) -> list[tuple[pd.Timestamp, str]]:
    """Momentos al azar en horario normal: POR_TRIMESTRE por cada trimestre con velas."""
    azar = np.random.default_rng(zlib.crc32(f"{simbolo}-historico".encode()))
    desde, hasta, _ = FRANJAS["sesion"]
    salida = []
    for anio in ANIOS_HISTORICO:
        archivo = RAIZ / "minuto" / simbolo / f"{anio}.parquet"
        if not archivo.exists():
            continue
        ts = pd.read_parquet(archivo, columns=["timestamp"])["timestamp"]
        dias = pd.DatetimeIndex(sorted(ts.dt.tz_convert(NY).dt.date.unique()))
        for trimestre in range(1, 5):
            del_trimestre = dias[dias.quarter == trimestre]
            for _ in range(POR_TRIMESTRE if len(del_trimestre) else 0):
                dia = del_trimestre[azar.integers(len(del_trimestre))]
                minuto = int(azar.integers(desde, hasta - 1))
                local = pd.Timestamp(dia.date(), tz=NY) + timedelta(minutes=minuto, seconds=int(azar.integers(60)))
                salida.append((local.tz_convert("UTC"), "sesion"))
    return salida


def momentos_bordes(simbolo: str) -> list[tuple[pd.Timestamp, str]]:
    """Momentos al azar en la apertura (10:00–10:35) y el cierre (15:45–15:59): POR_TRIMESTRE_BORDES por franja y trimestre."""
    azar = np.random.default_rng(zlib.crc32(f"{simbolo}-bordes".encode()))
    salida = []
    for anio in ANIOS_HISTORICO:
        archivo = RAIZ / "minuto" / simbolo / f"{anio}.parquet"
        if not archivo.exists():
            continue
        ts = pd.read_parquet(archivo, columns=["timestamp"])["timestamp"]
        dias = pd.DatetimeIndex(sorted(ts.dt.tz_convert(NY).dt.date.unique()))
        for trimestre in range(1, 5):
            del_trimestre = dias[dias.quarter == trimestre]
            if not len(del_trimestre):
                continue
            for franja, (desde, hasta) in FRANJAS_BORDES.items():
                for _ in range(POR_TRIMESTRE_BORDES):
                    dia = del_trimestre[azar.integers(len(del_trimestre))]
                    minuto = int(azar.integers(desde, hasta))
                    local = pd.Timestamp(dia.date(), tz=NY) + timedelta(minutes=minuto, seconds=int(azar.integers(60)))
                    salida.append((local.tz_convert("UTC"), franja))
    return salida


def medir(cli, simbolo: str, momento: pd.Timestamp) -> dict | None:
    """Mediana del spread en el minuto que sigue a `momento`, o None si la petición falló."""
    req = StockQuotesRequest(symbol_or_symbols=simbolo, start=momento.to_pydatetime(),
                             end=(momento + timedelta(minutes=1)).to_pydatetime(), limit=200, feed=DataFeed.SIP)
    for intento in range(5):
        try:
            q = cli.get_stock_quotes(req).df
            break
        except Exception as e:  # noqa: BLE001
            if isinstance(e, APIError) and e.status_code in (400, 401, 403, 422):
                sys.exit(f"Alpaca rechazó la petición ({e.status_code}): {e}")
            time.sleep(15 * (intento + 1))
    else:
        return None
    vacio = dict(cotizaciones=0, spread_bps=np.nan, spread_usd=np.nan, precio_medio=np.nan, tam_compra=np.nan, tam_venta=np.nan)
    if q.empty:
        return vacio
    q = q[(q["bid_price"] > 0) & (q["ask_price"] > q["bid_price"])]  # descarta puntas vacías o cruzadas
    if q.empty:
        return vacio
    medio = (q["bid_price"] + q["ask_price"]) / 2
    spread = q["ask_price"] - q["bid_price"]
    return dict(cotizaciones=len(q), spread_bps=float((1e4 * spread / medio).median()), spread_usd=float(spread.median()),
                precio_medio=float(medio.median()), tam_compra=float(q["bid_size"].median()), tam_venta=float(q["ask_size"].median()))


def main() -> None:
    ap = argparse.ArgumentParser(description="Muestrea el spread de cada símbolo con cotizaciones de Alpaca.")
    ap.add_argument("--simbolos", nargs="+", default=UNIVERSO, help="Lista de símbolos")
    ap.add_argument("--forzar", action="store_true", help="Repite aunque el archivo ya exista")
    ap.add_argument("--historico", action="store_true", help="Muestra por trimestre de 2016 a 2024, en horario normal")
    ap.add_argument("--bordes", action="store_true", help="Muestra por trimestre de 2016 a 2024 en la apertura (10:00–10:35) y el cierre (15:45–15:59)")
    args = ap.parse_args()

    cli = cliente()
    if args.bordes:
        carpeta, elegir = CARPETA_BORDES, momentos_bordes
    else:
        carpeta, elegir = (CARPETA_HISTORICO, momentos_historicos) if args.historico else (CARPETA, momentos)
    carpeta.mkdir(parents=True, exist_ok=True)
    fallos = []
    for i, simbolo in enumerate(args.simbolos, 1):
        archivo = carpeta / f"{simbolo}.parquet"
        if archivo.exists() and not args.forzar:
            continue
        filas, incompleto = [], False
        for momento, franja in elegir(simbolo):
            time.sleep(PAUSA)
            m = medir(cli, simbolo, momento)
            if m is None:
                incompleto = True
                break
            filas.append(dict(symbol=simbolo, momento=momento, franja=franja, **m))
        if incompleto:
            fallos.append(simbolo)
            print(f"[{i}/{len(args.simbolos)}] {simbolo}: falló, se salta")
            continue
        df = pd.DataFrame(filas)
        temporal = archivo.with_suffix(".parquet.tmp")
        df.to_parquet(temporal, index=False)
        temporal.replace(archivo)
        if args.bordes:
            med = df.groupby("franja")["spread_bps"].median()
            print(f"[{i}/{len(args.simbolos)}] {simbolo}: " + " | ".join(f"{f} {med.get(f, np.nan):.1f} bps" for f in FRANJAS_BORDES), flush=True)
        elif args.historico:
            med = df.groupby(df["momento"].dt.year)["spread_bps"].median()
            print(f"[{i}/{len(args.simbolos)}] {simbolo}: " + " | ".join(f"{a} {x:.1f}" for a, x in med.items()) + " bps", flush=True)
        else:
            med = df.groupby("franja")["spread_bps"].median()
            print(f"[{i}/{len(args.simbolos)}] {simbolo}: " + " | ".join(f"{f} {med.get(f, np.nan):.1f} bps" for f in FRANJAS))

    print(f"\nListo. Muestras de spread en {carpeta}")
    if fallos:
        sys.exit(f"Fallaron {len(fallos)} símbolos (volver a correr): {', '.join(fallos)}")


if __name__ == "__main__":
    main()
