#!/usr/bin/env python3
"""Archiva una versión del material en Google Drive mediante su API.

--simular enumera los archivos sin conectarse; --comprobar verifica el destino.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import sys
from pathlib import Path, PurePosixPath

from comun import config, rutas

FOLDER = 'application/vnd.google-apps.folder'
SCOPES = ['https://www.googleapis.com/auth/drive']
EXTENSIONES = {'.md', '.txt', '.pdf', '.png', '.jpg', '.jpeg', '.mp3', '.wav', '.mp4', '.m4a', '.pptx', '.key', '.yaml'}


def inventario(proy):
    cfg = proy.datos['drive']
    archivos = {}

    def agregar(origen, destino):
        if origen.is_symlink() or not origen.is_file():
            return
        if origen.suffix.lower() not in EXTENSIONES or any(x.startswith('.') for x in origen.relative_to(config.RAIZ).parts):
            return
        if origen.name.lower().startswith(('credentials', 'client_secret', 'token')):
            return
        origen.resolve().relative_to(config.RAIZ.resolve())
        if destino in archivos:
            raise ValueError(f'Destino duplicado: {destino}')
        archivos[destino] = origen

    def carpeta(origen, destino):
        if origen.is_dir():
            for p in sorted(origen.rglob('*')):
                if not any(x.is_symlink() for x in [p, *p.parents] if x != config.RAIZ):
                    agregar(p, str(PurePosixPath(destino) / p.relative_to(origen).as_posix()))

    for clave, destino in [('slides','Diapositivas'),('transcripcion','Exposicion'),('fichas','Lecturas'),('bibliografia','Bibliografia')]:
        carpeta(proy.insumo(clave), f'01_Fuentes/{destino}')
    agregar(proy.salida('guion'), '02_Guion/guion_maestro.md')
    for clave, destino in [('video','03_Publicacion/video_final.mp4'),('youtube','03_Publicacion/youtube.txt'),('cuestionario','04_Evaluacion/cuestionario.txt'),('cuestionario_resuelto','04_Evaluacion/cuestionario_resuelto.txt')]:
        origen=proy.salida(clave)
        if not origen.is_file():
            raise ValueError(f'Falta un entregable: {origen.name}. Completá el pipeline antes de archivar.')
        agregar(origen,destino)
    miniatura = proy.salida('miniatura')
    if not miniatura.is_file():
        raise ValueError('Falta la miniatura automática. Ejecutá el paso 07 antes de archivar.')
    agregar(miniatura, '03_Publicacion/miniatura.png')
    carpeta(proy.salida('qc'),'05_Control_calidad')
    agregar(proy.base/'proyecto.yaml','06_Configuracion/proyecto.yaml')
    for nombre in ('estilo_guion.md','lexico.yaml'):
        agregar(config.RAIZ/'config'/nombre,'06_Configuracion/'+nombre)
    if cfg.get('incluir_intermedios',True):
        for clave in ('textos','audios','segmentos'):
            carpeta(proy.salida(clave),f'07_Archivo_tecnico/{clave}')
    return archivos


CONTENEDORES = ('01_materialOriginal', '02_archivosIntermedios', '03_output')


def contenido_local(proy):
    """Inventaría TODO lo que se vaciará; nunca sigue enlaces simbólicos."""
    archivos = {}
    for nombre in CONTENEDORES:
        raiz = proy.base / nombre
        if raiz.is_symlink():
            raise ValueError(f'No se puede vaciar un enlace simbólico: {raiz}')
        if not raiz.exists():
            continue
        for p in sorted(raiz.rglob('*')):
            if p.is_symlink():
                raise ValueError(f'Hay un enlace simbólico en el contenedor: {p}')
            if p.is_dir():
                continue
            if not p.is_file():
                raise ValueError(f'Archivo especial no admitido: {p}')
            if p.name.lower().startswith(('credentials', 'client_secret', 'token', '.env')):
                raise ValueError(f'Retirá el archivo de credenciales del contenedor: {p.name}')
            archivos[p.relative_to(proy.base).as_posix()] = p
    return archivos


def completar_inventario(archivos, contenido):
    """Incluye originales y auxiliares omitidos por la selección editorial."""
    incluidos = set(archivos.values())
    for relativo, p in contenido.items():
        if p not in incluidos:
            archivos['08_Respaldo_completo/' + relativo] = p
    return archivos


def verificar_remotos(service, filas):
    for fila in filas:
        remoto = service.files().get(fileId=fila['drive_id'], supportsAllDrives=True,
            fields='id,md5Checksum,size,trashed').execute()
        if (remoto.get('trashed') or remoto.get('md5Checksum') != fila['md5']
                or int(remoto.get('size', -1)) != fila['bytes']):
            raise ValueError(f'Falló la verificación remota de {fila["ruta"]}. No se vaciará el contenido.')


def vaciar_contenedores(proy, esperado):
    # Comparar el conjunto completo antes de borrar el primer archivo.
    actual = contenido_local(proy)
    if hashes(actual)[0] != esperado:
        raise ValueError('El contenido local cambió durante la carga. No se vaciará.')
    for p in actual.values():
        p.unlink()
    # Se conservan todas las carpetas para cargar la siguiente lección.


def identificar_leccion(args, proy):
    numero = args.leccion
    titulo = args.titulo_leccion or proy.titulo
    if not titulo:
        raise ValueError("Falta el título en el guion maestro. Generá o revisá su encabezado antes de archivar.")
    if numero is None:
        if not sys.stdin.isatty():
            raise ValueError('Indicá --leccion N para archivar sin interacción.')
        numero = int(input('Número de lección: ').strip())
    if numero < 1 or not titulo.strip():
        raise ValueError('La lección necesita un número positivo y un título.')
    titulo = re.sub(r'[\\/\x00-\x1f]', '_', titulo.strip())
    return numero, titulo


def hashes(archivos):
    filas=[]
    for nombre,p in sorted(archivos.items()):
        h=hashlib.md5()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(8*1024*1024),b''):
                h.update(chunk)
        filas.append({'ruta':nombre,'bytes':p.stat().st_size,'md5':h.hexdigest()})
    version=hashlib.sha256(json.dumps(filas,sort_keys=True).encode()).hexdigest()[:16]
    return filas,version


def conectar(ruta):
    from googleapiclient.discovery import build
    datos=json.loads(ruta.read_text())
    es_servicio=datos.get('type')=='service_account'
    if es_servicio:
        from google.oauth2.service_account import Credentials
        cred=Credentials.from_service_account_file(str(ruta),scopes=SCOPES)
    else:
        if 'installed' not in datos:
            raise ValueError('Se necesitan credenciales OAuth de tipo Aplicación de escritorio.')
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        token=config.RAIZ/'.drive/token.json'
        cred=Credentials.from_authorized_user_file(str(token),SCOPES) if token.is_file() else None
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        if not cred or not cred.valid:
            print('Autorizá en el navegador la cuenta que tiene acceso a la carpeta.',flush=True)
            cred=InstalledAppFlow.from_client_secrets_file(str(ruta),SCOPES).run_local_server(
                port=0,timeout_seconds=180,prompt='select_account',
                authorization_prompt_message='Se abrió el navegador para autorizar Google Drive.')
        token.parent.mkdir(exist_ok=True,mode=0o700)
        fd=os.open(token,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,'w') as f:
            f.write(cred.to_json())
        token.chmod(0o600)
    return build('drive','v3',credentials=cred,cache_discovery=False),es_servicio


def comprobar(service,raiz,es_servicio):
    folder=service.files().get(fileId=raiz,supportsAllDrives=True,
        fields='id,name,mimeType,driveId,trashed,capabilities(canAddChildren)').execute()
    if folder.get('trashed') or folder.get('mimeType')!=FOLDER:
        raise ValueError('El destino no es una carpeta disponible.')
    if not folder.get('capabilities',{}).get('canAddChildren'):
        raise ValueError('La cuenta no tiene permiso para agregar archivos en esa carpeta.')
    if es_servicio and not folder.get('driveId'):
        raise ValueError('La carpeta está en Mi unidad. Usá credenciales OAuth de Aplicación de escritorio; una cuenta de servicio necesita una unidad compartida para almacenar estos archivos.')
    return folder


def buscar(service,parent,nombre):
    escapar=lambda s:s.replace('\\','\\\\').replace("'","\\'")
    resultado=[];token=None
    while True:
        datos=service.files().list(q=f"'{escapar(parent)}' in parents and name = '{escapar(nombre)}' and trashed = false",
            spaces='drive',fields='nextPageToken,files(id,name,mimeType,md5Checksum,size,webViewLink)',
            pageToken=token,supportsAllDrives=True,includeItemsFromAllDrives=True).execute()
        resultado.extend(datos.get('files',[]));token=datos.get('nextPageToken')
        if not token:break
    if len(resultado)>1:raise ValueError(f'Hay nombres duplicados en Drive: {nombre}')
    return resultado[0] if resultado else None


def carpeta(service,parent,nombre):
    encontrado=buscar(service,parent,nombre)
    if encontrado:
        if encontrado['mimeType']!=FOLDER:raise ValueError(f'{nombre} existe pero no es una carpeta.')
        return encontrado['id']
    return service.files().create(body={'name':nombre,'parents':[parent],'mimeType':FOLDER},fields='id',supportsAllDrives=True).execute()['id']


def subir(service,parent,nombre,ruta,md5):
    from googleapiclient.http import MediaFileUpload
    previo=buscar(service,parent,nombre)
    if previo:
        if previo.get('md5Checksum')!=md5:raise ValueError(f'El archivo remoto {nombre} cambió. No se reemplazó.')
        return previo
    request=service.files().create(body={'name':nombre,'parents':[parent]},
        media_body=MediaFileUpload(str(ruta),mimetype=mimetypes.guess_type(nombre)[0] or 'application/octet-stream',resumable=True,chunksize=8*1024*1024),
        supportsAllDrives=True,fields='id,name,md5Checksum,size,webViewLink')
    resultado=None
    while resultado is None:
        _,resultado=request.next_chunk(num_retries=5)
    if resultado.get('md5Checksum')!=md5:raise ValueError(f'No coincide la suma de control de {nombre}.')
    return resultado


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proyecto',default='01_content')
    parser.add_argument('--simular',action='store_true')
    parser.add_argument('--comprobar',action='store_true')
    parser.add_argument('--leccion', type=int)
    parser.add_argument('--titulo-leccion')
    parser.add_argument('--conservar-local', action='store_true', help='archiva sin vaciar los contenedores')
    args=parser.parse_args()
    try:
        proy=config.cargar(args.proyecto);cfg=proy.datos['drive']
        contenido = contenido_local(proy)
        esperado = hashes(contenido)[0]
        archivos=completar_inventario(inventario(proy), contenido)
        filas,version=hashes(archivos)
        print(f'{len(filas)} archivos · {sum(x["bytes"] for x in filas)/1e6:.1f} MB · versión {version}',flush=True)
        if args.simular:
            for fila in filas:print(fila['ruta'])
            print('Al archivar se vacían los tres contenedores.' if not args.conservar_local else 'Se conservarán los archivos locales.')
            return 0
        if not args.comprobar:
            numero, titulo = identificar_leccion(args, proy)
        service,es_servicio=conectar(config.RAIZ/cfg['credenciales'])
        raiz=comprobar(service,cfg['carpeta_id'],es_servicio)
        print(f'Destino verificado: {raiz["name"]}',flush=True)
        if args.comprobar:return 0
        proyecto=carpeta(service,raiz['id'],f'Lección {numero:02d} - {titulo}')
        destino=carpeta(service,proyecto,'version_'+version)
        carpetas={'':destino};reporte=[]
        for fila in filas:
            relative=PurePosixPath(fila['ruta']);parent=destino;acumulado=PurePosixPath()
            for parte in relative.parts[:-1]:
                acumulado/=parte;key=str(acumulado)
                if key not in carpetas:carpetas[key]=carpeta(service,parent,parte)
                parent=carpetas[key]
            local=archivos[fila['ruta']]
            # Detectar cambios posteriores al inventario.
            if hashes({fila['ruta']:local})[0][0]!=fila:raise ValueError(f'Cambió durante el archivado: {local.name}')
            remoto=subir(service,parent,relative.name,local,fila['md5'])
            reporte.append({**fila,'drive_id':remoto['id'],'url':remoto.get('webViewLink')})
            print(f'OK {fila["ruta"]}',flush=True)
        datos={'leccion': numero, 'titulo': titulo, 'carpeta_url':f'https://drive.google.com/drive/folders/{destino}','version':version,'archivos':reporte}
        reporte_local=config.RAIZ/'historial_drive'/f'leccion_{numero:02d}_{version}.json'
        rutas.escribir_atomico(reporte_local,json.dumps(datos,ensure_ascii=False,indent=2))
        md5=hashlib.md5(reporte_local.read_bytes()).hexdigest()
        manifiesto = subir(service,destino,'inventario.json',reporte_local,md5)
        verificar_remotos(service, reporte + [{'drive_id': manifiesto['id'], 'md5': md5,
            'bytes': reporte_local.stat().st_size, 'ruta': 'inventario.json'}])
        print('Archivo completo y verificado: '+datos['carpeta_url'])
        if not args.conservar_local:
            vaciar_contenedores(proy, esperado)
            print('Contenedores vacíos y listos para la siguiente lección.')
        return 0
    except Exception as exc:
        from googleapiclient.errors import HttpError
        if isinstance(exc,HttpError):
            print(f'Google Drive devolvió HTTP {exc.resp.status}. Verificá que la API esté habilitada y que la cuenta pueda acceder a la carpeta.')
        else:print(f'No se completó el archivo: {exc}')
        return 1


if __name__=='__main__':
    raise SystemExit(main())
