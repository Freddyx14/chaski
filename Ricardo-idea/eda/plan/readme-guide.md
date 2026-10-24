# Reusable EDA Template

A function catalogue for exploratory analysis of large tabular event data. It was
built against a 1.8 GB, 3.1 million row police record file, and it is written to be
reused on any dataset of that shape: many rows, mixed types, timestamps,
geolocation, high cardinality categoricals, and an uncertain target.

Two variants are provided, and section 8 explains how to choose between them:

1. **Unsupervised variant**, when the dataset carries no label.
2. **Supervised variant**, when a defensible target exists or can be defined.

Blocks 1 to 6 are shared by both variants. Block 7 is unsupervised only. Block 8 is
supervised only. Block 9 is the orchestrator.

Everything runs on DuckDB for SQL style profiling and Polars for dataframe work,
with pandas used only at the boundary where scikit learn, LightGBM and SHAP require
it.

## 0. Setup

```python
import gc, json, time, warnings
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({"figure.dpi": 110, "figure.autolayout": True, "font.size": 9})

CONFIG = {
    "csv": "delitos_lima_metropolitana_completo_2018-25.csv",
    "salida": Path("."),
    "muestra_esquema": 200_000,
    "umbral_null_descarte": 0.30,
    "umbral_categoria": 0.05,
    "top_n_categorias": 20,
    "semilla": 42,
}
```

## Block 1. Ingestion and schema profiling

### 1.1 Open the file without loading it

DuckDB reads a CSV through a view. Nothing is materialised until a query runs, so a
1.8 GB file can be profiled in seconds inside a few hundred megabytes of RAM. This is
the first thing to do with any large file, before deciding what to load.

```python
def abrir_duckdb(csv_path, nombre="d", threads=4, memoria="6GB", muestra=200_000):
    """Create a DuckDB connection with a lazy view over the CSV.

    Returns the connection. Nothing is read into memory yet.
    """
    con = duckdb.connect()
    con.execute(f"SET threads TO {threads}; SET memory_limit='{memoria}';")
    con.execute(f"""
        CREATE OR REPLACE VIEW {nombre} AS
        SELECT * FROM read_csv('{csv_path}', header=true,
                               sample_size={muestra}, ignore_errors=true)
    """)
    return con
```

### 1.2 Profile every column in one pass

One aggregate query over the whole file gives dtype, nulls, cardinality and range for
every column. Running 58 separate queries would reread the file 58 times.

```python
def perfilar_esquema(con, tabla="d"):
    """Null count, null share, cardinality and dtype for every column, in one scan."""
    meta = con.execute(f"DESCRIBE {tabla}").fetchdf()
    cols = meta["column_name"].tolist()
    piezas = [
        f'sum(CASE WHEN "{c}" IS NULL THEN 1 ELSE 0 END) AS "n_{c}", '
        f'count(DISTINCT "{c}") AS "u_{c}"'
        for c in cols
    ]
    fila = con.execute(
        f"SELECT count(*) AS n_filas, {', '.join(piezas)} FROM {tabla}"
    ).fetchdf()
    n = int(fila["n_filas"].iloc[0])

    perfil = pd.DataFrame({
        "columna": cols,
        "tipo": meta["column_type"].tolist(),
        "n_filas": n,
        "n_nulos": [int(fila[f"n_{c}"].iloc[0]) for c in cols],
        "n_unicos": [int(fila[f"u_{c}"].iloc[0]) for c in cols],
    })
    perfil["pct_nulos"] = (100 * perfil["n_nulos"] / n).round(2)
    perfil["cardinalidad_rel"] = (perfil["n_unicos"] / n).round(6)
    perfil["constante"] = perfil["n_unicos"] <= 1
    perfil["candidata_clave"] = perfil["n_unicos"] == n
    return perfil.sort_values("pct_nulos", ascending=False).reset_index(drop=True)
```

### 1.3 Recommend an action per column, then write the data dictionary

The recommendation is mechanical and reviewable. It never drops anything by itself,
it only proposes.

```python
def recomendar_accion(perfil, umbral_null=0.30, umbral_card=0.90):
    """Propose keep, drop, flag or key for each column. Rules, not magic."""
    def regla(r):
        if r["constante"]:
            return "DESCARTAR: constante, varianza cero"
        if r["pct_nulos"] >= 100:
            return "DESCARTAR: totalmente vacia"
        if r["candidata_clave"]:
            return "CLAVE: identificador unico"
        if r["pct_nulos"] >= umbral_null * 100:
            return "CONVERTIR A FLAG: nulos por encima del umbral, no imputar"
        if r["cardinalidad_rel"] > umbral_card:
            return "DESCARTAR O HASHEAR: cardinalidad casi unica, texto libre"
        return "CONSERVAR"
    perfil = perfil.copy()
    perfil["accion"] = perfil.apply(regla, axis=1)
    return perfil


def generar_diccionario(perfil, descripciones, salida="diccionario_datos.csv"):
    """Merge the mechanical profile with hand written Spanish descriptions."""
    dic = perfil.copy()
    dic["descripcion"] = dic["columna"].map(descripciones).fillna("Sin descripcion")
    orden = ["columna", "descripcion", "tipo", "n_filas", "n_nulos",
             "pct_nulos", "n_unicos", "cardinalidad_rel", "accion"]
    dic = dic[orden]
    dic.to_csv(salida, index=False, encoding="utf-8-sig")
    return dic
```

The descripciones dictionary is the only part of this block that cannot be automated.
Write it once per dataset. It is the contract every later stage depends on.

### 1.4 Load, in both engines

Loading a column subset is the single largest lever on memory. Never load all columns
by default.

```python
def cargar_duckdb(con, columnas, tabla="d", filtro=None):
    """SQL path. Projection and filter are pushed down into the CSV scan."""
    sel = ", ".join(f'"{c}"' for c in columnas)
    where = f"WHERE {filtro}" if filtro else ""
    t0 = time.perf_counter()
    df = con.execute(f"SELECT {sel} FROM {tabla} {where}").pl()
    return df, round(time.perf_counter() - t0, 2)


def cargar_polars(csv_path, columnas, filtro=None, muestra=100_000):
    """Dataframe path. scan_csv is lazy, so select and filter run during the scan."""
    t0 = time.perf_counter()
    lf = pl.scan_csv(csv_path, infer_schema_length=muestra, ignore_errors=True)
    lf = lf.select(columnas)
    if filtro is not None:
        lf = lf.filter(filtro)
    df = lf.collect()
    return df, round(time.perf_counter() - t0, 2)
```

