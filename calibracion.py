"""
Paso 2.6.c · Calibración: corrige cuánto exagera el modelo de velas antes de comparar con el costo.

El modelo ordena bien las acciones, pero sus predicciones son más grandes que
lo que ocurre después. Como se opera cuando la ganancia esperada supera el
costo, esa exageración deja pasar operaciones que no pagan.

Regla, fijada de antemano:
  - Para cada año de prueba A se calcula una pendiente con las predicciones de
    los años de prueba anteriores a A (que también son fuera de muestra):
    pendiente = suma(predicción x real) / suma(predicción al cuadrado), en las
    acciones operables. Es la recta por el origen que mejor explica lo real.
  - La predicción de A se multiplica por esa pendiente y se opera igual que antes.
  - 2019 no tiene años de prueba anteriores, así que la comparación va de 2020
    en adelante, con la versión sin calibrar medida en esos mismos años.

No reentrena nada: usa las predicciones guardadas por modelo_velas.py.
Cuenta como una variante nueva por horizonte.

Uso:
    python calibracion.py

Salida:
    resultados/calibracion.md
    datos/modelos/operaciones_calibradas_<h>.parquet
"""

import numpy as np
import pandas as pd

import modelo_velas as mv
import referencia
from descargar_datos import UNIVERSO
from referencia import HORIZONTES, RESULTADOS, num, resumen

MODELO = "lgbm2"
CALIBRADO = "lgbm2c"
VARIANTES_PREVIAS = 6


def calibrar(pred: pd.DataFrame, operables: set) -> tuple[pd.Series, dict]:
    """Predicción multiplicada por la pendiente de los años de prueba anteriores; NaN en el primer año."""
    anio = pred["dia"].dt.year
    usa = pred["symbol"].isin(operables)
    salida, pendientes = pd.Series(np.nan, index=pred.index), {}
    for a in sorted(anio.unique())[1:]:
        x = pred[usa & (anio < a)]
        pendientes[a] = (x[MODELO] * x["rel_bps"]).sum() / (x[MODELO] ** 2).sum()
        salida[anio == a] = pendientes[a] * pred.loc[anio == a, MODELO]
    return salida, pendientes


def fila(nombre: str, o: pd.DataFrame, neto_a: pd.Series | None, dias: pd.DatetimeIndex) -> str:
    s, doble = resumen(o), resumen(o, 2.0)
    t_ref = "—" if neto_a is None else num(mv.contra(o.groupby("dia")["neto_bps"].sum(), neto_a, dias), 2)
    return (f"| {nombre} | {num(s['n'], 0)} | {num(100 * s['acierto'])}% | {num(s['bruto'], 2)} | {num(s['costo'], 2)} | {num(s['neto'], 2)} | "
            f"{num(s['t'], 2)} | {num(doble['neto'], 2)} | {num(doble['t'], 2)} | {t_ref} |")


def main() -> None:
    costo_bps, universo = referencia.costos_y_universo()
    costo = pd.Series(costo_bps, index=UNIVERSO)
    L = ["# Calibración del modelo de velas (paso 2.6.c)", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `calibracion.py`, sobre las predicciones guardadas de LightGBM v2. La pendiente de cada año se "
         "calcula solo con años de prueba anteriores. No incluye la muestra final.", "",
         "Unidades: bps por operación. Los t agrupan por día. La comparación va de 2020 en adelante, porque 2019 no tiene años anteriores para calibrar.", "",
         f"Variantes probadas hasta ahora: {VARIANTES_PREVIAS + len(HORIZONTES)} (las {VARIANTES_PREVIAS} de `modelo_velas.py` más la calibrada en cada horizonte).", ""]
    for h in HORIZONTES:
        pred = pd.read_parquet(mv.CARPETA / f"predicciones_{h}.parquet")
        operables = set(np.array(UNIVERSO)[universo[h]]) & set(pred["symbol"].unique())
        pred[CALIBRADO], pendientes = calibrar(pred, operables)
        pred = pred[pred["dia"].dt.year >= min(pendientes)]
        dias = pd.DatetimeIndex(np.sort(pred["dia"].unique()))
        antes, despues = mv.operar(pred, MODELO, h, costo, operables), mv.operar(pred, CALIBRADO, h, costo, operables)
        despues.to_parquet(mv.CARPETA / f"operaciones_calibradas_{h}.parquet", index=False)
        a = pd.read_parquet(referencia.CARPETA / f"operaciones_{h}.parquet")
        a = a[a["dia"].isin(dias)]
        neto_a = a.groupby("dia")["neto_bps"].sum()
        L += [f"## Horizonte de {h} minutos ({len(operables)} acciones operables, {min(pendientes)}–{max(pendientes)})", "",
              "| Competidor | Operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | t | Neta con costo doble | t con costo doble | t contra la referencia |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
              fila("A · Referencia", a, None, dias), fila("B · LightGBM v2", antes, neto_a, dias), fila("B · LightGBM v2 calibrado", despues, neto_a, dias), "",
              "Por año (ganancia neta por operación; entre paréntesis, operaciones):", "",
              "| Año | Pendiente | v2 | v2 calibrado | Calibrado con costo doble |", "| --- | --- | --- | --- | --- |"]
        for anio, b in pendientes.items():
            x1, x2 = antes[antes["dia"].dt.year == anio], despues[despues["dia"].dt.year == anio]
            L.append(f"| {anio} | {num(b, 2)} | {num(x1['neto_bps'].mean(), 2)} ({num(len(x1), 0)}) | {num(x2['neto_bps'].mean(), 2)} ({num(len(x2), 0)}) | "
                     f"{num((x2['bruto_bps'] - 2 * x2['costo_bps']).mean(), 2)} |")
        trimestre = despues.groupby(despues["dia"].dt.to_period("Q"))["neto_bps"].sum()
        L += ["", f"Trimestres con ganancia neta positiva (calibrado): {int((trimestre > 0).sum())} de {len(trimestre)}.", ""]
    texto = "\n".join(L)
    (RESULTADOS / "calibracion.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
