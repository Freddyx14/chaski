import pytest

from voz.contrato import Grabacion, Transcripcion, entender, escribir_manifiesto, leer_manifiesto


def test_nombre_estable():
    g = Grabacion(persona="p1", bloque="A", numero=7, audio="x.wav")
    assert g.nombre == "p1_A_007"


def test_bloque_invalido():
    with pytest.raises(ValueError):
        Grabacion(persona="p1", bloque="C", numero=1, audio="x.wav")


def test_ida_y_vuelta_json(tmp_path):
    originales = [
        Grabacion("p1", "A", 1, "a.wav", "sangre kaptinqa", "Si hay sangrado", 3.1, True),
        Grabacion("p2", "B", 2, "b.wav", "", "", 5.0, True),
    ]
    ruta = tmp_path / "manifiesto.jsonl"
    escribir_manifiesto(ruta, originales, cabecera="prueba: queda fuera p3")
    assert leer_manifiesto(ruta) == originales


def test_entender_devuelve_el_contrato():
    t = entender("cualquiera.ogg")
    assert isinstance(t, Transcripcion)
    assert t.modelo == "falso"
    assert t.texto
