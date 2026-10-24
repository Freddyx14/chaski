"""Ablation: cuanto aporta cada bloque de informacion, por encima del baseline.

La pregunta no es cual modelo gana, sino que informacion vale la pena cruzar.
El baseline duro es la persistencia de la violencia: en la validacion previa dio
lift 33x contra 6.7x de la extorsion (propuesta/09-validaciones.md seccion 2).
"""
import pandas as pd

from pipeline.features import BLOQUES
from pipeline.metricas import baseline_extorsion, baseline_violencia
from pipeline.modelo import entrenar, evaluar, evaluar_score, particionar

ACUMULATIVO = [["A"], ["A", "B"], ["A", "B", "C"], ["A", "B", "C", "D"],
               ["A", "B", "C", "D", "G"]]


def correr(features: pd.DataFrame, salida_csv: str = "reports/ablation.csv") -> pd.DataFrame:
    entrenamiento, prueba = particionar(features)
    filas = []

    for nombre, score in (("baseline_extorsion", baseline_extorsion(prueba)),
                          ("baseline_violencia", baseline_violencia(prueba))):
        filas.append({"modelo": nombre, "bloques": "-", **evaluar_score(prueba, score)})

    for combo in ACUMULATIVO:
        columnas = [c for bloque in combo for c in BLOQUES[bloque]]
        modelo = entrenar(entrenamiento, columnas)
        filas.append({"modelo": "hgb", "bloques": "+".join(combo),
                      **evaluar(modelo, prueba, columnas)})

    # dejar uno fuera, sobre el modelo completo
    completo = ["A", "B", "C", "D", "G"]
    for fuera in completo:
        combo = [b for b in completo if b != fuera]
        columnas = [c for bloque in combo for c in BLOQUES[bloque]]
        modelo = entrenar(entrenamiento, columnas)
        filas.append({"modelo": "hgb", "bloques": f"todo menos {fuera}",
                      **evaluar(modelo, prueba, columnas)})

    tabla = pd.DataFrame(filas)
    tabla.to_csv(salida_csv, index=False)
    return tabla
