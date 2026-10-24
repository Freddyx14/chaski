# Validaciones: lo que la data aguanta y lo que no

> Corrido el viernes 23 de octubre de 2026, antes de escribir una línea de prototipo.
> Scripts reproducibles en `../validacion/`. Se ejecutan con
> `uv run --with duckdb --with pytz python validacion/0X_*.py` desde `Ricardo-idea/`.

## Resumen: dos hallazgos que cambian el plan

1. **La coordenada del 64% de las denuncias de extorsión no es el lugar del hecho.** Es un punto de
   volcado, casi seguro la comisaría. Hay que filtrarlo, y al filtrarlo el dataset usable se reduce mucho.
2. **La precisión geográfica del registro se derrumba con los años, justo cuando el delito explota.**
   En 2018 el 48.5% de las denuncias de extorsión tenía coordenada de calle usable. En 2025 es el **3.2%**.
   Eso **invalida la partición de prueba que habíamos elegido** (2025-01 a 2025-06).

Ninguno de los dos mata el proyecto. Los dos lo habrían hecho explotar el sábado a las tres de la tarde.

## Validación 1 · Calidad de la coordenada

`validacion/01_calidad_coordenada_y_lift.py`, sobre SJL + Comas + SMP (683,710 hechos).

| Resultado | Valor |
|---|---|
| `estado_coord = 'CON COORDENADA'` | 383,971 de 683,710 (**56%**) |
| Hechos en la coordenada más repetida | **127,922 en un solo punto** (-11.939356, -76.999332) |
| Segunda coordenada más repetida | 90,982 hechos |
| Extorsión concentrada en las 20 coordenadas más repetidas | **5,386 de 8,402 = 64.1%** |

**Interpretación.** Cuando la comisaría no geocodifica la dirección del hecho, el registro hereda un punto
por defecto. Un análisis por corredor que no filtre esto produciría "corredores de extorsión" que en
realidad son la puerta de una comisaría. Es el error que habría arruinado el mapa entero.

**Filtro adoptado:** se excluye todo punto exacto con más de 200 hechos (653 puntos en toda Lima) y se
exige `estado_coord = 'CON COORDENADA'`.

## Validación 2 · ¿La extorsión anticipa la violencia armada?

Esta era la pregunta que, si salía mal, obligaba a cambiar de objetivo. `validacion/02_lift_sin_volcadero.py`,
celdas de ~110 m, ventana de 4 semanas, tres distritos, datos ya limpios.

| Condición | P(violencia en las próximas 4 semanas) | Lift |
|---|---|---|
| Base (cualquier celda-semana) | 0.00103 | 1.0× |
| **Hubo extorsión en las últimas 4 semanas** | **0.00690** | **6.7×** |
| Hubo violencia armada en las últimas 4 semanas | 0.03412 | **33.0×** |

**Lo bueno:** la señal existe. Una denuncia de extorsión multiplica por 6.7 la probabilidad de un hecho
con arma de fuego o daños cerca y pronto. No es ruido.

**Lo incómodo, y hay que decirlo:** la violencia previa predice mucho mejor (33×) que la extorsión previa
(6.7×). Esto significa dos cosas:

1. **El baseline a vencer no es "dónde hubo extorsión" sino "dónde hubo violencia".** Hay que cambiar el
   baseline del ablation (`07-ablation.md`), porque el que habíamos escrito era demasiado fácil de ganar.
2. El aporte real del modelo es **lo que la extorsión agrega por encima de la persistencia de la
   violencia**. Esa es la pregunta del ablation, y ahora tiene una cifra de referencia.

Sin el filtro del volcadero este mismo cálculo daba 48.5×, un número precioso y falso. Queda como
advertencia.

## Validación 3 · ¿Alcanza la muestra? No, no como estaba planeada

`validacion/03_cobertura_toda_lima.py`, toda Lima Metropolitana.

**Denuncias de extorsión que sobreviven la limpieza, por año:**

| Año | Todas | Con coordenada usable | % |
|---|---|---|---|
| 2018 | 588 | 285 | 48.5% |
| 2019 | 754 | 276 | 36.6% |
| 2020 | 727 | 207 | 28.5% |
| 2021 | 1,336 | 462 | 34.6% |
| 2022 | 7,525 | 2,814 | 37.4% |
| 2023 | 10,136 | 3,103 | 30.6% |
| 2024 | 8,118 | 1,374 | 16.9% |
| **2025 (ene–jun)** | **5,755** | **182** | **3.2%** |

Violencia armada limpia, misma serie: 1,099 (2018) · 660 (2023) · 438 (2024) · **94 (2025 ene–jun)**.

