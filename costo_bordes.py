"""
Idea 5 · Control del costo en los bordes (apertura y cierre).

Aplica la regla fijada el 16 de noviembre de 2026, antes de medir (documento del
proyecto, "Control del costo en los bordes"). Las operaciones de la idea 5 pagan
el spread de horario normal; aquí se mide cuánto más (o menos) cuesta entrar en
la apertura y salir en el cierre, y se vuelve a costear.

Regla, fijada de antemano:
  1. Razón de cada muestra de borde: spread_bps de la muestra dividido por el
     spread de horario normal de su símbolo y trimestre, corregido por la
     volatilidad de su día. Ese denominador es recostear.costo_de aplicado a una
     fila con el symbol y el dia de la muestra (día de Nueva York), atras=0.
  2. Razón R de cada símbolo y franja: la mediana de esas razones (sin NaN).
  3. Costo corregido de cada operación = 0,5 x costo_época x R(símbolo, apertura)
     + 0,5 x costo_época x R(símbolo, cierre), con costo_época el costo_bps ya
     guardado. Vale para todas las entradas (10:00 a 12:30), aunque la apertura
     medida sea 10:00-10:35; el informe cuenta las que entran fuera de esa franja.
  4. Mismas operaciones: no cambia ninguna decisión.
  5. Un símbolo sin muestras de bordes (todavía) queda fuera del cálculo y se reporta.
  Decisión: "la salida a las 15:55 queda como horizonte de B" si la neta corregida
  es positiva y su t por bloques es de al menos 1,65; si no, "no pasa el control".
  No se elige otra hora mirando estos resultados.

La medición (muestrear_spread.py --bordes) puede estar incompleta: el script usa
los símbolos que haya y dice cuáles faltan; con faltantes el informe es provisional.
Muestra final: no se usa nada desde referencia.CORTE.

Uso:
    python costo_bordes.py
    python costo_bordes.py --probar     # solo las pruebas internas (razones 1 = costo guardado)

Salida:
    resultados/costo_bordes.md
"""

import argparse

import numpy as np
import pandas as pd

import horizonte_largo as hl
import recostear
import referencia
from referencia import CORTE, RESULTADOS, RAIZ, num

BORDES = RAIZ / "spread_bordes"
CARPETA_OPERACIONES = hl.mv.CARPETA
FRANJAS = ["apertura", "cierre"]
FIN_APERTURA = 65          # minuto de entrada (30 = 10:00) hasta el que cae dentro de 10:00-10:35
UMBRAL_T = 1.65


def cargar_muestras(carpeta=BORDES) -> pd.DataFrame:
    """Muestras de bordes de los símbolos ya medidos, con el día de Nueva York y antes de la muestra final."""
    archivos = sorted(carpeta.glob("*.parquet"))
    if not archivos:
        return pd.DataFrame(columns=["symbol", "momento", "franja", "spread_bps", "dia", "anio"])
    t = pd.concat([pd.read_parquet(a) for a in archivos], ignore_index=True)
    local = t["momento"].dt.tz_convert("America/New_York").dt.tz_localize(None)
    t["dia"], t["anio"] = local.dt.normalize(), local.dt.year
    return t[t["franja"].isin(FRANJAS) & (t["dia"] < CORTE)].reset_index(drop=True)


def razones(m: pd.DataFrame, tabla, rv, beta) -> pd.DataFrame:
    """Razón de cada muestra: spread medido / costo_de(symbol, dia, atras=0). NaN si no hay denominador válido."""
    m = m.copy()
    m["dia"] = m["dia"].astype(rv.index.dtype)
    base = np.full(len(m), np.nan)
    en_rv = m["dia"].isin(rv.index).to_numpy() & m["symbol"].isin(rv.columns).to_numpy()
    if en_rv.any():     # costo_de busca el día en rv; un día fuera de rv no debe tomar otra fila
        base[en_rv] = recostear.costo_de(m.loc[en_rv, ["symbol", "dia"]], tabla, rv, beta, 0)
    base = np.where(base > 0, base, np.nan)
    m["razon"] = m["spread_bps"].to_numpy(dtype="float64") / base
    m.loc[~np.isfinite(m["razon"]), "razon"] = np.nan
    return m


