"""The automatic memory: saved only when said, judged by the next turn, used only when approved, never slower."""
import time
from types import SimpleNamespace

from chaski import banco, memoria
from chaski.interprete import DecisionModelo
from chaski.orquestador import Veredicto, _hilos, interpretar
from chaski.traducir import TextoTraducido


def esperar():
    _hilos.submit(lambda: None).result()  # background writes are queued before this one
    time.sleep(0.05)


class Cliente:
    def __init__(self, *decisiones):
        self.decisiones = list(decisiones)
        self.messages = SimpleNamespace(parse=lambda **kw: SimpleNamespace(stop_reason="end_turn",
                                                                           parsed_output=self.decisiones.pop(0)))


def dec(accion, texto, para="paciente", salida="quy"):
    return DecisionModelo(accion=accion, para=para, idioma_salida=salida, texto_pulido=texto, motivo="m",
                          frase_banco_id=None, dato_faltante=None)


def deps(critico_ok=True):
    return dict(traducir_fn=lambda t, de, a: TextoTraducido(texto=f"QUY({t})", de=de, a=a, motor="claude", motor_pedido="claude"),
                guardas_fn=lambda e: Veredicto(ok=True), auditar_fn=lambda e: Veredicto(ok=critico_ok, motivo="x"),
                anticipar=False)


def test_turno_dicho_se_guarda_pendiente_y_la_respuesta_normal_lo_confirma():
    r1 = interpretar({"texto": "Tome la pastilla", "idioma": "spa", "rol": "personal"},
                     client=Cliente(dec("traducir", "Tome la pastilla.")), **deps())
    esperar()
    (e,) = memoria.leer().values()
    assert e["estado"] == "pendiente" and e["es"] == "Tome la pastilla." and e["quy"] == "QUY(Tome la pastilla.)"
    interpretar({"texto": "ari", "idioma": "quy", "rol": "paciente"}, r1.contexto,
                client=Cliente(dec("traducir", "ari", para="personal", salida="spa")), **deps())
    esperar()
    assert memoria.leer()[e["id"]]["estado"] == "confirmada" and memoria.candidatas()[0]["id"] == e["id"]


def test_preguntar_que_dijo_lo_marca_dudosa():
    r1 = interpretar({"texto": "Tome la pastilla", "idioma": "spa", "rol": "personal"},
                     client=Cliente(dec("traducir", "Tome la pastilla.")), **deps())
    interpretar({"texto": "imatataq nin", "idioma": "quy", "rol": "paciente"}, r1.contexto,
                client=Cliente(dec("responder", "Dijo que tome la pastilla.", para="paciente", salida="quy")), **deps())
    esperar()
    assert [e["estado"] for e in memoria.leer().values()][0] == "dudosa"


def test_bloqueado_o_ensayo_no_se_guarda():
    interpretar({"texto": "Tome la pastilla", "idioma": "spa", "rol": "personal"},
                client=Cliente(dec("traducir", "Tome la pastilla.")), **deps(critico_ok=False))
    interpretar({"texto": "Tome la pastilla", "idioma": "spa", "rol": "personal"},
                client=Cliente(dec("traducir", "Tome la pastilla.")), traduccion_forzada="X", **deps())
    esperar()
    assert memoria.leer() == {}


def test_solo_lo_aprobado_es_ejemplo(monkeypatch):
    monkeypatch.setattr(banco, "cargar_items", lambda *a, **k: [])
    monkeypatch.setattr(banco, "_revisados", {})
    monkeypatch.setattr(banco.Banco, "puntajes", lambda self, t, modo="hibrido": banco.Lexico(self.textos).puntajes(t))
    memoria.guardar_turno("personal", "Tome agua", "Tome agua", "Tome agua.", "Yakuta upyay.", "spa", "quy")
    assert banco.ejemplos_revisados("tome agua", "spa") == []
    (e,) = memoria.leer().values()
    memoria.senal(e["id"], "aprobada")
    assert banco.ejemplos_revisados("tome agua", "spa") == [{"es": "Tome agua.", "quy": "Yakuta upyay."}]


def test_un_error_de_memoria_no_rompe_el_turno(monkeypatch):
    def rota(*a, **k):
        raise OSError("disco lleno")

    monkeypatch.setattr(memoria, "_escribir", rota)
    r = interpretar({"texto": "Tome la pastilla", "idioma": "spa", "rol": "personal"},
                    client=Cliente(dec("traducir", "Tome la pastilla.")), **deps())
    assert r.estado == "dicho"


def test_apagada_no_escribe(monkeypatch):
    monkeypatch.setenv("CHASKI_MEMORIA_AUTO", "0")
    interpretar({"texto": "Tome la pastilla", "idioma": "spa", "rol": "personal"},
                client=Cliente(dec("traducir", "Tome la pastilla.")), **deps())
    esperar()
    assert memoria.leer() == {}


def test_una_senal_escrita_antes_que_su_turno_no_se_pierde():
    memoria.senal(memoria.clave("personal", "Tome agua"), "confirmada")
    memoria.guardar_turno("personal", "Tome agua", "Tome agua", "Tome agua.", "Yakuta upyay.", "spa", "quy")
    assert list(memoria.leer().values())[0]["estado"] == "confirmada"
