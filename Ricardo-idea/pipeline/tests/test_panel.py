import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from pipeline.panel import construir_panel, recortar_borde


def corredores(ids=("c1", "c2")):
    return gpd.GeoDataFrame(
        [{"corredor_id": i, "largo_m": 300.0,
          "geometry": LineString([(-77, -12), (-77, -12.001)])} for i in ids],
        geometry="geometry", crs="epsg:4326")


def un_evento(corredor="c1", fecha="2022-01-03", ext=1, viol=0):
    return {"corredor_id": corredor, "ts": pd.Timestamp(fecha),
            "es_ext": ext, "es_viol": viol}


def test_incluye_corredores_sin_eventos():
    panel = construir_panel(pd.DataFrame([un_evento()]), corredores(),
                            "2022-01-01", "2022-02-01")
    assert set(panel["corredor_id"]) == {"c1", "c2"}


def test_incluye_semanas_sin_eventos():
    panel = construir_panel(pd.DataFrame([un_evento()]), corredores(("c1",)),
                            "2022-01-01", "2022-02-01")
    assert panel["semana"].nunique() >= 4
    assert (panel["ext"] == 0).sum() >= 3


def test_etiqueta_mira_cuatro_semanas_adelante():
    eventos = pd.DataFrame([
        un_evento(fecha="2022-01-03"),
        un_evento(fecha="2022-01-24", ext=0, viol=1),
    ])
    panel = construir_panel(eventos, corredores(("c1",)), "2022-01-01", "2022-03-01")
    fila = panel[panel["semana"] == pd.Timestamp("2022-01-03")].iloc[0]
    assert fila["y_escala"] == 1


def test_la_etiqueta_no_mira_la_semana_actual():
    eventos = pd.DataFrame([un_evento(fecha="2022-01-03", ext=0, viol=1)])
    panel = construir_panel(eventos, corredores(("c1",)), "2022-01-01", "2022-03-01")
    fila = panel[panel["semana"] == pd.Timestamp("2022-01-03")].iloc[0]
    assert fila["viol"] == 1
    assert fila["y_escala"] == 0


def test_recorta_las_ultimas_cuatro_semanas():
    panel = pd.DataFrame({
        "corredor_id": ["c1"] * 10,
        "semana": pd.date_range("2022-11-07", periods=10, freq="7D"),
        "ext": 0, "viol": 0, "y_escala": 0,
    })
    recortado = recortar_borde(panel, "2022-12-31")
    assert recortado["semana"].max() <= pd.Timestamp("2022-12-03")
