"""Panel corredor x semana con la etiqueta de escalamiento.

y_escala = 1 si en las 4 semanas SIGUIENTES hay al menos un hecho con arma de
fuego o danos en ese corredor. Se predice violencia y no extorsion porque la
extorsion se subregistra entre 75%% y 90%% (ver propuesta/05-estado-del-arte.md
seccion 7); un disparo o una fachada destrozada si quedan registrados.
"""
import pandas as pd

VENTANA_ETIQUETA = 4   # semanas hacia adelante que mira la etiqueta
BORDE = 4              # semanas que se cortan al final de cada ventana


def construir_panel(eventos: pd.DataFrame, corredores, inicio: str, fin: str) -> pd.DataFrame:
    eventos = eventos.copy()
    eventos["semana"] = (pd.to_datetime(eventos["ts"])
                         .dt.to_period("W-SUN").dt.start_time)
    agregado = (eventos.groupby(["corredor_id", "semana"])[["es_ext", "es_viol"]]
                .sum().rename(columns={"es_ext": "ext", "es_viol": "viol"}))

    semanas = pd.date_range(
        pd.Timestamp(inicio).to_period("W-SUN").start_time, pd.Timestamp(fin), freq="7D")
    ids = list(corredores["corredor_id"])
    indice = pd.MultiIndex.from_product([ids, semanas], names=["corredor_id", "semana"])

    panel = (agregado.reindex(indice, fill_value=0).reset_index()
             .sort_values(["corredor_id", "semana"]).reset_index(drop=True))

    # suma de violencia en las 4 semanas siguientes, sin incluir la actual
    # r(t) = suma de las ultimas 4 semanas incluida t  ->  r(t+4) = suma de t+1..t+4
    futuro = (panel.groupby("corredor_id")["viol"]
              .transform(lambda s: s.rolling(VENTANA_ETIQUETA, min_periods=1)
                         .sum().shift(-VENTANA_ETIQUETA)))
    panel["y_escala"] = (futuro.fillna(0) > 0).astype("int8")
    return panel


def recortar_borde(panel: pd.DataFrame, fin_ventana: str) -> pd.DataFrame:
    """Quita las ultimas semanas de una ventana.

    Dos razones: la etiqueta mira 4 semanas adelante y al borde las tomaria de la
    ventana siguiente, y el registro llega con retraso (9.3%% pasa de 30 dias).
    """
    corte = pd.Timestamp(fin_ventana) - pd.Timedelta(weeks=BORDE)
    return panel[panel["semana"] <= corte].copy()
