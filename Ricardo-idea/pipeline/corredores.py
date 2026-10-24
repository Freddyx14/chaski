"""Agrupa las aristas del grafo vial en corredores.

Un corredor es un tramo de via de 300 a 800 metros: la unidad que absorbe el
error de geocodificacion de la PNP (decenas de metros) sin borrar el fenomeno,
como hace el distrito. Ver propuesta/02-diseno-tecnico.md seccion 1.
"""
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge, substring

UTM_LIMA = 32718          # EPSG:32718, UTM 18S: metros, la zona de Lima
LARGO_MAX = 800.0         # metros; un corredor mas largo se parte
TOLERANCIA_VECINO = 25.0  # metros; dos corredores que se tocan son vecinos


def _primero(valor):
    """OSM trae listas en name y highway, y el PBF trae NaN, que es truthy."""
    if isinstance(valor, list):
        valor = valor[0] if valor else None
    if valor is None or valor != valor or valor == "":   # valor != valor detecta NaN
        return None
    return valor


def _geometria(G, u, v, datos):
    if "geometry" in datos:
        return datos["geometry"]
    return LineString([(G.nodes[u]["x"], G.nodes[u]["y"]),
                       (G.nodes[v]["x"], G.nodes[v]["y"])])


def _partir(linea, largo_max=LARGO_MAX):
    """Parte una linea proyectada en metros en tramos de a lo mas largo_max."""
    largo = linea.length
    if largo <= largo_max:
        return [linea]
    n = int(largo // largo_max) + 1
    paso = largo / n
    return [substring(linea, i * paso, (i + 1) * paso) for i in range(n)]


def _desde_grupos(grupos: dict) -> gpd.GeoDataFrame:
    filas = []
    for i, (nombre, grupo) in enumerate(sorted(grupos.items())):
        unida = linemerge(grupo["geoms"])
        partes = list(unida.geoms) if isinstance(unida, MultiLineString) else [unida]
        filas.append({"nombre": nombre, "jerarquia": grupo["jerarquia"],
                      "grado": len(grupo["nodos"]), "indice": i, "partes": partes})

    # proyectar una sola vez para medir y partir en metros
    crudo = gpd.GeoDataFrame(
        [{"indice": f["indice"], "nombre": f["nombre"], "jerarquia": f["jerarquia"],
          "grado": f["grado"], "geometry": parte}
         for f in filas for parte in f["partes"]],
        geometry="geometry", crs="epsg:4326").to_crs(UTM_LIMA)

    salida = []
    for _, fila in crudo.iterrows():
        for j, tramo in enumerate(_partir(fila.geometry)):
            salida.append({
                "corredor_id": f"c{fila['indice']:06d}_{len(salida):06d}",
                "nombre": fila["nombre"],
                "jerarquia": fila["jerarquia"],
                "grado": int(fila["grado"]),
                "largo_m": float(tramo.length),
                "geometry": tramo,
            })
    return gpd.GeoDataFrame(salida, geometry="geometry", crs=UTM_LIMA).to_crs("epsg:4326")


def construir_corredores(G) -> gpd.GeoDataFrame:
    """Corredores a partir de un grafo de networkx u osmnx."""
    grupos = {}
    for u, v, datos in G.edges(data=True):
        nombre = _primero(datos.get("name"))
        clave = nombre or f"sin_nombre_{min(u, v)}_{max(u, v)}"
        grupo = grupos.setdefault(clave, {"geoms": [], "jerarquia": None, "nodos": set()})
        grupo["geoms"].append(_geometria(G, u, v, datos))
        grupo["jerarquia"] = grupo["jerarquia"] or _primero(datos.get("highway"))
        grupo["nodos"].update((u, v))
    return _desde_grupos(grupos)


def construir_corredores_desde_lineas(lineas: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Corredores a partir de las lineas del PBF de OSM (capa 'lines').

    Se usa cuando Overpass no responde. El grado queda en 0 porque el PBF no
    trae la topologia de nodos; los vecinos se calculan igual por geometria.
    """
    grupos = {}
    for fila in lineas.itertuples():
        nombre = _primero(getattr(fila, "name", None))
        # Las vias sin nombre van todas al mismo grupo: linemerge las une en
        # cadenas contiguas. Una clave por via dejaba corredores de 150 m.
        clave = nombre or "sin_nombre"
        grupo = grupos.setdefault(clave, {"geoms": [], "jerarquia": None, "nodos": set()})
        grupo["geoms"].append(fila.geometry)
        grupo["jerarquia"] = grupo["jerarquia"] or _primero(getattr(fila, "highway", None))
    return _desde_grupos(grupos)


def vecinos(gdf: gpd.GeoDataFrame, tolerancia_m: float = TOLERANCIA_VECINO) -> dict:
    """Corredores que se tocan dentro de la tolerancia, por identificador."""
    metrico = gdf.to_crs(UTM_LIMA)
    indice = metrico.sindex
    salida = {}
    for pos, fila in enumerate(metrico.itertuples()):
        buffer = fila.geometry.buffer(tolerancia_m)
        candidatos = indice.query(buffer)
        salida[gdf.iloc[pos]["corredor_id"]] = [
            gdf.iloc[c]["corredor_id"] for c in candidatos
            if c != pos and metrico.iloc[c].geometry.intersects(buffer)
        ]
    return salida
