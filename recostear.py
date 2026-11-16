"""
Sensibilidad al costo: vuelve a costear las operaciones con el spread de su época.

Hasta ahora el costo de cada operación es el spread de la acción medido en los
últimos 60 días de mercado, el mismo número para toda la historia. Aquí se usa
el spread medido en el trimestre en que ocurrió la operación
(muestrear_spread.py --historico: 8 momentos por símbolo y trimestre).

Dos lecturas:
  a) Mismas operaciones, costo de la época. No cambia qué se operó; solo cuánto costó.
  b) Volviendo a decidir. El modelo de velas opera cuando la ganancia esperada
     supera el costo; aquí el costo esperado es el spread del trimestre anterior
     (lo que se podía saber en ese momento) y se cobra el del trimestre en curso.
     Aplica a la segunda versión y a la calibrada. La referencia y el filtro no
     deciden con el costo, así que solo tienen la lectura a).

El spread de un trimestre es la mediana de sus muestras; si hay menos de 4 con
cotización, se usa la mediana del año de ese símbolo.

Ajuste por volatilidad del día: dentro de un trimestre el spread no es parejo
(en marzo de 2020 fue mucho mayor que en enero). Con todas las muestras se mide
cuánto sube el spread cuando sube la volatilidad del día (una sola elasticidad
para todos los símbolos, comparando cada muestra con su propio símbolo y
trimestre), y el spread de cada operación se corrige con la volatilidad de su
día frente a la de los días muestreados. Para decidir (lectura b) se usa la
volatilidad del día anterior.

No entrena nada. Las acciones operables siguen siendo las del paso 2.1.
Muestra final: no se usa nada desde referencia.CORTE.

Uso:
    python recostear.py

Salida:
    resultados/costo_historico.md
"""

import numpy as np
import pandas as pd

import calibracion
import modelo_velas as mv
import referencia
from descargar_datos import RAIZ, UNIVERSO
from referencia import HORIZONTES, RESULTADOS, num

HISTORICO = RAIZ / "spread_historico"
MINIMO_MUESTRAS = 4
DESDE = 2020            # mismo periodo de la calibración y el filtro


def volatilidad_diaria() -> pd.DataFrame:
    """Volatilidad de cada símbolo dentro de cada día (retornos de 1 minuto), días x símbolos."""
    p = referencia.cargar_precios()
    with np.errstate(invalid="ignore", divide="ignore"):
        r1 = np.diff(np.log(p["C"].astype("float64")), axis=2)
    rv = np.sqrt(np.nansum(r1 ** 2, axis=2)).T
    return pd.DataFrame(np.where(rv > 0, rv, np.nan), index=pd.DatetimeIndex(p["dias"]), columns=UNIVERSO)


