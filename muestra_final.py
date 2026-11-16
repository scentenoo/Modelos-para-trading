"""
Paso 3.2 · Muestra final: evalúa el modelo de velas (B) una sola vez, con el protocolo fijado.

Protocolo, fijado el 16 de noviembre de 2026 antes de abrirla (documento del proyecto,
sección 5, "Cómo se evalúa B en la muestra final", y criterios de la Fase 2):
  - Modelo: el que dejó modelo_final.py en datos/modelos/final/ (entrenado con 2016-2024,
    pendiente fija). Nada se reentrena ni se ajusta.
  - Filas: las de datos/variables del periodo, con la lógica de modelo_velas.cargar() (sin ETF,
    sin medios días, puestos p_* y s_* por momento, sector_n con la codificación guardada),
    solo los momentos de 10:00 a 12:30 cada 30 minutos.
  - Operación: la de horizonte_largo.py --retraso 20 (variante 12): decide en el momento,
    entra 20 minutos después, sale a las 15:55; una operación por acción y día; solo las
    acciones operables guardadas (36).
  - Periodo: del 2 de enero de 2025 al último día completo disponible, sin medios días.
  - Costo: el de la época. Las medianas trimestrales de 2016-2024 salen de datos/spread_historico
    y las de 2025-2026 de datos/spread_reciente; la elasticidad a la volatilidad se toma SOLO de
    2016-2024. Decide con el trimestre y el día anteriores (atras=1) y paga el del trimestre en
    curso (atras=0). Todo resultado se repite con el costo doble.
  - Referencia (criterio 2): la de 60 minutos, con las operaciones de sus reglas fijas y el costo
    de la época. Diferencia B - A sobre la ganancia neta diaria por acción operable (suma por día
    entre las acciones operables a 60 minutos, como comparaciones.series_diarias; los días sin
    operaciones valen 0), con el t por bloques de comparaciones.py (semilla 7). Pasa con t >= 1,65.

Criterios de la Fase 2 (B pasa solo si cumple los cinco):
  1. Ganancia neta por operación de al menos 1 bps.
  2. Ganancia neta diaria mayor que la de la referencia, con t por bloques >= 1,65.
  3. Ganancia neta por operación no negativa con el costo doble.
  4. Al menos 2.000 operaciones.
  5. Ganancia neta positiva en al menos la mitad de los trimestres.

Información adicional (no decide): neta y t contra cero, por trimestre, selección y mercado, por
momento de entrada, y el costo corregido por los bordes (razones de costo_bordes.py con
datos/spread_bordes, que son de 2016-2024).

Se usa una sola vez. Sin argumentos el script se niega a correr.

Uso:
    python muestra_final.py --abrir                  # ABRE la muestra final (2025 en adelante); una sola vez
    python muestra_final.py --abrir --hasta 2026-10-30
    python muestra_final.py --ensayo 2024            # prueba del código sobre un año anterior; NO es un resultado

Salida (con --abrir):
    resultados/muestra_final.md
    datos/modelos/operaciones_muestra_final.parquet
Con --ensayo, los mismos archivos en la carpeta temporal (muestra_final_ensayo), nunca en resultados/.
"""

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

import comparaciones
import costo_bordes
import horizonte_largo as hl
import modelo_velas as mv
import recostear
import referencia
from descargar_datos import UNIVERSO
from referencia import CORTE, RESULTADOS, SALIDA_MAXIMA, num, resumen

CARPETA_MODELO = mv.CARPETA / "final"
RECIENTE = recostear.RAIZ / "spread_reciente"
HORIZONTE_REFERENCIA = 60
UMBRALES = dict(neta=1.0, t=1.65, operaciones=2000, trimestres=0.5)
AVISO_ENSAYO = ("#" * 78 + "\n"
                "#  ENSAYO: ESTO NO ES LA MUESTRA FINAL. Corre sobre {anio}, un año que el modelo final\n"
                "#  YA VIO al entrenar (2016-2024). Sus números no significan nada: solo prueban el código.\n"
                + "#" * 78)


