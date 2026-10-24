from types import SimpleNamespace

import pytest

from chaski.auditoria import SinRespuesta
from chaski.resumen import Borrador, Termino, Turno, glosario_verificado, no_se_dijo, resumir, texto_para_decir


class FakeClient:
    def __init__(self, salida):
        self.salida = salida
        self.llamadas = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.llamadas.append(kw)
        if self.salida == "refusal":
            return SimpleNamespace(stop_reason="refusal", parsed_output=None)
        return SimpleNamespace(stop_reason="end_turn", parsed_output=self.salida)


TURNOS = [
    Turno(lado="castellano", castellano="Tome una pastilla de paracetamol cada 8 horas por 3 días.", quechua="q", estado="dicho"),
    Turno(lado="castellano", castellano="Tome dos juntas si le duele mucho.", estado="bloqueado"),
    Turno(lado="quechua", castellano="¿Y si me olvido la de la noche?", quechua="q", estado="con_dudas"),
]

BORRADOR = Borrador(
    resumen="Fiebre. Se indicó paracetamol.",
    indicaciones=["Tome una pastilla de paracetamol cada 8 horas por 3 días"],
    senales_de_alarma=["la fiebre no baja"],
    proxima_cita="en 3 días",
    dudas=["qué hacer si olvida la dosis de la noche"],
)


def test_lo_bloqueado_nunca_se_le_pasa_al_modelo_y_va_a_no_se_dijo():
    cliente = FakeClient(BORRADOR)
    r = resumir(cliente, TURNOS, "personal")
    prompt = cliente.llamadas[0]["messages"][0]["content"]
    assert "dos juntas" not in prompt
    assert r.no_se_dijo == ["Tome dos juntas si le duele mucho."]


def test_el_rol_elige_el_prompt():
    a, b = FakeClient(BORRADOR), FakeClient(BORRADOR)
    resumir(a, TURNOS, "personal")
    resumir(b, TURNOS, "paciente")
    assert a.llamadas[0]["system"] != b.llamadas[0]["system"]
    assert "historia clínica" in a.llamadas[0]["system"]
    assert "en casa" in b.llamadas[0]["system"]


def test_dudas_marcadas_en_la_conversacion():
    cliente = FakeClient(BORRADOR)
    resumir(cliente, TURNOS, "paciente")
    assert "[con dudas]" in cliente.llamadas[0]["messages"][0]["content"]


def test_sin_turnos_dichos_no_llama_a_la_api():
    cliente = FakeClient(BORRADOR)
    r = resumir(cliente, [TURNOS[1]], "paciente")
    assert cliente.llamadas == []
    assert r.indicaciones == [] and r.no_se_dijo == ["Tome dos juntas si le duele mucho."]


def test_rechazo_no_inventa_resumen():
    with pytest.raises(SinRespuesta):
        resumir(FakeClient("refusal"), TURNOS, "personal")


def test_texto_para_decir_solo_lo_dicho():
    r = resumir(FakeClient(BORRADOR), TURNOS, "paciente")
    texto = texto_para_decir(r)
    assert texto == ("Tome una pastilla de paracetamol cada 8 horas por 3 días. "
                     "Venga a la posta de inmediato si: la fiebre no baja. Su próximo control: en 3 días.")
    assert "dos juntas" not in texto


QUY = [
    Turno(lado="castellano", castellano="Tome una pastilla cada 8 horas.", quechua="Sapa pusaq horapi huk pastillata ukyay.", estado="dicho"),
    Turno(lado="quechua", castellano="Me duele la cabeza.", quechua="Umaymi nanawan.", estado="entendido"),
    Turno(lado="castellano", castellano="Tome dos juntas.", quechua="Iskayta kuskata ukyay.", estado="bloqueado"),
]


def test_glosario_solo_con_quechua_que_se_dijo():
    propuestos = [Termino(quechua="Umaymi nanawan", castellano="me duele la cabeza"),
                  Termino(quechua="sapa pusaq horapi", castellano="cada ocho horas"),
                  Termino(quechua="wiksa nanay", castellano="dolor de barriga"),          # inventado
                  Termino(quechua="iskayta kuskata", castellano="dos juntas")]           # turno bloqueado
    g = glosario_verificado(propuestos, QUY)
    assert [t.quechua for t in g] == ["Umaymi nanawan", "sapa pusaq horapi"]


def test_glosario_sin_repetidos_y_maximo_ocho():
    turno = [Turno(lado="castellano", castellano="x", quechua=" ".join(f"p{i}" for i in range(20)), estado="dicho")]
    propuestos = [Termino(quechua=f"p{i}", castellano="x") for i in range(12)] + [Termino(quechua="P1", castellano="x")]
    assert len(glosario_verificado(propuestos, turno)) == 8


def test_resumir_filtra_el_glosario_y_le_muestra_el_quechua_al_modelo():
    b = Borrador(resumen="r", indicaciones=[], senales_de_alarma=[], proxima_cita=None, dudas=[],
                 glosario=[Termino(quechua="Umaymi nanawan", castellano="me duele la cabeza"),
                           Termino(quechua="inventado", castellano="x")])
    cliente = FakeClient(b)
    r = resumir(cliente, QUY, "personal")
    assert [t.quechua for t in r.glosario] == ["Umaymi nanawan"]
    prompt = cliente.llamadas[0]["messages"][0]["content"]
    assert "en quechua: Umaymi nanawan." in prompt and "Iskayta" not in prompt
