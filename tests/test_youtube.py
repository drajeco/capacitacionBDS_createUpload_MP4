import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import sys

import pytest

spec = importlib.util.spec_from_file_location('paso07', Path(__file__).resolve().parents[1] / '07_preparar_youtube.py')
paso = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paso)


@pytest.mark.parametrize('titulo,descripcion', [('', 'Texto'), ('x'*101, 'Texto'), ('Dos\nlíneas', 'Texto'), ('Título', ''), ('Título', 'x'*5001)])
def test_rechaza_publicacion_invalida(titulo, descripcion):
    with pytest.raises(ValueError):
        paso.renderizar(paso.Publicacion(titulo=titulo, descripcion=descripcion))


def test_genera_y_preserva_archivo(tmp_path, monkeypatch):
    import openai
    proy = paso.config.cargar(tmp_path)
    proy.salida('slides').mkdir(parents=True)
    (proy.salida('slides') / 'slide_01.png').write_bytes(b'imagen-de-prueba')
    guion = proy.salida('guion')
    guion.parent.mkdir(parents=True)
    guion.write_text('## Diapositiva 01 - Tema\n\nNarración:\n\nContenido revisado.', encoding='utf-8')
    monkeypatch.setattr(paso.config, 'cargar', lambda _: proy)
    monkeypatch.setattr(paso.config, 'clave_openai', lambda: 'clave-ficticia')
    monkeypatch.setattr(sys, 'argv', ['07_preparar_youtube.py'])
    parse = Mock(return_value=SimpleNamespace(status='completed', output_parsed=paso.Publicacion(titulo='Un título', descripcion='Una descripción.')))
    monkeypatch.setattr(openai, 'OpenAI', lambda **_: SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    assert paso.main() == 0
    salida = proy.salida('youtube')
    assert salida.read_text() == 'TÍTULO\nUn título\n\nDESCRIPCIÓN\nUna descripción.\n'
    assert 'Contenido revisado.' in parse.call_args.kwargs['input'][0]['content']
    salida.write_text('Edición manual', encoding='utf-8')
    assert paso.main() == 0
    assert parse.call_count == 1
    monkeypatch.setattr(sys, 'argv', ['07_preparar_youtube.py', '--forzar'])
    parse.return_value = SimpleNamespace(status='incomplete', output_parsed=None)
    with pytest.raises(SystemExit):
        paso.main()
    assert salida.read_text() == 'Edición manual'


def test_miniatura_se_actualiza_desde_content(tmp_path):
    proy = paso.config.cargar(tmp_path)
    proy.salida('slides').mkdir(parents=True)
    (proy.salida('slides') / 'slide_02.png').write_bytes(b'segunda')
    primera = proy.salida('slides') / 'slide_01.png'
    primera.write_bytes(b'primera')
    paso.preparar_miniatura(proy)
    assert proy.salida('miniatura').read_bytes() == b'primera'
    primera.write_bytes(b'nueva-leccion')
    paso.preparar_miniatura(proy)
    assert proy.salida('miniatura').read_bytes() == b'nueva-leccion'


def test_titulo_proviene_del_guion_no_yaml(tmp_path):
    proy = paso.config.cargar(tmp_path)
    proy.datos['proyecto']['titulo'] = 'Tema anterior'
    assert proy.titulo == ''
    guion = proy.salida('guion')
    guion.parent.mkdir(parents=True)
    guion.write_text('# Guion de locución — Tema nuevo\n\nContenido')
    assert proy.titulo == 'Tema nuevo'
    guion.write_text('# Guion de locución — Título corregido\n')
    assert proy.titulo == 'Título corregido'
