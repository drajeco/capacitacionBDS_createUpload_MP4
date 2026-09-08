#!/usr/bin/env python3
"""Paso 04 - Convierte cada texto de locución en un audio.

Un audio por segmento, no uno solo largo: así cada diapositiva dura exactamente
lo que dura su narración, se puede rehacer un tramo sin regenerar todo, y los
errores se detectan segmento por segmento.

Antes de sintetizar se aplica el diccionario de pronunciación (config/lexico.yaml),
para que las siglas y los términos en inglés suenen bien sin ensuciar el guion.

    python 04_crear_audios.py --proyecto 01_content --segmentos 1 2   # probar la voz
    python 04_crear_audios.py --proyecto 01_content                   # todo
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor

from comun import config, consola, ffmpeg, lexico as lexico_mod, modelo, voz as voz_mod


def main() -> int:
    args = config.parser(__doc__, con_segmentos=True).parse_args()
    proy = config.cargar(args.proyecto)
    consola.titulo("Paso 04", f"Generar audios · {proy.nombre}")

    cfg = proy.audio_cfg
    formato = cfg["formato"]
    dir_textos = proy.salida("textos")
    dir_audios = proy.salida("audios")
    dir_audios.mkdir(parents=True, exist_ok=True)

    segmentos = modelo.descubrir_segmentos(dir_textos, ".txt")
    if not segmentos:
        consola.abortar(
            f"No hay textos de locución en {dir_textos}.\n"
            f"  Correr antes: python 03_dividir_guion.py --proyecto {args.proyecto}"
        )

    if args.segmentos:
        try:
            pedidos = {int(n) for n in args.segmentos}
        except ValueError:
            consola.abortar("--segmentos espera números de diapositiva (ej: --segmentos 1 2)")
        segmentos = [s for s in segmentos if s.slide in pedidos]
        if not segmentos:
            consola.abortar(f"Ninguna diapositiva coincide con {sorted(pedidos)}")
        consola.info(f"[dim]Solo diapositivas {sorted(pedidos)}[/]")

    # --- léxico de pronunciación ---
    lex = lexico_mod.Lexico.desde_archivo(proy.lexico)
    if len(lex):
        consola.ok(f"Léxico: {len(lex)} reglas de pronunciación desde {proy.lexico.name}")
    else:
        consola.aviso(f"sin léxico de pronunciación ({proy.lexico} no existe o está vacío)")

    # --- proveedor de voz ---
    try:
        proveedor = voz_mod.construir(cfg, clave_openai=config.clave_openai())
    except voz_mod.ErrorVoz as exc:
        consola.abortar(str(exc))
    consola.ok(f"Proveedor '{proveedor.nombre}' con la voz '{cfg.get('voz')}'")

    # --- pausa de transición al inicio de cada diapositiva ---
    pausa_seg = float(cfg.get("pausa_inicial_seg", 0) or 0)
    primeros = modelo.primeros_de_cada_slide(segmentos) if pausa_seg > 0 else set()
    if pausa_seg > 0:
        consola.ok(f"Pausa inicial: {pausa_seg:.2f}s en el primer segmento de cada diapositiva")

    pendientes = []
    for seg in segmentos:
        destino = dir_audios / f"{seg.id}.{formato}"
        texto = (dir_textos / f"{seg.id}.txt").read_text(encoding="utf-8").strip()
        if not texto:
            consola.abortar(f"{seg.etiqueta}: el texto de locución está vacío")
        if destino.is_file() and not args.forzar:
            continue
        pendientes.append((seg, lex.aplicar(texto), destino, seg.id in primeros))

    ya_estaban = len(segmentos) - len(pendientes)
    if not pendientes:
        consola.info(f"  [dim]los {ya_estaban} audios ya existen; usar --forzar para rehacerlos[/]")
    else:
        consola.info(f"Generando {len(pendientes)} audio(s)"
                     + (f", {ya_estaban} ya estaban" if ya_estaban else ""))

        fallos: list[str] = []

        def generar(item):
            seg, texto, destino, es_primero = item
            temporal = None
            try:
                if es_primero and pausa_seg > 0:
                    temporal = destino.with_name(f".tmp_{destino.name}")
                    proveedor.sintetizar(texto, temporal)
                    ffmpeg.anteponer_silencio(temporal, destino, pausa_seg, formato)
                else:
                    proveedor.sintetizar(texto, destino)
            except (voz_mod.ErrorVoz, ffmpeg.ErrorFfmpeg) as exc:
                return seg, None, str(exc)
            finally:
                if temporal is not None:
                    temporal.unlink(missing_ok=True)
            return seg, destino, None

        with ThreadPoolExecutor(max_workers=max(int(cfg.get("concurrencia", 4)), 1)) as pool:
            for seg, destino, error in pool.map(generar, pendientes):
                if error:
                    fallos.append(f"{seg.etiqueta}: {error}")
                    consola.error(f"  {seg.id}  {error}")
                else:
                    consola.info(f"  [green]·[/] {seg.id}  {ffmpeg.duracion(destino):6.1f}s")

        if fallos:
            consola.abortar(f"\n{len(fallos)} audio(s) fallaron. Volvé a correr el paso: "
                            "los que salieron bien no se regeneran.")

    # --- resumen de duraciones ---
    total = 0.0
    for seg in segmentos:
        archivo = dir_audios / f"{seg.id}.{formato}"
        if archivo.is_file():
            total += ffmpeg.duracion(archivo)
    minutos, segundos = divmod(total, 60)
    consola.ok(f"{len(segmentos)} audios · {int(minutos)}m {segundos:04.1f}s en total")

    if args.segmentos:
        consola.info(
            "\n[bold]Escuchá estos audios ahora[/]: ritmo, siglas y términos técnicos.\n"
            f"  [dim]open {dir_audios}[/]\n"
            "  Si algo suena mal, ajustá config/lexico.yaml o la voz en proyecto.yaml "
            "y repetí con --forzar."
        )
        consola.siguiente(f"python 04_crear_audios.py --proyecto {args.proyecto}")
    else:
        consola.siguiente(f"python 05_montar_video.py --proyecto {args.proyecto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
