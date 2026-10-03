"""Carga de proyecto.yaml y argumentos comunes a los scripts."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent

_DEFECTOS: dict = {
    "proyecto": {"nombre": "contenido", "titulo": "", "idioma": "es-AR"},
    "insumos": {
        "slides": "01_materialOriginal/slides",
        "transcripcion": "01_materialOriginal/exposicion",
        "fichas": "01_materialOriginal/fichas_lectura",
        "bibliografia": "01_materialOriginal/material_bibliográfico",
    },
    "salidas": {
        "guion": "02_archivosIntermedios/guion/guion_maestro.md",
        "slides": "02_archivosIntermedios/slides",
        "textos": "02_archivosIntermedios/text_files",
        "audios": "02_archivosIntermedios/audio_files",
        "segmentos": "02_archivosIntermedios/video_segmentos",
        "video": "03_output/video_final.mp4",
        "qc": "03_output/qc",
        "youtube": "03_output/youtube.txt",
        "miniatura": "03_output/miniatura.png",
        "cuestionario": "03_output/cuestionario.txt",
        "cuestionario_resuelto": "03_output/cuestionario_resuelto.txt",
    },
    "guion": {
        "modelo": "gpt-5.4",
        "esfuerzo": "high",
        "max_output_tokens": 32000,
        "duracion_objetivo_min": 18,
        "reglas": "",
        "max_segmentos_por_slide": 4,
        "palabras_por_segmento": 220,
        # El primer segmento de cada diapositiva abre con una frase de
        # transición propia, redactada por el modelo (no el título literal).
        "transicion_titulo": True,
    },
    "audio": {
        "proveedor": "edge",
        "voz": "es-AR-TomasNeural",
        "formato": "mp3",
        "concurrencia": 4,
        "lexico": "config/lexico.yaml",
        # Silencio real antepuesto al audio del primer segmento de cada
        # diapositiva, para marcar el cambio de imagen. 0 lo desactiva.
        "pausa_inicial_seg": 0.7,
    },
    "video": {
        "ancho": 1920,
        "alto": 1080,
        "fps": 30,
        "codec_video": "libx264",
        "codec_audio": "aac",
        "bitrate_audio": "192k",
        "movimiento": "ninguno",
        "umbral_movimiento_seg": 90,
    },
    "drive": {
        "carpeta_id": "",
        "credenciales": "credentials.json",
        "incluir_intermedios": True,
    },
    "cuestionario": {
        "modelo": "gpt-5.4",
        "esfuerzo": "high",
        "max_output_tokens": 18000,
        "reglas": "",
    },
    "youtube": {
        "modelo": "gpt-5.4",
        "esfuerzo": "medium",
        "max_output_tokens": 6000,
        "reglas": "",
    },
    "qc": {"min_seg": 5, "max_seg": 300, "capturas": 8},
}


def _fusionar(base: dict, encima: dict) -> dict:
    salida = dict(base)
    for clave, valor in (encima or {}).items():
        if isinstance(valor, dict) and isinstance(salida.get(clave), dict):
            salida[clave] = _fusionar(salida[clave], valor)
        else:
            salida[clave] = valor
    return salida


@dataclass
class Proyecto:
    """proyecto.yaml resuelto, con todas las rutas ya absolutas."""

    base: Path
    datos: dict

    # --- secciones ---
    @property
    def nombre(self) -> str:
        return self.datos["proyecto"]["nombre"]

    @property
    def titulo(self) -> str:
        guion = self.salida("guion")
        if guion.is_file():
            for linea in guion.read_text(encoding="utf-8").splitlines():
                prefijo = "# Guion de locución — "
                if linea.startswith(prefijo):
                    return linea[len(prefijo):].strip()
        return ""

    @property
    def idioma(self) -> str:
        return self.datos["proyecto"]["idioma"]

    @property
    def guion_cfg(self) -> dict:
        return self.datos["guion"]

    @property
    def audio_cfg(self) -> dict:
        return self.datos["audio"]

    @property
    def video_cfg(self) -> dict:
        return self.datos["video"]

    @property
    def qc_cfg(self) -> dict:
        return self.datos["qc"]

    # --- rutas ---
    def insumo(self, clave: str) -> Path:
        return self.base / self.datos["insumos"][clave]

    def salida(self, clave: str) -> Path:
        return self.base / self.datos["salidas"][clave]

    @property
    def lexico(self) -> Path:
        return RAIZ / self.datos["audio"]["lexico"]

    def crear_carpetas(self) -> None:
        for clave in ("slides", "textos", "audios", "segmentos", "qc"):
            self.salida(clave).mkdir(parents=True, exist_ok=True)
        self.salida("guion").parent.mkdir(parents=True, exist_ok=True)
        self.salida("video").parent.mkdir(parents=True, exist_ok=True)


def cargar(carpeta_proyecto: str | Path) -> Proyecto:
    base = Path(carpeta_proyecto)
    if not base.is_absolute():
        base = RAIZ / base
    base = base.resolve()
    if not base.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de proyecto: {base}")

    archivo = base / "proyecto.yaml"
    propios = {}
    if archivo.is_file():
        propios = yaml.safe_load(archivo.read_text(encoding="utf-8")) or {}
    return Proyecto(base=base, datos=_fusionar(_DEFECTOS, propios))


def parser(descripcion: str, con_segmentos: bool = False) -> argparse.ArgumentParser:
    """Argumentos idénticos en los scripts."""
    p = argparse.ArgumentParser(description=descripcion)
    p.add_argument("--proyecto", default="01_content", help="carpeta del video (por defecto 01_content)")
    p.add_argument("--forzar", action="store_true", help="rehace lo ya generado")
    if con_segmentos:
        p.add_argument(
            "--segmentos",
            nargs="+",
            default=None,
            metavar="N",
            help="procesar solo estas diapositivas (ej: --segmentos 1 2)",
        )
    return p


def clave_openai() -> str | None:
    """OPENAI_API_KEY del entorno o del .env de la raíz del proyecto."""
    if clave := os.environ.get("OPENAI_API_KEY"):
        return clave.strip()
    env = RAIZ / ".env"
    if env.is_file():
        for linea in env.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea.startswith("OPENAI_API_KEY="):
                valor = linea.split("=", 1)[1].strip().strip("'\"")
                if valor and not valor.startswith("sk-..."):
                    return valor
    return None
