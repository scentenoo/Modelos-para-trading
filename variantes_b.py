"""
Paso 2.7 · Variantes 13 y 14 de B: rasgos de régimen y ridge multinivel por grupo.

Las dos parten de B (variante 12 = horizonte_largo.py --retraso 20): las mismas filas
(momentos de 10:00 a 12:30), el mismo objetivo (retorno desde k + 20 minutos hasta las 15:55,
menos el promedio de las acciones), la misma calibración, decisión, costo de la época y
operación (una por acción y día, 36 operables). Validación hacia adelante de 2019 a 2024;
comparación de 2020 a 2024. Todo se reutiliza de horizonte_largo.py. Diseño fijado antes de
programarlas en el documento del proyecto (paso 2.7).

  - Variante 13: LightGBM v2 (modelo_velas.predecir_lgbm2) con las columnas de siempre más
    cuatro rasgos de régimen del día (volatilidad de 20 días de SPY, choque de volatilidad,
    tendencia y dispersión entre acciones), calculados con segmentos.rasgos_del_mercado
    para todos los días de 2016 a 2024. Cada rasgo usa solo días anteriores (shift(1)).
  - Variante 14: ridge multinivel sobre las mismas columnas (sin los rasgos de régimen y sin
    sector_n, como predecir_logit): y = X·b + Σ_g [grupo = g]·X·d_g, con penalización λ en b
    y 10·λ en cada d_g. Se resuelve como un solo ridge con penalización λ: las columnas de
    interacción se multiplican por 1/√10 (d' = √10·d, así 10·λ·|d|² = λ·|d'|²). Grupo =
    grupo_car de datos/segmentos/grupos.parquet para el año de prueba (la misma agrupación
    en entrenamiento y prueba). λ se elige entre LAMBDAS con el último año de entrenamiento
    como validación (correlación de rangos media por momento) y se reentrena con todo. Se
    resuelve con ecuaciones normales acumuladas por bloques (float32 por bloque, float64 en
    la suma), sin formar la matriz completa. La predicción se guarda en la columna "lgbm2"
    para reutilizar calibracion.calibrar y el informe.

Regla de decisión: la conclusión sobre B es "reemplaza a B" si la diferencia de ganancia
neta diaria (variante - B, 2020-2024, días sin operaciones = 0) es positiva y el t por
bloques es >= 1,65; si no, "B queda como está".

Muestra final: no se usa nada desde referencia.CORTE.

Uso:
    python variantes_b.py --variante 13
    python variantes_b.py --variante 14

Salida:
    datos/modelos/predicciones_v13.parquet, operaciones_v13.parquet (y lo mismo con v14)
    datos/modelos/informe_v13.md, informe_v14.md   (parte de cada variante)
    resultados/variantes_b.md                      (informe con las partes que existan)
"""

import argparse
import time

import numpy as np
import pandas as pd

import calibracion
import horizonte_largo as hl
import modelo_velas as mv
import recostear
import referencia
import segmentos
from descargar_datos import UNIVERSO
from referencia import CORTE, RESULTADOS, SALIDA_MAXIMA, num

RETRASO = 20
LAMBDAS = [1e2, 1e3, 1e4, 1e5, 1e6]       # penalización general λ (suma de cuadrados; ~600.000 filas estandarizadas)
FACTOR_GRUPO = 10.0                       # la penalización de cada desviación por grupo es 10 veces la general
BLOQUE_FILAS = 50_000
UMBRAL_T = 1.65
BONFERRONI = "14 (t exigido con Bonferroni 2,69)."
PARTES = {13: "LightGBM v2 con rasgos de régimen", 14: "Ridge multinivel por grupo"}


# ---------------------------------------------------------------- variante 13: rasgos de régimen

