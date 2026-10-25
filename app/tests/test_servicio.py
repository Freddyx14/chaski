"""The product path end to end with a fake Anthropic client: real guards, the real critic (critico.revisar),
the real bank file, the service handlers. No network."""
import json
import threading
from types import SimpleNamespace

import pytest

from chaski import banco, critico, orquestador, servicio
from chaski.auditoria import Retraduccion
from chaski.guardas import Agregados
from chaski.hechos import Hechos
from chaski.interprete import DecisionModelo

TE = "Tómela con agua, no con té"
TE_PULIDO = "Tómela con agua, no con té."
QUY_BIEN = "Yakuwan upyay, ama tewan upyaychu."
QUY_SIN_NEGACION = "Yakuwan upyay tehawan"  # evals/ataques/banco.jsonl form-p15-C3-negacion: «manan» removed
HECHOS_TE = Hechos(medicamentos=[], proxima_cita_en_dias=None, ir_ya_si=[], prohibiciones=["tomar con té"])
LIMPIO = Agregados(consejos_nuevos=[], diagnosticos_nuevos=[], destinatario_original="paciente",
                   destinatario_version="paciente")


@pytest.fixture(autouse=True)
def _entorno(monkeypatch):
    monkeypatch.delenv("CHASKI_MODELO_PRINCIPAL", raising=False)
    monkeypatch.delenv("CHASKI_MODELO_CRITICO", raising=False)


class FakeClient:
    """Answers by output type, so it works with the critic's parallel calls. Records every call."""

    def __init__(self, decision: DecisionModelo, hechos=HECHOS_TE, retro=TE_PULIDO, agregados=LIMPIO):
        self.decision, self.hechos, self.retro, self.agregados = decision, hechos, retro, agregados
        self.llamadas = []
        self._lock = threading.Lock()
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        with self._lock:
            self.llamadas.append(kw)
        fmt, contenido = kw["output_format"], kw["messages"][0]["content"]
        if fmt is Hechos and isinstance(self.hechos, dict):  # {text: facts}, HECHOS_TE for any other text
            salida = self.hechos.get(contenido, HECHOS_TE)
        else:
            salida = {DecisionModelo: self.decision, Hechos: self.hechos, Agregados: self.agregados,
                      Retraduccion: Retraduccion(castellano=self.retro)}[fmt]
        return SimpleNamespace(stop_reason="end_turn", parsed_output=salida)

    def formatos(self):
        return [k["output_format"].__name__ for k in self.llamadas]


def traducir(texto=TE_PULIDO):
    return DecisionModelo(accion="traducir", para="paciente", idioma_salida="quy", texto_pulido=texto, motivo="m",
                          frase_banco_id=None, dato_faltante=None)


def deps(client, **kw):
    d = orquestador.dependencias(client, **kw)
    d["traducir_fn"] = lambda t, de, a: pytest.fail("en ensayo no se llama al traductor")
    d["candidatos_fn"] = None
    return d


# ── End to end through the real guards and the real critic ──────────────────────────────────────────────────

def test_ensayo_que_quita_la_negacion_sale_bloqueado_y_sembrado():
    c = FakeClient(traducir())
    r = servicio.turno(TE, "spa", "personal", None, traduccion_sembrada=QUY_SIN_NEGACION, dependencias=deps(c))
    assert r["estado"] == "bloqueado" and r["sembrada"] is True and r["texto_salida"] == ""
    assert r["paso_fallido"] == "guardas" and "negación" in r["motivo"]
    assert r["texto_original"] == TE and r["para"] == "personal"
    assert c.formatos() == ["DecisionModelo"]  # B4 in code stopped it before any critic call


def test_sin_las_guardas_lo_ataja_igual_el_critico():
    # Defense in depth: with the code guard switched off, the measured critic still blocks, because the facts of
    # the blind back-translation lost the prohibition (B5).
    c = FakeClient(traducir(), retro="Tómela con agua, con té.",
                   hechos={"Tómela con agua, con té.": Hechos(medicamentos=[], proxima_cita_en_dias=None, ir_ya_si=[])})
    d = deps(c)
    d["guardas_fn"] = lambda e: orquestador.Veredicto(ok=True)
    r = servicio.turno(TE, "spa", "personal", None, traduccion_sembrada=QUY_SIN_NEGACION, dependencias=d)
    assert r["estado"] == "bloqueado" and r["paso_fallido"] == "critico" and "prohibiciones" in r["motivo"]
    assert r["sembrada"] is True


