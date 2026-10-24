# Plan de implementación — pipeline, modelos y API

> **Para quien ejecute esto:** las tareas van en orden y cada una termina en algo probado y commiteado.
> Pasos con `- [ ]` para ir marcando.

**Meta:** convertir 3.1M denuncias en un ranking de corredores viales de Lima por riesgo de violencia armada
en las próximas 4 semanas, servido por una API que cumple el contrato, con el ablation que dice qué
información aporta.

**Arquitectura:** DuckDB limpia y agrega el CSV a eventos con coordenada válida. `osmnx` da el grafo vial y
se agrupa en corredores. Los eventos se enganchan al corredor más cercano. De ahí sale un panel
corredor × semana con features de lags propios, vecinos del grafo y violencia previa. Los modelos se
entrenan hasta 2022 y se prueban en 2023. FastAPI sirve el resultado por coordenada.

**Stack:** Python 3.14 con `uv` (el Python del sistema está bloqueado por PEP 668), DuckDB, osmnx,
geopandas, scikit-learn, shap, FastAPI, pytest.

**Spec:** `02-diseno-tecnico.md` (diseño), `07-ablation.md` (experimentos), `09-validaciones.md` (qué
aguanta la data). El frontend va en plan aparte: `08-frontend-d3.md`.

## Restricciones globales

- Todo se ejecuta con `uv run --with <deps> python ...`. **Nunca `pip install` al Python del sistema.**
- Filtro de coordenada obligatorio en cualquier lectura del CSV: `estado_coord = 'CON COORDENADA'` **y**
  excluir los puntos exactos con más de 200 hechos (653 en Lima). Sin esto el mapa muestra comisarías.
- Partición: entrenamiento hasta **2022-12-31**, prueba **2023-01-01 a 2023-12-31**. La prueba se toca una
  sola vez.
- Se descartan las **últimas 4 semanas** de cualquier ventana (truncamiento por retraso de registro).
- Etiqueta `y_escala`: 1 si hay ≥1 hecho de `LESIONES POR PAF`, `MUERTE POR ARMA DE FUEGO`,
  `LESIONES POR PAF SEGUIDAS DE MUERTE` o `DAÑOS` en el corredor en las **4 semanas siguientes**.
- Umbral de enganche al corredor: **80 m**. Lo que quede fuera se descarta y se cuenta.
- Métricas: AUC-PR, PAI@k y recall@k con k medido en **longitud de vía**, no en número de corredores.
- Ningún archivo de salida contiene identificadores de persona o de negocio.
- Commits en inglés, Conventional Commits, con el trailer `Co-Authored-By`.

## Foco de revisión

Lo que la spec implica, ningún test obvio cubre, y rompería el resultado:

1. **Fuga temporal en el borde.** `y_escala` mira 4 semanas adelante: las últimas 4 semanas del
   entrenamiento ven etiquetas construidas con datos de la ventana de prueba. Hay que cortarlas. Test en
   la tarea 4.
2. **Corredores sin ningún evento.** Si el panel solo incluye corredores que tuvieron hechos, el PAI
   compara contra un universo falso y sale inflado. El panel debe tener todos los corredores. Test en la
   tarea 4.
3. **Semanas sin eventos.** Reindexar el producto completo corredor × semana; si solo se usan las semanas
   observadas, los lags saltan huecos y mienten. Test en la tarea 4.
4. **Volcaderos locales.** El umbral de 200 captura los grandes, pero una comisaría chica puede acumular
   150 hechos y sobrevivir el filtro. Test en la tarea 1: ningún corredor puede concentrar más del 2% de
   los eventos de su distrito.
5. **PAI por longitud.** Calcular k como "los 100 corredores top" da un número distinto a "el 5% de la
   longitud de vía" y solo el segundo es comparable con la literatura. Test en la tarea 6.

---

### Tarea 1: Eventos limpios

**Archivos:**
- Crear: `pipeline/limpieza.py`
- Crear: `pipeline/tests/test_limpieza.py`
- Salida: `data/eventos_limpios.parquet`

**Interfaces:**
- Produce: `cargar_eventos(csv_path: str, con=None) -> duckdb.DuckDBPyRelation` y
  `escribir_parquet(csv_path: str, salida: str) -> dict` con el resumen de conteos.

- [ ] **Paso 1: test que falla**

