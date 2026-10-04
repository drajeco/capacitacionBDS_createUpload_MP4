"""Autorización de YouTube separada del token de Drive."""
import json
import os
from pathlib import Path

from . import config

SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube.readonly']


def conectar(credenciales: Path):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    datos = json.loads(credenciales.read_text(encoding='utf-8'))
    if 'installed' not in datos:
        raise ValueError('YouTube requiere un cliente OAuth de Aplicación de escritorio.')
    token = config.RAIZ / '.youtube/token.json'
    cred = Credentials.from_authorized_user_file(str(token), SCOPES) if token.is_file() else None
    if cred and cred.client_id != datos['installed']['client_id']:
        raise ValueError('El token de YouTube pertenece a otro cliente OAuth.')
    if cred and cred.expired and cred.refresh_token:
        cred.refresh(Request())
    if not cred or not cred.valid:
        print('Autorizá YouTube en el navegador y elegí el canal correcto.', flush=True)
        cred = InstalledAppFlow.from_client_secrets_file(str(credenciales), SCOPES).run_local_server(
            port=0, timeout_seconds=600, prompt='select_account',
            authorization_prompt_message='Esperando autorización de YouTube en el navegador.')
    token.parent.mkdir(exist_ok=True, mode=0o700)
    fd = os.open(token, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(cred.to_json())
    token.chmod(0o600)
    return build('youtube', 'v3', credentials=cred, cache_discovery=False)


def canal_actual(service):
    datos = service.channels().list(part='snippet,status', mine=True).execute()
    items = datos.get('items', [])
    if len(items) != 1:
        raise ValueError('La autorización debe identificar exactamente un canal de YouTube.')
    canal = items[0]
    return {'id': canal['id'], 'titulo': canal['snippet']['title'],
            'estado': canal.get('status', {})}