def test_ensayo_correcto_pasa_guardas_y_critico():
    c = FakeClient(traducir())
    r = servicio.turno(TE, "spa", "personal", None, traduccion_sembrada=QUY_BIEN, dependencias=deps(c))
    assert r["estado"] == "dicho", r["motivo"]
    assert r["sembrada"] is True and r["texto_salida"] == QUY_BIEN and r["idioma_salida"] == "quy"
    # Polish differs from the transcript (a final period): both critic paths ran, 6 calls (the Spanish facts are shared), on the critic model.
    criticas = [k for k in c.llamadas if k["output_format"] is not DecisionModelo]
    assert len(criticas) == critico.LLAMADAS_AMBOS
    assert {k["model"] for k in criticas} == {orquestador.MODELO_CRITICO}
    retro = next(k for k in criticas if k["output_format"] is Retraduccion)
    assert retro["messages"][0]["content"] == QUY_BIEN  # blind
    assert r["modelos"] == {"principal": "claude-opus-5", "critico": "claude-sonnet-5"}


def test_pulido_que_agrega_un_numero_se_cambia_por_lo_dicho():
    c = FakeClient(traducir("Tómela con agua tres veces, no con té."))
    r = servicio.turno(TE, "spa", "personal", None, traduccion_sembrada=QUY_BIEN, dependencias=deps(c))
    assert r["texto_pulido"] == TE and "Se usó lo dicho tal cual" in (r["aviso"] or "")


def test_oido_poco_confiable_sobre_un_numero_bloquea():
    c = FakeClient(traducir("Tome dos pastillas."))
    r = servicio.turno("Tome dos pastillas", "spa", "personal", None, confianza="0.4",
                       traduccion_sembrada="Iskay pastillata upyay", dependencias=deps(c))
    assert r["estado"] == "bloqueado" and r["motivo"].startswith("B1")


def test_quechua_a_castellano_se_audita_contra_lo_oido():
    c = FakeClient(DecisionModelo(accion="traducir", para="personal", idioma_salida="spa", texto_pulido="Umaymi nanawan.",
                                  motivo="m", frase_banco_id=None, dato_faltante=None),
                   hechos=Hechos(medicamentos=[], proxima_cita_en_dias=None, ir_ya_si=[]), retro="Me duele la cabeza.")
    d = deps(c)
    d["traducir_fn"] = lambda t, de, a: "Me duele la cabeza."
    r = servicio.turno("umaymi nanawan", "quy", "paciente", None, dependencias=d)
    assert r["estado"] == "dicho" and r["texto_salida"] == "Me duele la cabeza." and r["sembrada"] is False
    retro = next(k for k in c.llamadas if k["output_format"] is Retraduccion)
    assert retro["messages"][0]["content"] == "umaymi nanawan"  # what was heard, not the polish


# ── contexto and n_mejores as the app sends them ────────────────────────────────────────────────────────────

def test_contexto_json_ida_y_vuelta():
    c = FakeClient(traducir())
    r1 = servicio.turno(TE, "spa", "personal", "", traduccion_sembrada=QUY_BIEN, dependencias=deps(c))
    enviado = json.dumps({**r1["contexto"], "modo": "emergencia"})  # what the app sends back next turn
    r2 = servicio.turno(TE, "spa", "personal", enviado, traduccion_sembrada=QUY_BIEN, dependencias=deps(c))
    assert [h["texto"] for h in r2["contexto"]["historial"]] == [TE, TE] and r2["contexto"]["modo"] == "emergencia"
    decisiones = [k for k in c.llamadas if k["output_format"] is DecisionModelo]
    assert "Modo: emergencia" in decisiones[-1]["messages"][0]["content"]
    assert f"personal: {TE}" in decisiones[-1]["messages"][0]["content"]  # the history reached the interpreter
    json.dumps(r2)  # the whole result serialises as the route returns it


def test_contexto_mal_formado_es_un_error_claro():
    with pytest.raises(ValueError, match="contexto"):
        servicio.turno(TE, "spa", "personal", "{no es json", dependencias=deps(FakeClient(traducir())))


@pytest.mark.parametrize("crudo,esperado", [
    (None, []), ("", []), ('["a", " b ", ""]', ["a", "b"]), ('[["kimsa", 0.9], ["kinsa", 0.4]]', ["kimsa", "kinsa"]),
])
def test_n_mejores(crudo, esperado):
    assert servicio.leer_n_mejores(crudo) == esperado


# ── The bank: an unreviewed phrase is never served ──────────────────────────────────────────────────────────

ITEMS = [
    {"id": "rev", "es": "¿Dónde le duele?", "quy": "¿Maypim nanasunki?", "audio": "a.wav", "tags": ["emergencia"], "revisado": True},
    {"id": "sin-rev", "es": "¿Tiene fiebre?", "quy": "¿Rupaywanchu kachkanki?", "audio": None, "tags": ["emergencia"], "revisado": False},
    {"id": "sin-quy", "es": "Respire hondo", "quy": " ", "audio": None, "tags": ["examen"], "revisado": True},
]