def rasgos_de_regimen() -> pd.DataFrame:
    """Los cuatro rasgos de segmentos.py para todos los días 2016-2024; comprueba contra regimenes.parquet."""
    ret, vol_spy = segmentos.cargar_diario()
    rasgos = segmentos.rasgos_del_mercado(ret, vol_spy)
    guardado = pd.read_parquet(segmentos.CARPETA / "regimenes.parquet")
    mio = rasgos.reindex(guardado["dia"])
    dif = np.abs(mio.to_numpy() - guardado[list(segmentos.RASGOS)].to_numpy()).max()
    print(f"Comprobación de los rasgos de régimen: {len(guardado):,} filas de regimenes.parquet ({guardado['dia'].nunique():,} días), "
          f"diferencia máxima {dif:.3e}")
    assert dif < 1e-9, "los rasgos no coinciden con regimenes.parquet"
    assert rasgos.index.max() < CORTE
    return rasgos


# ---------------------------------------------------------------- variante 14: ridge multinivel

def preprocesar(X_e: pd.DataFrame, columnas: list[str]):
    """Recorte 1%-99%, mediana y estandarización con el entrenamiento, como predecir_logit; devuelve una función para aplicarlo."""
    bajo, alto, centro = (X_e[columnas].quantile(q) for q in (0.01, 0.99, 0.5))
    recortado = X_e[columnas].clip(bajo, alto, axis=1).fillna(centro)
    media, desviacion = recortado.mean(), recortado.std().replace(0, 1)
    return lambda X: ((X[columnas].clip(bajo, alto, axis=1).fillna(centro) - media) / desviacion).values.astype("float32")


def diseno(X: np.ndarray, g: np.ndarray, n_grupos: int) -> np.ndarray:
    """[X, X·[g=0]/√10, ..., X·[g=G-1]/√10]: un ridge con penalización λ sobre esto equivale a λ en b y 10·λ en cada d_g."""
    k = X.shape[1]
    Z = np.zeros((len(X), k * (n_grupos + 1)), dtype="float32")
    Z[:, :k] = X
    for i in range(n_grupos):
        Z[g == i, k * (i + 1):k * (i + 2)] = X[g == i] / np.sqrt(FACTOR_GRUPO)
    return Z


