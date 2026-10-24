import pandas as pd
from pipeline.limpieza import cargar_eventos

CABECERA = ("estado_coord,lat_hecho,long_hecho,fecha_hora_hecho_iso_utc,"
            "año_hecho,distrito_hecho,tipo_hecho,subtipo_hecho")


def _escribir_csv(tmp_path, filas):
    csv = tmp_path / "muestra.csv"
    csv.write_text("\n".join([CABECERA] + filas), encoding="utf-8")
    return str(csv)


def test_excluye_puntos_de_volcado(tmp_path):
    filas = [
        f"CON COORDENADA,-12.0,-77.0,2022-03-0{i % 9 + 1}T10:00:00+00:00,2022,"
        "SAN JUAN DE LURIGANCHO,PATRIMONIO (DELITO),HURTO"
        for i in range(250)
    ]
    filas += [
        f"CON COORDENADA,-12.00{i},-77.01{i},2022-03-01T10:00:00+00:00,2022,"
        "SAN JUAN DE LURIGANCHO,LIBERTAD (DELITO),EXTORSION"
        for i in range(1, 4)
    ]
    filas += ["SIN COORDENADA,-12.5,-77.5,2022-03-01T10:00:00+00:00,2022,"
              "COMAS,PATRIMONIO (DELITO),HURTO"]
    df = cargar_eventos(_escribir_csv(tmp_path, filas)).df()
    assert len(df) == 3
    assert df["es_ext"].sum() == 3


def test_marca_violencia_armada(tmp_path):
    filas = [
        "CON COORDENADA,-12.001,-77.011,2022-03-01T10:00:00+00:00,2022,COMAS,"
        '"VIDA, EL CUERPO Y LA SALUD (DELITO)",LESIONES POR PAF',
        "CON COORDENADA,-12.002,-77.012,2022-03-01T10:00:00+00:00,2022,COMAS,"
        "PATRIMONIO (DELITO),HURTO",
    ]
    df = cargar_eventos(_escribir_csv(tmp_path, filas)).df()
    assert df["es_viol"].sum() == 1
    assert df["es_ext"].sum() == 0


def test_ningun_punto_concentra_mas_del_2pct_de_su_distrito():
    """Foco de revision 4: el umbral global de 200 puede dejar pasar volcaderos
    chicos, por ejemplo una comisaria de distrito con 150 hechos."""
    import pathlib
    import pytest

    parquet = pathlib.Path("data/eventos_limpios.parquet")
    if not parquet.exists():
        pytest.skip("falta data/eventos_limpios.parquet")
    from pipeline.limpieza import PISO_RELATIVO

    df = pd.read_parquet(parquet, columns=["distrito", "lat", "lon"])
    por_distrito = df.groupby("distrito").size()
    conteo = df.groupby(["distrito", df["lat"].round(5), df["lon"].round(5)]).size()
    limite = conteo.index.get_level_values(0).map(por_distrito) * 0.02
    peores = conteo[(conteo.values > limite.values) & (conteo.values >= PISO_RELATIVO)]
    assert peores.empty, f"puntos sospechosos:\n{peores.sort_values(ascending=False).head()}"
