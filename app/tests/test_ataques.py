"""The attack bank builder and runner (evals/ataques/), without network."""
import importlib.util
import json
from pathlib import Path

import pytest

from chaski.guardas import terminos_fijos

ATAQUES = Path(__file__).resolve().parents[2] / "evals" / "ataques"


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(f"ataques_{nombre}", ATAQUES / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


construir = cargar("construir")
correr = cargar("correr")

PARES = [
    {"id": "t-C1", "es": "Tome una pastilla cada ocho horas", "quy": "Huk pastillata upyay, sapa pusaq horaspi",
     "fuente": "prueba", "bloque": "C"},
    {"id": "t-C3", "es": "Tómela con agua, no con té", "quy": "Yakuwan upyay, ama tewan upyaychu.",
     "fuente": "prueba", "bloque": "C"},
    {"id": "t-C5", "es": "Son siete días de tratamiento", "quy": "Qanchis punchawmi hampikuy.",
     "fuente": "prueba", "bloque": "C"},
    {"id": "t-M1", "es": "Tome paracetamol", "quy": "Paracetamolta upyay.", "fuente": "prueba", "bloque": "M"},
    {"id": "t-M17", "es": "Una cucharadita de jarabe", "quy": "Huk uchuy wisllachapi jarabeta upyay.",
     "fuente": "prueba", "bloque": "M"},
    {"id": "t-V1", "es": "Espere un momento, por favor", "quy": "Allicha, huk ratucha suyay",
     "fuente": "prueba", "bloque": "V"},
]


@pytest.fixture
def banco():
    return construir.construir(PARES)


def test_banco_tiene_cada_tipo(banco):
    tipos = {c["tipo"] for c in banco}
    assert {"limpio", "numero", "dias", "negacion", "medicamento", "unidad", "vehiculo", "pulido_agrega",
            "pulido_limpio"} <= tipos
    assert tipos & {"agrega_consejo", "agrega_diagnostico"}


def test_banco_es_determinista():
    assert construir.construir(PARES) == construir.construir(PARES)


def test_esquema_y_etiquetas(banco):
    for c in banco:
        assert {"id", "tipo", "es", "quy", "mutacion", "esperado", "fuente"} <= c.keys()
        assert c["esperado"] == ("pasar" if c["tipo"] in ("limpio", "pulido_limpio") else "bloquear")
    assert len({c["id"] for c in banco}) == len(banco)


def test_limpio_es_el_original_y_las_mutaciones_lo_cambian(banco):
    originales = {p["id"]: p["quy"] for p in PARES}
    for c in banco:
        if c["fuente"] != "prueba" or c["tipo"].startswith("pulido"):
            continue
        base = originales[c["id"].rsplit("-", 1)[0]]
        assert (c["quy"] == base) == (c["tipo"] == "limpio")


def test_frase_de_cortesia_no_recibe_mutacion_de_numero(banco):
    assert not [c for c in banco if c["id"].startswith("t-V1") and c["tipo"] in ("numero", "dias")]


def test_las_mutaciones_mecanicas_las_atrapa_b4(banco):
    for c in banco:
        if c["tipo"] in ("numero", "dias", "negacion", "medicamento", "unidad", "vehiculo"):
            assert not terminos_fijos(c["es"], c["quy"]).ok, c
        if c["tipo"] == "limpio":
            assert terminos_fijos(c["es"], c["quy"]).ok, c


def test_caso_vivo_del_24_oct_esta_fijo_en_el_banco(banco):
    vivos = {c["id"]: c for c in banco if c["fuente"] == "vivo-2026-10-24"}
    assert vivos["vivo-20261024-limpio"]["quy"] == "Unuwan upyaykuy, manan téwanchu"
    assert vivos["vivo-20261024-limpio"]["esperado"] == "pasar"
    assert vivos["vivo-20261024-vehiculo"]["esperado"] == "bloquear"
    assert "unuwan" not in vivos["vivo-20261024-vehiculo"]["quy"].lower()


def test_mutacion_de_vehiculo_no_mueve_los_demas_casos(banco):
    # The vehicle mutation uses a hash, not the shared rng: removing it leaves every other case equal.
    sin_vehiculo = [c for c in banco if c["tipo"] != "vehiculo" and c["fuente"] != "vivo-2026-10-24"]
    original = construir.mutar_vehiculo
    try:
        construir.mutar_vehiculo = lambda *a: []
        assert [c for c in construir.construir(PARES) if c["fuente"] != "vivo-2026-10-24"] == sin_vehiculo
    finally:
        construir.mutar_vehiculo = original


def test_cargar_pares_solo_usa_filas_con_transcripcion(tmp_path):
    m = tmp_path / "manifest.jsonl"
    filas = [{"persona": "p1", "bloque": "C", "numero": 1, "castellano": "Tome", "transcripcion": "Upyay", "audio": "x"},
             {"persona": "p1", "bloque": "C", "numero": 2, "castellano": "Venga", "transcripcion": "  "}]
    m.write_text("\n".join(json.dumps(f) for f in filas), encoding="utf-8")
    f = tmp_path / "frases.json"
    f.write_text(json.dumps({"verificadas": [{"castellano": "Escuche", "chanka": "Uyariy"}]}), encoding="utf-8")
    pares = construir.cargar_pares(m, f)
    assert [(p["es"], p["quy"]) for p in pares] == [("Tome", "Upyay"), ("Escuche", "Uyariy")]
    assert all("audio" not in p for p in pares)


# --- runner ---------------------------------------------------------------------------------------

@pytest.fixture
def ruta_banco(tmp_path, banco):
    ruta = tmp_path / "banco.jsonl"
    ruta.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in banco), encoding="utf-8")
    return ruta


