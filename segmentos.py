"""
Pasos 2.3 y 2.4 · Segmentos: grupos de acciones y regímenes de mercado.

Regla anti-anticipación: todo se calcula por ventana de la validación hacia
adelante. Para el año de prueba A solo se usan días anteriores a A, y con eso
se etiquetan tanto los años de entrenamiento como el año A.

Grupos de acciones (2.3), con los tres años anteriores a A:
  - Por correlación: a los retornos diarios se les quita el primer componente
    principal (el mercado), y con la correlación de lo que queda se hace un
    clustering jerárquico. Junta las acciones que se mueven juntas.
  - Por características: K-means sobre volatilidad, monto negociado, beta,
    rango del día y cantidad de noticias. Junta las acciones que se parecen.
  El número de grupos se elige con el coeficiente de silueta, dentro de la ventana.

Regímenes de mercado (2.4), con todos los días anteriores a A:
  - Mezcla gaussiana sobre cuatro rasgos de SPY y del conjunto de acciones, todos
    conocidos antes de la apertura: volatilidad de 20 días, volatilidad de 5 días
    frente a la de 20, tendencia de 20 días y dispersión entre acciones.
  - El número de regímenes (2 a 4) se elige con el BIC, dentro de la ventana.
  - Se numeran del más calmado (1) al más volátil.
  No se usa un modelo oculto de Markov: sus estados suavizados miran el futuro.

Diagnóstico: con las predicciones ya guardadas del modelo de velas (primera
versión) se mide si la señal cambia según el régimen o el grupo. Es solo
descriptivo: no entrena nada ni cuenta como variante.

Muestra final: no se usa nada desde referencia.CORTE.

Uso:
    python segmentos.py
    python segmentos.py --prueba-desde 2023     # corrida corta, para probar

Salida:
    resultados/segmentos.md               resumen
    datos/segmentos/grupos.parquet        anio_prueba, symbol, grupo_corr, grupo_car
    datos/segmentos/regimenes.parquet     anio_prueba, dia, regimen y los cuatro rasgos
"""

import argparse

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import squareform
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture

import referencia
from descargar_datos import RAIZ, SECTOR, UNIVERSO
from referencia import CORTE, HORIZONTES, RESULTADOS, num, resumen

CARPETA = RAIZ / "segmentos"
MODELOS = RAIZ / "modelos"
ACCIONES = [s for s in UNIVERSO if SECTOR[s] != "etf"]
PRIMER_ANIO_DE_PRUEBA = 2019
VENTANA_GRUPOS = 3                      # años hacia atrás para agrupar acciones
K_CORRELACION = range(4, 11)
K_CARACTERISTICAS = range(3, 7)
COMPONENTES = range(2, 5)
CARACTERISTICAS = ["vol_20d", "dolares_20d", "beta_60d", "rango_dia", "not_desde_cierre"]
RASGOS = {"vol_20": "Volatilidad anual de SPY", "choque": "Volatilidad de 5 días frente a 20",
          "tendencia": "Tendencia de 20 días", "dispersion": "Dispersión entre acciones"}
SEMILLA = 7


# ---------------------------------------------------------------- datos

def cargar_diario() -> tuple[pd.DataFrame, pd.Series]:
    """Retornos diarios de cada símbolo y volatilidad de SPY dentro de cada día, sin la muestra final."""
    p = referencia.cargar_precios()
    dias = pd.DatetimeIndex(p["dias"])
    antes = dias < CORTE
    C, dias = p["C"][:, antes], dias[antes]
    cierre = pd.DataFrame(C[:, :, -1].T.astype("float64"), index=dias, columns=UNIVERSO)
    r1 = np.diff(np.log(C[UNIVERSO.index("SPY")].astype("float64")), axis=1)
    return np.log(cierre / cierre.shift(1)), pd.Series(np.sqrt(np.nansum(r1 ** 2, axis=1)), index=dias)


