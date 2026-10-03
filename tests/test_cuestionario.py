import importlib.util
import sys
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('paso08', Path(__file__).resolve().parents[1] / '08_crear_cuestionario.py')
paso = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = paso
spec.loader.exec_module(paso)


def ejemplo():
    fuentes = {'V01': ('Diapositiva 01', 'Texto del video.'), 'R01': ('Lectura', 'Texto de lectura.')}
    preguntas = []
    for n, nivel in enumerate(['comprension']*4 + ['razonamiento']*4 + ['integracion']*2):
        evidencias = [paso.Evidencia(fuente='V01', fragmento='Texto del video.')]
        if n >= 4:
            evidencias.append(paso.Evidencia(fuente='R01', fragmento='Texto de lectura.'))
        preguntas.append(paso.Pregunta(nivel=nivel, enunciado=f'Caso {n+1}', opciones=['Uno','Dos','Tres','Cuatro'], correcta='C', explicacion='Justificación reservada.', analisis_opciones=['Error uno','Error dos','Acierto tres','Error cuatro'], evidencias=evidencias))
    return paso.Cuestionario(preguntas=preguntas), fuentes


def test_version_limpia_no_filtra_soluciones():
    cuestionario, fuentes = ejemplo()
    limpio, resuelto = paso.renderizar(cuestionario, 'Tema', fuentes)
    assert 'INSTRUCCIONES' in limpio and '10: ___' in limpio
    for texto in ['Respuesta correcta:', 'Justificación reservada.', 'Error uno', '[R01]', 'Nivel:']:
        assert texto not in limpio
        assert texto in resuelto
    for n in range(1, 11):
        assert f'{n}. Caso {n}' in limpio and f'{n}. Caso {n}' in resuelto


@pytest.mark.parametrize('fallo', ['distribucion','sin_lectura','cita_inventada','opciones_duplicadas'])
def test_rechaza_estructura_o_fundamento_invalido(fallo):
    cuestionario, fuentes = ejemplo()
    if fallo == 'distribucion':
        cuestionario.preguntas[0].nivel = 'integracion'
    elif fallo == 'sin_lectura':
        cuestionario.preguntas[5].evidencias.pop()
    elif fallo == 'cita_inventada':
        cuestionario.preguntas[9].evidencias[0].fragmento = 'No existe esta cita.'
    else:
        cuestionario.preguntas[0].opciones[1] = 'Uno'
    with pytest.raises(ValueError):
        paso.renderizar(cuestionario, 'Tema', fuentes)


def test_corrige_una_respuesta_con_cita_invalida(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    import openai

    cuestionario, fuentes = ejemplo()
    invalido = cuestionario.model_copy(deep=True)
    invalido.preguntas[0].evidencias[0].fragmento = 'Cita inventada.'
    proy = paso.config.cargar(tmp_path)
    monkeypatch.setattr(paso.config, 'cargar', lambda _: proy)
    monkeypatch.setattr(paso, 'cargar_fuentes', lambda _: fuentes)
    monkeypatch.setattr(paso.config, 'clave_openai', lambda: 'clave-ficticia')
    monkeypatch.setattr(sys, 'argv', ['08_crear_cuestionario.py'])
    parse = Mock(side_effect=[
        SimpleNamespace(status='completed', output_parsed=invalido),
        SimpleNamespace(status='completed', output_parsed=cuestionario),
    ])
    monkeypatch.setattr(openai, 'OpenAI', lambda **_: SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    assert paso.main() == 0
    assert parse.call_count == 2
    assert proy.salida('cuestionario').is_file()
    assert proy.salida('cuestionario_resuelto').is_file()
    assert 'Cita inventada.' not in proy.salida('cuestionario_resuelto').read_text()
