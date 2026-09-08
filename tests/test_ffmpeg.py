"""anteponer_silencio: el filtro adelay y el códec correcto por formato."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comun import ffmpeg  # noqa: E402


def _correr_falso(llamados):
    """Registra los argumentos y crea el archivo de salida, como haría ffmpeg de verdad."""
    def _fake(args):
        llamados.append(args)
        Path(args[-1]).write_bytes(b"audio falso")
    return _fake


def test_anteponer_silencio_arma_adelay_en_ms(monkeypatch, tmp_path):
    llamados = []
    monkeypatch.setattr(ffmpeg, "correr", _correr_falso(llamados))

    origen = tmp_path / "slide_01.mp3"
    destino = tmp_path / "slide_01_final.mp3"
    ffmpeg.anteponer_silencio(origen, destino, 0.7, formato="mp3")

    assert len(llamados) == 1
    args = llamados[0]
    assert "-af" in args
    assert args[args.index("-af") + 1] == "adelay=700|700"
    assert args[args.index("-c:a") + 1] == "libmp3lame"
    # Escritura atómica: el destino final no aparece como argumento de ffmpeg,
    # solo el temporal que después se renombra.
    assert str(destino) not in args


def test_anteponer_silencio_redondea_milisegundos(monkeypatch, tmp_path):
    llamados = []
    monkeypatch.setattr(ffmpeg, "correr", _correr_falso(llamados))
    ffmpeg.anteponer_silencio(tmp_path / "a.mp3", tmp_path / "b.mp3", 0.333, formato="mp3")
    assert llamados[0][llamados[0].index("-af") + 1] == "adelay=333|333"


def test_anteponer_silencio_codec_por_formato(monkeypatch, tmp_path):
    llamados = []
    monkeypatch.setattr(ffmpeg, "correr", _correr_falso(llamados))
    casos = [
        ("wav", "pcm_s16le", "wav"),
        ("m4a", "aac", "ipod"),
        ("ogg", "libmp3lame", "mp3"),  # formato no mapeado: cae al default mp3
    ]
    for formato, codec_esperado, muxer_esperado in casos:
        llamados.clear()
        ffmpeg.anteponer_silencio(tmp_path / "a", tmp_path / f"b_{formato}", 0.5, formato=formato)
        args = llamados[0]
        assert args[args.index("-c:a") + 1] == codec_esperado, formato
        assert args[args.index("-f") + 1] == muxer_esperado, formato


def test_anteponer_silencio_deja_el_archivo_final_en_destino(monkeypatch, tmp_path):
    """La función escribe atómico: correr() crea el .parcial, y acá se confirma
    que el rename deja el archivo con el nombre de destino esperado."""
    def fake_correr(args):
        # simula que ffmpeg escribió el archivo temporal que pidieron
        salida = Path(args[-1])
        salida.write_bytes(b"audio falso")

    monkeypatch.setattr(ffmpeg, "correr", fake_correr)
    destino = tmp_path / "slide_01.mp3"
    ffmpeg.anteponer_silencio(tmp_path / "origen.mp3", destino, 0.7)
    assert destino.is_file()
    assert not destino.with_name(destino.name + ".parcial").exists()


def test_anteponer_silencio_rechaza_segundos_no_positivos(tmp_path):
    with pytest.raises(ValueError):
        ffmpeg.anteponer_silencio(tmp_path / "a.mp3", tmp_path / "b.mp3", 0)
    with pytest.raises(ValueError):
        ffmpeg.anteponer_silencio(tmp_path / "a.mp3", tmp_path / "b.mp3", -0.5)