def cargar_caracteristicas() -> pd.DataFrame:
    """Una fila por acción y día, con las variables al último momento de decisión (15:45)."""
    columnas = ["symbol", "dia", "minuto", "es_etf", *CARACTERISTICAS]
    archivos = [a for a in sorted((RAIZ / "variables").glob("*.parquet")) if int(a.stem) < CORTE.year]
    t = pd.concat([pd.read_parquet(a, columns=columnas) for a in archivos], ignore_index=True)
    t = t[(t["minuto"] == t["minuto"].max()) & ~t["es_etf"]].drop(columns=["minuto", "es_etf"])
    t["not_desde_cierre"] = np.log1p(t["not_desde_cierre"])
    return t


# ---------------------------------------------------------------- grupos de acciones (2.3)

def grupos_por_correlacion(ret: pd.DataFrame) -> tuple[np.ndarray, dict]:
    """Clustering jerárquico sobre la correlación de los retornos sin el componente de mercado."""
    z = (ret - ret.mean()) / ret.std()
    lleno = z.fillna(0.0).values
    pca = PCA(5).fit(lleno)
    resto = z - np.outer(lleno @ pca.components_[0], pca.components_[0])      # sin el primer componente
    corr = resto.corr(min_periods=120).fillna(0.0).clip(-1, 1).values
    dist = np.sqrt(0.5 * (1 - (corr + corr.T) / 2))
    np.fill_diagonal(dist, 0.0)
    arbol = linkage(squareform(dist, checks=False), "average")
    opciones = {k: fcluster(arbol, k, "maxclust") for k in K_CORRELACION}
    siluetas = {k: silhouette_score(dist, e, metric="precomputed") for k, e in opciones.items() if len(set(e)) > 1}
    k = max(siluetas, key=siluetas.get)
    return opciones[k], dict(k=len(set(opciones[k])), silueta=siluetas[k], varianza=pca.explained_variance_ratio_)


def grupos_por_caracteristicas(car: pd.DataFrame) -> tuple[np.ndarray, dict]:
    """K-means sobre el promedio de cada característica en la ventana."""
    medias = car.groupby("symbol")[CARACTERISTICAS].mean().reindex(ACCIONES)
    X = ((medias - medias.mean()) / medias.std()).fillna(0.0).values
    opciones = {k: KMeans(k, n_init=10, random_state=SEMILLA).fit_predict(X) + 1 for k in K_CARACTERISTICAS}
    siluetas = {k: silhouette_score(X, e) for k, e in opciones.items()}
    k = max(siluetas, key=siluetas.get)
    return opciones[k], dict(k=k, silueta=siluetas[k], medias=medias)


def alinear(nuevas: np.ndarray, previas: np.ndarray | None, tope: int) -> tuple[np.ndarray, int]:
    """Renombra los grupos para que cada uno conserve el número del grupo anterior que más se le parece."""
    a = np.unique(nuevas)
    nombre = {}
    if previas is not None:
        b = np.unique(previas)
        comunes = np.array([[np.sum((nuevas == i) & (previas == j)) for j in b] for i in a])
        filas, columnas = linear_sum_assignment(-comunes)
        nombre = {a[i]: b[j] for i, j in zip(filas, columnas) if comunes[i, j] > 0}
    for i in a:
        if i not in nombre:
            tope += 1
            nombre[i] = tope
    return np.array([nombre[i] for i in nuevas]), tope


# ---------------------------------------------------------------- regímenes (2.4)

def rasgos_del_mercado(ret: pd.DataFrame, vol_spy: pd.Series) -> pd.DataFrame:
    """Rasgos de cada día conocidos antes de la apertura: todo se calcula con los días anteriores."""
    spy = ret["SPY"]
    dispersion = ret[ACCIONES].std(axis=1)
    return pd.DataFrame({
        "vol_20": np.log(vol_spy.rolling(20).mean()),
        "choque": np.log(vol_spy.rolling(5).mean() / vol_spy.rolling(20).mean()),
        "tendencia": spy.rolling(20).sum() / (spy.rolling(20).std() * np.sqrt(20)),
        "dispersion": np.log(dispersion.rolling(20).mean()),
    }).shift(1)