# ---------------------------------------------------------------- datos

def cargar_modelo() -> tuple[lgb.Booster, dict]:
    meta = json.loads((CARPETA_MODELO / "modelo_b.json").read_text(encoding="utf-8"))
    return lgb.Booster(model_file=str(CARPETA_MODELO / "modelo_b.txt")), meta


def filas(desde: pd.Timestamp, fin: pd.Timestamp, meta: dict, medios_dias: pd.DatetimeIndex) -> pd.DataFrame:
    """Las filas de modelo_velas.cargar() para el periodo [desde, fin], solo los momentos guardados.

    Misma lógica que cargar() (sin ETF ni medios días; puestos p_* y s_* por momento), pero con la
    codificación de sector_n del entrenamiento y sin su corte en CORTE. No cambia cargar().
    """
    archivos = [a for a in sorted(mv.VARIABLES.glob("*.parquet")) if desde.year <= int(a.stem) <= fin.year]
    t = pd.concat([pd.read_parquet(a) for a in archivos], ignore_index=True)
    t = t[~t["es_etf"] & (t["dia"] >= desde) & (t["dia"] <= fin) & ~t["dia"].isin(medios_dias)].reset_index(drop=True)
    codigo = {sector: int(c) for c, sector in meta["sector_n"].items()}
    t["sector_n"] = t["sector"].map(codigo)
    if t["sector_n"].isna().any():
        raise ValueError(f"sectores sin codificación guardada: {sorted(t.loc[t['sector_n'].isna(), 'sector'].unique())}")
    t["sector_n"] = t["sector_n"].astype("int8")
    puestos = t.groupby("momento")[mv.CON_PUESTO].rank(pct=True).astype("float32")
    t[[f"p_{c}" for c in mv.CON_PUESTO]] = puestos.values
    del_sector = t.groupby(["momento", "sector_n"])[mv.CON_SECTOR].transform("mean")
    t[[f"s_{c}" for c in mv.CON_SECTOR]] = (t[mv.CON_SECTOR] - del_sector).values
    faltan = [c for c in meta["columnas"] if c not in t.columns]
    if faltan:
        raise ValueError(f"faltan variables del modelo en datos/variables: {faltan}")
    return t[t["minuto"].isin(meta["momentos"])].reset_index(drop=True)


def predicciones(t: pd.DataFrame, p: dict, modelo: lgb.Booster, meta: dict) -> pd.DataFrame:
    """Predicción calibrada (bps) y retorno real hasta las 15:55 de cada fila, como horizonte_largo.py --retraso 20."""
    retraso = meta["retraso_min"]
    t = t.copy()
    t["obj_cierre"] = hl.retorno(t, p, meta["salida_min"], t["minuto"].to_numpy() + retraso)
    t["rel_cierre"] = hl.relativo(t, t["obj_cierre"].to_numpy())
    t = t[np.isfinite(t["obj_cierre"]) & np.isfinite(t["rel_cierre"])].reset_index(drop=True)
    pred = t[["symbol", "momento", "dia", "minuto"]].copy()
    pred["obj_bps"], pred["rel_bps"] = t["obj_cierre"].to_numpy() * 1e4, t["rel_cierre"].to_numpy() * 1e4
    pred[hl.MODELO] = modelo.predict(t[meta["columnas"]]) * meta["pendiente"]
    return pred


def tabla_de_costos(rv: pd.DataFrame) -> tuple[pd.DataFrame, float, pd.DataFrame]:
    """Spread por símbolo y trimestre: la histórica (2016-2024) más la reciente (2025-2026). Elasticidad solo de la histórica."""
    historica, muestras, e = recostear.spreads_por_trimestre(rv)
    reciente, _, _ = recostear.spreads_por_trimestre(rv, RECIENTE)
    reciente = reciente[reciente.index.get_level_values("trimestre") >= pd.Period("2025Q1")]      # las muestras de 2024 ya están en la histórica
    return pd.concat([historica, reciente]), e["beta"], reciente


