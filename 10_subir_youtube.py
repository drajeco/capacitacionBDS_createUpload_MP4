#!/usr/bin/env python3
"""Sube el video en PRIVADO; ejecutar ANTES del paso 09 que vacía el contenido.

--comprobar conecta y muestra el canal sin subir; --simular no conecta.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import re
import time

from comun import config, rutas
from comun.youtube_api import conectar, canal_actual


def huella(ruta):
    h = hashlib.sha256()
    with ruta.open('rb') as f:
        for bloque in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(bloque)
    return h.hexdigest()


def publicacion(ruta):
    texto = ruta.read_text(encoding='utf-8').strip()
    partes = re.fullmatch(r'TÍTULO\s*\n([^\n]+)\n\s*DESCRIPCIÓN\s*\n(.+)', texto, re.S)
    if not partes:
        raise ValueError('youtube.txt debe contener TÍTULO y DESCRIPCIÓN.')
    titulo, descripcion = (x.strip() for x in partes.groups())
    if not titulo or len(titulo) > 100 or not descripcion or len(descripcion.encode('utf-8')) > 5000:
        raise ValueError('El título o descripción excede los límites de YouTube.')
    if any(c in titulo + descripcion for c in '<>'):
        raise ValueError('YouTube no admite < ni > en título o descripción.')
    return {'title': titulo, 'description': descripcion, 'categoryId': '27', 'defaultLanguage': 'es'}


@contextmanager
def bloqueo(ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open('a') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Ya hay una carga en curso para este video.') from None
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def guardar(ruta, datos):
    rutas.escribir_atomico(ruta, json.dumps(datos, ensure_ascii=False, indent=2))


def verificar_video(service, video_id, canal_id):
    respuesta = service.videos().list(part='snippet,status,processingDetails', id=video_id).execute()
    if len(respuesta.get('items', [])) != 1:
        raise ValueError('El video no está disponible en el canal autorizado.')
    video = respuesta['items'][0]
    if video['snippet']['channelId'] != canal_id:
        raise ValueError('El video pertenece a otro canal.')
    estado = video['status']
    if estado.get('uploadStatus') in ('failed', 'rejected', 'deleted'):
        raise ValueError('YouTube rechazó el video: ' + estado.get('rejectionReason', estado.get('failureReason', 'sin detalle')))
    return video


def cargar_video(service, canal, archivo, miniatura, snippet, registro, recuperar_id=None):
    """Un fallo ambiguo bloquea nuevas inserciones hasta recuperar el ID manualmente."""
    from googleapiclient.http import MediaFileUpload

    datos = json.loads(registro.read_text()) if registro.exists() else {}
    if datos and datos.get('canal_id') != canal['id']:
        raise ValueError('El registro pertenece a otro canal.')
    if recuperar_id:
        if not datos or datos.get('video_id'):
            raise ValueError('Solo se recuperan cargas pendientes sin ID registrado.')
        verificar_video(service, recuperar_id, canal['id'])
        datos.update(video_id=recuperar_id, url=f'https://youtu.be/{recuperar_id}')
        guardar(registro, datos)
    if datos and not datos.get('video_id'):
        raise ValueError('Hay una carga anterior de resultado incierto. Revisá YouTube Studio; si existe, usá --recuperar-id ID. No se subió otro video.')
    if not datos:
        datos = {'canal_id': canal['id'], 'canal': canal['titulo'], 'sha256': huella(archivo),
                 'titulo': snippet['title'], 'estado': 'iniciando'}
        # Persistir ANTES de cualquier solicitud que pueda crear un video.
        guardar(registro, datos)
        request = service.videos().insert(part='snippet,status', notifySubscribers=False,
            body={'snippet': snippet, 'status': {'privacyStatus': 'private', 'selfDeclaredMadeForKids': False}},
            media_body=MediaFileUpload(str(archivo), mimetype='video/mp4', resumable=True, chunksize=8*1024*1024))
        respuesta = None
        while respuesta is None:
            progreso, respuesta = request.next_chunk(num_retries=5)
            if progreso:
                print(f'Carga: {progreso.progress():.0%}', flush=True)
        datos.update(video_id=respuesta['id'], url=f'https://youtu.be/{respuesta["id"]}', estado='subido')
        guardar(registro, datos)
    video = verificar_video(service, datos['video_id'], canal['id'])
    # No cambiar una publicación que el usuario haya hecho pública posteriormente.
    if not datos.get('miniatura_subida'):
        service.thumbnails().set(videoId=datos['video_id'],
            media_body=MediaFileUpload(str(miniatura), mimetype='image/png')).execute()
        datos['miniatura_subida'] = True
        guardar(registro, datos)
    limite = time.monotonic() + 120
    while video['status'].get('uploadStatus') != 'processed':
        if time.monotonic() >= limite:
            datos['estado'] = 'procesando'
            guardar(registro, datos)
            raise ValueError(f'Video subido; YouTube todavía lo procesa: {datos["url"]}. Repetí el comando para verificar sin duplicar.')
        print('YouTube está procesando el video…', flush=True)
        time.sleep(10)
        video = verificar_video(service, datos['video_id'], canal['id'])
    datos.update(estado='verificado', privacidad=video['status']['privacyStatus'])
    guardar(registro, datos)
    return datos


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--proyecto', default='01_content')
    p.add_argument('--credenciales', default='client_secret_yt.json')
    p.add_argument('--canal-id', help='ID del canal destino, obligatorio para subir')
    p.add_argument('--simular', action='store_true')
    p.add_argument('--comprobar', action='store_true')
    p.add_argument('--recuperar-id', help='ID revisado manualmente en Studio para recuperar una carga interrumpida')
    args = p.parse_args()
    try:
        proy = config.cargar(args.proyecto)
        if args.comprobar:
            canal = canal_actual(conectar(config.RAIZ / args.credenciales))
            print(f'Canal: {canal["titulo"]} ({canal["id"]})')
            return 0
        archivo, miniatura = proy.salida('video'), proy.salida('miniatura')
        if not archivo.is_file() or not miniatura.is_file():
            raise ValueError('Falta video_final.mp4 o miniatura.png. Completá el pipeline (miniatura: paso 07).')
        snippet = publicacion(proy.salida('youtube'))
        print(f'Título: {snippet["title"]}\nVisibilidad inicial: privada\nVideo: {archivo.stat().st_size / 1e6:.1f} MB', flush=True)
        if args.simular:
            return 0
        if not args.canal_id:
            raise ValueError('Indicá --canal-id con el ID que muestra --comprobar.')
        service = conectar(config.RAIZ / args.credenciales)
        canal = canal_actual(service)
        if canal['id'] != args.canal_id:
            raise ValueError('La cuenta autorizada no corresponde al canal solicitado. No se subió nada.')
        digest = huella(archivo)
        registro = config.RAIZ / 'historial_youtube' / f'{canal["id"]}_{digest}.json'
        with bloqueo(registro.with_suffix('.lock')):
            datos = cargar_video(service, canal, archivo, miniatura, snippet, registro, args.recuperar_id)
            if huella(archivo) != digest:
                raise ValueError('El video local cambió durante la carga. No continuar con Drive.')
            guardar(archivo.parent / 'youtube_subida.json', datos)
        print(f'Video verificado ({datos["privacidad"]}): {datos["url"]}', flush=True)
        return 0
    except Exception as exc:
        from googleapiclient.errors import HttpError
        if isinstance(exc, HttpError):
            error = json.loads(exc.content.decode('utf-8')).get('error', {})
            motivos = ', '.join(x.get('reason', '') for x in error.get('errors', []))
            print(f'YouTube HTTP {exc.resp.status}: {motivos}. Revisá API habilitada, usuario de prueba y permisos del canal.')
        else:
            print(f'No se completó YouTube: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
