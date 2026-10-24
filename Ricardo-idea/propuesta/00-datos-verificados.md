# Datos verificados — `delitos_lima_metropolitana_completo_2018-25.csv`

> Verificado el viernes 23 de octubre de 2026 en la máquina de Ricardo, con DuckDB sobre el CSV completo.
> Todo lo que está en este archivo salió de una consulta, no de una fuente secundaria.
> Lo que no se verificó está marcado **(por confirmar)**.

## Cómo reproducir

No hay `duckdb` ni `polars` instalados en el Python del sistema (Homebrew 3.14.7, PEP 668 bloquea `pip install`).
Se usa `uv`, que crea el entorno al vuelo y no ensucia nada:

```bash
cd "~/Documents/CAL HACKS/cal-hacks/Ricardo-idea"
uv run --with duckdb --with pytz python tu_script.py
```

`pytz` hace falta porque la columna `fecha_hora_hecho_iso_utc` trae zona horaria y DuckDB la convierte con esa librería.
Si se consulta esa columna sin `pytz`, falla con:

```
Invalid Input Error: Required module 'pytz' failed to import
```

Vista base usada en todas las consultas:

```sql
CREATE VIEW d AS
SELECT * FROM read_csv_auto('delitos_lima_metropolitana_completo_2018-25.csv',
                            ignore_errors=true, sample_size=300000);
```

## Tamaño y cobertura

| Hecho | Valor |
|---|---|
| Filas | 3,137,221 (más la cabecera) |
| Peso | 1.82 GB |
| Rango de fechas del hecho | 2018-01-01 a **2025-06-30** |
| Columnas | 58 |
| Archivo reducido | `basico_lima.csv`, 180 MB, solo `fecha_hora_hecho`, `año_hecho`, `lat_hecho`, `long_hecho` |

**El corte en 2025-06-30 es el dato más importante del pitch.** El año 2025 del dataset es medio año,
así que cualquier comparación contra 2024 tiene que anualizarse o decirse como "primer semestre".

## Extorsión por año

Filtro: `subtipo_hecho ILIKE '%EXTORSION%' OR tipo_hecho ILIKE '%EXTORSION%'`.

| Año | Denuncias | Con coordenada |
|---|---|---|
| 2018 | 588 | 588 |
| 2019 | 754 | 754 |
| 2020 | 727 | 727 |
| 2021 | 1,336 | 1,336 |
| 2022 | 7,525 | 7,525 |
| 2023 | 10,136 | 10,136 |
| 2024 | 8,118 | 8,118 |
| 2025 (ene–jun) | 5,755 | 5,755 |

Hay además 24 registros sueltos con `año_hecho` entre 1990 y 2017, que son errores de captura o hechos
denunciados años después. Se descartan.

**Dos lecturas, las dos verdaderas:**

- 2018 → 2023: de 588 a 10,136, **17 veces más**.
- 2025 va a ritmo de ~11,500 al año (5,755 en seis meses), **+42% sobre 2024**. Es el peor año registrado
  y va a la mitad.

**El 100% de las denuncias de extorsión tiene `lat_hecho` y `long_hecho`.** No hay que geocodificar nada.

## Distritos con más extorsión (2018–2025 jun)

| Distrito | Denuncias |
|---|---|
| San Juan de Lurigancho | 4,304 |
| Lima (Cercado) | 4,019 |
| Comas | 2,260 |
| San Martín de Porres | 1,843 |
| Ate | 1,704 |
| Los Olivos | 1,655 |
| Villa El Salvador | 1,598 |
| Chorrillos | 1,268 |
| San Juan de Miraflores | 1,230 |
| Villa María del Triunfo | 1,221 |

Los tres distritos del prototipo (SJL + Comas + SMP) suman **8,407 denuncias de extorsión**.

Serie de San Juan de Lurigancho: 60 (2018) · 64 (2019) · 64 (2020) · 123 (2021) · 787 (2022) ·
1,226 (2023) · 1,177 (2024) · **803 en seis meses de 2025**.

## Modalidades de extorsión