Use DuckDB when the question is an aggregate over the whole file and the answer is
small. Use Polars when a working slice has to stay in memory for many operations.

### 1.5 Parse timestamps

Polars refuses a naive parse when the string carries an offset. Always pass the format
explicitly and convert to the local zone once, at the boundary.

```python
def parsear_timestamps(df, columnas, tz="America/Lima",
                       formato="%Y-%m-%dT%H:%M:%S%z"):
    return df.with_columns([
        pl.col(c).str.to_datetime(format=formato, strict=False)
                 .dt.convert_time_zone(tz).alias(c)
        for c in columnas
    ])
```

## Block 2. Type reduction and memory release

Downcasting is not cosmetic. On the reference dataset a 24 column slice went from
962.3 MB to 290.6 MB, a 69.8 percent reduction, which is the difference between
fitting in memory and not. Most of that gain comes from the Categorical
conversion, not from the numeric downcast.

```python
def optimizar_memoria(df, umbral_categoria=0.05, verbose=True):
    """Downcast numerics by observed range and convert low cardinality text to
    Categorical. Returns the optimised frame and a per column report."""
    antes = df.estimated_size("mb")
    n = df.height
    exprs, reporte = [], []

    for col, dt in df.schema.items():
        nuevo = None
        if dt in (pl.Float64,):
            nuevo = pl.Float32
        elif dt in (pl.Int64, pl.Int32, pl.UInt64, pl.UInt32):
            lo, hi = df[col].min(), df[col].max()
            if lo is None:
                nuevo = pl.Int32
            elif lo >= -128 and hi <= 127:
                nuevo = pl.Int8
            elif lo >= -32768 and hi <= 32767:
                nuevo = pl.Int16
            elif lo >= -2147483648 and hi <= 2147483647:
                nuevo = pl.Int32
        elif dt == pl.Utf8:
            if df[col].n_unique() / max(n, 1) < umbral_categoria:
                nuevo = pl.Categorical
        if nuevo is not None and nuevo != dt:
            exprs.append(pl.col(col).cast(pl.Utf8).cast(nuevo)
                         if nuevo == pl.Categorical else pl.col(col).cast(nuevo))
            reporte.append({"columna": col, "de": str(dt), "a": str(nuevo)})

    out = df.with_columns(exprs) if exprs else df
    despues = out.estimated_size("mb")
    if verbose:
        print(f"Memoria antes:   {antes:8.1f} MB")
        print(f"Memoria despues: {despues:8.1f} MB")
        print(f"Reduccion:       {100 * (1 - despues / antes):8.1f} por ciento")
    return out, pd.DataFrame(reporte)


def liberar(*objetos):
    """Drop references and force a collection. Call it after every heavy stage."""
    for o in objetos:
        del o
    return gc.collect()
```

Two cautions. Float32 holds about 7 significant digits, which is enough for a latitude
at metre resolution and not enough for a currency amount that must reconcile to the
cent. Categorical in Polars is fast for grouping but a cast to Categorical on a column
whose cardinality later grows will produce a different physical encoding, so cast once
and keep the frame.

## Block 3. Descriptive statistics

```python
def resumen_numerico(df, columnas=None):
    """Quantiles, dispersion, skew and outlier ratio by the interquartile rule."""
    columnas = columnas or [c for c, t in df.schema.items() if t.is_numeric()]
    filas = []
    for c in columnas:
        s = df[c].drop_nulls()
        if s.len() == 0:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = (q3 or 0) - (q1 or 0)
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        atipicos = ((s < lo) | (s > hi)).sum()
        filas.append({
            "columna": c, "n": s.len(), "media": s.mean(), "std": s.std(),
            "min": s.min(), "p01": s.quantile(0.01), "q1": q1,
            "mediana": s.median(), "q3": q3, "p99": s.quantile(0.99),
            "max": s.max(), "asimetria": s.skew(),
            "pct_atipicos": round(100 * atipicos / s.len(), 2),
        })
    return pd.DataFrame(filas)


def resumen_categorico(df, columnas=None, top_n=5):
    """Cardinality, mode, concentration of the top category and null share."""
    columnas = columnas or [c for c, t in df.schema.items()
                            if t in (pl.Utf8, pl.Categorical, pl.Boolean)]
    filas = []
    for c in columnas:
        vc = df[c].value_counts(sort=True)
        if vc.height == 0:
            continue
        total = df.height
        top = vc.row(0)
        filas.append({
            "columna": c,
            "n_unicos": df[c].n_unique(),
            "pct_nulos": round(100 * df[c].null_count() / total, 2),
            "moda": top[0],
            "pct_moda": round(100 * top[1] / total, 2),
            "pct_top5": round(100 * sum(vc[str(vc.columns[1])][:top_n]) / total, 2),
        })
    return pd.DataFrame(filas)
```

The pct_moda column is the one to read first. A categorical whose top value covers
more than about 90 percent of rows carries almost no information, whatever its
cardinality.

## Block 4. Missing values

The rule applied here is the one from the project instructions: below 30 percent
impute, at or above 30 percent drop, unless there is a logical way to recover the
value. A fourth branch is added because it occurs constantly in real data: a column
that is null because a row does not belong to a subpopulation is not missing, it is a
flag.

