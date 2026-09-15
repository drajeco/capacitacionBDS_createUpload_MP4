#!/usr/bin/env python3
"""Corre los siete pasos en orden, con la parada de revisión del guion.

    python correr_pipeline.py --proyecto 01_content
    python correr_pipeline.py --proyecto 01_content --desde 04
    python correr_pipeline.py --proyecto 01_content --sin-parada
    python correr_pipeline.py --proyecto 01_content --limpiar

Cada paso también se puede correr suelto; esto solo los encadena.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

PASOS = [
    ("00", "00_validar_insumos.py", "Validar insumos"),
    ("01", "01_preparar_slides.py", "Preparar diapositivas"),
    ("02", "02_escribir_guion.py", "Escribir guion"),
    ("03", "03_dividir_guion.py", "Dividir guion"),
    ("04", "04_crear_audios.py", "Generar audios"),
    ("05", "05_montar_video.py", "Montar video"),
    ("06", "06_control_calidad.py", "Control de calidad"),
]

# Después del guion hay que leerlo antes de convertirlo en voz.
PARADA_TRAS = "02"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proyecto", default="01_content")
    p.add_argument("--desde", default="00", help="número del paso inicial (por defecto 00)")
    p.add_argument("--hasta", default="06", help="número del paso final (por defecto 06)")
    p.add_argument("--forzar", action="store_true")
    p.add_argument("--sin-parada", action="store_true",
                   help="no se detiene tras el guion (solo si ya lo revisaste)")
    p.add_argument("--limpiar", action="store_true",
                   help="borra 02_archivosIntermedios/ y 03_output/ antes de arrancar (empezar de cero)")
    args = p.parse_args()

    seleccion = [s for s in PASOS if args.desde <= s[0] <= args.hasta]
    if not seleccion:
        print(f"Ningún paso entre {args.desde} y {args.hasta}", file=sys.stderr)
        return 1

    if args.limpiar:
        proc = subprocess.run(
            [sys.executable, "limpiar_proyecto.py", "--proyecto", args.proyecto, "--si"],
            cwd=RAIZ,
        )
        if proc.returncode != 0:
            print("\nLa limpieza falló. El pipeline se detiene acá.", file=sys.stderr)
            return proc.returncode

    for numero, script, nombre in seleccion:
        cmd = [sys.executable, script, "--proyecto", args.proyecto]
        if args.forzar:
            cmd.append("--forzar")
        proc = subprocess.run(cmd, cwd=RAIZ)
        if proc.returncode != 0:
            print(f"\nEl paso {numero} ({nombre}) falló. El pipeline se detiene acá.", file=sys.stderr)
            return proc.returncode

        if numero == PARADA_TRAS and not args.sin_parada and numero != args.hasta:
            print(
                "\n" + "=" * 70 + "\n"
                "  PARADA: revisá el guion antes de convertirlo en voz.\n"
                f"  Cuando esté aprobado, seguí con:\n"
                f"    python correr_pipeline.py --proyecto {args.proyecto} --desde 03\n"
                + "=" * 70
            )
            return 0

    print("\nPipeline completo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
