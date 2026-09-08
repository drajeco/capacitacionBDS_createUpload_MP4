"""Diccionario de pronunciación aplicado justo antes de sintetizar la voz.

El guion se mantiene legible en castellano normal ("LCR", "cash flow") y la
corrección fonética vive acá, en un solo lugar para todos los videos. Así
revisar el guion sigue siendo cómodo y cambiar de motor de voz no obliga a
reescribirlo.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


class Lexico:
    def __init__(self, siglas: dict[str, str] | None = None, terminos: dict[str, str] | None = None):
        self.siglas = siglas or {}
        self.terminos = terminos or {}
        self._reglas = self._compilar()

    @classmethod
    def desde_archivo(cls, ruta: Path) -> "Lexico":
        if not ruta.is_file():
            return cls()
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
        return cls(siglas=datos.get("siglas") or {}, terminos=datos.get("terminos") or {})

    def _compilar(self) -> list[tuple[re.Pattern, str]]:
        reglas: list[tuple[re.Pattern, str]] = []
        # Las siglas distinguen mayúsculas: "LCR" se reemplaza, "lcr" dentro de
        # otra palabra no. Los términos no las distinguen.
        for origen, destino in sorted(self.siglas.items(), key=lambda kv: -len(kv[0])):
            reglas.append((re.compile(rf"\b{re.escape(origen)}\b"), destino))
        for origen, destino in sorted(self.terminos.items(), key=lambda kv: -len(kv[0])):
            reglas.append((re.compile(rf"\b{re.escape(origen)}\b", re.IGNORECASE), destino))
        return reglas

    def aplicar(self, texto: str) -> str:
        for patron, destino in self._reglas:
            texto = patron.sub(destino.replace("\\", r"\\"), texto)
        return texto

    def __len__(self) -> int:
        return len(self.siglas) + len(self.terminos)
