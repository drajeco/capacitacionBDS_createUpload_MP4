#!/usr/bin/env python3
"""Corre los pasos 00 a 02 y termina para revisar el guion.

    python correr_pipeline_guion.py --proyecto 01_content

Cada paso también se puede correr suelto.
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
]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proyecto", default="01_content")
    p.add_argument("--forzar", action="store_true", help="rehace lo ya generado")
    p.add_argument("--limpiar", action="store_true",
                   help="borra 02_archivosIntermedios/ y 03_output/, incluido el guion editado")
    args = p.parse_args()

    if args.limpiar:
        proc = subprocess.run(
            [sys.executable, "limpiar_proyecto.py", "--proyecto", args.proyecto, "--si"],
            cwd=RAIZ,
        )
        if proc.returncode != 0:
            print("\nLa limpieza falló. El pipeline se detiene acá.", file=sys.stderr)
            return proc.returncode

    for numero, script, nombre in PASOS:
        cmd = [sys.executable, script, "--proyecto", args.proyecto]
        if args.forzar:
            cmd.append("--forzar")
        proc = subprocess.run(cmd, cwd=RAIZ)
        if proc.returncode != 0:
            print(f"\nEl paso {numero} ({nombre}) falló. El pipeline se detiene acá.", file=sys.stderr)
            return proc.returncode

    print(
        "\nGuion preparado. Revisá y editá el guion maestro antes de continuar.\n"
        "Cuando esté aprobado, ejecutá:\n"
        f"  python correr_pipeline_video.py --proyecto {args.proyecto}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
