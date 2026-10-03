"""Lectura de fuentes complementarias sin llamadas a la API."""

import importlib.util
from pathlib import Path
import sys

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

spec = importlib.util.spec_from_file_location(
    "paso02", Path(__file__).resolve().parent.parent / "02_escribir_guion.py"
)
paso02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paso02)


def test_lee_texto_complementario(tmp_path):
    archivo = tmp_path / "ficha.md"
    archivo.write_text("\nInformación de apoyo.\n", encoding="utf-8")
    assert paso02.leer_material_complementario(archivo) == "Información de apoyo."


def test_lee_pdf_con_texto(tmp_path):
    archivo = tmp_path / "capitulo.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    fuente = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): fuente})
    })
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 10 100 Td (Informacion complementaria) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    with archivo.open("wb") as salida:
        writer.write(salida)
    texto = paso02.leer_material_complementario(archivo)
    assert "Página 1" in texto
    assert "Informacion complementaria" in texto


def test_pdf_sin_texto_exige_ocr(tmp_path):
    archivo = tmp_path / "escaneado.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    with archivo.open("wb") as salida:
        writer.write(salida)
    with pytest.raises(ValueError, match="OCR"):
        paso02.leer_material_complementario(archivo)


def test_texto_vacio_no_se_envia_como_fuente(tmp_path):
    archivo = tmp_path / "vacio.txt"
    archivo.write_text("  \n", encoding="utf-8")
    with pytest.raises(ValueError, match="no contiene texto"):
        paso02.leer_material_complementario(archivo)


def test_estilo_se_carga_sin_guion_previo(tmp_path, monkeypatch):
    """Una limpieza de intermedios no debe eliminar la referencia de estilo."""
    (tmp_path / "config").mkdir()
    (tmp_path / "config/estilo_guion.md").write_text(
        "Referencia editorial de prueba.", encoding="utf-8"
    )
    monkeypatch.setattr(paso02.config, "RAIZ", tmp_path)
    proyecto = paso02.config.cargar(tmp_path)
    proyecto.guion_cfg["_cantidad_slides"] = 3
    assert not proyecto.salida("guion").exists()
    assert "Referencia editorial de prueba." in paso02.construir_instrucciones(proyecto)