```python
# pipeline/tests/test_limpieza.py
import duckdb, pathlib
from pipeline.limpieza import cargar_eventos

CSV = "data/muestra_test.csv"

def test_excluye_puntos_de_volcado(tmp_path):
    csv = tmp_path / "m.csv"
    filas = ["estado_coord,lat_hecho,long_hecho,fecha_hora_hecho_iso_utc,año_hecho,distrito_hecho,tipo_hecho,subtipo_hecho"]
    # 250 hechos en el mismo punto = volcadero
    filas += [f"CON COORDENADA,-12.0,-77.0,2022-03-0{i%9+1}T10:00:00+00:00,2022,SAN JUAN DE LURIGANCHO,PATRIMONIO (DELITO),HURTO" for i in range(250)]
    # 3 hechos en puntos distintos = se quedan
    filas += [f"CON COORDENADA,-12.00{i},-77.01{i},2022-03-01T10:00:00+00:00,2022,SAN JUAN DE LURIGANCHO,LIBERTAD (DELITO),EXTORSION" for i in range(1,4)]
    # 1 hecho sin coordenada valida = se va
    filas += ["SIN COORDENADA,-12.5,-77.5,2022-03-01T10:00:00+00:00,2022,COMAS,PATRIMONIO (DELITO),HURTO"]
    csv.write_text("\n".join(filas), encoding="utf-8")
    rel = cargar_eventos(str(csv))
    df = rel.df()
    assert len(df) == 3
    assert df["es_ext"].sum() == 3
```

- [ ] **Paso 2: correr y verificar que falla**

Correr: `uv run --with duckdb --with pytz --with pytest --with pandas python -m pytest pipeline/tests/test_limpieza.py -v`
Esperado: FAIL, `ModuleNotFoundError: No module named 'pipeline.limpieza'`.

- [ ] **Paso 3: implementación mínima**

```python
# pipeline/limpieza.py
import duckdb

VIOLENCIA = ("LESIONES POR PAF", "MUERTE POR ARMA DE FUEGO",
             "LESIONES POR PAF SEGUIDAS DE MUERTE", "DAÑOS")
UMBRAL_VOLCADERO = 200

def cargar_eventos(csv_path: str, con=None):
    con = con or duckdb.connect()
    con.execute(f"""
        create or replace view raw as
        select * from read_csv_auto('{csv_path}', ignore_errors=true, sample_size=300000)
    """)
    con.execute(f"""
        create or replace table volcadero as
        select round(lat_hecho,6) la, round(long_hecho,6) lo
        from raw where lat_hecho is not null
        group by 1,2 having count(*) > {UMBRAL_VOLCADERO}
    """)
    viol = ",".join(f"'{v}'" for v in VIOLENCIA)
    con.execute(f"""
        create or replace table eventos as
        select
            cast(r.fecha_hora_hecho_iso_utc as timestamp) ts,
            r.lat_hecho lat, r.long_hecho lon,
            r.distrito_hecho distrito, r.subtipo_hecho subtipo, r."año_hecho" anio,
            case when r.subtipo_hecho ilike '%EXTORSION%' or r.tipo_hecho ilike '%EXTORSION%'
                 then 1 else 0 end es_ext,
            case when r.subtipo_hecho in ({viol}) then 1 else 0 end es_viol
        from raw r
        left join volcadero v
          on round(r.lat_hecho,6)=v.la and round(r.long_hecho,6)=v.lo
        where v.la is null
          and r.estado_coord = 'CON COORDENADA'
          and r.lat_hecho is not null
    """)
    return con.table("eventos")

def escribir_parquet(csv_path: str, salida: str) -> dict:
    con = duckdb.connect()
    cargar_eventos(csv_path, con)
    con.execute(f"copy eventos to '{salida}' (format parquet)")
    n, ext, viol = con.execute("select count(*), sum(es_ext), sum(es_viol) from eventos").fetchone()
    return {"eventos": n, "extorsion": ext, "violencia": viol}
```

- [ ] **Paso 4: correr el test**

Esperado: PASS.

- [ ] **Paso 5: test del foco de revisión 4 (volcaderos locales)**

```python
def test_ningun_punto_concentra_mas_del_2pct(tmp_path):
    from pipeline.limpieza import cargar_eventos
    import collections
    rel = cargar_eventos("delitos_lima_metropolitana_completo_2018-25.csv")
    df = rel.df()
    por_distrito = df.groupby("distrito").size()
    conteo = df.groupby(["distrito", df.lat.round(5), df.lon.round(5)]).size()
    for (dist, _, _), n in conteo.items():
        assert n <= 0.02 * por_distrito[dist], f"punto sospechoso en {dist}: {n} hechos"
```

Si este test falla, **bajar `UMBRAL_VOLCADERO`** hasta que pase y anotar el valor usado en
`09-validaciones.md`.

- [ ] **Paso 6: generar el parquet y commitear**

```bash
uv run --with duckdb --with pytz --with pandas --with pyarrow python -c \
 "from pipeline.limpieza import escribir_parquet; print(escribir_parquet('delitos_lima_metropolitana_completo_2018-25.csv','data/eventos_limpios.parquet'))"
git add pipeline/limpieza.py pipeline/tests/test_limpieza.py
git commit -m "feat: clean event loader with dump-point filter"
```

---

### Tarea 2: Corredores desde el grafo

**Archivos:**
- Crear: `pipeline/corredores.py`
- Crear: `pipeline/tests/test_corredores.py`
- Entrada: `data/lima_drive.graphml` (lo produce `validacion/04_grafo_lima.py`)
- Salida: `data/corredores.parquet` con `corredor_id, nombre, geometria_wkt, largo_m, jerarquia, grado`