# ---------------------------------------------------------------- referencia

def referencia_epoca(p: dict, desde: pd.Timestamp, fin: pd.Timestamp, universo: np.ndarray, costo) -> pd.DataFrame:
    """Operaciones de la referencia de 60 minutos en el periodo, con el costo de la época (mismas operaciones, atras=0)."""
    nd = int(np.searchsorted(pd.DatetimeIndex(p["dias"]).values, (fin + pd.Timedelta(days=1)).to_datetime64(), side="left"))
    recortado = {k: (v[:, :nd] if k in ("C", "alto", "bajo") else v[:nd]) for k, v in p.items()}   # nada posterior al periodo entra al cálculo
    costo_hoy, _ = referencia.costos_y_universo()
    o = referencia.operaciones(recortado, HORIZONTE_REFERENCIA, costo_hoy, universo, fin + pd.Timedelta(days=1))
    o = o[o["dia"] >= desde].copy()
    o["costo_hoy_bps"] = o["costo_bps"]
    o["costo_bps"] = costo(o)
    o["neto_bps"] = o["bruto_bps"] - o["costo_bps"]
    return o.reset_index(drop=True)


# ---------------------------------------------------------------- informe

def por_dia(o: pd.DataFrame, dias: pd.DatetimeIndex, n: int) -> pd.Series:
    """Ganancia neta diaria por acción operable: suma por día entre n acciones; sin operaciones vale 0."""
    return (o.groupby("dia")["neto_bps"].sum() / n).reindex(dias, fill_value=0.0)


def criterios(o: pd.DataFrame, dias: pd.DatetimeIndex, a: pd.DataFrame, n_ref: int) -> tuple[list, dict]:
    """Los cinco criterios: (nombre, valor en texto, pasa). Y los números detrás."""
    neta = o["neto_bps"].mean()
    doble = (o["bruto_bps"] - 2 * o["costo_bps"]).mean()
    serie_b, serie_a = por_dia(o, dias, n_ref), por_dia(a, dias, n_ref)
    dif = serie_b - serie_a
    t_dif = hl.t_bloques(dif)
    trimestres = dias.to_period("Q")
    por_trimestre = o.groupby(o["dia"].dt.to_period("Q"))["neto_bps"].sum().reindex(trimestres.unique(), fill_value=0.0)
    positivos = int((por_trimestre > 0).sum())
    lista = [
        ("1. Ganancia neta por operación de al menos 1 bps", f"{num(neta, 2)} bps", bool(neta >= UMBRALES["neta"])),
        ("2. Mayor que la referencia (A) con t por bloques de al menos 1,65",
         f"B {num(serie_b.mean(), 3)} contra A {num(serie_a.mean(), 3)} bps por acción operable y día; diferencia {num(dif.mean(), 3)}, t {num(t_dif, 2)}",
         bool(dif.mean() > 0 and t_dif >= UMBRALES["t"])),
        ("3. Neta no negativa con el costo doble", f"{num(doble, 2)} bps", bool(doble >= 0)),
        ("4. Al menos 2.000 operaciones", f"{num(len(o), 0)} operaciones", bool(len(o) >= UMBRALES["operaciones"])),
        ("5. Neta positiva en al menos la mitad de los trimestres", f"{positivos} de {len(por_trimestre)} trimestres",
         bool(positivos >= UMBRALES["trimestres"] * len(por_trimestre))),
    ]
    return lista, dict(serie_b=serie_b, serie_a=serie_a, t_dif=t_dif, por_trimestre=por_trimestre)


