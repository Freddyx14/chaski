# Diseño técnico

> Depende de los números de `00-datos-verificados.md` y del producto descrito en `01-propuesta.md`.

## Resumen en una línea

Tabla **corredor × semana** construida sobre el grafo vial de OSM, con la difusión a vecinos del grafo
como variable, para predecir **escalamiento a violencia armada en las próximas 4 semanas**, evaluado
contra un holdout temporal real (enero–junio de 2025) y explicado con SHAP.

## 1 · Unidad de análisis: el corredor

Las coordenadas de la PNP vienen de geocodificar la dirección que escribió la comisaría. El error es de
decenas de metros y puede caer en la cuadra de al lado. Una unidad del tamaño de una cuadra heredaría todo
ese ruido; un distrito borra el fenómeno.

**Corredor = cadena de aristas de OSM de la misma vía, entre dos intersecciones importantes.** Largo típico
de 300 a 800 metros. Absorbe el error de geocodificación y sigue siendo la escala a la que una banda cobra.

Construcción:

1. Descargar el grafo vial de **toda Lima Metropolitana** con `osmnx` (`network_type='drive'`).
   Tres distritos parecían suficientes con 8,407 extorsiones, pero tras el filtro de coordenada quedan
   2,414 en siete años y 29 en el primer semestre de 2025. Toda Lima deja 8,703 extorsiones limpias, de
   las cuales 3,103 caen en la ventana de prueba de 2023 (`09-validaciones.md` §3). El mapa del demo sigue
   centrado en San Juan de Lurigancho.
2. Agrupar aristas consecutivas con el mismo `name` y sin intersección de grado ≥ 4 en medio.
3. Cada corredor guarda: `corredor_id`, geometría, longitud, `highway` (jerarquía de la vía), grado de
   conexión, vecinos a 1 y 2 saltos.

Snap de incidentes: punto a la arista más cercana. Se descarta por encima de 80 metros y se cuenta cuántos
se descartan (va en el README como medida de calidad).

## 1.1 · Qué se puede afirmar de un corredor

Nunca observamos el cobro. Observamos **denuncias registradas de extorsión**, con un subregistro enorme:
`CUPOS LABORALES` aparece 18 veces en siete años y medio. Por eso ninguna etiqueta del sistema afirma que
en un tramo se cobra cupo. Las etiquetas describen la evidencia, no el hecho.

| Etiqueta | Regla |
|---|---|
| Sin señal | 0 denuncias de extorsión en las últimas 12 semanas |
| Señal reciente | ≥1 denuncia en las últimas 12 semanas |
| Señal sostenida | denuncias en ≥3 de las últimas 12 semanas **y** `tasa_100neg` en el decil superior de los corredores del distrito |
| Con antecedente violento | además, ≥1 hecho `LESIONES POR PAF`, `MUERTE POR ARMA DE FUEGO` o `DAÑOS` en el corredor en 26 semanas |

**Los umbrales (3 de 12 semanas, decil superior) son provisionales.** Salen del percentil empírico una vez
construidos los corredores, y hoy no sabemos cuántos corredores hay ni cómo se distribuyen las denuncias
entre ellos. Se fijan el sábado con la distribución real y se escriben en el README con el valor usado.

La etiqueta del corredor es descriptiva y mira al pasado. La predicción de escalamiento (§2, `y_escala`)
es lo que mira al futuro. Son dos cosas distintas y la respuesta al usuario las separa:

- descriptivo: "en este tramo hubo denuncias de extorsión en 5 de las últimas 12 semanas";
- predictivo: "el modelo estima 31% de probabilidad de un hecho con arma de fuego o daños en las próximas
  4 semanas, y es el percentil 94 del distrito";
- aviso obligatorio en ambos casos: "la ausencia de denuncias no significa ausencia de cobro".

En el JSON (§6) la etiqueta viaja como `senal` con valores `sin_senal`, `reciente`, `sostenida`, y el
antecedente violento como booleano aparte. **No existe ningún campo llamado `cobro_activo`.**

