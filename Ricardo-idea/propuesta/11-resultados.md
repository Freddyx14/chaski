# Resultados del prototipo — el modelo de escalamiento no funciona

> Corrido el viernes 23 de octubre de 2026, sobre los datos reales. Código en `../pipeline/`,
> tabla en `../reports/ablation.csv`. Esto es un resultado negativo y se reporta como tal.

## Lo que se construyó y funciona

| Pieza | Estado | Cifra |
|---|---|---|
| Limpieza con filtro iterativo de volcaderos | ✅ 3/3 tests | 1,236,864 hechos limpios · 8,695 extorsiones · 4,598 violentos |
| Corredores desde el PBF de Geofabrik | ✅ 7/7 tests | 79,293 corredores, mediana 171 m |
| Enganche de hechos al corredor | ✅ 3/3 tests | **97.8% enganchado**, distancia mediana 6.3 m, p90 24.7 m |
| Panel corredor × semana con etiqueta | ✅ 5/5 tests | 2,442,652 filas, 313 semanas, prevalencia 0.575% |
| Features (lags, difusión en grafo, violencia previa) | ✅ 5/5 tests | 19 columnas, mediana de 8 vecinos por corredor |
| Métricas PAI y recall@k por longitud | ✅ 4/4 tests | — |
| Partición temporal sin fuga | ✅ 2/2 tests | entrenamiento ≤2022-12-03, prueba 2023, hueco de 4 semanas |

El pipeline entero corre de punta a punta en unos 5 minutos y es reproducible.

## Lo que no funciona

Ablation sobre 2023 (374,592 filas de prueba, 2,222 positivos):

| Modelo | Bloques | AUC-PR | PAI@5% | Recall@5% |
|---|---|---|---|---|
| baseline extorsión reciente | — | 0.0067 | 1.07 | 0.054 |
| **baseline violencia reciente** | — | 0.0062 | **1.34** | **0.067** |
| gradient boosting | A | 0.0059 | 0.90 | 0.045 |
| gradient boosting | A+B | 0.0060 | 0.87 | 0.044 |
| gradient boosting | A+B+C | 0.0079 | 1.09 | 0.054 |
| gradient boosting | A+B+C+D | 0.0083 | 0.57 | 0.029 |
| gradient boosting | A+B+C+D+G | 0.0069 | 1.26 | 0.063 |

**Ningún modelo le gana al baseline de violencia reciente.** La prevalencia es 0.0059 y el AUC-PR de todos
ronda ese mismo valor: el modelo no ordena mejor que el azar.

Peor aún, al mirar el extremo del ranking, que es lo que importa:

| | tasa de positivos |
|---|---|
| Base del periodo | 0.0059 |
| Corredores con violencia reciente | 0.0182 (**3.1×**) |
| **1% con mayor score del modelo** | **0.0044 (por debajo de la base)** |

El modelo entrenado **invierte**: los corredores que más marca tienen menos violencia futura que el
promedio. Un segundo intento con features más densas (sumas móviles de 4, 12, 26 y 52 semanas), etiqueta
de 8 semanas y `class_weight='balanced'` empeoró: PAI 0.12 a 0.25 contra 1.59 a 3.47 del baseline.

## Por qué, hasta donde se puede afirmar

1. **Dispersión.** Solo el 0.57% de las filas tiene violencia previa distinta de cero, y la extorsión
   aparece en el 0.3%. A 171 metros y una semana, casi todo el panel es cero, y el modelo aprende a
   predecir cero.
2. **Cambio de régimen en el registro, y esta es la explicación más probable.** El geocodificado se
   derrumba con los años (48.5% en 2018 → 30.6% en 2023, `09-validaciones.md`). El modelo entrenado con
   2018–2022 aprende dónde se registraban bien los hechos, y en 2023 esos mismos corredores perdieron
   registro. La inversión del ranking es consistente con eso: lo que marca son corredores cuyo registro
   se deterioró, no corredores donde bajó la violencia.
3. **La persistencia ya agota la señal fácil.** 3.1× es real, pero es lo que da mirar hacia atrás. Lo que
   el proyecto prometía —que la extorsión anticipa la violencia por encima de eso— no se sostiene a esta
   escala.

## Qué se hace con esto

Se aplica la regla de corte escrita en `03-plan-36h.md` y `07-ablation.md`: **se corta la predicción de
escalamiento.** No se presenta un modelo que no le gana a "mira dónde hubo violencia el mes pasado".

Lo que sí se sostiene y sigue valiendo:

- **La capa descriptiva.** Dónde, cuándo y cuánto, a nivel de corredor y no de distrito, con el filtro de
  volcaderos que nadie más aplica. Eso es un mapa que hoy no existe para Lima.
- **El hallazgo del geocodificado.** En 2025 solo el 3.2% de las denuncias de extorsión tiene coordenada
  utilizable, y el 64% de las de 2018–2025 cae en puntos de volcado. Es verificable, es reproducible con
  `validacion/`, y dice algo real sobre la calidad del dato con el que se gobierna la seguridad en Lima.
- **La disciplina de evaluación.** Partición temporal, PAI por longitud, baseline duro y un resultado
  negativo reportado. Eso es lo que separa esto de un dashboard.

## Si alguien retoma esto

En orden de lo que más probablemente cambie el resultado:

1. **Corregir el sesgo de registro antes de modelar.** Normalizar por la tasa de geocodificado del
   distrito y el año, o entrenar y probar dentro del mismo régimen (por ejemplo 2022 contra 2023).
2. **Subir la escala.** Corredor-mes en vez de corredor-semana, o corredores de 500 a 800 m fusionando
   vecinos.
3. **Cambiar el objetivo.** En vez de predecir el siguiente hecho violento, estimar la prevalencia
   corregida de extorsión por corredor, que es la cifra que nadie tiene.
4. **Hawkes sobre el grafo**, que usa los tiempos exactos en vez de agregarlos por semana y no sufre
   igual la dispersión.
