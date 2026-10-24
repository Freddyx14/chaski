from types import SimpleNamespace

import pytest

from chaski.auditoria import SinRespuesta
from chaski.resumen import Borrador, Turno, no_se_dijo, resumir, texto_para_decir


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
