"""
Paso 2.6 · Modelo de velas (competidor B): LightGBM con precio y volumen, sin IA.

Qué predice: el retorno de cada acción en los próximos h minutos, menos el
promedio de las demás acciones en ese momento (rel_h de variables.py).

Cómo se valida (hacia adelante): para cada año de prueba se entrena con todos
los años anteriores y se predice ese año. Así cada predicción sale de un modelo
que nunca vio ese año. El primer año de prueba es 2019 (tres años de entrenamiento).

Cómo opera: en cada momento de decisión se opera una acción solo si la ganancia
que el modelo espera es mayor que el costo (el spread de esa acción). Se compra
si espera que suba frente a las demás y se vende si espera que baje. Las
decisiones se toman cada h minutos, para que las operaciones no se encimen.

Tres modelos:
  - lgbm:  LightGBM con las variables de cada acción y parámetros fijados de antemano.
  - lgbm2: LightGBM con, además, variables comparativas (el puesto de la acción
           frente a las demás en ese momento y su retorno frente al sector) y
           búsqueda de hiperparámetros. La búsqueda va dentro de cada
           entrenamiento: se entrena sin el último año disponible, se elige la
           combinación que mejor ordena ese año y se vuelve a entrenar con todo.
           El año de prueba nunca participa en la elección.
  - logit: regresión logística, la base simple. Predice si la acción sube o baja
           frente a las demás; la ganancia esperada es (2p - 1) por el movimiento típico.

Se entrena con las 50 acciones y se opera solo en las baratas de operar (paso
2.1). Los ETF no entran: el objetivo es relativo a las acciones.

Muestra final: no se usa nada desde referencia.CORTE (criterios, paso 0.4).

Uso:
    python modelo_velas.py
    python modelo_velas.py --prueba-desde 2023     # corrida corta, para probar

Salida:
    resultados/modelo_velas.md                 resumen
    datos/modelos/predicciones_<h>.parquet     predicción de cada fila de prueba
    datos/modelos/operaciones_<h>.parquet      una fila por operación
"""

import argparse
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

import referencia
from descargar_datos import RAIZ, UNIVERSO
from referencia import CORTE, HORIZONTES, RESULTADOS, num, resumen

VARIABLES = RAIZ / "variables"
CARPETA = RAIZ / "modelos"
PRIMER_ANIO_DE_PRUEBA = 2019
MODELOS = {"lgbm": "LightGBM", "lgbm2": "LightGBM v2 (comparativas y búsqueda)", "logit": "Regresión logística (base)"}
# Variables comparativas: puesto (0 a 1) frente a las demás acciones en el mismo momento, y retorno frente al sector.
CON_PUESTO = ["ret_15", "ret_30", "ret_60", "ret_apertura", "ret_noche", "ret_ayer", "ret_5d", "ret_20d", "vol_30", "vol_20d",
              "rango_dia", "volrel_15", "volrel_dia", "dist_vwap", "pos_rango", "not_60m"]
CON_SECTOR = ["ret_30", "ret_60", "ret_apertura", "ret_noche"]
# Búsqueda de hiperparámetros: tres tamaños de árbol por cuatro cantidades de árboles.
CANDIDATOS = [dict(num_leaves=7, min_child_samples=5000), dict(num_leaves=31, min_child_samples=2000),
              dict(num_leaves=127, min_child_samples=500)]
ARBOLES = [100, 200, 300, 500]
NO_SON_VARIABLES = {"symbol", "momento", "dia", "es_etf", "sector",
                    "obj_15", "obj_30", "obj_60", "rel_15", "rel_30", "rel_60"}
PARAMETROS = dict(objective="huber", alpha=30.0, n_estimators=300, learning_rate=0.03, num_leaves=31,
                  min_child_samples=2000, subsample=0.7, subsample_freq=1, colsample_bytree=0.7,
                  reg_lambda=10.0, max_bin=63, n_jobs=4, verbose=-1, random_state=7)


