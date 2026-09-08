import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comun import modelo  # noqa: E402


def test_id_y_id_slide():
    assert modelo.Segmento(3).id == "slide_03"
    assert modelo.Segmento(3, "a").id == "slide_03_a"
    assert modelo.Segmento(3, "a").id_slide == "slide_03"
    assert modelo.Segmento(12).id == "slide_12"


def test_desde_id():
    assert modelo.desde_id("slide_07") == modelo.Segmento(7)
    assert modelo.desde_id("slide_07_b") == modelo.Segmento(7, "b")


def test_desde_id_invalido():
    with pytest.raises(ValueError):
        modelo.desde_id("audio_final")


def test_descubrir_segmentos_ordena(tmp_path):
    for nombre in ("slide_10.txt", "slide_02_b.txt", "slide_02_a.txt", "notas.txt"):
        (tmp_path / nombre).write_text("x")
    encontrados = modelo.descubrir_segmentos(tmp_path, ".txt")
    assert [s.id for s in encontrados] == ["slide_02_a", "slide_02_b", "slide_10"]


def test_descubrir_segmentos_carpeta_inexistente(tmp_path):
    assert modelo.descubrir_segmentos(tmp_path / "nada", ".txt") == []


def test_primeros_de_cada_slide_una_sola_diapositiva():
    segs = [modelo.Segmento(1)]
    assert modelo.primeros_de_cada_slide(segs) == {"slide_01"}


def test_primeros_de_cada_slide_con_sub_segmentos():
    segs = [modelo.Segmento(1), modelo.Segmento(2, "a"), modelo.Segmento(2, "b"),
            modelo.Segmento(2, "c"), modelo.Segmento(3)]
    # Solo el primer segmento de cada diapositiva marca apertura; b y c no.
    assert modelo.primeros_de_cada_slide(segs) == {"slide_01", "slide_02_a", "slide_03"}


def test_primeros_de_cada_slide_no_depende_del_orden_de_entrada():
    desordenados = [modelo.Segmento(2, "b"), modelo.Segmento(1), modelo.Segmento(2, "a")]
    assert modelo.primeros_de_cada_slide(desordenados) == {"slide_01", "slide_02_a"}


def test_primeros_de_cada_slide_lista_vacia():
    assert modelo.primeros_de_cada_slide([]) == set()