## 2 · Tabla base

| Columna | Qué es |
|---|---|
| `corredor_id`, `semana` | Clave. 2018-01 a 2025-06, 390 semanas |
| `ext_t` | Denuncias de extorsión en el corredor esa semana |
| `ext_lag_1,2,4,8,12` | Lags propios |
| `ext_vec1_lag_1,2,4` | Suma de extorsión en vecinos a 1 salto |
| `ext_vec2_lag_1,2,4` | Lo mismo a 2 saltos |
| `viol_lag_4,12` | Violencia armada previa en el corredor |
| `patrimonio_lag_4` | Robo y hurto como fondo de criminalidad general |
| `negocios_exp` | Negocios expuestos estimados (sección 4) |
| `tasa_100neg` | `ext_t / negocios_exp * 100` |
| `grado`, `jerarquia_via`, `long_m` | Estructura del corredor |
| `semana_del_año`, `tendencia` | Estacionalidad y deriva |
| **`y_escala`** | **1 si hay ≥1 hecho de `LESIONES POR PAF`, `MUERTE POR ARMA DE FUEGO` o `DAÑOS` en el corredor en las 4 semanas siguientes** |

La clase positiva va a ser rara. Se reporta la prevalencia real en el holdout y se usa AUC-PR, nunca
accuracy.

## 3 · Modelos

**Base (obligatorio, sábado mañana).** Gradient boosting sobre la tabla. Corre en minutos, da SHAP directo
y es el plan que garantiza que haya demo.

**Grafo (si el sábado rinde).** GNN temporal con `torch_geometric`: nodos = corredores, aristas =
adyacencia vial, señal = la serie semanal. Aquí la difusión deja de ser una feature calculada a mano y la
aprende el modelo. Se compara contra la base con la misma partición. Si no gana, se dice que no ganó.

**Stretch (sábado noche, solo si todo lo demás está cerrado).** Hawkes multivariado sobre el grafo, con
excitación cruzada extorsión → violencia. Es el modelo correcto para el fenómeno (auto-excitante y
contagioso por adyacencia), pero ajustarlo bien no cabe en el tiempo. No se empieza por aquí.

**Corredores análogos.** Embedding de la serie de cada corredor (la representación de la GNN, o features
de forma si no hay GNN) y vecinos por coseno. Produce la frase: "tu corredor hoy se parece a cómo estaba
la Av. X ocho meses antes de su pico". Es la idea original de Ricardo —comparar subgrafos con
comportamiento parecido— con un uso concreto.

## 4 · Denominador: negocios expuestos

Sin denominador, 12 denuncias en un corredor de 40 bodegas se ven igual que 12 en uno de 400.
Ningún registro público da bodegas por cuadra, así que se estima:

1. **POIs comerciales de OSM** dentro de un buffer de 30 m del corredor: `shop`, `amenity=restaurant`,
   `commercial`. Es el piso, porque OSM subregistra la bodega de barrio.
2. **Footprints de Google Open Buildings** dentro del buffer, como medida de densidad construida
   **(por confirmar: cobertura y calidad en Lima)**.
3. **VIIRS nocturno** (mensual, 500 m, gratis) como proxy de actividad comercial. La resolución es más
   gruesa que un corredor, así que entra como variable de contexto, no como conteo. **Esto hay que decirlo
   en el pitch, no esconderlo.**

El denominador se calcula una vez, no por semana. Si falta tiempo, se usa solo (1) y se declara la
limitación.

## 5 · Evaluación

- **Partición temporal estricta:** entrenamiento 2018-01 a 2022-12, **prueba 2023-01-01 a 2023-12-31**.
  Nada de mezclar semanas al azar: eso filtra el futuro y infla todo.
  **La ventana de prueba cambió** de 2025 a 2023 porque en 2025 solo el 3.2% de las denuncias de extorsión
  tiene coordenada usable: quedaban 9 hechos violentos en los tres distritos, y con 9 positivos no se
  evalúa nada (`09-validaciones.md` §3).
