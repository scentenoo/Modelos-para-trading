"""
Paso 2.5 · Referencia (competidor A): cuatro efectos documentados, sin modelo ni IA.

Es el piso de la comparación: si el modelo de velas no le gana a esto en
ganancia neta, no hay ventaja que valga la pena.

Los cuatro efectos (reglas fijas, sin parámetros ajustados con los datos):
  1. Impulso intradía: si la acción subió entre el cierre de ayer y las 10:00,
     se compra a las 15:30; si bajó, se vende. Se cierra a las 15:55.
  2. Reversión de corto plazo: cada h minutos se ordenan las acciones por su
     retorno de los últimos h minutos frente al promedio; se compra la quinta
     parte que más cayó y se vende la que más subió. Se cierra h minutos después.
  3. Deriva tras resultados: en la primera sesión después de un comunicado de
     resultados (8-K, tema 2.02) publicado fuera del horario normal, a las 10:00
     se opera en la dirección de la reacción (retorno desde el cierre anterior
     menos el de SPY). Se cierra h minutos después.
  4. Ruptura del rango de apertura: la primera vez que un cierre de 1 minuto
     supera el máximo de los primeros 15 minutos se compra; si rompe el mínimo,
     se vende. Una operación por acción y por día; se cierra h minutos después.

Convenciones, iguales a las de variables.py:
  - En el minuto k se conocen las velas 0 .. k-1. Se entra al cierre de la vela
    k y se sale al cierre de la vela k+h.
  - Todo se cierra a más tardar a las 15:55. Se excluyen los medios días.
  - Costo: un spread completo por operación (medio al entrar, medio al salir),
    con el spread de cada acción medido en el paso 2.1.
  - Solo se operan las acciones baratas de operar en ese horizonte (paso 2.1).

Muestra final: por defecto se usan solo los días anteriores a CORTE. Lo que
viene después no se toca hasta el cierre del experimento (criterios, paso 0.4).

Uso:
    python referencia.py              # 2016 a 2024
    python referencia.py --rehacer    # vuelve a leer las velas (tras actualizar datos)

Salida:
    resultados/referencia.md                  resumen
    datos/referencia/operaciones_<h>.parquet  una fila por operación
"""

import argparse
import warnings

import numpy as np
import pandas as pd

import variables
from barrera_costos import acierto_minimo
from descargar_datos import RAIZ, SECTOR, UNIVERSO

CORTE = pd.Timestamp("2025-01-01")     # desde aquí es la muestra final: no se mira
HORIZONTES = [30, 60]
SALIDA_MAXIMA = 384                    # cierre de la vela de las 15:54 = 15:55
RANGO_APERTURA = 15
ACIERTO_MAXIMO = 0.55                  # "barata de operar", según el paso 2.1
CARPETA = RAIZ / "referencia"
RESULTADOS = RAIZ.parent / "resultados"
ZONA = "America/New_York"
EFECTOS = {"impulso": "Impulso intradía", "reversion": "Reversión de corto plazo",
           "deriva": "Deriva tras resultados", "ruptura": "Ruptura del rango de apertura"}


# ---------------------------------------------------------------- precios

def cargar_precios(rehacer: bool = False) -> dict:
    """Cierres de cada minuto, alineados a los días de SPY: C[símbolo, día, minuto]."""
    archivo = CARPETA / "cierres.npz"
    if archivo.exists() and not rehacer:
        z = np.load(archivo, allow_pickle=False)
        return {k: z[k] for k in z.files}

    spy = variables.matrices("SPY")
    dias = spy["dias"]
    n = len(dias)
    C = np.full((len(UNIVERSO), n, variables.MINUTOS), np.nan, dtype="float32")
    alto, bajo = np.full((len(UNIVERSO), n), np.nan), np.full((len(UNIVERSO), n), np.nan)
    for i, s in enumerate(UNIVERSO):
        m = spy if s == "SPY" else variables.matrices(s)
        pos = dias.get_indexer(m["dias"])
        ok = pos >= 0
        C[i, pos[ok]] = m["C"][ok]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")    # días sin velas en los primeros minutos
            alto[i, pos[ok]] = np.nanmax(m["H"][ok, :RANGO_APERTURA], axis=1)
            bajo[i, pos[ok]] = np.nanmin(m["L"][ok, :RANGO_APERTURA], axis=1)
        print(f"[{i + 1}/{len(UNIVERSO)}] {s}")

    # Medio día: el mercado cierra a la 1:00 p. m. y casi no hay volumen al final.
    V = spy["V"]
    medio_dia = V[:, 360:].sum(axis=1) < 0.2 * V[:, 180:210].sum(axis=1)
    datos = dict(dias=dias.values.astype("datetime64[D]"), C=C, alto=alto, bajo=bajo, medio_dia=medio_dia)
    CARPETA.mkdir(parents=True, exist_ok=True)
    np.savez(archivo, **datos)
    return datos


