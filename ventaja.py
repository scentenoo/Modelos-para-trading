"""
Paso 2.8 · Revisión de la ganancia: ¿de dónde sale lo que gana un competidor?

Dos preguntas sobre un archivo de operaciones ya guardado:
  1. ¿Es ventaja propia o exposición al mercado? Se arma la ganancia neta de
     cada día y se compara con bases fijadas de antemano, usando la habilidad
     residual-edge-analyzer (regresión con errores HAC y ventanas móviles):
       - principal: retorno diario de SPY;
       - alterna 1: promedio simple de las 50 acciones;
       - alterna 2: SPY más la referencia (competidor A), neta de costos.
  2. ¿Está concentrada? Cuánto aportan los mejores días, el mejor año, las
     compras frente a las ventas y cada acción.

Es descriptivo: no entrena nada y no cuenta como variante.

Capital: una unidad por acción operable; cada operación usa la unidad de su
acción durante el horizonte. Solo cambia la escala del retorno anual, no los t.

Muestra final: las operaciones guardadas no la incluyen.

Uso:
    python ventaja.py                                  # la versión calibrada
    python ventaja.py --operaciones operaciones_filtro

Salida:
    resultados/ventaja.md
    datos/ventaja/   serie diaria, configuración e informe completo del analizador, por horizonte
"""

import argparse
import json
import subprocess
import sys

import numpy as np
import pandas as pd

import referencia
from descargar_datos import RAIZ, SECTOR, UNIVERSO
from referencia import HORIZONTES, RESULTADOS, num

CARPETA = RAIZ / "ventaja"
ANALIZADOR = RAIZ.parent / ".claude" / "skills" / "residual-edge-analyzer" / "scripts" / "analyze_residual_edge.py"
MEJORES_DIAS = 10
MODELOS = {"mercado": "SPY", "promedio_de_las_50": "Promedio de las 50 acciones", "mercado_y_referencia": "SPY y la referencia"}
VEREDICTOS = {"RESIDUAL_EDGE": "ventaja propia", "BASELINE_EXPLAINED": "explicada por la base", "RESIDUAL_FRAGILE": "ventaja frágil",
              "INSUFFICIENT_EVIDENCE": "evidencia insuficiente"}


def serie_diaria(o: pd.DataFrame, h: int, n_operables: int) -> pd.DataFrame:
    """Ganancia neta diaria del competidor y de las bases, en los mismos días."""
    p = referencia.cargar_precios()
    dias = pd.DatetimeIndex(p["dias"])
    cierre = pd.DataFrame(p["C"][:, :, -1].T.astype("float64"), index=dias, columns=UNIVERSO)
    ret = cierre.pct_change()
    acciones = [s for s in UNIVERSO if SECTOR[s] != "etf"]
    periodo = dias[(dias >= o["dia"].min()) & (dias <= o["dia"].max()) & ~p["medio_dia"]]
    a = pd.read_parquet(referencia.CARPETA / f"operaciones_{h}.parquet")
    reg = pd.read_parquet(RAIZ / "segmentos" / "regimenes.parquet")
    reg = reg[reg["anio_prueba"] == reg["dia"].dt.year].set_index("dia")["regimen"]     # cada día, con la ventana de su año

    t = pd.DataFrame(index=periodo)
    t["strategy_return"] = (o.groupby("dia")["neto_bps"].sum() / n_operables / 1e4).reindex(periodo, fill_value=0.0)
    t["market_return"] = ret["SPY"].reindex(periodo)
    t["equal_weight_return"] = ret[acciones].mean(axis=1).reindex(periodo)
    t["reference_return"] = (a.groupby("dia")["neto_bps"].sum() / n_operables / 1e4).reindex(periodo, fill_value=0.0)
    t["regimen"] = "regimen_" + reg.reindex(periodo).astype("Int64").astype(str)
    return t.dropna()


