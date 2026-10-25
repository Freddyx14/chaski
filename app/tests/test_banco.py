"""Phrase bank: retrieval sanity, tag filter, leakage rule, threshold behavior, cache.

Most tests use a deterministic fake encoder (hashed bag of tokens) so they run offline in milliseconds.
One test uses the real fastembed model and is skipped when it isn't downloaded yet.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from chaski import banco as mod
from chaski.banco import Banco, normalizar

RAIZ = Path(__file__).resolve().parents[2]
FRASES = RAIZ / "ricardo-artifacts" / "datos" / "frases" / "frases.json"
SEMIOLOGIA = RAIZ / "ricardo-artifacts" / "datos" / "frases" / "semiologia_cmp.jsonl"


class FakeCodificador:
    """Hashed bag of normalized tokens. Same words → same vector; counts calls so the cache can be tested."""

    def __init__(self, dim: int = 64):
        self.dim = dim
        self.llamadas = 0

    def __call__(self, textos: list[str]) -> np.ndarray:
        self.llamadas += 1
        m = np.zeros((len(textos), self.dim), dtype=np.float32)
        for i, t in enumerate(textos):
            for tok in normalizar(t).split():
                m[i, int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim] += 1.0
        return m


ITEMS = [
    {"id": "a", "es": "¿Dónde le duele?", "quy": "", "audio": None, "tags": ["emergencia", "dolor", "falta_quechua"]},
    {"id": "b", "es": "¿Le duele la cabeza?", "quy": "¿Umayki nanan?", "audio": None, "tags": ["emergencia", "dolor"]},
    {"id": "c", "es": "Abra la boca", "quy": "Kichay simiykita", "audio": None, "tags": ["examen_fisico"]},
    {"id": "d", "es": "¿Tiene fiebre o escalofríos?", "quy": "¿Rupaychu japisunki?", "audio": "https://x/a.webm",
     "tags": ["emergencia", "fiebre"]},
]


@pytest.fixture
def banco() -> Banco:
    return Banco(ITEMS, codificador=FakeCodificador())


# ---------- text ----------

def test_normalizar_quita_tildes_mayusculas_y_signos():
    assert normalizar("¿Está EMBARAZADA, señora?") == "esta embarazada senora"
    assert normalizar("  ¡Ñaña!  ") == "nana"


# ---------- retrieval ----------

def test_frase_exacta_sale_primera(banco):
    top = banco.buscar("¿Le duele la cabeza?", k=3)
    assert top[0][0]["id"] == "b"
    assert top[0][1] > top[1][1]


def test_puntajes_ordenados_y_k_respetado(banco):
    top = banco.buscar("le duele", k=2)
    assert len(top) == 2
    assert top[0][1] >= top[1][1]


def test_consulta_vacia_no_devuelve_nada(banco):
    assert banco.buscar("   ") == []
    assert banco.candidatos("") == []


def test_modos_lexico_y_embedding_tambien_funcionan(banco):
    for modo in ("lexico", "embedding", "hibrido"):
        assert banco.buscar("abra la boca", k=1, modo=modo)[0][0]["id"] == "c"
    with pytest.raises(ValueError):
        banco.puntajes("x", modo="otro")


def test_hibrido_es_la_combinacion_documentada(banco):
    q = "¿le duele la cabeza?"
    esperado = mod.PESO_EMBEDDING * banco.puntajes(q, "embedding") + mod.PESO_LEXICO * banco.puntajes(q, "lexico")
    assert np.allclose(banco.puntajes(q, "hibrido"), esperado)


def test_lexico_esta_en_cero_uno():
    s = mod.Lexico([it["es"] for it in ITEMS]).puntajes("duele duele cabeza cabeza")
    assert s.min() >= 0 and s.max() <= 1


# ---------- tag filter ----------

def test_filtro_por_tag(banco):
    ids = {it["id"] for it, _ in banco.buscar("abra la boca", k=10, tag="emergencia")}
    assert ids == {"a", "b", "d"}


def test_por_tag_conserva_orden_y_puede_exigir_quechua(banco):
    assert [it["id"] for it in banco.por_tag("emergencia")] == ["a", "b", "d"]
    assert [it["id"] for it in banco.por_tag("emergencia", solo_con_quechua=True)] == ["b", "d"]
    assert banco.por_tag("no-existe") == []


def test_candidatos_solo_id_y_es_y_solo_lo_que_se_puede_decir(banco):
    c = banco.candidatos("¿dónde le duele?", k=20)
    assert all(set(x) == {"id", "es"} for x in c)
    assert "a" not in {x["id"] for x in c}  # no Quechua yet → can't be said
    assert "a" in {x["id"] for x in banco.candidatos("¿dónde le duele?", solo_con_quechua=False)}


def test_para_app_tiene_exactamente_las_claves_de_ios():
    assert set(mod.para_app({**ITEMS[3], "fuente": "x", "revisado": False, "split": "banco"})) == {
        "id", "es", "quy", "audio", "tags"}


# ---------- threshold ----------

def test_mejor_abstiene_bajo_el_umbral_y_propone_sobre_el(banco):
    assert banco.mejor("¿Le duele la cabeza?")[0]["id"] == "b"
    assert banco.mejor("firme el consentimiento informado por favor") is None
    assert banco.mejor("¿Le duele la cabeza?", umbral=1.01) is None


def test_umbral_es_una_constante_razonable():
    assert 0.3 < mod.UMBRAL_MISMA_INTENCION < 0.9


# ---------- cache ----------

def test_cache_se_reusa_y_se_invalida_si_cambia_el_banco(tmp_path):
    cache = tmp_path / "emb.npz"
    f1 = FakeCodificador()
    Banco(ITEMS, codificador=f1, cache=cache).vectores()
    assert cache.exists() and f1.llamadas == 1

    f2 = FakeCodificador()
    Banco(ITEMS, codificador=f2, cache=cache).vectores()
    assert f2.llamadas == 0  # same texts → read from disk

    f3 = FakeCodificador()
    otros = [*ITEMS, {"id": "e", "es": "¿Tiene sed?", "quy": "x", "audio": None, "tags": []}]
    v = Banco(otros, codificador=f3, cache=cache).vectores()
    assert f3.llamadas == 1 and v.shape[0] == 5


# ---------- the real banco.json ----------

@pytest.fixture(scope="module")
def items_reales() -> list[dict]:
    return mod.cargar_items()


def test_regla_de_fuga_ninguna_verificada_en_el_banco(items_reales):
    verificadas = {normalizar(v["castellano"]) for v in json.loads(FRASES.read_text(encoding="utf-8"))["verificadas"]}
    choques = [it["es"] for it in items_reales if normalizar(it["es"]) in verificadas]
    assert choques == []
    assert {it["split"] for it in items_reales} == {"banco"}


def test_esquema_e_ids_unicos(items_reales):
    for it in items_reales:
        base = {"id", "es", "quy", "audio", "tags", "fuente", "revisado", "split"}
        assert base <= set(it) <= base | {"quy_original", "nota"}  # the nurse's review adds these two
        assert it["es"].strip() and it["tags"]
        assert it["audio"] is None or it["audio"].startswith("https://")
    assert len({it["id"] for it in items_reales}) == len(items_reales)
    assert len({normalizar(it["es"]) for it in items_reales}) == len(items_reales)


def test_emergencia_nunca_inventa_quechua(items_reales):
    manual = {}
    for l in SEMIOLOGIA.read_text(encoding="utf-8").splitlines():
        fila = json.loads(l)
        manual.setdefault(normalizar(fila["castellano"].replace("\x00", "fi")), fila["chanka_propuesto"].strip())
    emergencia = [it for it in items_reales if "emergencia" in it["tags"]]
    assert len(emergencia) >= 15
    for it in emergencia:
        if "falta_quechua" in it["tags"]:
            assert it["quy"] == "" and it["revisado"] is False and it["audio"] is None
        elif it["fuente"].startswith("enfermera"):
            assert it.get("quy_original"), it["id"]  # written by the nurse, her original kept next to the normalized one
        else:
            assert it["quy"] == manual[normalizar(it["es"])], it["id"]  # Quechua comes from the manual, verbatim


def test_solo_lo_que_la_enfermera_aprobo_viene_revisado(items_reales):
    for it in items_reales:
        if it["fuente"].startswith("cmp-"):
            assert it["revisado"] is ("revisada por la enfermera" in it["fuente"]), it["id"]


def test_lo_que_falta_confirmar_no_se_dice(items_reales):
    for it in items_reales:
        if "por_confirmar" in it["tags"]:
            assert it["revisado"] is False, it["id"]


def _construir():
    ruta = RAIZ / "evals" / "banco" / "construir.py"
    spec = importlib.util.spec_from_file_location("construir_banco", ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_construccion_determinista():
    c = _construir()
    a, _ = c.construir(c.MANIFEST_POR_DEFECTO)
    b, _ = c.construir(c.MANIFEST_POR_DEFECTO)
    assert a == b
    if c.MANIFEST_POR_DEFECTO.exists():
        assert a == mod.cargar_items()  # banco.json on disk is what the script produces


# ---------- real model (skipped offline) ----------

def _modelo_disponible() -> bool:
    return mod.CARPETA_MODELOS.exists() and any(mod.CARPETA_MODELOS.rglob("*.onnx"))


@pytest.mark.skipif(not _modelo_disponible(), reason="fastembed model not downloaded")
def test_modelo_real_entiende_parafrasis_coloquial():
    b = Banco.desde_archivo()
    assert "emg-dolor-donde" in [it["id"] for it, _ in b.buscar("a ver, ¿dónde es el dolor, mamita?", k=5)]
    assert b.buscar("¿tiene fiebre?", k=1)[0][0]["id"] == "emg-fiebre"
    assert b.mejor("¿tiene seguro integral SIS?") is None
