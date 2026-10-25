"""The hands-free turn: audio in, Chaski works out who spoke. Fakes for the detector and both recognizers, the fake
Anthropic client from test_servicio, the real interpreter path. No network."""
import json

import pytest

from chaski import orquestador, servicio
from chaski.hechos import Hechos
from chaski.interprete import Contexto, DecisionModelo
from tests.test_servicio import QUY_BIEN, TE, TE_PULIDO, FakeClient, traducir

AUDIO = b"RIFF....WAVEfmt "


@pytest.fixture(autouse=True)
def _entorno(monkeypatch):
    monkeypatch.delenv("CHASKI_MODELO_PRINCIPAL", raising=False)
    monkeypatch.delenv("CHASKI_MODELO_CRITICO", raising=False)
    monkeypatch.setenv("CHASKI_MEMORIA_AUTO", "0")


@pytest.fixture
def entradas(monkeypatch):
    """Every `entrada` the interpreter received, while the real interpreter still runs."""
    vistas = []
    real = orquestador.interpretar

    def espia(entrada, *a, **kw):
        vistas.append(entrada)
        return real(entrada, *a, **kw)

    monkeypatch.setattr(orquestador, "interpretar", espia)
    return vistas


class Oidos:
    """The three injected callables, recording who was called."""

    def __init__(self, codigo="spa", confianza=0.95, castellano=TE, quechua="umaymi nanawan",
                 alternativas=(["umaymi nanawan", 0.8], ["umayqa nanawan", 0.3]), conf_quechua=0.82, detector=None):
        self.codigo, self.conf, self.castellano, self.quechua = codigo, confianza, castellano, quechua
        self.alternativas, self.conf_quechua, self.detector = list(alternativas), conf_quechua, detector
        self.llamadas = []

    def detectar_idioma(self, audio, nombre):
        self.llamadas.append("idioma")
        if self.detector:
            return self.detector(audio, nombre)
        return {"codigo": self.codigo, "confianza": self.conf}

    def oir_castellano(self, audio, nombre):
        self.llamadas.append("castellano")
        return {"texto": self.castellano}

    def oir_quechua(self, audio, nombre):
        self.llamadas.append("quechua")
        return {"texto": self.quechua, "alternativas": self.alternativas, "confianza": self.conf_quechua}

    def kw(self):
        return {"detectar_idioma": self.detectar_idioma, "oir_castellano": self.oir_castellano,
                "oir_quechua": self.oir_quechua}


def deps_ensayo(client):
    d = orquestador.dependencias(client)
    d["candidatos_fn"] = None
    return d


def deps_personal(client):
    d = deps_ensayo(client)
    d["traducir_fn"] = lambda t, de, a: QUY_BIEN
    return d


def deps_paciente(client):
    d = deps_ensayo(client)
    d["traducir_fn"] = lambda t, de, a: "Me duele la cabeza."
    return d


def cliente_paciente():
    return FakeClient(DecisionModelo(accion="traducir", para="personal", idioma_salida="spa",
                                     texto_pulido="Umaymi nanawan.", motivo="m", frase_banco_id=None,
                                     dato_faltante=None),
                      hechos=Hechos(medicamentos=[], proxima_cita_en_dias=None, ir_ya_si=[]),
                      retro="Me duele la cabeza.")


def historial(*roles):
    c = Contexto()
    for rol in roles:
        c.agregar(rol, f"algo que dijo {rol}")
    return json.dumps(c.model_dump(mode="json"))


# ── decidir_lado: the pure decision ─────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("deteccion,roles,esperado", [
    ({"codigo": "spa", "confianza": 0.9}, ("personal",), ("personal", "detector")),
    ({"codigo": "quy", "confianza": 0.6}, (), ("paciente", "detector")),
    ({"codigo": "quy_Latn", "confianza": 0.99}, (), ("paciente", "detector")),
    ({"codigo": "spa", "confianza": None}, ("personal",), ("personal", "detector")),
    ({"codigo": "spa", "confianza": 0.59}, ("personal",), ("paciente", "alternancia")),
    ({"codigo": "quy", "confianza": 0.3}, ("paciente",), ("personal", "alternancia")),
    ({"codigo": "eng", "confianza": 0.99}, ("paciente",), ("personal", "alternancia")),
    ({}, ("personal",), ("paciente", "alternancia")),
    ({}, ("personal", "chaski"), ("personal", "alternancia")),  # Chaski asked the staff something: they answer (C1)
    ({}, ("chaski",), ("personal", "alternancia")),
    (None, (), ("personal", "alternancia")),
])
def test_decidir_lado(deteccion, roles, esperado):
    ctx = Contexto.model_validate(json.loads(historial(*roles))) if roles else None
    assert servicio.decidir_lado(deteccion, ctx) == esperado