def cargar() -> tuple[pd.DataFrame, list[str], list[str]]:
    """Tabla de variables de las acciones, sin la muestra final ni los medios días."""
    archivos = [a for a in sorted(VARIABLES.glob("*.parquet")) if int(a.stem) < CORTE.year]
    t = pd.concat([pd.read_parquet(a) for a in archivos], ignore_index=True)
    z = np.load(referencia.CARPETA / "cierres.npz")
    medios_dias = pd.DatetimeIndex(z["dias"][z["medio_dia"]])
    t = t[~t["es_etf"] & (t["dia"] < CORTE) & ~t["dia"].isin(medios_dias)].reset_index(drop=True)
    t["sector_n"] = t["sector"].astype("category").cat.codes.astype("int8")
    base = [c for c in t.columns if c not in NO_SON_VARIABLES]
    puestos = t.groupby("momento")[CON_PUESTO].rank(pct=True).astype("float32")
    t[[f"p_{c}" for c in CON_PUESTO]] = puestos.values
    del_sector = t.groupby(["momento", "sector_n"])[CON_SECTOR].transform("mean")
    t[[f"s_{c}" for c in CON_SECTOR]] = (t[CON_SECTOR] - del_sector).values
    return t, base, [c for c in t.columns if c not in NO_SON_VARIABLES]


def correlacion_de_rangos(pred: np.ndarray, real: np.ndarray, momento: np.ndarray) -> pd.Series:
    """Correlación entre el orden predicho y el real, una por momento."""
    x = pd.DataFrame({"pred": pred, "real": real})
    r = x.groupby(momento).rank()
    return r["pred"].groupby(momento).corr(r["real"])


def predecir_lgbm2(X_e: pd.DataFrame, y_e: np.ndarray, anio_e: np.ndarray, momento_e: np.ndarray, X_p: pd.DataFrame) -> tuple:
    """Elige hiperparámetros con el último año de entrenamiento y vuelve a entrenar con todos los años."""
    v = anio_e == anio_e.max()
    mejor = (-np.inf, None, None)
    for candidato in CANDIDATOS:
        modelo = lgb.LGBMRegressor(**{**PARAMETROS, **candidato, "n_estimators": max(ARBOLES)})
        modelo.fit(X_e[~v], y_e[~v], categorical_feature=["sector_n"])
        for n in ARBOLES:
            orden = correlacion_de_rangos(modelo.predict(X_e[v], num_iteration=n), y_e[v], momento_e[v]).mean()
            if orden > mejor[0]:
                mejor = (orden, candidato, n)
    _, candidato, n = mejor
    modelo = lgb.LGBMRegressor(**{**PARAMETROS, **candidato, "n_estimators": n}).fit(X_e, y_e, categorical_feature=["sector_n"])
    eleccion = f"{candidato['num_leaves']} hojas, {n} árboles"
    return modelo.predict(X_p), modelo.booster_.feature_importance("gain"), eleccion


