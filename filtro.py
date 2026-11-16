"""
Paso 2.6 · Filtro de operaciones (meta-labeling): un segundo modelo decide si se opera.

El modelo de velas (LightGBM v2) da la dirección. El filtro es un clasificador
que estima la probabilidad de que esa operación gane más de K veces el spread,
y solo se opera cuando esa probabilidad es de las más altas.

Diseño, fijado de antemano (está en el documento del proyecto):
  - Filas: las operaciones candidatas, es decir, acciones operables en los
    momentos de decisión de cada horizonte.
  - Etiqueta: 1 si el retorno en la dirección del modelo de velas supera
    K = 2 veces el spread (lo mismo que no perder con el costo doble).
  - Variables: 12, todas conocidas en el momento de decidir (ver VARIABLES).
  - Para cada año de prueba A:
      1. se entrena el filtro con las predicciones de los años de prueba hasta A-2
         (son fuera de muestra: cada una salió de un modelo que no vio ese año);
      2. con el año A-1 se calibra la probabilidad (regresión isotónica) y se
         elige qué fracción de las candidatas operar, entre cinco valores fijos:
         la de mayor ganancia neta total con costo doble;
      3. se opera el año A con ese umbral.
    Los regímenes y grupos son los de la ventana de A (segmentos.py), que solo
    usan días anteriores a A.
  - Para poder probar 2020 hace falta la predicción del modelo de velas en 2018
    (entrenado con 2016 y 2017). Se calcula aquí una vez y se guarda.

El spread es el de los últimos 60 días de mercado, un número por símbolo: no
hay spread histórico (limitación anotada en el documento).

Muestra final: no se usa nada desde referencia.CORTE.
Cuenta como una variante nueva por horizonte.

Uso:
    python filtro.py

Salida:
    resultados/filtro.md
    datos/modelos/predicciones_2018_<h>.parquet   predicción del modelo de velas en 2018
    datos/modelos/operaciones_filtro_<h>.parquet  una fila por operación, con su probabilidad calibrada
"""

import time

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score

import modelo_velas as mv
import referencia
import segmentos
from calibracion import fila
from descargar_datos import RAIZ, UNIVERSO
from referencia import CORTE, HORIZONTES, RESULTADOS, num

MODELO = "lgbm2"
K = 2.0                                   # la etiqueta exige ganar K veces el spread
FRACCIONES = [0.50, 0.35, 0.25, 0.15, 0.10]   # parte de las candidatas que se opera
MINIMO_OPERACIONES = 1500
ANIO_EXTRA = 2018                         # primer año con predicción del modelo de velas
PRIMER_ANIO_DE_PRUEBA = 2020
VARIANTES_PREVIAS = 8
VARIABLES = ["pred", "pred_abs", "puesto", "pred_costo", "mov_costo", "minuto", "volrel_15", "not_60m",
             "vol_spy", "regimen", "grupo_car", "vol_20d"]
NOMBRES = {"pred": "predicción", "pred_abs": "tamaño de la predicción", "puesto": "puesto entre las acciones del momento",
           "pred_costo": "predicción frente al spread", "mov_costo": "movimiento esperado frente al spread", "minuto": "minuto del día",
           "volrel_15": "volumen relativo", "not_60m": "noticias en la última hora", "vol_spy": "volatilidad de SPY",
           "regimen": "régimen", "grupo_car": "grupo por características", "vol_20d": "volatilidad de 20 días"}
PARAMETROS = dict(objective="binary", n_estimators=200, learning_rate=0.03, num_leaves=7, min_child_samples=500,
                  subsample=0.7, subsample_freq=1, colsample_bytree=0.7, reg_lambda=10.0, n_jobs=4, verbose=-1, random_state=7)


def predicciones_del_anio_extra() -> dict[int, pd.DataFrame]:
    """Predicción del modelo de velas en 2018, entrenado con 2016 y 2017. Se calcula una sola vez."""
    archivos = {h: mv.CARPETA / f"predicciones_{ANIO_EXTRA}_{h}.parquet" for h in HORIZONTES}
    if not all(a.exists() for a in archivos.values()):
        t, base, columnas = mv.cargar()
        t = t[t["dia"].dt.year <= ANIO_EXTRA]
        for h, a in archivos.items():
            pred, _, eleccion = mv.validar(t, base, columnas, h, ANIO_EXTRA)
            pred.to_parquet(a, index=False)
            print(f"   {h} min · {ANIO_EXTRA}: {eleccion[ANIO_EXTRA]}")
    return {h: pd.read_parquet(a) for h, a in archivos.items()}


def variables_extra() -> tuple[pd.DataFrame, pd.Series]:
    """Variables de la tabla general que usa el filtro, y la volatilidad de SPY en cada momento."""
    columnas = ["symbol", "momento", "vol_30", "volrel_15", "not_60m", "vol_20d"]
    archivos = [a for a in sorted((RAIZ / "variables").glob("*.parquet")) if ANIO_EXTRA <= int(a.stem) < CORTE.year]
    v = pd.concat([pd.read_parquet(a, columns=columnas) for a in archivos], ignore_index=True)
    spy = v[v["symbol"] == "SPY"].set_index("momento")["vol_30"]
    return v, spy


