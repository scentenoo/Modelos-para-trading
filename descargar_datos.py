"""
Descarga velas de 1 minuto (mercado completo, SIP) desde Alpaca y las guarda en Parquet.

Proyecto: IA vs. modelos estadísticos en trading de corto plazo.

Requisitos (una sola vez):
    pip install alpaca-py pandas pyarrow

Llaves de API (cuenta de papel de Alpaca): en un archivo .env junto a este script
    APCA_API_KEY_ID=tu_llave
    APCA_API_SECRET_KEY=tu_secreto
o como variables de entorno en la terminal antes de correr:
    Linux / macOS:
        export APCA_API_KEY_ID="tu_llave"
        export APCA_API_SECRET_KEY="tu_secreto"
    Windows (PowerShell):
        $env:APCA_API_KEY_ID="tu_llave"
        $env:APCA_API_SECRET_KEY="tu_secreto"

Uso:
    python descargar_datos.py                      # universo por defecto, 2016 a hoy
    python descargar_datos.py --inicio 2024-01-01  # solo desde 2024
    python descargar_datos.py --simbolos SPY QQQ   # solo esos símbolos
    python descargar_datos.py --forzar             # re-descarga todo, aunque ya exista
    python descargar_datos.py --ajuste all         # copia ajustada por splits y dividendos

Estructura de salida:
    datos/minuto/SIMBOLO/AAAA.parquet            precios sin ajustar (por defecto)
    datos/minuto_ajustado/SIMBOLO/AAAA.parquet   con --ajuste all
    (un archivo por símbolo y año)

Si se interrumpe, vuelve a correrlo: salta los años ya completos (los que
llegan hasta el último día hábil del año) y re-descarga los incompletos y el
año en curso.

Ojo:
  - Por defecto se guardan los precios SIN ajustar: los que realmente se
    negociaron, que nunca cambian. Los splits y dividendos se bajan aparte con
    descargar_ajustes.py y se aplican al leer (ver precios.py).
  - Con --ajuste all los precios vienen ajustados a la fecha de descarga.
    Después de un split o dividendo, los años ya guardados quedan con el ajuste
    viejo: usar --forzar para dejar toda la serie en la misma base.
  - Un archivo que empieza a mitad de año (por --inicio) no se completa hacia
    atrás solo: usar --forzar con la fecha de inicio nueva.
  - Las velas incluyen pre-mercado y post-mercado (4:00–20:00 hora de Nueva
    York). Las horas están en UTC.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from alpaca.common.exceptions import APIError
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Universo inicial: ETF de referencia + ~50 acciones líquidas de varios sectores
# (la variedad de sectores es lo que le da material a la segmentación).
# Ojo: son empresas que existen hoy -> hay sesgo de supervivencia. Anotarlo.
UNIVERSO = [
    # ETF de referencia
    "SPY", "QQQ", "IWM",
    # Tecnología
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AVGO", "AMD", "ORCL", "CRM", "ADBE", "INTC",
    # Financiero
    "JPM", "BAC", "GS", "MS", "WFC", "V", "MA",
    # Salud
    "JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY",
    # Consumo
    "WMT", "COST", "PG", "KO", "PEP", "MCD", "NKE", "HD", "TSLA",
    # Energía
    "XOM", "CVX", "COP",
    # Industrial
    "CAT", "BA", "GE", "HON", "UPS",
    # Servicios públicos
    "NEE", "DUK", "SO",
    # Comunicaciones
    "DIS", "NFLX", "T", "VZ",
    # Materiales
    "LIN",
]

RAIZ = Path(__file__).resolve().parent / "datos"
CARPETAS = {"raw": RAIZ / "minuto", "all": RAIZ / "minuto_ajustado"}
AJUSTES = {"raw": Adjustment.RAW, "all": Adjustment.ALL}
# El plan gratis no permite los últimos 15 minutos del feed SIP: dejamos margen.
MARGEN_FIN = timedelta(minutes=20)


def cargar_env(ruta: Path = Path(__file__).with_name(".env")) -> None:
    """Lee NOMBRE=valor del archivo .env (si existe) sin pisar lo que ya esté en el entorno."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        nombre, valor = linea.split("=", 1)
        os.environ.setdefault(nombre.strip(), valor.strip().strip("\"'"))


def cliente() -> StockHistoricalDataClient:
    cargar_env()
    llave = os.environ.get("APCA_API_KEY_ID")
    secreto = os.environ.get("APCA_API_SECRET_KEY")
    if not llave or not secreto:
        sys.exit("Faltan APCA_API_KEY_ID y APCA_API_SECRET_KEY (ver instrucciones arriba).")
    return StockHistoricalDataClient(llave, secreto)