```python
def analisis_nulos(df, plot=True, top=30):
    nulos = (
        pd.DataFrame({
            "columna": df.columns,
            "n_nulos": [df[c].null_count() for c in df.columns],
        })
        .assign(pct_nulos=lambda d: (100 * d["n_nulos"] / df.height).round(2))
        .sort_values("pct_nulos", ascending=False)
        .reset_index(drop=True)
    )
    if plot:
        sub = nulos[nulos["pct_nulos"] > 0].head(top)
        if len(sub):
            fig, ax = plt.subplots(figsize=(9, max(3, 0.28 * len(sub))))
            ax.barh(sub["columna"], sub["pct_nulos"], color="#c44e52")
            ax.invert_yaxis()
            ax.axvline(30, color="black", ls=":", lw=1)
            ax.set_xlabel("porcentaje de nulos")
            ax.set_title("Columnas con valores faltantes")
            plt.show()
    return nulos


def estrategia_nulos(df, nulos, umbral=30.0, subpoblacion=None):
    """Assign one of four strategies per column.

    subpoblacion: columns that are null because the row is outside a
    subpopulation. They become a boolean flag plus the original value, and are
    never imputed.
    """
    subpoblacion = set(subpoblacion or [])
    plan = []
    for _, r in nulos.iterrows():
        c, pct = r["columna"], r["pct_nulos"]
        if pct == 0:
            est, just = "NINGUNA", "sin nulos"
        elif c in subpoblacion:
            est, just = "FLAG", "nulo estructural, indica no pertenencia al subgrupo"
        elif pct >= 100:
            est, just = "DESCARTAR", "columna vacia"
        elif pct >= umbral:
            est, just = "DESCARTAR", f"nulos {pct} por ciento, por encima del umbral"
        else:
            if df.schema[c] in (pl.Utf8, pl.Categorical, pl.Boolean):
                est, just = "IMPUTAR_MODA", "categorica por debajo del umbral"
            else:
                s = df[c].drop_nulls()
                q1, q3 = s.quantile(0.25), s.quantile(0.75)
                iqr = (q3 or 0) - (q1 or 0)
                ratio = (((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()
                         / max(s.len(), 1))
                if ratio > 0.05:
                    est, just = "IMPUTAR_MEDIANA", f"atipicos {ratio:.1%}, media inestable"
                else:
                    est, just = "IMPUTAR_MEDIA", f"atipicos {ratio:.1%}, distribucion estable"
        plan.append({"columna": c, "pct_nulos": pct,
                     "estrategia": est, "justificacion": just})
    return pd.DataFrame(plan)
```

When a column sits just under the threshold and matters, KNNImputer or an
IterativeImputer over the correlated numeric block is preferable to a constant. Both
cost a full pass over the data and both leak if fitted before the train test split, so
fit on train only.

## Block 5. Data quality audit

This block exists because the descriptive statistics of a broken column look
perfectly healthy. Run it before any plot is trusted.

```python
def auditar_claves(df, candidatas):
    """Which candidate columns are actually unique."""
    n = df.height
    return pd.DataFrame([{
        "columna": c, "n_filas": n, "n_unicos": df[c].n_unique(),
        "duplicados": n - df[c].n_unique(),
        "es_clave": df[c].n_unique() == n,
    } for c in candidatas])


def auditar_temporal(df, col_evento, col_registro=None, ventana=None):
    """Out of window dates, negative reporting lag and minute rounding."""
    s = df[col_evento].drop_nulls()
    out = {"min": s.min(), "max": s.max(), "n": s.len()}
    if ventana:
        ini, fin = ventana
        fuera = df.filter(
            (pl.col(col_evento).dt.year() < ini) | (pl.col(col_evento).dt.year() > fin)
        ).height
        out["fuera_de_ventana"] = fuera
        out["pct_fuera"] = round(100 * fuera / df.height, 3)
    minutos = df[col_evento].dt.minute().value_counts(sort=True)
    top_min = minutos.row(0)
    out["minuto_mas_comun"] = top_min[0]
    out["pct_minuto_mas_comun"] = round(100 * top_min[1] / df.height, 2)
    if col_registro:
        lag = (df.select(
            (pl.col(col_registro) - pl.col(col_evento)).dt.total_days().alias("lag")
        )["lag"].drop_nulls())
        out["lag_mediana_dias"] = lag.median()
        out["lag_p95_dias"] = lag.quantile(0.95)
        out["lag_p99_dias"] = lag.quantile(0.99)
        out["lag_negativos"] = int((lag < 0).sum())
    return pd.Series(out)


def auditar_geografia(df, lat, lon, bbox=None, col_estado=None, top=500):
    """Coordinate validity and, above all, artificial concentration.

    A high share of rows on a few coordinate pairs means the coordinates were
    imputed to a centroid. Detecting this is the point of the function.
    """
    out = {}
    if bbox:
        la_min, la_max, lo_min, lo_max = bbox
        fuera = df.filter(
            (pl.col(lat) < la_min) | (pl.col(lat) > la_max)
            | (pl.col(lon) < lo_min) | (pl.col(lon) > lo_max)
        ).height
        out["fuera_bbox"] = fuera
    out["ceros"] = df.filter((pl.col(lat) == 0) | (pl.col(lon) == 0)).height
    conteo = (df.group_by([lat, lon]).len()
                .sort("len", descending=True).head(top)["len"].sum())
    out[f"pct_en_top{top}_puntos"] = round(100 * conteo / df.height, 2)
    if col_estado:
        out["estados"] = df[col_estado].value_counts(sort=True).to_pandas()
    return out


def auditar_constantes(df):
    return [c for c in df.columns if df[c].n_unique() <= 1]
```

## Block 6. Univariate, correlation and bivariate plots

Every plotting function returns the figure so it can be saved, and every one is called
next to a written interpretation. A plot with no interpretation is not a deliverable.

