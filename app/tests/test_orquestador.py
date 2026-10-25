"""Each action path through the orchestrator, and fail-closed on every step. All dependencies are fakes."""
from types import SimpleNamespace

import pytest

from chaski.interprete import NO_ENTENDI, Contexto, DecisionModelo
from chaski.orquestador import MODELO_PRINCIPAL, NO_PUDE, Veredicto, interpretar
from chaski.traducir import TextoTraducido


@pytest.fixture(autouse=True)
def _sin_modelos_en_el_entorno(monkeypatch):
    # These tests pin the step-by-step path; the anticipated one is tested with anticipar=True explicitly.
    monkeypatch.setenv("CHASKI_TRADUCIR_ANTICIPADO", "0")
    monkeypatch.setenv("CHASKI_REPREGUNTAR_AL_BLOQUEAR", "0")  # these pin the plain block; the ask-back has its own tests
    monkeypatch.delenv("CHASKI_MODELO_PRINCIPAL", raising=False)
    monkeypatch.delenv("CHASKI_MODELO_CRITICO", raising=False)


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
    assert r.modelos == {"principal": MODELO_PRINCIPAL, "critico": None}
    assert r.texto_original == ORDEN and r.sembrada is False


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


def test_guardas_por_defecto_son_las_reales_y_frenan_antes_del_critico():
    r_ = Registro()
    r = interpretar({"texto": "Tómela con agua, no con té", **PERSONAL},
                    client=FakeClient(propuesta("traducir", "Tómela con agua, no con té.")),
                    traducir_fn=lambda t, de, a: "Yakuwan upyay tehawan", auditar_fn=r_.auditar)
    assert r.estado == "bloqueado" and r.paso_fallido == "guardas" and "negación" in r.motivo
    assert r_.pasos() == []  # the critic never ran: code blocked first, for free


def test_sin_banco_fn_una_frase_del_banco_se_traduce():
    r_ = Registro()
    turno = {"texto": "¿dónde le duele?", "candidatas": [{"id": "dolor-donde", "es": "¿Dónde le duele?"}], **PERSONAL}
    r = interpretar(turno, client=FakeClient(propuesta("usar_frase_banco", "x", banco="dolor-donde")),
                    traducir_fn=r_.traducir, guardas_fn=r_.guardas, auditar_fn=r_.auditar)
    assert r.accion == "traducir" and r.estado == "dicho" and r_.pasos() == ["traducir", "guardas", "critico"]


def test_traduccion_forzada_reemplaza_al_traductor_y_marca_sembrada():
    r_ = Registro()
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)), **r_.kw(),
                    traduccion_forzada="(quechua sembrado)")
    assert r.sembrada is True and r.estado == "dicho" and r.texto_salida == "(quechua sembrado)"
    assert "traducir" not in r_.pasos() and r_.pasos() == ["guardas", "critico"]
    assert r_.llamadas[-1][2] == "(quechua sembrado)"


def test_traduccion_forzada_no_usa_el_banco_para_que_se_revise_lo_sembrado():
    r_ = Registro(banco={"id": "dolor-donde", "es": "¿Dónde le duele?", "quy": "¿Maypim nanasunki?", "audio": None})
    turno = {"texto": "¿dónde le duele?", "candidatas": [{"id": "dolor-donde", "es": "¿Dónde le duele?"}], **PERSONAL}
    r = interpretar(turno, client=FakeClient(propuesta("usar_frase_banco", "x", banco="dolor-donde")), **r_.kw(),
                    traduccion_forzada="(sembrado)")
    assert r.sembrada and r.accion == "traducir" and "banco" not in r_.pasos() and r.texto_salida == "(sembrado)"


def test_bloqueado_lleva_texto_original_y_sembrada():
    r_ = Registro(auditoria_ok=False)
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=FakeClient(propuesta("traducir", PULIDO)), **r_.kw(),
                    traduccion_forzada="x")
    assert r.estado == "bloqueado" and r.texto_original == ORDEN and r.sembrada is True


def test_candidatos_del_banco_llegan_al_interprete_solo_en_turnos_del_personal():
    vistos = []
    r_ = Registro()

    def candidatos(texto):
        vistos.append(texto)
        return [{"id": "dolor-donde", "es": "¿Dónde le duele?"}]

    c = FakeClient(propuesta("traducir", PULIDO), propuesta("traducir", "Umaymi nanawan."))
    interpretar({"texto": ORDEN, **PERSONAL}, client=c, candidatos_fn=candidatos, **r_.kw())
    assert vistos == [ORDEN] and "dolor-donde: ¿Dónde le duele?" in c.llamadas[0]["messages"][0]["content"]
    interpretar({"texto": "umaymi nanawan", **PACIENTE}, client=c, candidatos_fn=candidatos, **r_.kw())
    assert vistos == [ORDEN]  # the bank holds staff phrases: never looked up for the patient


