"""Each action path through the orchestrator, and fail-closed on every step. All dependencies are fakes."""
from types import SimpleNamespace

import pytest

from chaski import auditoria
from chaski.hechos import Hechos, Medicamento
from chaski.interprete import NO_ENTENDI, Contexto, DecisionModelo
from chaski.orquestador import MODELO_CRITICO, NO_PUDE, Critica, Veredicto, critico, interpretar
from chaski.traducir import TextoTraducido


class FakeClient:
    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.llamadas.append(kw)
        salida = self.respuestas.pop(0)
        if isinstance(salida, Exception):
            raise salida
        assert isinstance(salida, kw["output_format"]), f"esperaba {kw['output_format'].__name__}"
        return SimpleNamespace(stop_reason="end_turn", parsed_output=salida)


def propuesta(accion, texto, banco=None, dato=None):
    return DecisionModelo(accion=accion, para="paciente", idioma_salida="quy", texto_pulido=texto, motivo="m",
                          frase_banco_id=banco, dato_faltante=dato)


class Registro:
    """Fake traducir/guardas/auditar/banco that record their calls."""

    def __init__(self, guardas=None, auditoria_ok=True, banco=None, traduccion=None):
        self.llamadas = []
        self.guardas_respuestas = list(guardas or [])
        self.auditoria_ok = auditoria_ok
        self.banco = banco
        self.traduccion = traduccion

    def traducir(self, texto, de, a):
        self.llamadas.append(("traducir", texto, de, a))
        if isinstance(self.traduccion, Exception):
            raise self.traduccion
        return TextoTraducido(texto=f"[{a}] {texto}", de=de, a=a, motor="nllb", motor_pedido="nllb")

    def guardas(self, entrada):
        self.llamadas.append(("guardas", entrada))
        return self.guardas_respuestas.pop(0) if self.guardas_respuestas else Veredicto(ok=True)

    def auditar(self, e):
        self.llamadas.append(("critico", e.pulido, e.traduccion, e.de, e.a))
        return Veredicto(ok=self.auditoria_ok, motivo="cambió un dato crítico: paracetamol.cada_horas")

    def banco_fn(self, frase_id):
        self.llamadas.append(("banco", frase_id))
        return self.banco

    def kw(self):
        return dict(traducir_fn=self.traducir, guardas_fn=self.guardas, auditar_fn=self.auditar, banco_fn=self.banco_fn)

    def pasos(self):
        return [ll[0] for ll in self.llamadas]


PERSONAL = dict(idioma="spa", rol="personal")
PACIENTE = dict(idioma="quy", rol="paciente")
ORDEN = "este… que tome una pastilla de paracetamol cada ocho horas"
PULIDO = "Tome una pastilla de paracetamol cada ocho horas."


def test_traducir_pasa_todo_y_se_dice():
    r_ = Registro()
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)), **r_.kw())
    assert r.estado == "dicho" and r.accion == "traducir" and r.para == "paciente" and r.idioma_salida == "quy"
    assert r.texto_salida == f"[quy] {PULIDO}" and r.motor == "nllb"
    assert r_.pasos() == ["traducir", "guardas", "critico"]
    assert r_.llamadas[0][1:] == (PULIDO, "spa", "quy")
    assert r.contexto.historial[-1].texto == ORDEN
    assert set(r.ms) >= {"decidir", "traducir", "guardas", "critico", "total"}
    assert r.modelos == {"principal": "claude-sonnet-5", "critico": None}


def test_auditoria_que_falla_bloquea():
    r_ = Registro(auditoria_ok=False)
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)), **r_.kw())
    assert r.estado == "bloqueado" and r.texto_salida == "" and r.para == "personal"
    assert "cada_horas" in r.motivo and r.aviso.startswith(NO_PUDE) and r.paso_fallido == "critico"


def test_guarda_que_falla_bloquea_sin_auditar():
    r_ = Registro(guardas=[Veredicto(ok=False, motivo="B3: dato nuevo")])
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)), **r_.kw())
    assert r.estado == "bloqueado" and "B3" in r.motivo and "critico" not in r_.pasos()