```python
def plot_numericas(df, columnas, bins=50, muestra=200_000):
    """Histogram and boxplot side by side for each numeric column."""
    columnas = [c for c in columnas if df.schema[c].is_numeric()]
    fig, axes = plt.subplots(len(columnas), 2,
                             figsize=(11, 2.5 * len(columnas)), squeeze=False)
    d = df.sample(min(muestra, df.height), seed=42) if df.height > muestra else df
    for i, c in enumerate(columnas):
        v = d[c].drop_nulls().to_numpy()
        axes[i, 0].hist(v, bins=bins, color="#4c72b0", edgecolor="white", lw=0.3)
        axes[i, 0].set_title(f"{c} distribucion", fontsize=9)
        axes[i, 1].boxplot(v, vert=False, widths=0.6,
                           flierprops=dict(markersize=2, alpha=0.3))
        axes[i, 1].set_title(f"{c} dispersion y atipicos", fontsize=9)
    return fig


def plot_categoricas(df, columnas, top_n=15):
    """Horizontal barplot of the top N categories, annotated with the share."""
    ncol = 2
    nrow = int(np.ceil(len(columnas) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(13, 3.2 * nrow), squeeze=False)
    for i, c in enumerate(columnas):
        ax = axes[i // ncol, i % ncol]
        vc = df[c].value_counts(sort=True).head(top_n).to_pandas()
        etq, val = vc.columns[0], vc.columns[1]
        ax.barh(vc[etq].astype(str).str.slice(0, 32)[::-1], vc[val][::-1],
                color="#55a868")
        ax.set_title(f"{c} (top {top_n} de {df[c].n_unique()})", fontsize=9)
        ax.tick_params(labelsize=7)
    for j in range(len(columnas), nrow * ncol):
        axes[j // ncol, j % ncol].axis("off")
    return fig


def plot_correlacion(df, columnas, metodo="spearman"):
    """Spearman by default: count style variables are rarely normal."""
    pdf = df.select(columnas).drop_nulls().to_pandas()
    corr = pdf.corr(method=metodo)
    fig, ax = plt.subplots(figsize=(0.6 * len(columnas) + 3,
                                    0.5 * len(columnas) + 2.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                vmin=-1, vmax=1, square=True, linewidths=0.4,
                cbar_kws={"shrink": 0.7}, ax=ax, annot_kws={"size": 7})
    ax.set_title(f"Correlacion {metodo}")
    return fig, corr


def cramer_v(tabla):
    """Association strength between two categoricals, normalised to 0 and 1."""
    from scipy.stats import chi2_contingency
    chi2 = chi2_contingency(tabla)[0]
    n = tabla.to_numpy().sum()
    r, k = tabla.shape
    phi2 = chi2 / n
    phi2c = max(0, phi2 - (k - 1) * (r - 1) / (n - 1))
    rc = r - (r - 1) ** 2 / (n - 1)
    kc = k - (k - 1) ** 2 / (n - 1)
    return np.sqrt(phi2c / max(min(kc - 1, rc - 1), 1e-12))


def plot_bivariado_cat_cat(df, a, b, top_a=12, top_b=10, normalizar="index"):
    """Row normalised heatmap plus Cramer V. Percentages, never raw counts:
    raw counts only redraw the marginal distribution."""
    ta = df[a].value_counts(sort=True).head(top_a).to_pandas().iloc[:, 0].tolist()
    tb = df[b].value_counts(sort=True).head(top_b).to_pandas().iloc[:, 0].tolist()
    sub = df.filter(pl.col(a).is_in(ta) & pl.col(b).is_in(tb)).select([a, b]).to_pandas()
    tabla = pd.crosstab(sub[a], sub[b])
    v = cramer_v(tabla)
    pct = tabla.div(tabla.sum(axis=1), axis=0) * 100 if normalizar == "index" else tabla
    fig, ax = plt.subplots(figsize=(1.0 * len(tb) + 4, 0.45 * len(ta) + 3))
    sns.heatmap(pct, annot=True, fmt=".1f", cmap="YlOrRd", linewidths=0.4,
                ax=ax, annot_kws={"size": 7}, cbar_kws={"label": "porcentaje de fila"})
    ax.set_title(f"{a} contra {b}   Cramer V igual a {v:.3f}")
    return fig, tabla, v


def plot_serie_temporal(df, col_ts, freq="1mo", por=None, titulo="", corte=None):
    """Aggregate to a period and plot. corte draws a vertical marker where the
    series stops being comparable, for example a partial final year."""
    base = df.select([pl.col(col_ts).dt.truncate(freq).alias("periodo")]
                     + ([pl.col(por)] if por else []))
    g = (base.group_by(["periodo"] + ([por] if por else [])).len()
             .sort("periodo").to_pandas())
    fig, ax = plt.subplots(figsize=(12, 4.2))
    if por:
        for k, sub in g.groupby(por):
            ax.plot(sub["periodo"], sub["len"], lw=1.4, label=str(k)[:28])
        ax.legend(fontsize=7, ncol=3)
    else:
        ax.plot(g["periodo"], g["len"], lw=1.6, color="#4c72b0")
    if corte is not None:
        ax.axvline(pd.Timestamp(corte), color="red", ls="--", lw=1.2)
    ax.set_title(titulo or f"Evolucion temporal por {freq}")
    ax.set_ylabel("registros")
    return fig, g


def plot_heatmap_hora_dia(df, col_ts, titulo=""):
    d = df.select([
        pl.col(col_ts).dt.hour().alias("hora"),
        pl.col(col_ts).dt.weekday().alias("dia"),
    ]).group_by(["dia", "hora"]).len().to_pandas()
    piv = d.pivot(index="dia", columns="hora", values="len")
    piv.index = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"][:len(piv)]
    fig, ax = plt.subplots(figsize=(13, 3.4))
    sns.heatmap(piv, cmap="magma", linewidths=0.3, ax=ax,
                cbar_kws={"label": "registros"})
    ax.set_title(titulo or "Concentracion por hora y dia de la semana")
    return fig, piv
```

## Block 7. Unsupervised variant

Use this variant when the dataset has no label, when the available label is an
administrative artefact, or when the question is descriptive segmentation rather than
prediction.

The central design choice: cluster entities on **proportions**, not on counts.
Clustering districts on raw counts produces one cluster of large districts and one of
small ones, which is a restatement of population. Clustering on the composition of
their activity produces groups that share a problem, which is what a decision needs.

