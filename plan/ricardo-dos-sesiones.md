# Ricardo, partido en dos sesiones de Claude

> Escrito el viernes 23 de octubre de 2026, después de decidir que el equipo va 100% con Rimay.
> Depende de `plan-completo.md` (el plan de Freddy), `../ideas/producto.md` y
> `../research/voz-quechua-modelos.md`. La propuesta de corredores de extorsión (`../Ricardo-idea/`) queda
> cerrada y commiteada; no se trabaja más ahí.

## Qué le toca a Ricardo, en una línea

**Todo lo que convierte audio en texto, texto en audio, y resultados en números que aguanten una pregunta
técnica.** Freddy tiene Claude, WhatsApp, el panel y el pitch. Ricardo tiene la voz, la visión y la
medición.

De las piezas de `plan-completo.md` §3, le corresponden P1, P2, P3, P5, la medición de T1 y T2, y los
gráficos de P9.

## Por qué se parte en dos, y por dónde

La partición es **por carpeta**, igual que funcionó antes: dos sesiones que editan el mismo archivo
producen conflictos a las tres de la mañana. Y el corte natural ya existe en el plan de Freddy: la voz
tiene su propio ciclo de datos y entrenamiento, y la medición depende de otras entradas y produce otras
salidas.

```
rimay/
├── contrato/          # compartido, se escribe primero y no se toca sin avisar
│   ├── datos.md       # formato {persona, bloque, numero, audio, transcripcion}
│   └── entender.py    # la firma que el lado de Claude llama
├── voz/               # SESIÓN A
└── medicion/          # SESIÓN B
```

---

## Sesión A · Voz

Dueña de `voz/`. Es la que tiene el riesgo técnico más alto y la que más tarda, así que arranca primero.

| # | Tarea | Criterio de aprobación |
|---|---|---|
| A1 | **Ingesta** (P1): audios de WhatsApp → 16 kHz mono, nombrados, con su transcripción, y los conjuntos partidos **por hablante** | El conjunto de prueba no comparte ni una voz con el de entrenamiento. Se imprime quién quedó fuera |
| A2 | **Línea base de reconocimiento** (P2, paso 0) | CER y WER del modelo sin tocar, sobre el conjunto de prueba. Es el número «antes» del pitch |
| A3 | **Sesgo de vocabulario** (P2, paso 1): lista de términos de la posta, números, días, señales de alarma | Mejora medida sobre la línea base. Si no mejora, se dice y se queda la línea base |
| A4 | **Ajuste fino** (P2, paso 2) | Solo si A3 ya está cerrado. Mejora medida sobre el mismo conjunto de prueba |
| A5 | **`entender(audio) → texto`** | Freddy puede llamarla sin saber qué hay adentro. Es el contrato |
| A6 | **Voz de Rimay** (P3): MMS-TTS `quy`, más los audios pregrabados de la mamá de Freddy para lo fijo | La mamá de Freddy escucha a ciegas y dice si se entiende. Su juicio manda sobre cualquier métrica |

**Regla de honestidad de esta sesión:** los tres números de voz (antes, con vocabulario, con ajuste fino)
se miden **sobre la misma voz jamás vista**. Si el ajuste fino no mejora, se reporta que no mejoró.

**Dónde corre el entrenamiento.** La máquina local es un **Apple M4 con 16 GB y 282 GB libres, sin
`torch` instalado**. Sirve para inferencia, línea base y evaluación. Para el ajuste fino, Colab con GPU es
el camino principal y la M4 el respaldo: instalar `torch` con MPS toma minutos, pero un ajuste fino de un
modelo mediano en 16 GB es apretado. **Decidir esto en la primera hora, no a las tres de la mañana.**

---

## Sesión B · Medición y visión

Dueña de `medicion/`. Produce los números que van a la página y al pitch, y la lectura de la receta.

