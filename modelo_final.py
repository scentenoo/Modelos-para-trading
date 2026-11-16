"""
Paso 3.1 · Modelo final de B: entrena y guarda el modelo de velas que se usará en vivo.

Regla, fijada el 16 de noviembre de 2026 antes de entrenar (documento del proyecto,
"Qué falta para calcular las variables en vivo", punto 4):
  - Filas y objetivo de la variante 12 (horizonte_largo.py --retraso 20): momentos de
    10:00 a 12:30 cada 30 minutos; objetivo = retorno desde 20 minutos después del
    momento hasta las 15:55, menos el promedio de las 50 acciones.
  - Datos: todo 2016–2024 (nada de la muestra final).
  - Modelo: LightGBM v2 de modelo_velas, con su búsqueda de hiperparámetros (elige con
    el último año, 2024, y vuelve a entrenar con todos).
  - Pendiente de calibración: una sola, fija, con todas las predicciones fuera de muestra
    de 2019–2024 de la variante 12 (datos/modelos/predicciones_cierre_retraso20.parquet)
    en las 36 acciones operables: suma(pred x real) / suma(pred²), como calibracion.py.
  - Se reentrena cada trimestre con la misma regla.

Uso:
    python modelo_final.py

Salida:
    datos/modelos/final/modelo_b.txt    modelo LightGBM (booster.save_model)
    datos/modelos/final/modelo_b.json   columnas en orden, codificación del sector,
                                        pendiente, acciones operables, momentos, retraso,
                                        hiperparámetros elegidos y fecha de entrenamiento
"""

import json
import time

import lightgbm as lgb
import numpy as np
import pandas as pd

import horizonte_largo as hl
import modelo_velas as mv
import recostear
import referencia
from descargar_datos import UNIVERSO
from referencia import CORTE, SALIDA_MAXIMA

RETRASO = 20
CARPETA = mv.CARPETA / "final"


def entrenar(X: pd.DataFrame, y: np.ndarray, anio: np.ndarray, momento: np.ndarray) -> tuple[lgb.LGBMRegressor, dict]:
    """La misma búsqueda que modelo_velas.predecir_lgbm2, devolviendo el modelo."""
    v = anio == anio.max()
    mejor = (-np.inf, None, None)
    for candidato in mv.CANDIDATOS:
        m = lgb.LGBMRegressor(**{**mv.PARAMETROS, **candidato, "n_estimators": max(mv.ARBOLES)})
        m.fit(X[~v], y[~v], categorical_feature=["sector_n"])
        for n in mv.ARBOLES:
            orden = mv.correlacion_de_rangos(m.predict(X[v], num_iteration=n), y[v], momento[v]).mean()
            if orden > mejor[0]:
                mejor = (orden, candidato, n)
    orden, candidato, n = mejor
    m = lgb.LGBMRegressor(**{**mv.PARAMETROS, **candidato, "n_estimators": n}).fit(X, y, categorical_feature=["sector_n"])
    return m, dict(**candidato, n_estimators=n, orden_validacion=float(orden))


def main() -> None:
    inicio = time.time()
    t, _, columnas = mv.cargar()
    sectores = dict(enumerate(t["sector"].astype("category").cat.categories))     # código -> sector, como en cargar()
    p = referencia.cargar_precios()
    t = t[t["minuto"].isin(hl.MOMENTOS)].reset_index(drop=True)
    t["obj_cierre"] = hl.retorno(t, p, SALIDA_MAXIMA, entrada=t["minuto"].to_numpy() + RETRASO)
    t["rel_cierre"] = hl.relativo(t, t["obj_cierre"].to_numpy())
    t = t[np.isfinite(t["obj_cierre"]) & np.isfinite(t["rel_cierre"]) & (t["dia"] < CORTE)].reset_index(drop=True)
    y = (t["rel_cierre"] * 1e4).to_numpy()
    anio = t["dia"].dt.year.to_numpy()
    print(f"{len(t):,} filas de {anio.min()} a {anio.max()}, {len(columnas)} variables")

    modelo, elegido = entrenar(t[columnas], y, anio, t["momento"].to_numpy())

    _, universo = referencia.costos_y_universo()
    _, muestras, _ = recostear.spreads_por_trimestre(recostear.volatilidad_diaria())
    operables = sorted(set(np.array(UNIVERSO)[universo[hl.HORIZONTE_BASE]]) & set(t["symbol"].unique()) & set(muestras["symbol"].unique()))
    pred = pd.read_parquet(mv.CARPETA / f"predicciones_cierre_retraso{RETRASO}.parquet")
    if (pred["dia"].dt.year == mv.PRIMER_ANIO_DE_PRUEBA).sum() == 0:
        # horizonte_largo.py no guarda el primer año de prueba (no tiene años anteriores para calibrar):
        # se predice igual que allí, entrenando con los años anteriores.
        primero, _ = hl.validar(t, columnas, y, mv.PRIMER_ANIO_DE_PRUEBA, mv.PRIMER_ANIO_DE_PRUEBA)
        pred = pd.concat([primero, pred], ignore_index=True)
    x = pred[pred["symbol"].isin(operables) & (pred["dia"] < CORTE)]
    pendiente = float((x[hl.MODELO] * x["rel_bps"]).sum() / (x[hl.MODELO] ** 2).sum())

    CARPETA.mkdir(parents=True, exist_ok=True)
    modelo.booster_.save_model(str(CARPETA / "modelo_b.txt"))
    meta = dict(entrenado=pd.Timestamp.now().isoformat(timespec="seconds"), datos=f"{anio.min()}-{anio.max()}", filas=len(t),
                columnas=columnas, sector_n=sectores, momentos=hl.MOMENTOS, retraso_min=RETRASO, salida_min=SALIDA_MAXIMA,
                hiperparametros=elegido, pendiente=pendiente,
                pendiente_de=f"predicciones fuera de muestra {int(x['dia'].dt.year.min())}-{int(x['dia'].dt.year.max())}, {len(x):,} filas",
                operables=operables)
    (CARPETA / "modelo_b.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    # Comprobación: el modelo guardado, al leerlo, predice lo mismo que el de memoria.
    leido = lgb.Booster(model_file=str(CARPETA / "modelo_b.txt"))
    muestra = t[columnas].sample(2000, random_state=7)
    dif = np.abs(leido.predict(muestra) - modelo.predict(muestra)).max()
    print(f"Hiperparámetros: {elegido}")
    print(f"Pendiente de calibración: {pendiente:.3f} ({meta['pendiente_de']}); {len(operables)} acciones operables")
    print(f"Modelo guardado en {CARPETA}; diferencia al releerlo: {dif:.2e} bps; {time.time() - inicio:.0f} s")
    assert dif < 1e-9


if __name__ == "__main__":
    main()