- **Se descartan las últimas 4 semanas de cualquier ventana**, porque el registro llega con retraso
  (mediana 1 día, pero 9.3% pasa de 30 días) y esos datos están truncados por la derecha.
- **Filtro de coordenada obligatorio antes de todo:** `estado_coord = 'CON COORDENADA'` y excluir los 653
  puntos exactos con más de 200 hechos. Sin ese filtro el mapa muestra comisarías, no corredores.
- **Métricas:** AUC-PR, y sobre todo **recall en el top-k**: de los k corredores que el modelo marca como
  de mayor riesgo, cuántos efectivamente tuvieron un hecho armado. Es lo que le importa a alguien que
  decide a quién avisar.
- **Baseline a vencer:** "los corredores con más extorsión el mes pasado". Si el modelo no le gana a eso,
  el modelo no sirve y se dice.
- **SHAP por corredor** para las tres razones que Claude traduce a lenguaje humano.

## 6 · Contrato entre Ricardo y Freddy

Se cierra antes de escribir código. Un `GET /corredor?lat=&lon=` devuelve:

```json
{
  "corredor_id": "sjl_proceres_0412",
  "nombre": "Av. Próceres de la Independencia (cuadra 41-44)",
  "geom": "...GeoJSON LineString...",
  "ext_12sem": 7,
  "semanas_con_denuncia_12": 5,
  "senal": "sostenida",
  "antecedente_violento_26sem": true,
  "tasa_100neg": 2.4,
  "p_escalamiento_4sem": 0.31,
  "p_percentil": 0.94,
  "tendencia": "subiendo",
  "frente": [
    {"corredor_id": "sjl_canto_0188", "nombre": "Jr. Canto Grande", "p": 0.22, "dist_m": 410}
  ],
  "analogos": [
    {"corredor_id": "comas_tupac_0077", "nombre": "Av. Túpac Amaru", "meses_antes_del_pico": 8}
  ],
  "top_features": [
    {"f": "ext_vec1_lag_2", "shap": 0.41, "txt": "subió la extorsión en calles conectadas hace 2 semanas"},
    {"f": "viol_lag_4", "shap": 0.19, "txt": "ya hubo un hecho con arma cerca el mes pasado"}
  ],
  "cobertura": {"denuncias_ok": true, "aviso_subregistro": true},
  "umbrales": {"senal_sostenida_semanas": 3, "ventana_semanas": 12, "decil_tasa": 10}
}
```

`POST /reporte-anonimo` recibe `{lat, lon, modalidad, texto_o_audio}`, devuelve `{corredor_id, aceptado}`
y **no guarda** ni teléfono, ni nombre, ni la coordenada exacta: solo el `corredor_id`.

## 7 · Stack

| Pieza | Herramienta | Por qué |
|---|---|---|
| Ingesta y agregación | DuckDB sobre el CSV | 1.8 GB sin cargar a memoria, SQL directo |
| Grafo vial | `osmnx` + `networkx` | Grafo y adyacencia en una línea |
| Snap y geometría | `geopandas` + índice espacial | Lo estándar |
| Modelo base | `scikit-learn` / gradient boosting | Rápido y explicable |
| Modelo grafo | `torch_geometric` | Si alcanza |
| Explicación | `shap` | Da las razones que Claude traduce |
| API | FastAPI | Mínimo |
| Mapa | deck.gl o Leaflet sobre el GeoJSON | Lo que Freddy levante más rápido |

Entorno: `uv run --with ...`, porque el Python del sistema está bloqueado por PEP 668.

## 8 · Privacidad por diseño

- No se publica mapa de territorios ni de riesgo de toda la ciudad. Se responde por ubicación consultada.
- El reporte anónimo guarda `corredor_id`, nunca la coordenada que llegó.
- Nada a nivel de negocio o persona, en ninguna salida.
- Cero atribución a bandas con nombre.
- Todo el texto del producto usa "denuncias registradas", no "delitos".
