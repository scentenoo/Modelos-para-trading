"""
Comparaciones múltiples: ¿alguna variante gana de verdad, o es la mejor de muchas por suerte?

Cuando se prueban varias variantes y se mira la mejor, su resultado sale inflado.
Aquí se toma la ganancia neta diaria de todas las variantes probadas del modelo
de velas, todas con el costo de la época, y se corrige de tres maneras (criterios, sección 5 del documento):

  - Bonferroni: el valor p de cada variante se multiplica por el número de variantes.
  - Holm: igual de estricto con la mejor y algo menos con las siguientes.
  - SPA de Hansen (2005): pregunta directamente si la mejor variante le gana a
    la base, teniendo en cuenta que las variantes se parecen entre sí. Se hace
    con remuestreo por bloques (bootstrap estacionario), porque los días
    cercanos no son independientes. Se reportan sus tres versiones: la
    consistente es la que se usa; la inferior y la superior la acotan (la
    superior es el Reality Check de White).

Dos bases: no operar (ganancia cero) y la referencia (competidor A).

Todas las variantes se miden en los mismos días (desde 2020, el primer año que
tienen todas). Un día sin operaciones cuenta como ganancia cero. Cada variante
nueva que se pruebe debe agregarse a VARIANTES, también si se descarta.

Costo: todas las variantes usan el costo de la época (recostear.py; se escriben con
recostear_variantes.py en operaciones_epoca_{h}.parquet), igual que la variante hasta el
cierre y la referencia.

Muestra final: las operaciones guardadas no la incluyen.

Uso:
    python comparaciones.py

Salida:
    resultados/comparaciones.md
"""

import numpy as np
import pandas as pd
from scipy.stats import norm

import referencia
from descargar_datos import RAIZ
from referencia import RESULTADOS, num

MODELOS = RAIZ / "modelos"
DESDE = 2020
REMUESTREOS = 10_000
BLOQUE = 10             # largo medio de los bloques del remuestreo, en días
SEMILLA = 7
# (nombre, archivo en datos/modelos, modelo dentro del archivo o None, horizonte)
VARIANTES = [(f"{nombre}, {h} min", "operaciones_epoca_{h}".format(h=h), modelo, h)
             for h in referencia.HORIZONTES
             for nombre, modelo in [("Regresión logística", "logit"),
                                    ("LightGBM v1", "lgbm"),
                                    ("LightGBM v2", "lgbm2"),
                                    ("LightGBM v2 calibrado", "lgbm2c"),
                                    ("LightGBM v2 con filtro", "filtro")]]
# Idea 5: salida a las 15:55; se compara con la referencia de 60 minutos.
VARIANTES.append(("LightGBM v2 calibrado, hasta el cierre", "operaciones_cierre", None, 60))
VARIANTES.append(("LightGBM v2 calibrado, hasta el cierre, entrada 20 min después", "operaciones_cierre_retraso20", None, 60))