| # | Tarea | Criterio de aprobación |
|---|---|---|
| B1 | **Arnés de evaluación chanka-salud** (T1): corre las indicaciones de prueba por cada sistema y guarda las salidas con su identificador | La mamá de Freddy califica **a ciegas**: no sabe qué salida es de quién. Sin eso la evaluación no vale |
| B2 | **Métricas de T1**: exactitud y, sobre todo, **riesgo clínico** del error (cambió una dosis, una fecha, una señal de alarma) | Claude contra Google Translate, con la misma rúbrica, calificado por la misma persona. El protocolo sale de Kong et al. (2026) |
| B3 | **Medición del detector** (T2): de los errores que la hablante encontró en B2, cuántos atrapó el detector de Freddy | Es el número del pitch: «atrapa X de cada 10». Se reporta también qué se le escapó |
| B4 | **Lectura de receta con abstención** (P5): foto → medicamento, dosis, frecuencia, **y un umbral medido para callarse** | Se mide cuántas veces se abstiene y cuántas se equivoca cuando no se abstiene. Un sistema que nunca se abstiene no sirve |
| B5 | **Gráficos de la página de resultados** (P9) | Reusa el marco de visualización de `../Ricardo-idea/viz`: tokens claros, canvas o SVG, sin modo oscuro |

**Pendiente de acordar con Freddy:** en `plan-completo.md` §2 la lectura de la receta aparece del lado de
Claude (Freddy) y en `ideas/producto.md` §11 (T4) aparece del lado de Ricardo. **Lo difícil de P5 no es
leer la receta, es la abstención medida**, y eso es medición. Propuesta: B4 lo lleva la sesión B y Freddy
revisa el prompt. Confirmarlo antes de que las dos sesiones escriban lo mismo.

---

## El contrato, que se escribe antes que nada

1. **Formato de datos**, de `plan-completo.md` §2: `{persona, bloque, numero, audio, transcripcion}`.
   Lo escribe la sesión A en `contrato/datos.md` en los primeros 20 minutos, porque es quien recibe los
   audios.
2. **`entender(audio) → texto`**: la sesión A publica la firma en `contrato/entender.py` con una
   implementación falsa que devuelve una transcripción fija. **La sesión B y Freddy trabajan contra esa
   versión falsa desde el minuto cero** y nunca esperan al modelo.
3. **Salidas de métricas**: las dos sesiones escriben JSON en `reports/`, una por número.
   `reports/asr.json`, `reports/traduccion.json`, `reports/detector.json`, `reports/receta.json`.
   La página de resultados lee esos cuatro archivos y nada más.

Ninguna sesión cambia el contrato por su cuenta. Si hace falta, se cambia en los dos lados.

## Ramas

**Nada de ramas por sesión.** Eso ya se probó esta noche y no sirvió: las carpetas son disjuntas, así que
las dos sesiones commitean a `main`. La regla que las mantiene separadas es la carpeta, no la rama.

## Qué le dices a la otra sesión al abrirla

> Trabajamos en Rimay, un asistente de WhatsApp que lleva las indicaciones de la posta de Pilpichaca a
> gestantes quechuahablantes, en audio y en quechua chanka. Lee `plan/plan-completo.md`,
> `ideas/producto.md` y `plan/ricardo-dos-sesiones.md`.
> Eres la **sesión [A · voz]** o la **[B · medición]**. Eres dueña de la carpeta `voz/` o `medicion/`.
> No edites la carpeta de la otra sesión, ni `contrato/`, sin avisar. Trabaja contra `contrato/`.

## Orden de arranque

1. Sesión A escribe `contrato/datos.md` y `contrato/entender.py` (versión falsa). **20 minutos.**
2. Sesión A sigue con A1 y A2, que son el camino crítico.
3. Sesión B arranca con B1 en paralelo, contra el `entender` falso.
4. Las dos se encuentran cuando A5 esté listo y se cambie la versión falsa por la real.

## Lo que no se hace

- Nada de la API de Claude hasta que Ricardo lo diga. Freddy lleva ese lado.
- Nada más en `Ricardo-idea/`. Queda cerrado, commiteado y sirve como antecedente: pipeline, evaluación
  honesta y un resultado negativo reportado.