def costos_y_universo() -> tuple[np.ndarray, dict[int, np.ndarray]]:
    """Spread de cada símbolo en horario normal y, por horizonte, cuáles son baratos de operar."""
    t = pd.read_csv(RESULTADOS / "barrera_costos.csv")
    t = t[t["franja"] == "sesion"].set_index("symbol")
    costo = t[t["horizonte"] == 30]["spread_bps"].reindex(UNIVERSO).values
    universo = {}
    for h in HORIZONTES:
        x = t[t["horizonte"] == h].reindex(UNIVERSO)
        universo[h] = (acierto_minimo(x["spread_bps"], x["mov_noticia_bps"]) <= ACIERTO_MAXIMO).values
    return costo, universo


# ---------------------------------------------------------------- efectos
# Cada efecto devuelve (símbolo, día, minuto de entrada, minuto de salida, dirección).

def impulso(p: dict, h: int) -> tuple:
    C = p["C"]
    ayer = np.roll(C[:, :, -1], 1, axis=1); ayer[:, 0] = np.nan
    primera_media_hora = np.log(C[:, :, 29] / ayer)          # cierre de ayer a las 10:00
    s, d = np.nonzero(np.isfinite(primera_media_hora) & (primera_media_hora != 0))
    return s, d, np.full(len(s), 360), np.full(len(s), SALIDA_MAXIMA), np.sign(primera_media_hora[s, d])


def reversion(p: dict, h: int, acciones: np.ndarray) -> tuple:
    C = p["C"]
    partes = []
    for k in range(h + 15, SALIDA_MAXIMA - h + 1, h):
        pasado = np.log(C[:, :, k - 1] / C[:, :, k - 1 - h])
        pasado[~acciones] = np.nan                             # solo acciones operables, sin ETF
        n = np.isfinite(pasado).sum(axis=0)
        por_lado = np.maximum(1, np.round(0.2 * n)).astype(int)
        orden = np.argsort(np.argsort(np.where(np.isfinite(pasado), pasado, np.inf), axis=0), axis=0)
        compra = (orden < por_lado) & np.isfinite(pasado)
        venta = (orden >= n - por_lado) & (orden < n) & np.isfinite(pasado)
        venta &= ~compra
        for mascara, direccion in ((compra, 1.0), (venta, -1.0)):
            s, d = np.nonzero(mascara & (n >= 10))
            partes.append((s, d, np.full(len(s), k), np.full(len(s), k + h), np.full(len(s), direccion)))
    return tuple(np.concatenate(x) for x in zip(*partes))


def deriva(p: dict, h: int) -> tuple:
    C, dias = p["C"], pd.DatetimeIndex(p["dias"])
    indice = pd.read_parquet(RAIZ / "sec" / "comunicados_indice.parquet", columns=["symbol", "aceptado", "temas"])
    e = indice[indice["temas"].str.split(",").apply(lambda x: "2.02" in x) & indice["symbol"].isin(UNIVERSO)]
    local = e["aceptado"].dt.tz_convert(ZONA)
    minuto = local.dt.hour * 60 + local.dt.minute
    dia_local = local.dt.tz_localize(None).dt.normalize()
    en_sesion = (minuto >= 570) & (minuto < 960) & dia_local.isin(dias)
    e, minuto, dia_local = e[~en_sesion], minuto[~en_sesion], dia_local[~en_sesion]
    # Primera sesión que abre después del comunicado.
    d = np.searchsorted(dias.values, (dia_local + pd.to_timedelta((minuto >= 570).astype(int), unit="D")).values, side="left")
    s = pd.Index(UNIVERSO).get_indexer(e["symbol"])
    par = pd.DataFrame({"s": s, "d": d}).drop_duplicates()
    par = par[par["d"] < len(dias)]
    s, d = par["s"].values, par["d"].values

    ayer = np.roll(C[:, :, -1], 1, axis=1); ayer[:, 0] = np.nan
    reaccion = np.log(C[:, :, 29] / ayer)
    anormal = reaccion[s, d] - reaccion[UNIVERSO.index("SPY"), d]
    ok = np.isfinite(anormal) & (anormal != 0)
    s, d = s[ok], d[ok]
    return s, d, np.full(len(s), 30), np.full(len(s), 30 + h), np.sign(anormal[ok])


def ruptura(p: dict, h: int) -> tuple:
    C = p["C"]
    ultimo = SALIDA_MAXIMA - h                                # última entrada posible
    visto = C[:, :, RANGO_APERTURA - 1:ultimo]                # cierre conocido en k = 15 .. ultimo
    with np.errstate(invalid="ignore"):
        rompe = np.where(visto > p["alto"][:, :, None], 1.0, np.where(visto < p["bajo"][:, :, None], -1.0, 0.0))
    primero = np.argmax(rompe != 0, axis=2)
    s, d = np.nonzero((rompe != 0).any(axis=2))
    k = primero[s, d] + RANGO_APERTURA
    return s, d, k, k + h, rompe[s, d, primero[s, d]]


# ---------------------------------------------------------------- operaciones y resumen

