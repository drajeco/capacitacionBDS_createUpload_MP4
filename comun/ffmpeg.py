"""Envoltorios de ffmpeg/ffprobe."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class FaltaFfmpeg(RuntimeError):
    pass


class ErrorFfmpeg(RuntimeError):
    pass


def disponible() -> tuple[bool, bool]:
    return shutil.which("ffmpeg") is not None, shutil.which("ffprobe") is not None


def _exigir(binario: str) -> str:
    ruta = shutil.which(binario)
    if ruta is None:
        raise FaltaFfmpeg(f"'{binario}' no está en el PATH. Instalar con: brew install ffmpeg")
    return ruta


def correr(argumentos: list[str]) -> subprocess.CompletedProcess:
    """Ejecuta ffmpeg y levanta ErrorFfmpeg con las últimas líneas del log.

    ffmpeg escribe cientos de líneas en stderr aun cuando todo sale bien, así
    que en el error solo se muestran las finales, que son las que explican qué
    falló.
    """
    cmd = [_exigir("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", *argumentos]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        cola = "\n".join(proc.stderr.strip().splitlines()[-12:])
        raise ErrorFfmpeg(f"ffmpeg falló (código {proc.returncode}):\n{cola}")
    return proc


def duracion(archivo: Path) -> float:
    """Duración en segundos de un audio o video, según ffprobe."""
    cmd = [
        _exigir("ffprobe"),
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(archivo),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ErrorFfmpeg(f"ffprobe no pudo leer {archivo.name}: {proc.stderr.strip()}")
    try:
        return float(json.loads(proc.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise ErrorFfmpeg(f"ffprobe devolvió una duración ilegible para {archivo.name}") from exc


def info_video(archivo: Path) -> dict:
    """Códecs, resolución y fps del MP4 final, para el control de calidad."""
    cmd = [
        _exigir("ffprobe"),
        "-v", "error",
        "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate",
        "-show_entries", "format=duration,size",
        "-of", "json",
        str(archivo),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ErrorFfmpeg(f"ffprobe no pudo analizar {archivo.name}: {proc.stderr.strip()}")
    datos = json.loads(proc.stdout)
    resumen: dict = {"duracion": float(datos.get("format", {}).get("duration", 0.0))}
    resumen["tamano_bytes"] = int(datos.get("format", {}).get("size", 0))
    for stream in datos.get("streams", []):
        if stream.get("codec_type") == "video":
            resumen["video_codec"] = stream.get("codec_name")
            resumen["ancho"] = stream.get("width")
            resumen["alto"] = stream.get("height")
            tasa = stream.get("r_frame_rate", "0/1")
            num, _, den = tasa.partition("/")
            resumen["fps"] = round(int(num) / int(den or 1), 3) if den not in ("", "0") else None
        elif stream.get("codec_type") == "audio":
            resumen["audio_codec"] = stream.get("codec_name")
    return resumen


def captura(video: Path, segundo: float, destino: Path, ancho: int = 640) -> None:
    """Extrae un fotograma en un instante dado, para el reporte de QC."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    correr([
        "-ss", f"{segundo:.3f}",
        "-i", str(video),
        "-frames:v", "1",
        "-vf", f"scale={ancho}:-2",
        str(destino),
    ])


def silencio(destino: Path, segundos: float) -> None:
    """Genera un audio mudo. Sirve para probar el montaje sin gastar TTS."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    correr([
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", f"{segundos:.3f}",
        "-c:a", "libmp3lame", "-b:a", "128k",
        str(destino),
    ])


_CODEC_POR_FORMATO = {
    "mp3": "libmp3lame",
    "wav": "pcm_s16le",
    "aac": "aac",
    "m4a": "aac",
}

_MUXER_POR_FORMATO = {
    "mp3": "mp3",
    "wav": "wav",
    "aac": "adts",
    "m4a": "ipod",
}


def anteponer_silencio(origen: Path, destino: Path, segundos: float, formato: str = "mp3") -> None:
    """Agrega `segundos` de silencio real al principio de un audio ya sintetizado.

    Usa el filtro "adelay" (un solo input, sin generar y concatenar un archivo
    de silencio aparte). Sirve para marcar la transición al inicio de cada
    diapositiva sin depender de que el proveedor de voz soporte pausas: no
    todos aceptan SSML desde su API pública, así que esto se aplica después de
    sintetizar, igual que el léxico de pronunciación.
    """
    if segundos <= 0:
        raise ValueError("anteponer_silencio necesita segundos > 0")
    ms = round(segundos * 1000)
    formato = formato.lower()
    codec = _CODEC_POR_FORMATO.get(formato, "libmp3lame")
    # El sufijo ".parcial" de la escritura atómica rompe la detección de
    # formato por extensión, así que el muxer se indica explícito con "-f".
    muxer = _MUXER_POR_FORMATO.get(formato, "mp3")
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.name + ".parcial")
    correr([
        "-i", str(origen),
        "-af", f"adelay={ms}|{ms}",
        "-c:a", codec,
        "-f", muxer,
        str(tmp),
    ])
    tmp.replace(destino)