def analizar(t: pd.DataFrame, h: int) -> dict:
    """Corre residual-edge-analyzer y devuelve su informe."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    csv, config, salida = CARPETA / f"serie_{h}.csv", CARPETA / f"config_{h}.json", CARPETA / f"informe_{h}.json"
    t.set_axis(t.index.strftime("%Y-%m-%d")).rename_axis("date").to_csv(csv)
    config.write_text(json.dumps({
        "schema_version": "1.0", "date_column": "date", "strategy_column": "strategy_return", "return_unit": "decimal", "frequency": "daily",
        "primary_model": {"name": "mercado", "baseline_columns": ["market_return"]},
        "sensitivity_models": [{"name": "promedio_de_las_50", "baseline_columns": ["equal_weight_return"]},
                               {"name": "mercado_y_referencia", "baseline_columns": ["market_return", "reference_return"]}],
        "regime_columns": ["regimen"], "rolling_window": 63, "minimum_observations": 60, "minimum_regime_observations": 20,
        "minimum_rolling_windows": 12, "hac_lags": "auto", "include_series": False,
        "data_declarations": {"baseline_selection": "predeclared", "strategy_return_basis": "net", "baseline_return_basis": "net",
                              "analysis_scope": "out_of_sample", "universe_data": "current_constituents"},
    }, indent=2), encoding="utf-8")
    subprocess.run([sys.executable, str(ANALIZADOR), "--input", str(csv), "--config", str(config), "--output-json", str(salida),
                    "--output-markdown", str(salida.with_suffix(".md"))], check=True, capture_output=True)
    return json.loads(salida.read_text(encoding="utf-8"))


def _linea(nombre: str, o: pd.DataFrame) -> str:
    por_dia = o.groupby("dia")["neto_bps"].sum()
    t = por_dia.mean() / (por_dia.std(ddof=1) / np.sqrt(len(por_dia)))
    return f"| {nombre} | {num(len(o), 0)} | {num(o['neto_bps'].mean(), 2)} | {num(t, 2)} | {num((o['bruto_bps'] - 2 * o['costo_bps']).mean(), 2)} |"


def seccion(h: int, o: pd.DataFrame, t: pd.DataFrame, j: dict) -> list[str]:
    L = [f"## Horizonte de {h} minutos ({t.index.min():%Y-%m-%d} a {t.index.max():%Y-%m-%d}, {len(t)} días)", "",
         f"**Veredicto del analizador: {VEREDICTOS[j['verdict']['status']]}.**", "",
         "### ¿Ventaja propia o exposición al mercado?", "",
         "| Base de comparación | Variación explicada (R²) | Ganancia anual sin la base | t | Ventanas de 63 días con ganancia positiva |", "| --- | --- | --- | --- | --- |"]
    for m in j["models"]:
        movil = m["rolling"]
        positivas = f"{num(100 * movil['positive_alpha_fraction'], 0)}%" if movil.get("enabled") else "—"
        L.append(f"| {MODELOS[m['name']]} | {num(100 * m['r_squared'])}% | {num(100 * m['alpha']['annualized_arithmetic'], 2)}% | {num(m['alpha']['t_stat'], 2)} | {positivas} |")
    beta = next(c for c in j["models"][0]["coefficients"] if c["name"] == "market_return")
    L += ["", f"Beta frente a SPY: {num(beta['estimate'], 3)} (t {num(beta['t_stat'], 2)}). El analizador pide al menos 60% de ventanas positivas para llamarlo ventaja propia.", "",
          "Por régimen (cada día se etiqueta con el modelo de regímenes de su propio año de prueba):", "",
          "| Régimen | Días | Ganancia anual sin la base | Días positivos |", "| --- | --- | --- | --- |"]
    for r in j["regime_analysis"]["regimen"]:
        L.append(f"| {r['label'].replace('regimen_', '')} | {r['observation_count']} | {num(100 * r['active_return_metrics']['annualized_arithmetic_return'], 2)}% | {num(100 * r['positive_fraction'], 0)}% |")

    por_dia = o.groupby("dia")["neto_bps"].sum().sort_values(ascending=False)
    anual = o.groupby(o["dia"].dt.year)["neto_bps"].sum()
    mejor_anio, total = int(anual.idxmax()), o["neto_bps"].sum()
    mensual = o.groupby(o["dia"].dt.to_period("M"))["neto_bps"].sum()
    L += ["", "### ¿Está concentrada?", "",
          f"Ganancia total: {num(total, 0)} bps. Los {MEJORES_DIAS} mejores días aportan {num(por_dia.head(MEJORES_DIAS).sum(), 0)} bps "
          f"({num(100 * por_dia.head(MEJORES_DIAS).sum() / total, 0)}%); el mejor mes, {mensual.idxmax()}, aporta {num(mensual.max(), 0)}. "
          f"Días con ganancia: {num(100 * (por_dia > 0).mean(), 0)}%.", "",
          "| Corte | Operaciones | Ganancia neta | t | Neta con costo doble |", "| --- | --- | --- | --- | --- |",
          _linea("Todo el periodo", o), _linea(f"Sin los {MEJORES_DIAS} mejores días", o[~o["dia"].isin(por_dia.head(MEJORES_DIAS).index)]),
          _linea(f"Sin {mejor_anio}, el mejor año", o[o["dia"].dt.year != mejor_anio]),
          _linea("Solo compras", o[o["direccion"] > 0]), _linea("Solo ventas", o[o["direccion"] < 0]), "",
          "Mejores días: " + ", ".join(f"{d:%Y-%m-%d} ({num(v, 0)})" for d, v in por_dia.head(6).items()) + ".", ""]
    por_s = o.groupby("symbol")["neto_bps"].agg(["sum", "count", "mean"]).sort_values("sum", ascending=False)
    L += [f"Por acción: {int((por_s['sum'] > 0).sum())} de {len(por_s)} ganan. Las que más aportan: "
          + ", ".join(f"{s} ({num(100 * r['sum'] / total, 0)}%)" for s, r in por_s.head(5).iterrows()) + ". Las que más restan: "
          + ", ".join(f"{s} ({num(100 * r['sum'] / total, 0)}%)" for s, r in por_s.tail(3).iloc[::-1].iterrows()) + ".", ""]
    return L


def main() -> None:
    ap = argparse.ArgumentParser(description="Revisa de dónde sale la ganancia de un archivo de operaciones.")
    ap.add_argument("--operaciones", default="operaciones_calibradas", help="Prefijo del archivo en datos/modelos (por defecto, la versión calibrada)")
    args = ap.parse_args()

    _, universo = referencia.costos_y_universo()
    L = ["# Revisión de la ganancia (paso 2.8)", "",
         f"Generado el {pd.Timestamp.now():%Y-%m-%d} con `ventaja.py` sobre `datos/modelos/{args.operaciones}_<h>.parquet`. "
         "Es descriptivo: no entrena nada y no cuenta como variante. No incluye la muestra final.", "",
         "La primera parte usa `residual-edge-analyzer` sobre la ganancia neta de cada día, con bases de comparación fijadas de antemano. "
         "Unidades de la segunda parte: bps por operación; los t agrupan por día.", "",
         "Advertencia del analizador: el universo son empresas que existen hoy (sesgo de supervivencia), así que el resultado no es apto para decidir por sí solo.", ""]
    for h in HORIZONTES:
        o = pd.read_parquet(RAIZ / "modelos" / f"{args.operaciones}_{h}.parquet")
        t = serie_diaria(o, h, int(universo[h].sum()))
        L += seccion(h, o, t, analizar(t, h))
    texto = "\n".join(L)
    nombre = "ventaja.md" if args.operaciones == "operaciones_calibradas" else f"ventaja_{args.operaciones}.md"
    (RESULTADOS / nombre).write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