def candidatas(pred: pd.DataFrame, v: pd.DataFrame, spy: pd.Series, h: int, costo: pd.Series, operables: set) -> pd.DataFrame:
    """Una fila por operación candidata, con las variables del filtro (menos régimen y grupo) y la etiqueta."""
    pred = pred[["symbol", "momento", "dia", "minuto", "obj_bps", MODELO]].copy()
    pred["puesto"] = pred.groupby("momento")[MODELO].rank(pct=True)
    x = pred[pred["symbol"].isin(operables) & (pred["minuto"] % h == 30 % h) & (pred[MODELO] != 0)]
    x = x.merge(v, on=["symbol", "momento"], how="left")
    c = x["symbol"].map(costo).values
    x["anio"], x["costo_bps"], x["direccion"] = x["dia"].dt.year, c, np.sign(x[MODELO]).astype("int8")
    x["pred"], x["pred_abs"], x["pred_costo"] = x[MODELO], x[MODELO].abs(), x[MODELO].abs() / c
    x["mov_costo"] = x["vol_30"] * np.sqrt(h) * 1e4 / c
    x["vol_spy"] = x["momento"].map(spy).values
    x["bruto_bps"] = x["direccion"] * x["obj_bps"]
    x["y"] = (x["bruto_bps"] > K * c).astype("int8")
    return x.reset_index(drop=True)


def filtrar(x: pd.DataFrame, h: int) -> tuple[pd.DataFrame, dict, pd.Series]:
    """Validación hacia adelante del filtro. Devuelve las operaciones, el detalle por año y la importancia de las variables."""
    partes, detalle, importancia = [], {}, np.zeros(len(VARIABLES))
    for a in range(PRIMER_ANIO_DE_PRUEBA, CORTE.year):
        grupos, regimen = segmentos.de_la_ventana(a)
        w = x[x["anio"] <= a].copy()
        w["regimen"], w["grupo_car"] = w["dia"].map(regimen), w["symbol"].map(grupos["grupo_car"])
        e, c, p = (w["anio"] <= a - 2).values, (w["anio"] == a - 1).values, (w["anio"] == a).values
        modelo = lgb.LGBMClassifier(**PARAMETROS).fit(w.loc[e, VARIABLES], w.loc[e, "y"])
        crudo_c, crudo_p = modelo.predict_proba(w.loc[c, VARIABLES])[:, 1], modelo.predict_proba(w.loc[p, VARIABLES])[:, 1]
        isotonica = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(crudo_c, w.loc[c, "y"])

        # Umbral: la fracción de candidatas que más gana con costo doble en el año A-1.
        doble = (w.loc[c, "bruto_bps"] - 2 * w.loc[c, "costo_bps"]).values
        mejor = (-np.inf, None, None)
        for fraccion in FRACCIONES:
            umbral = np.quantile(crudo_c, 1 - fraccion)
            entra = crudo_c >= umbral
            if entra.sum() >= MINIMO_OPERACIONES and doble[entra].sum() > mejor[0]:
                mejor = (doble[entra].sum(), fraccion, umbral)
        _, fraccion, umbral = mejor

        entra = crudo_p >= umbral
        o = w.loc[p, ["symbol", "dia", "minuto", "direccion", "bruto_bps", "costo_bps"]][entra].rename(columns={"minuto": "entrada"})
        o["salida"], o["prob"], o["modelo"] = o["entrada"] + h, isotonica.predict(crudo_p[entra]), "filtro"
        o["neto_bps"] = o["bruto_bps"] - o["costo_bps"]
        partes.append(o)
        ganancia = modelo.booster_.feature_importance("gain")
        importancia += ganancia / ganancia.sum()
        detalle[a] = dict(entrenamiento=int(e.sum()), positivos=w.loc[p, "y"].mean(), auc=roc_auc_score(w.loc[p, "y"], crudo_p),
                          fraccion=fraccion, candidatas=int(p.sum()))
    return pd.concat(partes, ignore_index=True), detalle, pd.Series(importancia / len(partes), index=VARIABLES)


