"""Validacion 1 (ruta alterna): corredores de Lima desde el PBF de Geofabrik.

Overpass devolvio 502 de forma sostenida, asi que las vias salen del extracto de
Peru. Criterio de aprobacion: la mediana de largo_m cae entre 200 y 900 m.
Uso: uv run --with geopandas --with pyogrio python validacion/05_corredores_desde_pbf.py
"""
import time

import geopandas as gpd

from pipeline.corredores import construir_corredores_desde_lineas, vecinos

W, S, E, N = -77.20, -12.35, -76.70, -11.70
VIAS = {"motorway", "trunk", "primary", "secondary", "tertiary",
        "unclassified", "residential", "living_street",
        "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link"}

t0 = time.time()
lineas = gpd.read_file("data/peru-latest.osm.pbf", layer="lines",
                       columns=["osm_id", "name", "highway"], bbox=(W, S, E, N),
                       engine="pyogrio")
print(f"lineas en el bbox: {len(lineas)} ({time.time() - t0:.0f}s)", flush=True)
lineas = lineas[lineas["highway"].isin(VIAS)].copy()
print(f"vias vehiculares: {len(lineas)}", flush=True)

corredores = construir_corredores_desde_lineas(lineas)
corredores.to_parquet("data/corredores.parquet")
print(f"corredores: {len(corredores)}")
print(f"largo_m  mediana {corredores.largo_m.median():.0f}  "
      f"media {corredores.largo_m.mean():.0f}  max {corredores.largo_m.max():.0f}")
print(f"con nombre: {(~corredores.nombre.str.startswith('sin_nombre')).mean() * 100:.1f}%")
print(f"TOTAL {time.time() - t0:.0f}s")