def bordes(o: pd.DataFrame, dias: pd.DatetimeIndex, tabla, rv, beta) -> list[str]:
    """Costo corregido por los bordes (costo_bordes.py, con las razones de 2016-2024 de datos/spread_bordes). Solo informa."""
    m = costo_bordes.razones(costo_bordes.cargar_muestras(), tabla, rv, beta)
    R = costo_bordes.razon_por_simbolo(m)
    con = R.dropna(subset=["R_apertura", "R_cierre"]).index
    excluidas = ~o["symbol"].isin(con)
    ops = o[~excluidas].copy()
    if ops.empty:
        return ["Sin operaciones de símbolos con muestras de bordes."]
    ops["costo_corr"] = costo_bordes.corregir(ops, R["R_apertura"], R["R_cierre"])
    corr = ops.assign(costo_bps=ops["costo_corr"])
    neta_c = ops["bruto_bps"] - ops["costo_corr"]
    serie_c, serie_cd = hl.serie_diaria(corr, dias), hl.serie_diaria(corr, dias, 2.0)
    L = [f"Razones medianas de apertura y cierre por símbolo, de las muestras de 2016-2024 (`datos/spread_bordes`); mismas operaciones, solo cambia lo que se paga: "
         f"0,5 x costo x R(apertura) + 0,5 x costo x R(cierre). Símbolos operados con razones: {o['symbol'].nunique() - o.loc[excluidas, 'symbol'].nunique()} de {o['symbol'].nunique()}."
         + (f" Operaciones excluidas por no tener razones de su símbolo: {int(excluidas.sum())}." if excluidas.any() else ""), "",
         "| Costo | Operaciones | Costo medio | Ganancia neta | t por bloques | Neta con costo doble | t por bloques (doble) |", "| --- | --- | --- | --- | --- | --- | --- |",
         f"| De la época | {num(len(ops), 0)} | {num(ops['costo_bps'].mean(), 2)} | {num((ops['bruto_bps'] - ops['costo_bps']).mean(), 2)} | "
         f"{num(hl.t_bloques(hl.serie_diaria(ops, dias)), 2)} | {num((ops['bruto_bps'] - 2 * ops['costo_bps']).mean(), 2)} | "
         f"{num(hl.t_bloques(hl.serie_diaria(ops, dias, 2.0)), 2)} |",
         f"| Corregido por los bordes | {num(len(ops), 0)} | {num(ops['costo_corr'].mean(), 2)} | {num(neta_c.mean(), 2)} | {num(hl.t_bloques(serie_c), 2)} | "
         f"{num((ops['bruto_bps'] - 2 * ops['costo_corr']).mean(), 2)} | {num(hl.t_bloques(serie_cd), 2)} |", "",
         f"Regla del control de bordes: neta corregida positiva y t por bloques de al menos {num(costo_bordes.UMBRAL_T, 2)}. Aquí es solo información."]
    return L


