"""Particion temporal, entrenamiento y evaluacion.

La ventana de prueba es 2023 y no 2025 porque en 2025 solo el 3.2% de las
denuncias de extorsion tiene coordenada utilizable (propuesta/09-validaciones.md).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, brier_score_loss

from pipeline.metricas import pai, recall_en_k
from pipeline.panel import recortar_borde

FIN_ENTRENAMIENTO = "2022-12-31"
INICIO_PRUEBA = "2023-01-01"
FIN_PRUEBA = "2023-12-31"


def particionar(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    entrenamiento = features[features["semana"] <= pd.Timestamp(FIN_ENTRENAMIENTO)]
    entrenamiento = recortar_borde(entrenamiento, FIN_ENTRENAMIENTO)
    prueba = features[(features["semana"] >= pd.Timestamp(INICIO_PRUEBA)) &
                      (features["semana"] <= pd.Timestamp(FIN_PRUEBA))]
    prueba = recortar_borde(prueba, FIN_PRUEBA)
    return entrenamiento.copy(), prueba.copy()


def entrenar(entrenamiento: pd.DataFrame, columnas: list, semilla: int = 0):
    modelo = HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.1, random_state=semilla)
    modelo.fit(entrenamiento[columnas], entrenamiento["y_escala"])
    return modelo


def evaluar(modelo, prueba: pd.DataFrame, columnas: list) -> dict:
    datos = prueba.copy()
    datos["score"] = modelo.predict_proba(datos[columnas])[:, 1]
    return _metricas(datos)


def _metricas(datos: pd.DataFrame) -> dict:
    por_semana = [
        (pai(grupo, "score", 0.05), recall_en_k(grupo, "score", 0.05))
        for _, grupo in datos.groupby("semana") if grupo["y_escala"].sum() > 0
    ]
    pais = [p for p, _ in por_semana]
    recalls = [r for _, r in por_semana]
    return {
        "auc_pr": float(average_precision_score(datos["y_escala"], datos["score"])),
        "pai_5": float(np.mean(pais)) if pais else 0.0,
        "recall_5": float(np.mean(recalls)) if recalls else 0.0,
        # el Brier solo tiene sentido si el score es una probabilidad; los
        # baselines son conteos
        "brier": (float(brier_score_loss(datos["y_escala"], datos["score"]))
                  if datos["score"].between(0, 1).all() else None),
        "prevalencia": float(datos["y_escala"].mean()),
        "semanas": len(por_semana),
    }


def evaluar_score(prueba: pd.DataFrame, score: pd.Series) -> dict:
    """Metricas de un baseline, que no es un modelo entrenado."""
    datos = prueba.copy()
    datos["score"] = score.to_numpy()
    salida = _metricas(datos)
    salida["auc_pr"] = float(average_precision_score(datos["y_escala"], datos["score"]))
    return salida
