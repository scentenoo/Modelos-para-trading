"""
Fase 3 · Semana de prueba técnica del sistema en vivo (17 al 23 de noviembre de 2026).

Revisa que el sistema funcione en sesiones reales, sin prueba de H0 (decisión del
16 de noviembre de 2026, documento del proyecto): lector de noticias con Claude
Haiku 5.5, B en modo sombra, cierre diario y actualización nocturna.

Por cada día de la semana resume, desde datos/decisiones.sqlite y systemd:
  - Noticias: llegadas, omitidas, enviadas a la IA, válidas, sin respuesta,
    reintentos, latencia (mediana, 90%, máxima), tokens y costo estimado.
  - B en modo sombra: momentos hechos y saltados (con el motivo), cierre hecho,
    operaciones y su ganancia (solo informativa: con ~10 operaciones al día no
    dice nada estadísticamente).
  - Servicios: estado de noticias-vivo y b-sombra, y resultado de la última
    actualización nocturna.

Uso (en el PC viejo):
    python prueba_tecnica.py                 # informe del día de hoy (Nueva York)
    python prueba_tecnica.py --dia 2026-11-17
    python prueba_tecnica.py --semana        # resumen de toda la semana

Salida:
    datos/registros/prueba_tecnica.md   (una sección por informe, se agrega al final)
"""

import argparse
import sqlite3
import subprocess
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from descargar_datos import RAIZ

BASE = RAIZ / "decisiones.sqlite"
SALIDA = RAIZ / "registros" / "prueba_tecnica.md"
NY = ZoneInfo("America/New_York")
INICIO, FIN = "2026-11-17", "2026-11-23"
PRECIO_ENTRADA, PRECIO_SALIDA = 0.10 / 1e6, 0.50 / 1e6       # Claude Haiku 5.5, dólares por token
SERVICIOS = ["noticias-vivo", "b-sombra", "actualizar-datos.timer"]


