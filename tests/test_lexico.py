"""El léxico se aplica sobre el texto final: un reemplazo de más arruina el audio."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comun.lexico import Lexico  # noqa: E402


def test_sigla_como_palabra_completa():
    lex = Lexico(siglas={"LCR": "ele-ce-erre"})
    assert lex.aplicar("El LCR mide liquidez.") == "El ele-ce-erre mide liquidez."


def test_no_toca_palabras_que_contienen_la_sigla():
    lex = Lexico(siglas={"LCR": "ele-ce-erre"})
    assert lex.aplicar("LCRX y XLCR quedan igual.") == "LCRX y XLCR quedan igual."


def test_sigla_distingue_mayusculas():
    lex = Lexico(siglas={"PIB": "pib"})
    assert "pib bajo" in lex.aplicar("El pib bajo")


def test_termino_ignora_mayusculas():
    lex = Lexico(terminos={"cash flow": "cash flou"})
    assert lex.aplicar("El Cash Flow manda") == "El cash flou manda"


def test_reemplaza_el_mas_largo_primero():
    lex = Lexico(terminos={"trade": "treid", "trade finance": "treid fáinans"})
    assert lex.aplicar("El trade finance crece") == "El treid fáinans crece"


def test_lexico_inexistente_no_cambia_nada(tmp_path):
    lex = Lexico.desde_archivo(tmp_path / "no_existe.yaml")
    assert len(lex) == 0
    assert lex.aplicar("Texto LCR intacto") == "Texto LCR intacto"


def test_reemplazo_con_barras_no_rompe():
    lex = Lexico(terminos={"a/b": "a barra b"})
    assert lex.aplicar("el a/b final") == "el a barra b final"