@pytest.fixture
def banco_falso(monkeypatch):
    class SinEmbeddings:
        def __call__(self, textos):
            raise AssertionError("no debía cargar el modelo de embeddings")

    b = banco.Banco(ITEMS, codificador=SinEmbeddings())
    monkeypatch.setattr(banco, "_banco", b)
    return b


def test_solo_se_sirve_lo_revisado_con_quechua(banco_falso):
    assert orquestador.frase_servible("rev")["quy"] == "¿Maypim nanasunki?"
    assert orquestador.frase_servible("sin-rev") is None
    assert orquestador.frase_servible("sin-quy") is None
    assert orquestador.frase_servible("no-existe") is None


def test_el_banco_real_no_sirve_nada_sin_revisar(monkeypatch):
    monkeypatch.setattr(banco, "_banco", None)
    items = banco.banco().items
    for it in items:
        if not it.get("revisado"):
            assert orquestador.frase_servible(it["id"]) is None, it["id"]


def test_turno_que_elige_una_frase_sin_revisar_se_traduce(banco_falso):
    c = FakeClient(DecisionModelo(accion="usar_frase_banco", para="paciente", idioma_salida="quy",
                                  texto_pulido="¿Tiene fiebre?", motivo="m", frase_banco_id="sin-rev", dato_faltante=None),
                   hechos=Hechos(medicamentos=[], proxima_cita_en_dias=None, ir_ya_si=[]), retro="¿Tiene fiebre?",
                   agregados=LIMPIO)
    d = orquestador.dependencias(c)
    d["traducir_fn"] = lambda t, de, a: "¿Rupaywanchu kachkanki?"
    d["candidatos_fn"] = lambda t: [{"id": "sin-rev", "es": "¿Tiene fiebre?"}]  # offered anyway: still not served
    r = orquestador.interpretar({"texto": "¿tiene fiebre?", "idioma": "spa", "rol": "personal"}, **d)
    assert r.accion == "traducir" and r.frase_banco_id is None and r.audio is None


def test_turno_con_frase_revisada_la_dice_sin_generar(banco_falso, monkeypatch):
    monkeypatch.setattr(banco_falso, "candidatos", lambda texto, k=20: [{"id": "rev", "es": "¿Dónde le duele?"}])
    c = FakeClient(DecisionModelo(accion="usar_frase_banco", para="paciente", idioma_salida="quy",
                                  texto_pulido="¿Dónde le duele?", motivo="m", frase_banco_id="rev", dato_faltante=None))
    d = orquestador.dependencias(c)
    d["traducir_fn"] = lambda t, de, a: pytest.fail("no se traduce una frase verificada")
    r = orquestador.interpretar({"texto": "¿dónde le duele?", "idioma": "spa", "rol": "personal"}, **d)
    assert (r.estado, r.texto_salida, r.audio) == ("dicho", "¿Maypim nanasunki?", "a.wav")
    assert "rev: ¿Dónde le duele?" in c.llamadas[0]["messages"][0]["content"]  # candidates reached the interpreter


def test_candidatos_servibles_filtra_lo_no_revisado(banco_falso, monkeypatch):
    monkeypatch.setattr(banco_falso, "candidatos", lambda texto, k=20: [{"id": i["id"], "es": i["es"]} for i in ITEMS])
    assert orquestador.candidatos_servibles("¿dónde le duele?") == [{"id": "rev", "es": "¿Dónde le duele?"}]


def test_sin_frases_revisadas_no_se_carga_el_modelo(monkeypatch):
    b = banco.Banco([{**ITEMS[1]}], codificador=lambda t: pytest.fail("cargó el modelo"))
    monkeypatch.setattr(banco, "_banco", b)
    assert orquestador.candidatos_servibles("¿tiene fiebre?") == []


def test_banco_por_tag_devuelve_exactamente_las_claves_de_la_app(banco_falso):
    filas = servicio.banco_por_tag("emergencia")
    assert [f["id"] for f in filas] == ["rev", "sin-rev"]
    assert all(set(f) == {"id", "es", "quy", "audio", "tags", "revisado"} for f in filas)
    assert [f["revisado"] for f in filas] == [True, False]
    assert len(servicio.banco_por_tag(None)) == len(ITEMS)


# ── Models from the environment, and the client ─────────────────────────────────────────────────────────────

