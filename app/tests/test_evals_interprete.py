"""The eval harness in evals/interprete runs offline (--simulado) and never calls the API by accident."""
import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2] / "evals" / "interprete"
_spec = importlib.util.spec_from_file_location("correr_interprete", RAIZ / "correr.py")
correr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(correr)


def test_escenarios_cubren_todo():
    casos = correr.cargar()
    assert len(casos) >= 40 and len({c["id"] for c in casos}) == len(casos)
    acciones = {a for c in casos for a in correr._lista(c["esperado"]["accion"])}
    assert acciones == {"traducir", "repreguntar", "responder", "no_entendi", "usar_frase_banco"}
    categorias = {c["categoria"] for c in casos}
    assert {"emergencia", "medicamento", "orden", "meta", "basura", "media_frase", "asr", "inyeccion",
            "ambiguedad_repetida", "banco"} <= categorias
    assert any(c["turno"]["idioma"] == "quy" for c in casos)


def test_simulado_da_100_y_escribe_el_informe(tmp_path, capsys):
    assert correr.main(["--simulado", "--salida", str(tmp_path)]) == 0
    [archivo] = list(tmp_path.glob("*-simulado-*.json"))
    informe = json.loads(archivo.read_text())
    assert informe["accion_acc"] == 1.0 and informe["completo_acc"] == 1.0
    assert informe["violaciones_c7"] == [] and informe["errores"] == []
    assert informe["modelos"]["critico"] == correr.MODELO_CRITICO and informe["critico"]["revisadas"] > 0
    assert set(informe["latencia_ms"]) >= {"p50", "p95"}


def test_sin_llave_sale_sin_correr(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert correr.main(["--modelo", "claude-opus-5", "--salida", str(tmp_path)]) == 2
    assert list(tmp_path.iterdir()) == []


def test_con_llave_pero_sin_si_no_llama(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert correr.main(["--limite", "3", "--salida", str(tmp_path)]) == 1
    assert "3 llamadas" in capsys.readouterr().out and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("fuente,dicho,nuevos", [
    ("tome 10 pastillas", "Tome 10 pastillas.", []),
    ("tome la pastilla cada", "Tome la pastilla cada ocho horas.", ["ocho"]),
    ("dele el antibiótico", "Tome amoxicilina.", ["amoxicilina"]),
    ("tome paracetamol", "Tome paracetamol después de comer.", ["despues de comer"]),
    ("pusaq horapi", "pusaq horapi upiyay", []),
    ("umaymi nanawan", "Dijo que le duele la cabeza.", []),
])
def test_datos_nuevos(fuente, dicho, nuevos):
    assert correr.datos_nuevos(fuente, dicho) == nuevos


def test_evaluar_marca_must_not_y_omisiones():
    caso = {"turno": {"texto": "tome paracetamol cada ocho horas", "idioma": "spa", "rol": "personal"},
            "esperado": {"accion": "traducir", "must_include": ["ocho"], "must_not": ["ibuprofeno"]}}
    from chaski.interprete import Decision
    d = Decision(accion="traducir", para="paciente", idioma_salida="quy", texto_pulido="Tome ibuprofeno.", motivo="m",
                 frase_banco_id=None, dato_faltante=None)
    ev = correr.evaluar(caso, d)
    assert ev["accion_ok"] and "must_not: ibuprofeno" in ev["violaciones"] and "dato nuevo: ibuprofeno" in ev["violaciones"]
    assert ev["omisiones"] == ["ocho"]