def test_guarda_pide_literal_se_retraduce_lo_dicho_con_aviso():
    r_ = Registro(guardas=[Veredicto(ok=False, usar_literal=True, motivo="el pulido cambió la dosis"), Veredicto(ok=True)])
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", "Tome dos pastillas.")), **r_.kw())
    assert r.estado == "dicho_con_aviso" and r.texto_pulido == ORDEN and "cambió la dosis" in r.aviso
    traducciones = [ll for ll in r_.llamadas if ll[0] == "traducir"]
    assert [t[1] for t in traducciones] == ["Tome dos pastillas.", ORDEN]
    assert r_.llamadas[-1] == ("critico", ORDEN, f"[quy] {ORDEN}", "spa", "quy")


def test_literal_que_tampoco_pasa_bloquea():
    r_ = Registro(guardas=[Veredicto(ok=False, usar_literal=True, motivo="x"), Veredicto(ok=False, motivo="sigue mal")])
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", "otra")), **r_.kw())
    assert r.estado == "bloqueado" and "sigue mal" in r.motivo


def test_aviso_de_guarda_da_dicho_con_aviso():
    r_ = Registro(guardas=[Veredicto(ok=True, aviso="confianza baja del reconocimiento")])
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)), **r_.kw())
    assert r.estado == "dicho_con_aviso" and "confianza baja" in r.aviso


def test_frase_banco_no_genera_nada():
    r_ = Registro(banco={"id": "dolor-donde", "es": "¿Dónde le duele?", "quy": "¿Maypim nanasunki?", "audio": "https://a/1.wav"})
    turno = {"texto": "¿dónde le duele?", "candidatas": [{"id": "dolor-donde", "es": "¿Dónde le duele?"}], **PERSONAL}
    r = interpretar(turno, client=FakeClient(propuesta("usar_frase_banco", "x", banco="dolor-donde")), **r_.kw())
    assert r.estado == "dicho" and r.accion == "usar_frase_banco" and r.frase_banco_id == "dolor-donde"
    assert (r.texto_salida, r.audio) == ("¿Maypim nanasunki?", "https://a/1.wav")
    assert r_.pasos() == ["banco"]


def test_banco_sin_item_traduce_lo_dicho():
    r_ = Registro(banco=None)
    turno = {"texto": "¿dónde le duele?", "candidatas": [{"id": "dolor-donde", "es": "¿Dónde le duele?"}], **PERSONAL}
    r = interpretar(turno, client=FakeClient(propuesta("usar_frase_banco", "x", banco="dolor-donde")), **r_.kw())
    assert r.accion == "traducir" and r.frase_banco_id is None and r.estado == "dicho"
    assert r_.pasos() == ["banco", "traducir", "guardas", "critico"]


def test_repreguntar_al_paciente_se_traduce_y_audita():
    r_ = Registro()
    r = interpretar({"texto": "nanawanmi", **PACIENTE},
                    client=FakeClient(propuesta("repreguntar", "¿Dónde le duele?", dato="parte_del_cuerpo")), **r_.kw())
    assert r.accion == "repreguntar" and r.para == "paciente" and r.idioma_salida == "quy"
    assert r.dato_faltante == "parte_del_cuerpo" and r.texto_salida == "[quy] ¿Dónde le duele?"
    assert r_.llamadas[0][1:] == ("¿Dónde le duele?", "spa", "quy") and "critico" in r_.pasos()
    assert r.contexto.repreguntas_seguidas == ["parte_del_cuerpo"]
    assert r.contexto.historial[-1].rol == "chaski"


def test_repreguntar_al_personal_no_se_traduce_pero_el_critico_lo_revisa():
    r_ = Registro()
    r = interpretar({"texto": "dele el antibiótico", **PERSONAL},
                    client=FakeClient(propuesta("repreguntar", "¿Qué antibiótico?", dato="medicamento")), **r_.kw())
    assert r.para == "personal" and r.texto_salida == "¿Qué antibiótico?" and r_.pasos() == ["guardas", "critico"]


