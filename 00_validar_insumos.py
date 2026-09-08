#!/usr/bin/env python3
"""Paso 00 - Verifica que estén los insumos, las herramientas y las credenciales.

Se corre antes de gastar tiempo o tokens. Reporta las diapositivas detectadas en
el orden en que el pipeline las va a usar, que es lo que conviene mirar primero.

    python 00_validar_insumos.py --proyecto 01_content
"""

from __future__ import annotations

import sys

from comun import config, consola, ffmpeg, rutas


def main() -> int:
    args = config.parser(__doc__).parse_args()
    try:
        proy = config.cargar(args.proyecto)
    except FileNotFoundError as exc:
        consola.abortar(str(exc))

    consola.titulo("Paso 00", f"Validar insumos · {proy.nombre}")
    problemas: list[str] = []
    avisos: list[str] = []

    # --- proyecto.yaml ---
    if (proy.base / "proyecto.yaml").is_file():
        consola.ok(f"proyecto.yaml encontrado en {proy.base.name}/")
    else:
        avisos.append("no hay proyecto.yaml; se usan todos los valores por defecto")

    # --- transcripción ---
    transcripcion = rutas.primer_archivo(proy.insumo("transcripcion"))
    if transcripcion:
        palabras = len(transcripcion.read_text(encoding="utf-8").split())
        consola.ok(f"Transcripción: {transcripcion.name} ({palabras:,} palabras)")
    else:
        problemas.append(f"falta la transcripción en {proy.insumo('transcripcion')}")

    # --- fichas de lectura (opcionales) ---
    fichas = rutas.todos_los_archivos(proy.insumo("fichas"))
    if fichas:
        consola.ok(f"Fichas de lectura: {len(fichas)} ({', '.join(f.name for f in fichas)})")
    else:
        avisos.append("no hay fichas de lectura; el guion se apoyará solo en la transcripción")

    # --- diapositivas ---
    dir_slides = proy.insumo("slides")
    if not dir_slides.is_dir():
        problemas.append(f"no existe la carpeta de diapositivas: {dir_slides}")
    else:
        imagenes = rutas.descubrir_slides(dir_slides)
        if not imagenes:
            problemas.append(f"no hay imágenes numeradas en {dir_slides}")
        else:
            consola.ok(f"Diapositivas: {len(imagenes)}, en este orden:")
            for i, img in enumerate(imagenes, start=1):
                limpio = rutas.normalizar_nombre(img.name)
                invisible = " [dim](tenía caracteres invisibles)[/]" if limpio != img.name else ""
                consola.info(f"    {i:>2}. {limpio}{invisible}")
            numeros = [rutas.numero_de(p) for p in imagenes]
            if numeros != sorted(set(numeros)):
                problemas.append(f"números de diapositiva repetidos: {numeros}")

    # --- ffmpeg ---
    tiene_ffmpeg, tiene_ffprobe = ffmpeg.disponible()
    if tiene_ffmpeg and tiene_ffprobe:
        consola.ok("ffmpeg y ffprobe disponibles")
    else:
        problemas.append("faltan ffmpeg/ffprobe. Instalar con: brew install ffmpeg")

    # --- credencial y modelo de OpenAI ---
    clave = config.clave_openai()
    if not clave:
        avisos.append(
            "no hay OPENAI_API_KEY (ni en el entorno ni en .env). "
            "Solo queda bloqueado el paso 02; el resto funciona igual."
        )
    else:
        modelo = proy.guion_cfg["modelo"]
        try:
            from openai import OpenAI

            disponibles = {m.id for m in OpenAI(api_key=clave).models.list()}
            if modelo in disponibles:
                consola.ok(f"OPENAI_API_KEY válida, con acceso a '{modelo}'")
            else:
                avisos.append(
                    f"tu clave no lista el modelo '{modelo}'. "
                    "Cambiá 'guion.modelo' en proyecto.yaml por uno al que tengas acceso."
                )
        except Exception as exc:
            avisos.append(f"no se pudo verificar la clave de OpenAI: {exc}")

    # --- resumen ---
    consola.info("")
    for a in avisos:
        consola.aviso(a)
    if problemas:
        for p in problemas:
            consola.error(p)
        consola.error(f"\n{len(problemas)} problema(s) que impiden continuar.")
        return 1

    proy.crear_carpetas()
    consola.ok("Todo listo.")
    consola.siguiente(f"python 01_preparar_slides.py --proyecto {args.proyecto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
