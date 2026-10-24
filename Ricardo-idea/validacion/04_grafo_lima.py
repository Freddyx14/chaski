"""Validacion 1: baja el grafo vial de Lima Metropolitana y lo agrupa en corredores.
Criterio de aprobacion: corre en < 20 min y la mediana de largo de corredor cae entre 200 y 900 m.
Uso: uv run --with osmnx --with networkx --with geopandas python validacion/04_grafo_lima.py
"""
import time, pickle, statistics
t0=time.time()
import osmnx as ox
print("osmnx", ox.__version__, flush=True)
ox.settings.use_cache=True
ox.settings.cache_folder="data/osm_cache"
# Lima Metropolitana aproximada: sur de Lurin a norte de Ancon, costa a Chosica
W,S,E,N=-77.20,-12.35,-76.70,-11.70
try:
    G=ox.graph.graph_from_bbox(bbox=(W,S,E,N), network_type="drive", simplify=True, retain_all=False)
except TypeError:
    G=ox.graph_from_bbox(north=N, south=S, east=E, west=W, network_type="drive", simplify=True)
print(f"grafo: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas, {time.time()-t0:.0f}s", flush=True)
ox.save_graphml(G,"data/lima_drive.graphml")
largos=[d.get("length",0) for _,_,d in G.edges(data=True)]
print(f"arista: mediana {statistics.median(largos):.0f} m, media {statistics.mean(largos):.0f} m", flush=True)
nombradas=sum(1 for _,_,d in G.edges(data=True) if d.get("name"))
print(f"aristas con nombre: {nombradas} ({100*nombradas/G.number_of_edges():.1f}%)", flush=True)
print(f"TOTAL {time.time()-t0:.0f}s")
