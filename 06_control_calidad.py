#!/usr/bin/env python3
"""Paso 06 - Reporte de calidad del MP4 final.

Produce la evidencia que hay que mirar antes de publicar: duración por
segmento, capturas repartidas en la línea de tiempo (para confirmar que las
diapositivas efectivamente avanzan) y avisos sobre segmentos demasiado cortos o
demasiado largos.

    python 06_control_calidad.py --proyecto 01_content
"""

from __future__ import annotations

import sys
from datetime import datetime

from comun import config, consola, ffmpeg, modelo


def mmss(segundos: float) -> str:
    minutos, resto = divmod(segundos, 60)
    return f"{int(minutos):02d}:{resto:04.1f}"


def main() -> int:
    args = config.parser(__doc__).parse_args()
    proy = config.cargar(args.proyecto)
    consola.titulo("Paso 06", f"Control de calidad · {proy.nombre}")

    video = proy.salida("video")
    if not video.is_file():
        consola.abortar(
            f"No existe {video}.\n"
            f"  Correr antes: python 05_montar_video.py --proyecto {args.proyecto}"
        )

    cfg_qc = proy.qc_cfg
    formato = proy.audio_cfg["formato"]
    segmentos = modelo.descubrir_segmentos(proy.salida("textos"), ".txt")
    info = ffmpeg.info_video(video)

    # --- tabla por segmento ---
    filas = []
    acumulado = 0.0
    avisos: list[str] = []
    for seg in segmentos:
        audio = proy.salida("audios") / f"{seg.id}.{formato}"
        texto = proy.salida("textos") / f"{seg.id}.txt"
        dur = ffmpeg.duracion(audio) if audio.is_file() else 0.0
        palabras = len(texto.read_text(encoding="utf-8").split()) if texto.is_file() else 0
        ppm = (palabras / dur * 60) if dur else 0.0
        filas.append({
            "id": seg.id,
            "slide": seg.id_slide,
            "inicio": acumulado,
            "duracion": dur,
            "palabras": palabras,
            "ppm": ppm,
        })
        if dur and dur < cfg_qc["min_seg"]:
            avisos.append(f"{seg.etiqueta}: solo {dur:.1f}s, sospechosamente corto")
        if dur > cfg_qc["max_seg"]:
            avisos.append(
                f"{seg.etiqueta}: {mmss(dur)} con una imagen fija. "
                "Conviene subdividir el segmento o activar video.movimiento: kenburns"
            )
        acumulado += dur

    # --- capturas repartidas en la línea de tiempo ---
    dir_capturas = proy.salida("qc") / "capturas"
    for viejo in dir_capturas.glob("*.png"):
        viejo.unlink()
    cantidad = max(int(cfg_qc["capturas"]), 2)
    total = info["duracion"]
    # Se evitan los bordes exactos: en el último fotograma ffmpeg puede no
    # devolver imagen.
    instantes = [total * i / (cantidad - 1) for i in range(cantidad)]
    instantes[0], instantes[-1] = 0.5, max(total - 0.5, 0.0)

    capturas = []
    for i, t in enumerate(instantes, start=1):
        destino = dir_capturas / f"captura_{i:02d}_{int(t):05d}s.png"
        try:
            ffmpeg.captura(video, t, destino)
            capturas.append((t, destino))
        except ffmpeg.ErrorFfmpeg as exc:
            avisos.append(f"no se pudo capturar el segundo {t:.1f}: {exc}")

    # --- reporte ---
    ancho, alto = proy.video_cfg["ancho"], proy.video_cfg["alto"]
    resolucion_ok = (info.get("ancho"), info.get("alto")) == (ancho, alto)
    codecs_ok = info.get("video_codec") == "h264" and info.get("audio_codec") == "aac"
    desvio = abs(info["duracion"] - acumulado)

    lineas = [
        f"# Control de calidad - {proy.titulo or proy.nombre}",
        "",
        f"Generado: {datetime.now():%Y-%m-%d %H:%M}",
        f"Archivo: `{video.name}`",
        "",
        "## Resumen",
        "",
        "| Dato | Valor | |",
        "| --- | --- | --- |",
        f"| Duración total | {mmss(info['duracion'])} | |",
        f"| Resolución | {info.get('ancho')}x{info.get('alto')} | {'OK' if resolucion_ok else 'REVISAR'} |",
        f"| Fotogramas por segundo | {info.get('fps')} | |",
        f"| Códecs | {info.get('video_codec')} / {info.get('audio_codec')} | {'OK' if codecs_ok else 'REVISAR'} |",
        f"| Tamaño | {info['tamano_bytes'] / 1e6:.1f} MB | |",
        f"| Segmentos | {len(segmentos)} | |",
        f"| Suma de audios | {mmss(acumulado)} | {'OK' if desvio <= 1.0 else f'desvío {desvio:.2f}s'} |",
        "",
        "## Duración por segmento",
        "",
        "| Segmento | Diapositiva | Inicio | Duración | Palabras | Palabras/min |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for f in filas:
        lineas.append(
            f"| `{f['id']}` | `{f['slide']}` | {mmss(f['inicio'])} | {mmss(f['duracion'])} "
            f"| {f['palabras']} | {f['ppm']:.0f} |"
        )

    lineas += ["", "## Avisos", ""]
    lineas += [f"- {a}" for a in avisos] if avisos else ["- Sin avisos."]

    lineas += [
        "",
        "## Capturas de control",
        "",
        "Confirmar que muestran diapositivas **distintas** a lo largo del video "
        "y que la última no es la portada.",
        "",
    ]
    lineas += [f"- `{d.name}` (segundo {t:.1f})" for t, d in capturas]
    lineas += [
        "",
        "## Revisión manual pendiente",
        "",
        "- [ ] Escuchar inicio, un tramo central y el cierre.",
        "- [ ] Verificar la pronunciación de siglas y términos técnicos.",
        "- [ ] Confirmar que el guion no menciona clases, reuniones ni contenido previo.",
        "- [ ] Confirmar que el audio no se corta al final de ningún segmento.",
        "",
    ]

    reporte = proy.salida("qc") / "reporte.md"
    reporte.write_text("\n".join(lineas), encoding="utf-8")

    # --- salida por consola ---
    consola.ok(f"Duración total: {mmss(info['duracion'])} en {len(segmentos)} segmentos")
    ficha = (f"{info.get('ancho')}x{info.get('alto')} · {info.get('fps')} fps · "
             f"{info.get('video_codec')}/{info.get('audio_codec')}")
    if resolucion_ok and codecs_ok:
        consola.ok(ficha)
    else:
        consola.aviso(f"{ficha} — no coincide con lo configurado en proyecto.yaml")
    consola.ok(f"{len(capturas)} capturas en {dir_capturas}")
    for a in avisos:
        consola.aviso(a)
    consola.ok(f"Reporte: {reporte}")
    consola.info(
        "\n[bold]Abrí las capturas[/] y confirmá que las diapositivas avanzan "
        "y que la última no es la portada."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
