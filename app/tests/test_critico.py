"""The critic with a fake client: model parameter, dependency order, code decides, fails closed."""
import threading
import time
from types import SimpleNamespace

import pytest

from chaski import critico
from chaski.auditoria import MARCA_NO_ENTIENDO, Retraduccion
from chaski.critico import MODELO_CRITICO, criticar, criticar_pulido, revisar
from chaski.guardas import Agregados, sin_agregados
from chaski.hechos import Hechos, Medicamento

ES = "Tome una pastilla de paracetamol cada ocho horas"
QUY = "Paracetamol pastillata upyay, sapa pusaq horapi"
RETR = "Tome una pastilla de paracetamol cada ocho horas."
TRANSCRIPCION = "Eh, tome una pastilla de paracetamol cada ocho horas"
H = Hechos(medicamentos=[Medicamento(nombre="paracetamol", cantidad=1, unidad="pastilla", cada_horas=8, dias=None,
                                     momento=None)], proxima_cita_en_dias=None, ir_ya_si=[])
LIMPIO = Agregados(consejos_nuevos=[], diagnosticos_nuevos=[], destinatario_original="paciente",
                   destinatario_version="paciente")


class FakeClient:
    """Answers by what is asked, not by call order: the critic's calls run concurrently.

    `hechos` maps an input text to its facts (default H); `retr` is the back-translation; `agregados` the added
    content. A value may be an Exception (raised) or "refusal". `demora` delays every call (to prove concurrency).
    """

    def __init__(self, retr=RETR, hechos=None, agregados=LIMPIO, demora=0.0):
        self.retr, self.hechos, self.agregados, self.demora = retr, hechos or {}, agregados, demora
        self.llamadas = []
        self._lock = threading.Lock()
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        with self._lock:
            self.llamadas.append(kw)
        if self.demora:
            time.sleep(self.demora)
        formato, contenido = kw["output_format"], kw["messages"][0]["content"]
        retr = Retraduccion(castellano=self.retr) if self.retr not in ("refusal",) and isinstance(self.retr, str) \
            else self.retr
        salida = {Retraduccion: retr, Agregados: self.agregados, Hechos: self.hechos.get(contenido, H)}[formato]
        if isinstance(salida, Exception):
            raise salida
        if salida == "refusal":
            return SimpleNamespace(stop_reason="refusal", parsed_output=None)
        assert isinstance(salida, formato), f"esperaba {formato.__name__}"
        return SimpleNamespace(stop_reason="end_turn", parsed_output=salida)

    def de(self, formato):
        return [k for k in self.llamadas if k["output_format"] is formato]


def test_critico_por_defecto_es_el_del_producto_y_lo_usa_en_todas_las_llamadas():
    c = FakeClient()
    r = criticar(c, ES, QUY)
    assert r.veredicto.ok, r.veredicto
    from chaski import orquestador
    assert MODELO_CRITICO == orquestador.modelo_critico_env()  # the eval and the product share one default
    assert [k["model"] for k in c.llamadas] == [MODELO_CRITICO] * 4 and r.llamadas == 4


def test_modelo_critico_se_puede_cambiar():
    c = FakeClient()
    r = criticar(c, ES, QUY, modelo="claude-sonnet-x")
    assert {k["model"] for k in c.llamadas} == {"claude-sonnet-x"} and r.modelo == "claude-sonnet-x"


def test_modelo_de_hechos_separado_solo_para_la_extraccion():
    c = FakeClient()
    criticar(c, ES, QUY, modelo="claude-sonnet-x", modelo_hechos="claude-haiku-x")
    assert {k["model"] for k in c.de(Hechos)} == {"claude-haiku-x"}
    assert {k["model"] for k in c.de(Retraduccion) + c.de(Agregados)} == {"claude-sonnet-x"}


def test_retraduccion_es_ciega():
    c = FakeClient()
    criticar(c, ES, QUY)
    (retr,) = c.de(Retraduccion)
    assert retr["messages"][0]["content"] == QUY and ES not in str(retr)


def test_hechos_y_agregados_de_la_retraduccion_van_despues_de_ella():
    c = FakeClient()
    criticar(c, ES, QUY)
    i_retr = c.llamadas.index(c.de(Retraduccion)[0])
    despues = [k for k in c.llamadas if RETR in k["messages"][0]["content"]]
    assert len(despues) == 2 and all(c.llamadas.index(k) > i_retr for k in despues)


def test_criticar_corre_en_paralelo():
    c = FakeClient(demora=0.2)
    t0 = time.perf_counter()
    assert criticar(c, ES, QUY).veredicto.ok
    assert time.perf_counter() - t0 < 0.6  # 2 waves of 0.2 s, not 4 sequential calls (0.8 s)


def test_pulido_corre_en_paralelo():
    c = FakeClient(demora=0.2)
    t0 = time.perf_counter()
    assert criticar_pulido(c, TRANSCRIPCION, ES).veredicto.ok
    assert time.perf_counter() - t0 < 0.4  # one wave, not 3 sequential calls (0.6 s)


