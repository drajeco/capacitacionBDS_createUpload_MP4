#!/usr/bin/env python3
"""Paso 03 - Parte el guion aprobado en un archivo de texto por segmento.

Lee el guion_maestro.md ya revisado (y editado, si hizo falta) y escribe un
.txt por segmento con solo el texto que va a leer la voz. Falla ante cualquier
ambigüedad en vez de adivinar: un guion mal dividido produce audios
desalineados que recién se notan mirando el video terminado.

    python 03_dividir_guion.py --proyecto 01_content
"""

from __future__ import annotations

import sys

from comun import config, consola, guion as guion_mod, modelo, rutas


def main() -> int:
    args = config.parser(__doc__).parse_args()
    proy = config.cargar(args.proyecto)
    consola.titulo("Paso 03", f"Dividir guion · {proy.nombre}")

    origen = proy.salida("guion")
    if not origen.is_file():
        consola.abortar(
            f"No existe {origen}.\n"
            f"  Correr antes: python 02_escribir_guion.py --proyecto {args.proyecto}"
        )

    try:
        segmentos = guion_mod.parsear(origen.read_text(encoding="utf-8"))
    except guion_mod.GuionInvalido as exc:
        consola.abortar(f"{origen.name}: {exc}")

    # --- correspondencia con las diapositivas reales ---
    imagenes = rutas.descubrir_slides(proy.salida("slides"))
    if not imagenes:
        consola.abortar(
            f"No hay diapositivas en {proy.salida('slides')}.\n"
            f"  Correr antes: python 01_preparar_slides.py --proyecto {args.proyecto}"
        )
    disponibles = set(range(1, len(imagenes) + 1))

    if sin_imagen := sorted({s.slide for s in segmentos} - disponibles):
        consola.abortar(
            f"el guion narra las diapositivas {sin_imagen}, que no existen "
            f"(hay {len(imagenes)}). Corregí los encabezados '## Diapositiva NN'."
        )
    if sin_narrar := sorted(disponibles - {s.slide for s in segmentos}):
        consola.aviso(
            f"las diapositivas {sin_narrar} no tienen narración y no van a aparecer en el video"
        )

    # --- escritura ---
    destino_dir = proy.salida("textos")
    destino_dir.mkdir(parents=True, exist_ok=True)

    # Se limpian los .txt de corridas anteriores: si el guion editado tiene
    # menos segmentos, los sobrantes generarían audio y video de más.
    previos = {p.stem for p in destino_dir.glob("*.txt")}
    actuales = {s.id for s in segmentos}
    for obsoleto in sorted(previos - actuales):
        (destino_dir / f"{obsoleto}.txt").unlink()
        consola.info(f"  [dim]- {obsoleto}.txt (ya no está en el guion)[/]")

    total_palabras = 0
    for seg in segmentos:
        rutas.escribir_atomico(destino_dir / f"{seg.id}.txt", seg.narracion.strip() + "\n")
        total_palabras += len(seg.narracion.split())

    consola.ok(f"{len(segmentos)} textos de locución en {destino_dir.name}/")

    por_slide: dict[int, int] = {}
    for s in segmentos:
        por_slide[s.slide] = por_slide.get(s.slide, 0) + 1
    detalle = ", ".join(
        f"d{n:02d}×{c}" if c > 1 else f"d{n:02d}" for n, c in sorted(por_slide.items())
    )
    consola.info(f"  [dim]{detalle}[/]")
    consola.ok(f"{total_palabras:,} palabras · ~{total_palabras / 150:.0f} min de locución estimados")

    consola.info(
        "\n[bold]Antes de generar todos los audios[/], probá la voz con dos diapositivas."
    )
    consola.siguiente(f"python 04_crear_audios.py --proyecto {args.proyecto} --segmentos 1 2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
