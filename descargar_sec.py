"""
Descarga de la SEC (EDGAR) los comunicados oficiales 8-K y las cifras de los
estados financieros de las acciones del universo. Es gratis y no pide llave.

Qué baja:
  1. Índice de comunicados: cada 8-K con la hora exacta en que la SEC lo
     publicó y los temas que trata (por ejemplo 2.02 = resultados).
  2. Cifras: todos los datos contables que la empresa reporta en formato
     estructurado (ingresos, utilidad, ganancia por acción...).
  3. Textos: el cuerpo de cada 8-K y sus anexos de prensa (EX-99), en texto plano.

Identificación (obligatoria): la SEC exige que cada programa diga quién es.
Agregar una línea al archivo .env con tu nombre o proyecto y un correo:
    SEC_USER_AGENT=Nombre Apellido correo@ejemplo.com

Uso:
    python descargar_sec.py                    # todo, 2016 a hoy
    python descargar_sec.py --solo indice      # solo el índice de comunicados
    python descargar_sec.py --solo cifras
    python descargar_sec.py --solo textos      # el paso largo (cerca de una hora)
    python descargar_sec.py --simbolos AAPL NVDA

Estructura de salida:
    datos/sec/comunicados_indice.parquet       (todas las empresas)
    datos/sec/cifras/SIMBOLO.parquet
    datos/sec/comunicados/SIMBOLO/AAAA.parquet (textos)

Si se interrumpe, vuelve a correrlo: en los textos salta los años ya guardados
y re-descarga solo el año en curso.

Ojo:
  - Los ETF (SPY, QQQ, IWM) no se incluyen: no publican comunicados de empresa.
  - `aceptado` es la hora (UTC) en que el comunicado quedó público: úsala como
    el momento desde el que la información está disponible.
  - Las cifras traen la fecha de presentación (`filed`), no la hora. La hora de
    un resultado trimestral sale del 8-K con tema 2.02 de ese mismo día.
  - La SEC no trae lo que esperaban los analistas, solo lo que la empresa reportó.
  - Cuando una empresa se reorganiza bajo una sociedad nueva, la SEC le da otro
    número de registro (CIK) y la historia anterior queda en el viejo. Esos
    casos están en CIK_ANTERIORES; si una empresa aparece con muy pocos
    comunicados o su historia empieza tarde, falta agregarla ahí.
"""

import argparse
import html
import os
import re
import sys
import time
from datetime import datetime, timezone

import pandas as pd
import requests

from descargar_datos import RAIZ, UNIVERSO, cargar_env

CARPETA = RAIZ / "sec"
ETF = {"SPY", "QQQ", "IWM"}
PAUSA = 0.2  # segundos entre peticiones: 5 por segundo (la SEC permite 10)
FORMULARIOS = {"8-K", "8-K/A"}
# Registros anteriores de empresas que se reorganizaron bajo una sociedad nueva.
CIK_ANTERIORES = {
    "XOM": [34088],              # Exxon Mobil Corp, hasta julio de 2026
    "DIS": [1001039],            # Walt Disney Co anterior a la compra de Fox, hasta marzo de 2019
    "AVGO": [1649338, 1441634],  # Broadcom Ltd y Avago Technologies, hasta abril de 2018
}
COLUMNAS_INDICE = ["accessionNumber", "form", "filingDate", "acceptanceDateTime", "reportDate", "items", "primaryDocument"]

_sesion = requests.Session()
_ultima = 0.0


def pedir(url: str) -> requests.Response | None:
    """GET con pausa y reintentos. Devuelve None si el archivo no existe o si falla 5 veces."""
    global _ultima
    for intento in range(5):
        time.sleep(max(0.0, PAUSA - (time.monotonic() - _ultima)))
        _ultima = time.monotonic()
        try:
            r = _sesion.get(url, timeout=60)
        except requests.RequestException as e:
            r, motivo = None, str(e)
        else:
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
            if r.status_code == 403:
                sys.exit("La SEC rechazó la petición (403). Revisa que SEC_USER_AGENT en .env tenga nombre y correo; "
                         "si ya los tiene, la SEC bloqueó temporalmente por exceso de peticiones: espera 10 minutos.")
            motivo = f"HTTP {r.status_code}"
        espera = 10 * (intento + 1)
        print(f"   error ({motivo}); reintento en {espera}s")
        time.sleep(espera)
    return None


def mapa_cik(simbolos: list[str]) -> dict[str, list[int]]:
    """Números de registro (CIK) de cada símbolo en la SEC: el actual y los anteriores."""
    r = pedir("https://www.sec.gov/files/company_tickers.json")
    if r is None:
        sys.exit("No se pudo bajar la lista de empresas de la SEC.")
    todos = {fila["ticker"]: int(fila["cik_str"]) for fila in r.json().values()}
    faltan = [s for s in simbolos if s not in todos]
    if faltan:
        print(f"   sin registro en la SEC, se saltan: {', '.join(faltan)}")
    return {s: [todos[s], *CIK_ANTERIORES.get(s, [])] for s in simbolos if s in todos}


