"""
Diagnósticos de la señal del modelo de velas: noticias y horizonte.

Dos preguntas, con las predicciones y operaciones ya guardadas (LightGBM v2 y su
versión calibrada, 2020-2024). No entrena nada y no cuenta como variante.

  1. ¿El modelo elige mejor justo después de una noticia?
     Se separan los momentos de decisión según si la acción tuvo noticias en la
     última hora. Es la pregunta de fondo de la Fase 3: si tras una noticia hay
     más para ganar.

  2. ¿Cuánto dura la señal?
     Para cada predicción se mide qué pasa si la operación se mantiene 15, 30,
     60, 120 o 180 minutos, o hasta el cierre (15:55), en vez del horizonte
     para el que se entrenó. Si la ganancia sigue creciendo y el costo es el
     mismo, un horizonte más largo rinde más por operación.

"Selección" es el retorno de la acción frente al promedio de las 50, en la
dirección que predijo el modelo: lo que se gana por elegir bien, sin el
movimiento del mercado y antes de costos.

Muestra final: las predicciones guardadas no la incluyen.

Uso:
    python diagnosticos.py

Salida:
    resultados/diagnosticos.md
"""

import numpy as np
import pandas as pd

import referencia
from descargar_datos import RAIZ, SECTOR, UNIVERSO
from referencia import HORIZONTES, RESULTADOS, SALIDA_MAXIMA, num

MODELOS = RAIZ / "modelos"
DESDE = 2020
DURACIONES = [15, 30, 60, 120, 180]
CIERRE = "cierre"


def media_t(x: pd.Series, dia: pd.Series) -> str:
    """Media por fila y, entre paréntesis, el t agrupando por día."""
    ok = x.notna()
    x, dia = x[ok], dia[ok]
    if len(x) < 30:
        return "—"
    d = x.groupby(dia).sum()
    return f"{num(x.mean(), 2)} ({num(d.mean() / (d.std(ddof=1) / np.sqrt(len(d))), 2)})"


def candidatas(h: int, operables: set) -> pd.DataFrame:
    """Momentos de decisión de las acciones operables, con la predicción, las noticias y si se operó."""
    pred = pd.read_parquet(MODELOS / f"predicciones_{h}.parquet", columns=["symbol", "momento", "dia", "minuto", "obj_bps", "rel_bps", "lgbm2"])
    x = pred[pred["symbol"].isin(operables) & (pred["minuto"] % h == 30 % h) & (pred["dia"].dt.year >= DESDE) & (pred["lgbm2"] != 0)]
    columnas = ["symbol", "momento", "not_60m", "not_desde_cierre", "vol_30"]
    v = pd.concat([pd.read_parquet(RAIZ / "variables" / f"{a}.parquet", columns=columnas) for a in sorted(x["dia"].dt.year.unique())], ignore_index=True)
    x = x.merge(v, on=["symbol", "momento"], how="left")
    o = pd.read_parquet(MODELOS / f"operaciones_calibradas_{h}.parquet")[["symbol", "dia", "entrada", "costo_bps"]]
    x = x.merge(o.rename(columns={"entrada": "minuto"}), on=["symbol", "dia", "minuto"], how="left")
    x["opera"] = x["costo_bps"].notna()
    x["direccion"] = np.sign(x["lgbm2"])
    x["seleccion"] = x["direccion"] * x["rel_bps"]
    x["esperado"] = (x["vol_30"] * np.sqrt(h) * 1e4).where(x["vol_30"] > 0)   # movimiento típico de la acción en el horizonte
    return x.reset_index(drop=True)