def spreads_por_trimestre(rv: pd.DataFrame, carpeta=HISTORICO) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Spread (bps) y volatilidad de referencia por símbolo y trimestre, las muestras, y la elasticidad del spread a la volatilidad.

    carpeta: de dónde salen las muestras (por defecto datos/spread_historico; muestra_final.py usa también datos/spread_reciente).
    """
    t = pd.concat([pd.read_parquet(a) for a in sorted(carpeta.glob("*.parquet"))], ignore_index=True)
    local = t["momento"].dt.tz_convert("America/New_York").dt.tz_localize(None)
    t["trimestre"], t["anio"], t["dia"] = local.dt.to_period("Q"), local.dt.year, local.dt.normalize()
    t = t[t["anio"] >= 2016]      # el archivo de velas de 2016 trae la tarde del 31 de diciembre de 2015
    largo = rv.rename_axis(index="dia", columns="symbol").stack().rename("rv").reset_index()
    largo["dia"] = largo["dia"].astype(t["dia"].dtype)
    t = t.merge(largo, on=["symbol", "dia"], how="left")
    t["log_spread"], t["log_rv"] = np.log(t["spread_bps"]), np.log(t["rv"])
    ok = t.dropna(subset=["log_spread", "log_rv"])

    # Elasticidad: cada muestra frente al promedio de su símbolo y trimestre.
    g = ok.groupby(["symbol", "trimestre"])
    x, y = ok["log_rv"] - g["log_rv"].transform("mean"), ok["log_spread"] - g["log_spread"].transform("mean")
    beta = (x * y).sum() / (x ** 2).sum()
    resto = y - beta * x
    error = np.sqrt((resto ** 2).sum() / (len(ok) - g.ngroups - 1) / (x ** 2).sum())
    elasticidad = dict(beta=beta, t=beta / error, r2=1 - (resto ** 2).sum() / (y ** 2).sum(), n=len(ok))

    q = g.agg(mediana=("spread_bps", "median"), n=("spread_bps", "size"), ref=("log_rv", "mean")).reset_index()
    anual = ok.groupby(["symbol", "anio"]).agg(mediana=("spread_bps", "median"), ref=("log_rv", "mean"))
    del_anio = anual.reindex(pd.MultiIndex.from_arrays([q["symbol"], q["trimestre"].dt.year]))
    pocas = (q["n"] < MINIMO_MUESTRAS).values
    q["spread"] = np.where(pocas, del_anio["mediana"].values, q["mediana"])
    q["ref"] = np.where(pocas, del_anio["ref"].values, q["ref"])
    return q.set_index(["symbol", "trimestre"])[["spread", "ref"]], t, elasticidad


def costo_de(o: pd.DataFrame, tabla: pd.DataFrame, rv: pd.DataFrame, beta: float, atras: int = 0) -> np.ndarray:
    """Spread de cada fila: el de su trimestre corregido por la volatilidad de su día.

    Con atras=1 es lo que se podía saber antes de operar: el trimestre anterior y la volatilidad del día anterior.
    """
    llave = pd.MultiIndex.from_arrays([o["symbol"], o["dia"].dt.to_period("Q") - atras])
    base, ref = tabla["spread"].reindex(llave).to_numpy(dtype="float64"), tabla["ref"].reindex(llave).to_numpy(dtype="float64")
    v = rv.shift(atras)
    fila, columna = v.index.get_indexer(o["dia"]), v.columns.get_indexer(o["symbol"])
    if (fila < 0).any() or (columna < 0).any():      # get_indexer da -1 y numpy tomaría la última fila sin avisar
        raise ValueError(f"costo_de: {(fila < 0).sum()} días y {(columna < 0).sum()} símbolos no están en la tabla de volatilidad")
    del_dia = np.log(v.to_numpy()[fila, columna])
    ajuste = np.exp(np.clip(beta * (del_dia - ref), np.log(0.25), np.log(8.0)))
    return base * np.where(np.isfinite(ajuste), ajuste, 1.0)


def decidir(pred: pd.DataFrame, columna: str, h: int, operables: set, costo) -> pd.DataFrame:
    """La regla del modelo de velas, esperando el spread del trimestre anterior y pagando el del trimestre en curso."""
    x = pred[pred["symbol"].isin(operables) & (pred["minuto"] % h == 30 % h)]
    espera, paga = costo(x, atras=1), costo(x)
    entra = np.abs(x[columna].values) > espera
    x, paga = x[entra], paga[entra]
    direccion = np.sign(x[columna].values)
    return pd.DataFrame({"symbol": x["symbol"].values, "dia": x["dia"].values, "bruto_bps": direccion * x["obj_bps"].values, "costo_epoca": paga})


def fila(nombre: str, o: pd.DataFrame) -> str:
    """Una línea de la tabla: con el costo de hoy (si lo tiene) y con el de la época."""
    def t_de(neto):
        d = neto.groupby(o["dia"]).sum()
        return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    hoy = "— | — | —"
    if "costo_bps" in o:
        neto = o["bruto_bps"] - o["costo_bps"]
        hoy = f"{num(o['costo_bps'].mean(), 2)} | {num(neto.mean(), 2)} | {num(t_de(neto), 2)}"
    neto = o["bruto_bps"] - o["costo_epoca"]
    doble = o["bruto_bps"] - 2 * o["costo_epoca"]
    return (f"| {nombre} | {num(len(o), 0)} | {hoy} | {num(o['costo_epoca'].mean(), 2)} | {num(neto.mean(), 2)} | {num(t_de(neto), 2)} | "
            f"{num(doble.mean(), 2)} | {num(t_de(doble), 2)} |")


def main() -> None:
    rv = volatilidad_diaria()
    tabla, muestras, e = spreads_por_trimestre(rv)
    costo = lambda o, atras=0: costo_de(o, tabla, rv, e["beta"], atras)
    medidos = set(muestras["symbol"].unique())
    faltan = [s for s in UNIVERSO if s not in medidos]
    costo_hoy, universo = referencia.costos_y_universo()
    hoy = pd.Series(costo_hoy, index=UNIVERSO)

    L = ["# Sensibilidad al costo: el spread de cada época", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `recostear.py`. Vuelve a costear las operaciones guardadas con el spread del trimestre en que ocurrieron, "
         "medido con cotizaciones de ese trimestre. No entrena nada y no incluye la muestra final.", ""]
    if faltan:
        L += [f"**Informe parcial:** faltan por medir {len(faltan)} símbolos ({', '.join(faltan)}). Solo entran las operaciones de los {len(medidos)} ya medidos.", ""]

    # 1. Cómo ha cambiado el spread
    anual = muestras.groupby(["symbol", "anio"])["spread_bps"].median().unstack("anio")
    L += ["## 1. Cuánto costaba operar cada año", "",
          "Mediana, entre símbolos, del spread de cada año en horario normal, y el mismo dato frente al spread que se usa hoy para toda la historia.", "",
          "| Año | Spread mediano | Frente al de hoy | Símbolo que más cambia |", "| --- | --- | --- | --- |"]
    razon = anual.div(hoy.reindex(anual.index), axis=0)
    for a in anual.columns:
        r = razon[a].dropna()
        L.append(f"| {a} | {num(anual[a].median(), 2)} bps | {num(r.median(), 2)} veces | {r.idxmax()} ({num(r.max(), 1)} veces) |")
    t20 = muestras[(muestras["trimestre"] == pd.Period("2020Q1"))].groupby("symbol")["spread_bps"].median()
    r20 = (t20 / hoy.reindex(t20.index)).dropna()
    m20 = muestras[(muestras["dia"] >= "2020-03-01") & (muestras["dia"] < "2020-04-01")].groupby("symbol")["spread_bps"].median()
    rm20 = (m20 / hoy.reindex(m20.index)).dropna()
    L += ["", f"Primer trimestre de 2020: el spread mediano fue {num(r20.median(), 2)} veces el de hoy. Solo en marzo de 2020 "
          f"({num(muestras[(muestras['dia'] >= '2020-03-01') & (muestras['dia'] < '2020-04-01')]['spread_bps'].notna().sum(), 0)} muestras): {num(rm20.median(), 2)} veces.", "",
          f"**Spread y volatilidad del día:** cuando la volatilidad del día sube 1%, el spread sube {num(e['beta'], 2)}% (t {num(e['t'], 1)}, con {num(e['n'], 0)} muestras; "
          f"explica el {num(100 * e['r2'], 0)}% de la variación dentro de cada símbolo y trimestre). Con esa elasticidad se corrige el spread de cada operación.", ""]

    for h in HORIZONTES:
        operables = (set(np.array(UNIVERSO)[universo[h]]) & medidos) - {s for s in UNIVERSO if referencia.SECTOR[s] == "etf"}
        con = lambda o: o[o["symbol"].isin(medidos) & (o["dia"].dt.year >= DESDE)].assign(costo_epoca=lambda x: costo(x))
        a = con(pd.read_parquet(referencia.CARPETA / f"operaciones_{h}.parquet"))
        b = pd.read_parquet(mv.CARPETA / f"operaciones_{h}.parquet")
        v2 = con(b[b["modelo"] == "lgbm2"])
        cal = con(pd.read_parquet(mv.CARPETA / f"operaciones_calibradas_{h}.parquet"))
        fil = con(pd.read_parquet(mv.CARPETA / f"operaciones_filtro_{h}.parquet"))

        pred = pd.read_parquet(mv.CARPETA / f"predicciones_{h}.parquet")
        todas = set(np.array(UNIVERSO)[universo[h]]) & set(pred["symbol"].unique())
        pred["lgbm2c"], _ = calibracion.calibrar(pred, todas)          # misma pendiente del informe de calibración
        pred = pred[pred["dia"].dt.year >= DESDE]
        v2_b, cal_b = decidir(pred, "lgbm2", h, operables, costo), decidir(pred, "lgbm2c", h, operables, costo)

        L += [f"## Horizonte de {h} minutos ({DESDE}–2024)", "",
              "| Competidor | Operaciones | Costo de hoy | Neta | t | Costo de la época | Neta | t | Neta con el doble | t |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
              fila("A · Referencia", a), fila("B · v2, mismas operaciones", v2), fila("B · v2 calibrada, mismas operaciones", cal),
              fila("B · v2 con filtro, mismas operaciones", fil), fila("B · v2, volviendo a decidir", v2_b),
              fila("B · v2 calibrada, volviendo a decidir", cal_b), "",
              "Versión calibrada, por año (ganancia neta por operación; entre paréntesis, operaciones):", "",
              "| Año | Costo de hoy | Costo de la época | Neta con el costo de hoy | Mismas operaciones, costo de la época | Volviendo a decidir |",
              "| --- | --- | --- | --- | --- | --- |"]
        for anio in sorted(cal["dia"].dt.year.unique()):
            x, y = cal[cal["dia"].dt.year == anio], cal_b[cal_b["dia"].dt.year == anio]
            L.append(f"| {anio} | {num(x['costo_bps'].mean(), 2)} | {num(x['costo_epoca'].mean(), 2)} | {num((x['bruto_bps'] - x['costo_bps']).mean(), 2)} ({num(len(x), 0)}) | "
                     f"{num((x['bruto_bps'] - x['costo_epoca']).mean(), 2)} | {num((y['bruto_bps'] - y['costo_epoca']).mean(), 2)} ({num(len(y), 0)}) |")
        marzo = cal[(cal["dia"] >= "2020-03-01") & (cal["dia"] < "2020-04-01")]
        if len(marzo):
            L += ["", f"Marzo de 2020, versión calibrada: {num(len(marzo), 0)} operaciones; costo de hoy {num(marzo['costo_bps'].mean(), 2)} bps y de la época "
                  f"{num(marzo['costo_epoca'].mean(), 2)}; ganancia total {num((marzo['bruto_bps'] - marzo['costo_bps']).sum(), 0)} bps con el costo de hoy y "
                  f"{num((marzo['bruto_bps'] - marzo['costo_epoca']).sum(), 0)} con el de la época."]
        L.append("")
    texto = "\n".join(L)
    (RESULTADOS / ("costo_historico_parcial.md" if faltan else "costo_historico.md")).write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
