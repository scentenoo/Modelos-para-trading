"""
Lee las velas de 1 minuto guardadas SIN ajustar y, si se pide, las ajusta por
splits y dividendos con la tabla de datos/ajustes (ver descargar_ajustes.py).

Uso:
    from precios import cargar
    df = cargar("NVDA")                    # ajustado por splits y dividendos
    df = cargar("NVDA", ajuste="splits")   # solo splits
    df = cargar("NVDA", ajuste=None)       # tal como se negoció

El ajuste es hacia atrás: los precios de hoy quedan iguales y los anteriores a
cada split o dividendo se multiplican por un factor, para que no haya saltos falsos.
    Split:      factor = acciones viejas / acciones nuevas   (10 por 1 -> 0,1)
    Dividendo:  factor = 1 - dividendo / cierre del día anterior

Ojo: las escisiones (spin-offs) NO se ajustan, porque el factor depende del
precio de la empresa nueva. Son pocas; dias_con_escision() da las fechas para
excluir o revisar el salto de ese día.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from descargar_datos import RAIZ

CARPETA_VELAS = RAIZ / "minuto"
CARPETA_AJUSTES = RAIZ / "ajustes"
COLUMNAS_PRECIO = ["open", "high", "low", "close", "vwap"]
ZONA = "America/New_York"


def _ajustes(tipo: str) -> pd.DataFrame:
    archivo = CARPETA_AJUSTES / f"{tipo}.parquet"
    return pd.read_parquet(archivo) if archivo.exists() else pd.DataFrame()


def _acumular(dias: np.ndarray, fechas: pd.Series, factores: pd.Series) -> np.ndarray:
    """Para cada día, el producto de los factores de los ajustes posteriores a ese día."""
    total = np.ones(len(dias))
    for fecha, factor in zip(fechas, factores):
        total[: np.searchsorted(dias, np.datetime64(fecha), side="left")] *= factor
    return total


def factores(simbolo: str, cierres: pd.Series) -> pd.DataFrame:
    """
    Factores de ajuste por día. `cierres` es el cierre sin ajustar de la sesión
    regular, indexado por día. Devuelve las columnas `splits` y `dividendos`.
    """
    dias = cierres.index.values
    salida = pd.DataFrame({"splits": 1.0, "dividendos": 1.0}, index=cierres.index)

    partes = [s[s["symbol"] == simbolo] for s in (_ajustes("forward_splits"), _ajustes("reverse_splits")) if not s.empty]
    if partes:
        splits = pd.concat(partes)
        salida["splits"] = _acumular(dias, splits["ex_date"], splits["old_rate"] / splits["new_rate"])

    div = _ajustes("cash_dividends")
    if not div.empty:
        div = div[div["symbol"] == simbolo]
        # Cierre de la última sesión anterior a la fecha ex-dividendo.
        pos = np.searchsorted(dias, div["ex_date"].values.astype(dias.dtype), side="left") - 1
        div = div[pos >= 0]
        cierre_previo = cierres.values[pos[pos >= 0]]
        salida["dividendos"] = _acumular(dias, div["ex_date"], 1 - div["rate"].values / cierre_previo)
    return salida


def cargar(simbolo: str, ajuste: str | None = "total", carpeta: Path = CARPETA_VELAS) -> pd.DataFrame:
    """
    Velas de 1 minuto de un símbolo, ordenadas por hora (UTC).
    ajuste: "total" (splits y dividendos), "splits" o None (sin ajustar).
    Agrega la columna `dia`: fecha de la sesión en hora de Nueva York.
    """
    if ajuste not in ("total", "splits", None):
        raise ValueError(f"ajuste debe ser 'total', 'splits' o None, no {ajuste!r}")
    archivos = sorted((carpeta / simbolo).glob("*.parquet"))
    if not archivos:
        raise FileNotFoundError(f"No hay velas de {simbolo} en {carpeta}")
    df = pd.concat([pd.read_parquet(a) for a in archivos], ignore_index=True)
    df = df.drop_duplicates(subset="timestamp").sort_values("timestamp", ignore_index=True)

    local = df["timestamp"].dt.tz_convert(ZONA)
    df["dia"] = local.dt.tz_localize(None).dt.normalize()
    if ajuste is None:
        return df

    # Cierre de la sesión regular (9:30–16:00 de Nueva York) de cada día.
    minuto = local.dt.hour * 60 + local.dt.minute
    regular = (minuto >= 9 * 60 + 30) & (minuto < 16 * 60)
    cierres = df.loc[regular].groupby("dia")["close"].last()
    cierres = cierres.reindex(np.sort(df["dia"].unique())).ffill().bfill()

    f = factores(simbolo, cierres)
    f_splits = df["dia"].map(f["splits"]).values
    f_precio = f_splits * df["dia"].map(f["dividendos"]).values if ajuste == "total" else f_splits
    df[COLUMNAS_PRECIO] = df[COLUMNAS_PRECIO].mul(f_precio, axis=0)
    df["volume"] = df["volume"] / f_splits
    return df


def dias_con_escision(simbolo: str) -> list[pd.Timestamp]:
    """Fechas en que el símbolo escindió una empresa: el salto de ese día no está ajustado."""
    esc = _ajustes("spin_offs")
    if esc.empty:
        return []
    return sorted(esc.loc[esc["source_symbol"] == simbolo, "ex_date"])
