"""Proveedores de síntesis de voz, intercambiables desde proyecto.yaml.

Todos exponen el mismo método síncrono ``sintetizar``. El paralelismo lo maneja
04_crear_audios.py con un pool de hilos, así el pipeline no cambia al cambiar
de motor.
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Protocol


class ErrorVoz(RuntimeError):
    pass


class ProveedorVoz(Protocol):
    nombre: str

    def sintetizar(self, texto: str, destino: Path) -> None: ...


def _guardar_atomico(destino: Path, datos: bytes) -> None:
    """Un audio a medio escribir pasaría la validación de existencia del paso
    siguiente y rompería recién en el montaje: se escribe temporal y se renombra."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.name + ".parcial")
    tmp.write_bytes(datos)
    tmp.replace(destino)


class VozEdge:
    """edge-tts: gratis, sin credenciales, voces neuronales en español."""

    nombre = "edge"

    def __init__(self, voz: str = "es-UY-ValentinaNeural", velocidad: str = "+0%", tono: str = "+0Hz"):
        self.voz = voz
        self.velocidad = velocidad
        self.tono = tono

    def sintetizar(self, texto: str, destino: Path) -> None:
        import edge_tts

        async def _generar() -> bytes:
            com = edge_tts.Communicate(texto, self.voz, rate=self.velocidad, pitch=self.tono)
            trozos = bytearray()
            async for evento in com.stream():
                if evento["type"] == "audio":
                    trozos.extend(evento["data"])
            return bytes(trozos)

        try:
            datos = asyncio.run(_generar())
        except Exception as exc:  # edge-tts levanta excepciones de red variadas
            raise ErrorVoz(f"edge-tts falló con la voz '{self.voz}': {exc}") from exc
        if not datos:
            raise ErrorVoz(f"edge-tts devolvió audio vacío con la voz '{self.voz}'")
        _guardar_atomico(destino, datos)


class VozOpenAI:
    """TTS de OpenAI. Usa la misma clave que el paso 02."""

    nombre = "openai"

    def __init__(self, clave: str, voz: str = "onyx", modelo: str = "gpt-4o-mini-tts",
                 formato: str = "mp3", instrucciones: str = "", velocidad: float | None = None):
        from openai import OpenAI

        self._cliente = OpenAI(api_key=clave)
        self.voz = voz
        self.modelo = modelo
        self.formato = formato
        self.instrucciones = instrucciones
        self.velocidad = velocidad

    def sintetizar(self, texto: str, destino: Path) -> None:
        extra: dict = {}
        if self.instrucciones:
            extra["instructions"] = self.instrucciones
        if self.velocidad:
            extra["speed"] = self.velocidad
        try:
            respuesta = self._cliente.audio.speech.create(
                model=self.modelo,
                voice=self.voz,
                input=texto,
                response_format=self.formato,
                **extra,
            )
        except Exception as exc:
            raise ErrorVoz(f"la API de voz de OpenAI falló: {exc}") from exc
        _guardar_atomico(destino, respuesta.content)


class VozExistente:
    """Reusa audios ya producidos por otra herramienta."""

    nombre = "existente"

    def __init__(self, origen: Path):
        self.origen = Path(origen)

    def sintetizar(self, texto: str, destino: Path) -> None:  # noqa: ARG002 - texto no se usa
        candidato = self.origen / destino.name
        if not candidato.is_file():
            raise ErrorVoz(f"no hay audio previo para {destino.name} en {self.origen}")
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidato, destino)


def construir(cfg: dict, clave_openai: str | None = None) -> ProveedorVoz:
    """Instancia el proveedor indicado en la sección `audio` de proyecto.yaml."""
    proveedor = (cfg.get("proveedor") or "edge").lower()

    if proveedor == "edge":
        return VozEdge(
            voz=cfg.get("voz", "es-UY-ValentinaNeural"),
            velocidad=str(cfg.get("velocidad", "+0%")),
            tono=str(cfg.get("tono", "+0Hz")),
        )
    if proveedor == "openai":
        if not clave_openai:
            raise ErrorVoz("el proveedor de voz 'openai' necesita OPENAI_API_KEY")
        return VozOpenAI(
            clave=clave_openai,
            voz=cfg.get("voz", "onyx"),
            modelo=cfg.get("modelo", "gpt-4o-mini-tts"),
            formato=cfg.get("formato", "mp3"),
            instrucciones=cfg.get("instrucciones", ""),
            velocidad=cfg.get("velocidad_openai"),
        )
    if proveedor == "existente":
        origen = cfg.get("origen")
        if not origen:
            raise ErrorVoz("el proveedor 'existente' necesita 'origen' en proyecto.yaml")
        return VozExistente(Path(origen))

    raise ErrorVoz(f"proveedor de voz desconocido: '{proveedor}' (edge | openai | existente)")