def test_revisar_con_los_dos_comparte_los_hechos_del_castellano_y_corre_en_paralelo():
    c = FakeClient(demora=0.2)
    t0 = time.perf_counter()
    r = revisar(c, ES, quechua=QUY, transcripcion=TRANSCRIPCION)
    assert r.veredicto.ok and r.pulido is not None
    assert time.perf_counter() - t0 < 0.6
    textos = [k["messages"][0]["content"] for k in c.de(Hechos)]
    assert textos.count(ES) == 1 and r.llamadas == len(c.llamadas) == critico.LLAMADAS_AMBOS
    assert r.hechos_original == H and r.pulido.hechos_retraducido == H


def test_revisar_el_pulido_manda_aunque_la_traduccion_pase():
    c = FakeClient(hechos={ES + ", por cinco días": H})
    r = revisar(c, ES + ", por cinco días", quechua=QUY, transcripcion=ES)
    assert not r.veredicto.ok and r.veredicto.capa.startswith("B3")


def test_dato_cambiado_en_la_ida_y_vuelta_bloquea():
    mal = H.model_copy(deep=True)
    mal.medicamentos[0].cada_horas = 6
    r = criticar(FakeClient(hechos={RETR: mal}), ES, QUY)
    assert not r.veredicto.ok and r.veredicto.capa.startswith("B5")


def test_retraduccion_que_no_entiende_bloquea():
    r = criticar(FakeClient(retr=f"Tome {MARCA_NO_ENTIENDO}"), ES, QUY)
    assert not r.veredicto.ok


def test_b4_bloquea_aunque_la_ida_y_vuelta_coincida():
    r = criticar(FakeClient(), ES, "Paracetamol pastillata upyay, sapa suqta horapi")
    assert not r.veredicto.ok and r.veredicto.capa.startswith("B4")


def test_consejo_inventado_bloquea():
    ag = LIMPIO.model_copy(update={"consejos_nuevos": ["tome bastante agua"]})
    r = criticar(FakeClient(agregados=ag), ES, QUY)
    assert not r.veredicto.ok and r.veredicto.capa.startswith("C") and "agua" in r.veredicto.motivo


def test_rechazo_o_error_falla_cerrado():
    r = criticar(FakeClient(retr="refusal"), ES, QUY)
    assert not r.veredicto.ok and r.veredicto.motivo == "no pude verificar"
    r = criticar(FakeClient(hechos={ES: TimeoutError("lento")}), ES, QUY)
    assert not r.veredicto.ok and "TimeoutError" in r.veredicto.detalle[0]
    r = criticar_pulido(FakeClient(agregados=TimeoutError("lento")), TRANSCRIPCION, ES)
    assert not r.veredicto.ok and "TimeoutError" in r.veredicto.detalle[0]
    r = revisar(FakeClient(hechos={ES: TimeoutError("lento")}), ES, quechua=QUY, transcripcion=TRANSCRIPCION)
    assert not r.veredicto.ok  # the shared extraction failing blocks both checks


def test_pulido_limpio_pasa_y_pulido_con_dato_nuevo_bloquea():
    c = FakeClient()
    assert criticar_pulido(c, TRANSCRIPCION, ES).veredicto.ok
    assert c.llamadas[0]["model"] == MODELO_CRITICO and len(c.llamadas) == 3
    r = criticar_pulido(FakeClient(), ES, ES + ", por cinco días")
    assert not r.veredicto.ok and r.veredicto.capa.startswith("B3")


# --- per-step options ------------------------------------------------------------------------

def test_opciones_por_defecto_hechos_sin_pensar_y_juicio_con_esfuerzo_bajo():
    c = FakeClient()
    criticar(c, ES, QUY)
    (h, *_), (retr,), (ag,) = c.de(Hechos), c.de(Retraduccion), c.de(Agregados)
    assert h["thinking"] == {"type": "disabled"} and "output_config" not in h
    assert retr["output_config"] == {"effort": "low"} and ag["output_config"] == {"effort": "low"}
    assert all(k["max_tokens"] <= 2000 for k in c.llamadas)
    assert all(k["system"][0]["cache_control"] == {"type": "ephemeral"} for k in c.llamadas)


def test_opciones_modelo_no_manda_pensamiento_y_haiku_no_recibe_esfuerzo(monkeypatch):
    monkeypatch.setitem(critico.PENSAR, "retraducir", "modelo")
    assert critico.opciones("retraducir", "claude-sonnet-5") == {"max_tokens": critico.MAX_TOKENS_PENSANDO}
    assert critico.opciones("agregados", "claude-haiku-4-5-20251001") == {"max_tokens": critico.MAX_TOKENS["agregados"]}


def test_opcion_de_pensar_invalida_falla_cerrado(monkeypatch):
    monkeypatch.setitem(critico.PENSAR, "hechos", "mucho")
    with pytest.raises(ValueError):
        critico.opciones("hechos", "claude-sonnet-5")
    assert not criticar(FakeClient(), ES, QUY).veredicto.ok


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
