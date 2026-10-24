import pandas as pd

from pipeline.features import BLOQUES, agregar_features


def panel_simple(ext=(0, 5, 0, 0, 0)):
    return pd.DataFrame({
        "corredor_id": ["c1"] * len(ext),
        "semana": pd.date_range("2022-01-03", periods=len(ext), freq="7D"),
        "ext": list(ext), "viol": 0, "y_escala": 0, "largo_m": 300.0, "grado": 4,
    })


def test_lag_propio_no_usa_la_semana_actual():
    f = agregar_features(panel_simple(), {"c1": []})
    en = lambda fecha, col: f.loc[f["semana"] == pd.Timestamp(fecha), col].iloc[0]
    assert en("2022-01-10", "ext_lag_1") == 0
    assert en("2022-01-17", "ext_lag_1") == 5


def test_difusion_toma_del_vecino():
    panel = pd.DataFrame({
        "corredor_id": ["c1"] * 3 + ["c2"] * 3,
        "semana": list(pd.date_range("2022-01-03", periods=3, freq="7D")) * 2,
        "ext": [0, 0, 0, 7, 0, 0], "viol": 0, "y_escala": 0,
        "largo_m": 300.0, "grado": 4,
    })
    f = agregar_features(panel, {"c1": ["c2"], "c2": ["c1"]})
    fila = f[(f.corredor_id == "c1") & (f.semana == pd.Timestamp("2022-01-10"))].iloc[0]
    assert fila["ext_vec1_lag_1"] == 7


def test_el_vecino_no_se_cuenta_a_si_mismo():
    panel = pd.DataFrame({
        "corredor_id": ["c1"] * 3,
        "semana": pd.date_range("2022-01-03", periods=3, freq="7D"),
        "ext": [9, 0, 0], "viol": 0, "y_escala": 0, "largo_m": 300.0, "grado": 4,
    })
    f = agregar_features(panel, {"c1": []})
    assert f["ext_vec1_lag_1"].sum() == 0


def test_violencia_previa_no_incluye_la_semana_actual():
    panel = panel_simple(ext=(0, 0, 0, 0, 0))
    panel["viol"] = [0, 3, 0, 0, 0]
    f = agregar_features(panel, {"c1": []})
    en = lambda fecha, col: f.loc[f["semana"] == pd.Timestamp(fecha), col].iloc[0]
    assert en("2022-01-10", "viol_lag_4") == 0
    assert en("2022-01-17", "viol_lag_4") == 3


def test_bloques_cubren_todas_las_columnas_nuevas():
    f = agregar_features(panel_simple(), {"c1": []})
    nuevas = set(f.columns) - set(panel_simple().columns)
    cubiertas = {c for cols in BLOQUES.values() for c in cols}
    assert nuevas == cubiertas - {"largo_m", "grado"}
