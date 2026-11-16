"""
Idea 5 · Horizonte hasta el cierre: el modelo de velas apuntando a la salida de las 15:55.

Qué predice: el retorno de cada acción desde su momento de entrada hasta las 15:55
(minuto 384, referencia.SALIDA_MAXIMA), menos el promedio de las 50 acciones en ese
momento (igual que rel_h de variables.py). Se calcula aquí a partir de los precios
(referencia.cargar_precios); no se toca la tabla de variables.

Regla, fijada de antemano (documento del proyecto, "Diseño de la idea 5"):
  - Filas: las de modelo_velas.cargar() (acciones, sin medios días ni muestra final),
    solo los momentos de 10:00 a 12:30 cada 30 minutos (minutos 30, 60, ..., 180).
    Se entrena y se predice con esas mismas filas.
  - Modelo: LightGBM v2 de modelo_velas (mismas variables y búsqueda de hiperparámetros),
    con validación hacia adelante: cada año de 2019 a 2024 se predice con un modelo
    entrenado con los años anteriores.
  - Calibración: la de calibracion.calibrar (pendiente con años de prueba anteriores),
    en las acciones operables. La comparación va de 2020 a 2024.
  - Acciones operables: las del horizonte de 60 minutos (paso 2.1).
  - Costo: el de cada época (recostear.py). Decide con el spread del trimestre anterior
    y la volatilidad del día anterior; paga el del trimestre en curso.
  - Operar: si |predicción calibrada| > costo esperado, en la dirección del signo.
    Sin encimar: cada acción, como máximo una operación al día, la del primer momento
    que pasa el filtro. Sale a las 15:55. Sin cobertura.
  - t por bloques: sobre la ganancia neta diaria (suma por día; días sin operaciones
    valen 0), con el bootstrap estacionario de comparaciones.py.

Muestra final: no se usa nada desde referencia.CORTE (criterios, paso 0.4).

Uso:
    python horizonte_largo.py
    python horizonte_largo.py --retraso 20 # variante 12: entra 20 minutos después
    python horizonte_largo.py --rapido     # solo el año de prueba 2024, sin calibrar; escribe en la carpeta temporal

Salida:
    resultados/horizonte_largo.md
    datos/modelos/predicciones_cierre.parquet
    datos/modelos/operaciones_cierre.parquet
"""

import argparse
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

import calibracion
import comparaciones
import modelo_velas as mv
import recostear
import referencia
import variables
from descargar_datos import UNIVERSO
from referencia import CORTE, RESULTADOS, SALIDA_MAXIMA, num, resumen

MOMENTOS = [30, 60, 90, 120, 150, 180]        # 10:00 a 12:30
HORIZONTE_BASE = 60                           # de aquí salen las acciones operables
MODELO = "lgbm2"
CALIBRADO = "lgbm2c"
NOMBRE = "lgbm2_cierre"
DESDE = 2020
BASE_CONOCIDA = "1,00 bps (t 1,40 por días)"
BASE_RETRASO = "2,87 bps (t por bloques 2,30)"


def retorno(t: pd.DataFrame, p: dict, salida, entrada=None) -> np.ndarray:
    """log(C[salida] / C[entrada]) de cada fila (entrada por defecto: el minuto de la fila), con los mismos precios y huecos que referencia.py (NaN si falta alguno)."""
    s = pd.Index(UNIVERSO).get_indexer(t["symbol"])
    d = pd.DatetimeIndex(p["dias"]).get_indexer(t["dia"])
    entrada = t["minuto"].to_numpy() if entrada is None else np.asarray(entrada)
    salida = np.broadcast_to(np.asarray(salida), entrada.shape)
    dentro = (salida < variables.MINUTOS) & (entrada < variables.MINUTOS) & (s >= 0) & (d >= 0)
    C = p["C"]
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.log(C[s, d, np.where(dentro, salida, 0)].astype("float64") / C[s, d, entrada].astype("float64"))
    return np.where(dentro, r, np.nan)


def relativo(t: pd.DataFrame, obj: np.ndarray) -> np.ndarray:
    """Retorno menos el promedio de las acciones en ese momento, como variables.agregar_relativos."""
    media = pd.Series(obj, index=t.index).groupby(t["momento"]).transform("mean")
    return obj - media.to_numpy()