```python
def construir_matriz_perfil(df, entidad, categoria, top_categorias=15, min_n=200):
    """Entity by category matrix of row normalised proportions."""
    top = (df[categoria].value_counts(sort=True).head(top_categorias)
             .to_pandas().iloc[:, 0].tolist())
    sub = df.filter(pl.col(categoria).is_in(top))
    tabla = (sub.group_by([entidad, categoria]).len()
                .to_pandas()
                .pivot(index=entidad, columns=categoria, values="len")
                .fillna(0))
    tabla = tabla[tabla.sum(axis=1) >= min_n]
    prop = tabla.div(tabla.sum(axis=1), axis=0)
    return prop, tabla


def elegir_k(X, k_min=2, k_max=10, semilla=42, plot=True):
    """Silhouette and inertia over a range of k. Silhouette decides, the elbow
    is only a sanity check."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    filas = []
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=semilla, n_init=10).fit(X)
        filas.append({"k": k, "inercia": km.inertia_,
                      "silhouette": silhouette_score(X, km.labels_)})
    res = pd.DataFrame(filas)
    if plot:
        fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
        ax[0].plot(res["k"], res["inercia"], "o-", color="#4c72b0")
        ax[0].set_title("Inercia (codo)"); ax[0].set_xlabel("k")
        ax[1].plot(res["k"], res["silhouette"], "o-", color="#c44e52")
        mejor = res.loc[res["silhouette"].idxmax(), "k"]
        ax[1].axvline(mejor, ls=":", color="black")
        ax[1].set_title("Coeficiente de silueta"); ax[1].set_xlabel("k")
        plt.show()
    return res, int(res.loc[res["silhouette"].idxmax(), "k"])


def clusterizar_perfil(prop, k, semilla=42):
    """Standardise, cluster, and return labels with the fitted objects."""
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    X = StandardScaler().fit_transform(prop.values)
    km = KMeans(n_clusters=k, random_state=semilla, n_init=20).fit(X)
    etiquetas = pd.Series(km.labels_, index=prop.index, name="cluster")
    return etiquetas, km, X


def describir_clusters(prop, etiquetas, top_n=3):
    """Name each cluster by the categories where it exceeds the global average
    by the widest margin. This is what makes the output usable."""
    global_med = prop.mean()
    filas = []
    for c in sorted(etiquetas.unique()):
        miembros = etiquetas[etiquetas == c].index
        perfil = prop.loc[miembros].mean()
        lift = (perfil - global_med).sort_values(ascending=False)
        filas.append({
            "cluster": c,
            "n_entidades": len(miembros),
            "miembros": ", ".join(map(str, miembros[:8])),
            "rasgos_altos": ", ".join(
                f"{i} ({100 * perfil[i]:.1f}%)" for i in lift.head(top_n).index),
            "rasgos_bajos": ", ".join(
                f"{i} ({100 * perfil[i]:.1f}%)" for i in lift.tail(top_n).index),
        })
    return pd.DataFrame(filas)


def plot_clusters_pca(X, etiquetas, nombres=None, titulo=""):
    from sklearn.decomposition import PCA
    p = PCA(n_components=2, random_state=42)
    Z = p.fit_transform(X)
    fig, ax = plt.subplots(figsize=(9, 6.5))
    ax.scatter(Z[:, 0], Z[:, 1], c=etiquetas.values, cmap="tab10", s=90,
               edgecolor="white", lw=0.8)
    if nombres is not None:
        for i, n in enumerate(nombres):
            ax.annotate(str(n)[:18], (Z[i, 0], Z[i, 1]), fontsize=7,
                        xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel(f"CP1 ({100 * p.explained_variance_ratio_[0]:.1f}% varianza)")
    ax.set_ylabel(f"CP2 ({100 * p.explained_variance_ratio_[1]:.1f}% varianza)")
    ax.set_title(titulo or "Proyeccion PCA de los clusters")
    return fig, p


def hotspots_espaciales(df, lat, lon, k=8, semilla=42, muestra=300_000):
    """KMeans over coordinates. Run it ONLY on rows with trusted coordinates.
    Imputed centroids create clusters that describe police stations."""
    from sklearn.cluster import KMeans
    d = df.select([lat, lon]).drop_nulls()
    if d.height > muestra:
        d = d.sample(muestra, seed=semilla)
    P = d.to_numpy()
    km = KMeans(n_clusters=k, random_state=semilla, n_init=10).fit(P)
    centros = pd.DataFrame(km.cluster_centers_, columns=["lat", "lon"])
    centros["n"] = pd.Series(km.labels_).value_counts().sort_index().values
    centros["pct"] = (100 * centros["n"] / len(P)).round(2)
    return km, centros, P
```

## Block 8. Supervised variant

### 8.1 Choosing between the two variants

| Situation | Variant |
|---|---|
| No label column exists | Unsupervised |
| The only label is derivable from the features by definition | Unsupervised, the label is a relabelling |
| A label exists but every positive case is recorded and no negative case is | Unsupervised, or supervised with explicit negative sampling and a stated denominator |
| A label exists, both classes are observed, and the features are knowable before the label | Supervised |
| Both apply | Run unsupervised first. It describes the structure the supervised model will have to respect |

Before writing a single feature, answer these five questions in writing.

1. What decision changes depending on the prediction. If none, stop.
2. Is the label observed independently of the features, or is it a function of them.
3. Are both classes observed, or only the positives.
4. What is the natural validation split. If the data has a time axis, it is temporal.
5. Which columns encode the answer. Those are excluded before anything else.

### 8.2 Leakage guard

This runs first and it raises. Prose commitments are not enforcement.

```python
def verificar_fuga(features, prohibidas):
    """Fail loudly if any feature encodes the target."""
    fuga = sorted(set(features) & set(prohibidas))
    if fuga:
        raise ValueError(
            "Fuga de informacion. Estas columnas codifican el target: "
            + ", ".join(fuga)
        )
    return True
```

### 8.3 Reversible label encoding

Label encoding is preferred over one hot for tree models: it keeps the matrix narrow
and LightGBM splits categorical codes natively. The mapping is kept and persisted, so
the original meaning is always recoverable.

```python
def codificar_categoricas(pdf, columnas, mapas=None):
    """Label encode with an explicit dictionary. Unseen categories map to minus one."""
    aprender = mapas is None
    mapas = {} if aprender else mapas
    out = pdf.copy()
    for c in columnas:
        s = out[c].astype(str).fillna("DESCONOCIDO")
        if aprender:
            mapas[c] = {v: i for i, v in enumerate(sorted(s.unique()))}
        out[c + "_le"] = s.map(mapas[c]).fillna(-1).astype("int32")
    return out, mapas


def guardar_mapas(mapas, ruta="mapas_categoricos.json"):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(mapas, f, ensure_ascii=False, indent=2)


def recuperar_categoria(mapas, columna, codigo):
    """Inverse lookup. This is why label encoding is safe here."""
    inverso = {v: k for k, v in mapas[columna].items()}
    return inverso.get(int(codigo), "DESCONOCIDO")
```