def regimenes(rasgos: pd.DataFrame, anio: int) -> tuple[pd.Series, int]:
    """Mezcla gaussiana ajustada con los días anteriores a `anio`; etiqueta esos días y los de `anio`."""
    todos = rasgos[rasgos.index.year <= anio].dropna()
    e = todos[todos.index.year < anio]
    media, desviacion = e.mean(), e.std()
    X = ((e - media) / desviacion).values
    candidatos = [GaussianMixture(n, covariance_type="full", n_init=5, random_state=SEMILLA).fit(X) for n in COMPONENTES]
    modelo = min(candidatos, key=lambda m: m.bic(X))
    puesto = np.argsort(np.argsort(modelo.means_[:, 0]))                      # del más calmado al más volátil
    etiquetas = puesto[modelo.predict(((todos - media) / desviacion).values)] + 1
    return pd.Series(etiquetas, index=todos.index, name="regimen"), modelo.n_components


# ---------------------------------------------------------------- lectura para los modelos

def de_la_ventana(anio: int) -> tuple[pd.DataFrame, pd.Series]:
    """Grupos (por símbolo) y régimen (por día) calculados para el año de prueba `anio`."""
    g = pd.read_parquet(CARPETA / "grupos.parquet")
    r = pd.read_parquet(CARPETA / "regimenes.parquet")
    return (g[g["anio_prueba"] == anio].set_index("symbol")[["grupo_corr", "grupo_car"]],
            r[r["anio_prueba"] == anio].set_index("dia")["regimen"])


# ---------------------------------------------------------------- diagnóstico con el modelo de velas

