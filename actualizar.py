"""
Actualización diaria: pone al día todas las fuentes de datos en una sola corrida.

Corre, en orden, los cuatro scripts de descarga. Cada uno baja solo lo que
falta (el año o el mes en curso), así que en total tarda unos 20 minutos.

    1. descargar_datos.py     velas de 1 minuto sin ajustar
    2. descargar_ajustes.py   splits, dividendos y escisiones
    3. descargar_noticias.py  noticias
    4. descargar_sec.py       comunicados 8-K y cifras financieras

Uso:
    python actualizar.py

Deja un registro por día en datos/registros/AAAA-MM-DD.log con todo lo que
imprimió cada script. Si un paso falla, sigue con los demás y al final termina
con error, para que la tarea programada lo muestre como fallida.

Pensado para correr una vez al día después del cierre del post-mercado
(8:00 p. m. de Nueva York).
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from descargar_datos import RAIZ

AQUI = Path(__file__).resolve().parent
PASOS = ["descargar_datos.py", "descargar_ajustes.py", "descargar_noticias.py", "descargar_sec.py"]
MAXIMO_POR_PASO = 3 * 60 * 60  # segundos; si un paso se cuelga, se corta y se sigue


def main() -> None:
    carpeta = RAIZ / "registros"
    carpeta.mkdir(parents=True, exist_ok=True)
    registro = carpeta / f"{datetime.now():%Y-%m-%d}.log"
    fallos = []

    with open(registro, "a", encoding="utf-8") as f:
        def anotar(linea: str) -> None:
            print(linea, flush=True)
            f.write(linea + "\n")
            f.flush()

        anotar(f"===== Actualización del {datetime.now():%Y-%m-%d %H:%M} =====")
        for paso in PASOS:
            anotar(f"\n--- {paso} ---")
            inicio = time.monotonic()
            try:
                r = subprocess.run([sys.executable, "-u", str(AQUI / paso)], cwd=AQUI, stdout=f, stderr=subprocess.STDOUT,
                                   timeout=MAXIMO_POR_PASO, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
                codigo = r.returncode
            except subprocess.TimeoutExpired:
                codigo = "sin terminar tras 3 horas"
            minutos = (time.monotonic() - inicio) / 60
            if codigo == 0:
                anotar(f"--- {paso}: bien ({minutos:.1f} min) ---")
            else:
                anotar(f"--- {paso}: FALLÓ ({codigo}, {minutos:.1f} min) ---")
                fallos.append(paso)

        anotar(f"\n===== Fin {datetime.now():%H:%M}: " + ("todo bien" if not fallos else "fallaron " + ", ".join(fallos)) + " =====")

    print(f"Registro en {registro}")
    if fallos:
        sys.exit(1)


if __name__ == "__main__":
    main()
