"""Descubrimiento y normalización de rutas del proyecto.

Los PNG exportados desde Keynote/PowerPoint llegan con caracteres de control
bidireccional invisibles en el nombre (U+200E en el material de 01_content), y
el número de diapositiva no coincide con el orden alfabético en cuanto se pasa
de 9 slides. Todo el descubrimiento de archivos pasa por acá.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

# Marcas de dirección y de formato que Keynote/PowerPoint insertan al exportar.
_CONTROLES_BIDI = dict.fromkeys(
    [0x200E, 0x200F, 0x061C, 0x200B, 0xFEFF, *range(0x202A, 0x202F), *range(0x2066, 0x206A)]
)

_NUMERO_FINAL = re.compile(r"(\d+)(?!.*\d)")


def normalizar_nombre(nombre: str) -> str:
    """Quita controles bidi/invisibles y normaliza a NFC."""
    return unicodedata.normalize("NFC", nombre.translate(_CONTROLES_BIDI))


def numero_de(ruta: Path) -> int | None:
    """Último número del nombre de archivo, ignorando la extensión."""
    m = _NUMERO_FINAL.search(normalizar_nombre(ruta.stem))
    return int(m.group(1)) if m else None


def descubrir_slides(directorio: Path, extensiones=(".png", ".jpg", ".jpeg")) -> list[Path]:
    """Imágenes de diapositiva ordenadas por su número, no alfabéticamente.

    Devuelve las rutas reales en disco (con los caracteres invisibles intactos,
    que es como hay que abrirlas); la normalización solo se usa para leer el
    número. Los archivos sin número se descartan.
    """
    candidatos = [
        p
        for p in directorio.iterdir()
        if p.is_file() and p.suffix.lower() in extensiones and not p.name.startswith(".")
    ]
    numeradas = [(numero_de(p), p) for p in candidatos]
    return [p for n, p in sorted((n, p) for n, p in numeradas if n is not None)]


def primer_archivo(directorio: Path, extensiones=(".md", ".txt")) -> Path | None:
    """Primer archivo de texto de una carpeta de insumos, en orden estable."""
    if not directorio.is_dir():
        return None
    encontrados = sorted(
        p
        for p in directorio.iterdir()
        if p.is_file() and p.suffix.lower() in extensiones and not p.name.startswith(".")
    )
    return encontrados[0] if encontrados else None


def todos_los_archivos(directorio: Path, extensiones=(".md", ".txt")) -> list[Path]:
    if not directorio.is_dir():
        return []
    return sorted(
        p
        for p in directorio.iterdir()
        if p.is_file() and p.suffix.lower() in extensiones and not p.name.startswith(".")
    )


def escribir_atomico(destino: Path, contenido: str | bytes) -> None:
    """Escribe a un temporal y renombra, para no dejar archivos truncados.

    Un .txt o .mp3 a medio escribir pasaría las validaciones de existencia del
    paso siguiente y rompería recién en el montaje.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.name + ".parcial")
    modo, encoding = ("wb", None) if isinstance(contenido, bytes) else ("w", "utf-8")
    with open(tmp, modo, encoding=encoding) as f:
        f.write(contenido)
    tmp.replace(destino)
