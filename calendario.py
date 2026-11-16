"""
Paso 3.1 · Calendario de sesiones: qué días abre el mercado y a qué hora cierra.

En lo histórico, los medios días (cierre a la 1:00 p. m.) se detectan por el volumen
de la tarde (referencia.py). En vivo eso no se sabe a las 10:00, así que se usa el
calendario oficial que entrega Alpaca, con la hora de apertura y cierre de cada día.

Comprobación: los medios días del calendario deben coincidir con los que referencia.py
detecta por volumen en los días que tienen velas. Si el calendario dice día completo y
a las velas les falta la tarde, es un hueco de datos (2019-08-12), no un error.

Uso:
    python calendario.py

Salida:
    datos/calendario.parquet   (dia, apertura y cierre en hora de Nueva York, medio_dia)
"""

import sys
from datetime import date

import numpy as np
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetCalendarRequest

import referencia
from descargar_datos import RAIZ, cargar_env

ARCHIVO = RAIZ / "calendario.parquet"
DESDE, HASTA = date(2016, 1, 1), date(2027, 12, 31)


def descargar() -> pd.DataFrame:
    import os
    cargar_env()
    cli = TradingClient(os.environ["APCA_API_KEY_ID"], os.environ["APCA_API_SECRET_KEY"], paper=True)
    filas = cli.get_calendar(GetCalendarRequest(start=DESDE, end=HASTA))
    c = pd.DataFrame([{"dia": pd.Timestamp(f.date), "apertura": pd.Timestamp(f.open), "cierre": pd.Timestamp(f.close)} for f in filas])
    c["medio_dia"] = c["cierre"].dt.hour * 60 + c["cierre"].dt.minute < 16 * 60
    return c


def main() -> None:
    c = descargar()
    p = referencia.cargar_precios()
    velas = pd.Series(p["medio_dia"], index=pd.DatetimeIndex(p["dias"]))
    comun = velas.index.intersection(c["dia"])
    cal = c.set_index("dia").loc[comun, "medio_dia"]
    # Calendario normal y volumen de "medio día": a los datos les falta la tarde (por ejemplo, 2019-08-12 termina a
    # las 15:31). No es un error del calendario, y está bien que lo histórico excluya ese día. Lo contrario sí lo sería.
    huecos = comun[~cal.values & velas.loc[comun].values]
    distintos = comun[cal.values & ~velas.loc[comun].values]
    sin_calendario = velas.index.difference(c["dia"])
    c.to_parquet(ARCHIVO, index=False)
    print(f"{len(c):,} sesiones de {c['dia'].min():%Y-%m-%d} a {c['dia'].max():%Y-%m-%d}; medios días: {int(c['medio_dia'].sum())}")
    print(f"Días con velas: {len(velas):,}; en el calendario: {len(comun):,}; con velas pero sin sesión en el calendario: {len(sin_calendario)}")
    print(f"Medio día en el calendario y día completo en las velas (error): {len(distintos)}" + (f" ({', '.join(f'{d:%Y-%m-%d}' for d in distintos[:10])})" if len(distintos) else ""))
    print(f"Día completo en el calendario y sin la tarde en las velas (hueco de datos): {len(huecos)}" + (f" ({', '.join(f'{d:%Y-%m-%d}' for d in huecos[:10])})" if len(huecos) else ""))
    proximos = c[(c["dia"] >= pd.Timestamp.now().normalize()) & c["medio_dia"]].head(4)
    print("Próximos medios días: " + ", ".join(f"{d:%Y-%m-%d} (cierra {h:%H:%M})" for d, h in zip(proximos["dia"], proximos["cierre"])))
    print(f"Guardado en {ARCHIVO}")
    if len(distintos) or len(sin_calendario):
        sys.exit(1)


if __name__ == "__main__":
    main()
