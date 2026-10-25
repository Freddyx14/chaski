"""Prescription by voice: vision reads a box, Chaski asks the staff aloud, and only a spoken «sí» says it to the
patient, through the guards and the critic. All fakes, no network."""
import json
from types import SimpleNamespace

import pytest

from chaski import servicio
from chaski.interprete import Contexto, DecisionModelo
from chaski.orquestador import Veredicto, es_afirmacion, interpretar
from chaski.traducir import TextoTraducido

LECTURA = {"seguro": True, "medicamento": "paracetamol", "concentracion": "500 mg", "presentacion": "tabletas",
           "cantidad": 1.0, "unidad": "tableta", "cada_horas": 8.0, "dias": 3.0, "advertencias": [],
           "posologia_de": "receta", "no_leido": []}
INSTRUCCION = "Tome una tableta de paracetamol 500 mg cada 8 horas, por 3 días."


@pytest.fixture(autouse=True)
def _entorno(monkeypatch):
    monkeypatch.setenv("CHASKI_TRADUCIR_ANTICIPADO", "1")  # the confirmed path must not depend on it
    monkeypatch.setenv("CHASKI_REPREGUNTAR_AL_BLOQUEAR", "1")
    monkeypatch.delenv("CHASKI_MODELO_PRINCIPAL", raising=False)
    monkeypatch.delenv("CHASKI_MODELO_CRITICO", raising=False)


class FakeClient:
    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.llamadas.append(kw)
        return SimpleNamespace(stop_reason="end_turn", parsed_output=self.respuestas.pop(0))


class Registro:
    def __init__(self, guardas=None, critico_ok=True):
        self.llamadas, self.guardas_resp, self.critico_ok = [], list(guardas or []), critico_ok

    def traducir(self, texto, de, a):
        self.llamadas.append(("traducir", texto, de, a))
        return TextoTraducido(texto=f"[{a}] {texto}", de=de, a=a, motor="claude", motor_pedido="claude")

    def guardas(self, e):
        self.llamadas.append(("guardas", e.original, e.pulido, e.confianza))
        return self.guardas_resp.pop(0) if self.guardas_resp else Veredicto(ok=True)

    def auditar(self, e):
        self.llamadas.append(("critico", e.pulido, e.traduccion))
        return Veredicto(ok=self.critico_ok, motivo="cambió un dato crítico: paracetamol.dosis")

    def kw(self):
        return dict(traducir_fn=self.traducir, guardas_fn=self.guardas, auditar_fn=self.auditar)


def _pendiente() -> Contexto:
    r = servicio.receta(LECTURA, None)
    return Contexto.model_validate(r["contexto"])


# ── The question to the staff ────────────────────────────────────────────────────────────────────────────────

def test_receta_completa_pregunta_al_personal_y_guarda_la_indicacion():
    voces = []
    r = servicio.receta(LECTURA, None, voz_fn=lambda t, i: voces.append((t, i)) or b"RIFF")
    assert r["accion"] == "repreguntar" and r["para"] == "personal" and r["idioma_salida"] == "spa"
    assert r["estado"] == "dicho"
    assert r["texto_salida"] == "Leí: paracetamol 500 mg, una tableta cada 8 horas, por 3 días. ¿Se lo digo?"
    assert r["texto_pulido"] == INSTRUCCION
    assert r["contexto"]["receta_pendiente"] == INSTRUCCION and r["contexto"]["modo"] == "receta"
    assert voces == [(r["texto_salida"], "spa")] and r["audio_wav_b64"]


def test_receta_solo_con_los_campos_presentes():
    r = servicio.receta({**LECTURA, "dias": None, "concentracion": None, "advertencias": ["No tomar con alcohol."]},
                        None)
    assert r["texto_pulido"] == "Tome una tableta de paracetamol cada 8 horas."
    assert "días" not in r["texto_salida"] and "mg" not in r["texto_salida"]
    # vision writes the warnings itself: they go to the staff screen, never into what the patient hears
    assert "alcohol" not in r["texto_salida"] and "alcohol" in r["aviso"]


def test_falta_la_dosis_pregunta_por_ella_y_no_deja_nada_pendiente():
    r = servicio.receta({**LECTURA, "cantidad": None, "unidad": None, "dias": None, "posologia_de": "falta"}, None)
    assert r["contexto"]["receta_pendiente"] is None and r["texto_pulido"] == ""
    assert "la dosis" in r["texto_salida"] and "¿Se lo digo?" not in r["texto_salida"]
    assert "tableta" not in r["texto_salida"] and r["dato_faltante"] == "dosis"


