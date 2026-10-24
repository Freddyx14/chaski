"""Corrige el sesgo de registro y entrena dentro del mismo regimen.

Hipotesis de 11-resultados.md: el modelo entrenado con 2018-2022 aprende DONDE SE
REGISTRABA BIEN, no donde hay violencia, porque la tasa de geocodificado cae de
48.5% (2018) a 30.6% (2023). Dos correcciones:
  1. Entrenar solo con 2022 y probar 2023: regimenes contiguos.
  2. Meter la tasa de geocodificado del distrito y el ano como feature, para que
     el modelo pueda descontarla.
Uso: PYTHONPATH=. uv run --with ... python validacion/06_sesgo_registro.py
"""
import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score

from pipeline.metricas import pai, recall_en_k
from pipeline.panel import recortar_borde

CSV = "delitos_lima_metropolitana_completo_2018-25.csv"


def tasa_geocodificado() -> pd.DataFrame:
    """Fraccion de hechos con coordenada utilizable, por distrito y ano."""
    con = duckdb.connect()
    con.execute(f"create view raw as select * from read_csv_auto('{CSV}', "
                "ignore_errors=true, sample_size=300000)")
    return con.execute("""
        select distrito_hecho distrito, "año_hecho" anio,
               avg(case when estado_coord = 'CON COORDENADA' then 1.0 else 0 end) tasa_geo,
               count(*) hechos_totales
        from raw where "año_hecho" between 2018 and 2025
        group by 1, 2
    """).df()


def evaluar(nombre, datos, columna_score):
    datos = datos.rename(columns={columna_score: "score"})
    fila = {"config": nombre,
            "auc_pr": average_precision_score(datos["y_escala"], datos["score"])}
    for k in (0.01, 0.05):
        fila[f"pai_{int(k*100)}"] = pai(datos, "score", k)
        fila[f"recall_{int(k*100)}"] = recall_en_k(datos, "score", k)
    alto = datos["score"] >= datos["score"].quantile(0.99)
    fila["tasa_top1"] = datos.loc[alto, "y_escala"].mean()
    fila["tasa_base"] = datos["y_escala"].mean()
    return fila


def main():
    panel = pd.read_parquet("data/panel.parquet").sort_values(["corredor_id", "semana"])
    extra = pd.read_parquet("data/features.parquet",
                            columns=["corredor_id", "semana", "largo_m", "grado",
                                     "ext_vec1_lag_1"])
    panel = panel.merge(extra, on=["corredor_id", "semana"], how="left")

    # distrito de cada corredor: el del hecho mas frecuente enganchado ahi
    eventos = pd.read_parquet("data/eventos_con_corredor.parquet",
                              columns=["corredor_id", "distrito"])
    distrito = (eventos.groupby("corredor_id")["distrito"]
                .agg(lambda s: s.value_counts().index[0]))
    panel["distrito"] = panel["corredor_id"].map(distrito)
    panel["anio"] = panel["semana"].dt.year
    panel = panel.merge(tasa_geocodificado(), on=["distrito", "anio"], how="left")
    panel["tasa_geo"] = panel["tasa_geo"].fillna(panel["tasa_geo"].median())

    grupo = panel.groupby("corredor_id")
    for v in (4, 12, 26, 52):
        panel[f"ext_r{v}"] = grupo["ext"].transform(
            lambda s, v=v: s.shift(1).rolling(v, min_periods=1).sum())
        panel[f"viol_r{v}"] = grupo["viol"].transform(
            lambda s, v=v: s.shift(1).rolling(v, min_periods=1).sum())
    for v in (4, 12):
        panel[f"vec_r{v}"] = grupo["ext_vec1_lag_1"].transform(
            lambda s, v=v: s.rolling(v, min_periods=1).sum())

    base = [c for c in panel.columns if c.startswith(("ext_r", "viol_r", "vec_r"))]
    base += ["largo_m", "grado"]

    prueba = recortar_borde(panel[panel["anio"] == 2023], "2023-12-31").copy()
    filas = [evaluar("baseline violencia 4 sem", prueba.assign(s=prueba["viol_r4"]), "s")]

    ventanas = {"2018-2022 (como estaba)": (2018, 2022), "solo 2022 (mismo regimen)": (2022, 2022)}
    for nombre, (desde, hasta) in ventanas.items():
        entrenamiento = recortar_borde(
            panel[(panel["anio"] >= desde) & (panel["anio"] <= hasta)], f"{hasta}-12-31")
        for con_tasa in (False, True):
            columnas = base + (["tasa_geo"] if con_tasa else [])
            modelo = HistGradientBoostingClassifier(
                max_iter=250, learning_rate=0.08, random_state=0)
            modelo.fit(entrenamiento[columnas], entrenamiento["y_escala"])
            puntaje = modelo.predict_proba(prueba[columnas])[:, 1]
            etiqueta = f"{nombre}{' + tasa_geo' if con_tasa else ''}"
            filas.append(evaluar(etiqueta, prueba.assign(s=puntaje), "s"))

    tabla = pd.DataFrame(filas)
    tabla.to_csv("reports/sesgo_registro.csv", index=False)
    pd.set_option("display.width", 200)
    print(tabla.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