### 8.4 Optimal binning, applied only when it pays

The instruction is to bucketize only when discriminative power improves. So measure
it. Information Value before and after, and keep the binned version only if it wins.

```python
def bucketizar_si_mejora(pdf, columnas, y, ganancia_minima=0.02):
    """OptimalBinning per column. Keep the binned version only when the
    Information Value gain exceeds the threshold."""
    from optbinning import OptimalBinning
    out, decisiones = pdf.copy(), []
    for c in columnas:
        x = pdf[c].values
        try:
            ob = OptimalBinning(name=c, dtype="numerical", solver="cp")
            ob.fit(x, y)
            iv_bin = ob.binning_table.build()["IV"].iloc[-1]
        except Exception as e:
            decisiones.append({"columna": c, "decision": "SIN_BINNING",
                               "motivo": str(e)[:60], "iv_bin": np.nan})
            continue
        iv_crudo = iv_univariado(x, y)
        gana = (iv_bin - iv_crudo) > ganancia_minima
        if gana:
            out[c + "_bin"] = ob.transform(x, metric="woe")
        decisiones.append({
            "columna": c, "iv_crudo": round(iv_crudo, 4),
            "iv_binned": round(float(iv_bin), 4),
            "decision": "BUCKETIZAR" if gana else "MANTENER_ESCALA_REAL",
        })
    return out, pd.DataFrame(decisiones)


def iv_univariado(x, y, bins=10):
    """Information Value of a raw numeric column, via quantile bins."""
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    d["b"] = pd.qcut(d["x"], bins, duplicates="drop")
    g = d.groupby("b", observed=True)["y"].agg(["sum", "count"])
    g["bad"] = g["sum"]
    g["good"] = g["count"] - g["sum"]
    g = g[(g["bad"] > 0) & (g["good"] > 0)]
    pb, pg = g["bad"] / g["bad"].sum(), g["good"] / g["good"].sum()
    return float(((pb - pg) * np.log(pb / pg)).sum())
```

A note that generalises beyond this dataset: **never drop a categorical because one
category dominates it.** On the reference data, tipo_via_hecho holds one value in
87.9 percent of rows and every descriptive summary flags it as uninformative. It
turned out to be the single most valuable categorical feature in the model,
because its missing marker separates the classes by 23.6 points. Concentration and
information are different quantities. Let the funnel decide by measurement.

Keeping the real scale is the default. Tree models split on raw values without help,
and binning throws away resolution. Binning earns its place with logistic regression,
with monotonicity constraints, or when a variable has a genuinely non monotone
relationship with the target.

### 8.5 The feature selection funnel

Four rounds for numeric features, then fewer rounds for categoricals, exactly as
specified in the project instructions.