def leer_resultado(carpeta):
    (archivo,) = list(carpeta.glob("*.json"))
    return json.loads(archivo.read_text(encoding="utf-8"))


def test_sin_barreras_no_atrapa_nada(ruta_banco, tmp_path):
    salida = tmp_path / "res"
    assert correr.main(["--modo", "sin_barreras", "--banco", str(ruta_banco), "--salida", str(salida)]) == 0
    r = leer_resultado(salida)["resumen"]
    assert r["atrapados"] == 0 and r["falsos_bloqueos"] == 0 and r["errores_sembrados"] > 0


def test_chaski_simulado_atrapa_las_capas_de_codigo(ruta_banco, tmp_path):
    salida = tmp_path / "res"
    assert correr.main(["--modo", "chaski", "--simulado", "--banco", str(ruta_banco), "--salida", str(salida),
                        "--modelo-critico", "claude-sonnet-x"]) == 0
    r = leer_resultado(salida)
    assert r["simulado"] is True and r["modelo_critico"] == "claude-sonnet-x"
    por_tipo = r["resumen"]["por_tipo"]
    for tipo in ("numero", "dias", "negacion", "medicamento", "unidad"):
        assert por_tipo[tipo]["tasa_bloqueo"] == 1.0, tipo
    assert por_tipo["limpio"]["bloqueados"] == 0 and por_tipo["pulido_limpio"]["bloqueados"] == 0
    assert r["resumen"]["tasa_atrapados"] > 0


def test_juez_simulado_dice_que_todo_es_fiel(ruta_banco, tmp_path):
    salida = tmp_path / "res"
    assert correr.main(["--modo", "juez_claude", "--simulado", "--banco", str(ruta_banco), "--salida", str(salida)]) == 0
    assert leer_resultado(salida)["resumen"]["atrapados"] == 0


def test_limite_es_por_tipo(ruta_banco):
    casos = correr.cargar_banco(ruta_banco, 1)
    tipos = [c["tipo"] for c in casos]
    assert len(tipos) == len(set(tipos))


def test_modo_pago_sin_llave_sale_con_mensaje(ruta_banco, tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert correr.main(["--modo", "chaski", "--banco", str(ruta_banco), "--salida", str(tmp_path / "r")]) == 1
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err
    assert not (tmp_path / "r").exists()


def test_modo_pago_sin_si_no_gasta(ruta_banco, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "prueba-no-real")

    class Prohibido:
        def __init__(self, *a, **k):
            raise AssertionError("no debía crear un cliente real")

    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", Prohibido)
    assert correr.main(["--modo", "juez_claude", "--limite", "2", "--banco", str(ruta_banco),
                        "--salida", str(tmp_path / "r")]) == 2
    out = capsys.readouterr().out
    assert "llamadas" in out and "--si" in out


def test_estimacion_de_llamadas(banco):
    n_trad = sum(1 for c in banco if c.get("pulido") is None)
    n_pul = len(banco) - n_trad
    assert correr.llamadas_estimadas(banco, "chaski") == 4 * n_trad + 3 * n_pul
    assert correr.llamadas_estimadas(banco, "juez_claude") == len(banco)
    assert correr.llamadas_estimadas(banco, "sin_barreras") == 0


def test_error_del_cliente_es_bloqueo():
    class Roto:
        messages = None

    s = correr.evaluar({"es": "x", "quy": "y", "tipo": "limpio"}, "juez_claude", Roto(), "m", "m")
    assert s["bloqueado"] is True and "no pude verificar" in s["motivo"]
