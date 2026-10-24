import networkx as nx
import pytest

from pipeline.corredores import construir_corredores, vecinos


def grafo_juguete():
    """Cuatro nodos en linea sobre la misma avenida, mas un ramal con otro nombre."""
    G = nx.MultiDiGraph(crs="epsg:4326")
    puntos = [(-77.000, -12.000), (-77.001, -12.000), (-77.002, -12.000), (-77.003, -12.000)]
    for i, (x, y) in enumerate(puntos):
        G.add_node(i, x=x, y=y)
    for i in range(3):
        G.add_edge(i, i + 1, name="AV TEST", highway="primary", length=110.0)
    G.add_node(9, x=-77.002, y=-12.002)
    G.add_edge(2, 9, name="JR RAMAL", highway="residential", length=220.0)
    return G


def test_agrupa_aristas_de_la_misma_via():
    gdf = construir_corredores(grafo_juguete())
    av = gdf[gdf["nombre"] == "AV TEST"]
    assert len(av) == 1
    assert 320 < av.iloc[0]["largo_m"] < 340


def test_separa_vias_distintas():
    gdf = construir_corredores(grafo_juguete())
    assert set(gdf["nombre"]) == {"AV TEST", "JR RAMAL"}


def test_identificadores_unicos():
    gdf = construir_corredores(grafo_juguete())
    assert gdf["corredor_id"].is_unique


def test_vecinos_detecta_el_ramal_que_toca_la_avenida():
    gdf = construir_corredores(grafo_juguete())
    v = vecinos(gdf)
    av = gdf[gdf["nombre"] == "AV TEST"].iloc[0]["corredor_id"]
    ramal = gdf[gdf["nombre"] == "JR RAMAL"].iloc[0]["corredor_id"]
    assert ramal in v[av]
    assert av in v[ramal]


def test_corredor_muy_largo_se_parte():
    G = nx.MultiDiGraph(crs="epsg:4326")
    for i in range(21):
        G.add_node(i, x=-77.0 - i * 0.001, y=-12.0)
    for i in range(20):
        G.add_edge(i, i + 1, name="AV LARGA", highway="primary", length=110.0)
    gdf = construir_corredores(G)
    assert len(gdf) >= 2, "una via de 2.2 km debe partirse en varios corredores"
    assert gdf["largo_m"].max() <= 900


def test_construye_desde_lineas_de_osm():
    """Ruta alterna: cuando Overpass no responde, las vias salen del PBF de
    Geofabrik como GeoDataFrame de lineas en vez de grafo de networkx."""
    import geopandas as gpd
    from shapely.geometry import LineString

    from pipeline.corredores import construir_corredores_desde_lineas

    lineas = gpd.GeoDataFrame(
        [
            {"name": "AV TEST", "highway": "primary",
             "geometry": LineString([(-77.000, -12.0), (-77.001, -12.0)])},
            {"name": "AV TEST", "highway": "primary",
             "geometry": LineString([(-77.001, -12.0), (-77.002, -12.0)])},
            {"name": "JR RAMAL", "highway": "residential",
             "geometry": LineString([(-77.002, -12.0), (-77.002, -12.002)])},
        ],
        geometry="geometry", crs="epsg:4326")
    gdf = construir_corredores_desde_lineas(lineas)
    assert set(gdf["nombre"]) == {"AV TEST", "JR RAMAL"}
    av = gdf[gdf["nombre"] == "AV TEST"]
    assert len(av) == 1
    assert 200 < av.iloc[0]["largo_m"] < 240


def test_lineas_sin_nombre_no_rompen_el_agrupado():
    """El PBF trae NaN en name, y NaN es truthy: si no se normaliza, la clave del
    grupo queda en float y el ordenado revienta."""
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import LineString

    from pipeline.corredores import construir_corredores_desde_lineas

    lineas = gpd.GeoDataFrame(
        [
            {"name": np.nan, "highway": "residential",
             "geometry": LineString([(-77.000, -12.0), (-77.001, -12.0)])},
            {"name": "AV TEST", "highway": "primary",
             "geometry": LineString([(-77.001, -12.0), (-77.002, -12.0)])},
        ],
        geometry="geometry", crs="epsg:4326")
    gdf = construir_corredores_desde_lineas(lineas)
    assert len(gdf) == 2
    assert sum(n.startswith("sin_nombre") for n in gdf["nombre"]) == 1