def seccion(h: int, x: pd.DataFrame, o: pd.DataFrame, detalle: dict, importancia: pd.Series, n_operables: int) -> list[str]:
    a = pd.read_parquet(referencia.CARPETA / f"operaciones_{h}.parquet")
    v2 = pd.read_parquet(mv.CARPETA / f"operaciones_{h}.parquet")
    v2 = v2[v2["modelo"] == MODELO]
    calibrado = pd.read_parquet(mv.CARPETA / f"operaciones_calibradas_{h}.parquet")
    L = [f"## Horizonte de {h} minutos ({n_operables} acciones operables)", ""]
    for desde in (PRIMER_ANIO_DE_PRUEBA, PRIMER_ANIO_DE_PRUEBA + 1):
        dias = pd.DatetimeIndex(np.sort(x.loc[x["anio"] >= desde, "dia"].unique()))
        corte = lambda t: t[t["dia"].isin(dias)]
        neto_a = corte(a).groupby("dia")["neto_bps"].sum()
        L += [f"### De {desde} a {CORTE.year - 1}", "",
              "| Competidor | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t con costo doble | t contra la referencia |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
              fila("A · Referencia", corte(a), None, dias), fila("B · LightGBM v2", corte(v2), neto_a, dias),
              fila("B · LightGBM v2 calibrado", corte(calibrado), neto_a, dias), fila("B · LightGBM v2 con filtro", corte(o), neto_a, dias), ""]
    L += ["### Por año", "",
          "El AUC mide si el filtro distingue las operaciones que ganan de las que no (0,5 = azar), en el año de prueba.", "",
          "| Año | Filas de entrenamiento | Candidatas que cumplen la etiqueta | AUC | Fracción elegida | Operaciones | Ganancia neta | Con costo doble | Calibrado, para comparar |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for anio, d in detalle.items():
        x1, x2 = o[o["dia"].dt.year == anio], calibrado[calibrado["dia"].dt.year == anio]
        L.append(f"| {anio} | {num(d['entrenamiento'], 0)} | {num(100 * d['positivos'])}% | {num(d['auc'], 3)} | {num(100 * d['fraccion'], 0)}% | {num(len(x1), 0)} | "
                 f"{num(x1['neto_bps'].mean(), 2)} | {num((x1['bruto_bps'] - 2 * x1['costo_bps']).mean(), 2)} | {num(x2['neto_bps'].mean(), 2)} ({num(len(x2), 0)}) |")
    trimestre = o.groupby(o["dia"].dt.to_period("Q"))["neto_bps"].sum()
    L += ["", f"Trimestres con ganancia neta positiva: {int((trimestre > 0).sum())} de {len(trimestre)}.", "",
          "Variables que más usa el filtro: " + ", ".join(f"{NOMBRES[c]} ({num(100 * v, 0)}%)" for c, v in importancia.nlargest(6).items()) + ".", "",
          "### Probabilidad calibrada y resultado, para el tamaño de posición", "",
          "Operaciones del filtro en quintos de su probabilidad calibrada. Kelly necesita la probabilidad y cuánto se gana y se pierde.", "",
          "| Quinto | Probabilidad media | Cumplen la etiqueta | Ganancia media cuando gana | Pérdida media cuando pierde | Ganancia neta |", "| --- | --- | --- | --- | --- | --- |"]
    quinto = pd.qcut(o["prob"].rank(method="first"), 5, labels=False)
    for q, g in o.groupby(quinto):
        gana = g["neto_bps"] > 0
        L.append(f"| {int(q) + 1} | {num(100 * g['prob'].mean())}% | {num(100 * (g['bruto_bps'] > K * g['costo_bps']).mean())}% | "
                 f"{num(g.loc[gana, 'neto_bps'].mean(), 1)} | {num(g.loc[~gana, 'neto_bps'].mean(), 1)} | {num(g['neto_bps'].mean(), 2)} |")
    return L + [""]


def main() -> None:
    inicio = time.time()
    costo_bps, universo = referencia.costos_y_universo()
    costo = pd.Series(costo_bps, index=UNIVERSO)
    extra = predicciones_del_anio_extra()
    v, spy = variables_extra()
    L = ["# Filtro de operaciones sobre el modelo de velas (meta-labeling, paso 2.6)", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `filtro.py`. El modelo de velas (LightGBM v2) da la dirección y un clasificador decide si se opera. "
         "Para cada año de prueba, el filtro se entrena con años anteriores y elige su umbral con el año inmediatamente anterior. No incluye la muestra final.", "",
         f"Unidades: bps por operación. Los t agrupan por día. Etiqueta: la operación gana más de {num(K, 0)} veces el spread. "
         f"Fracciones posibles: {', '.join(num(100 * f, 0) + '%' for f in FRACCIONES)} de las candidatas.", "",
         f"Variantes probadas hasta ahora: {VARIANTES_PREVIAS + len(HORIZONTES)} (las {VARIANTES_PREVIAS} anteriores más el filtro en cada horizonte).", ""]
    for h in HORIZONTES:
        pred = pd.concat([extra[h], pd.read_parquet(mv.CARPETA / f"predicciones_{h}.parquet")], ignore_index=True)
        operables = set(np.array(UNIVERSO)[universo[h]]) & set(pred["symbol"].unique())
        x = candidatas(pred, v, spy, h, costo, operables)
        o, detalle, importancia = filtrar(x, h)
        o.to_parquet(mv.CARPETA / f"operaciones_filtro_{h}.parquet", index=False)
        L += seccion(h, x, o, detalle, importancia, len(operables))
        print(f"   {h} min: {len(x):,} candidatas, {len(o):,} operaciones, {time.time() - inicio:.0f} s")
    texto = "\n".join(L)
    (RESULTADOS / "filtro.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