def test_modelos_por_defecto_y_desde_el_entorno(monkeypatch):
    assert (orquestador.modelo_principal_env(), orquestador.modelo_critico_env()) == ("claude-opus-5", "claude-sonnet-5")
    d = orquestador.dependencias(FakeClient(traducir()))
    assert d["modelo"] == "claude-opus-5" and d["auditar_fn"].modelo == "claude-sonnet-5"
    monkeypatch.setenv("CHASKI_MODELO_PRINCIPAL", "claude-sonnet-5")
    monkeypatch.setenv("CHASKI_MODELO_CRITICO", "claude-haiku-4-5-20251001")
    c = FakeClient(traducir())
    r = servicio.turno(TE, "spa", "personal", None, traduccion_sembrada=QUY_BIEN, dependencias=deps(c))
    assert r["modelos"] == {"principal": "claude-sonnet-5", "critico": "claude-haiku-4-5-20251001"}
    assert c.llamadas[0]["model"] == "claude-sonnet-5"
    assert {k["model"] for k in c.llamadas[1:]} == {"claude-haiku-4-5-20251001"}
    explicito = orquestador.dependencias(c, modelo_principal="p", modelo_critico="k")
    assert explicito["modelo"] == "p" and explicito["auditar_fn"].modelo == "k"


def test_cliente_se_crea_una_vez_con_la_llave_del_entorno(monkeypatch):
    import anthropic

    creados = []

    class Falso:
        def __init__(self, api_key):
            creados.append(api_key)

    monkeypatch.setattr(anthropic, "Anthropic", Falso)
    monkeypatch.setattr(servicio, "_cliente", None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        servicio.cliente()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "prueba")
    assert servicio.cliente() is servicio.cliente() and creados == ["prueba"]


# ── critico.revisar: the one function the eval and the product share ────────────────────────────────────────

def test_revisar_sin_nada_que_retraducir_no_llama():
    c = FakeClient(traducir())
    r = critico.revisar(c, TE, transcripcion=TE)
    assert r.veredicto.ok and r.llamadas == 0 and c.llamadas == []


def test_revisar_con_pulido_y_quechua_suma_llamadas_y_el_pulido_manda():
    c = FakeClient(traducir(), agregados=Agregados(consejos_nuevos=["descanse"], diagnosticos_nuevos=[],
                                                    destinatario_original="paciente", destinatario_version="paciente"))
    r = critico.revisar(c, TE_PULIDO, quechua=QUY_BIEN, transcripcion=TE, modelo="m")
    assert not r.veredicto.ok and r.llamadas == critico.LLAMADAS_AMBOS and r.pulido is not None
    assert r.veredicto == r.pulido.veredicto


# ── Streaming: decision first, then the same result ─────────────────────────────────────────────────────────

def _eventos(stream):
    salida = []
    for bloque in stream:
        cab, datos = bloque.strip().split("\n")
        salida.append((cab.removeprefix("event: "), json.loads(datos.removeprefix("data: "))))
    return salida


def test_eventos_dan_la_decision_antes_que_el_resultado():
    c = FakeClient(traducir())
    ev = _eventos(servicio.turno_eventos(TE, "spa", "personal", None, traduccion_sembrada=QUY_BIEN,
                                         dependencias=deps(c)))
    assert [e for e, _ in ev] == ["decision", "resultado"]
    assert ev[0][1]["texto_pulido"] == TE_PULIDO and ev[0][1]["accion"] == "traducir"
    assert "ms_decidir" in ev[0][1]
    # the result is exactly what the plain route returns
    plano = servicio.turno(TE, "spa", "personal", None, traduccion_sembrada=QUY_BIEN, dependencias=deps(FakeClient(traducir())))
    assert {k: v for k, v in ev[1][1].items() if k != "ms"} == {k: v for k, v in json.loads(json.dumps(plano, default=str)).items() if k != "ms"}


def test_eventos_bloqueado_igual_llega_como_resultado():
    c = FakeClient(traducir())
    ev = _eventos(servicio.turno_eventos(TE, "spa", "personal", None, traduccion_sembrada=QUY_SIN_NEGACION,
                                         dependencias=deps(c)))
    assert [e for e, _ in ev] == ["decision", "resultado"] and ev[1][1]["estado"] == "bloqueado"


def test_eventos_un_fallo_termina_en_error_no_cuelga():
    ev = _eventos(servicio.turno_eventos(TE, "spa", "personal", "{no es json", dependencias=deps(FakeClient(traducir()))))
    assert [e for e, _ in ev] == ["error"] and "contexto mal formado" in ev[0][1]["error"]


def test_un_al_decidir_que_falla_no_rompe_el_turno():
    c = FakeClient(traducir())

    def explota(_):
        raise RuntimeError("la vista previa falló")

    r = orquestador.interpretar({"texto": TE, "idioma": "spa", "rol": "personal"}, None, traduccion_forzada=QUY_BIEN,
                                al_decidir=explota, **deps(c))
    assert r.estado != "bloqueado" or r.paso_fallido != "decidir"
