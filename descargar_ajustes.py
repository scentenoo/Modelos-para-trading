"""
Descarga los ajustes corporativos (splits, dividendos, escisiones, cambios de
nombre...) desde Alpaca y los guarda en Parquet.

Los precios de datos/minuto están SIN ajustar; con esta tabla se ajustan al
leerlos (ver precios.py).

Uso:
    python descargar_ajustes.py                    # universo por defecto, 2016 a hoy
    python descargar_ajustes.py --simbolos SPY QQQ

Estructura de salida:
    datos/ajustes/TIPO.parquet   (forward_splits, reverse_splits, cash_dividends, spin_offs...)

Es una descarga pequeña: cada corrida reemplaza los archivos completos.

Ojo:
  - Alpaca filtra por fecha de pago, no por fecha ex-dividendo. Por eso se pide
    hasta 6 meses hacia adelante: así entran los dividendos que ya pasaron su
    fecha ex pero todavía no se han pagado.
  - Para cada escisión se guarda el precio de apertura de la empresa nueva en su
    primer día (`apertura_nueva`), que es lo que permite ajustar el precio de la
    empresa original. Si Alpaca no lo tiene, queda vacío y esa escisión no se ajusta.
"""

import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone

import pandas as pd
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.corporate_actions import CorporateActionsClient
from alpaca.data.requests import CorporateActionsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from descargar_datos import RAIZ, UNIVERSO, cargar_env

CARPETA = RAIZ / "ajustes"


def apertura_primer_dia(cli_precios, simbolo: str, dia: pd.Timestamp) -> float | None:
    """Precio de apertura (sin ajustar) de un símbolo en un día, o None si Alpaca no lo tiene."""
    inicio = datetime(dia.year, dia.month, dia.day, tzinfo=timezone.utc)
    req = StockBarsRequest(symbol_or_symbols=simbolo, timeframe=TimeFrame.Day, start=inicio,
                           end=inicio + timedelta(days=1), feed=DataFeed.SIP, adjustment=Adjustment.RAW)
    try:
        df = cli_precios.get_stock_bars(req).df
    except Exception as e:  # noqa: BLE001
        print(f"   sin precio de {simbolo} el {dia.date()}: {e}")
        return None
    return float(df["open"].iloc[0]) if len(df) else None


def main() -> None:
    ap = argparse.ArgumentParser(description="Descarga ajustes corporativos (splits, dividendos, escisiones) desde Alpaca.")
    ap.add_argument("--inicio", default="2016-01-01", help="Fecha inicial AAAA-MM-DD (por defecto 2016-01-01)")
    ap.add_argument("--simbolos", nargs="+", default=UNIVERSO, help="Lista de símbolos")
    args = ap.parse_args()

    cargar_env()
    llave = os.environ.get("APCA_API_KEY_ID")
    secreto = os.environ.get("APCA_API_SECRET_KEY")
    if not llave or not secreto:
        sys.exit("Faltan APCA_API_KEY_ID y APCA_API_SECRET_KEY (ver descargar_datos.py).")
    cli = CorporateActionsClient(llave, secreto)

    # Un símbolo por petición: así un error deja claro cuál falló.
    por_tipo: dict[str, list[dict]] = {}
    for simbolo in args.simbolos:
        req = CorporateActionsRequest(symbols=[simbolo], start=date.fromisoformat(args.inicio),
                                      end=date.today() + timedelta(days=180))
        for tipo, registros in cli.get_corporate_actions(req).data.items():
            por_tipo.setdefault(tipo, []).extend(e.model_dump(mode="json") for e in registros)

    CARPETA.mkdir(parents=True, exist_ok=True)
    for tipo, filas in sorted(por_tipo.items()):
        df = pd.DataFrame(filas).drop_duplicates(subset="id")
        for col in df.columns:
            if col.endswith("_date"):
                df[col] = pd.to_datetime(df[col])
        if tipo == "spin_offs":
            cli_precios = StockHistoricalDataClient(llave, secreto)
            df["apertura_nueva"] = [apertura_primer_dia(cli_precios, f.new_symbol, f.ex_date) for f in df.itertuples()]
        temporal = CARPETA / f"{tipo}.parquet.tmp"
        df.to_parquet(temporal, index=False)
        temporal.replace(CARPETA / f"{tipo}.parquet")
        print(f"   {tipo}: {len(df):,} registros")

    print(f"\nListo. Ajustes guardados en {CARPETA}")


if __name__ == "__main__":
    main()