def comprobar_obj_60(t: pd.DataFrame, p: dict) -> tuple[float, int]:
    """Con la misma función, el retorno a 60 minutos debe coincidir con obj_60 guardado. Devuelve la diferencia máxima (bps)."""
    mio = retorno(t, p, t["minuto"].to_numpy() + 60)
    guardado = t["obj_60"].to_numpy(dtype="float64")
    iguales_nan = (np.isfinite(mio) == np.isfinite(guardado)).all()
    ok = np.isfinite(mio) & np.isfinite(guardado)
    dif = np.abs(mio[ok] - guardado[ok]).max() * 1e4
    rel = np.abs(relativo(t, mio)[ok] - t["rel_60"].to_numpy(dtype="float64")[ok]).max() * 1e4
    print(f"Comprobación obj_60: {ok.sum():,} filas comparadas, diferencia máxima {dif:.6f} bps "
          f"(rel_60: {rel:.6f} bps), huecos {'iguales' if iguales_nan else 'DISTINTOS'}")
    return max(dif, rel), int(ok.sum())


def validar(t: pd.DataFrame, columnas: list[str], y: np.ndarray, primer_anio: int, ultimo_anio: int) -> tuple[pd.DataFrame, dict]:
    """Predicciones hacia adelante de LightGBM v2, en bps, para cada año de prueba."""
    anio = t["dia"].dt.year
    partes, elecciones = [], {}
    for a in range(primer_anio, ultimo_anio + 1):
        e, p = (anio < a).values, (anio == a).values
        inicio = time.time()
        salida = t.loc[p, ["symbol", "momento", "dia", "minuto"]].copy()
        salida["obj_bps"], salida["rel_bps"] = t.loc[p, "obj_cierre"].values * 1e4, y[p]
        salida[MODELO], _, elecciones[a] = mv.predecir_lgbm2(t.loc[e, columnas], y[e], anio[e].values, t.loc[e, "momento"].values, t.loc[p, columnas])
        partes.append(salida)
        print(f"   cierre · prueba {a}: {e.sum():,} filas de entrenamiento, {p.sum():,} de prueba, {time.time() - inicio:.0f} s")
    return pd.concat(partes, ignore_index=True), elecciones


def operar(pred: pd.DataFrame, columna: str, operables: set, costo, retraso: int = 0) -> pd.DataFrame:
    """Opera si |predicción| supera el costo esperado; una operación por acción y día, la del primer momento. Sale a las 15:55."""
    x = pred[pred["symbol"].isin(operables) & pred["minuto"].isin(MOMENTOS)].sort_values(["dia", "minuto", "symbol"])
    entra = np.abs(x[columna].values) > costo(x, atras=1)
    x = x[entra].drop_duplicates(["symbol", "dia"], keep="first")
    paga = costo(x)
    direccion = np.sign(x[columna].values)
    o = pd.DataFrame({"modelo": NOMBRE, "symbol": x["symbol"].values, "dia": x["dia"].values, "entrada": x["minuto"].values + retraso,
                      "salida": SALIDA_MAXIMA, "direccion": direccion.astype("int8"), "esperado_bps": np.abs(x[columna].values),
                      "bruto_bps": direccion * x["obj_bps"].values, "costo_bps": paga})
    o["neto_bps"] = o["bruto_bps"] - o["costo_bps"]
    o["seleccion_bps"] = direccion * x["rel_bps"].values
    o["mercado_bps"] = o["bruto_bps"] - o["seleccion_bps"]
    return o.reset_index(drop=True)


def serie_diaria(o: pd.DataFrame, dias: pd.DatetimeIndex, costos: float = 1.0) -> pd.Series:
    """Ganancia neta diaria (suma por día) en los días dados; sin operaciones vale 0."""
    neto = o["bruto_bps"] - costos * o["costo_bps"]
    return neto.groupby(o["dia"]).sum().reindex(dias, fill_value=0.0)


def t_bloques(serie: pd.Series) -> float:
    """Media entre la desviación de las medias remuestreadas (bootstrap estacionario de comparaciones.py)."""
    idx = comparaciones.indices_del_remuestreo(len(serie), np.random.default_rng(comparaciones.SEMILLA))
    v = serie.to_numpy()
    medias = np.concatenate([v[idx[i:i + 500]].mean(axis=1) for i in range(0, len(idx), 500)])
    return serie.mean() / medias.std(ddof=1)


def t_dias(valor: pd.Series, dia: pd.Series) -> float:
    d = valor.groupby(dia.values).sum()
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else np.nan