def hora_utc(serie: pd.Series) -> pd.Series:
    """La SEC marca `acceptanceDateTime` como UTC ('...Z') y lo es."""
    return pd.to_datetime(serie, utc=True, errors="coerce")


def indice_empresa(simbolo: str, cik: int, inicio: str) -> pd.DataFrame | None:
    r = pedir(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    if r is None:
        return None
    datos = r.json()
    partes = [pd.DataFrame(datos["filings"]["recent"])]
    for extra in datos["filings"].get("files", []):
        if extra.get("filingTo", "9999") < inicio:
            continue  # ese archivo solo trae presentaciones anteriores a la fecha inicial
        r = pedir(f"https://data.sec.gov/submissions/{extra['name']}")
        if r is None:
            return None
        partes.append(pd.DataFrame(r.json()))
    df = pd.concat(partes, ignore_index=True)
    df = df[df["form"].isin(FORMULARIOS) & (df["filingDate"] >= inicio)][COLUMNAS_INDICE]
    df = df.rename(columns={
        "accessionNumber": "numero", "form": "formulario", "filingDate": "fecha", "acceptanceDateTime": "aceptado",
        "reportDate": "fecha_reporte", "items": "temas", "primaryDocument": "documento",
    })
    df["aceptado"] = hora_utc(df["aceptado"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    df.insert(0, "cik", cik)
    df.insert(0, "symbol", simbolo)
    return df.drop_duplicates(subset="numero").sort_values("aceptado", ignore_index=True)


def cifras_empresa(simbolo: str, cik: int) -> pd.DataFrame | None:
    r = pedir(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    if r is None:
        return None
    filas = []
    for taxonomia, conceptos in r.json().get("facts", {}).items():
        for concepto, info in conceptos.items():
            for unidad, valores in info.get("units", {}).items():
                for v in valores:
                    filas.append((taxonomia, concepto, unidad, v.get("start"), v.get("end"), v.get("val"),
                                  v.get("fy"), v.get("fp"), v.get("form"), v.get("filed"), v.get("accn"), v.get("frame")))
    df = pd.DataFrame(filas, columns=["taxonomia", "concepto", "unidad", "inicio", "fin", "valor",
                                      "anio_fiscal", "periodo_fiscal", "formulario", "filed", "numero", "marco"])
    for col in ("inicio", "fin", "filed"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["anio_fiscal"] = pd.to_numeric(df["anio_fiscal"], errors="coerce").astype("Int64")
    df.insert(0, "symbol", simbolo)
    return df


_DOC = re.compile(r"<DOCUMENT>(.*?)</DOCUMENT>", re.S)
_CAMPO = {c: re.compile(rf"<{c}>([^\n\r]*)") for c in ("TYPE", "FILENAME")}
_TEXTO = re.compile(r"<TEXT>(.*)</TEXT>", re.S)
_OCULTO = re.compile(r"<(script|style|ix:header|head)\b.*?</\1>", re.S | re.I)
_SALTO = re.compile(r"<(br|/p|/div|/tr|/h\d|/li|/table)\b[^>]*>", re.I)
_ETIQUETA = re.compile(r"<[^>]+>")


def a_texto(crudo: str) -> str:
    """Convierte HTML a texto plano legible."""
    t = _OCULTO.sub(" ", crudo)
    t = _SALTO.sub("\n", t)
    t = html.unescape(_ETIQUETA.sub(" ", t)).replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\s*\n\s*", "\n", t).strip()


def textos_comunicado(cik: int, numero: str) -> list[tuple[str, str, str]] | None:
    """Documentos de texto de un comunicado: (tipo, archivo, texto) del 8-K y de los anexos EX-99."""
    r = pedir(f"https://www.sec.gov/Archives/edgar/data/{cik}/{numero.replace('-', '')}/{numero}.txt")
    if r is None:
        return None
    r.encoding = r.encoding or "utf-8"
    salida = []
    for doc in _DOC.findall(r.text):
        tipo = _CAMPO["TYPE"].search(doc)
        archivo = _CAMPO["FILENAME"].search(doc)
        cuerpo = _TEXTO.search(doc)
        if not tipo or not cuerpo:
            continue
        tipo = tipo.group(1).strip().upper()
        archivo = archivo.group(1).strip() if archivo else ""
        if not (tipo in FORMULARIOS or tipo.startswith("EX-99")):
            continue
        if not archivo.lower().endswith((".htm", ".html", ".txt")):
            continue  # imágenes, PDF y otros binarios
        salida.append((tipo, archivo, a_texto(cuerpo.group(1))))
    return salida


def guardar(df: pd.DataFrame, archivo) -> None:
    archivo.parent.mkdir(parents=True, exist_ok=True)
    temporal = archivo.with_suffix(".parquet.tmp")
    df.to_parquet(temporal, index=False)
    temporal.replace(archivo)


def main() -> None:
    ap = argparse.ArgumentParser(description="Descarga comunicados 8-K y cifras financieras desde la SEC.")
    ap.add_argument("--inicio", default="2016-01-01", help="Fecha inicial AAAA-MM-DD (por defecto 2016-01-01)")
    ap.add_argument("--simbolos", nargs="+", default=[s for s in UNIVERSO if s not in ETF], help="Lista de símbolos")
    ap.add_argument("--solo", choices=["indice", "cifras", "textos"], help="Corre solo ese paso")
    ap.add_argument("--forzar", action="store_true", help="Re-descarga los textos aunque el archivo ya exista")
    args = ap.parse_args()

    cargar_env()
    identificacion = os.environ.get("SEC_USER_AGENT", "").strip()
    if not identificacion:
        sys.exit("Falta SEC_USER_AGENT en .env (ver instrucciones arriba).")
    _sesion.headers.update({"User-Agent": identificacion, "Accept-Encoding": "gzip, deflate"})

    ciks = mapa_cik(args.simbolos)
    fallos = []
    archivo_indice = CARPETA / "comunicados_indice.parquet"

    if args.solo in (None, "indice"):
        print("Índice de comunicados")
        partes = []
        for simbolo, lista in ciks.items():
            trozos = [indice_empresa(simbolo, cik, args.inicio) for cik in lista]
            if any(t is None for t in trozos):
                fallos.append(f"índice {simbolo}")
                continue
            df = pd.concat(trozos, ignore_index=True).drop_duplicates(subset="numero").sort_values("aceptado", ignore_index=True)
            partes.append(df)
            print(f"   {simbolo}: {len(df):,} comunicados")
        if partes:
            nuevo = pd.concat(partes, ignore_index=True)
            if archivo_indice.exists():  # conservar las empresas que no se pidieron esta vez
                viejo = pd.read_parquet(archivo_indice)
                nuevo = pd.concat([viejo[~viejo["symbol"].isin(nuevo["symbol"].unique())], nuevo], ignore_index=True)
            guardar(nuevo, archivo_indice)

    if args.solo in (None, "cifras"):
        print("Cifras financieras")
        for simbolo, lista in ciks.items():
            trozos = [cifras_empresa(simbolo, cik) for cik in lista]
            trozos = [t for t in trozos if t is not None]  # un registro viejo puede no tener cifras estructuradas
            if not trozos:
                fallos.append(f"cifras {simbolo}")
                continue
            df = pd.concat(trozos, ignore_index=True).sort_values("filed", ignore_index=True)
            guardar(df, CARPETA / "cifras" / f"{simbolo}.parquet")
            print(f"   {simbolo}: {len(df):,} datos")

    if args.solo in (None, "textos"):
        print("Textos de los comunicados")
        if not archivo_indice.exists():
            sys.exit("Falta el índice: correr primero con --solo indice.")
        indice = pd.read_parquet(archivo_indice)
        indice = indice[indice["symbol"].isin(ciks) & (indice["fecha"] >= args.inicio)]
        anio_actual = datetime.now(timezone.utc).year
        for (simbolo, anio), grupo in indice.groupby(["symbol", indice["fecha"].dt.year]):
            archivo = CARPETA / "comunicados" / simbolo / f"{anio}.parquet"
            if archivo.exists() and anio < anio_actual and not args.forzar:
                continue
            filas, incompleto = [], False
            for fila in grupo.itertuples():
                docs = textos_comunicado(fila.cik, fila.numero)
                if docs is None:
                    incompleto = True
                    continue
                filas += [(simbolo, fila.numero, fila.aceptado, fila.temas, tipo, nombre, texto) for tipo, nombre, texto in docs]
            if incompleto:
                fallos.append(f"textos {simbolo} {anio}")
                continue  # no se guarda a medias: se reintenta completo en la próxima corrida
            guardar(pd.DataFrame(filas, columns=["symbol", "numero", "aceptado", "temas", "tipo", "archivo", "texto"]), archivo)
            print(f"   {simbolo} {anio}: {len(grupo)} comunicados, {len(filas)} documentos")

    print(f"\nListo. Datos de la SEC en {CARPETA}")
    if fallos:
        sys.exit(f"Fallaron {len(fallos)} descargas (volver a correr): {', '.join(fallos)}")


if __name__ == "__main__":
    main()