def predecir_lgbm(X_e: pd.DataFrame, y_e: np.ndarray, X_p: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    modelo = lgb.LGBMRegressor(**PARAMETROS).fit(X_e, y_e, categorical_feature=["sector_n"])
    return modelo.predict(X_p), modelo.booster_.feature_importance("gain")


def predecir_logit(X_e: pd.DataFrame, y_e: np.ndarray, X_p: pd.DataFrame) -> np.ndarray:
    """Variables recortadas al 1%–99%, sin huecos y en la misma escala; todo calculado con el entrenamiento."""
    columnas = [c for c in X_e.columns if c != "sector_n"]
    bajo, alto, centro = (X_e[columnas].quantile(q) for q in (0.01, 0.99, 0.5))
    def preparar(X):
        X = X[columnas].clip(bajo, alto, axis=1).fillna(centro)
        return ((X - media) / desviacion).values.astype("float32")
    recortado = X_e[columnas].clip(bajo, alto, axis=1).fillna(centro)
    media, desviacion = recortado.mean(), recortado.std().replace(0, 1)
    modelo = LogisticRegression(C=0.01, max_iter=200).fit(preparar(X_e), y_e > 0)
    p = modelo.predict_proba(preparar(X_p))[:, 1]
    return (2 * p - 1) * np.abs(y_e).mean()


def validar(t: pd.DataFrame, base: list[str], columnas: list[str], h: int, primer_anio: int) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Predicciones hacia adelante, en bps, para cada año de prueba."""
    t = t[np.isfinite(t[f"rel_{h}"]) & np.isfinite(t[f"obj_{h}"])]
    anio = t["dia"].dt.year
    y = (t[f"rel_{h}"] * 1e4).values
    partes, importancia, elecciones = [], np.zeros(len(columnas)), {}
    for a in range(primer_anio, int(anio.max()) + 1):
        e, p = (anio < a).values, (anio == a).values
        inicio = time.time()
        salida = t.loc[p, ["symbol", "momento", "dia", "minuto"]].copy()
        salida["obj_bps"], salida["rel_bps"] = t.loc[p, f"obj_{h}"].values * 1e4, y[p]
        salida["lgbm"], _ = predecir_lgbm(t.loc[e, base], y[e], t.loc[p, base])
        salida["lgbm2"], ganancia, elecciones[a] = predecir_lgbm2(t.loc[e, columnas], y[e], anio[e].values, t.loc[e, "momento"].values, t.loc[p, columnas])
        salida["logit"] = predecir_logit(t.loc[e, base], y[e], t.loc[p, base])
        importancia += ganancia / ganancia.sum()
        partes.append(salida)
        print(f"   {h} min · prueba {a}: {e.sum():,} filas de entrenamiento, {p.sum():,} de prueba, {time.time() - inicio:.0f} s")
    return pd.concat(partes, ignore_index=True), pd.Series(importancia / len(partes), index=columnas), elecciones


def operar(pred: pd.DataFrame, modelo: str, h: int, costo: pd.Series, operable: set) -> pd.DataFrame:
    """Opera cuando la ganancia esperada supera el costo. Decisiones cada h minutos, sin encimar."""
    x = pred[pred["symbol"].isin(operable) & (pred["minuto"] % h == 30 % h)]
    c = x["symbol"].map(costo).values
    entra = np.abs(x[modelo].values) > c
    x, c = x[entra], c[entra]
    direccion = np.sign(x[modelo].values)
    o = pd.DataFrame({"modelo": modelo, "symbol": x["symbol"].values, "dia": x["dia"].values, "entrada": x["minuto"].values,
                      "salida": x["minuto"].values + h, "direccion": direccion.astype("int8"), "esperado_bps": np.abs(x[modelo].values),
                      "bruto_bps": direccion * x["obj_bps"].values, "costo_bps": c})
    o["neto_bps"] = o["bruto_bps"] - o["costo_bps"]
    return o


def orden_acertado(pred: pd.DataFrame, modelo: str) -> tuple[float, float]:
    """Correlación de rangos entre lo predicho y lo ocurrido en cada momento: promedio y estadístico t por día."""
    por_momento = correlacion_de_rangos(pred[modelo].values, pred["rel_bps"].values, pred["momento"].values)
    por_dia = por_momento.groupby(pred.drop_duplicates("momento").set_index("momento")["dia"]).mean().dropna()
    return por_dia.mean(), por_dia.mean() / (por_dia.std(ddof=1) / np.sqrt(len(por_dia)))


def contra(neto_b: pd.Series, neto_a: pd.Series, dias: pd.DatetimeIndex) -> float:
    """Estadístico t de la diferencia de ganancia neta diaria (B menos A), sobre los mismos días."""
    d = neto_b.reindex(dias, fill_value=0.0) - neto_a.reindex(dias, fill_value=0.0)
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def informe(resultados: dict, primer_anio: int) -> str:
    L = ["# Modelo de velas: competidor B (paso 2.6)", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `modelo_velas.py`. Validación hacia adelante: cada año de {primer_anio} a "
         f"{CORTE.year - 1} se predice con un modelo entrenado solo con los años anteriores. No incluye la muestra final.", "",
         "Unidades: bps por operación (1 bps = 0,01%). Costo: un spread completo por operación. Los estadísticos t agrupan por día; "
         "por encima de 2 el resultado se distingue de cero.", "",
         f"Variantes probadas hasta ahora: {len(MODELOS) * len(HORIZONTES)} (tres modelos por dos horizontes). La búsqueda de hiperparámetros de la v2 "
         "no suma variantes porque elige con años anteriores al de prueba.", ""]
    for h, r in resultados.items():
        pred, dias = r["pred"], pd.DatetimeIndex(np.sort(r["pred"]["dia"].unique()))
        a = r["referencia"]
        L += [f"## Horizonte de {h} minutos ({r['n_operables']} acciones operables)", "",
              "### ¿El modelo ordena bien las acciones?", "",
              "Correlación entre el orden predicho y el orden real en cada momento (0 = azar). Mide la señal antes de costos, en las 50 acciones.", "",
              "| Modelo | Correlación de rangos | t |", "| --- | --- | --- |"]
        for m, nombre in MODELOS.items():
            ic, t_ic = orden_acertado(pred, m)
            L.append(f"| {nombre} | {num(ic, 4)} | {num(t_ic, 2)} |")
        L += ["", "### Operando cuando la ganancia esperada supera el costo", "",
              "| Competidor | Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t contra la referencia |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        neto_a = a.groupby("dia")["neto_bps"].sum()
        filas = [("A · Referencia", a, None), *((f"B · {MODELOS[m]}", r["operaciones"][m], m) for m in MODELOS)]
        for nombre, o, m in filas:
            if len(o) == 0:
                L.append(f"| {nombre} | 0 | 0 | — | — | — | — | — | — | — |")
                continue
            s, doble = resumen(o), resumen(o, 2.0)
            t_ref = "—" if m is None else num(contra(o.groupby("dia")["neto_bps"].sum(), neto_a, dias), 2)
            L.append(f"| {nombre} | {num(s['n'], 0)} | {num(s['dias'], 0)} de {len(dias)} | {num(100 * s['acierto'])}% | {num(s['bruto'], 2)} | "
                     f"{num(s['costo'], 2)} | {num(s['neto'], 2)} | {num(s['t'], 2)} | {num(doble['neto'], 2)} | {t_ref} |")
        L += ["", "Ganancia neta por operación, por año (entre paréntesis, operaciones):", "",
              "| Año | LightGBM | LightGBM v2 | v2 con costo doble | Elección de la búsqueda (v2) |", "| --- | --- | --- | --- | --- |"]
        o1, o2 = r["operaciones"]["lgbm"], r["operaciones"]["lgbm2"]
        for anio in sorted(pred["dia"].dt.year.unique()):
            x1, x2 = o1[o1["dia"].dt.year == anio], o2[o2["dia"].dt.year == anio]
            L.append(f"| {anio} | {num(x1['neto_bps'].mean(), 2)} ({num(len(x1), 0)}) | {num(x2['neto_bps'].mean(), 2)} ({num(len(x2), 0)}) | "
                     f"{num((x2['bruto_bps'] - 2 * x2['costo_bps']).mean(), 2)} | {r['elecciones'][anio]} |")
        L += ["", "Si se operara todo sin filtrar por costo, por décimas de la predicción de LightGBM v2 (acciones operables):", "",
              "| Décima de la predicción | Predicción media | Retorno relativo real |", "| --- | --- | --- |"]
        x = pred[pred["symbol"].isin(r["operables"])]
        decima = pd.qcut(x["lgbm2"], 10, labels=False, duplicates="drop")
        for d, g in x.groupby(decima):
            L.append(f"| {int(d) + 1} | {num(g['lgbm2'].mean(), 2)} | {num(g['rel_bps'].mean(), 2)} |")
        L += ["", "Variables que más usa LightGBM v2: " + ", ".join(f"`{c}` ({num(100 * v, 0)}%)" for c, v in r["importancia"].nlargest(8).items()) + ".", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Modelo de velas (competidor B) con validación hacia adelante.")
    ap.add_argument("--prueba-desde", type=int, default=PRIMER_ANIO_DE_PRUEBA, help="Primer año de prueba")
    args = ap.parse_args()

    t, base, columnas = cargar()
    print(f"{len(t):,} filas, {len(base)} variables de la acción y {len(columnas) - len(base)} comparativas")
    costo_bps, universo = referencia.costos_y_universo()
    costo = pd.Series(costo_bps, index=UNIVERSO)
    CARPETA.mkdir(parents=True, exist_ok=True)
    resultados = {}
    for h in HORIZONTES:
        pred, importancia, elecciones = validar(t, base, columnas, h, args.prueba_desde)
        operables = set(np.array(UNIVERSO)[universo[h]]) & set(t["symbol"].unique())
        operaciones = {m: operar(pred, m, h, costo, operables) for m in MODELOS}
        a = pd.read_parquet(referencia.CARPETA / f"operaciones_{h}.parquet")
        a = a[a["dia"].isin(pred["dia"].unique())]
        pred.to_parquet(CARPETA / f"predicciones_{h}.parquet", index=False)
        pd.concat(operaciones.values(), ignore_index=True).to_parquet(CARPETA / f"operaciones_{h}.parquet", index=False)
        resultados[h] = dict(pred=pred, importancia=importancia, elecciones=elecciones, operaciones=operaciones, referencia=a,
                             operables=operables, n_operables=len(operables))
    texto = informe(resultados, args.prueba_desde)
    if args.prueba_desde == PRIMER_ANIO_DE_PRUEBA:
        (RESULTADOS / "modelo_velas.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
