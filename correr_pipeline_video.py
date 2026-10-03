#!/usr/bin/env python3
"""Corre los pasos 03 a 08 a partir del guion revisado.

    python correr_pipeline_video.py --proyecto 01_content

Cada paso también se puede correr suelto.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

PASOS = [
    ("03", "03_dividir_guion.py", "Dividir guion"),
    ("04", "04_crear_audios.py", "Generar audios"),
    ("05", "05_montar_video.py", "Montar video"),
    ("06", "06_control_calidad.py", "Control de calidad"),
    ("07", "07_preparar_youtube.py", "Preparar publicación de YouTube"),
    ("08", "08_crear_cuestionario.py", "Crear cuestionario"),
]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proyecto", default="01_content")
    p.add_argument("--forzar", action="store_true", help="rehace lo ya generado")
    p.add_argument("--archivar-drive", action="store_true", help="archiva en Google Drive después del paso 08")
    p.add_argument("--leccion", type=int, help="número para el archivo en Drive")
    p.add_argument("--titulo-leccion", help="título para el archivo en Drive")
    p.add_argument("--conservar-local", action="store_true", help="archiva sin vaciar el contenido local")
    args = p.parse_args()

    for numero, script, nombre in PASOS:
        cmd = [sys.executable, script, "--proyecto", args.proyecto]
        if args.forzar:
            cmd.append("--forzar")
        proc = subprocess.run(cmd, cwd=RAIZ)
        if proc.returncode != 0:
            print(f"\nEl paso {numero} ({nombre}) falló. El pipeline se detiene acá.", file=sys.stderr)
            return proc.returncode

    if args.archivar_drive:
        cmd = [sys.executable, "09_archivar_drive.py", "--proyecto", args.proyecto]
        if args.leccion is not None:
            cmd += ["--leccion", str(args.leccion)]
        if args.titulo_leccion:
            cmd += ["--titulo-leccion", args.titulo_leccion]
        if args.conservar_local:
            cmd.append("--conservar-local")
        proc = subprocess.run(cmd, cwd=RAIZ)
        if proc.returncode != 0:
            return proc.returncode

    print("\nPipeline de video completo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