def anio_completo(archivo: Path, anio: int) -> bool:
    """Un año pasado está completo si su última vela es del último día hábil del año."""
    try:
        ultima = pd.read_parquet(archivo, columns=["timestamp"])["timestamp"].max()
    except Exception:  # noqa: BLE001  (archivo dañado o ilegible -> se re-descarga)
        return False
    dia = datetime(anio, 12, 31, 18, tzinfo=timezone.utc)  # 18:00 UTC = 1 p. m. en Nueva York
    while dia.weekday() >= 5:  # sábado o domingo
        dia -= timedelta(days=1)
    return ultima >= dia


def descargar_anio(cli, simbolo: str, anio: int, inicio_global: datetime, fin_global: datetime,
                   ajuste: str = "raw") -> pd.DataFrame | None:
    """Devuelve las velas del año, un DataFrame vacío si no hay, o None si la descarga falló."""
    inicio = max(datetime(anio, 1, 1, tzinfo=timezone.utc), inicio_global)
    # El fin es inclusivo en Alpaca: se resta 1 s para no repetir la vela de las 00:00 del 1 de enero.
    fin = min(datetime(anio + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1), fin_global)
    if inicio >= fin:
        return pd.DataFrame()

    req = StockBarsRequest(
        symbol_or_symbols=simbolo,
        timeframe=TimeFrame.Minute,
        start=inicio,
        end=fin,
        feed=DataFeed.SIP,           # mercado completo (histórico gratis)
        adjustment=AJUSTES[ajuste],  # raw: sin ajustar; all: ajustado por splits y dividendos
    )
    # La librería pagina sola; reintentamos ante errores de red o límite de llamadas.
    for intento in range(5):
        try:
            df = cli.get_stock_bars(req).df
            break
        except Exception as e:  # noqa: BLE001
            # Llaves malas, plan sin permiso o petición inválida: reintentar no sirve.
            if isinstance(e, APIError) and e.status_code in (400, 401, 403, 422):
                sys.exit(f"Alpaca rechazó la petición ({e.status_code}): {e}")
            espera = 15 * (intento + 1)
            print(f"   error ({e}); reintento en {espera}s")
            time.sleep(espera)
    else:
        print(f"   {simbolo} {anio}: falló tras 5 intentos, se salta")
        return None

    if df.empty:
        return df
    df = df.reset_index()  # columnas: symbol, timestamp, open, high, low, close, volume, trade_count, vwap
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description="Descarga velas de 1 minuto desde Alpaca.")
    ap.add_argument("--inicio", default="2016-01-01", help="Fecha inicial AAAA-MM-DD (por defecto 2016-01-01)")
    ap.add_argument("--simbolos", nargs="+", default=UNIVERSO, help="Lista de símbolos")
    ap.add_argument("--forzar", action="store_true", help="Re-descarga aunque el archivo ya exista")
    ap.add_argument("--ajuste", choices=list(AJUSTES), default="raw",
                    help="raw: precios sin ajustar (por defecto); all: ajustados por splits y dividendos")
    args = ap.parse_args()

    inicio_global = datetime.fromisoformat(args.inicio).replace(tzinfo=timezone.utc)
    fin_global = datetime.now(timezone.utc) - MARGEN_FIN
    anio_actual = fin_global.year
    cli = cliente()

    total_filas = 0
    fallos = []
    for i, simbolo in enumerate(args.simbolos, 1):
        carpeta = CARPETAS[args.ajuste] / simbolo
        carpeta.mkdir(parents=True, exist_ok=True)
        print(f"[{i}/{len(args.simbolos)}] {simbolo}")
        for anio in range(inicio_global.year, anio_actual + 1):
            archivo = carpeta / f"{anio}.parquet"
            if not args.forzar and anio < anio_actual and archivo.exists() and anio_completo(archivo, anio):
                continue  # año completo ya descargado
            df = descargar_anio(cli, simbolo, anio, inicio_global, fin_global, args.ajuste)
            if df is None:
                fallos.append(f"{simbolo} {anio}")
                continue
            if df.empty:
                print(f"   {anio}: sin datos")
                continue
            # Se escribe a un temporal y se renombra: un corte a mitad no deja un archivo dañado.
            temporal = archivo.with_suffix(".parquet.tmp")
            df.to_parquet(temporal, index=False)
            temporal.replace(archivo)
            total_filas += len(df)
            print(f"   {anio}: {len(df):,} velas")

    print(f"\nListo. {total_filas:,} velas guardadas en {CARPETAS[args.ajuste]}")
    if fallos:
        sys.exit(f"Fallaron {len(fallos)} descargas (volver a correr): {', '.join(fallos)}")


if __name__ == "__main__":
    main()
