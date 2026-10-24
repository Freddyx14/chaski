"""The critic with a fake client: model parameter, call order, code decides, fails closed."""
from types import SimpleNamespace

from chaski.auditoria import MARCA_NO_ENTIENDO, Retraduccion
from chaski.critico import MODELO_CRITICO, criticar, criticar_pulido
from chaski.guardas import Agregados, sin_agregados
from chaski.hechos import Hechos, Medicamento

ES = "Tome una pastilla de paracetamol cada ocho horas"
QUY = "Paracetamol pastillata upyay, sapa pusaq horapi"
H = Hechos(medicamentos=[Medicamento(nombre="paracetamol", cantidad=1, unidad="pastilla", cada_horas=8, dias=None,
                                     momento=None)], proxima_cita_en_dias=None, ir_ya_si=[])
LIMPIO = Agregados(consejos_nuevos=[], diagnosticos_nuevos=[], destinatario_original="paciente",
                   destinatario_version="paciente")


class FakeClient:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.llamadas.append(kw)
        salida = self.respuestas.pop(0)
        if isinstance(salida, Exception):
            raise salida
        if salida == "refusal":
            return SimpleNamespace(stop_reason="refusal", parsed_output=None)
        assert isinstance(salida, kw["output_format"]), f"esperaba {kw['output_format'].__name__}"
        return SimpleNamespace(stop_reason="end_turn", parsed_output=salida)


def flujo(retr_hechos=H, retr="Tome una pastilla de paracetamol cada ocho horas", agregados=LIMPIO):
    return [H, Retraduccion(castellano=retr), retr_hechos, agregados]


def test_critico_por_defecto_es_haiku_y_lo_usa_en_todas_las_llamadas():
    c = FakeClient(flujo())
    r = criticar(c, ES, QUY)
    assert r.veredicto.ok, r.veredicto
    assert MODELO_CRITICO == "claude-haiku-4-5-20251001"
    assert [k["model"] for k in c.llamadas] == [MODELO_CRITICO] * 4 and r.llamadas == 4


def test_modelo_critico_se_puede_cambiar():
    c = FakeClient(flujo())
    r = criticar(c, ES, QUY, modelo="claude-sonnet-x")
    assert {k["model"] for k in c.llamadas} == {"claude-sonnet-x"} and r.modelo == "claude-sonnet-x"


def test_retraduccion_es_ciega():
    c = FakeClient(flujo())
    criticar(c, ES, QUY)
    assert c.llamadas[1]["messages"][0]["content"] == QUY


def test_dato_cambiado_en_la_ida_y_vuelta_bloquea():
    mal = H.model_copy(deep=True)
    mal.medicamentos[0].cada_horas = 6
    r = criticar(FakeClient(flujo(retr_hechos=mal)), ES, QUY)
    assert not r.veredicto.ok and r.veredicto.capa.startswith("B5")


def test_retraduccion_que_no_entiende_bloquea():
    r = criticar(FakeClient(flujo(retr=f"Tome {MARCA_NO_ENTIENDO}")), ES, QUY)
    assert not r.veredicto.ok


def test_b4_bloquea_aunque_la_ida_y_vuelta_coincida():
    r = criticar(FakeClient(flujo()), ES, "Paracetamol pastillata upyay, sapa suqta horapi")
    assert not r.veredicto.ok and r.veredicto.capa.startswith("B4")


def test_consejo_inventado_bloquea():
    ag = LIMPIO.model_copy(update={"consejos_nuevos": ["tome bastante agua"]})
    r = criticar(FakeClient(flujo(agregados=ag)), ES, QUY)
    assert not r.veredicto.ok and r.veredicto.capa.startswith("C") and "agua" in r.veredicto.motivo


def test_rechazo_o_error_falla_cerrado():
    r = criticar(FakeClient([H, "refusal"]), ES, QUY)
    assert not r.veredicto.ok and r.veredicto.motivo == "no pude verificar"
    r = criticar(FakeClient([TimeoutError("lento")]), ES, QUY)
    assert not r.veredicto.ok and "TimeoutError" in r.veredicto.detalle[0]


def test_pulido_limpio_pasa_y_pulido_con_dato_nuevo_bloquea():
    c = FakeClient([H, H, LIMPIO])
    assert criticar_pulido(c, "Eh, tome una pastilla de paracetamol cada ocho horas", ES).veredicto.ok
    assert c.llamadas[0]["model"] == MODELO_CRITICO and len(c.llamadas) == 3
    r = criticar_pulido(FakeClient([H, H, LIMPIO]), ES, ES + ", por cinco días")
    assert not r.veredicto.ok and r.veredicto.capa.startswith("B3")


# --- sin_agregados ---------------------------------------------------------------------------

def test_sin_agregados_limpio_pasa():
    assert sin_agregados(LIMPIO).ok


def test_diagnostico_inventado_bloquea():
    assert not sin_agregados(LIMPIO.model_copy(update={"diagnosticos_nuevos": ["anemia"]})).ok


def test_destinatario_equivocado_bloquea():
    v = sin_agregados(LIMPIO.model_copy(update={"destinatario_version": "personal"}))
    assert not v.ok and "personal" in v.motivo


def test_paciente_y_acompanante_son_el_mismo_lado():
    assert sin_agregados(LIMPIO.model_copy(update={"destinatario_version": "acompanante"})).ok


def test_destinatario_desconocido_no_bloquea():
    assert sin_agregados(LIMPIO.model_copy(update={"destinatario_version": "no_se_sabe"})).ok


def test_sin_agregados_mal_formado_falla_cerrado():
    assert not sin_agregados(None).ok
