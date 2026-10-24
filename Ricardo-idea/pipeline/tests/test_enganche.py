import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from pipeline.enganche import enganchar


def corredor_vertical():
    return gpd.GeoDataFrame(
        [{"corredor_id": "c1",
          "geometry": LineString([(-77.000, -12.000), (-77.000, -12.004)])}],
        geometry="geometry", crs="epsg:4326")


def test_engancha_lo_cercano_y_descarta_lo_lejano():
    eventos = pd.DataFrame([
        {"lat": -12.002, "lon": -77.0002},   # ~22 m del corredor
        {"lat": -12.002, "lon": -77.0100},   # ~1 km del corredor
    ])
    enganchados, resumen = enganchar(eventos, corredor_vertical(), umbral_m=80.0)
    assert resumen["enganchados"] == 1
    assert resumen["descartados"] == 1
    assert enganchados.iloc[0]["corredor_id"] == "c1"


def test_conserva_las_columnas_del_evento():
    eventos = pd.DataFrame([
        {"lat": -12.002, "lon": -77.0002, "es_ext": 1, "es_viol": 0,
         "ts": pd.Timestamp("2022-01-03")},
    ])
    enganchados, _ = enganchar(eventos, corredor_vertical(), umbral_m=80.0)
    assert {"es_ext", "es_viol", "ts", "corredor_id", "dist_m"} <= set(enganchados.columns)


def test_el_umbral_manda():
    eventos = pd.DataFrame([{"lat": -12.002, "lon": -77.0005}])   # ~55 m
    assert enganchar(eventos, corredor_vertical(), umbral_m=80.0)[1]["enganchados"] == 1
    assert enganchar(eventos, corredor_vertical(), umbral_m=30.0)[1]["enganchados"] == 0