**Interfaces:**
- Produce: `construir_corredores(G) -> geopandas.GeoDataFrame` y `vecinos(corredores) -> dict[str, list[str]]`.

- [ ] **Paso 1: test que falla**

```python
# pipeline/tests/test_corredores.py
import networkx as nx
from pipeline.corredores import construir_corredores

def grafo_juguete():
    G = nx.MultiDiGraph(crs="epsg:4326")
    # cuatro nodos en linea sobre la misma avenida
    for i, (x, y) in enumerate([(-77.00,-12.00), (-77.001,-12.00), (-77.002,-12.00), (-77.003,-12.00)]):
        G.add_node(i, x=x, y=y)
    for i in range(3):
        G.add_edge(i, i+1, name="AV TEST", highway="primary", length=110.0)
    return G

def test_agrupa_aristas_de_la_misma_via():
    gdf = construir_corredores(grafo_juguete())
    assert len(gdf) == 1
    assert gdf.iloc[0]["nombre"] == "AV TEST"
    assert 320 < gdf.iloc[0]["largo_m"] < 340
```

- [ ] **Paso 2: correr y verificar que falla**

Correr: `uv run --with osmnx --with geopandas --with pytest python -m pytest pipeline/tests/test_corredores.py -v`

- [ ] **Paso 3: implementación**

```python
# pipeline/corredores.py
import networkx as nx, geopandas as gpd
from shapely.geometry import LineString
from shapely.ops import linemerge

LARGO_MAX = 800.0   # metros; partir corredores mas largos

def _geom(G, u, v, d):
    if "geometry" in d:
        return d["geometry"]
    return LineString([(G.nodes[u]["x"], G.nodes[u]["y"]), (G.nodes[v]["x"], G.nodes[v]["y"])])

def construir_corredores(G) -> gpd.GeoDataFrame:
    grupos = {}
    for u, v, d in G.edges(data=True):
        nombre = d.get("name")
        if isinstance(nombre, list):
            nombre = nombre[0]
        clave = nombre or f"sin_nombre_{min(u,v)}_{max(u,v)}"
        g = grupos.setdefault(clave, {"geoms": [], "largo": 0.0,
                                      "jerarquia": d.get("highway"), "nodos": set()})
        g["geoms"].append(_geom(G, u, v, d))
        g["largo"] += float(d.get("length", 0.0))
        g["nodos"].update((u, v))
    filas = []
    for i, (nombre, g) in enumerate(sorted(grupos.items())):
        merged = linemerge(g["geoms"])
        partes = list(merged.geoms) if merged.geom_type == "MultiLineString" else [merged]
        for j, parte in enumerate(partes):
            jer = g["jerarquia"]
            if isinstance(jer, list):
                jer = jer[0]
            filas.append({
                "corredor_id": f"c{i:06d}_{j}",
                "nombre": nombre,
                "largo_m": g["largo"] / len(partes),
                "jerarquia": jer,
                "grado": len(g["nodos"]),
                "geometry": parte,
            })
    return gpd.GeoDataFrame(filas, geometry="geometry", crs="epsg:4326")

def vecinos(gdf: gpd.GeoDataFrame, tolerancia_m: float = 25.0) -> dict:
    """Corredores que se tocan: comparten un extremo dentro de la tolerancia."""
    m = gdf.to_crs(32718)   # UTM 18S, metros
    sindex = m.sindex
    out = {}
    for idx, fila in m.iterrows():
        buf = fila.geometry.buffer(tolerancia_m)
        cand = list(sindex.intersection(buf.bounds))
        out[gdf.loc[idx, "corredor_id"]] = [
            gdf.loc[c, "corredor_id"] for c in cand
            if c != idx and m.loc[c].geometry.intersects(buf)
        ]
    return out
```

- [ ] **Paso 4: correr el test** → PASS.

- [ ] **Paso 5: criterio de aprobación sobre datos reales**

```bash
uv run --with osmnx --with geopandas --with pyarrow python -c "
import osmnx as ox; from pipeline.corredores import construir_corredores
G = ox.load_graphml('data/lima_drive.graphml')
gdf = construir_corredores(G); gdf.to_parquet('data/corredores.parquet')
print(len(gdf), 'corredores | mediana largo', gdf.largo_m.median())"
```

Aprueba si la mediana de `largo_m` cae entre 200 y 900. Si no, ajustar `LARGO_MAX` y volver a correr.

- [ ] **Paso 6: commit**

```bash
git add pipeline/corredores.py pipeline/tests/test_corredores.py
git commit -m "feat: build street corridors and adjacency from the OSM graph"
```

---

### Tarea 3: Enganche de eventos al corredor

**Archivos:**
- Crear: `pipeline/enganche.py`
- Crear: `pipeline/tests/test_enganche.py`
- Salida: `data/eventos_con_corredor.parquet`