# ── turno_auto ──────────────────────────────────────────────────────────────────────────────────────────────

def test_castellano_va_al_personal(entradas):
    o = Oidos("spa", 0.97)
    r = servicio.turno_auto(AUDIO, "turno.wav", None, dependencias=deps_personal(FakeClient(traducir())), **o.kw())
    assert o.llamadas == ["idioma", "castellano"]
    assert (r["quien_hablo"], r["lado_por"], r["idioma_detectado"], r["confianza_idioma"]) == \
        ("personal", "detector", "spa", 0.97)
    assert entradas[0]["rol"] == "personal" and entradas[0]["idioma"] == "spa" and entradas[0]["texto"] == TE
    assert entradas[0]["n_mejores"] == [] and entradas[0]["confianza"] is None
    assert r["estado"] == "dicho" and r["para"] == "paciente" and r["texto_salida"] == QUY_BIEN
    assert {"idioma", "oir", "total"} <= set(r["ms"])
    json.dumps(r, default=str)


def test_quechua_va_al_paciente_con_n_mejores_y_confianza(entradas):
    o = Oidos("quy", 0.91)
    r = servicio.turno_auto(AUDIO, "turno.wav", "", dependencias=deps_paciente(cliente_paciente()), **o.kw())
    assert o.llamadas == ["idioma", "quechua"]
    assert r["quien_hablo"] == "paciente" and r["lado_por"] == "detector"
    e = entradas[0]
    assert (e["rol"], e["idioma"], e["texto"]) == ("paciente", "quy", "umaymi nanawan")
    assert e["n_mejores"] == ["umaymi nanawan", "umayqa nanawan"] and e["confianza"] == 0.82
    assert r["estado"] == "dicho" and r["texto_salida"] == "Me duele la cabeza." and r["para"] == "personal"


def test_poca_confianza_alterna_con_el_ultimo_que_hablo(entradas):
    o = Oidos("spa", 0.4)  # the detector leans Spanish, but it isn't sure; the staff spoke last
    r = servicio.turno_auto(AUDIO, "turno.wav", historial("personal"),
                            dependencias=deps_paciente(cliente_paciente()), **o.kw())
    assert o.llamadas == ["idioma", "quechua"]
    assert (r["quien_hablo"], r["lado_por"], r["confianza_idioma"]) == ("paciente", "alternancia", 0.4)
    assert entradas[0]["rol"] == "paciente" and entradas[0]["idioma"] == "quy"


def test_detector_caido_alterna_y_sin_historial_es_el_personal(entradas):
    def explota(audio, nombre):
        raise ConnectionError("la instancia no responde")

    o = Oidos(detector=explota)
    r = servicio.turno_auto(AUDIO, "turno.wav", None, dependencias=deps_personal(FakeClient(traducir())), **o.kw())
    assert o.llamadas == ["idioma", "castellano"]
    assert (r["quien_hablo"], r["lado_por"], r["idioma_detectado"], r["confianza_idioma"]) == \
        ("personal", "alternancia", None, None)

    o = Oidos(detector=explota)
    r = servicio.turno_auto(AUDIO, "turno.wav", historial("personal"),
                            dependencias=deps_paciente(cliente_paciente()), **o.kw())
    assert r["quien_hablo"] == "paciente" and o.llamadas == ["idioma", "quechua"]


