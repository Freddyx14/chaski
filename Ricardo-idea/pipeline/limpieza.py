"""Carga el CSV de denuncias y devuelve solo los hechos con coordenada utilizable.

Dos filtros, los dos obligatorios (ver propuesta/09-validaciones.md):
  1. estado_coord = 'CON COORDENADA'.
  2. Fuera los puntos de volcado: coordenadas exactas que acumulan demasiados
     hechos. Son comisarias, no lugares de hechos. En Lima el peor concentra
     127,922 hechos.

La regla es mixta, porque un umbral absoluto solo captura los volcaderos de los
distritos grandes: un punto se descarta si supera UMBRAL_ABSOLUTO hechos, o si
tiene al menos PISO_RELATIVO hechos y representa mas de FRACCION_DISTRITO de los
hechos de su distrito. Una coordenada de 6 decimales son ~10 cm: ningun lugar
real concentra el 2% del delito de su distrito en 10 cm.
"""
import duckdb

VIOLENCIA = (
    "LESIONES POR PAF",
    "MUERTE POR ARMA DE FUEGO",
    "LESIONES POR PAF SEGUIDAS DE MUERTE",
    "DAÑOS",
)
UMBRAL_ABSOLUTO = 200
PISO_RELATIVO = 20
FRACCION_DISTRITO = 0.02
MAX_PASADAS = 8
DECIMALES = 5  # ~1.1 m; la misma rejilla con la que se verifica


def cargar_eventos(csv_path: str, con: duckdb.DuckDBPyConnection | None = None):
    con = con or duckdb.connect()
    con.execute(
        "create or replace view raw as "
        f"select * from read_csv_auto('{csv_path}', ignore_errors=true, sample_size=300000)"
    )
    con.execute(
        "create or replace table base as "
        f"select round(lat_hecho, {DECIMALES}) la, round(long_hecho, {DECIMALES}) lo,"
        "       distrito_hecho d "
        "from raw where lat_hecho is not null and estado_coord = 'CON COORDENADA'"
    )
    con.execute("create or replace table volcadero(la double, lo double)")
    # La regla relativa depende del total del distrito, y ese total cambia cuando
    # se saca un volcadero. Se itera hasta que no aparezcan puntos nuevos.
    for _ in range(MAX_PASADAS):
        nuevos = con.execute(
            "with vivos as ("
            "  select b.* from base b left join volcadero v"
            "    on b.la = v.la and b.lo = v.lo where v.la is null),"
            " tot as (select d, count(*) n from vivos group by 1),"
            " pts as (select la, lo, d, count(*) n from vivos group by 1, 2, 3)"
            " select p.la, p.lo from pts p join tot t on t.d = p.d"
            f" where p.n > {UMBRAL_ABSOLUTO}"
            f"    or (p.n >= {PISO_RELATIVO} and p.n > {FRACCION_DISTRITO} * t.n)"
        ).fetchall()
        if not nuevos:
            break
        con.executemany("insert into volcadero values (?, ?)", nuevos)
    viol = ", ".join(f"'{v}'" for v in VIOLENCIA)
    con.execute(
        "create or replace table eventos as select "
        "  cast(r.fecha_hora_hecho_iso_utc as timestamp) ts,"
        "  r.lat_hecho lat, r.long_hecho lon,"
        "  r.distrito_hecho distrito, r.subtipo_hecho subtipo, r.\"año_hecho\" anio,"
        "  case when r.subtipo_hecho ilike '%EXTORSION%'"
        "         or r.tipo_hecho ilike '%EXTORSION%' then 1 else 0 end es_ext,"
        f"  case when r.subtipo_hecho in ({viol}) then 1 else 0 end es_viol "
        "from raw r "
        "left join volcadero v "
        f"  on round(r.lat_hecho, {DECIMALES}) = v.la"
        f" and round(r.long_hecho, {DECIMALES}) = v.lo "
        "where v.la is null "
        "  and r.estado_coord = 'CON COORDENADA' "
        "  and r.lat_hecho is not null"
    )
    return con.table("eventos")


def escribir_parquet(csv_path: str, salida: str) -> dict:
    con = duckdb.connect()
    cargar_eventos(csv_path, con)
    con.execute(f"copy eventos to '{salida}' (format parquet)")
    n, ext, viol = con.execute(
        "select count(*), sum(es_ext), sum(es_viol) from eventos"
    ).fetchone()
    return {"eventos": n, "extorsion": ext, "violencia": viol}
