"""Formato del guion maestro: se escribe en el paso 02 y se lee en el 03.

El .md es la única fuente de verdad, porque es el archivo que se revisa y se
edita a mano. El paso 02 lo genera a partir de una respuesta estructurada del
modelo (nunca le pide markdown directamente), y el paso 03 lo vuelve a leer ya
editado. Por eso el renderizador y el parser viven juntos: cualquier cambio de
formato tiene que tocarlos a los dos.
"""

from __future__ import annotations

import re

from .modelo import Segmento

ENCABEZADO_SLIDE = re.compile(r"^##\s+Diapositiva\s+(\d+)\s*(?:[-–—]\s*(.*))?$", re.IGNORECASE)
ENCABEZADO_SEGMENTO = re.compile(r"^###\s+Segmento\s+([a-z]+)\s*$", re.IGNORECASE)
MARCA_NARRACION = re.compile(r"^Narraci[oó]n\s*:\s*$", re.IGNORECASE)


class GuionInvalido(ValueError):
    """El guion no se puede dividir en segmentos sin ambigüedad."""


def renderizar(segmentos: list[Segmento], titulo: str) -> str:
    lineas = [
        f"# Guion de locución — {titulo}",
        "",
        "> Este archivo es la fuente de verdad de la narración. Revisalo y editalo",
        "> libremente antes de correr `03_dividir_guion.py`; se respeta el formato",
        "> de encabezados, no el texto.",
        "",
    ]
    slide_actual = None
    for seg in segmentos:
        if seg.slide != slide_actual:
            lineas += [f"## Diapositiva {seg.slide:02d} - {seg.titulo}".rstrip(" -"), ""]
            slide_actual = seg.slide
        if seg.sufijo:
            lineas += [f"### Segmento {seg.sufijo}", ""]
        lineas += ["Narración:", "", seg.narracion.strip(), ""]
    return "\n".join(lineas).rstrip() + "\n"


def parsear(texto: str) -> list[Segmento]:
    """Lee el guion editado y devuelve los segmentos en orden.

    Falla ante cualquier ambigüedad en lugar de adivinar: un guion mal dividido
    produce audios desalineados que recién se notan al mirar el video.
    """
    segmentos: list[Segmento] = []
    slide: int | None = None
    titulo = ""
    sufijo = ""
    acumulando = False
    cuerpo: list[str] = []

    def cerrar() -> None:
        nonlocal cuerpo, acumulando
        if not acumulando:
            return
        narracion = "\n".join(cuerpo).strip()
        if slide is None:
            raise GuionInvalido("hay un bloque 'Narración:' antes del primer encabezado de diapositiva")
        if not narracion:
            etiqueta = f"Diapositiva {slide:02d}" + (f", segmento {sufijo}" if sufijo else "")
            raise GuionInvalido(f"{etiqueta}: el bloque 'Narración:' está vacío")
        segmentos.append(Segmento(slide=slide, sufijo=sufijo, titulo=titulo, narracion=narracion))
        cuerpo = []
        acumulando = False

    for cruda in texto.splitlines():
        linea = cruda.rstrip()

        if m := ENCABEZADO_SLIDE.match(linea):
            cerrar()
            slide = int(m.group(1))
            titulo = (m.group(2) or "").strip()
            sufijo = ""
            continue

        if m := ENCABEZADO_SEGMENTO.match(linea):
            cerrar()
            if slide is None:
                raise GuionInvalido("hay un '### Segmento' antes del primer encabezado de diapositiva")
            sufijo = m.group(1).lower()
            continue

        if MARCA_NARRACION.match(linea):
            cerrar()
            acumulando = True
            continue

        # Un encabezado de otro nivel corta la narración en curso.
        if linea.startswith("#"):
            cerrar()
            continue

        if acumulando:
            cuerpo.append(linea)

    cerrar()

    if not segmentos:
        raise GuionInvalido(
            "no se encontró ningún segmento. El guion debe tener encabezados "
            "'## Diapositiva NN - Título' y bloques 'Narración:'."
        )

    identificadores = [s.id for s in segmentos]
    repetidos = {i for i in identificadores if identificadores.count(i) > 1}
    if repetidos:
        raise GuionInvalido(f"segmentos repetidos: {', '.join(sorted(repetidos))}")

    # Una diapositiva no puede mezclar un bloque sin sufijo con bloques con sufijo:
    # sería ambiguo qué audio corresponde a qué parte.
    por_slide: dict[int, list[str]] = {}
    for s in segmentos:
        por_slide.setdefault(s.slide, []).append(s.sufijo)
    for numero, sufijos in por_slide.items():
        if "" in sufijos and len(sufijos) > 1:
            raise GuionInvalido(
                f"Diapositiva {numero:02d}: mezcla un bloque sin '### Segmento' con "
                "bloques que sí lo tienen. Usá sufijos en todos o en ninguno."
            )

    return sorted(segmentos)
