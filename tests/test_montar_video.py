"""Regresión: -shortest solo no corta el video al terminar el audio.

Con la imagen en loop infinito, el lookahead de libx264 (B-frames +
rc-lookahead) sigue generando fotogramas después de que el audio terminó,
agregando ~1-2s de más por segmento (~27s en un video de 15 segmentos). El fix
es pasar "-t <duración real del audio>" además de "-shortest".
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import importlib.util

_spec = importlib.util.spec_from_file_location("paso05", Path(__file__).resolve().parent.parent / "05_montar_video.py")
paso05 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(paso05)


def test_montar_segmento_pasa_dash_t_con_duracion_del_audio(monkeypatch, tmp_path):
    llamados = []
    monkeypatch.setattr(paso05.ffmpeg, "correr", lambda args: llamados.append(args))
    monkeypatch.setattr(paso05.ffmpeg, "duracion", lambda ruta: 55.584)

    cfg = {"ancho": 1920, "alto": 1080, "fps": 30, "codec_video": "libx264",
           "codec_audio": "aac", "bitrate_audio": "192k", "crf": 20,
           "movimiento": "ninguno", "umbral_movimiento_seg": 90}

    paso05.montar_segmento(
        seg=None, imagen=tmp_path / "slide_01.png", audio=tmp_path / "slide_01.mp3",
        destino=tmp_path / "slide_01.mp4", cfg=cfg,
    )

    assert len(llamados) == 1
    args = llamados[0]
    assert "-t" in args, "sin -t, el video puede quedar ~1-2s más largo que el audio"
    assert args[args.index("-t") + 1] == "55.584"
    # -shortest se mantiene como resguardo adicional, no como único corte.
    assert "-shortest" in args
