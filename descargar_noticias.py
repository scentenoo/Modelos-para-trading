"""
Descarga las noticias de las acciones del universo desde Alpaca y las guarda en Parquet.

Cada noticia trae titular, resumen, texto, fuente, símbolos mencionados y la
hora exacta de publicación (UTC). Es lo que leerá la IA.

Uso:
    python descargar_noticias.py                      # universo por defecto, 2016 a hoy
    python descargar_noticias.py --inicio 2026-01-01  # solo desde 2026
    python descargar_noticias.py --forzar             # re-descarga todo, aunque ya exista

Estructura de salida:
    datos/noticias/AAAA-MM.parquet   (un archivo por mes, todas las acciones juntas)

Si se interrumpe, vuelve a correrlo: salta los meses ya guardados y re-descarga
solo el mes en curso.

Ojo:
  - Una noticia puede mencionar varias acciones (columna `symbols`), y solo
    aparecen las que mencionan alguna acción del universo.
  - Alpaca filtra por fecha de actualización: el archivo de un mes puede traer
    noticias publicadas a finales del mes anterior y corregidas después.
  - `created_at` es cuándo salió la noticia; `updated_at`, cuándo se corrigió.
    Si son distintas, el texto guardado es el corregido, no el original: para
    no usar información del futuro, tratar la noticia como disponible desde
    `updated_at`.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
from alpaca.common.exceptions import APIError
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

from descargar_datos import RAIZ, UNIVERSO, cargar_env

CARPETA = RAIZ / "noticias"
COLUMNAS = ["id", "created_at", "updated_at", "headline", "summary", "content", "source", "author", "url", "symbols"]


def descargar_mes(cli, simbolos: list[str], inicio: datetime, fin: datetime) -> pd.DataFrame | None:
    """Noticias entre inicio y fin, un DataFrame vacío si no hay, o None si la descarga falló."""
    req = NewsRequest(symbols=",".join(simbolos), start=inicio, end=fin, include_content=True, sort="asc")
    for intento in range(5):
        try:
            noticias = cli.get_news(req).data.get("news", [])
            break
        except Exception as e:  # noqa: BLE001
            if isinstance(e, APIError) and e.status_code in (400, 401, 403, 422):
                sys.exit(f"Alpaca rechazó la petición ({e.status_code}): {e}")
            espera = 15 * (intento + 1)
            print(f"   error ({e}); reintento en {espera}s")
            time.sleep(espera)
    else:
        return None

    if not noticias:
        return pd.DataFrame(columns=COLUMNAS)
    df = pd.DataFrame([n.model_dump(mode="json", include=set(COLUMNAS)) for n in noticias])[COLUMNAS]
    for col in ("created_at", "updated_at"):
        df[col] = pd.to_datetime(df[col], utc=True)
    return df.drop_duplicates(subset="id").sort_values("created_at", ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Descarga noticias desde Alpaca.")
    ap.add_argument("--inicio", default="2016-01-01", help="Fecha inicial AAAA-MM-DD (por defecto 2016-01-01)")
    ap.add_argument("--simbolos", nargs="+", default=UNIVERSO, help="Lista de símbolos")
    ap.add_argument("--forzar", action="store_true", help="Re-descarga aunque el archivo ya exista")
    args = ap.parse_args()

    cargar_env()
    llave = os.environ.get("APCA_API_KEY_ID")
    secreto = os.environ.get("APCA_API_SECRET_KEY")
    if not llave or not secreto:
        sys.exit("Faltan APCA_API_KEY_ID y APCA_API_SECRET_KEY (ver descargar_datos.py).")
    cli = NewsClient(llave, secreto)

    inicio_global = datetime.fromisoformat(args.inicio).replace(tzinfo=timezone.utc)
    ahora = datetime.now(timezone.utc)
    CARPETA.mkdir(parents=True, exist_ok=True)

    total, fallos = 0, []
    mes = inicio_global.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while mes <= ahora:
        siguiente = (mes + timedelta(days=32)).replace(day=1)
        nombre = f"{mes:%Y-%m}"
        archivo = CARPETA / f"{nombre}.parquet"
        en_curso = siguiente > ahora
        if archivo.exists() and not en_curso and not args.forzar:
            mes = siguiente
            continue
        # El fin es inclusivo: se resta 1 s para no repetir noticias entre meses.
        df = descargar_mes(cli, args.simbolos, max(mes, inicio_global), min(siguiente - timedelta(seconds=1), ahora))
        if df is None:
            print(f"   {nombre}: falló tras 5 intentos, se salta")
            fallos.append(nombre)
        else:
            temporal = archivo.with_suffix(".parquet.tmp")
            df.to_parquet(temporal, index=False)
            temporal.replace(archivo)
            total += len(df)
            print(f"   {nombre}: {len(df):,} noticias")
        mes = siguiente

    print(f"\nListo. {total:,} noticias guardadas en {CARPETA}")
    if fallos:
        sys.exit(f"Fallaron {len(fallos)} meses (volver a correr): {', '.join(fallos)}")


if __name__ == "__main__":
    main()