def ecuaciones_normales(X: np.ndarray, g: np.ndarray, n_grupos: int, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Z'Z y Z'y acumulados por bloques de filas."""
    d = X.shape[1] * (n_grupos + 1)
    A, b = np.zeros((d, d)), np.zeros(d)
    for i in range(0, len(X), BLOQUE_FILAS):
        Z = diseno(X[i:i + BLOQUE_FILAS], g[i:i + BLOQUE_FILAS], n_grupos).astype("float64")
        A += Z.T @ Z
        b += Z.T @ y[i:i + BLOQUE_FILAS]
    return A, b


def predecir_con(coef: np.ndarray, X: np.ndarray, g: np.ndarray, n_grupos: int) -> np.ndarray:
    return np.concatenate([diseno(X[i:i + BLOQUE_FILAS], g[i:i + BLOQUE_FILAS], n_grupos).astype("float64") @ coef
                           for i in range(0, len(X), BLOQUE_FILAS)])


def predecir_ridge(X_e: pd.DataFrame, y_e: np.ndarray, g_e: np.ndarray, anio_e: np.ndarray, momento_e: np.ndarray,
                   X_p: pd.DataFrame, g_p: np.ndarray, n_grupos: int) -> tuple[np.ndarray, str]:
    """Elige λ con el último año de entrenamiento (correlación de rangos media por momento) y reentrena con todos los años."""
    columnas = [c for c in X_e.columns if c != "sector_n"]
    v = anio_e == anio_e.max()
    prep = preprocesar(X_e[~v], columnas)
    Xa, Xv = prep(X_e[~v]), prep(X_e[v])
    centro = y_e[~v].mean()
    A, b = ecuaciones_normales(Xa, g_e[~v], n_grupos, y_e[~v] - centro)
    ordenes = {}
    for lam in LAMBDAS:
        coef = np.linalg.solve(A + lam * np.eye(len(A)), b)
        ordenes[lam] = mv.correlacion_de_rangos(predecir_con(coef, Xv, g_e[v], n_grupos), y_e[v], momento_e[v]).mean()
    lam = max(ordenes, key=ordenes.get)
    prep = preprocesar(X_e, columnas)
    Xe = prep(X_e)
    centro = y_e.mean()
    A, b = ecuaciones_normales(Xe, g_e, n_grupos, y_e - centro)
    coef = np.linalg.solve(A + lam * np.eye(len(A)), b)
    return predecir_con(coef, prep(X_p), g_p, n_grupos) + centro, f"λ = {lam:g}, {n_grupos} grupos"


def validar_ridge(t: pd.DataFrame, columnas: list[str], y: np.ndarray, primer_anio: int, ultimo_anio: int) -> tuple[pd.DataFrame, dict]:
    anio = t["dia"].dt.year
    grupos = pd.read_parquet(segmentos.CARPETA / "grupos.parquet")
    partes, elecciones = [], {}
    for a in range(primer_anio, ultimo_anio + 1):
        e, p = (anio < a).values, (anio == a).values
        inicio = time.time()
        gr = grupos[grupos["anio_prueba"] == a].set_index("symbol")["grupo_car"]
        etiqueta = t["symbol"].map(gr)
        assert etiqueta.notna().all(), f"acciones sin grupo en la ventana de {a}"
        ids = {k: i for i, k in enumerate(sorted(gr.unique()))}
        g = etiqueta.map(ids).to_numpy()
        salida = t.loc[p, ["symbol", "momento", "dia", "minuto"]].copy()
        salida["obj_bps"], salida["rel_bps"] = t.loc[p, "obj_cierre"].values * 1e4, y[p]
        salida[hl.MODELO], elecciones[a] = predecir_ridge(t.loc[e, columnas], y[e], g[e], anio[e].values, t.loc[e, "momento"].values,
                                                          t.loc[p, columnas], g[p], len(ids))
        partes.append(salida)
        print(f"   ridge · prueba {a}: {e.sum():,} filas de entrenamiento, {p.sum():,} de prueba, {elecciones[a]}, {time.time() - inicio:.0f} s")
    return pd.concat(partes, ignore_index=True), elecciones


# ---------------------------------------------------------------- comparación con B

def contra_b(o: pd.DataFrame, dias: pd.DatetimeIndex) -> list[str]:
    """Diferencia de ganancia neta diaria (variante - B), 2020-2024, y la regla de decisión."""
    b = pd.read_parquet(mv.CARPETA / "operaciones_cierre_retraso20.parquet")
    dif = hl.serie_diaria(o, dias) - hl.serie_diaria(b, dias)
    t = hl.t_bloques(dif)
    reemplaza = t >= UMBRAL_T and dif.mean() > 0
    return ["## Comparación con B (variante 12)", "",
            "Diferencia de ganancia neta diaria (variante menos B, suma por día en bps; B = `operaciones_cierre_retraso20.parquet`; "
            f"mismos {len(dias)} días de {dias.min().year} a {dias.max().year}, los días sin operaciones valen 0). t por bloques con `horizonte_largo.t_bloques`.", "",
            "| Ganancia neta diaria, variante | Ganancia neta diaria, B | Diferencia | t por bloques |", "| --- | --- | --- | --- |",
            f"| {num(hl.serie_diaria(o, dias).mean(), 2)} | {num(hl.serie_diaria(b, dias).mean(), 2)} | {num(dif.mean(), 2)} | {num(t, 2)} |", "",
            f"Regla del documento: \"reemplaza a B\" si t >= {num(UMBRAL_T, 2)} y la diferencia es positiva; si no, \"B queda como está\".", "",
            f"**Conclusión: {'reemplaza a B' if reemplaza else 'B queda como está'}.**", ""]


def escribir_informe() -> None:
    partes = [mv.CARPETA / f"informe_v{v}.md" for v in PARTES if (mv.CARPETA / f"informe_v{v}.md").exists()]
    (RESULTADOS / "variantes_b.md").write_text("\n".join(p.read_text(encoding="utf-8") for p in partes), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Variantes 13 y 14 de B.")
    ap.add_argument("--variante", type=int, choices=sorted(PARTES), required=True)
    args = ap.parse_args()
    v, inicio = args.variante, time.time()

    t, base, columnas = mv.cargar()
    p = referencia.cargar_precios()
    comprobacion = hl.comprobar_obj_60(t, p)
    if v == 13:
        rasgos = rasgos_de_regimen()
        for c in segmentos.RASGOS:
            t[c] = t["dia"].map(rasgos[c]).astype("float32")
        print("Rasgos de régimen sin dato (primeros días de 2016):", int(t[list(segmentos.RASGOS)].isna().any(axis=1).sum()), "filas")
        columnas = columnas + list(segmentos.RASGOS)

    t = t[t["minuto"].isin(hl.MOMENTOS)].reset_index(drop=True)
    t["obj_cierre"] = hl.retorno(t, p, SALIDA_MAXIMA, t["minuto"].to_numpy() + RETRASO)
    t["rel_cierre"] = hl.relativo(t, t["obj_cierre"].to_numpy())
    t = t[np.isfinite(t["obj_cierre"]) & np.isfinite(t["rel_cierre"])].reset_index(drop=True)
    y = (t["rel_cierre"] * 1e4).to_numpy()
    print(f"{len(t):,} filas en {len(hl.MOMENTOS)} momentos, {len(columnas)} variables")
    assert t["dia"].max() < CORTE

    ultimo = CORTE.year - 1
    if v == 13:
        pred, elecciones = hl.validar(t, columnas, y, mv.PRIMER_ANIO_DE_PRUEBA, ultimo)
    else:
        pred, elecciones = validar_ridge(t, columnas, y, mv.PRIMER_ANIO_DE_PRUEBA, ultimo)

    _, universo = referencia.costos_y_universo()
    rv = recostear.volatilidad_diaria()
    tabla, muestras, e = recostear.spreads_por_trimestre(rv)
    costo = lambda o, atras=0: recostear.costo_de(o, tabla, rv, e["beta"], atras)
    operables = set(np.array(UNIVERSO)[universo[hl.HORIZONTE_BASE]]) & set(pred["symbol"].unique()) & set(muestras["symbol"].unique())

    pred[hl.CALIBRADO], pendientes = calibracion.calibrar(pred, operables)
    pred = pred[pred["dia"].dt.year >= min(pendientes)]
    desde = min(pendientes)
    o = hl.operar(pred, hl.CALIBRADO, operables, costo, RETRASO)
    o["modelo"] = f"v{v}"

    mv.CARPETA.mkdir(parents=True, exist_ok=True)
    pred.to_parquet(mv.CARPETA / f"predicciones_v{v}.parquet", index=False)
    o.to_parquet(mv.CARPETA / f"operaciones_v{v}.parquet", index=False)

    dias = pd.DatetimeIndex(p["dias"])
    dias = dias[(dias.year >= desde) & (dias < CORTE) & ~p["medio_dia"]]
    texto = hl.informe(pred, o, dias, pendientes, elecciones, len(operables), comprobacion, desde, False, time.time() - inicio, RETRASO,
                       titulo=f"# Variante {v}: {PARTES[v]} (entrada retrasada {RETRASO} minutos)", probadas=BONFERRONI, script="variantes_b.py")
    texto += "\n" + "\n".join(contra_b(o, dias)) + "\n"
    (mv.CARPETA / f"informe_v{v}.md").write_text(texto, encoding="utf-8")
    escribir_informe()
    print(texto)


if __name__ == "__main__":
    main()