def test_responder_al_personal_lleva_el_historial_a_las_guardas():
    r_ = Registro()
    ctx = Contexto(historial=[{"rol": "paciente", "texto": "wiksaymi nanawan (en castellano: me duele la barriga)"}])
    r = interpretar({"texto": "¿qué dijo?", **PERSONAL}, ctx,
                    client=FakeClient(propuesta("responder", "Dijo que le duele la barriga.")), **r_.kw())
    assert r.accion == "responder" and r.para == "personal" and r.texto_salida == "Dijo que le duele la barriga."
    entrada = r_.llamadas[0][1]
    assert "me duele la barriga" in entrada.fuente and r_.pasos() == ["guardas", "critico"]


def test_no_entendi_dice_la_frase_fija_sin_traducir():
    r_ = Registro()
    r = interpretar({"texto": "asdf la la", **PACIENTE}, client=FakeClient(propuesta("no_entendi", "x")), **r_.kw())
    assert r.estado == "dicho" and r.texto_salida == NO_ENTENDI["quy"] and r_.pasos() == []


def test_paciente_traducido_queda_en_el_historial_con_su_castellano():
    r_ = Registro()
    r = interpretar({"texto": "umaymi nanawan", **PACIENTE}, client=FakeClient(propuesta("traducir", "Umaymi nanawan.")), **r_.kw())
    assert r.para == "personal" and r.idioma_salida == "spa"
    assert "(en castellano: [spa] Umaymi nanawan.)" in r.contexto.historial[-1].texto


def test_segunda_repregunta_sale_con_aviso_y_contexto_persistido():
    r_ = Registro()
    c = FakeClient(propuesta("repreguntar", "¿Dónde?", dato="parte_del_cuerpo"), propuesta("repreguntar", "¿Dónde?", dato="parte_del_cuerpo"))
    r1 = interpretar({"texto": "nanawan", **PACIENTE}, client=c, **r_.kw())
    r2 = interpretar({"texto": "kaypi", **PACIENTE}, r1.contexto.model_dump(), client=c, **r_.kw())
    assert r2.accion == "traducir" and r2.estado == "dicho_con_aviso" and r2.texto_pulido == "kaypi"


@pytest.mark.parametrize("paso", ["decidir", "traducir", "guardas", "critico"])
def test_falla_cerrada_en_cada_paso(paso):
    r_ = Registro(traduccion=RuntimeError("timeout") if paso == "traducir" else None)
    kw = r_.kw()
    if paso == "guardas":
        kw["guardas_fn"] = lambda e: (_ for _ in ()).throw(RuntimeError("x"))
    if paso == "critico":
        kw["auditar_fn"] = lambda e: (_ for _ in ()).throw(RuntimeError("x"))
    salida = RuntimeError("api caída") if paso == "decidir" else propuesta("traducir", PULIDO)
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(salida), **kw)
    assert r.estado == "bloqueado" and r.paso_fallido == paso and r.texto_salida == ""
    assert r.aviso.startswith(NO_PUDE)


def test_veredicto_mal_formado_bloquea():
    r_ = Registro()
    kw = r_.kw()
    kw["guardas_fn"] = lambda e: "sí"
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)), **kw)
    assert r.estado == "bloqueado"


def test_traduccion_vacia_bloquea():
    r_ = Registro()
    kw = r_.kw()
    kw["traducir_fn"] = lambda t, de, a: "  "
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)), **kw)
    assert r.estado == "bloqueado" and r.paso_fallido == "traducir"


def test_stubs_por_defecto_dejan_pasar_y_el_critico_corre_igual():
    r_ = Registro()
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)),
                    traducir_fn=r_.traducir, auditar_fn=r_.auditar)
    assert r.estado == "dicho" and r_.pasos() == ["traducir", "critico"]


HECHOS = Hechos(medicamentos=[Medicamento(nombre="paracetamol", cantidad=1, unidad="pastilla", cada_horas=8, dias=3, momento=None)],
                proxima_cita_en_dias=None, ir_ya_si=[])