**Interfaces:**
- Consume: `data/eventos_limpios.parquet`, `data/corredores.parquet`.
- Produce: `enganchar(eventos_df, corredores_gdf, umbral_m=80.0) -> (DataFrame, dict)`. El dict trae
  `{"enganchados": int, "descartados": int, "pct": float}`.

- [ ] **Paso 1: test que falla**

```python
# pipeline/tests/test_enganche.py
import pandas as pd, geopandas as gpd
from shapely.geometry import LineString
from pipeline.enganche import enganchar

def test_engancha_lo_cercano_y_descarta_lo_lejano():
    corr = gpd.GeoDataFrame(
        [{"corredor_id": "c1", "geometry": LineString([(-77.000,-12.000), (-77.000,-12.004)])}],
        geometry="geometry", crs="epsg:4326")
    ev = pd.DataFrame([
        {"lat": -12.002, "lon": -77.0002},   # ~22 m: engancha
        {"lat": -12.002, "lon": -77.0100},   # ~1 km: se descarta
    ])
    out, resumen = enganchar(ev, corr, umbral_m=80.0)
    assert resumen["enganchados"] == 1
    assert resumen["descartados"] == 1
    assert out.iloc[0]["corredor_id"] == "c1"
```

- [ ] **Paso 2: correr y verificar que falla.**

- [ ] **Paso 3: implementación**

```python
# pipeline/enganche.py
import geopandas as gpd, pandas as pd

def enganchar(eventos: pd.DataFrame, corredores: gpd.GeoDataFrame, umbral_m: float = 80.0):
    pts = gpd.GeoDataFrame(
        eventos.copy(),
        geometry=gpd.points_from_xy(eventos["lon"], eventos["lat"]),
        crs="epsg:4326").to_crs(32718)
    corr = corredores.to_crs(32718)
    j = gpd.sjoin_nearest(pts, corr[["corredor_id", "geometry"]],
                          how="left", max_distance=umbral_m, distance_col="dist_m")
    enganchados = j[j["corredor_id"].notna()].copy()
    resumen = {"enganchados": len(enganchados),
               "descartados": len(j) - len(enganchados),
               "pct": round(100 * len(enganchados) / max(len(j), 1), 1)}
    return enganchados.drop(columns=["geometry", "index_right"], errors="ignore"), resumen
```

- [ ] **Paso 4: correr el test** → PASS.

- [ ] **Paso 5: criterio de aprobación sobre datos reales**

Correr sobre `data/eventos_limpios.parquet`. **Aprueba si `pct` ≥ 80.** Si queda por debajo, subir el
umbral a 120 m, anotarlo en `09-validaciones.md` y decirlo en el README del proyecto.

- [ ] **Paso 6: commit**

```bash
git add pipeline/enganche.py pipeline/tests/test_enganche.py
git commit -m "feat: snap events to the nearest corridor within 80 m"
```

---

### Tarea 4: Panel corredor × semana y etiqueta

**Archivos:**
- Crear: `pipeline/panel.py`
- Crear: `pipeline/tests/test_panel.py`
- Salida: `data/panel.parquet`

**Interfaces:**
- Produce: `construir_panel(eventos_con_corredor, corredores, inicio, fin) -> DataFrame` con columnas
  `corredor_id, semana, ext, viol, y_escala`.
- Produce: `recortar_borde(panel, fin_entrenamiento) -> DataFrame`.

- [ ] **Paso 1: tests que fallan (los tres del foco de revisión)**

```python
# pipeline/tests/test_panel.py
import pandas as pd, geopandas as gpd
from shapely.geometry import LineString
from pipeline.panel import construir_panel, recortar_borde

def corredores_juguete(ids=("c1","c2")):
    return gpd.GeoDataFrame(
        [{"corredor_id": i, "geometry": LineString([(-77,-12), (-77,-12.001)])} for i in ids],
        geometry="geometry", crs="epsg:4326")

def test_incluye_corredores_sin_eventos():
    ev = pd.DataFrame([{"corredor_id": "c1", "ts": pd.Timestamp("2022-01-03"), "es_ext": 1, "es_viol": 0}])
    p = construir_panel(ev, corredores_juguete(), "2022-01-01", "2022-02-01")
    assert set(p["corredor_id"]) == {"c1", "c2"}

def test_incluye_semanas_sin_eventos():
    ev = pd.DataFrame([{"corredor_id": "c1", "ts": pd.Timestamp("2022-01-03"), "es_ext": 1, "es_viol": 0}])
    p = construir_panel(ev, corredores_juguete(("c1",)), "2022-01-01", "2022-02-01")
    assert p["semana"].nunique() >= 4
    assert (p["ext"] == 0).sum() >= 3

def test_etiqueta_mira_cuatro_semanas_adelante():
    ev = pd.DataFrame([
        {"corredor_id": "c1", "ts": pd.Timestamp("2022-01-03"), "es_ext": 1, "es_viol": 0},
        {"corredor_id": "c1", "ts": pd.Timestamp("2022-01-24"), "es_ext": 0, "es_viol": 1},
    ])
    p = construir_panel(ev, corredores_juguete(("c1",)), "2022-01-01", "2022-03-01")
    fila = p[p["semana"] == pd.Timestamp("2022-01-03")].iloc[0]
    assert fila["y_escala"] == 1

def test_recorta_las_ultimas_cuatro_semanas_del_entrenamiento():
    p = pd.DataFrame({"corredor_id": ["c1"]*10,
                      "semana": pd.date_range("2022-11-07", periods=10, freq="7D"),
                      "ext": 0, "viol": 0, "y_escala": 0})
    r = recortar_borde(p, "2022-12-31")
    assert r["semana"].max() <= pd.Timestamp("2022-12-03")
```