En los tres distritos del prototipo quedaban **29 extorsiones y 9 hechos violentos** en todo el primer
semestre de 2025. **Con 9 positivos no se evalúa nada.**

### Las tres decisiones que salen de aquí

1. **La ventana de prueba se mueve a 2023.** Entrenar con 2018–2022, probar con 2023 (3,103 extorsiones y
   660 hechos violentos limpios). Es una partición temporal honesta sobre datos que existen.
2. **El prototipo cubre toda Lima Metropolitana, no tres distritos.** Tres distritos no dan muestra
   suficiente después de limpiar. El mapa del demo puede seguir centrado en SJL.
3. **El derrumbe del geocodificado es, él mismo, un hallazgo del proyecto.** En 2025 solo 3 de cada 100
   denuncias de extorsión en Lima tienen una coordenada utilizable. Es verificable, es nuestro, y encaja
   con que las cifras oficiales se contradigan en público (`05-estado-del-arte.md` §10). **Va en el
   pitch.**

## Validación 4 · Retraso de registro

Mediana de 1 día entre el hecho y su registro; percentil 90 de 27 días; **9.3% se registra más de 30 días
después**.

Dos consecuencias:

- Un sistema que lea el registro oficial en vivo sería razonablemente oportuno para la mayoría de casos.
- Las últimas 4 semanas de cualquier corte están **truncadas por la derecha**: faltan hechos que todavía no
  se registran. Al evaluar, se descartan las últimas 4 semanas de la ventana.

## Lo que todavía falta validar antes del prototipo

Ordenado por lo que más puede romper el plan. Nada de esto toma más de una hora.

| # | Qué | Criterio de aprobación | Si falla |
|---|---|---|---|
| 1 | **Construcción del grafo**: `osmnx` sobre Lima Metropolitana, agrupar aristas en corredores | El grafo baja y se procesa en < 20 min; la mediana de largo de corredor cae entre 200 y 900 m | Limitar a Lima Norte y Este, o usar una malla hexagonal (H3) en vez del grafo |
| 2 | **Snap al corredor**: distancia de cada hecho limpio a su corredor más cercano | ≥ 80% de los hechos a menos de 80 m | Subir el umbral y declararlo, o agregar por malla |
| 3 | **Densidad del panel**: positivos por corredor-semana con la ventana 2023 | ≥ 300 corredores-semana positivos en la ventana de prueba | Pasar a corredor-mes, o ventana de 8 semanas en vez de 4 |
| 4 | **Lift en el grafo, no en la malla**: repetir la validación 2 con corredores y vecinos de 1 salto | Lift de extorsión > 3× sobre el baseline de violencia | El contagio no vive en la topología vial; volver a distancia euclidiana |
| 5 | **Denominador**: POIs comerciales de OSM por corredor | < 50% de corredores con cero POIs | Usar el padrón RUC de SUNAT, o normalizar por longitud de vía |
| 6 | **Padrón RUC de SUNAT**: que exista, se descargue y traiga dirección con ubigeo | Se puede filtrar Lima y geocodificar una muestra | Queda OSM como piso y se declara |
| 7 | **`torch_geometric`** instalado en el Mac | Importa y corre un ejemplo mínimo | El GNN sale del plan; gradient boosting es el modelo |

Las dos primeras son las que hay que correr esta noche, porque definen si la unidad de análisis es el
corredor o hay que caer a una malla.

## Lo que se le puede preguntar a Germain García-Zanabria

Ricardo investiga con él, y CriPAV (`05-estado-del-arte.md` §4.b) ataca exactamente el problema de series
dispersas a nivel de calle. Preguntas concretas, por orden de utilidad:

1. **El mecanismo estocástico de CriPAV**, ¿aguanta una serie con 0 a 3 eventos por corredor-año, como la
   nuestra, o necesita la densidad de São Paulo?
2. **¿Cómo trataron la calidad del geocodificado en los datos de la SSP de São Paulo?** Casi con seguridad
   tuvieron el mismo problema del punto de volcado, y su solución nos ahorra horas.
3. **¿Qué unidad usaron exactamente**: segmento de calle, calle completa, o intersecciones?
4. ¿Hay algo publicado sobre **extorsión** en su línea, o es territorio abierto como parece?

**Aviso sobre las reglas del hackathon:** todo el código se escribe durante el evento. El método publicado
se cita y se reimplementa; **código privado previo no se puede traer**. Conviene preguntarle por el método
y por la experiencia con los datos, no pedirle un repositorio.