LIMPIA = Critica(datos_agregados=[], datos_cambiados=[], datos_omitidos=[], obedece_al_texto=False, inapropiado=False, motivo="ok")


class ClienteCritico:
    """Answers the critic's calls by output type (they run in threads, so order is not stable)."""

    def __init__(self, critica=LIMPIA, hechos_retro=HECHOS, retro="Tome una pastilla de paracetamol cada ocho horas por tres días."):
        self.critica, self.hechos_retro, self.retro = critica, hechos_retro, retro
        self.llamadas = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.llamadas.append(kw)
        fmt, contenido = kw["output_format"], kw["messages"][0]["content"]
        if fmt is auditoria.Retraduccion:
            salida = auditoria.Retraduccion(castellano=self.retro)
        elif fmt is Critica:
            salida = self.critica
        else:
            salida = self.hechos_retro if contenido == self.retro else HECHOS
        return SimpleNamespace(stop_reason="end_turn", parsed_output=salida)


def revision(accion="traducir", de="spa", a="quy", traduccion="(quechua)"):
    from chaski.orquestador import EntradaRevision
    return EntradaRevision(accion=accion, original=ORDEN, fuente=ORDEN, pulido=PULIDO, traduccion=traduccion, de=de, a=a)


def test_critico_usa_haiku_por_defecto_y_lo_registra():
    c = ClienteCritico()
    revisar = critico(c)
    assert revisar(revision()).ok is True
    assert revisar.modelo == MODELO_CRITICO == "claude-haiku-4-5-20251001"
    assert {k["model"] for k in c.llamadas} == {MODELO_CRITICO}
    assert all(k["system"][0]["cache_control"] == {"type": "ephemeral"} for k in c.llamadas)
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)),
                    traducir_fn=lambda t, de, a: "(quechua)", auditar_fn=critico(ClienteCritico(), "claude-x"))
    assert r.modelos == {"principal": "claude-sonnet-5", "critico": "claude-x"} and "critico" in r.ms


def test_critico_retraduce_a_ciegas_y_el_codigo_compara_hechos():
    mal = HECHOS.model_copy(deep=True)
    mal.medicamentos[0].cada_horas = 6
    c = ClienteCritico(hechos_retro=mal, retro="cada seis horas")
    v = critico(c)(revision())
    assert v.ok is False and "cada_horas" in v.motivo
    retraduccion = next(k for k in c.llamadas if k["output_format"] is auditoria.Retraduccion)
    assert retraduccion["messages"][0]["content"] == "(quechua)"  # blind: never sees the original
    juicio = next(k for k in c.llamadas if k["output_format"] is Critica)
    assert "cada seis horas" in juicio["messages"][0]["content"] and ORDEN in juicio["messages"][0]["content"]


@pytest.mark.parametrize("campo,valor,accion,bloquea", [
    ("datos_agregados", ["después de comer"], "traducir", True),
    ("datos_cambiados", ["no tome con té → tome con té"], "traducir", True),
    ("datos_omitidos", ["por tres días"], "traducir", True),
    ("datos_omitidos", ["por tres días"], "repreguntar", False),  # a question naturally leaves things out
    ("obedece_al_texto", True, "traducir", True),
    ("inapropiado", True, "responder", True),
])
def test_cualquier_marca_del_critico_bloquea(campo, valor, accion, bloquea):
    c = ClienteCritico(critica=LIMPIA.model_copy(update={campo: valor}))
    v = critico(c)(revision(accion=accion, de="spa", a="spa", traduccion=PULIDO))
    assert v.ok is (not bloquea)
    assert not any(k["output_format"] is auditoria.Retraduccion for k in c.llamadas)  # Spanish out: no back-translation


def test_critico_sin_respuesta_falla_cerrado_en_el_turno():
    class Rechaza(ClienteCritico):
        def _parse(self, **kw):
            return SimpleNamespace(stop_reason="refusal", parsed_output=None)

    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)),
                    traducir_fn=lambda t, de, a: "(quechua)", auditar_fn=critico(Rechaza()))
    assert r.estado == "bloqueado" and r.paso_fallido == "critico"