- [ ] **Paso 2: correr y verificar que fallan.**

- [ ] **Paso 3: implementación**

```python
# pipeline/panel.py
import pandas as pd

VENTANA_ETIQUETA = 4   # semanas hacia adelante
BORDE = 4              # semanas que se cortan al final de cada ventana

def construir_panel(eventos: pd.DataFrame, corredores, inicio: str, fin: str) -> pd.DataFrame:
    ev = eventos.copy()
    ev["semana"] = pd.to_datetime(ev["ts"]).dt.to_period("W-MON").dt.start_time
    agg = (ev.groupby(["corredor_id", "semana"])[["es_ext", "es_viol"]]
             .sum().rename(columns={"es_ext": "ext", "es_viol": "viol"}).reset_index())
    semanas = pd.date_range(pd.Timestamp(inicio).to_period("W-MON").start_time,
                            pd.Timestamp(fin), freq="7D")
    ids = list(corredores["corredor_id"])
    idx = pd.MultiIndex.from_product([ids, semanas], names=["corredor_id", "semana"])
    panel = (agg.set_index(["corredor_id", "semana"])
                .reindex(idx, fill_value=0).reset_index())
    panel = panel.sort_values(["corredor_id", "semana"])
    futuro = (panel.groupby("corredor_id")["viol"]
                   .rolling(VENTANA_ETIQUETA, min_periods=1).sum()
                   .shift(-VENTANA_ETIQUETA).reset_index(level=0, drop=True))
    panel["y_escala"] = (futuro.fillna(0) > 0).astype(int)
    return panel

def recortar_borde(panel: pd.DataFrame, fin_ventana: str) -> pd.DataFrame:
    corte = pd.Timestamp(fin_ventana) - pd.Timedelta(weeks=BORDE)
    return panel[panel["semana"] <= corte].copy()
```

- [ ] **Paso 4: correr los cuatro tests** → PASS.

- [ ] **Paso 5: generar el panel real y commitear**

```bash
git add pipeline/panel.py pipeline/tests/test_panel.py
git commit -m "feat: corridor-week panel with four-week escalation label"
```

---

### Tarea 5: Features

**Archivos:**
- Crear: `pipeline/features.py`
- Crear: `pipeline/tests/test_features.py`

**Interfaces:**
- Consume: `data/panel.parquet`, el dict de `corredores.vecinos`.
- Produce: `agregar_features(panel, vecinos) -> DataFrame` con los bloques A, B, C, D y G de
  `07-ablation.md`, y `BLOQUES: dict[str, list[str]]` que mapea cada bloque a sus columnas.

- [ ] **Paso 1: test que falla**

```python
# pipeline/tests/test_features.py
import pandas as pd
from pipeline.features import agregar_features, BLOQUES

def test_lag_propio_no_usa_la_semana_actual():
    panel = pd.DataFrame({
        "corredor_id": ["c1"]*5,
        "semana": pd.date_range("2022-01-03", periods=5, freq="7D"),
        "ext": [0, 5, 0, 0, 0], "viol": 0, "y_escala": 0,
    })
    f = agregar_features(panel, {"c1": []})
    # en la semana del evento, el lag de 1 semana todavia es 0
    assert f.loc[f["semana"] == pd.Timestamp("2022-01-10"), "ext_lag_1"].iloc[0] == 0
    # una semana despues, ya vale 5
    assert f.loc[f["semana"] == pd.Timestamp("2022-01-17"), "ext_lag_1"].iloc[0] == 5

def test_difusion_toma_del_vecino():
    panel = pd.DataFrame({
        "corredor_id": ["c1"]*3 + ["c2"]*3,
        "semana": list(pd.date_range("2022-01-03", periods=3, freq="7D"))*2,
        "ext": [0,0,0, 7,0,0], "viol": 0, "y_escala": 0,
    })
    f = agregar_features(panel, {"c1": ["c2"], "c2": ["c1"]})
    fila = f[(f.corredor_id=="c1") & (f.semana==pd.Timestamp("2022-01-10"))].iloc[0]
    assert fila["ext_vec1_lag_1"] == 7

def test_bloques_cubren_todas_las_columnas_nuevas():
    panel = pd.DataFrame({"corredor_id": ["c1"]*3,
                          "semana": pd.date_range("2022-01-03", periods=3, freq="7D"),
                          "ext": 0, "viol": 0, "y_escala": 0})
    f = agregar_features(panel, {"c1": []})
    nuevas = set(f.columns) - set(panel.columns)
    cubiertas = {c for cols in BLOQUES.values() for c in cols}
    assert nuevas == cubiertas
```