def series_diarias() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ganancia neta diaria de cada variante y de la referencia de su horizonte, en bps por acción operable."""
    p = referencia.cargar_precios()
    dias = pd.DatetimeIndex(p["dias"])
    dias = dias[(dias.year >= DESDE) & (dias < referencia.CORTE) & ~p["medio_dia"]]
    _, universo = referencia.costos_y_universo()
    b, a = {}, {}
    for nombre, archivo, modelo, h in VARIANTES:
        o = pd.read_parquet(MODELOS / f"{archivo}.parquet")
        if modelo is not None:
            o = o[o["modelo"] == modelo]
        ref = pd.read_parquet(referencia.CARPETA / f"operaciones_epoca_{h}.parquet")
        n = int(universo[h].sum())
        b[nombre] = (o.groupby("dia")["neto_bps"].sum() / n).reindex(dias, fill_value=0.0)
        a[nombre] = (ref.groupby("dia")["neto_bps"].sum() / n).reindex(dias, fill_value=0.0)
    return pd.DataFrame(b), pd.DataFrame(a)


def indices_del_remuestreo(n: int, azar: np.random.Generator) -> np.ndarray:
    """Bootstrap estacionario: bloques de días seguidos de largo aleatorio (media BLOQUE)."""
    idx = np.empty((REMUESTREOS, n), dtype=np.int32)
    idx[:, 0] = azar.integers(n, size=REMUESTREOS)
    for t in range(1, n):
        nuevo = azar.random(REMUESTREOS) < 1.0 / BLOQUE
        idx[:, t] = np.where(nuevo, azar.integers(n, size=REMUESTREOS), (idx[:, t - 1] + 1) % n)
    return idx


def spa(d: np.ndarray, idx: np.ndarray) -> dict:
    """SPA de Hansen sobre d (días x variantes): ganancia diaria de cada variante menos la base."""
    n, k = d.shape
    media = d.mean(axis=0)
    medias = np.vstack([d[idx[i:i + 500]].mean(axis=1) for i in range(0, len(idx), 500)])     # remuestreos x variantes
    omega = np.sqrt(n) * medias.std(axis=0, ddof=1)
    t = np.sqrt(n) * media / omega
    estadistico = max(t.max(), 0.0)
    umbral = -np.sqrt(2 * np.log(np.log(n)))
    centros = {"inferior": np.maximum(media, 0.0), "consistente": np.where(t >= umbral, media, 0.0), "superior": media}
    p = {}
    for nombre, centro in centros.items():
        t_b = np.maximum((np.sqrt(n) * (medias - centro) / omega).max(axis=1), 0.0)
        p[nombre] = float((t_b >= estadistico).mean())
    return dict(t=t, p=p, media=media)


def tabla(d: pd.DataFrame, r: dict) -> list[str]:
    k = d.shape[1]
    p_solo = norm.sf(r["t"])
    orden = np.argsort(p_solo)
    holm = np.empty(k)
    acumulado = 0.0
    for puesto, i in enumerate(orden):
        acumulado = max(acumulado, min(1.0, (k - puesto) * p_solo[i]))
        holm[i] = acumulado
    L = ["| Variante | Ganancia diaria media | t | p sin corregir | p con Bonferroni | p con Holm |", "| --- | --- | --- | --- | --- | --- |"]
    for i in orden:
        L.append(f"| {d.columns[i]} | {num(r['media'][i], 3)} | {num(r['t'][i], 2)} | {num(p_solo[i], 3)} | {num(min(1.0, k * p_solo[i]), 3)} | {num(holm[i], 3)} |")
    L += ["", f"**SPA de Hansen** (¿la mejor variante le gana a la base?): p = {num(r['p']['consistente'], 3)}. "
          f"Cota inferior {num(r['p']['inferior'], 3)}; cota superior (Reality Check de White) {num(r['p']['superior'], 3)}.", ""]
    return L


def main() -> None:
    b, a = series_diarias()
    idx = indices_del_remuestreo(len(b), np.random.default_rng(SEMILLA))
    contra_cero, contra_a = spa(b.values, idx), spa((b - a).values, idx)
    L = ["# Comparaciones múltiples del modelo de velas", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `comparaciones.py`. {b.shape[1]} variantes, {len(b)} días ({b.index.min():%Y-%m-%d} a {b.index.max():%Y-%m-%d}), "
         f"{num(REMUESTREOS, 0)} remuestreos por bloques de {BLOQUE} días en promedio. No incluye la muestra final.", "",
         "La ganancia diaria está en bps por acción operable, con el costo de la época en todas las variantes. El t se calcula con el remuestreo por bloques, así que puede diferir un poco del de los otros informes. "
         "Pruebas de una cola: un valor p menor que 0,05 indica que la ganancia se distingue de la base.", "",
         "## Contra no operar (ganancia cero)", "", *tabla(b, contra_cero),
         "## Contra la referencia (competidor A)", "", *tabla(b, contra_a)]
    texto = "\n".join(L)
    (RESULTADOS / "comparaciones.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
