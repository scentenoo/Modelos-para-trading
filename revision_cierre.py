"""
Paso 2.8 · Revisión contra el sobreajuste de la idea 5 (horizonte hasta el cierre).

Trata de romper el resultado de horizonte_largo.py con lo que ya está guardado,
sin reentrenar nada:
  1. Umbral de entrada: se opera si la predicción calibrada supera k veces el
     costo esperado, con k de 0,5 a 2. Un resultado sano cambia poco alrededor
     de k = 1 (meseta); uno sobreajustado solo funciona en k = 1.
  2. Hora de salida: las mismas operaciones, saliendo a las 14:55, 15:25,
     15:40, 15:55 (la del diseño) o 15:59.
  3. Costo: 1, 1,5 y 2 veces el de la época.
  4. Concentración y mercado: ventaja propia frente a SPY, al promedio de las
     50 y a SPY más la referencia, por régimen, sin los mejores días y sin el
     mejor año (con las funciones de ventaja.py y residual-edge-analyzer).
  5. Caída máxima y las cifras que pide la lista de backtest-expert.

Es descriptivo: no cuenta como variante. Ninguna de estas versiones se adopta;
solo dicen qué tan frágil es la del diseño.

Capital: una unidad por acción operable, como en ventaja.py.
Muestra final: no se usa nada desde referencia.CORTE.

Uso:
    python revision_cierre.py

Salida:
    resultados/revision_cierre.md
    datos/ventaja/   serie diaria, configuración e informe del analizador (sufijo "cierre")
"""

import numpy as np
import pandas as pd

import horizonte_largo as hl
import recostear
import referencia
import ventaja
from descargar_datos import RAIZ, UNIVERSO
from referencia import CORTE, RESULTADOS, num

UMBRALES = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
SALIDAS = {324: "14:55", 354: "15:25", 369: "15:40", 384: "15:55 (diseño)", 389: "15:59"}
COSTOS = [1.0, 1.5, 2.0]


def fila(nombre: str, o: pd.DataFrame, dias: pd.DatetimeIndex, veces: float = 1.0) -> str:
    serie = hl.serie_diaria(o, dias, veces)
    neto = o["bruto_bps"] - veces * o["costo_bps"]
    return (f"| {nombre} | {num(len(o), 0)} | {num(o['bruto_bps'].mean(), 2)} | {num(veces * o['costo_bps'].mean(), 2)} | "
            f"{num(neto.mean(), 2)} | {num(hl.t_bloques(serie), 2)} |")


def caida_maxima(r: pd.Series) -> float:
    """Caída máxima de la curva acumulada (retornos diarios simples sobre el capital), en %."""
    curva = (1 + r).cumprod()
    return float(100 * (1 - curva / curva.cummax()).max())


def main() -> None:
    pred = pd.read_parquet(RAIZ / "modelos" / "predicciones_cierre.parquet")
    pred = pred[(pred["dia"].dt.year >= hl.DESDE) & (pred["dia"] < CORTE)]
    o = pd.read_parquet(RAIZ / "modelos" / "operaciones_cierre.parquet")
    p = referencia.cargar_precios()
    dias = pd.DatetimeIndex(p["dias"])
    dias = dias[(dias.year >= hl.DESDE) & (dias < CORTE) & ~p["medio_dia"]]

    rv = recostear.volatilidad_diaria()
    tabla, muestras, e = recostear.spreads_por_trimestre(rv)
    base = lambda x, atras=0: recostear.costo_de(x, tabla, rv, e["beta"], atras)
    _, universo = referencia.costos_y_universo()
    operables = set(np.array(UNIVERSO)[universo[hl.HORIZONTE_BASE]]) & set(pred["symbol"].unique()) & set(muestras["symbol"].unique())

    cab = ["| Versión | Operaciones | Bruta | Costo | Neta | t por bloques |", "| --- | --- | --- | --- | --- | --- |"]
    L = ["# Revisión contra el sobreajuste: horizonte hasta el cierre (paso 2.8)", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `revision_cierre.py` sobre lo guardado por `horizonte_largo.py`, {hl.DESDE}–{CORTE.year - 1}. "
         "Es descriptivo: no reentrena, no cuenta como variante y ninguna versión de aquí se adopta. Unidades: bps por operación; "
         "el t usa el remuestreo por bloques de `comparaciones.py`.", ""]

    # 1. Umbral de entrada
    L += ["## 1. Umbral de entrada", "", "Se opera si la predicción calibrada supera k veces el costo esperado; se paga el costo de la época sin multiplicar.", "", *cab]
    for k in UMBRALES:
        costo_k = lambda x, atras=0, k=k: base(x, atras) * (k if atras == 1 else 1.0)
        L.append(fila(f"k = {num(k, 2)}" + (" (diseño)" if k == 1 else ""), hl.operar(pred, hl.CALIBRADO, operables, costo_k), dias))

    # 2. Hora de salida
    s = pd.Index(UNIVERSO).get_indexer(o["symbol"])
    d = pd.DatetimeIndex(p["dias"]).get_indexer(o["dia"])
    C = p["C"].astype("float64")
    L += ["", "## 2. Hora de salida", "", "Las mismas operaciones del diseño, cambiando solo la hora de salida.", "", *cab]
    for minuto, hora in SALIDAS.items():
        x = o.copy()
        with np.errstate(invalid="ignore", divide="ignore"):
            r = np.log(C[s, d, minuto] / C[s, d, o["entrada"].to_numpy()]) * 1e4
        x["bruto_bps"] = x["direccion"] * r
        x = x[np.isfinite(x["bruto_bps"])]
        L.append(fila(hora, x, dias))

    # 3. Costo
    L += ["", "## 3. Costo", "", *cab]
    for v in COSTOS:
        L.append(fila(f"{num(v, 1)} veces el costo de la época", o, dias, v))

    # 4. Concentración y mercado
    n = int(universo[hl.HORIZONTE_BASE].sum())
    t = ventaja.serie_diaria(o, hl.HORIZONTE_BASE, n)
    j = ventaja.analizar(t, "cierre")
    seccion = ventaja.seccion(hl.HORIZONTE_BASE, o, t, j)
    seccion[0] = f"## 4. Concentración y mercado ({t.index.min():%Y-%m-%d} a {t.index.max():%Y-%m-%d}, {len(t)} días)"
    L += [""] + seccion

    # 5. Cifras para backtest-expert
    r = t["strategy_return"]
    neto = o["neto_bps"]
    gana, pierde = neto[neto > 0], neto[neto <= 0]
    L += ["## 5. Cifras para la lista de backtest-expert", "",
          f"- Operaciones: {num(len(o), 0)} en {num(len(dias), 0)} días ({hl.DESDE}–{CORTE.year - 1}).",
          f"- Acierto neto: {num(100 * (neto > 0).mean())}%. Ganancia media de las que ganan: {num(gana.mean() / 100, 3)}%; pérdida media de las que pierden: {num(-pierde.mean() / 100, 3)}%.",
          f"- Caída máxima de la curva diaria (una unidad de capital por acción operable): {num(caida_maxima(r), 2)}%. Retorno anual medio: {num(100 * 252 * r.mean(), 2)}%.",
          f"- Parámetros elegidos a mano: momentos de decisión, hora de salida, umbral (k = 1) y lista de acciones; los hiperparámetros se eligen dentro de cada año.", ""]
    texto = "\n".join(L)
    (RESULTADOS / "revision_cierre.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