def test_falta_la_frecuencia_pregunta_por_ella():
    r = servicio.receta({**LECTURA, "cada_horas": None}, None)
    assert r["contexto"]["receta_pendiente"] is None and "cada cuántas horas" in r["texto_salida"]


def test_contexto_viejo_sin_el_campo_sigue_funcionando():
    viejo = json.dumps({"historial": [{"rol": "personal", "texto": "hola"}], "modo": "consulta"})
    assert servicio.leer_contexto(viejo).receta_pendiente is None
    r = servicio.receta(LECTURA, viejo)
    assert r["contexto"]["historial"][0]["texto"] == "hola"


# ── The staff's answer ───────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("texto", ["Sí.", "ya, dígale", "Está bien", "ok", "así es", "Correcto", "sí, dígale nomás"])
def test_afirmaciones(texto):
    assert es_afirmacion(texto)


@pytest.mark.parametrize("texto", ["no", "sí, pero son dos", "no, son dos tabletas", "por favor", "mmm", "", "ya no"])
def test_no_afirmaciones(texto):
    assert not es_afirmacion(texto)


def test_si_traduce_la_receta_al_paciente_con_barreras_y_critico():
    reg, cliente = Registro(), FakeClient()  # no model decision: the client must not be called
    r = interpretar({"texto": "Sí, dígale", "idioma": "spa", "rol": "personal", "confianza": 0.2}, _pendiente(),
                    client=cliente, **reg.kw())
    assert cliente.llamadas == []
    assert r.estado == "dicho" and r.accion == "traducir" and r.para == "paciente" and r.idioma_salida == "quy"
    assert r.texto_salida == f"[quy] {INSTRUCCION}"
    assert [p[0] for p in reg.llamadas] == ["traducir", "guardas", "critico"]
    assert reg.llamadas[1] == ("guardas", INSTRUCCION, INSTRUCCION, None)  # the «sí»'s ASR confidence is not the order's
    assert r.contexto.receta_pendiente is None


def test_no_con_correccion_limpia_y_es_un_turno_normal():
    reg = Registro()
    cliente = FakeClient(DecisionModelo(accion="traducir", para="paciente", idioma_salida="quy",
                                        texto_pulido="Son dos tabletas.", motivo="m", frase_banco_id=None,
                                        dato_faltante=None))
    r = interpretar({"texto": "no, son dos tabletas", "idioma": "spa", "rol": "personal"}, _pendiente(),
                    client=cliente, anticipar=False, **reg.kw())
    assert len(cliente.llamadas) == 1 and r.contexto.receta_pendiente is None
    assert r.texto_salida == "[quy] Son dos tabletas." and INSTRUCCION not in r.texto_salida


def test_turno_del_paciente_no_toca_la_receta_pendiente():
    reg = Registro()
    cliente = FakeClient(DecisionModelo(accion="traducir", para="personal", idioma_salida="spa",
                                        texto_pulido="Allillanmi", motivo="m", frase_banco_id=None,
                                        dato_faltante=None))
    r = interpretar({"texto": "allillanmi", "idioma": "quy", "rol": "paciente"}, _pendiente(), client=cliente,
                    anticipar=False, **reg.kw())
    assert r.contexto.receta_pendiente == INSTRUCCION


def test_bloqueo_en_la_receta_confirmada_pregunta_una_vez():
    reg = Registro(critico_ok=False)
    r = interpretar({"texto": "sí", "idioma": "spa", "rol": "personal"}, _pendiente(), client=FakeClient(),
                    **reg.kw())
    assert r.estado == "dicho_con_aviso" and r.accion == "repreguntar" and r.para == "personal"
    assert r.texto_salida.startswith("No quiero decir un dato equivocado: la dosis")
    assert r.paso_fallido == "critico" and r.contexto.receta_pendiente is None


def test_alternancia_le_da_el_turno_al_personal_cuando_hay_receta_pendiente():
    ctx = _pendiente()
    ctx.agregar("personal", "tome agua")  # last human was the staff: alternation alone would pick the patient
    assert servicio.decidir_lado({}, ctx) == ("personal", "alternancia")
