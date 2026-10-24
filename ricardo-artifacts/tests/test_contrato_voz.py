import pytest

from voz.contrato import Audio, Idioma, hablar, idioma


def test_hablar_devuelve_audio_del_contrato():
    a = hablar("Mamáy, allillanmi")
    assert isinstance(a, Audio)
    assert a.frecuencia == 16000
    assert a.modelo == "falso"
    assert a.ruta.endswith(".wav")


def test_hablar_respeta_el_destino_pedido(tmp_path):
    destino = tmp_path / "salida.wav"
    assert hablar("texto", destino).ruta == str(destino)


@pytest.mark.parametrize("nombre,esperado", [
    ("p1_A_001.wav", "quy"),
    ("muestras/mms-tts-quy/todas.wav", "quy"),
    ("prueba_spa.wav", "spa"),
    ("frase_es.wav", "spa"),
    ("es_mezcla.wav", "spa"),
])
def test_idioma_falso_es_determinista(nombre, esperado):
    assert idioma(nombre).codigo == esperado


def test_idioma_rechaza_codigos_fuera_del_contrato():
    with pytest.raises(ValueError):
        Idioma(codigo="aym", confianza=1.0, modelo="x")


def test_la_confianza_falsa_es_cero():
    """Ningun numero de la version falsa debe pasar por medicion."""
    assert idioma("x.wav").confianza == 0.0
