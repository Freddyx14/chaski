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
