"""El guion editado a mano es la fuente de verdad: el parser tiene que ser estricto."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comun import guion  # noqa: E402
from comun.modelo import Segmento  # noqa: E402

SIMPLE = """## Diapositiva 01 - Portada

Narración:

Bienvenidos al video.
"""

CON_SEGMENTOS = """## Diapositiva 01 - Portada

Narración:

Bienvenidos.

## Diapositiva 03 - Riesgos

### Segmento a

Narración:

Primera idea.

### Segmento b

Narración:

Segunda idea,
en dos líneas.
"""


def test_diapositiva_simple():
    segs = guion.parsear(SIMPLE)
    assert [s.id for s in segs] == ["slide_01"]
    assert segs[0].titulo == "Portada"
    assert segs[0].narracion == "Bienvenidos al video."


def test_sub_segmentos_y_orden():
    segs = guion.parsear(CON_SEGMENTOS)
    assert [s.id for s in segs] == ["slide_01", "slide_03_a", "slide_03_b"]
    # Los sub-segmentos comparten la imagen de su diapositiva.
    assert segs[1].id_slide == segs[2].id_slide == "slide_03"
    assert segs[2].narracion == "Segunda idea,\nen dos líneas."


def test_roundtrip_render_parse():
    originales = guion.parsear(CON_SEGMENTOS)
    assert guion.parsear(guion.renderizar(originales, "Título")) == originales


def test_acepta_guion_largo_en_el_encabezado():
    assert guion.parsear("## Diapositiva 02 – Título\n\nNarración:\n\nTexto.")[0].slide == 2


def test_encabezado_sin_titulo():
    assert guion.parsear("## Diapositiva 02\n\nNarración:\n\nTexto.")[0].titulo == ""


def test_narracion_vacia_falla():
    with pytest.raises(guion.GuionInvalido, match="vacío"):
        guion.parsear("## Diapositiva 01 - A\n\nNarración:\n\n")


def test_segmentos_repetidos_fallan():
    texto = (
        "## Diapositiva 01 - A\n\n### Segmento a\n\nNarración:\n\nUno.\n\n"
        "### Segmento a\n\nNarración:\n\nDos.\n"
    )
    with pytest.raises(guion.GuionInvalido, match="repetidos"):
        guion.parsear(texto)


def test_mezclar_con_y_sin_sufijo_falla():
    texto = (
        "## Diapositiva 01 - A\n\nNarración:\n\nSuelto.\n\n"
        "### Segmento a\n\nNarración:\n\nCon sufijo.\n"
    )
    with pytest.raises(guion.GuionInvalido, match="mezcla"):
        guion.parsear(texto)


def test_sin_segmentos_falla():
    with pytest.raises(guion.GuionInvalido, match="ningún segmento"):
        guion.parsear("# Solo un título\n\nTexto suelto.")


def test_segmento_antes_de_diapositiva_falla():
    with pytest.raises(guion.GuionInvalido, match="antes del primer encabezado"):
        guion.parsear("### Segmento a\n\nNarración:\n\nTexto.")


def test_ids_con_dos_digitos():
    segs = guion.parsear("## Diapositiva 12 - X\n\nNarración:\n\nTexto.")
    assert segs[0].id == "slide_12" and segs[0].id_slide == "slide_12"