| Modalidad | Denuncias |
|---|---|
| EXTORSION | 30,194 |
| EXTORSION AGRAVADA | 4,090 |
| CHANTAJE | 648 |
| CUPOS LABORALES | 18 |
| POR PROTECCION O SEGURO | 6 |
| TRANQUILIDAD LABORAL | 4 |
| VIGILANCIA PARTICULAR | 2 |
| RESCATE DE VEHICULO ROBADO Y/O HURTADO | 1 |

**"Cupos laborales": 18 registros en siete años y medio.** El cobro de cupo a obras, bodegas y transporte
—lo que cualquiera en Lima describe como la forma dominante del delito— casi no existe en el registro
oficial. La cifra negra no es un defecto del proyecto: es parte de lo que el producto tiene que decir en
voz alta.

## Etiqueta de escalamiento a violencia

Subtipos disponibles para marcar que un corredor pasó de amenaza a violencia:

| Subtipo | Registros |
|---|---|
| LESIONES | 80,372 |
| HOMICIDIO | 12,146 |
| DAÑOS | 6,444 |
| LESIONES POR PAF | 2,613 |
| MUERTE POR ARMA DE FUEGO | 557 |
| MUERTE POR ARMA DE FUEGO POR INTERVENCION POLICIAL | 421 |
| HALLAZGO DE ARMAMENTO | 252 |
| LESIONES POR PAF SEGUIDAS DE MUERTE | 187 |

PAF es "proyectil de arma de fuego". `LESIONES POR PAF` + `MUERTE POR ARMA DE FUEGO` + `DAÑOS` es la firma
del cobro de cupo: la balacera o el ataque a la fachada del negocio que no pagó. Esa es la variable que el
modelo predice.

## Volumen general por tipo de hecho

| Tipo | Registros |
|---|---|
| PATRIMONIO (DELITO) | 1,011,604 |
| LEY DE VIOLENCIA CONTRA LA MUJER Y GRUPOS VULNERABLES | 752,584 |
| INTERVENCION POLICIALES | 719,986 |
| FALTAS | 189,432 |
| SEGURIDAD PUBLICA (DELITO) | 108,902 |
| LIBERTAD (DELITO) | 100,207 |
| VIDA, EL CUERPO Y LA SALUD (DELITO) | 94,353 |
| LEY 30096 DELITOS INFORMATICOS | 83,944 |

Conteos aproximados por palabra clave sobre la línea completa (no por campo exacto, así que pueden
sobrecontar): HURTO ~602,023 · ROBO ~345,801 · DROGA/MICROCOMERCIALIZACION ~95,322 · SICARIATO 70.

## Columnas inútiles

- `tipologias_ia`: vacía en 3,137,220 de 3,137,221 filas. Ignorar.
- `barrio`, `comisaria`, `departamento`, `provincia`, `distrito`, `indice_priorizacion`,
  `fecha_inaguracion`: vacías en las filas inspeccionadas **(por confirmar en el conteo completo)**.
  Usar las versiones `_hecho`, que sí vienen llenas.

## Columnas que sí se usan

`fecha_hora_hecho_iso_utc`, `año_hecho`, `lat_hecho`, `long_hecho`, `distrito_hecho`, `ubigeo_hecho_delito`,
`turno_hecho` (mañana/tarde/noche/madrugada), `tipo_hecho`, `subtipo_hecho`, `modalidad_hecho`,
`comisaria_hecho`, `fecha_hora_registro_hecho_iso_utc` (sirve para medir el retraso de registro),
`estado_coord` (marca si la coordenada es válida).

## Advertencia sobre la coordenada

> **Actualizado tras las validaciones del 23 de octubre.** El problema es más grave de lo que decía este
> párrafo: el 64% de las denuncias de extorsión de SJL, Comas y SMP cae en 20 coordenadas repetidas, y la
> más repetida concentra 127,922 hechos de todo tipo. Son puntos de volcado, no lugares de hechos. Y la
> fracción de denuncias con coordenada usable cae de 48.5% en 2018 a **3.2% en 2025**. Ver
> `../propuesta/09-validaciones.md` antes de usar cualquier cifra geográfica de este archivo.


`lat_hecho`/`long_hecho` vienen de geocodificar la dirección que tomó la comisaría, no de un GPS en el
lugar del hecho. El error es de decenas de metros y puede caer en la cuadra equivocada. Por eso la unidad
de análisis del proyecto es el **corredor** (una cadena de cuadras de la misma vía), no la cuadra suelta.
