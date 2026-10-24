"""The whole audit with a fake Claude client: no network, no cost."""
from types import SimpleNamespace

import pytest

from chaski import auditoria
from chaski.auditoria import MARCA_NO_ENTIENDO, Retraduccion, SinRespuesta, Traduccion, auditar, decidir
from chaski.hechos import Diferencia, Hechos, Medicamento

ORIGINAL = "Tome una pastilla de sulfato ferroso cada día, durante un mes."
HECHOS_OK = Hechos(
    medicamentos=[Medicamento(nombre="sulfato ferroso", cantidad=1, unidad="pastilla", cada_horas=24, dias=30, momento=None)],
    proxima_cita_en_dias=None,
    ir_ya_si=[],
)


class FakeClient:
    """Answers each structured call from a queue, in call order, and records what it was asked."""

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.llamadas.append(kw)
        salida = self.respuestas.pop(0)
        if salida == "refusal":
            return SimpleNamespace(stop_reason="refusal", parsed_output=None)
        assert isinstance(salida, kw["output_format"]), f"esperaba {kw['output_format'].__name__}"
        return SimpleNamespace(stop_reason="end_turn", parsed_output=salida)


def flujo(hechos_retraducido=HECHOS_OK, inseguros=(), retraduccion="Tome una pastilla de sulfato ferroso cada día por un mes."):
    return [
        HECHOS_OK,
        Traduccion(quechua="(quechua)", terminos_inseguros=list(inseguros)),
        Retraduccion(castellano=retraduccion),
        hechos_retraducido,
    ]


def test_todo_coincide_se_envia():
    r = auditar(FakeClient(flujo()), ORIGINAL, glosario=[])
    assert r.enviar is True and r.diferencias == []


def test_dosis_cambiada_no_se_envia():
    mal = HECHOS_OK.model_copy(deep=True)
    mal.medicamentos[0].cada_horas = 12
    r = auditar(FakeClient(flujo(hechos_retraducido=mal)), ORIGINAL, glosario=[])
    assert r.enviar is False and "cada_horas" in r.motivo


def test_termino_inseguro_no_se_envia():
    r = auditar(FakeClient(flujo(inseguros=["sulfato ferroso"])), ORIGINAL, glosario=[])
    assert r.enviar is False and "sulfato ferroso" in r.motivo


def test_retraduccion_que_no_entiende_no_se_envia():
    r = auditar(FakeClient(flujo(retraduccion=f"Tome {MARCA_NO_ENTIENDO} cada día.")), ORIGINAL, glosario=[])
    assert r.enviar is False


def test_retraductor_nunca_ve_el_original():
    cliente = FakeClient(flujo())
    auditar(cliente, ORIGINAL, glosario=[])
    llamada_retraduccion = cliente.llamadas[2]
    assert llamada_retraduccion["output_format"] is Retraduccion
    assert ORIGINAL not in llamada_retraduccion["messages"][0]["content"]
    assert llamada_retraduccion["messages"][0]["content"] == "(quechua)"


def test_glosario_llega_a_la_traduccion():
    cliente = FakeClient(flujo())
    auditar(cliente, ORIGINAL, glosario=[{"castellano": "pastilla", "quechua": "PRUEBA"}])
    assert "pastilla → PRUEBA" in cliente.llamadas[1]["messages"][0]["content"]


def test_rechazo_de_claude_corta_todo():
    with pytest.raises(SinRespuesta):
        auditar(FakeClient(["refusal"]), ORIGINAL, glosario=[])


def test_decidir_prioriza_los_datos_criticos():
    enviar, motivo = decidir([Diferencia(campo="x.dias", original="30", retraducido="3")], ["algo"], MARCA_NO_ENTIENDO)
    assert enviar is False and "x.dias" in motivo


def test_glosario_vacio_si_no_existe(tmp_path):
    assert auditoria.cargar_glosario(tmp_path / "no-existe.json") == []
