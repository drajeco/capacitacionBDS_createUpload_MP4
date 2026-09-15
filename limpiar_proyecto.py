#!/usr/bin/env python3
"""Vacía los artefactos regenerables de un proyecto antes de correr el pipeline de cero.

Borra 02_archivosIntermedios/ y 03_output/ enteros. No toca 01_materialOriginal/
(el material original) ni proyecto.yaml.

    python limpiar_proyecto.py --proyecto 01_content
    python limpiar_proyecto.py --proyecto 01_content --si   # sin confirmar
"""

from __future__ import annotations

import argparse
import shutil
import sys

from comun import config, consola

CARPETAS_REGENERABLES = ("02_archivosIntermedios", "03_output")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proyecto", default="01_content", help="carpeta del video (por defecto 01_content)")
    p.add_argument("--si", action="store_true", help="no pedir confirmación antes de borrar")
    args = p.parse_args()

    proy = config.cargar(args.proyecto)
    consola.titulo("Limpieza", f"Vaciar artefactos regenerables · {proy.nombre}")

    objetivos = [proy.base / carpeta for carpeta in CARPETAS_REGENERABLES]
    existentes = [c for c in objetivos if c.exists() and any(c.iterdir())]

    if not existentes:
        consola.ok("02_archivosIntermedios/ y 03_output/ ya están vacías o no existen. Nada que borrar.")
        return 0

    for carpeta in existentes:
        consola.aviso(f"{carpeta.relative_to(proy.base)}/ tiene contenido:")
        for hijo in sorted(carpeta.iterdir()):
            consola.info(f"    - {hijo.relative_to(proy.base)}")

    if not args.si:
        respuesta = input("\n¿Borrar todo lo anterior? [s/N] ").strip().lower()
        if respuesta != "s":
            consola.info("Cancelado: no se borró nada.")
            return 1

    for carpeta in existentes:
        shutil.rmtree(carpeta)
        consola.ok(f"Borrado {carpeta.relative_to(proy.base)}/")

    consola.siguiente(f"python 00_validar_insumos.py --proyecto {args.proyecto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