- [ ] **Paso 2: correr y verificar que fallan.**

- [ ] **Paso 3: implementación**

```python
# pipeline/features.py
import pandas as pd

LAGS = [1, 2, 4, 8, 12]
BLOQUES = {
    "A": [f"ext_lag_{l}" for l in LAGS],
    "B": [f"ext_vec1_lag_{l}" for l in (1, 2, 4)],
    "C": [f"viol_lag_{l}" for l in (4, 12)],
    "D": ["largo_m", "grado"],
    "G": ["semana_del_anio", "tendencia"],
}

def agregar_features(panel: pd.DataFrame, vecinos: dict) -> pd.DataFrame:
    df = panel.sort_values(["corredor_id", "semana"]).copy()
    for l in LAGS:
        df[f"ext_lag_{l}"] = df.groupby("corredor_id")["ext"].shift(l).fillna(0)
    for l in (4, 12):
        df[f"viol_lag_{l}"] = (df.groupby("corredor_id")["viol"]
                                 .shift(1).rolling(l, min_periods=1).sum()
                                 .reset_index(level=0, drop=True).fillna(0))
    ancho = df.pivot_table(index="semana", columns="corredor_id", values="ext",
                           aggfunc="sum", fill_value=0)
    for l in (1, 2, 4):
        desplazado = ancho.shift(l).fillna(0)
        suma_vecinos = pd.DataFrame(
            {cid: desplazado[[v for v in vs if v in desplazado.columns]].sum(axis=1)
                  if vs else 0.0
             for cid, vs in vecinos.items()},
            index=desplazado.index)
        largo = suma_vecinos.stack().rename(f"ext_vec1_lag_{l}").reset_index()
        largo.columns = ["semana", "corredor_id", f"ext_vec1_lag_{l}"]
        df = df.merge(largo, on=["semana", "corredor_id"], how="left")
        df[f"ext_vec1_lag_{l}"] = df[f"ext_vec1_lag_{l}"].fillna(0)
    df["semana_del_anio"] = df["semana"].dt.isocalendar().week.astype(int)
    df["tendencia"] = (df["semana"] - df["semana"].min()).dt.days // 7
    for col in ("largo_m", "grado"):
        if col not in df.columns:
            df[col] = 0.0
    return df
```

- [ ] **Paso 4: correr los tests** → PASS.

- [ ] **Paso 5: commit**

```bash
git add pipeline/features.py pipeline/tests/test_features.py
git commit -m "feat: lag, graph-diffusion and structure features"
```

---

### Tarea 6: Métricas y baselines

**Archivos:**
- Crear: `pipeline/metricas.py`
- Crear: `pipeline/tests/test_metricas.py`

**Interfaces:**
- Produce: `pai(df, score_col, k_frac, largo_col="largo_m", y_col="y_escala") -> float`,
  `recall_en_k(...) -> float`, `baseline_extorsion(features) -> Series`,
  `baseline_violencia(features) -> Series`.

- [ ] **Paso 1: test que falla (foco de revisión 5)**

```python
# pipeline/tests/test_metricas.py
import pandas as pd
from pipeline.metricas import pai

def test_pai_usa_longitud_no_conteo():
    # c1 es corto y concentra el hecho; c2 es larguisimo y no tiene nada
    df = pd.DataFrame({
        "corredor_id": ["c1", "c2"],
        "largo_m": [100.0, 9900.0],
        "y_escala": [1, 0],
        "score": [0.9, 0.1],
    })
    # marcando el 1% de la longitud entra solo c1, que tiene el 100% de los hechos
    assert pai(df, "score", k_frac=0.01) == 100.0
```

- [ ] **Paso 2: correr y verificar que falla.**

- [ ] **Paso 3: implementación**

```python
# pipeline/metricas.py
import pandas as pd

def pai(df: pd.DataFrame, score_col: str, k_frac: float,
        largo_col: str = "largo_m", y_col: str = "y_escala") -> float:
    d = df.sort_values(score_col, ascending=False).copy()
    largo_total = d[largo_col].sum()
    d["acum"] = d[largo_col].cumsum()
    marcados = d[d["acum"] <= k_frac * largo_total]
    if marcados.empty:
        marcados = d.head(1)
    n, N = marcados[y_col].sum(), d[y_col].sum()
    a, A = marcados[largo_col].sum(), largo_total
    if N == 0 or a == 0:
        return 0.0
    return float((n / N) / (a / A))

def recall_en_k(df, score_col, k_frac, largo_col="largo_m", y_col="y_escala") -> float:
    d = df.sort_values(score_col, ascending=False).copy()
    d["acum"] = d[largo_col].cumsum()
    marcados = d[d["acum"] <= k_frac * d[largo_col].sum()]
    N = d[y_col].sum()
    return float(marcados[y_col].sum() / N) if N else 0.0

def baseline_extorsion(features: pd.DataFrame) -> pd.Series:
    return features[[f"ext_lag_{l}" for l in (1, 2, 4)]].sum(axis=1)

def baseline_violencia(features: pd.DataFrame) -> pd.Series:
    return features["viol_lag_4"]
```

