"""Engancha cada hecho al corredor mas cercano.

El umbral existe porque la coordenada de la PNP sale de geocodificar la direccion
escrita en la comisaria: trae error de decenas de metros. Lo que cae demasiado
lejos de cualquier via se descarta y se cuenta, y ese conteo va al README.
"""
import geopandas as gpd
import pandas as pd

UTM_LIMA = 32718
UMBRAL_M = 80.0


def enganchar(eventos: pd.DataFrame, corredores: gpd.GeoDataFrame,
              umbral_m: float = UMBRAL_M) -> tuple[pd.DataFrame, dict]:
    puntos = gpd.GeoDataFrame(
        eventos.copy(),
        geometry=gpd.points_from_xy(eventos["lon"], eventos["lat"]),
        crs="epsg:4326").to_crs(UTM_LIMA)
    vias = corredores[["corredor_id", "geometry"]].to_crs(UTM_LIMA)

    unido = gpd.sjoin_nearest(puntos, vias, how="left",
                              max_distance=umbral_m, distance_col="dist_m")
    # sjoin_nearest puede duplicar un punto si empata con dos corredores
    unido = unido[~unido.index.duplicated(keep="first")]
    enganchados = unido[unido["corredor_id"].notna()].copy()
    resumen = {
        "total": len(puntos),
        "enganchados": len(enganchados),
        "descartados": len(puntos) - len(enganchados),
        "pct": round(100 * len(enganchados) / max(len(puntos), 1), 1),
    }
    enganchados = enganchados.drop(columns=["geometry", "index_right"], errors="ignore")
    return pd.DataFrame(enganchados), resumen