def razon_por_simbolo(m: pd.DataFrame) -> pd.DataFrame:
    """Mediana de las razones por símbolo y franja (sin NaN), con las muestras válidas. Columnas: R_<franja>, n_<franja>."""
    v = m.dropna(subset=["razon"])
    g = v.groupby(["symbol", "franja"])["razon"].agg(["median", "size"]).unstack("franja")
    out = pd.DataFrame(index=g.index)
    for f in FRANJAS:
        out[f"R_{f}"] = g["median"][f] if f in g["median"] else np.nan
        out[f"n_{f}"] = g["size"][f] if f in g["size"] else 0
    out[[f"n_{f}" for f in FRANJAS]] = out[[f"n_{f}" for f in FRANJAS]].fillna(0).astype(int)
    return out


def corregir(o: pd.DataFrame, R_apertura, R_cierre) -> pd.Series:
    """Costo corregido: 0,5 x costo_época x R(apertura) + 0,5 x costo_época x R(cierre). Las R son Series por símbolo."""
    ra, rc = o["symbol"].map(R_apertura), o["symbol"].map(R_cierre)
    return 0.5 * o["costo_bps"] * ra + 0.5 * o["costo_bps"] * rc


def probar(o, tabla, rv, beta) -> None:
    """Pruebas internas: con todas las razones 1 el costo corregido es el guardado; con muestras iguales al denominador, R = 1."""
    unos = pd.Series(1.0, index=o["symbol"].unique())
    assert np.allclose(corregir(o, unos, unos), o["costo_bps"]), "razones 1 no reproducen costo_bps"
    dos = pd.Series(2.0, index=unos.index)
    assert np.allclose(corregir(o, dos, unos), 1.5 * o["costo_bps"]), "R apertura 2 y cierre 1 debe dar 1,5 veces"
    x = o[["symbol", "dia"]].drop_duplicates().head(500).copy()
    x["spread_bps"] = recostear.costo_de(x, tabla, rv, beta, 0)
    x["franja"] = np.where(np.arange(len(x)) % 2 == 0, "apertura", "cierre")
    r = razon_por_simbolo(razones(x, tabla, rv, beta))
    assert np.allclose(r[["R_apertura", "R_cierre"]].to_numpy()[np.isfinite(r[["R_apertura", "R_cierre"]].to_numpy())], 1.0), "muestras iguales al costo de horario normal deben dar razón 1"
    print("Pruebas internas correctas: razones 1 -> costo guardado; muestras iguales al denominador -> razón 1.")


