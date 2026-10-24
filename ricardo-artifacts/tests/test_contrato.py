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


def test_entender_devuelve_n_mejores():
    """SOT-7 F10: Claude corrige eligiendo entre las hipotesis del modelo de voz."""
    t = entender("x.wav", n_mejores=3)
    assert len(t.alternativas) == 3
    assert t.alternativas[0][0] == t.texto
    assert all(isinstance(p, float) for _, p in t.alternativas)


def test_una_sola_hipotesis_sigue_siendo_valida():
    t = entender("x.wav", n_mejores=1)
    assert len(t.alternativas) == 1


def test_la_primera_alternativa_no_puede_contradecir_al_texto():
    from voz.contrato import Transcripcion
    with pytest.raises(ValueError):
        Transcripcion(texto="a", confianza=0.5, segundos=1.0, modelo="x",
                      alternativas=(("b", 0.9),))
