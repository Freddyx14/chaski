import pandas as pd

from pipeline.metricas import pai, recall_en_k


def test_pai_usa_longitud_no_conteo():
    """Foco de revision 5: marcar el 1% de la longitud no es lo mismo que marcar
    el 1% de los corredores."""
    df = pd.DataFrame({
        "corredor_id": ["c1", "c2"],
        "largo_m": [100.0, 9900.0],
        "y_escala": [1, 0],
        "score": [0.9, 0.1],
    })
    assert pai(df, "score", k_frac=0.01) == 100.0


def test_pai_vale_uno_cuando_el_score_no_informa():
    df = pd.DataFrame({
        "corredor_id": [f"c{i}" for i in range(10)],
        "largo_m": [100.0] * 10,
        "y_escala": [1, 0] * 5,
        "score": [0.5] * 10,
    })
    assert 0.0 < pai(df, "score", k_frac=0.5) <= 2.0


def test_recall_en_k():
    df = pd.DataFrame({
        "corredor_id": ["a", "b", "c", "d"],
        "largo_m": [100.0] * 4,
        "y_escala": [1, 1, 0, 0],
        "score": [0.9, 0.8, 0.2, 0.1],
    })
    assert recall_en_k(df, "score", k_frac=0.5) == 1.0


def test_sin_positivos_no_revienta():
    df = pd.DataFrame({"corredor_id": ["a"], "largo_m": [100.0],
                       "y_escala": [0], "score": [0.5]})
    assert pai(df, "score", 0.5) == 0.0
    assert recall_en_k(df, "score", 0.5) == 0.0