- [ ] **Paso 4: correr el test** → PASS.

- [ ] **Paso 5: commit**

```bash
git add pipeline/metricas.py pipeline/tests/test_metricas.py
git commit -m "feat: PAI and recall-at-k measured by road length"
```

---

### Tarea 7: Modelo y ablation

**Archivos:**
- Crear: `pipeline/modelo.py`
- Crear: `pipeline/ablation.py`
- Crear: `pipeline/tests/test_modelo.py`
- Salida: `reports/ablation.csv`, `reports/ablation.md`, `reports/shap_top_features.json`

**Interfaces:**
- Produce: `particionar(features) -> (entrenamiento, prueba)` con el corte de 2022-12-31 / 2023 y el
  recorte de borde ya aplicado; `entrenar(entrenamiento, columnas) -> modelo`;
  `evaluar(modelo, prueba, columnas) -> dict` con `auc_pr`, `pai_5`, `recall_5`.

- [ ] **Paso 1: test que falla (foco de revisión 1)**

```python
# pipeline/tests/test_modelo.py
import pandas as pd
from pipeline.modelo import particionar

def test_la_particion_no_se_solapa_ni_filtra_el_futuro():
    f = pd.DataFrame({"corredor_id": ["c1"]*80,
                      "semana": pd.date_range("2022-01-03", periods=80, freq="7D"),
                      "y_escala": 0})
    tr, te = particionar(f)
    assert tr["semana"].max() <= pd.Timestamp("2022-12-03")   # 4 semanas de borde
    assert te["semana"].min() >= pd.Timestamp("2023-01-01")
    assert te["semana"].max() <= pd.Timestamp("2023-12-03")
    assert set(tr["semana"]).isdisjoint(set(te["semana"]))
```

- [ ] **Paso 2: correr y verificar que falla.**

- [ ] **Paso 3: implementación**

```python
# pipeline/modelo.py
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
from pipeline.panel import recortar_borde
from pipeline.metricas import pai, recall_en_k

FIN_ENTRENAMIENTO = "2022-12-31"
INICIO_PRUEBA, FIN_PRUEBA = "2023-01-01", "2023-12-31"

def particionar(features: pd.DataFrame):
    tr = features[features["semana"] <= pd.Timestamp(FIN_ENTRENAMIENTO)]
    tr = recortar_borde(tr, FIN_ENTRENAMIENTO)
    te = features[(features["semana"] >= pd.Timestamp(INICIO_PRUEBA)) &
                  (features["semana"] <= pd.Timestamp(FIN_PRUEBA))]
    te = recortar_borde(te, FIN_PRUEBA)
    return tr.copy(), te.copy()

def entrenar(tr: pd.DataFrame, columnas: list):
    m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, random_state=0)
    m.fit(tr[columnas], tr["y_escala"])
    return m

def evaluar(modelo, te: pd.DataFrame, columnas: list) -> dict:
    d = te.copy()
    d["score"] = modelo.predict_proba(d[columnas])[:, 1]
    ultima = d[d["semana"] == d["semana"].max()]
    return {
        "auc_pr": float(average_precision_score(d["y_escala"], d["score"])),
        "pai_5": pai(ultima, "score", 0.05),
        "recall_5": recall_en_k(ultima, "score", 0.05),
        "prevalencia": float(d["y_escala"].mean()),
    }
```

- [ ] **Paso 4: correr el test** → PASS.

- [ ] **Paso 5: el runner del ablation**

```python
# pipeline/ablation.py
import itertools, json, pandas as pd
from pipeline.features import BLOQUES
from pipeline.modelo import particionar, entrenar, evaluar
from pipeline.metricas import baseline_extorsion, baseline_violencia, pai, recall_en_k

ACUMULATIVO = [["A"], ["A","B"], ["A","B","C"], ["A","B","C","D"], ["A","B","C","D","G"]]

def correr(features: pd.DataFrame, salida_csv="reports/ablation.csv") -> pd.DataFrame:
    tr, te = particionar(features)
    filas = []
    ultima = te[te["semana"] == te["semana"].max()].copy()
    for nombre, score in (("baseline_extorsion", baseline_extorsion(ultima)),
                          ("baseline_violencia", baseline_violencia(ultima))):
        u = ultima.assign(score=score)
        filas.append({"modelo": nombre, "bloques": "-",
                      "auc_pr": None, "pai_5": pai(u, "score", 0.05),
                      "recall_5": recall_en_k(u, "score", 0.05)})
    for combo in ACUMULATIVO:
        cols = [c for b in combo for c in BLOQUES[b]]
        m = entrenar(tr, cols)
        r = evaluar(m, te, cols)
        filas.append({"modelo": "hgb", "bloques": "+".join(combo), **r})
    df = pd.DataFrame(filas)
    df.to_csv(salida_csv, index=False)
    return df
```

