import pytest

from voz.contrato import Grabacion
from voz.ingesta import partir_por_hablante, resumen_por_persona


def grabaciones(personas=("p1", "p2", "p3"), por_persona=6):
    salida = []
    for p in personas:
        for n in range(por_persona):
            bloque = "A" if n % 2 == 0 else "B"
            salida.append(Grabacion(p, bloque, n, f"{p}_{n}.wav", "texto", "", 3.0, True))
    return salida


def test_la_persona_de_prueba_no_aparece_en_entrenamiento():
    partes = partir_por_hablante(grabaciones(), persona_prueba="p3")
    personas_entrenamiento = {g.persona for g in partes["entrenamiento"]}
    personas_validacion = {g.persona for g in partes["validacion"]}
    assert "p3" not in personas_entrenamiento
    assert "p3" not in personas_validacion
    assert {g.persona for g in partes["prueba"]} == {"p3"}


def test_elige_automaticamente_a_quien_dejar_fuera():
    """Sin persona indicada, deja fuera a quien tenga mas respuestas del bloque B,
    porque el bloque B es el que se parece al uso real."""
    datos = grabaciones(("p1", "p2"), 4)
    datos += [Grabacion("p2", "B", 50 + n, f"p2_x{n}.wav", "t", "", 3.0, True) for n in range(10)]
    partes = partir_por_hablante(datos)
    assert {g.persona for g in partes["prueba"]} == {"p2"}


def test_descarta_lo_que_no_tiene_consentimiento():
    datos = grabaciones(("p1", "p2"), 2)
    datos.append(Grabacion("p9", "A", 1, "p9.wav", "t", "", 3.0, False))
    partes = partir_por_hablante(datos, persona_prueba="p2")
    todas = [g for parte in partes.values() for g in parte]
    assert all(g.consentimiento for g in todas)
    assert "p9" not in {g.persona for g in todas}


def test_descarta_lo_que_no_tiene_transcripcion():
    datos = [Grabacion("p1", "A", 1, "a.wav", "", "", 3.0, True),
             Grabacion("p1", "A", 2, "b.wav", "texto", "", 3.0, True),
             Grabacion("p2", "A", 1, "c.wav", "texto", "", 3.0, True)]
    partes = partir_por_hablante(datos, persona_prueba="p2")
    assert [g.audio for g in partes["entrenamiento"]] == ["b.wav"]


def test_una_sola_persona_no_permite_particion_honesta():
    with pytest.raises(ValueError, match="dos personas"):
        partir_por_hablante(grabaciones(("p1",), 4))


def test_validacion_sale_del_entrenamiento_y_no_se_solapa():
    partes = partir_por_hablante(grabaciones(("p1", "p2", "p3", "p4"), 10), persona_prueba="p4")
    audios = [g.audio for parte in partes.values() for g in parte]
    assert len(audios) == len(set(audios))
    assert len(partes["validacion"]) > 0


def test_resumen_cuenta_minutos_por_persona():
    datos = [Grabacion("p1", "A", 1, "a.wav", "t", "", 60.0, True),
             Grabacion("p1", "B", 2, "b.wav", "t", "", 30.0, True)]
    resumen = resumen_por_persona(datos)
    assert resumen["p1"]["clips"] == 2
    assert resumen["p1"]["minutos"] == pytest.approx(1.5)
    assert resumen["p1"]["bloque_B"] == 1