def _media_y_t(por_dia: pd.Series) -> tuple[float, float, int]:
    n = len(por_dia)
    return (por_dia.mean(), por_dia.mean() / (por_dia.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan, n)


def diagnostico(h: int, grupos: pd.DataFrame, reg: pd.DataFrame, modelo: str = "lgbm") -> list[str]:
    """¿La señal del modelo de velas cambia según el régimen o el grupo? Solo describe; no elige nada."""
    pred = pd.read_parquet(MODELOS / f"predicciones_{h}.parquet", columns=["symbol", "momento", "dia", "rel_bps", modelo])
    ops = pd.read_parquet(MODELOS / f"operaciones_{h}.parquet")
    ops = ops[ops["modelo"] == modelo]
    propio = reg[reg["anio_prueba"] == reg["dia"].dt.year].set_index("dia")["regimen"]   # cada día, con la ventana de su año
    grupo = grupos.set_index(["anio_prueba", "symbol"])["grupo_car"]

    # Correlación de rangos por momento, promediada por día.
    r = pred.groupby("momento")[[modelo, "rel_bps"]].rank()
    r -= r.groupby(pred["momento"]).transform("mean")
    suma = lambda x: x.groupby(pred["momento"]).sum()
    ic = suma(r[modelo] * r["rel_bps"]) / np.sqrt(suma(r[modelo] ** 2) * suma(r["rel_bps"] ** 2))
    ic_dia = ic.groupby(pred.groupby("momento")["dia"].first()).mean().dropna()

    L = [f"### Horizonte de {h} minutos", "", "Por régimen (cada día se etiqueta con el modelo de regímenes de su propio año de prueba):", "",
         "| Régimen | Días | Correlación de rangos | t | Operaciones | Ganancia bruta | Ganancia neta | t |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    reg_ops = ops["dia"].map(propio)
    for k in sorted(propio.loc[ic_dia.index.intersection(propio.index)].unique()):
        m, t, n = _media_y_t(ic_dia[propio.reindex(ic_dia.index) == k])
        o = ops[reg_ops == k]
        s = resumen(o) if len(o) else dict(n=0, bruto=np.nan, neto=np.nan, t=np.nan)
        L.append(f"| {k} | {num(n, 0)} | {num(m, 4)} | {num(t, 2)} | {num(s['n'], 0)} | {num(s['bruto'], 2)} | {num(s['neto'], 2)} | {num(s['t'], 2)} |")

    # Por grupo: retorno relativo de seguir la predicción en todas las filas, sin filtrar por costo.
    pred["grupo"] = pd.MultiIndex.from_arrays([pred["dia"].dt.year, pred["symbol"]]).map(grupo)
    pred["seguir"] = np.sign(pred[modelo]) * pred["rel_bps"]
    grupo_ops = pd.MultiIndex.from_arrays([ops["dia"].dt.year, ops["symbol"]]).map(grupo)
    L += ["", "Por grupo de características (el número de cada grupo se mantiene de un año a otro cuando el grupo se parece):", "",
          "| Grupo | Retorno relativo siguiendo la predicción, sin filtrar | t | Operaciones | Ganancia bruta | Ganancia neta | t |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for k in sorted(pred["grupo"].dropna().unique()):
        x = pred[pred["grupo"] == k]
        m, t, _ = _media_y_t(x.groupby("dia")["seguir"].mean())
        o = ops[grupo_ops == k]
        s = resumen(o) if len(o) else dict(n=0, bruto=np.nan, neto=np.nan, t=np.nan)
        L.append(f"| {int(k)} | {num(m, 2)} | {num(t, 2)} | {num(s['n'], 0)} | {num(s['bruto'], 2)} | {num(s['neto'], 2)} | {num(s['t'], 2)} |")
    return L + [""]


# ---------------------------------------------------------------- informe

def informe(grupos: pd.DataFrame, reg: pd.DataFrame, detalle: dict, anios: list[int]) -> str:
    ultimo = anios[-1]
    L = ["# Segmentos: grupos de acciones y regímenes de mercado (pasos 2.3 y 2.4)", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `segmentos.py`. Para cada año de prueba, de {anios[0]} a {ultimo}, los grupos y los "
         "regímenes se calculan solo con días anteriores a ese año. No incluye la muestra final.", "",
         "## 1. Grupos de acciones", "",
         f"Con los {VENTANA_GRUPOS} años anteriores a cada año de prueba. La silueta va de −1 a 1: cerca de 0, los grupos se confunden entre sí. "
         "El parecido va de 0 (como al azar) a 1 (idénticos).", "",
         "| Año de prueba | Grupos por correlación | Silueta | Parecido con los sectores | Parecido con el año anterior | Grupos por características | Silueta | Parecido con el año anterior |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    sectores = pd.Series(SECTOR).reindex(ACCIONES).astype("category").cat.codes.values
    previo = None
    for a in anios:
        g = grupos[grupos["anio_prueba"] == a].set_index("symbol").reindex(ACCIONES)
        d = detalle[a]
        igual = lambda c: "—" if previo is None else num(adjusted_rand_score(previo[c], g[c]), 2)
        L.append(f"| {a} | {d['corr']['k']} | {num(d['corr']['silueta'], 2)} | {num(adjusted_rand_score(sectores, g['grupo_corr']), 2)} | {igual('grupo_corr')} | "
                 f"{d['car']['k']} | {num(d['car']['silueta'], 2)} | {igual('grupo_car')} |")
        previo = g
    v = detalle[ultimo]["corr"]["varianza"]
    L += ["", f"En la ventana de {ultimo}, el primer componente principal (el mercado) explica el {num(100 * v[0], 0)}% de la variación de los retornos diarios; "
          f"los cuatro siguientes, {', '.join(num(100 * x, 0) + '%' for x in v[1:])}.", "",
          f"### Grupos por correlación en la ventana de {ultimo}", "", "| Grupo | Acciones |", "| --- | --- |"]
    g = grupos[grupos["anio_prueba"] == ultimo]
    for k, x in g.groupby("grupo_corr"):
        L.append(f"| {k} | {', '.join(f'{s} ({SECTOR[s]})' for s in x['symbol'])} |")
    medias = detalle[ultimo]["car"]["medias"]
    L += ["", f"### Grupos por características en la ventana de {ultimo}", "",
          "| Grupo | Acciones | Volatilidad diaria | Monto diario (millones de dólares) | Beta | Noticias por día |", "| --- | --- | --- | --- | --- | --- |"]
    for k, x in g.groupby("grupo_car"):
        m = medias.loc[x["symbol"]].mean()
        L.append(f"| {k} | {', '.join(x['symbol'])} | {num(100 * m['vol_20d'], 2)}% | {num(np.exp(m['dolares_20d']) / 1e6, 0)} | {num(m['beta_60d'], 2)} | "
                 f"{num(np.expm1(m['not_desde_cierre']), 1)} |")

    L += ["", "## 2. Regímenes de mercado", "",
          "Se numeran del más calmado (1) al más volátil. El número de regímenes lo elige el BIC en cada ventana, entre 2 y 4.", "",
          f"### Cómo es cada régimen en la ventana de {ultimo} (días de entrenamiento)", "",
          "| Régimen | Días | " + " | ".join(RASGOS.values()) + " |", "| --- | --- |" + " --- |" * len(RASGOS)]
    r = reg[(reg["anio_prueba"] == ultimo) & (reg["dia"].dt.year < ultimo)]
    for k, x in r.groupby("regimen"):
        L.append(f"| {k} | {num(100 * len(x) / len(r), 0)}% | {num(100 * np.sqrt(252) * np.exp(x['vol_20']).median(), 1)}% | "
                 f"{num(np.exp(x['choque']).median(), 2)} veces | {num(x['tendencia'].mean(), 2)} | {num(1e4 * np.exp(x['dispersion']).median(), 0)} bps |")
    propio = reg[reg["anio_prueba"] == reg["dia"].dt.year]
    maximo = int(propio["regimen"].max())
    L += ["", "### Días de cada año de prueba en cada régimen", "",
          "Cada año se etiqueta con el modelo ajustado solo con los años anteriores.", "",
          "| Año | Regímenes | " + " | ".join(f"Régimen {k}" for k in range(1, maximo + 1)) + " |", "| --- | --- |" + " --- |" * maximo]
    for a in anios:
        x = propio[propio["anio_prueba"] == a]["regimen"]
        L.append(f"| {a} | {detalle[a]['n_regimenes']} | " + " | ".join(f"{num(100 * (x == k).mean(), 0)}%" for k in range(1, maximo + 1)) + " |")

    if all((MODELOS / f"predicciones_{h}.parquet").exists() for h in HORIZONTES):
        L += ["", "## 3. ¿La señal del modelo de velas cambia según el régimen o el grupo?", "",
              "Con las predicciones guardadas de LightGBM (primera versión) en los años que cubren los segmentos. Es descriptivo: no se entrenó nada con grupos "
              "ni regímenes, y operar solo en el régimen o el grupo que mejor salió sería una variante nueva. Unidades: bps; los t agrupan por día.", ""]
        for h in HORIZONTES:
            L += diagnostico(h, grupos, reg)
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Grupos de acciones y regímenes de mercado, por ventana de validación.")
    ap.add_argument("--prueba-desde", type=int, default=PRIMER_ANIO_DE_PRUEBA, help="Primer año de prueba")
    args = ap.parse_args()

    ret, vol_spy = cargar_diario()
    rasgos = rasgos_del_mercado(ret, vol_spy)
    car = cargar_caracteristicas()
    anios = list(range(args.prueba_desde, CORTE.year))
    partes_g, partes_r, detalle = [], [], {}
    previas, topes = {"corr": None, "car": None}, {"corr": 0, "car": 0}
    for a in anios:
        ventana = (ret.index.year >= a - VENTANA_GRUPOS) & (ret.index.year < a)
        anio_car = car["dia"].dt.year
        corr, d_corr = grupos_por_correlacion(ret.loc[ventana, ACCIONES])
        cars, d_car = grupos_por_caracteristicas(car[(anio_car >= a - VENTANA_GRUPOS) & (anio_car < a)])
        for clave, etiquetas in (("corr", corr), ("car", cars)):
            previas[clave], topes[clave] = alinear(etiquetas, previas[clave], topes[clave])
        partes_g.append(pd.DataFrame({"anio_prueba": a, "symbol": ACCIONES, "grupo_corr": previas["corr"], "grupo_car": previas["car"]}))
        r, n = regimenes(rasgos, a)
        partes_r.append(rasgos.loc[r.index].assign(regimen=r, anio_prueba=a).rename_axis("dia").reset_index())
        detalle[a] = dict(corr=d_corr, car=d_car, n_regimenes=n)
        print(f"   {a}: {d_corr['k']} grupos por correlación, {d_car['k']} por características, {n} regímenes")

    grupos, reg = pd.concat(partes_g, ignore_index=True), pd.concat(partes_r, ignore_index=True)
    texto = informe(grupos, reg, detalle, anios)
    if args.prueba_desde == PRIMER_ANIO_DE_PRUEBA:
        CARPETA.mkdir(parents=True, exist_ok=True)
        grupos.to_parquet(CARPETA / "grupos.parquet", index=False)
        reg.to_parquet(CARPETA / "regimenes.parquet", index=False)
        (RESULTADOS / "segmentos.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
