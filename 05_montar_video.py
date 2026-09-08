#!/usr/bin/env python3
"""Paso 05 - Monta el MP4 final: cada diapositiva dura lo que dura su audio.

El montaje va en dos fases. Primero un MP4 por segmento, generando fotogramas
reales durante toda la duración del audio: dar una sola imagen sin fotogramas
es lo que produjo el video congelado en la portada de la prueba manual. Después
se concatenan sin recodificar.

    python 05_montar_video.py --proyecto 01_content
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from comun import config, consola, ffmpeg, modelo


def filtro_video(cfg: dict, duracion: float) -> str:
    """Escalado con barras y, si corresponde, deriva lenta tipo Ken Burns.

    El scale+pad no es opcional: las diapositivas de 1672x941 no son 16:9
    exacto, y sin esto ffmpeg deforma la imagen o falla por dimensión impar.
    """
    ancho, alto, fps = cfg["ancho"], cfg["alto"], cfg["fps"]
    cadena = [
        f"scale={ancho}:{alto}:force_original_aspect_ratio=decrease",
        f"pad={ancho}:{alto}:(ow-iw)/2:(oh-ih)/2",
        "setsar=1",
    ]

    if cfg.get("movimiento", "ninguno") == "kenburns" and duracion >= cfg["umbral_movimiento_seg"]:
        fotogramas = max(int(duracion * fps), 1)
        # Zoom muy lento del 100% al 108%. Se sobremuestrea antes del zoompan
        # porque si no el filtro produce un temblor visible.
        cadena = [
            f"scale={ancho * 2}:{alto * 2}:force_original_aspect_ratio=decrease",
            f"pad={ancho * 2}:{alto * 2}:(ow-iw)/2:(oh-ih)/2",
            (
                f"zoompan=z='min(1.08,1+0.08*on/{fotogramas})'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={fotogramas}:s={ancho}x{alto}:fps={fps}"
            ),
            "setsar=1",
        ]
    return ",".join(cadena)


def montar_segmento(seg: modelo.Segmento, imagen: Path, audio: Path, destino: Path, cfg: dict) -> float:
    dur = ffmpeg.duracion(audio)
    ffmpeg.correr([
        "-loop", "1",
        "-framerate", str(cfg["fps"]),
        "-i", str(imagen),
        "-i", str(audio),
        "-vf", filtro_video(cfg, dur),
        "-c:v", cfg["codec_video"],
        "-preset", "medium",
        "-crf", str(cfg.get("crf", 20)),
        "-pix_fmt", "yuv420p",
        "-r", str(cfg["fps"]),
        "-c:a", cfg["codec_audio"],
        "-b:a", cfg["bitrate_audio"],
        "-ar", "44100", "-ac", "2",
        # "-shortest" solo no alcanza: con la imagen en loop infinito, el
        # lookahead de libx264 (B-frames + rc-lookahead) sigue metiendo
        # fotogramas después de que el audio terminó, agregando ~1-2s de más
        # por segmento. "-t" con la duración real del audio corta exacto.
        "-t", f"{dur:.3f}",
        "-shortest",
        "-movflags", "+faststart",
        str(destino),
    ])
    return dur


def validar_activos(proy, segmentos: list[modelo.Segmento], formato: str) -> list[str]:
    """Antes de montar: que texto, imagen y audio coincidan exactamente."""
    problemas = []
    for seg in segmentos:
        imagen = proy.salida("slides") / f"{seg.id_slide}.png"
        audio = proy.salida("audios") / f"{seg.id}.{formato}"
        if not imagen.is_file():
            problemas.append(f"{seg.etiqueta}: falta la imagen {imagen.name}")
        if not audio.is_file():
            problemas.append(f"{seg.etiqueta}: falta el audio {audio.name}")
            continue
        try:
            if ffmpeg.duracion(audio) <= 0:
                problemas.append(f"{seg.etiqueta}: el audio {audio.name} dura 0 segundos")
        except ffmpeg.ErrorFfmpeg as exc:
            problemas.append(f"{seg.etiqueta}: {exc}")

    # Audios sin texto: sobra un audio de una corrida anterior.
    ids_texto = {s.id for s in segmentos}
    for audio in sorted(proy.salida("audios").glob(f"*.{formato}")):
        if audio.stem not in ids_texto:
            problemas.append(f"sobra el audio {audio.name}: no tiene texto correspondiente")
    return problemas


def main() -> int:
    args = config.parser(__doc__).parse_args()
    proy = config.cargar(args.proyecto)
    consola.titulo("Paso 05", f"Montar video · {proy.nombre}")

    cfg = proy.video_cfg
    formato = proy.audio_cfg["formato"]

    segmentos = modelo.descubrir_segmentos(proy.salida("textos"), ".txt")
    if not segmentos:
        consola.abortar(
            f"No hay textos de locución en {proy.salida('textos')}.\n"
            f"  Correr antes: python 03_dividir_guion.py --proyecto {args.proyecto}"
        )

    problemas = validar_activos(proy, segmentos, formato)
    if problemas:
        for p in problemas:
            consola.error(p)
        consola.abortar(
            f"\n{len(problemas)} inconsistencia(s) entre textos, imágenes y audios. "
            "Se corta acá antes que producir un video incompleto."
        )
    consola.ok(f"{len(segmentos)} segmentos consistentes (texto + imagen + audio)")

    # --- fase 1: un MP4 por segmento ---
    dir_segmentos = proy.salida("segmentos")
    dir_segmentos.mkdir(parents=True, exist_ok=True)
    total = 0.0
    rehechos = 0

    for seg in segmentos:
        parcial = dir_segmentos / f"{seg.id}.mp4"
        imagen = proy.salida("slides") / f"{seg.id_slide}.png"
        audio = proy.salida("audios") / f"{seg.id}.{formato}"

        # Se rehace si el audio o la imagen son más nuevos que el MP4 parcial.
        vigente = (
            parcial.is_file()
            and not args.forzar
            and parcial.stat().st_mtime >= max(audio.stat().st_mtime, imagen.stat().st_mtime)
        )
        if vigente:
            total += ffmpeg.duracion(parcial)
            continue

        try:
            dur = montar_segmento(seg, imagen, audio, parcial, cfg)
        except ffmpeg.ErrorFfmpeg as exc:
            consola.abortar(f"{seg.etiqueta}: {exc}")
        total += dur
        rehechos += 1
        consola.info(f"  [green]·[/] {seg.id}  {dur:6.1f}s")

    if rehechos == 0:
        consola.info("  [dim]todos los segmentos ya estaban montados (--forzar para rehacer)[/]")

    # --- fase 2: concatenación sin recodificar ---
    salida = proy.salida("video")
    salida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as lista:
        for seg in segmentos:
            ruta = str((dir_segmentos / f"{seg.id}.mp4").resolve()).replace("'", r"'\''")
            lista.write(f"file '{ruta}'\n")
        ruta_lista = lista.name

    try:
        ffmpeg.correr([
            "-f", "concat", "-safe", "0", "-i", ruta_lista,
            "-c", "copy", "-movflags", "+faststart",
            str(salida),
        ])
    except ffmpeg.ErrorFfmpeg as exc:
        consola.abortar(f"falló la concatenación: {exc}")
    finally:
        Path(ruta_lista).unlink(missing_ok=True)

    info = ffmpeg.info_video(salida)
    minutos, segundos = divmod(info["duracion"], 60)
    consola.ok(
        f"{salida.name}: {int(minutos)}m {segundos:04.1f}s · "
        f"{info.get('ancho')}x{info.get('alto')} · {info.get('fps')} fps · "
        f"{info.get('video_codec')}/{info.get('audio_codec')} · "
        f"{info['tamano_bytes'] / 1e6:.1f} MB"
    )

    desvio = abs(info["duracion"] - total)
    if desvio > 1.0:
        consola.aviso(
            f"la duración del MP4 difiere {desvio:.2f}s de la suma de los audios "
            f"({total:.1f}s). Revisá el reporte del paso 06."
        )

    consola.siguiente(f"python 06_control_calidad.py --proyecto {args.proyecto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
