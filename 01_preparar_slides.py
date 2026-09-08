#!/usr/bin/env python3
"""Paso 01 - Normaliza las diapositivas a slide_NN.png y arma la hoja de contacto.

Los PNG exportados llegan con nombres impredecibles (en 01_content traen un
U+200E invisible) y en orden alfabético que deja de coincidir con el numérico a
partir de la décima diapositiva. Acá quedan con nombres deterministas, que son
los que usan todos los pasos siguientes.

    python 01_preparar_slides.py --proyecto 01_content
"""

from __future__ import annotations

import shutil
import sys

from PIL import Image, ImageDraw

from comun import config, consola, rutas

MINIATURA = (480, 270)
COLUMNAS = 3
MARGEN = 16


def hoja_de_contacto(imagenes: list, destino) -> None:
    """Una sola imagen con todas las diapositivas numeradas, para revisarlas de un vistazo."""
    filas = (len(imagenes) + COLUMNAS - 1) // COLUMNAS
    ancho = COLUMNAS * MINIATURA[0] + (COLUMNAS + 1) * MARGEN
    alto = filas * (MINIATURA[1] + 28) + (filas + 1) * MARGEN
    hoja = Image.new("RGB", (ancho, alto), "#1e1e1e")
    dibujo = ImageDraw.Draw(hoja)

    for indice, ruta in enumerate(imagenes):
        fila, columna = divmod(indice, COLUMNAS)
        x = MARGEN + columna * (MINIATURA[0] + MARGEN)
        y = MARGEN + fila * (MINIATURA[1] + 28 + MARGEN)
        with Image.open(ruta) as img:
            mini = img.convert("RGB").copy()
            mini.thumbnail(MINIATURA)
            hoja.paste(mini, (x + (MINIATURA[0] - mini.width) // 2, y))
        dibujo.text((x + 4, y + MINIATURA[1] + 6), ruta.stem, fill="#dddddd")

    destino.parent.mkdir(parents=True, exist_ok=True)
    hoja.save(destino)


def main() -> int:
    args = config.parser(__doc__).parse_args()
    proy = config.cargar(args.proyecto)
    consola.titulo("Paso 01", f"Preparar diapositivas · {proy.nombre}")

    origen = proy.insumo("slides")
    if not origen.is_dir():
        consola.abortar(f"No existe la carpeta de diapositivas: {origen}")

    encontradas = rutas.descubrir_slides(origen)
    if not encontradas:
        consola.abortar(f"No hay imágenes numeradas en {origen}")

    destino_dir = proy.salida("slides")
    destino_dir.mkdir(parents=True, exist_ok=True)

    generadas = []
    saltadas = 0
    for posicion, ruta in enumerate(encontradas, start=1):
        destino = destino_dir / f"slide_{posicion:02d}.png"
        if destino.exists() and not args.forzar:
            saltadas += 1
            generadas.append(destino)
            continue

        # Se reexporta con Pillow en vez de copiar: uniforma el modo de color y
        # descarta perfiles raros que después confunden a ffmpeg.
        if ruta.suffix.lower() == ".png":
            shutil.copy2(ruta, destino)
        else:
            with Image.open(ruta) as img:
                img.convert("RGB").save(destino, "PNG")
        generadas.append(destino)

    with Image.open(generadas[0]) as muestra:
        tamano = muestra.size

    consola.ok(f"{len(generadas)} diapositivas en {destino_dir.name}/ ({tamano[0]}x{tamano[1]})")
    if saltadas:
        consola.info(f"    [dim]{saltadas} ya estaban; usar --forzar para rehacerlas[/]")

    objetivo = (proy.video_cfg["ancho"], proy.video_cfg["alto"])
    if tamano != objetivo:
        consola.aviso(
            f"las diapositivas son {tamano[0]}x{tamano[1]} y el video sale "
            f"{objetivo[0]}x{objetivo[1]}: se escalarán con barras. "
            "Para máxima nitidez, reexportarlas desde Keynote a esa resolución."
        )

    hoja = proy.salida("qc") / "hoja_de_contacto.png"
    hoja_de_contacto(generadas, hoja)
    consola.ok(f"Hoja de contacto: {hoja}")

    consola.info("\n[bold]Revisá la hoja de contacto[/] antes de seguir: orden correcto, "
                 "portada incluida, sin diapositivas de más.")
    consola.siguiente(f"python 02_escribir_guion.py --proyecto {args.proyecto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
