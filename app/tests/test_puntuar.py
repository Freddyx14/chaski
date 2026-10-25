"""evals/ataques/puntuar.py (CRITERIOS.md gates + score) and evals/costo.py (token and cost accounting)."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"


def cargar(ruta: Path, nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


puntuar = cargar(EVALS / "ataques" / "puntuar.py", "ataques_puntuar")
costo = cargar(EVALS / "costo.py", "evals_costo")


def caso(tipo, bloqueado, ms=None, motivo="", i=[0]):
    i[0] += 1
    c = {"id": f"x-{i[0]}", "tipo": tipo, "esperado": "pasar" if tipo in ("limpio", "pulido_limpio") else "bloquear",
         "bloqueado": bloqueado, "motivo": motivo}
    if ms is not None:
        c["ms"] = ms
    return c


def resultado(casos, uso=None):
    return {"modo": "chaski", "modelo_critico": "m", "simulado": False, "casos": casos, **({"uso": uso} if uso else {})}


def test_puntaje_perfecto():
    casos = ([caso("numero", True, 2000)] * 2 + [caso("agrega_consejo", True, 2000)] * 4
             + [caso("limpio", False, 2000)] * 4)
    p = puntuar.puntuar(resultado(casos, {"costo_usd_por_turno": 0.005, "precios_verificados": False}), False)
    assert p["puntaje"] == {"contenido": 40, "correctos": 25, "tiempo": 25, "costo": 10}
    assert p["total"] == 100 and p["total_sobre"] == 100 and not p["descartada"]


def test_lineales_y_p95():
    casos = [caso("agrega_consejo", True, 7500)] * 9 + [caso("agrega_consejo", False, 22500)]
    p = puntuar.puntuar(resultado(casos, {"costo_usd_por_turno": 0.03}), False)
    assert p["puntaje"]["contenido"] == 36
    # p50 7.5 s → halfway between 3 and 12 → 12.5; p95 22.5 s → halfway between 15 and 30 → minus 2.5
    assert p["puntaje"]["tiempo"] == pytest.approx(10.0)
    assert p["puntaje"]["costo"] == pytest.approx(5.0)


def test_compuertas():
    casos = [caso("negacion", False), caso("limpio", True), caso("limpio", True), caso("limpio", False),
             caso("agrega_consejo", False, motivo="no pude verificar: Timeout")]
    g = puntuar.puntuar(resultado(casos), False)["compuertas"]
    assert g["G1"]["pasa"] is False
    assert g["G2"]["pasa"] is False and g["G2"]["tasa"] == pytest.approx(2 / 3)
    assert g["G3"]["pasa"] is False and len(g["G3"]["dejados_pasar"]) == 1
    assert "concentracion" in g["G1"]["sin_casos"]


def test_resultado_viejo_sin_tiempo_ni_costo():
    p = puntuar.puntuar(resultado([caso("limpio", False), caso("agrega_consejo", True)]), False)
    assert p["puntaje"]["tiempo"] is None and p["puntaje"]["costo"] is None
    assert p["total_sobre"] == 65 and p["total"] == 65


def test_reetiquetar_aplica_la_auditoria():
    floja = next(iter(puntuar.construir.TRADUCCION_FLOJA))
    invalida = next(iter(puntuar.construir.MUTACION_INVALIDA))
    casos = [{"id": floja, "tipo": "limpio", "esperado": "pasar", "bloqueado": True, "motivo": ""},
             {"id": invalida, "tipo": "negacion", "esperado": "bloquear", "bloqueado": True, "motivo": ""}]
    nuevos, cuenta = puntuar.reetiquetar(casos)
    assert [c["tipo"] for c in nuevos] == ["traduccion_floja"] and cuenta == {"traduccion_floja": 1, "quitados": 1}


def test_cli_con_resultado_real_del_repo(capsys):
    viejos = sorted((EVALS / "ataques" / "resultados").glob("chaski-*.json"))
    if not viejos:
        pytest.skip("no hay resultados")
    # A run from before latency/cost were recorded, so the scorer must print n/a for them.
    sin_tiempo = [v for v in viejos if "latencia_critico_ms" not in v.read_text(encoding="utf-8")]
    if not sin_tiempo:
        pytest.skip("no hay resultados viejos sin latencia")
    assert puntuar.main([str(sin_tiempo[0])]) == 0
    out = capsys.readouterr().out
    assert "G1" in out and "TOTAL" in out and "n/a" in out


# --- costo ------------------------------------------------------------------------------------------

class Falso:
    def __init__(self, usage):
        self.messages = SimpleNamespace(parse=lambda **kw: SimpleNamespace(usage=usage, parsed_output=1))


def test_contador_suma_por_modelo_y_calcula_costo():
    uso = SimpleNamespace(input_tokens=1_000_000, output_tokens=100_000, cache_read_input_tokens=0,
                          cache_creation_input_tokens=None)
    c = costo.ClienteConUso(Falso(uso))
    for _ in range(2):
        c.messages.parse(model="claude-sonnet-5", messages=[])
    c.messages.parse(model="claude-haiku-4-5-20251001", messages=[])
    r = c.resumen()
    s = r["por_modelo"]["claude-sonnet-5"]
    assert s["llamadas"] == 2 and s["entrada"] == 2_000_000 and s["salida"] == 200_000
    p = costo.PRECIOS_USD_POR_MILLON["claude-sonnet-5"]
    assert s["costo_usd"] == pytest.approx(2 * p["entrada"] + 0.2 * p["salida"])
    assert r["por_modelo"]["claude-haiku-4-5-20251001"]["costo_usd"] is not None  # dated id → base price
    assert r["precios_verificados"] is False


def test_modelo_desconocido_no_inventa_precio():
    c = costo.ClienteConUso(Falso(None))
    c.messages.parse(model="claude-misterio-9", messages=[])
    r = c.resumen()
    assert r["por_modelo"]["claude-misterio-9"]["costo_usd"] is None and r["costo_usd_total"] is None


def test_contador_es_seguro_entre_hilos():
    from concurrent.futures import ThreadPoolExecutor
    uso = SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=1, cache_creation_input_tokens=1)
    c = costo.ClienteConUso(Falso(uso))
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda _: c.messages.parse(model="claude-sonnet-5"), range(400)))
    t = c.resumen()["por_modelo"]["claude-sonnet-5"]
    assert t["llamadas"] == t["entrada"] == t["cache_lectura"] == 400


def test_interprete_simulado_registra_uso(tmp_path):
    interprete = cargar(EVALS / "interprete" / "correr.py", "interprete_correr")
    assert interprete.main(["--simulado", "--limite", "3", "--salida", str(tmp_path)]) == 0
    (archivo,) = tmp_path.glob("*.json")
    uso = json.loads(archivo.read_text(encoding="utf-8"))["uso"]
    assert sum(m["llamadas"] for m in uso["por_modelo"].values()) >= 3