def test_candidatos_dados_no_se_reemplazan():
    r_ = Registro()
    turno = {"texto": ORDEN, "candidatas": [{"id": "x", "es": "y"}], **PERSONAL}
    interpretar(turno, client=FakeClient(propuesta("traducir", PULIDO)),
                candidatos_fn=lambda t: pytest.fail("no debía buscar"), **r_.kw())


@pytest.mark.parametrize("falla", [RuntimeError("fastembed caído"), [{"sin_id": 1}]])
def test_banco_que_falla_no_rompe_el_turno(falla):
    r_ = Registro()

    def candidatos(texto):
        if isinstance(falla, Exception):
            raise falla
        return falla

    c = FakeClient(propuesta("traducir", PULIDO))
    r = interpretar({"texto": ORDEN, **PERSONAL}, client=c, candidatos_fn=candidatos, **r_.kw())
    assert r.estado == "dicho" and "Candidatas del banco verificado: ninguna" in c.llamadas[0]["messages"][0]["content"]


# ── Latency paths: anticipated translation and voice during the critic ───────────────────────────────────────

CRUDO = "ya este… que tome el paracetamol cada ocho horas"
PULIDO = "Tome el paracetamol cada ocho horas."


def test_anticipada_se_usa_y_pasa_por_todas_las_barreras():
    r = Registro()
    res = interpretar({"texto": CRUDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      anticipar=True, **r.kw())
    assert res.estado == "dicho" and res.anticipada is True
    assert res.texto_salida == f"[quy] {CRUDO}" and res.texto_pulido == PULIDO
    assert [x for x in r.llamadas if x[0] == "traducir"] == [("traducir", CRUDO, "spa", "quy")]  # one call, no retry
    critico = [x for x in r.llamadas if x[0] == "critico"][0]
    assert critico[1] == PULIDO  # the critic still checks against the polish (and the transcript)


def test_anticipada_rechazada_por_guardas_vuelve_al_camino_normal():
    r = Registro(guardas=[Veredicto(ok=False, motivo="B4: falta pusaq")])
    res = interpretar({"texto": CRUDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      anticipar=True, **r.kw())
    assert res.estado == "dicho" and res.anticipada is False
    assert res.texto_salida == f"[quy] {PULIDO}"
    assert [x[1] for x in r.llamadas if x[0] == "traducir"] == [CRUDO, PULIDO]


def test_anticipada_rechazada_por_el_critico_reintenta_y_si_falla_bloquea():
    r = Registro(auditoria_ok=False)
    res = interpretar({"texto": CRUDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      anticipar=True, **r.kw())
    assert res.estado == "bloqueado" and res.paso_fallido == "critico"
    assert len([x for x in r.llamadas if x[0] == "critico"]) == 2  # anticipated, then the normal path


def test_anticipada_no_se_usa_si_la_accion_no_es_traducir():
    r = Registro()
    res = interpretar({"texto": "¿cuántas veces?", "idioma": "spa", "rol": "personal"},
                      client=FakeClient(propuesta("repreguntar", "¿Cuántas veces al día?", dato="frecuencia")),
                      anticipar=True, **r.kw())
    assert res.anticipada is False and res.accion == "repreguntar"


def test_sin_anticipar_es_el_camino_de_siempre():
    r = Registro()
    res = interpretar({"texto": CRUDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      anticipar=False, **r.kw())
    assert res.anticipada is False and [x[1] for x in r.llamadas if x[0] == "traducir"] == [PULIDO]


def test_voz_se_adjunta_solo_si_el_critico_pasa():
    r = Registro()
    res = interpretar({"texto": PULIDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      anticipar=False, voz_fn=lambda t, a: b"RIFF", **r.kw())
    assert res.estado == "dicho" and res.audio_wav_b64 == "UklGRg==" and "voz" in res.ms


def test_voz_no_sale_si_el_critico_bloquea():
    r = Registro(auditoria_ok=False)
    res = interpretar({"texto": PULIDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      anticipar=False, voz_fn=lambda t, a: b"RIFF", **r.kw())
    assert res.estado == "bloqueado" and res.audio_wav_b64 is None


def test_voz_que_falla_no_bloquea():
    def rota(t, a):
        raise RuntimeError("GPU")

    r = Registro()
    res = interpretar({"texto": PULIDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      anticipar=False, voz_fn=rota, **r.kw())
    assert res.estado == "dicho_con_aviso" and res.audio_wav_b64 is None and "sin audio" in res.aviso


def test_ejemplos_para_respeta_el_interruptor_y_no_rompe(monkeypatch):
    from chaski import banco as b
    from chaski import orquestador as o
    monkeypatch.setattr(b, "ejemplos_revisados", lambda texto, idioma: [{"es": "x", "quy": "y"}])
    monkeypatch.setenv("CHASKI_EJEMPLOS", "1")
    assert o.ejemplos_para("hola", "spa") == [{"es": "x", "quy": "y"}]
    monkeypatch.setenv("CHASKI_EJEMPLOS", "0")
    assert o.ejemplos_para("hola", "spa") is None

    def rota(texto, idioma):
        raise RuntimeError("sin embeddings")

    monkeypatch.setenv("CHASKI_EJEMPLOS", "1")
    monkeypatch.setattr(b, "ejemplos_revisados", rota)
    assert o.ejemplos_para("hola", "spa") is None


# ── A block asks back once before giving up ──────────────────────────────────────────────────────────────────────

def test_bloqueo_del_personal_pregunta_el_dato_y_no_dice_nada_al_paciente(monkeypatch):
    monkeypatch.setenv("CHASKI_REPREGUNTAR_AL_BLOQUEAR", "1")
    r = Registro(auditoria_ok=False)  # motivo: «cambió un dato crítico: paracetamol.cada_horas»
    res = interpretar({"texto": PULIDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      **r.kw())
    assert res.accion == "repreguntar" and res.para == "personal" and res.idioma_salida == "spa"
    assert "cada cuánto" in res.texto_salida and "[quy]" not in res.texto_salida
    assert res.dato_faltante == "frecuencia" and res.paso_fallido == "critico"


def test_el_segundo_bloqueo_seguido_ya_no_pregunta(monkeypatch):
    monkeypatch.setenv("CHASKI_REPREGUNTAR_AL_BLOQUEAR", "1")
    r = Registro(auditoria_ok=False)
    res1 = interpretar({"texto": PULIDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                       **r.kw())
    res2 = interpretar({"texto": PULIDO, "idioma": "spa", "rol": "personal"}, res1.contexto,
                       client=FakeClient(propuesta("traducir", PULIDO)), **r.kw())
    assert res1.accion == "repreguntar" and res2.estado == "bloqueado"


def test_bloqueo_del_paciente_le_pide_repetir_en_quechua(monkeypatch):
    monkeypatch.setenv("CHASKI_REPREGUNTAR_AL_BLOQUEAR", "1")
    r = Registro(auditoria_ok=False)
    p = DecisionModelo(accion="traducir", para="personal", idioma_salida="spa", texto_pulido="umaymi nanan", motivo="m",
                       frase_banco_id=None, dato_faltante=None)
    res = interpretar({"texto": "umaymi nanan", "idioma": "quy", "rol": "paciente"}, client=FakeClient(p), **r.kw())
    assert res.accion == "no_entendi" and res.para == "paciente" and res.idioma_salida == "quy"
    assert res.texto_salida == NO_ENTENDI["quy"]


def test_ensayo_y_fallas_de_sistema_siguen_siendo_bloqueo(monkeypatch):
    monkeypatch.setenv("CHASKI_REPREGUNTAR_AL_BLOQUEAR", "1")
    r = Registro(auditoria_ok=False)
    res = interpretar({"texto": PULIDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      traduccion_forzada="X", **r.kw())
    assert res.estado == "bloqueado"  # the rehearsal shows the barrier
    r2 = Registro(traduccion=RuntimeError("red"))
    res2 = interpretar({"texto": PULIDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                       **r2.kw())
    assert res2.estado == "bloqueado"  # a broken step is not a doubt about the data


def test_la_pregunta_tras_un_bloqueo_viene_con_la_voz_del_servicio(monkeypatch):
    monkeypatch.setenv("CHASKI_REPREGUNTAR_AL_BLOQUEAR", "1")
    r = Registro(auditoria_ok=False)
    dichos = []
    res = interpretar({"texto": PULIDO, "idioma": "spa", "rol": "personal"}, client=FakeClient(propuesta("traducir", PULIDO)),
                      voz_fn=lambda t, a: dichos.append((t, a)) or b"RIFF", **r.kw())
    assert res.accion == "repreguntar" and res.audio_wav_b64 == "UklGRg=="
    assert dichos == [(res.texto_salida, "spa")]