def test_audio_sin_texto_da_no_entendi_sin_excepcion():
    c = FakeClient(traducir())
    o = Oidos("spa", 0.9, castellano="")
    r = servicio.turno_auto(AUDIO, "turno.wav", None, dependencias=deps_personal(c), **o.kw())
    assert r["accion"] == "no_entendi" and r["quien_hablo"] == "personal" and r["texto_original"] == ""

    o = Oidos("quy", 0.9, quechua=None, alternativas=(), conf_quechua=None)
    r = servicio.turno_auto(AUDIO, "turno.wav", None, dependencias=deps_paciente(cliente_paciente()), **o.kw())
    assert r["accion"] == "no_entendi" and r["quien_hablo"] == "paciente"


def test_contexto_mal_formado_falla_antes_de_oir():
    o = Oidos()
    with pytest.raises(ValueError, match="contexto"):
        servicio.turno_auto(AUDIO, "turno.wav", "{no es json", dependencias=deps_personal(FakeClient(traducir())),
                            **o.kw())
    assert o.llamadas == []


# ── turno_auto_eventos ──────────────────────────────────────────────────────────────────────────────────────

def _eventos(stream):
    salida = []
    for bloque in stream:
        cab, datos = bloque.strip().split("\n")
        salida.append((cab.removeprefix("event: "), json.loads(datos.removeprefix("data: "))))
    return salida


def test_eventos_oido_decision_resultado():
    o = Oidos("spa", 0.97)
    ev = _eventos(servicio.turno_auto_eventos(AUDIO, "turno.wav", None,
                                              dependencias=deps_personal(FakeClient(traducir())), **o.kw()))
    assert [e for e, _ in ev] == ["oido", "decision", "resultado"]
    oido, decision, resultado = (d for _, d in ev)
    assert (oido["quien_hablo"], oido["idioma"], oido["texto"], oido["lado_por"]) == ("personal", "spa", TE, "detector")
    assert decision["texto_pulido"] == TE_PULIDO
    assert resultado["estado"] == "dicho" and resultado["quien_hablo"] == "personal"
    assert resultado["lado_por"] == "detector" and {"idioma", "oir"} <= set(resultado["ms"])


def test_eventos_un_reconocedor_que_falla_termina_en_error():
    o = Oidos("quy", 0.9)

    def explota(audio, nombre):
        raise RuntimeError("omniASR reventó")

    o.oir_quechua = explota
    ev = _eventos(servicio.turno_auto_eventos(AUDIO, "turno.wav", None,
                                              dependencias=deps_paciente(cliente_paciente()), **o.kw()))
    assert [e for e, _ in ev] == ["error"] and "omniASR" in ev[0][1]["error"]


def test_eventos_contexto_mal_formado_termina_en_error():
    o = Oidos()
    ev = _eventos(servicio.turno_auto_eventos(AUDIO, "turno.wav", "{no es json",
                                              dependencias=deps_personal(FakeClient(traducir())), **o.kw()))
    assert [e for e, _ in ev] == ["error"] and "contexto mal formado" in ev[0][1]["error"] and o.llamadas == []


# ── Audit C1 / H3 ────────────────────────────────────────────────────────────────────────────────────────────────

def test_tras_una_pregunta_de_chaski_responde_el_mismo_que_hablo():
    ctx = Contexto()
    ctx.agregar("paciente", "umaymi nanan")
    ctx.agregar("chaski", "Pampachaway, ¿manachu kaqmanta rimariwaq?")
    assert servicio.decidir_lado({"codigo": "spa", "confianza": 0.3}, ctx) == ("paciente", "alternancia")
    assert servicio.decidir_lado({}, ctx) == ("paciente", "alternancia")


def test_lado_adivinado_baja_la_confianza_para_que_b1_frene_datos_clinicos():
    assert servicio._confianza_del_turno(None, "alternancia") == servicio.CONFIANZA_SI_ADIVINADO
    assert servicio._confianza_del_turno(0.9, "alternancia") == servicio.CONFIANZA_SI_ADIVINADO
    assert servicio._confianza_del_turno(0.3, "alternancia") == 0.3
    assert servicio._confianza_del_turno(0.9, "detector") == 0.9


def test_la_confianza_del_castellano_ya_no_se_descarta():
    assert servicio._confianza_del_turno("0.42", "detector") == 0.42