```python
def filtro_varianza(pdf, columnas, umbral=0.1):
    """Round zero. Drop near constant features. Compare on the standardised
    scale, otherwise the threshold means something different per column."""
    from sklearn.preprocessing import StandardScaler
    Z = StandardScaler().fit_transform(pdf[columnas].fillna(0))
    var = pd.Series(Z.var(axis=0), index=columnas)
    return var[var >= umbral].index.tolist(), var.sort_values()


def entrenar_modelo(X, y, split, params=None, categoricas=None):
    """LightGBM with a boolean train mask. The mask is the temporal split."""
    import lightgbm as lgb
    p = dict(n_estimators=400, learning_rate=0.06, num_leaves=64,
             subsample=0.8, colsample_bytree=0.8, random_state=42, verbose=-1)
    p.update(params or {})
    m = lgb.LGBMClassifier(**p)
    m.fit(X[split], y[split],
          categorical_feature=categoricas or "auto")
    return m


def evaluar_modelo(m, X, y, split_test, etiqueta=""):
    from sklearn.metrics import (roc_auc_score, average_precision_score,
                                 f1_score, balanced_accuracy_score)
    p = m.predict_proba(X[split_test])[:, 1]
    yt = y[split_test]
    return {
        "conjunto": etiqueta,
        "n": int(split_test.sum()),
        "tasa_positiva": round(float(yt.mean()), 4),
        "auc": round(roc_auc_score(yt, p), 4),
        "average_precision": round(average_precision_score(yt, p), 4),
        "ap_base": round(float(yt.mean()), 4),
        "f1_en_05": round(f1_score(yt, (p >= 0.5).astype(int)), 4),
        "exactitud_balanceada": round(
            balanced_accuracy_score(yt, (p >= 0.5).astype(int)), 4),
    }


def filtro_importancia(m, columnas, umbral=0.05):
    """Round one. Normalised gain importance below the threshold is dropped."""
    imp = pd.Series(m.feature_importances_, index=columnas).astype(float)
    imp = imp / imp.sum()
    return imp[imp >= umbral].index.tolist(), imp.sort_values(ascending=False)


def filtro_shap(m, X, columnas, umbral=0.1, muestra=20_000, semilla=42):
    """Round one, SHAP flavour. Mean absolute SHAP, normalised so the threshold
    is comparable across datasets. Slower than gain importance and far more
    faithful, because gain is biased toward high cardinality features."""
    import shap
    Xs = X.sample(min(muestra, len(X)), random_state=semilla)
    sv = shap.TreeExplainer(m).shap_values(Xs)
    if isinstance(sv, list):
        sv = sv[1]
    if sv.ndim == 3:
        sv = sv[:, :, 1]
    imp = pd.Series(np.abs(sv).mean(axis=0), index=columnas)
    imp = imp / imp.sum()
    return imp[imp >= umbral].index.tolist(), imp.sort_values(ascending=False), sv, Xs


def filtro_correlacion(pdf, columnas, importancia, umbral=0.5):
    """Round two. Within each correlated pair above the threshold, keep the
    member the model already ranks higher. Never drop blindly."""
    corr = pdf[columnas].corr(method="pearson").abs()
    descartar = set()
    for i, a in enumerate(columnas):
        for b in columnas[i + 1:]:
            if a in descartar or b in descartar:
                continue
            if corr.loc[a, b] > umbral:
                perdedor = b if importancia.get(a, 0) >= importancia.get(b, 0) else a
                descartar.add(perdedor)
    return [c for c in columnas if c not in descartar], sorted(descartar)


def diagnostico_sobreajuste(m, X, y, split_train, split_test):
    """Round three input. If the train test gap is wide, run a further
    importance round; if the model then improves, keep the reduced set."""
    from sklearn.metrics import roc_auc_score
    a_tr = roc_auc_score(y[split_train], m.predict_proba(X[split_train])[:, 1])
    a_te = roc_auc_score(y[split_test], m.predict_proba(X[split_test])[:, 1])
    return {"auc_train": round(a_tr, 4), "auc_test": round(a_te, 4),
            "brecha": round(a_tr - a_te, 4),
            "sobreajuste": (a_tr - a_te) > 0.05}


def embudo_numerico(pdf, numericas, y, split_tr, split_te,
                    umbral_var=0.1, umbral_imp=0.05,
                    umbral_shap=0.1, umbral_corr=0.5, usar_shap=True):
    """The full four round funnel. Returns the surviving features and a log of
    every round, so each drop is auditable."""
    log, cols = [], list(numericas)

    cols, var = filtro_varianza(pdf, cols, umbral_var)
    log.append({"ronda": "0 varianza", "quedan": len(cols)})

    m = entrenar_modelo(pdf[cols], y, split_tr)
    log.append({"ronda": "1 entrenamiento base",
                **evaluar_modelo(m, pdf[cols], y, split_te, "test")})
    if usar_shap:
        cols2, imp, _, _ = filtro_shap(m, pdf[cols], cols, umbral_shap)
    else:
        cols2, imp = filtro_importancia(m, cols, umbral_imp)
    log.append({"ronda": "1 filtro importancia", "quedan": len(cols2)})
    cols = cols2 or cols

    m = entrenar_modelo(pdf[cols], y, split_tr)
    cols3, quitadas = filtro_correlacion(pdf, cols, imp, umbral_corr)
    log.append({"ronda": "2 filtro correlacion", "quedan": len(cols3),
                "quitadas": ", ".join(quitadas)})
    cols = cols3 or cols

    m = entrenar_modelo(pdf[cols], y, split_tr)
    diag = diagnostico_sobreajuste(m, pdf[cols], y, split_tr, split_te)
    log.append({"ronda": "3 diagnostico", **diag})

    if diag["sobreajuste"]:
        cols4, _ = filtro_importancia(m, cols, umbral_imp * 2)
        m4 = entrenar_modelo(pdf[cols4], y, split_tr)
        e_antes = evaluar_modelo(m, pdf[cols], y, split_te)["auc"]
        e_desp = evaluar_modelo(m4, pdf[cols4], y, split_te)["auc"]
        if e_desp >= e_antes:
            cols, m = cols4, m4
        log.append({"ronda": "4 poda por sobreajuste", "quedan": len(cols),
                    "auc_antes": e_antes, "auc_despues": e_desp})

    return cols, m, pd.DataFrame(log)


def embudo_categorico(pdf, base_numerica, categoricas_le, y, split_tr, split_te):
    """Add categoricals one at a time on top of the surviving numeric block.
    Keep only those that raise holdout AUC. Fewer rounds, as specified."""
    actual = list(base_numerica)
    m = entrenar_modelo(pdf[actual], y, split_tr)
    mejor = evaluar_modelo(m, pdf[actual], y, split_te)["auc"]
    log = [{"paso": "base numerica", "auc": mejor, "n_features": len(actual)}]
    for c in categoricas_le:
        cand = actual + [c]
        mc = entrenar_modelo(pdf[cand], y, split_tr, categoricas=[c])
        auc = evaluar_modelo(mc, pdf[cand], y, split_te)["auc"]
        acepta = auc > mejor
        log.append({"paso": f"mas {c}", "auc": auc,
                    "decision": "ACEPTAR" if acepta else "RECHAZAR"})
        if acepta:
            actual, mejor = cand, auc
    m = entrenar_modelo(pdf[actual], y, split_tr,
                        categoricas=[c for c in actual if c in categoricas_le])
    return actual, m, pd.DataFrame(log)
```

### 8.6 Reading SHAP

Global mean absolute SHAP ranks features. The beeswarm shows direction and is the plot
that actually earns the compute: it tells whether a high value of a feature pushes the
prediction up or down, and whether the effect is uniform or splits into subpopulations.

```python
def plot_shap(sv, Xs, max_display=15):
    import shap
    shap.summary_plot(sv, Xs, max_display=max_display, show=False)
    fig = plt.gcf(); fig.set_size_inches(9, 5.5)
    plt.tight_layout(); plt.show()
    shap.summary_plot(sv, Xs, plot_type="bar", max_display=max_display, show=False)
    fig = plt.gcf(); fig.set_size_inches(8, 4.5)
    plt.tight_layout(); plt.show()
```

Two warnings that matter on label encoded features. A SHAP beeswarm colours points by
feature value, and for a label encoded categorical that value is an arbitrary integer,
so the colour gradient is meaningless. Read only the width of the band, which is the
magnitude of the effect, and use a dependence plot with the recovered category names
for direction. Second, gain importance is biased toward high cardinality features, so
when the two rankings disagree, trust SHAP.

## Block 9. Orchestrator