def por_noticias(x: pd.DataFrame, h: int) -> list[str]:
    grupos = [("Sin noticias desde el cierre de ayer", x["not_desde_cierre"] == 0),
              ("Con noticias hoy, ninguna en la última hora", (x["not_desde_cierre"] > 0) & (x["not_60m"] == 0)),
              ("Con noticia en la última hora", x["not_60m"] > 0),
              ("Con 3 o más noticias en la última hora", x["not_60m"] >= 3),
              ("Todos los momentos", pd.Series(True, index=x.index))]
    L = [f"### Horizonte de {h} minutos", "",
         "Selección y ganancia en bps por fila; entre paréntesis, el t. La selección relativa es un porcentaje del movimiento típico de la acción en ese momento, "
         "para no confundir \"elige mejor\" con \"se mueve más\".", "",
         "| Momentos | Filas | Movimiento típico | Selección, todas las filas | Selección relativa | Operadas | Selección, operadas | Ganancia neta, operadas |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for nombre, m in grupos:
        g = x[m]
        op = g[g["opera"]]
        neta = op["direccion"] * op["obj_bps"] - op["costo_bps"]
        L.append(f"| {nombre} | {num(len(g), 0)} ({num(100 * len(g) / len(x), 0)}%) | {num(g['rel_bps'].abs().median(), 1)} | {media_t(g['seleccion'], g['dia'])} | "
                 f"{media_t(100 * g['seleccion'] / g['esperado'], g['dia'])} | {num(len(op), 0)} | {media_t(op['seleccion'], op['dia'])} | {media_t(neta, op['dia'])} |")
    # ¿Es la noticia o es la acción? Las noticias se concentran en pocas acciones.
    con = x["not_60m"] > 0
    por_s = x.groupby("symbol").apply(lambda g: pd.Series({"con": g.loc[g["not_60m"] > 0, "seleccion"].mean(), "sin": g.loc[g["not_60m"] == 0, "seleccion"].mean(),
                                                           "n": (g["not_60m"] > 0).sum()}), include_groups=False)
    por_s = por_s[por_s["n"] >= 200]
    top = x.loc[con, "symbol"].value_counts(normalize=True).head(5)
    L += ["", f"Las noticias se concentran: {', '.join(f'{s} ({num(100 * v, 0)}%)' for s, v in top.items())} suman el {num(100 * top.sum(), 0)}% de los momentos con noticia. "
          f"Dentro de una misma acción, la selección es mayor con noticia que sin ella en {int((por_s['con'] > por_s['sin']).sum())} de {len(por_s)} acciones "
          f"(las que tienen al menos 200 momentos con noticia); la diferencia mediana es {num((por_s['con'] - por_s['sin']).median(), 2)} bps.", ""]
    return L


def retornos_adelante(x: pd.DataFrame, p: dict) -> dict:
    """Selección de cada fila si la operación se mantiene cada duración (o hasta el cierre)."""
    C = p["C"].astype("float64")
    dias = pd.DatetimeIndex(p["dias"])
    s, d, k = pd.Index(UNIVERSO).get_indexer(x["symbol"]), dias.get_indexer(x["dia"]), x["minuto"].values
    acciones = np.array([SECTOR[u] != "etf" for u in UNIVERSO])
    pares = pd.DataFrame({"d": d, "k": k}).drop_duplicates()
    llave = pd.MultiIndex.from_frame(pares)
    fila = llave.get_indexer(pd.MultiIndex.from_arrays([d, k]))
    salida = {}
    for duracion in [*DURACIONES, CIERRE]:
        fin = np.full(len(k), SALIDA_MAXIMA) if duracion == CIERRE else k + duracion
        fin_p = np.full(len(pares), SALIDA_MAXIMA) if duracion == CIERRE else pares["k"].values + duracion
        cabe, cabe_p = fin <= SALIDA_MAXIMA, fin_p <= SALIDA_MAXIMA
        with np.errstate(invalid="ignore", divide="ignore"):
            propio = np.log(C[s, d, np.minimum(fin, SALIDA_MAXIMA)] / C[s, d, k])
            todos = np.log(C[:, pares["d"].values, np.minimum(fin_p, SALIDA_MAXIMA)] / C[:, pares["d"].values, pares["k"].values])[acciones]
        mercado = np.where(cabe_p, np.nanmean(todos, axis=0), np.nan)
        salida[duracion] = pd.Series(np.where(cabe, x["direccion"].values * (propio - mercado[fila]) * 1e4, np.nan), index=x.index)
    return salida


def por_duracion(x: pd.DataFrame, h: int, p: dict) -> list[str]:
    r = retornos_adelante(x, p)
    control = np.corrcoef(r[h].fillna(0), x["seleccion"].fillna(0))[0, 1]
    mismas = x["minuto"] + max(DURACIONES) <= SALIDA_MAXIMA          # entradas en las que caben todas las duraciones
    op = x["opera"]
    L = [f"### Predicciones del modelo de {h} minutos", "",
         f"Selección en bps por operación; entre paréntesis, el t. Las columnas \"mismas entradas\" usan solo las entradas hasta las {int((SALIDA_MAXIMA - max(DURACIONES)) // 60 + 9)}:"
         f"{int((SALIDA_MAXIMA - max(DURACIONES)) % 60 + 30) % 60:02d}, en las que caben todas las duraciones, para comparar sobre las mismas operaciones. "
         f"El costo medio de las operadas es {num(x.loc[op, 'costo_bps'].mean(), 2)} bps y no cambia con la duración. "
         f"(Control: la selección recalculada a {h} minutos coincide con la guardada, correlación {num(control, 3)}.)", "",
         "| Se mantiene | Todas las filas | Todas, mismas entradas | Operadas | Operadas, mismas entradas | Operadas: neta con el mismo costo |", "| --- | --- | --- | --- | --- | --- |"]
    for duracion, sel in r.items():
        nombre = "Hasta el cierre" if duracion == CIERRE else f"{duracion} min"
        L.append(f"| {nombre} | {media_t(sel, x['dia'])} | {media_t(sel[mismas], x['dia'][mismas])} | {media_t(sel[op], x['dia'][op])} | "
                 f"{media_t(sel[op & mismas], x['dia'][op & mismas])} | {media_t((sel - x['costo_bps'])[op & mismas], x['dia'][op & mismas])} |")
    return L + [""]


def main() -> None:
    _, universo = referencia.costos_y_universo()
    p = referencia.cargar_precios()
    tablas = {}
    for h in HORIZONTES:
        operables = {s for s, ok in zip(UNIVERSO, universo[h]) if ok and SECTOR[s] != "etf"}
        tablas[h] = candidatas(h, operables)
    L = ["# Diagnósticos de la señal del modelo de velas", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `diagnosticos.py`, sobre las predicciones de LightGBM v2 y las operaciones de su versión calibrada, {DESDE}–2024. "
         "Es descriptivo: no entrena nada y no cuenta como variante. No incluye la muestra final.", "",
         "Selección: retorno de la acción frente al promedio de las 50, en la dirección que predijo el modelo, antes de costos. "
         "La última columna de cada tabla sí usa el retorno completo o descuenta el costo, según se indica.", "",
         "## 1. ¿El modelo elige mejor después de una noticia?", ""]
    for h in HORIZONTES:
        L += por_noticias(tablas[h], h)
    L += ["## 2. ¿Cuánto dura la señal?", "",
          "La \"neta con el mismo costo\" es la selección menos el spread: supone que la parte de mercado se cubre o se compensa, y no cuenta el costo de esa cobertura.", ""]
    for h in HORIZONTES:
        L += por_duracion(tablas[h], h, p)
    texto = "\n".join(L)
    (RESULTADOS / "diagnosticos.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