def operaciones(p: dict, h: int, costo: np.ndarray, operable: np.ndarray, hasta: pd.Timestamp | None) -> pd.DataFrame:
    C, dias = p["C"], pd.DatetimeIndex(p["dias"])
    acciones = operable & np.array([SECTOR[s] != "etf" for s in UNIVERSO])
    senales = {"impulso": impulso(p, h), "reversion": reversion(p, h, acciones), "deriva": deriva(p, h), "ruptura": ruptura(p, h)}
    partes = []
    for efecto, (s, d, entra, sale, direccion) in senales.items():
        bruto = direccion * np.log(C[s, d, sale] / C[s, d, entra]) * 1e4
        t = pd.DataFrame({"efecto": efecto, "symbol": np.array(UNIVERSO)[s], "dia": dias[d], "entrada": entra, "salida": sale,
                          "direccion": direccion.astype("int8"), "bruto_bps": bruto, "costo_bps": costo[s]})
        valida = np.isfinite(bruto) & operable[s] & ~p["medio_dia"][d]
        partes.append(t[valida])
    t = pd.concat(partes, ignore_index=True)
    if hasta is not None:
        t = t[t["dia"] < hasta]
    t["neto_bps"] = t["bruto_bps"] - t["costo_bps"]
    return t.sort_values(["dia", "entrada", "symbol"], ignore_index=True)


def resumen(t: pd.DataFrame, costos: float = 1.0) -> dict:
    """Ganancia por operación. La prueba t agrupa por día: las operaciones de un mismo día no son independientes."""
    neto = t["bruto_bps"] - costos * t["costo_bps"]
    por_dia = neto.groupby(t["dia"]).sum()
    estadistico = por_dia.mean() / (por_dia.std(ddof=1) / np.sqrt(len(por_dia))) if len(por_dia) > 1 else np.nan
    return dict(n=len(t), dias=len(por_dia), acierto=(t["bruto_bps"] > 0).mean(), bruto=t["bruto_bps"].mean(),
                costo=costos * t["costo_bps"].mean(), neto=neto.mean(), t=estadistico)


def num(x: float, d: int = 1) -> str:
    return "—" if not np.isfinite(x) else f"{x:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def informe(tablas: dict[int, pd.DataFrame], universo: dict, periodo: str) -> str:
    L = ["# Referencia: competidor A (paso 2.5)", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `referencia.py`. Periodo: {periodo}. "
         "Reglas fijas, sin parámetros ajustados con los datos.", "",
         "Unidades: bps por operación (1 bps = 0,01%). Costo: un spread completo por operación. "
         "El estadístico t agrupa las operaciones por día; por encima de 2 la ganancia se distingue de cero.", ""]
    for h, t in tablas.items():
        L += [f"## Horizonte de {h} minutos ({int(universo[h].sum())} símbolos)", "",
              "| Efecto | Operaciones | Días | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for nombre, x in [*((EFECTOS[e], t[t["efecto"] == e]) for e in EFECTOS), ("**A · los cuatro**", t)]:
            r, doble = resumen(x), resumen(x, 2.0)
            L.append(f"| {nombre} | {num(r['n'], 0)} | {num(r['dias'], 0)} | {num(100 * r['acierto'])}% | {num(r['bruto'], 2)} | "
                     f"{num(r['costo'], 2)} | {num(r['neto'], 2)} | {num(r['t'], 2)} | {num(doble['neto'], 2)} |")
        L += ["", "Ganancia neta por operación, por año:", "",
              "| Año | " + " | ".join(EFECTOS.values()) + " | A · los cuatro |", "| --- |" + " --- |" * (len(EFECTOS) + 1)]
        anio = t["dia"].dt.year
        for a in sorted(anio.unique()):
            x = t[anio == a]
            L.append(f"| {a} | " + " | ".join(num(x.loc[x["efecto"] == e, "neto_bps"].mean(), 2) for e in EFECTOS) + f" | {num(x['neto_bps'].mean(), 2)} |")
        L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Referencia (competidor A): cuatro efectos documentados.")
    ap.add_argument("--rehacer", action="store_true", help="Vuelve a leer las velas en vez de usar la copia guardada")
    ap.add_argument("--muestra-final", action="store_true", help="Incluye la muestra final. Solo al cierre del experimento")
    args = ap.parse_args()

    p = cargar_precios(args.rehacer)
    costo, universo = costos_y_universo()
    hasta = None if args.muestra_final else CORTE
    tablas = {h: operaciones(p, h, costo, universo[h], hasta) for h in HORIZONTES}

    CARPETA.mkdir(parents=True, exist_ok=True)
    for h, t in tablas.items():
        t.to_parquet(CARPETA / f"operaciones_{h}.parquet", index=False)
    t = tablas[HORIZONTES[0]]
    periodo = f"{t['dia'].min():%Y-%m-%d} a {t['dia'].max():%Y-%m-%d}" + ("" if args.muestra_final else " (sin la muestra final)")
    texto = informe(tablas, universo, periodo)
    nombre = "referencia_muestra_final.md" if args.muestra_final else "referencia.md"
    (RESULTADOS / nombre).write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
