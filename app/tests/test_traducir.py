"""The engine switch and its fallback. NLLB is faked by patching urlopen; Claude by a fake client."""
import io
import json
import urllib.parse
from types import SimpleNamespace

import pytest

from chaski import traducir as tr
from chaski.traducir import ENV_NLLB, FalloMotor, traducir


class FakeClient:
    def __init__(self, texto="Huk pastillata pusaq horapi upiyay.", rechazo=False):
        self.texto, self.rechazo, self.llamadas = texto, rechazo, []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.llamadas.append(kw)
        if self.rechazo:
            return SimpleNamespace(stop_reason="refusal", parsed_output=None)
        return SimpleNamespace(stop_reason="end_turn", parsed_output=kw["output_format"](traduccion=self.texto))


class Respuesta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def nllb(monkeypatch):
    """Patch urlopen; record the request; answer with `estado['respuesta']` or raise `estado['error']`."""
    estado = {"respuesta": {"traduccion": "Pusaq horapi upiyay"}, "error": None, "pedidos": []}

    def urlopen(pedido, timeout):
        estado["pedidos"].append(pedido)
        if estado["error"]:
            raise estado["error"]
        return Respuesta(json.dumps(estado["respuesta"]).encode())

    monkeypatch.setattr(tr.urllib.request, "urlopen", urlopen)
    monkeypatch.setenv(ENV_NLLB, "http://ricardo:8020")
    return estado


def test_nllb_usa_el_contrato_declarado(nllb):
    r = traducir("Tome cada ocho horas", "spa", "quy", motor="nllb", client=FakeClient())
    assert (r.texto, r.motor, r.respaldo) == ("Pusaq horapi upiyay", "nllb", False)
    pedido = nllb["pedidos"][0]
    assert pedido.full_url == "http://ricardo:8020/traducir"
    assert urllib.parse.parse_qs(pedido.data.decode()) == {"texto": ["Tome cada ocho horas"], "de": ["spa"], "a": ["quy"]}


def test_url_que_ya_trae_la_ruta_no_se_duplica(monkeypatch):
    monkeypatch.setenv(ENV_NLLB, "http://x/traducir/")
    assert tr.url_nllb() == "http://x/traducir"


@pytest.mark.parametrize("falla", ["error", "vacia", "sin_clave"])
def test_nllb_falla_y_cae_a_claude(nllb, falla):
    if falla == "error":
        nllb["error"] = OSError("connection refused")
    elif falla == "vacia":
        nllb["respuesta"] = {"traduccion": "  "}
    else:
        nllb["respuesta"] = {"otra": "x"}
    c = FakeClient()
    r = traducir("Tome cada ocho horas", "spa", "quy", motor="nllb", client=c)
    assert (r.motor, r.motor_pedido, r.respaldo) == ("claude", "nllb", True)
    assert r.error and r.texto == c.texto and len(c.llamadas) == 1


def test_sin_variable_de_entorno_cae_a_claude(monkeypatch):
    monkeypatch.delenv(ENV_NLLB, raising=False)
    r = traducir("Hola", "spa", "quy", motor="nllb", client=FakeClient())
    assert r.motor == "claude" and r.respaldo and ENV_NLLB in r.error


def test_claude_directo_no_es_respaldo():
    c = FakeClient()
    r = traducir("Tome paracetamol", "spa", "quy", client=c, glosario=[{"castellano": "pastilla", "quechua": "PRUEBA"}])
    assert (r.motor, r.respaldo, r.error) == ("claude", False, None)
    kw = c.llamadas[0]
    assert kw["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "Ayacucho" in kw["system"][0]["text"] and "préstamo" in kw["system"][0]["text"]
    assert "pastilla → PRUEBA" in kw["messages"][0]["content"]


def test_quechua_a_castellano_usa_su_prompt():
    c = FakeClient(texto="Me duele la cabeza")
    assert traducir("Umaymi nanawan", "quy", "spa", client=c, glosario=[]).texto == "Me duele la cabeza"
    assert "al castellano" in c.llamadas[0]["system"][0]["text"]


def test_rechazo_de_claude_levanta_error():
    with pytest.raises(FalloMotor):
        traducir("x", "spa", "quy", client=FakeClient(rechazo=True), glosario=[])


def test_mismo_idioma_no_llama_a_nadie():
    c = FakeClient()
    assert traducir("Hola", "spa", "spa", client=c).texto == "Hola" and c.llamadas == []
