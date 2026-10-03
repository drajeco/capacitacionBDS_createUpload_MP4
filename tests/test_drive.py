import importlib.util
from pathlib import Path
from unittest.mock import Mock
import sys

import pytest

spec = importlib.util.spec_from_file_location('paso09', Path(__file__).resolve().parents[1] / '09_archivar_drive.py')
paso = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paso)


def test_version_depende_del_contenido(tmp_path):
    archivo = tmp_path / 'archivo.txt'
    archivo.write_text('original')
    original = paso.hashes({'a.txt': archivo})
    assert paso.hashes({'a.txt': archivo}) == original
    archivo.write_text('cambiado')
    assert paso.hashes({'a.txt': archivo})[1] != original[1]


def test_cuenta_servicio_requiere_unidad_compartida():
    service = Mock()
    folder = {'id': 'destino', 'mimeType': paso.FOLDER, 'capabilities': {'canAddChildren': True}}
    service.files.return_value.get.return_value.execute.return_value = folder
    with pytest.raises(ValueError, match='Mi unidad'):
        paso.comprobar(service, 'destino', True)
    assert paso.comprobar(service, 'destino', False) == folder
    folder['driveId'] = 'compartida'
    assert paso.comprobar(service, 'destino', True) == folder
    service.files.return_value.create.assert_not_called()


def test_reutiliza_y_no_sobrescribe(monkeypatch, tmp_path):
    service = Mock()
    previo = {'id': 'existente', 'md5Checksum': 'abc'}
    monkeypatch.setattr(paso, 'buscar', lambda *_: previo)
    assert paso.subir(service, 'padre', 'a.txt', tmp_path / 'a.txt', 'abc') == previo
    with pytest.raises(ValueError, match='No se reemplazó'):
        paso.subir(service, 'padre', 'a.txt', tmp_path / 'a.txt', 'otro')
    service.files.assert_not_called()


def test_archivado_completo_y_reporte(tmp_path, monkeypatch):
    (tmp_path / 'proyecto').mkdir()
    proy = paso.config.cargar(tmp_path / 'proyecto')
    archivo = tmp_path / 'guion.txt'
    archivo.write_text('Contenido')
    monkeypatch.setattr(paso.config, 'cargar', lambda _: proy)
    monkeypatch.setattr(paso, 'inventario', lambda _: {'02_Guion/guion.txt': archivo})
    monkeypatch.setattr(paso, 'conectar', lambda _: (Mock(), False))
    monkeypatch.setattr(paso, 'comprobar', lambda *_: {'id': 'raiz', 'name': 'Destino'})
    monkeypatch.setattr(paso, 'carpeta', lambda _, parent, nombre: parent + '/' + nombre)
    subir = Mock(return_value={'id': 'archivo', 'webViewLink': 'https://example.com/archivo'})
    monkeypatch.setattr(paso, 'subir', subir)
    monkeypatch.setattr(paso.config, 'RAIZ', tmp_path)
    monkeypatch.setattr(paso, 'verificar_remotos', Mock())
    monkeypatch.setattr(sys, 'argv', ['09_archivar_drive.py', '--leccion', '1', '--titulo-leccion', 'Tema', '--conservar-local'])
    assert paso.main() == 0
    assert subir.call_count == 2
    assert subir.call_args.args[2] == 'inventario.json'
    assert list((tmp_path / 'historial_drive').glob('leccion_01_*.json'))


def preparar_contenedores(tmp_path):
    proy = paso.config.cargar(tmp_path)
    for nombre in paso.CONTENEDORES:
        carpeta = tmp_path / nombre / 'subcarpeta'
        carpeta.mkdir(parents=True)
        (carpeta / 'archivo.json').write_text('contenido')
    (tmp_path / 'proyecto.yaml').write_text('configuración')
    return proy


def test_vacia_solo_contenedores_y_preserva_estructura(tmp_path):
    proy = preparar_contenedores(tmp_path)
    contenido = paso.contenido_local(proy)
    respaldo = paso.completar_inventario({}, contenido)
    assert set(respaldo.values()) == set(contenido.values())
    paso.vaciar_contenedores(proy, paso.hashes(contenido)[0])
    assert not paso.contenido_local(proy)
    assert (tmp_path / 'proyecto.yaml').read_text() == 'configuración'
    assert all((tmp_path / n / 'subcarpeta').is_dir() for n in paso.CONTENEDORES)


@pytest.mark.parametrize('cambio', ['nuevo', 'modificado', 'enlace'])
def test_no_borra_si_cambia_contenido(tmp_path, cambio):
    proy = preparar_contenedores(tmp_path)
    esperado = paso.hashes(paso.contenido_local(proy))[0]
    carpeta = tmp_path / paso.CONTENEDORES[0] / 'subcarpeta'
    if cambio == 'enlace':
        (carpeta / 'enlace').symlink_to(tmp_path / 'proyecto.yaml')
    else:
        (carpeta / ('nuevo.txt' if cambio == 'nuevo' else 'archivo.json')).write_text('cambio')
    with pytest.raises(ValueError):
        paso.vaciar_contenedores(proy, esperado)
    assert all((tmp_path / n / 'subcarpeta' / 'archivo.json').is_file() for n in paso.CONTENEDORES)


def test_verificacion_remota_rechaza_archivo_incompleto():
    service = Mock()
    service.files.return_value.get.return_value.execute.return_value = {'md5Checksum': 'abc', 'size': '2'}
    with pytest.raises(ValueError, match='verificación remota'):
        paso.verificar_remotos(service, [{'drive_id': 'id', 'md5': 'abc', 'bytes': 3, 'ruta': 'video'}])


def test_fallo_verificacion_no_llama_limpieza(tmp_path, monkeypatch):
    proy = preparar_contenedores(tmp_path)
    monkeypatch.setattr(paso.config, 'RAIZ', tmp_path)
    monkeypatch.setattr(paso.config, 'cargar', lambda _: proy)
    monkeypatch.setattr(paso, 'inventario', lambda _: {})
    monkeypatch.setattr(paso, 'conectar', lambda _: (Mock(), False))
    monkeypatch.setattr(paso, 'comprobar', lambda *_: {'id': 'raiz', 'name': 'Destino'})
    monkeypatch.setattr(paso, 'carpeta', lambda *_: 'carpeta')
    monkeypatch.setattr(paso, 'subir', lambda *_: {'id': 'archivo'})
    monkeypatch.setattr(paso, 'verificar_remotos', Mock(side_effect=ValueError('fallo remoto')))
    vaciar = Mock()
    monkeypatch.setattr(paso, 'vaciar_contenedores', vaciar)
    monkeypatch.setattr(sys, 'argv', ['09_archivar_drive.py', '--leccion', '2', '--titulo-leccion', 'Otro tema'])
    assert paso.main() == 1
    vaciar.assert_not_called()
    assert len(paso.contenido_local(proy)) == 3


def test_archivo_pregunta_solo_numero_y_deriva_titulo(tmp_path, monkeypatch):
    from types import SimpleNamespace
    proy = paso.config.cargar(tmp_path)
    guion = proy.salida('guion')
    guion.parent.mkdir(parents=True)
    guion.write_text('# Guion de locución — Tema del contenido\n')
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)
    preguntar = Mock(return_value='2')
    monkeypatch.setattr('builtins.input', preguntar)
    assert paso.identificar_leccion(SimpleNamespace(leccion=None, titulo_leccion=None), proy) == (2, 'Tema del contenido')
    assert preguntar.call_count == 1
