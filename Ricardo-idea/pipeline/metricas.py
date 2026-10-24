"""Metricas de pronostico espacial.

PAI (Predictive Accuracy Index) es el estandar del campo (Kounadi et al. 2020;
Mohler & Porter 2020, ver propuesta/05-estado-del-arte.md seccion 5):

    PAI = (n/N) / (a/A)

n hechos dentro de lo marcado, N hechos totales, a longitud de via marcada,
A longitud total. PAI = 10 quiere decir que lo marcado concentra diez veces mas
hechos de los que le tocarian por tamano. Se mide en LONGITUD, no en numero de
corredores: un corredor largo cuesta mas patrullarlo que uno corto.
"""
import pandas as pd


def _marcados(df: pd.DataFrame, score_col: str, k_frac: float, largo_col: str) -> pd.DataFrame:
    orden = df.sort_values(score_col, ascending=False).copy()
    orden["acumulado"] = orden[largo_col].cumsum()
    marcados = orden[orden["acumulado"] <= k_frac * orden[largo_col].sum()]
    return marcados if not marcados.empty else orden.head(1)


def pai(df: pd.DataFrame, score_col: str, k_frac: float,
        largo_col: str = "largo_m", y_col: str = "y_escala") -> float:
    marcados = _marcados(df, score_col, k_frac, largo_col)
    n, total_n = marcados[y_col].sum(), df[y_col].sum()
    a, total_a = marcados[largo_col].sum(), df[largo_col].sum()
    if total_n == 0 or a == 0:
        return 0.0
    return float((n / total_n) / (a / total_a))


def recall_en_k(df: pd.DataFrame, score_col: str, k_frac: float,
                largo_col: str = "largo_m", y_col: str = "y_escala") -> float:
    total_n = df[y_col].sum()
    if total_n == 0:
        return 0.0
    return float(_marcados(df, score_col, k_frac, largo_col)[y_col].sum() / total_n)


def baseline_extorsion(features: pd.DataFrame) -> pd.Series:
    """Donde hubo denuncias de extorsion hace poco."""
    return features[[f"ext_lag_{l}" for l in (1, 2, 4)]].sum(axis=1)


def baseline_violencia(features: pd.DataFrame) -> pd.Series:
    """Donde hubo violencia armada hace poco. Es el baseline duro: en la
    validacion previa dio lift 33x contra 6.7x del de extorsion."""
    return features["viol_lag_4"]
