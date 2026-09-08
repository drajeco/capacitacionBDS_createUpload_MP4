"""El descubrimiento de diapositivas es el punto donde más fácil se rompe todo."""

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comun import rutas  # noqa: E402


def test_normalizar_quita_marca_ltr():
    # Es el caso real de 01_content: Keynote mete un U+200E en el nombre.
    sucio = "png_finales.‎001.png"
    assert rutas.normalizar_nombre(sucio) == "png_finales.001.png"


def test_normalizar_quita_bom_y_bidi():
    for invisible in ("﻿", "‪", "​", "⁦"):
        assert rutas.normalizar_nombre(f"a{invisible}b") == "ab"


def test_normalizar_aplica_nfc():
    descompuesto = unicodedata.normalize("NFD", "exposición.md")
    assert rutas.normalizar_nombre(descompuesto) == "exposición.md"


def test_numero_de_toma_el_ultimo():
    assert rutas.numero_de(Path("png_finales.‎012.png")) == 12
    assert rutas.numero_de(Path("v2_slide_07.png")) == 7
    assert rutas.numero_de(Path("portada.png")) is None


def test_orden_numerico_y_no_alfabetico(tmp_path):
    # Alfabéticamente "10" va antes que "2"; el pipeline necesita el orden real.
    for n in (1, 2, 10, 11, 3):
        (tmp_path / f"slide.‎{n:03d}.png").write_bytes(b"")
    encontradas = rutas.descubrir_slides(tmp_path)
    assert [rutas.numero_de(p) for p in encontradas] == [1, 2, 3, 10, 11]


def test_descubrir_ignora_ocultos_y_sin_numero(tmp_path):
    (tmp_path / "slide_01.png").write_bytes(b"")
    (tmp_path / ".DS_Store").write_bytes(b"")
    (tmp_path / "portada.png").write_bytes(b"")
    (tmp_path / "notas.md").write_text("x")
    assert [p.name for p in rutas.descubrir_slides(tmp_path)] == ["slide_01.png"]


def test_escritura_atomica_no_deja_parciales(tmp_path):
    destino = tmp_path / "sub" / "slide_01.txt"
    rutas.escribir_atomico(destino, "hola")
    assert destino.read_text(encoding="utf-8") == "hola"
    assert list(tmp_path.rglob("*.parcial")) == []