- [ ] **Paso 6: correr el ablation de verdad y commitear**

```bash
uv run --with scikit-learn --with pandas --with pyarrow python -c \
 "import pandas as pd; from pipeline.ablation import correr; print(correr(pd.read_parquet('data/features.parquet')))"
git add pipeline/modelo.py pipeline/ablation.py pipeline/tests/test_modelo.py reports/
git commit -m "feat: temporal split, gradient boosting and ablation runner"
```

**Criterio:** si ninguna combinación le gana a `baseline_violencia` en PAI@5%, **se corta el escalamiento**
y el producto pasa a corredores análogos, como dice `03-plan-36h.md`.

---

### Tarea 8: API con el contrato

**Archivos:**
- Crear: `api/main.py`
- Crear: `api/tests/test_api.py`
- Crear: `contrato/fixtures/corredores_muestra.json`

**Interfaces:**
- `GET /corredor?lat=&lon=` devuelve el JSON de `02-diseno-tecnico.md` §6.
- `POST /reporte-anonimo` recibe `{lat, lon, modalidad, texto}` y devuelve `{corredor_id, aceptado}`.

- [ ] **Paso 1: tests que fallan**

```python
# api/tests/test_api.py
from fastapi.testclient import TestClient
from api.main import app

cliente = TestClient(app)

def test_corredor_devuelve_el_contrato():
    r = cliente.get("/corredor", params={"lat": -12.0, "lon": -77.0})
    assert r.status_code == 200
    d = r.json()
    for campo in ("corredor_id", "nombre", "senal", "p_escalamiento_4sem",
                  "tasa_100neg", "frente", "analogos", "top_features", "cobertura"):
        assert campo in d
    assert d["cobertura"]["aviso_subregistro"] is True
    assert "cobro_activo" not in d

def test_reporte_anonimo_no_devuelve_la_coordenada():
    r = cliente.post("/reporte-anonimo",
                     json={"lat": -12.0, "lon": -77.0, "modalidad": "EXTORSION", "texto": "me cobran"})
    assert r.status_code == 200
    d = r.json()
    assert set(d.keys()) == {"corredor_id", "aceptado"}
```

- [ ] **Paso 2: correr y verificar que fallan.**

Correr: `uv run --with fastapi --with httpx --with pytest python -m pytest api/tests -v`

- [ ] **Paso 3: implementación**

```python
# api/main.py
import json, math, pathlib
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Corredores de extorsion")
RUTA = pathlib.Path("contrato/fixtures/corredores_muestra.json")
CORREDORES = json.loads(RUTA.read_text(encoding="utf-8"))

class Reporte(BaseModel):
    lat: float
    lon: float
    modalidad: str
    texto: str | None = None

def _mas_cercano(lat: float, lon: float) -> dict:
    def d2(c):
        return (c["centroide"]["lat"] - lat) ** 2 + (c["centroide"]["lon"] - lon) ** 2
    return min(CORREDORES, key=d2)

@app.get("/corredor")
def corredor(lat: float, lon: float):
    c = dict(_mas_cercano(lat, lon))
    c["cobertura"] = {"denuncias_ok": True, "aviso_subregistro": True}
    c.pop("centroide", None)
    return c

@app.post("/reporte-anonimo")
def reporte_anonimo(r: Reporte):
    c = _mas_cercano(r.lat, r.lon)
    # se guarda solo el corredor: ni coordenada, ni texto crudo, ni telefono
    return {"corredor_id": c["corredor_id"], "aceptado": True}
```

El fixture `contrato/fixtures/corredores_muestra.json` es una lista de objetos con el contrato de
`02-diseno-tecnico.md` §6 más un campo `centroide` que la API usa para buscar y borra antes de responder.

- [ ] **Paso 4: correr los tests** → PASS.

- [ ] **Paso 5: commit**

```bash
git add api/ contrato/
git commit -m "feat: corridor API serving the agreed JSON contract"
```

---

## Qué queda fuera de este plan

- El frontend en D3. Va en `08-frontend-d3.md` y lo ejecuta la sesión de Freddy contra
  `contrato/fixtures/`.
- La capa de Claude (texto para el bodeguero, clasificación del reporte de voz, denuncia anónima).
- GNN con `torch_geometric` y Hawkes continuo. Entran solo si las ocho tareas están cerradas.
- El denominador de negocios desde SUNAT. La tarea 5 deja `tasa_100neg` en el contrato; el pipeline lo
  llena con el conteo de POIs de OSM mientras no exista el padrón.