def informe(pred: pd.DataFrame, o: pd.DataFrame, dias: pd.DatetimeIndex, pendientes: dict, elecciones: dict, n_operables: int,
            comprobacion: tuple, desde: int, rapido: bool, tiempo: float, retraso: int = 0) -> str:
    s, doble = resumen(o), resumen(o, 2.0)
    serie, serie_doble = serie_diaria(o, dias), serie_diaria(o, dias, 2.0)
    ic, t_ic = mv.orden_acertado(pred, MODELO)
    ultimo = int(pred["dia"].dt.year.max())
    titulo = f"# Horizonte hasta el cierre (idea 5), entrada retrasada {retraso} minutos (variante 12)" if retraso else "# Horizonte hasta el cierre (idea 5)"
    L = [titulo, "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `horizonte_largo.py`. Validación hacia adelante: cada año de {int(pred['dia'].dt.year.min())} a {ultimo} se "
         f"predice con un modelo entrenado solo con los años anteriores. Comparación de {desde} a {ultimo}. No incluye la muestra final."
         + (" **Corrida rápida (`--rapido`): solo el año de prueba 2024 y sin calibrar; no son los resultados oficiales.**" if rapido else ""), "",
         "Unidades: bps por operación (1 bps = 0,01%). El modelo predice el retorno hasta las 15:55 (minuto 384) menos el promedio de las acciones; "
         f"se decide cada 30 minutos de 10:00 a 12:30, con una operación por acción y por día como máximo (la del primer momento que supera el costo). "
         f"Costo: el spread de la época, un spread completo por operación. {n_operables} acciones operables (las de 60 minutos). Sin cobertura.", "",
         f"Comprobación del objetivo: con la misma función, el retorno a 60 minutos coincide con `obj_60` guardado (diferencia máxima {num(comprobacion[0], 6)} bps "
         f"en {num(comprobacion[1], 0)} filas).", "",
         (f"Entrada retrasada {retraso} minutos: el modelo decide en los mismos momentos y con las mismas variables, pero entra en el minuto k + {retraso} "
          f"y el objetivo es el retorno desde esa entrada hasta las 15:55, menos el promedio de las acciones. "
          f"Base de comparación conocida: la idea 5 sin retraso, {BASE_RETRASO}." if retraso else
          f"Base de comparación conocida: la calibrada a 60 minutos con costo de la época, volviendo a decidir, dio {BASE_CONOCIDA}."), "",
         "Variantes probadas hasta ahora: " + ("12 (t exigido con Bonferroni 2,64)." if retraso else "11 (t exigido con Bonferroni 2,61)."), "",
         "## Resultado", "",
         "| Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t por días | t por bloques | Neta con costo doble | t por bloques (doble) |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
         f"| {num(s['n'], 0)} | {num(s['dias'], 0)} de {len(dias)} | {num(100 * s['acierto'])}% | {num(s['bruto'], 2)} | {num(s['costo'], 2)} | {num(s['neto'], 2)} | "
         f"{num(s['t'], 2)} | {num(t_bloques(serie), 2)} | {num(doble['neto'], 2)} | {num(t_bloques(serie_doble), 2)} |", "",
         "El t por bloques usa la ganancia neta diaria (suma por día; los días sin operaciones valen 0) y el remuestreo de `comparaciones.py` "
         f"(bloques de {comparaciones.BLOQUE} días, {num(comparaciones.REMUESTREOS, 0)} remuestreos, semilla {comparaciones.SEMILLA}).", "",
         "## Por año", "",
         "| Año | Ganancia neta | Operaciones | Neta con costo doble | Pendiente de calibración | Elección de la búsqueda |", "| --- | --- | --- | --- | --- | --- |"]
    for a in sorted(pred["dia"].dt.year.unique()):
        x = o[o["dia"].dt.year == a]
        L.append(f"| {a} | {num(x['neto_bps'].mean(), 2)} | {num(len(x), 0)} | {num((x['bruto_bps'] - 2 * x['costo_bps']).mean(), 2)} | "
                 f"{num(pendientes.get(a, np.nan), 2)} | {elecciones.get(a, '—')} |")
    if rapido:
        L += ["", "Sin 2020: no aplica en la corrida rápida."]
    else:
        o2, dias2 = o[o["dia"].dt.year != 2020], dias[dias.year != 2020]
        L += ["", f"Sin 2020: neta {num(o2['neto_bps'].mean(), 2)} bps por operación, t por bloques {num(t_bloques(serie_diaria(o2, dias2)), 2)}."]
    trimestre = o.groupby(o["dia"].dt.to_period("Q"))["neto_bps"].sum()
    L += ["", f"Trimestres con ganancia neta positiva: {int((trimestre > 0).sum())} de {len(trimestre)}.", "",
          "## Selección y mercado", "",
          "Ganancia bruta = selección (dirección por el retorno relativo) + mercado (el resto).", "",
          "| Parte | Media por operación | t por días |", "| --- | --- | --- |"]
    for nombre, c in (("Selección", "seleccion_bps"), ("Mercado", "mercado_bps")):
        L.append(f"| {nombre} | {num(o[c].mean(), 2)} | {num(t_dias(o[c], o['dia']), 2)} |")
    L += ["", "## ¿El modelo ordena bien las acciones?", "",
          f"Correlación de rangos media entre la predicción sin calibrar y el retorno relativo real, por momento y promediada por día (50 acciones): "
          f"{num(ic, 4)} (t {num(t_ic, 2)}).", "",
          "## Operaciones por momento de entrada", "", "| Entrada | Operaciones | Neta por operación |", "| --- | --- | --- |"]
    for m in MOMENTOS:
        x = o[o["entrada"] == m + retraso]
        L.append(f"| {(570 + m + retraso) // 60}:{(570 + m + retraso) % 60:02d} | {num(len(x), 0)} | {num(x['neto_bps'].mean(), 2)} |")
    L += ["", f"Tiempo de la corrida: {tiempo / 60:.1f} minutos.", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Idea 5: modelo de velas con salida a las 15:55.")
    ap.add_argument("--rapido", action="store_true", help="Solo el año de prueba 2024, sin calibrar; escribe en la carpeta temporal")
    ap.add_argument("--retraso", type=int, default=0, help="Minutos de retraso de la entrada (variante 12); por defecto 0")
    args = ap.parse_args()
    retraso = args.retraso
    sufijo = f"_retraso{retraso}" if retraso else ""
    inicio = time.time()

    t, base, columnas = mv.cargar()
    p = referencia.cargar_precios()
    comprobacion = comprobar_obj_60(t, p)

    t = t[t["minuto"].isin(MOMENTOS)].reset_index(drop=True)
    t["obj_cierre"] = retorno(t, p, SALIDA_MAXIMA, t["minuto"].to_numpy() + retraso)
    t["rel_cierre"] = relativo(t, t["obj_cierre"].to_numpy())
    t = t[np.isfinite(t["obj_cierre"]) & np.isfinite(t["rel_cierre"])].reset_index(drop=True)
    y = (t["rel_cierre"] * 1e4).to_numpy()
    print(f"{len(t):,} filas en {len(MOMENTOS)} momentos, {len(columnas)} variables")

    ultimo = CORTE.year - 1
    primer = ultimo if args.rapido else mv.PRIMER_ANIO_DE_PRUEBA
    pred, elecciones = validar(t, columnas, y, primer, ultimo)

    _, universo = referencia.costos_y_universo()
    rv = recostear.volatilidad_diaria()
    tabla, muestras, e = recostear.spreads_por_trimestre(rv)
    costo = lambda o, atras=0: recostear.costo_de(o, tabla, rv, e["beta"], atras)
    operables = set(np.array(UNIVERSO)[universo[HORIZONTE_BASE]]) & set(pred["symbol"].unique()) & set(muestras["symbol"].unique())

    pred[CALIBRADO], pendientes = calibracion.calibrar(pred, operables)
    if pendientes:
        pred = pred[pred["dia"].dt.year >= min(pendientes)]
    else:
        print("Sin años de prueba anteriores: no se calibra (pendiente 1).")
        pred[CALIBRADO] = pred[MODELO]
    desde = min(pendientes) if pendientes else primer
    o = operar(pred, CALIBRADO, operables, costo, retraso)

    salida = Path(tempfile.gettempdir()) / "horizonte_largo_rapido" if args.rapido else None
    if salida is not None:
        salida.mkdir(parents=True, exist_ok=True)
    carpeta_datos, carpeta_informe = (salida, salida) if args.rapido else (mv.CARPETA, RESULTADOS)
    carpeta_datos.mkdir(parents=True, exist_ok=True)
    pred.to_parquet(carpeta_datos / f"predicciones_cierre{sufijo}.parquet", index=False)
    o.to_parquet(carpeta_datos / f"operaciones_cierre{sufijo}.parquet", index=False)

    dias = pd.DatetimeIndex(p["dias"])
    dias = dias[(dias.year >= desde) & (dias < CORTE) & ~p["medio_dia"]]
    texto = informe(pred, o, dias, pendientes, elecciones, len(operables), comprobacion, desde, args.rapido, time.time() - inicio, retraso)
    (carpeta_informe / f"horizonte_largo{sufijo}.md").write_text(texto, encoding="utf-8")
    print(f"Escrito en {carpeta_informe}")
    print(texto)


if __name__ == "__main__":
    main()