def systemd(propiedad: str, unidad: str) -> str:
    try:
        return subprocess.run(["systemctl", "show", unidad, f"--property={propiedad}", "--value"],
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"(sin dato: {e})"


def num(x, d=1) -> str:
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def rango_utc(desde: str, hasta: str) -> tuple[str, str]:
    """Días de Nueva York [desde, hasta] como rango de horas UTC en ISO."""
    a = pd.Timestamp(desde, tz=NY).tz_convert("UTC")
    b = (pd.Timestamp(hasta, tz=NY) + pd.Timedelta(days=1)).tz_convert("UTC")
    return a.isoformat(timespec="milliseconds"), b.isoformat(timespec="milliseconds")


def noticias(con, desde: str, hasta: str) -> list[str]:
    a, b = rango_utc(desde, hasta)
    ll = pd.read_sql("SELECT estado, motivo FROM llegadas WHERE llegada_utc >= ? AND llegada_utc < ?", con, params=(a, b))
    r = pd.read_sql("SELECT noticia, version_noticia, intento, latencia_ms, tokens_entrada, tokens_salida, valido, texto_crudo "
                    "FROM respuestas_ia WHERE enviada_utc >= ? AND enviada_utc < ?", con, params=(a, b))
    por_noticia = r.groupby(["noticia", "version_noticia"]).agg(valida=("valido", "max"), intentos=("intento", "max"))
    validas = int(por_noticia["valida"].sum())
    reintento_tardio = int(((por_noticia["valida"] == 1) & (por_noticia["intentos"] > 2)).sum())
    errores_api = int(r["texto_crudo"].fillna("").str.startswith("ERROR").sum())
    costo = r["tokens_entrada"].sum() * PRECIO_ENTRADA + r["tokens_salida"].sum() * PRECIO_SALIDA
    lat = r["latencia_ms"].dropna() / 1000
    return ["**Noticias con Claude Haiku 5.5**", "",
            f"- Llegadas: {len(ll)} (omitidas {int((ll['estado'] == 'omitida').sum())}; enviadas a la IA {int((ll['estado'] == 'enviada').sum())}).",
            f"- Con respuesta válida: {validas} de {len(por_noticia)}; sin respuesta: {len(por_noticia) - validas}; "
            f"recuperadas con reintento tardío: {reintento_tardio}; intentos con error de la API o de conexión: {errores_api}.",
            f"- Latencia por intento: mediana {num(lat.median())} s, 90% {num(lat.quantile(0.9))} s, máxima {num(lat.max())} s." if len(lat) else "- Latencia: sin intentos.",
            f"- Tokens: {int(r['tokens_entrada'].sum()):,} de entrada y {int(r['tokens_salida'].sum()):,} de salida; costo estimado {num(costo, 4)} dólares.", ""]


def sombra(con, desde: str, hasta: str) -> list[str]:
    m = pd.read_sql("SELECT dia, tipo, k, estado, detalle FROM b_sombra_momentos WHERE dia >= ? AND dia <= ? AND modo = 'vivo'",
                    con, params=(desde, hasta))
    o = pd.read_sql("SELECT dia, symbol, neto_bps, bruto_bps, costo_bps, completada_utc FROM b_sombra_operaciones "
                    "WHERE dia >= ? AND dia <= ? AND modo = 'vivo'", con, params=(desde, hasta))
    mom = m[m["tipo"] != "cierre"]
    cierres = m[m["tipo"] == "cierre"]
    L = ["**B en modo sombra**", "",
         f"- Días con actividad: {m['dia'].nunique()}. Momentos hechos: {int((mom['estado'] == 'hecho').sum())}; "
         f"saltados: {int((mom['estado'] == 'saltado').sum())}. Cierres hechos: {int((cierres['estado'] == 'hecho').sum())}."]
    for _, s in mom[mom["estado"] == "saltado"].iterrows():
        L.append(f"  - Saltado {s['dia']} k={s['k']}: {s['detalle']}")
    completas = o[o["completada_utc"].notna()]
    L.append(f"- Operaciones registradas: {len(o)}; completadas al cierre: {len(completas)}.")
    if len(completas):
        L.append(f"- Ganancia (solo informativa): bruta {num(completas['bruto_bps'].mean(), 2)} bps, costo {num(completas['costo_bps'].mean(), 2)}, "
                 f"neta {num(completas['neto_bps'].mean(), 2)} bps por operación; total {num(completas['neto_bps'].sum(), 0)} bps.")
    return L + [""]


def servicios() -> list[str]:
    L = ["**Servicios**", ""]
    for s in SERVICIOS:
        L.append(f"- `{s}`: {systemd('ActiveState', s)} ({systemd('SubState', s)}); reinicios: {systemd('NRestarts', s) or '—'}.")
    L.append(f"- Última actualización nocturna: resultado `{systemd('Result', 'actualizar-datos.service')}`, "
             f"terminó {systemd('ExecMainExitTimestamp', 'actualizar-datos.service') or '—'}.")
    return L + [""]


def informe(desde: str, hasta: str, titulo: str) -> str:
    con = sqlite3.connect(BASE)
    try:
        L = [f"## {titulo}", "", f"Generado el {datetime.now(NY):%Y-%m-%d %H:%M} (Nueva York) con `prueba_tecnica.py`.", ""]
        L += noticias(con, desde, hasta) + sombra(con, desde, hasta) + servicios()
    finally:
        con.close()
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Informe de la semana de prueba técnica del sistema en vivo.")
    ap.add_argument("--dia", help="Día de Nueva York AAAA-MM-DD (por defecto hoy)")
    ap.add_argument("--semana", action="store_true", help=f"Resumen de toda la semana ({INICIO} a {FIN})")
    args = ap.parse_args()
    if args.semana:
        texto = informe(INICIO, FIN, f"Resumen de la semana de prueba técnica ({INICIO} a {FIN})")
    else:
        dia = args.dia or f"{datetime.now(NY):%Y-%m-%d}"
        texto = informe(dia, dia, f"Día {dia}")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "a", encoding="utf-8") as f:
        f.write(texto + "\n")
    print(texto)


if __name__ == "__main__":
    main()
