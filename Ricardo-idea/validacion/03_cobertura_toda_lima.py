import duckdb
f="delitos_lima_metropolitana_completo_2018-25.csv"
con=duckdb.connect()
con.execute(f"create view raw as select * from read_csv_auto('{f}', ignore_errors=true, sample_size=300000)")
con.execute("""create table ev0 as
select cast(fecha_hora_hecho_iso_utc as timestamp) ts, lat_hecho lat, long_hecho lon, año_hecho anio,
 distrito_hecho dist, estado_coord ec,
 case when subtipo_hecho ilike '%EXTORSION%' or tipo_hecho ilike '%EXTORSION%' then 1 else 0 end es_ext,
 case when subtipo_hecho in ('LESIONES POR PAF','MUERTE POR ARMA DE FUEGO','DAÑOS','LESIONES POR PAF SEGUIDAS DE MUERTE') then 1 else 0 end es_viol
from raw where lat_hecho is not null and año_hecho between 2018 and 2025""")
con.execute("create table dump as select round(lat,6) la, round(lon,6) lo from ev0 group by 1,2 having count(*)>200")
con.execute("""create table ev as select e.* from ev0 e left join dump d on round(e.lat,6)=d.la and round(e.lon,6)=d.lo
 where d.la is null and e.ec='CON COORDENADA'""")
print("TODA LIMA, limpio")
print(" ec CON COORDENADA total:", con.execute("select count(*) from ev0 where ec='CON COORDENADA'").fetchone()[0])
print(" puntos volcadero:", con.execute("select count(*) from dump").fetchone()[0])
print(" eventos limpios:", con.execute("select count(*) from ev").fetchone()[0])
print(" extorsion limpia por anio:", con.execute("select anio,sum(es_ext) from ev group by 1 order by 1").fetchall())
print(" violencia limpia por anio:", con.execute("select anio,sum(es_viol) from ev group by 1 order by 1").fetchall())
print("\n fraccion de extorsion que sobrevive la limpieza, por anio:")
print(con.execute("""select a.anio, a.n_todas, coalesce(b.n_limpias,0) n_limpias,
 round(100.0*coalesce(b.n_limpias,0)/a.n_todas,1) pct
 from (select anio, sum(es_ext) n_todas from ev0 group by 1) a
 left join (select anio, sum(es_ext) n_limpias from ev group by 1) b on a.anio=b.anio
 where a.n_todas>0 order by a.anio""").fetchall())
