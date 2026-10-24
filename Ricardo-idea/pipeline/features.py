"""Features del panel corredor x semana.

Bloques, segun propuesta/07-ablation.md:
  A  persistencia propia      lags de extorsion del mismo corredor
  B  difusion en el grafo     extorsion en los corredores vecinos
  C  contagio cruzado         violencia armada previa
  D  estructura               largo y conectividad del corredor
  G  temporal                 estacionalidad y tendencia

Todas las features de la semana t usan informacion de t-1 hacia atras. Nunca t.
"""
import numpy as np
import pandas as pd

LAGS_PROPIOS = [1, 2, 4, 8, 12]
LAGS_VECINOS = [1, 2, 4]
VENTANAS_VIOLENCIA = [4, 12]

BLOQUES = {
    "A": [f"ext_lag_{l}" for l in LAGS_PROPIOS],
    "B": [f"ext_vec1_lag_{l}" for l in LAGS_VECINOS],
    "C": [f"viol_lag_{v}" for v in VENTANAS_VIOLENCIA],
    "D": ["largo_m", "grado"],
    "G": ["semana_del_anio", "tendencia"],
}


def agregar_features(panel: pd.DataFrame, vecinos: dict) -> pd.DataFrame:
    df = panel.sort_values(["corredor_id", "semana"]).reset_index(drop=True).copy()

    for l in LAGS_PROPIOS:
        df[f"ext_lag_{l}"] = (df.groupby("corredor_id")["ext"].shift(l)
                              .fillna(0).astype("float32"))

    for v in VENTANAS_VIOLENCIA:
        df[f"viol_lag_{v}"] = (df.groupby("corredor_id")["viol"]
                               .transform(lambda s, v=v: s.shift(1)
                                          .rolling(v, min_periods=1).sum())
                               .fillna(0).astype("float32"))

    # difusion: suma de la extorsion de los vecinos, desplazada
    ancho = df.pivot_table(index="semana", columns="corredor_id", values="ext",
                           aggfunc="sum", fill_value=0)
    columnas = list(ancho.columns)
    posicion = {cid: i for i, cid in enumerate(columnas)}
    matriz = ancho.to_numpy(dtype="float32")
    indices = [[posicion[v] for v in vecinos.get(cid, []) if v in posicion]
               for cid in columnas]
    suma = np.zeros_like(matriz)
    for j, vecinos_j in enumerate(indices):
        if vecinos_j:
            suma[:, j] = matriz[:, vecinos_j].sum(axis=1)
    vecinos_df = pd.DataFrame(suma, index=ancho.index, columns=columnas)

    for l in LAGS_VECINOS:
        largo = (vecinos_df.shift(l).fillna(0).stack().rename(f"ext_vec1_lag_{l}")
                 .reset_index())
        largo.columns = ["semana", "corredor_id", f"ext_vec1_lag_{l}"]
        df = df.merge(largo, on=["semana", "corredor_id"], how="left")
        df[f"ext_vec1_lag_{l}"] = df[f"ext_vec1_lag_{l}"].fillna(0).astype("float32")

    df["semana_del_anio"] = df["semana"].dt.isocalendar().week.astype("int16")
    df["tendencia"] = ((df["semana"] - df["semana"].min()).dt.days // 7).astype("int16")

    for columna in ("largo_m", "grado"):
        if columna not in df.columns:
            df[columna] = 0.0
    return df
