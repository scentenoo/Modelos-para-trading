"""
Costo de la época para las variantes del modelo de velas y para la referencia.

El costo oficial del proyecto es el spread de la época (recostear.py): la mediana del
spread de la acción en el trimestre, corregida por la volatilidad del día. Diez de las
once variantes de comparaciones.py y la referencia estaban guardadas con el costo de
hoy. Aquí se escriben versiones con el costo de la época, sin tocar los archivos
originales y sin reentrenar nada.

Regla:
  - Vuelven a decidir (recostear.decidir): logit, lgbm, lgbm2 y lgbm2c (lgbm2 calibrada
    con calibracion.calibrar, en las mismas acciones que calibracion.py). Se parte de
    predicciones_{h}.parquet; solo los momentos de la rejilla (minuto % h == 30 % h);
    entra si |predicción| > costo esperado (trimestre anterior y volatilidad del día
    anterior, atras=1) y paga el del trimestre en curso (atras=0).
  - Mismas operaciones, costo de la época (atras=0): las del filtro
    (operaciones_filtro_{h}.parquet) y las de la referencia.
  - Solo días anteriores a referencia.CORTE.

Uso:
    python recostear_variantes.py

Salida:
    datos/modelos/operaciones_epoca_{h}.parquet      (columna modelo: logit, lgbm, lgbm2, lgbm2c, filtro)
    datos/modelos/referencia/operaciones_epoca_{h}.parquet   (referencia.CARPETA)
    Resumen por horizonte y variante en pantalla: operaciones, costo medio y neta media,
    con el costo de hoy y con el de la época (desde 2020, como recostear.py).
"""

import numpy as np
import pandas as pd

import calibracion
import modelo_velas as mv
import recostear
import referencia
from descargar_datos import UNIVERSO
from referencia import CORTE, HORIZONTES


def decidir(pred: pd.DataFrame, columna: str, modelo: str, h: int, operables: set, costo) -> pd.DataFrame:
    """recostear.decidir, con las columnas de una tabla de operaciones."""
    d = recostear.decidir(pred, columna, h, operables, costo)
    x = pred[pred["symbol"].isin(operables) & (pred["minuto"] % h == 30 % h)]
    x = x[np.abs(x[columna].values) > costo(x, atras=1)]
    assert (x["symbol"].values == d["symbol"].values).all() and (x["dia"].values == d["dia"].values).all()
    d.insert(0, "modelo", modelo)
    d["entrada"] = x["minuto"].values
    d["direccion"] = np.sign(x[columna].values).astype("int8")
    d["esperado_bps"] = np.abs(x[columna].values)
    return cerrar(d.rename(columns={"costo_epoca": "costo_bps"}))


def cerrar(o: pd.DataFrame) -> pd.DataFrame:
    o = o.copy()
    o["neto_bps"] = o["bruto_bps"] - o["costo_bps"]
    return o.reset_index(drop=True)


def recostear_mismas(o: pd.DataFrame, costo) -> pd.DataFrame:
    """Mismas operaciones: el costo guardado pasa a costo_hoy_bps y se paga el de la época."""
    o = o[o["dia"] < CORTE].copy()
    o["costo_hoy_bps"] = o["costo_bps"]
    o["costo_bps"] = costo(o)
    return cerrar(o)


def resumen(nombre: str, h: int, nuevo: pd.DataFrame, viejo: pd.DataFrame | None) -> None:
    """Línea del resumen (desde 2020): operaciones, costo medio y neta media, con el costo de hoy y con el de la época."""
    n = nuevo[nuevo["dia"].dt.year >= recostear.DESDE]
    hoy = "—"
    if viejo is not None:
        v = viejo[(viejo["dia"].dt.year >= recostear.DESDE) & (viejo["dia"] < CORTE)]
        hoy = f"{len(v):>7,} ops, costo {v['costo_bps'].mean():6.2f}, neta {v['neto_bps'].mean():6.2f}"
    print(f"  {h} min · {nombre:<10} época: {len(n):>7,} ops, costo {n['costo_bps'].mean():6.2f}, neta {n['neto_bps'].mean():6.2f}   | hoy: {hoy}")


def main() -> None:
    rv = recostear.volatilidad_diaria()
    tabla, muestras, e = recostear.spreads_por_trimestre(rv)
    costo = lambda o, atras=0: recostear.costo_de(o, tabla, rv, e["beta"], atras)
    medidos = set(muestras["symbol"].unique())
    _, universo = referencia.costos_y_universo()
    print(f"Elasticidad spread/volatilidad: {e['beta']:.3f}; {len(medidos)} símbolos medidos\n")

    for h in HORIZONTES:
        operables = (set(np.array(UNIVERSO)[universo[h]]) & medidos) - {s for s in UNIVERSO if referencia.SECTOR[s] == "etf"}
        pred = pd.read_parquet(mv.CARPETA / f"predicciones_{h}.parquet")
        todas = set(np.array(UNIVERSO)[universo[h]]) & set(pred["symbol"].unique())
        pred["lgbm2c"], _ = calibracion.calibrar(pred, todas)
        pred = pred[pred["dia"] < CORTE]

        antes = pd.read_parquet(mv.CARPETA / f"operaciones_{h}.parquet")
        partes = []
        for m in ["logit", "lgbm", "lgbm2", "lgbm2c"]:
            o = decidir(pred, m, m, h, operables, costo)
            partes.append(o)
            if m == "lgbm2c":
                viejo = pd.read_parquet(mv.CARPETA / f"operaciones_calibradas_{h}.parquet")
            else:
                viejo = antes[antes["modelo"] == m]
            resumen(m, h, o, viejo)
        fil_viejo = pd.read_parquet(mv.CARPETA / f"operaciones_filtro_{h}.parquet")
        fil = recostear_mismas(fil_viejo, costo).assign(modelo="filtro")
        partes.append(fil)
        resumen("filtro", h, fil, fil_viejo)
        pd.concat(partes, ignore_index=True).to_parquet(mv.CARPETA / f"operaciones_epoca_{h}.parquet", index=False)

        ref_viejo = pd.read_parquet(referencia.CARPETA / f"operaciones_{h}.parquet")
        ref = recostear_mismas(ref_viejo, costo)
        ref.to_parquet(referencia.CARPETA / f"operaciones_epoca_{h}.parquet", index=False)
        resumen("referencia", h, ref, ref_viejo)
        print()


if __name__ == "__main__":
    main()
