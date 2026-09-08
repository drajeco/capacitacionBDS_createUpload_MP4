"""Unidad central del pipeline: el segmento de narración."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class Segmento:
    """Un tramo de locución asociado a una diapositiva.

    Una diapositiva puede tener varios segmentos (sufijos "a", "b", ...) para
    que una imagen no quede fija durante varios minutos. El identificador del
    segmento nombra el .txt, el audio y el MP4 parcial; ``id_slide`` nombra el
    PNG, que varios segmentos pueden compartir.
    """

    slide: int
    sufijo: str = ""
    titulo: str = ""
    narracion: str = ""

    @property
    def id(self) -> str:
        base = f"slide_{self.slide:02d}"
        return f"{base}_{self.sufijo}" if self.sufijo else base

    @property
    def id_slide(self) -> str:
        return f"slide_{self.slide:02d}"

    @property
    def etiqueta(self) -> str:
        """Nombre legible para reportes y mensajes de error."""
        if self.sufijo:
            return f"Diapositiva {self.slide:02d}, segmento {self.sufijo}"
        return f"Diapositiva {self.slide:02d}"


_ID_SEGMENTO = re.compile(r"^slide_(\d+)(?:_([a-z]+))?$", re.IGNORECASE)


def desde_id(identificador: str) -> Segmento:
    """Reconstruye un Segmento a partir de 'slide_03' o 'slide_03_a'."""
    m = _ID_SEGMENTO.match(identificador)
    if not m:
        raise ValueError(f"identificador de segmento inválido: '{identificador}'")
    return Segmento(slide=int(m.group(1)), sufijo=(m.group(2) or "").lower())


def descubrir_segmentos(directorio: Path, extension: str) -> list[Segmento]:
    """Segmentos presentes en una carpeta, ordenados por diapositiva y sufijo.

    Se usa para enumerar los .txt y los audios ya generados sin volver a
    parsear el guion.
    """
    if not directorio.is_dir():
        return []
    encontrados = []
    for archivo in directorio.iterdir():
        if not archivo.is_file() or archivo.suffix.lower() != extension.lower():
            continue
        try:
            encontrados.append(desde_id(archivo.stem))
        except ValueError:
            continue
    return sorted(encontrados)


def primeros_de_cada_slide(segmentos: list[Segmento]) -> set[str]:
    """IDs de los segmentos que abren su diapositiva (el primero al ordenar).

    Es el segmento que coincide con el cambio de imagen: el que no tiene
    sufijo, o el "a" cuando la diapositiva se subdividió. Los b, c... de la
    misma diapositiva comparten PNG con el anterior y no cuentan como apertura.
    Se calcula por orden en vez de mirar el sufijo textual ("" vs "a") para no
    depender de esa convención en ningún otro lugar del pipeline.
    """
    vistos: set[int] = set()
    primeros: set[str] = set()
    for seg in sorted(segmentos):
        if seg.slide not in vistos:
            primeros.add(seg.id)
            vistos.add(seg.slide)
    return primeros
