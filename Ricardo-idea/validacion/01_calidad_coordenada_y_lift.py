import duckdb
f="delitos_lima_metropolitana_completo_2018-25.csv"
con=duckdb.connect()
con.execute(f"""create view raw as select * from read_csv_auto('{f}', ignore_errors=true, sample_size=300000)""")
con.execute("""
create table ev as
select
  cast(fecha_hora_hecho_iso_utc as timestamp) ts,
  cast(fecha_hora_registro_hecho_iso_utc as timestamp) ts_reg,
  lat_hecho lat, long_hecho lon, distrito_hecho dist, subtipo_hecho sub, modalidad_hecho moda, estado_coord ec,
  case when subtipo_hecho ilike '%EXTORSION%' or tipo_hecho ilike '%EXTORSION%' then 1 else 0 end es_ext,
  case when subtipo_hecho in ('LESIONES POR PAF','MUERTE POR ARMA DE FUEGO','DAÑOS','LESIONES POR PAF SEGUIDAS DE MUERTE') then 1 else 0 end es_viol
from raw
where distrito_hecho in ('SAN JUAN DE LURIGANCHO','COMAS','SAN MARTIN DE PORRES')
  and lat_hecho is not null and año_hecho between 2018 and 2025
""")
print("eventos 3 distritos:", con.execute("select count(*), sum(es_ext), sum(es_viol) from ev").fetchall())

print("\n== A. calidad de coordenada ==")
print("estado_coord:", con.execute("select ec, count(*) from ev group by 1 order by 2 desc limit 5").fetchall())
print("coords exactas mas repetidas (todas):", con.execute("""
 select round(lat,6) la, round(lon,6) lo, count(*) n from ev group by 1,2 order by n desc limit 5""").fetchall())
print("coords repetidas en EXTORSION:", con.execute("""
 select round(lat,6) la, round(lon,6) lo, count(*) n from ev where es_ext=1 group by 1,2 order by n desc limit 5""").fetchall())
tot=con.execute("select count(*) from ev where es_ext=1").fetchone()[0]
top=con.execute("select sum(n) from (select count(*) n from ev where es_ext=1 group by round(lat,6),round(lon,6) order by n desc limit 20)").fetchone()[0]
print(f"extorsion en las 20 coordenadas mas repetidas: {top} de {tot} = {100*top/tot:.1f}%")

print("\n== B. retraso de registro (dias) ==")
print(con.execute("""select median(date_diff('day',ts,ts_reg)) mediana,
 quantile_cont(date_diff('day',ts,ts_reg),0.9) p90,
 avg(case when date_diff('day',ts,ts_reg)>30 then 1.0 else 0 end) frac_mas_30d
 from ev where es_ext=1 and ts_reg is not null""").fetchall())

print("\n== C. KILL SWITCH: extorsion predice violencia? ==")
con.execute("""
create table panel as
with cell as (
  select round(lat,3) cy, round(lon,3) cx, date_trunc('week', ts) wk, sum(es_ext) ext, sum(es_viol) viol
  from ev group by 1,2,3
), grid as (
  select distinct cy,cx from cell
), weeks as (
  select distinct wk from cell
)
select g.cy,g.cx,w.wk, coalesce(c.ext,0) ext, coalesce(c.viol,0) viol
from grid g cross join weeks w left join cell c on c.cy=g.cy and c.cx=g.cx and c.wk=w.wk
""")
print("celdas x semanas:", con.execute("select count(*) from panel").fetchone())
r=con.execute("""
with f as (
 select *,
  sum(ext) over (partition by cy,cx order by wk rows between 3 preceding and current row) ext_4,
  sum(viol) over (partition by cy,cx order by wk rows between 1 following and 4 following) viol_fut
 from panel
)
select
 avg(case when viol_fut>0 then 1.0 else 0 end) base,
 avg(case when ext_4>0 and viol_fut>0 then 1.0 else 0 end)/nullif(avg(case when ext_4>0 then 1.0 else 0 end),0) p_dado_ext,
 sum(case when ext_4>0 then 1 else 0 end) n_con_ext
from f where viol_fut is not null
""").fetchone()
base,pext,n=r
print(f"P(violencia en 4 sem) base = {base:.4f}")
print(f"P(violencia en 4 sem | extorsion en ult 4 sem) = {pext:.4f}   (n={n})")
print(f"LIFT = {pext/base:.2f}x")
