import importlib.util
from pathlib import Path
from unittest.mock import Mock
import json
import pytest

spec = importlib.util.spec_from_file_location('subir_yt', Path(__file__).resolve().parents[1] / '10_subir_youtube.py')
paso = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paso)


def test_publicacion_valida_y_limites(tmp_path):
    p = tmp_path / 'youtube.txt'
    p.write_text('TÍTULO\nTema\n\nDESCRIPCIÓN\nDescripción del video.\n')
    assert paso.publicacion(p)['title'] == 'Tema'
    p.write_text('TÍTULO\nTema\n\nDESCRIPCIÓN\n' + 'é'*2501)
    with pytest.raises(ValueError): paso.publicacion(p)


def preparar(tmp_path):
    video, miniatura, registro = (tmp_path / x for x in ('video.mp4','miniatura.png','historial.json'))
    video.write_bytes(b'video')
    miniatura.write_bytes(b'png')
    canal = {'id': 'canal', 'titulo': 'Mi canal'}
    service = Mock()
    service.videos.return_value.insert.return_value.next_chunk.return_value = (None, {'id': 'video_id'})
    service.videos.return_value.list.return_value.execute.return_value = {'items': [{
        'id': 'video_id', 'snippet': {'channelId': 'canal'},
        'status': {'uploadStatus': 'processed', 'privacyStatus': 'private'}}]}
    return service, canal, video, miniatura, registro


def test_subida_privada_y_reintento_sin_duplicar(tmp_path):
    service, canal, video, miniatura, registro = preparar(tmp_path)
    resultado = paso.cargar_video(service, canal, video, miniatura, {'title':'Tema'}, registro)
    assert resultado['estado'] == 'verificado'
    body = service.videos.return_value.insert.call_args.kwargs['body']
    assert body['status']['privacyStatus'] == 'private'
    paso.cargar_video(service, canal, video, miniatura, {'title':'Tema'}, registro)
    assert service.videos.return_value.insert.call_count == 1
    assert service.thumbnails.return_value.set.call_count == 1


def test_fallo_ambiguo_bloquea_nueva_insercion(tmp_path):
    service, canal, video, miniatura, registro = preparar(tmp_path)
    service.videos.return_value.insert.return_value.next_chunk.side_effect = OSError('interrumpido')
    with pytest.raises(OSError): paso.cargar_video(service, canal, video, miniatura, {'title': 'Tema'}, registro)
    assert json.loads(registro.read_text())['estado'] == 'iniciando'
    with pytest.raises(ValueError, match='incierto'): paso.cargar_video(service, canal, video, miniatura, {'title': 'Tema'}, registro)
    assert service.videos.return_value.insert.call_count == 1


def test_fallo_miniatura_conserva_id(tmp_path):
    service, canal, video, miniatura, registro = preparar(tmp_path)
    service.thumbnails.return_value.set.return_value.execute.side_effect = OSError('fallo')
    with pytest.raises(OSError): paso.cargar_video(service, canal, video, miniatura, {'title': 'Tema'}, registro)
    assert json.loads(registro.read_text())['video_id'] == 'video_id'
    service.thumbnails.return_value.set.return_value.execute.side_effect = None
    paso.cargar_video(service, canal, video, miniatura, {'title': 'Tema'}, registro)
    assert service.videos.return_value.insert.call_count == 1


def test_canal_incorrecto_rechazado(tmp_path):
    service, canal, video, miniatura, registro = preparar(tmp_path)
    service.videos.return_value.list.return_value.execute.return_value['items'][0]['snippet']['channelId'] = 'otro'
    with pytest.raises(ValueError, match='otro canal'): paso.verificar_video(service, 'video_id', 'canal')


def test_pipeline_youtube_antes_drive_y_fallo_detiene(monkeypatch):
    import correr_pipeline_video as pipeline
    import sys
    from types import SimpleNamespace
    monkeypatch.setattr(sys, 'argv', ['pipeline', '--subir-youtube', '--canal-id', 'canal', '--archivar-drive'])
    ejecutar = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(pipeline.subprocess, 'run', ejecutar)
    assert pipeline.main() == 0
    nombres = [llamada.args[0][1] for llamada in ejecutar.call_args_list]
    assert nombres[-2:] == ['10_subir_youtube.py', '09_archivar_drive.py']
    ejecutar.reset_mock()
    ejecutar.side_effect = lambda cmd, **_: SimpleNamespace(returncode=1 if cmd[1] == '10_subir_youtube.py' else 0)
    assert pipeline.main() == 1
    assert all(c.args[0][1] != '09_archivar_drive.py' for c in ejecutar.call_args_list)
