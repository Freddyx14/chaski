import pandas as pd

from pipeline.modelo import particionar


def panel_largo(semanas=110, inicio="2022-01-03"):
    return pd.DataFrame({
        "corredor_id": ["c1"] * semanas,
        "semana": pd.date_range(inicio, periods=semanas, freq="7D"),
        "y_escala": 0,
    })


def test_la_particion_no_se_solapa_ni_filtra_el_futuro():
    entrenamiento, prueba = particionar(panel_largo())
    assert entrenamiento["semana"].max() <= pd.Timestamp("2022-12-03")
    assert prueba["semana"].min() >= pd.Timestamp("2023-01-01")
    assert prueba["semana"].max() <= pd.Timestamp("2023-12-03")
    assert set(entrenamiento["semana"]).isdisjoint(set(prueba["semana"]))


def test_entre_entrenamiento_y_prueba_hay_un_hueco_de_cuatro_semanas():
    """La etiqueta mira 4 semanas adelante: sin hueco, las ultimas semanas de
    entrenamiento llevan informacion de la ventana de prueba."""
    entrenamiento, prueba = particionar(panel_largo())
    hueco = (prueba["semana"].min() - entrenamiento["semana"].max()).days
    assert hueco >= 28