```python
def complete_eda(config, descripciones, modo="ambos", verbose=True):
    """Run the whole pipeline end to end.

    modo: "supervisado", "no_supervisado" or "ambos".
    Returns a dict with every intermediate artefact, so each stage can be
    inspected after the fact instead of only printed.
    """
    R, t0 = {}, time.perf_counter()

    def paso(n, txt):
        if verbose:
            print(f"\n{'=' * 78}\n[{n}] {txt}\n{'=' * 78}")

    paso(1, "Perfilado de esquema y diccionario de datos")
    con = abrir_duckdb(config["csv"], muestra=config["muestra_esquema"])
    R["perfil"] = recomendar_accion(perfilar_esquema(con),
                                    config["umbral_null_descarte"])
    R["diccionario"] = generar_diccionario(
        R["perfil"], descripciones, config["salida"] / "diccionario_datos.csv")

    paso(2, "Carga en ambos motores")
    R["df_duck"], R["t_duck"] = cargar_duckdb(con, config["columnas"])
    R["df"], R["t_polars"] = cargar_polars(config["csv"], config["columnas"])
    R["df"] = parsear_timestamps(R["df"], config["columnas_ts"])

    paso(3, "Optimizacion de memoria")
    R["df"], R["reporte_tipos"] = optimizar_memoria(
        R["df"], config["umbral_categoria"])
    liberar(R.pop("df_duck"))

    paso(4, "Estadisticas descriptivas")
    R["num"] = resumen_numerico(R["df"])
    R["cat"] = resumen_categorico(R["df"])

    paso(5, "Valores faltantes")
    R["nulos"] = analisis_nulos(R["df"])
    R["plan_nulos"] = estrategia_nulos(
        R["df"], R["nulos"], config["umbral_null_descarte"] * 100,
        config.get("nulos_estructurales"))

    paso(6, "Auditoria de calidad")
    R["auditoria"] = {
        "claves": auditar_claves(R["df"], config["claves_candidatas"]),
        "temporal": auditar_temporal(R["df"], config["col_evento"],
                                     config.get("col_registro"),
                                     config.get("ventana")),
        "geografia": auditar_geografia(R["df"], *config["geo"],
                                       bbox=config.get("bbox"),
                                       col_estado=config.get("col_estado_geo")),
        "constantes": auditar_constantes(R["df"]),
    }

    paso(7, "Distribuciones univariadas")
    plot_numericas(R["df"], config["plot_numericas"]); plt.show()
    plot_categoricas(R["df"], config["plot_categoricas"],
                     config["top_n_categorias"]); plt.show()

    paso(8, "Correlacion")
    _, R["corr"] = plot_correlacion(R["df"], config["plot_numericas"]); plt.show()

    paso(9, "Relaciones bivariadas")
    R["bivariado"] = {}
    for a, b in config["pares_bivariados"]:
        _, tabla, v = plot_bivariado_cat_cat(R["df"], a, b); plt.show()
        R["bivariado"][f"{a}|{b}"] = {"tabla": tabla, "cramer_v": v}

    paso(10, "Evolucion temporal")
    _, R["serie"] = plot_serie_temporal(R["df"], config["col_evento"],
                                        corte=config.get("corte_serie")); plt.show()
    _, R["heat_hora"] = plot_heatmap_hora_dia(R["df"], config["col_evento"]); plt.show()

    if modo in ("no_supervisado", "ambos"):
        paso(11, "Modelo no supervisado")
        prop, _ = construir_matriz_perfil(R["df"], config["entidad"],
                                          config["categoria_perfil"])
        _, k = elegir_k(
            __import__("sklearn.preprocessing", fromlist=["StandardScaler"])
            .StandardScaler().fit_transform(prop.values))
        etq, km, X = clusterizar_perfil(prop, k, config["semilla"])
        R["clusters"] = {"proporciones": prop, "k": k, "etiquetas": etq,
                         "descripcion": describir_clusters(prop, etq)}
        plot_clusters_pca(X, etq, prop.index); plt.show()

    if modo in ("supervisado", "ambos"):
        paso(12, "Modelo supervisado")
        pdf, y, split_tr, split_te, feats = config["preparar_supervisado"](R["df"])
        verificar_fuga(feats, config["columnas_prohibidas"])
        cols, modelo, log = embudo_numerico(pdf, config["numericas"], y,
                                            split_tr, split_te)
        cols, modelo, log_cat = embudo_categorico(pdf, cols, config["categoricas_le"],
                                                  y, split_tr, split_te)
        R["supervisado"] = {
            "features": cols, "modelo": modelo,
            "log_numerico": log, "log_categorico": log_cat,
            "metricas": evaluar_modelo(modelo, pdf[cols], y, split_te, "holdout"),
        }

    R["segundos"] = round(time.perf_counter() - t0, 1)
    if verbose:
        print(f"\nPipeline completo en {R['segundos']} segundos")
    return R
```

## 10. Reuse checklist

To point this template at a different dataset, change these and nothing else.

1. CONFIG csv path and the column projection.
2. The descripciones dictionary for the data dictionary.
3. config columns: col_evento, col_registro, geo, bbox, claves_candidatas.
4. nulos_estructurales, the columns that are null because of subpopulation
   membership rather than missingness.
5. columnas_prohibidas, everything that encodes the target.
6. preparar_supervisado, the function that builds the target and the split.
7. entidad and categoria_perfil for the unsupervised variant.

Everything else is dataset independent.

## 11. Failure modes this template is designed to catch

| Symptom | Real cause | Which block catches it |
|---|---|---|
| AUC above 0.98 on a hard problem | A feature encodes the target | Block 8.2, verificar_fuga |
| Beautiful density map, useless | Coordinates imputed to centroids | Block 5, auditar_geografia |
| Sharp decline in the final period | Partial period or reporting lag | Block 5, auditar_temporal |
| Hourly peak at an office hour | Timestamps rounded by the intake process | Block 5, minute rounding check |
| Clusters that are just big and small | Clustering on counts instead of proportions | Block 7, construir_matriz_perfil |
| Model degrades in production | Random split hid a temporal shift | Block 8, temporal split |
| Feature ranking dominated by an identifier | Gain importance favours high cardinality | Block 8.6, SHAP instead of gain |
| Ninety percent of a column imputed | Structural null treated as missing | Block 4, estrategia_nulos FLAG branch |
| A useful column dropped for being lopsided | pct_moda measures concentration, not information: the rare categories and the missing marker can separate the classes | Block 8.5, embudo_categorico decides by measured AUC gain |
| Two importance rankings disagree | Gain is biased toward high cardinality features | Block 8.6, follow SHAP and cross check with a measured AUC gain |
