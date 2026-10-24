import duckdb
f="delitos_lima_metropolitana_completo_2018-25.csv"
con=duckdb.connect()
con.execute(f"create view raw as select * from read_csv_auto('{f}', ignore_errors=true, sample_size=300000)")
con.execute("""
create table ev0 as
select cast(fecha_hora_hecho_iso_utc as timestamp) ts, lat_hecho lat, long_hecho lon,
 distrito_hecho dist, subtipo_hecho sub, estado_coord ec, año_hecho anio,
 case when subtipo_hecho ilike '%EXTORSION%' or tipo_hecho ilike '%EXTORSION%' then 1 else 0 end es_ext,
 case when subtipo_hecho in ('LESIONES POR PAF','MUERTE POR ARMA DE FUEGO','DAÑOS','LESIONES POR PAF SEGUIDAS DE MUERTE') then 1 else 0 end es_viol
from raw
where distrito_hecho in ('SAN JUAN DE LURIGANCHO','COMAS','SAN MARTIN DE PORRES')
 and lat_hecho is not null and año_hecho between 2018 and 2025
""")
# coordenadas "volcadero": mas de 200 eventos en el mismo punto exacto
con.execute("""create table dump as
 select round(lat,6) la, round(lon,6) lo from ev0 group by 1,2 having count(*)>200""")
print("puntos volcadero:", con.execute("select count(*) from dump").fetchone()[0])
con.execute("""create table ev as select e.* from ev0 e
 left join dump d on round(e.lat,6)=d.la and round(e.lon,6)=d.lo
 where d.la is null and e.ec='CON COORDENADA'""")
tot,ext,viol=con.execute("select count(*),sum(es_ext),sum(es_viol) from ev").fetchone()
print(f"limpio: {tot} eventos | extorsion {ext} | violencia {viol}")
print("extorsion limpia por anio:", con.execute("select anio, sum(es_ext) from ev group by 1 order by 1").fetchall())
print("violencia limpia por anio:", con.execute("select anio, sum(es_viol) from ev group by 1 order by 1").fetchall())
print("extorsion limpia 2025 ene-jun:", con.execute("select sum(es_ext) from ev where anio=2025").fetchone()[0])
print("violencia limpia 2025 ene-jun:", con.execute("select sum(es_viol) from ev where anio=2025").fetchone()[0])
con.execute("""
create table panel as
with cell as (select round(lat,3) cy, round(lon,3) cx, date_trunc('week', ts) wk, sum(es_ext) ext, sum(es_viol) viol
 from ev group by 1,2,3),
grid as (select distinct cy,cx from cell), weeks as (select distinct wk from cell)
select g.cy,g.cx,w.wk, coalesce(c.ext,0) ext, coalesce(c.viol,0) viol
from grid g cross join weeks w left join cell c on c.cy=g.cy and c.cx=g.cx and c.wk=w.wk""")
print("celdas:", con.execute("select count(distinct (cy,cx)) from panel").fetchone()[0], "| filas panel:", con.execute("select count(*) from panel").fetchone()[0])
r=con.execute("""
with f as (select *,
  sum(ext) over (partition by cy,cx order by wk rows between 3 preceding and current row) ext_4,
  sum(viol) over (partition by cy,cx order by wk rows between 3 preceding and current row) viol_4,
  sum(viol) over (partition by cy,cx order by wk rows between 1 following and 4 following) viol_fut
 from panel)
select avg(case when viol_fut>0 then 1.0 else 0 end),
 avg(case when ext_4>0 and viol_fut>0 then 1.0 else 0 end)/nullif(avg(case when ext_4>0 then 1.0 else 0 end),0),
 sum(case when ext_4>0 then 1 else 0 end),
 avg(case when viol_4>0 and viol_fut>0 then 1.0 else 0 end)/nullif(avg(case when viol_4>0 then 1.0 else 0 end),0)
from f where viol_fut is not null""").fetchone()
print(f"\nP(viol 4sem) base            = {r[0]:.5f}")
print(f"P(viol | extorsion ult 4sem) = {r[1]:.5f}  lift {r[1]/r[0]:.1f}x   (n celdas-semana con ext = {r[2]})")
print(f"P(viol | violencia ult 4sem) = {r[3]:.5f}  lift {r[3]/r[0]:.1f}x   <-- baseline a vencer")