def informe(o, ops, R, m, faltan_ops, sin_muestras, dias) -> str:
    """Texto del informe. o: todas las operaciones; ops: las de símbolos con muestras (con costo corregido en `costo_corr`)."""
    provisional = len(sin_muestras) > 0
    ops_c = ops.assign(costo_bps=ops["costo_corr"])
    serie, serie_d = hl.serie_diaria(ops, dias), hl.serie_diaria(ops, dias, 2.0)
    serie_c, serie_cd = hl.serie_diaria(ops_c, dias), hl.serie_diaria(ops_c, dias, 2.0)
    neta, neta_c = ops["bruto_bps"] - ops["costo_bps"], ops["bruto_bps"] - ops["costo_corr"]
    t_c = hl.t_bloques(serie_c)
    pasa = neta_c.mean() > 0 and t_c >= UMBRAL_T
    v = m.dropna(subset=["razon"])

    n_sim = o["symbol"].nunique()
    L = ["# Control del costo en los bordes (idea 5)", ""]
    if provisional:
        L += [f"# PROVISIONAL: faltan {len(sin_muestras)} de {n_sim} símbolos operados sin muestras de bordes; la decisión no es válida hasta completar la medición.", ""]
    L += [f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `costo_bordes.py`. Aplica la regla fijada el 16 de noviembre de 2026, antes de medir "
          "(documento del proyecto, \"Control del costo en los bordes\"). Mismas operaciones de `horizonte_largo.py`; solo cambia lo que se paga: "
          "0,5 x costo de la época x R(apertura) + 0,5 x costo de la época x R(cierre), con R la mediana, por símbolo y franja, del spread medido "
          "dividido por el de horario normal de su trimestre corregido por la volatilidad de su día. Sin muestra final.", "",
          f"Símbolos operados por la idea 5 con muestras de bordes: {n_sim - len(sin_muestras)} de {n_sim}. "
          + ("Sin muestras todavía: " + ", ".join(sin_muestras) + "." if provisional else "Están todos."), ""]
    if faltan_ops:
        L += [f"Operaciones excluidas por no tener muestras de su símbolo: {num(faltan_ops['n'], 0)} de {num(len(o), 0)} "
              f"({', '.join(faltan_ops['simbolos'])}). Los resultados de abajo son sobre las {num(len(ops), 0)} operaciones restantes.", ""]
    fuera = int((ops["entrada"] > FIN_APERTURA).sum())
    L += [f"Entradas fuera de la franja de apertura medida (10:00-10:35): {num(fuera, 0)} de {num(len(ops), 0)} operaciones "
          f"({num(100 * fuera / max(len(ops), 1))}%); a ellas se les aplica igual la razón de la apertura (regla, punto 3).", ""]

    L += ["## Razón mediana por franja (todas las acciones medidas)", "",
          "| Franja | Muestras válidas | Razón mediana (todas las muestras) | Mediana de las razones por símbolo |", "| --- | --- | --- | --- |"]
    for f in FRANJAS:
        L.append(f"| {f} | {num((v['franja'] == f).sum(), 0)} | {num(v.loc[v['franja'] == f, 'razon'].median(), 3)} | {num(R[f'R_{f}'].median(), 3)} |")
    L += ["", f"Muestras sin razón (sin denominador o sin spread): {num(len(m) - len(v), 0)} de {num(len(m), 0)}.", "",
          "## Razón por símbolo", "", "| Símbolo | R apertura | Muestras apertura | R cierre | Muestras cierre |", "| --- | --- | --- | --- | --- |"]
    for s, r in R.iterrows():
        L.append(f"| {s} | {num(r['R_apertura'], 3)} | {num(r['n_apertura'], 0)} | {num(r['R_cierre'], 3)} | {num(r['n_cierre'], 0)} |")
    L += ["", "## Razón por año (mediana entre muestras)", "", "| Año | Apertura | Muestras | Cierre | Muestras |", "| --- | --- | --- | --- | --- |"]
    for a in sorted(v["anio"].unique()):
        x = v[v["anio"] == a]
        ap, ci = x[x["franja"] == "apertura"]["razon"], x[x["franja"] == "cierre"]["razon"]
        L.append(f"| {a} | {num(ap.median(), 3)} | {num(len(ap), 0)} | {num(ci.median(), 3)} | {num(len(ci), 0)} |")

    L += ["", "## Resultado de la idea 5", "",
          "Mismas operaciones en las dos filas (símbolos con muestras de bordes). t por bloques sobre la ganancia neta diaria "
          f"(días desde 2020 y antes de la muestra final, sin medios días; días sin operaciones valen 0; `horizonte_largo.t_bloques`).", "",
          "| Costo | Operaciones | Costo medio | Ganancia neta | t por bloques | Neta con costo doble | t por bloques (doble) |", "| --- | --- | --- | --- | --- | --- | --- |",
          f"| De la época (antes) | {num(len(ops), 0)} | {num(ops['costo_bps'].mean(), 2)} | {num(neta.mean(), 2)} | {num(hl.t_bloques(serie), 2)} | "
          f"{num((ops['bruto_bps'] - 2 * ops['costo_bps']).mean(), 2)} | {num(hl.t_bloques(serie_d), 2)} |",
          f"| Corregido por los bordes | {num(len(ops), 0)} | {num(ops['costo_corr'].mean(), 2)} | {num(neta_c.mean(), 2)} | {num(t_c, 2)} | "
          f"{num((ops['bruto_bps'] - 2 * ops['costo_corr']).mean(), 2)} | {num(hl.t_bloques(serie_cd), 2)} |", "",
          "### Por año", "",
          "| Año | Operaciones | Costo época | Neta época | Costo corregido | Neta corregida | t por bloques (corregida) | Neta corregida con costo doble |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a in sorted(ops["dia"].dt.year.unique()):
        x, d = ops[ops["dia"].dt.year == a], dias[dias.year == a]
        xc = x.assign(costo_bps=x["costo_corr"])
        L.append(f"| {a} | {num(len(x), 0)} | {num(x['costo_bps'].mean(), 2)} | {num((x['bruto_bps'] - x['costo_bps']).mean(), 2)} | {num(x['costo_corr'].mean(), 2)} | "
                 f"{num((x['bruto_bps'] - x['costo_corr']).mean(), 2)} | {num(hl.t_bloques(hl.serie_diaria(xc, d)), 2)} | "
                 f"{num((x['bruto_bps'] - 2 * x['costo_corr']).mean(), 2)} |")
    L += ["", "## Decisión (regla del documento)", "",
          f"Neta corregida {num(neta_c.mean(), 2)} bps, t por bloques {num(t_c, 2)} (se exige neta positiva y t de al menos {num(UMBRAL_T, 2)}, una cola, sin corregir).", ""]
    L += [("**La salida a las 15:55 queda como horizonte de B.**" if pasa else "**No pasa el control.** No se elige otra hora mirando estos resultados: "
           "salir antes (por ejemplo, a las 15:25) sería una variante nueva, la 12.ª, con su propia prueba.")]
    if provisional:
        L += ["", f"**PROVISIONAL: faltan {len(sin_muestras)} símbolos ({', '.join(sin_muestras)}); esta decisión se vuelve a calcular al completar la medición.**"]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Idea 5: control del costo en los bordes.")
    ap.add_argument("--probar", action="store_true", help="Solo las pruebas internas, sin escribir el informe")
    ap.add_argument("--operaciones", default="operaciones_cierre", help="Archivo en datos/modelos (por ejemplo operaciones_cierre_retraso20)")
    args = ap.parse_args()

    o = pd.read_parquet(CARPETA_OPERACIONES / f"{args.operaciones}.parquet")
    o = o[o["dia"] < CORTE].reset_index(drop=True)
    p = referencia.cargar_precios()
    rv = recostear.volatilidad_diaria()
    tabla, _, e = recostear.spreads_por_trimestre(rv)
    probar(o, tabla, rv, e["beta"])
    if args.probar:
        return

    m = razones(cargar_muestras(), tabla, rv, e["beta"])
    R = razon_por_simbolo(m)
    con = R.dropna(subset=["R_apertura", "R_cierre"]).index
    operados = sorted(o["symbol"].unique())
    sin_muestras = [s for s in operados if s not in con]
    print(f"Símbolos operados con muestras de bordes: {len(operados) - len(sin_muestras)} de {len(operados)}. Faltan: {', '.join(sin_muestras) if sin_muestras else 'ninguno'}")

    excluidas = ~o["symbol"].isin(con)
    faltan_ops = dict(n=int(excluidas.sum()), simbolos=sorted(o.loc[excluidas, "symbol"].unique())) if excluidas.any() else None
    ops = o[~excluidas].reset_index(drop=True)
    if ops.empty:
        print("Sin operaciones de símbolos con muestras: no hay nada que calcular todavía.")
        return
    ops["costo_corr"] = corregir(ops, R["R_apertura"], R["R_cierre"])
    assert np.isfinite(ops["costo_corr"]).all() and (ops["costo_corr"] > 0).all()

    dias = pd.DatetimeIndex(p["dias"])
    dias = dias[(dias.year >= hl.DESDE) & (dias < CORTE) & ~p["medio_dia"]]
    texto = informe(o, ops, R, m, faltan_ops, sin_muestras, dias)
    sufijo = args.operaciones.removeprefix("operaciones_cierre")
    if sufijo:
        texto = texto.replace("\n", f"\n\nOperaciones: `datos/modelos/{args.operaciones}.parquet`.\n", 1)
    (RESULTADOS / f"costo_bordes{sufijo}.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
