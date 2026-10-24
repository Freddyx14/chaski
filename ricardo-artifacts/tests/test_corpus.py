import pytest

from servicio.corpus import leer_codigo


@pytest.mark.parametrize("texto,esperado", [
    ("C1. Tome una pastilla cada 8 horas.", ("C", 1)),
    ("c 12 su control es el lunes", ("C", 12)),
    ("ce uno, tome una pastilla", ("C", 1)),
    ("eme cinco paracetamol", ("M", 5)),
    ("ene tres los días de la semana", ("N", 3)),
    ("B2. Cuente dónde le duele", ("B", 2)),
    ("be quince, cuente cómo se siente", ("B", 15)),
])
def test_lee_el_codigo_del_inicio(texto, esperado):
    assert leer_codigo(texto) == esperado


@pytest.mark.parametrize("texto", [
    "Tome una pastilla cada 8 horas",          # sin codigo
    "cada ocho horas",                          # numero, pero no al inicio con letra
    "",
])
def test_sin_codigo_devuelve_nada(texto):
    assert leer_codigo(texto) is None


@pytest.mark.parametrize("texto,numero", [
    ("3. Tómela con agua, no con té", 3),
    ("20, cada ocho horas", 20),
    ("siete, venga en ayunas", 7),
    ("quince paracetamol", 15),
])
def test_lee_el_numero_corrido(texto, numero):
    leido = leer_codigo(texto)
    assert leido is not None and leido[1] == numero


def test_las_partes_salen_de_los_rangos():
    from servicio.corpus import parte_de, rangos
    r = rangos()
    assert r["C"][0] == 1
    assert parte_de(r["C"][0]) == "C"
    assert parte_de(r["M"][1]) == "M"


def test_la_distancia_de_palabras_cuenta_cambios():
    from servicio.corpus import _palabras, distancia_palabras
    a = _palabras("Huk pastillata upyay sapa pusaq horaspi")
    assert distancia_palabras(a, a) == 0
    assert distancia_palabras(a, _palabras("Huk pastillata upyay sapa pusaq")) == 1
    assert distancia_palabras(a, _palabras("mana imapas")) == 6


def test_el_importador_acepta_los_nombres_del_formulario():
    """El formulario manda `audio`, `transcripcion` y `numero_global`; el contrato
    original decía `audio_url`, `quechua_escrito` y `numero`. Valen los dos."""
    from voz.importar_formulario import campo
    del_formulario = {"persona": "p1", "bloque": "C", "numero": 1, "numero_global": 1,
                      "audio": "https://x/a.webm", "transcripcion": "Huk pastillata",
                      "castellano": "Tome una pastilla", "audio_segundos": 3.4}
    assert campo(del_formulario, "audio") == "https://x/a.webm"
    assert campo(del_formulario, "texto") == "Huk pastillata"
    assert campo(del_formulario, "segundos") == 3.4

    del_contrato = {"persona": "p1", "numero": 7, "audio_url": "https://x/b.webm",
                    "quechua_escrito": "Yakuwan upyay"}
    assert campo(del_contrato, "audio") == "https://x/b.webm"
    assert campo(del_contrato, "texto") == "Yakuwan upyay"


def test_numero_global_manda_sobre_numero():
    from voz.importar_formulario import campo
    assert campo({"numero": 1, "numero_global": 26}, "numero") == 26