def informe(o, a, dias, lista, extra, meta, n_ref, tabla, rv, beta, ensayo, desde, fin, tiempo) -> str:
    s, doble = resumen(o), resumen(o, 2.0)
    serie = hl.serie_diaria(o, dias)
    serie_doble = hl.serie_diaria(o, dias, 2.0)
    pasa = all(c[2] for c in lista)
    por_trimestre = extra["por_trimestre"]
    L = []
    if ensayo:
        L += [AVISO_ENSAYO.format(anio=ensayo), ""]
    L += [f"# Muestra final: evaluación de B{' (ENSAYO ' + str(ensayo) + ', sin valor)' if ensayo else ''}", ""]
    if ensayo:
        L += [f"**ENSAYO sobre {ensayo}: el modelo final se entrenó con 2016-2024, así que {ensayo} es parte de su entrenamiento. "
              "Estos números no significan nada; solo prueban que el código corre de principio a fin.**", ""]
    L += [f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `muestra_final.py`. Protocolo fijado el 16 de noviembre de 2026 antes de abrirla (documento del proyecto, sección 5). "
          f"Periodo: {desde:%Y-%m-%d} a {fin:%Y-%m-%d}, {len(dias)} días de mercado sin medios días. Modelo: `datos/modelos/final/` (entrenado {meta['entrenado']} con {meta['datos']}, "
          f"pendiente {num(meta['pendiente'], 3)}), sin reentrenar. Variante 12: decisiones de 10:00 a 12:30 cada 30 minutos, entrada {meta['retraso_min']} minutos después, "
          f"salida a las 15:55, una operación por acción y día, {len(meta['operables'])} acciones operables. "
          f"Costo: el de la época (spread del trimestre corregido por la volatilidad del día; decide con el trimestre y el día anteriores y paga el del trimestre en curso); "
          f"elasticidad {num(beta, 3)} tomada solo de 2016-2024.", "",
          "Unidades: bps por operación (1 bps = 0,01%).", "",
          "## Conclusión", "",
          f"**{'B PASA' if pasa else 'B NO PASA'} la Fase 2** ({sum(c[2] for c in lista)} de 5 criterios)."
          + ("" if pasa else " No se sigue a la Fase 3 con este modelo."), "",
          "| Criterio | Valor | Resultado |", "| --- | --- | --- |"]
    L += [f"| {nombre} | {valor} | {'pasa' if ok else 'no pasa'} |" for nombre, valor, ok in lista]
    L += ["", "## Resultado de B", "",
          "| Operaciones | Días con operaciones | Acierto | Ganancia bruta | Costo | Ganancia neta | Neta con costo doble |", "| --- | --- | --- | --- | --- | --- | --- |",
          f"| {num(s['n'], 0)} | {num(s['dias'], 0)} de {len(dias)} | {num(100 * s['acierto'])}% | {num(s['bruto'], 2)} | {num(s['costo'], 2)} | {num(s['neto'], 2)} | {num(doble['neto'], 2)} |", "",
          "## Referencia (A) de 60 minutos con el costo de la época", "",
          "Mismas operaciones de las reglas fijas de `referencia.py` con 60 minutos; costo de la época (atras=0). Ganancia neta diaria en bps por acción operable "
          f"(suma por día entre {n_ref} acciones operables a 60 minutos; días sin operaciones valen 0). t por bloques de la diferencia B - A con el remuestreo de `comparaciones.py` "
          f"(bloques de {comparaciones.BLOQUE} días, {num(comparaciones.REMUESTREOS, 0)} remuestreos, semilla {comparaciones.SEMILLA}); una cola, 5%: t >= 1,65.", "",
          "| | Operaciones | Neta por operación | Neta diaria por acción operable |", "| --- | --- | --- | --- |",
          f"| A · referencia 60 min | {num(len(a), 0)} | {num(a['neto_bps'].mean(), 2)} | {num(extra['serie_a'].mean(), 3)} |",
          f"| B | {num(len(o), 0)} | {num(o['neto_bps'].mean(), 2)} | {num(extra['serie_b'].mean(), 3)} |",
          f"| B - A | | | {num((extra['serie_b'] - extra['serie_a']).mean(), 3)} (t por bloques {num(extra['t_dif'], 2)}) |", "",
          "## Información adicional (no decide)", "",
          "### Contra cero", "",
          f"Neta {num(s['neto'], 2)} bps por operación; t por bloques {num(hl.t_bloques(serie), 2)} (ganancia neta diaria, suma por día, días sin operaciones valen 0; t por días {num(s['t'], 2)}). "
          f"Con costo doble: neta {num(doble['neto'], 2)}, t por bloques {num(hl.t_bloques(serie_doble), 2)}.", "",
          "### Por trimestre", "",
          "| Trimestre | Operaciones | Costo medio | Neta por operación | Ganancia neta total (bps) | Neta con costo doble |", "| --- | --- | --- | --- | --- | --- |"]
    for q in por_trimestre.index:
        x = o[o["dia"].dt.to_period("Q") == q]
        L.append(f"| {q} | {num(len(x), 0)} | {num(x['costo_bps'].mean(), 2)} | {num(x['neto_bps'].mean(), 2)} | {num(por_trimestre[q], 0)} | {num((x['bruto_bps'] - 2 * x['costo_bps']).mean(), 2)} |")
    L += ["", "### Selección y mercado", "", "Ganancia bruta = selección (dirección por el retorno relativo) + mercado (el resto).", "",
          "| Parte | Media por operación | t por días |", "| --- | --- | --- |"]
    for nombre, c in (("Selección", "seleccion_bps"), ("Mercado", "mercado_bps")):
        L.append(f"| {nombre} | {num(o[c].mean(), 2)} | {num(hl.t_dias(o[c], o['dia']), 2)} |")
    L += ["", "### Por momento de entrada", "", "| Entrada | Operaciones | Neta por operación |", "| --- | --- | --- |"]
    for m in meta["momentos"]:
        x = o[o["entrada"] == m + meta["retraso_min"]]
        h = 570 + m + meta["retraso_min"]
        L.append(f"| {h // 60}:{h % 60:02d} | {num(len(x), 0)} | {num(x['neto_bps'].mean(), 2)} |")
    L += ["", "### Costo corregido por los bordes", "", *bordes(o, dias, tabla, rv, beta), "",
          f"Tiempo de la corrida: {tiempo / 60:.1f} minutos.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- principal

def ultimo_dia_completo(p: dict) -> pd.Timestamp:
    """Último día de los precios con cierre a las 15:55 en al menos la mitad de los símbolos."""
    completo = np.isfinite(p["C"][:, :, SALIDA_MAXIMA]).mean(axis=0) >= 0.5
    return pd.DatetimeIndex(p["dias"])[np.nonzero(completo)[0][-1]]


def main() -> None:
    ap = argparse.ArgumentParser(description="Muestra final: evaluación única de B con el protocolo fijado.")
    ap.add_argument("--abrir", action="store_true", help="ABRE la muestra final (2025 en adelante). Se usa una sola vez")
    ap.add_argument("--ensayo", type=int, metavar="AAAA", help="Prueba el código sobre un año anterior a 2025; sus números no valen")
    ap.add_argument("--hasta", type=pd.Timestamp, metavar="AAAA-MM-DD", help="Último día del periodo")
    args = ap.parse_args()
    if args.abrir == (args.ensayo is not None):
        sys.exit("muestra_final.py se niega a correr sin una orden explícita.\n"
                 "  --abrir        evalúa B en la muestra final (2025-01-01 en adelante). Se usa UNA sola vez: lo que salga se reporta tal cual.\n"
                 "  --ensayo AAAA  prueba el código sobre un año anterior (por ejemplo 2024); escribe en la carpeta temporal.\n"
                 "Se elige uno de los dos (no ambos): así ningún dato de 2025 en adelante se calcula por accidente.")
    ensayo = args.ensayo
    if ensayo is not None:
        if not 2017 <= ensayo < CORTE.year:
            sys.exit(f"--ensayo pide un año entre 2017 y {CORTE.year - 1}, anterior a la muestra final.")
        desde, tope = pd.Timestamp(ensayo, 1, 1), pd.Timestamp(ensayo, 12, 31)
        if args.hasta is not None and not desde <= args.hasta <= tope:
            sys.exit(f"--hasta debe caer dentro de {ensayo} en un ensayo.")
        print(AVISO_ENSAYO.format(anio=ensayo))
    else:
        desde, tope = CORTE, None
        print("ABRIENDO LA MUESTRA FINAL (desde 2025-01-01). Se usa una sola vez.")
    inicio = time.time()

    p = referencia.cargar_precios()
    if ensayo is None:
        ultimo_variables = max(pd.read_parquet(a, columns=["dia"])["dia"].max() for a in sorted(mv.VARIABLES.glob("*.parquet"))[-1:])
        if pd.Timestamp(p["dias"].max()) < ultimo_variables:
            print(f"cierres.npz llega a {pd.Timestamp(p['dias'].max()):%Y-%m-%d} y las variables a {ultimo_variables:%Y-%m-%d}: se reconstruye con rehacer=True")
            p = referencia.cargar_precios(rehacer=True)
    fin = min(args.hasta, tope) if tope is not None and args.hasta is not None else (tope if tope is not None else (args.hasta or ultimo_dia_completo(p)))
    if pd.Timestamp(p["dias"].max()) < fin:
        sys.exit(f"cierres.npz solo llega a {pd.Timestamp(p['dias'].max()):%Y-%m-%d}; falta bajar velas (actualizar.py) y volver a correr.")
    dias = pd.DatetimeIndex(p["dias"])
    medios = dias[p["medio_dia"]]
    dias = dias[(dias >= desde) & (dias <= fin) & ~p["medio_dia"]]
    print(f"Periodo {desde:%Y-%m-%d} a {fin:%Y-%m-%d}: {len(dias)} días de mercado")

    modelo, meta = cargar_modelo()
    t = filas(desde, fin, meta, medios)
    if t["dia"].max() < dias.max():
        sys.exit(f"datos/variables solo llega a {t['dia'].max():%Y-%m-%d} y el periodo a {dias.max():%Y-%m-%d}: falta regenerar variables.py.")
    pred = predicciones(t, p, modelo, meta)
    print(f"{len(pred):,} filas con precio de salida de {pred['dia'].nunique()} días")

    rv = recostear.volatilidad_diaria()
    tabla, beta, reciente = tabla_de_costos(rv)
    costo = lambda x, atras=0: recostear.costo_de(x, tabla, rv, beta, atras)
    operables = set(meta["operables"])
    o = hl.operar(pred, hl.MODELO, operables, costo, meta["retraso_min"])
    o = o[o["dia"] >= desde].reset_index(drop=True)
    if o["costo_bps"].isna().any():
        sys.exit(f"{int(o['costo_bps'].isna().sum())} operaciones sin costo de la época (símbolo o trimestre ausente en la tabla de spreads).")
    print(f"{len(o):,} operaciones de B, costo medio {o['costo_bps'].mean():.2f} bps")

    _, universo = referencia.costos_y_universo()
    n_ref = int(universo[HORIZONTE_REFERENCIA].sum())
    a = referencia_epoca(p, desde, fin, universo[HORIZONTE_REFERENCIA], costo)
    sin_costo = a["costo_bps"].isna()
    if sin_costo.any():
        print(f"AVISO: {int(sin_costo.sum())} operaciones de la referencia sin costo de la época (símbolos sin muestras de spread: "
              f"{sorted(a.loc[sin_costo, 'symbol'].unique())}); quedan fuera.")
        a = a[~sin_costo].reset_index(drop=True)
    print(f"{len(a):,} operaciones de la referencia de {HORIZONTE_REFERENCIA} minutos, costo medio {a['costo_bps'].mean():.2f} bps")

    lista, extra = criterios(o, dias, a, n_ref)
    texto = informe(o, a, dias, lista, extra, meta, n_ref, tabla, rv, beta, ensayo, desde, fin, time.time() - inicio)
    if sin_costo.any():
        texto += f"\nNota: {int(sin_costo.sum())} operaciones de la referencia no tenían spread de su símbolo y trimestre y se dejaron fuera.\n"

    if ensayo is not None:
        carpeta_datos = carpeta_informe = Path(tempfile.gettempdir()) / "muestra_final_ensayo"
    else:
        carpeta_datos, carpeta_informe = mv.CARPETA, RESULTADOS
    carpeta_datos.mkdir(parents=True, exist_ok=True)
    carpeta_informe.mkdir(parents=True, exist_ok=True)
    o.to_parquet(carpeta_datos / "operaciones_muestra_final.parquet", index=False)
    (carpeta_informe / "muestra_final.md").write_text(texto, encoding="utf-8")
    print(f"Escrito en {carpeta_informe}")
    print(texto)
    if ensayo is not None:
        print(AVISO_ENSAYO.format(anio=ensayo))


if __name__ == "__main__":
    main()
