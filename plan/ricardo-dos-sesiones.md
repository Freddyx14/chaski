# Ricardo, partido en dos sesiones de Claude

> **Actualizado contra SOT-3** (viernes 23 de octubre, 23:50 PT). Si esto contradice a `../SOT.md`, gana el
> SOT. Depende también de `plan-completo.md` y `../research/voz-quechua-modelos.md`.
> La propuesta de corredores de extorsión (`../Ricardo-idea/`) queda cerrada; no se trabaja más ahí.
>
> **Qué cambió con SOT-3, y por qué este documento se reescribió:**
> - El producto ya no es WhatsApp para gestantes: es un **intérprete en vivo** que usa el personal de salud
>   en la consulta (D9, D10). La usuaria principal es la enfermera.
> - Entra una función nueva que es mía: **detección automática de idioma** por turno (F2, D11).
> - **Sale la lectura de receta.** No existe en SOT-3. Lo que yo había puesto como B4 se elimina.
> - La evaluación chanka-salud (F8) la arma Freddy con su mamá; **a mí me tocan las métricas y los gráficos**.
> - El modelo base de reconocimiento es **Meta Omnilingual ASR `quy`**, no Whisper.

## Qué le toca a Ricardo, en una línea

**Todo lo que convierte audio en texto, texto en audio, y resultados en números que aguanten una pregunta
técnica.** Freddy tiene Claude, WhatsApp, el panel y el pitch. Ricardo tiene la voz, la visión y la
medición.

Según SOT-3 §5: **datos de voz, reconocimiento (pasos 0-1-2), detección de idioma, la voz de Chaski, y las
métricas con sus gráficos.** Más el que no está escrito pero es suyo: **que los modelos corran en la VM
con GPU de 40 GB** (D7).

## Por qué se parte en dos, y por dónde

La partición es **por carpeta**, igual que funcionó antes: dos sesiones que editan el mismo archivo
producen conflictos a las tres de la mañana. Y el corte natural ya existe en el plan de Freddy: la voz
tiene su propio ciclo de datos y entrenamiento, y la medición depende de otras entradas y produce otras
salidas.

Y en carpeta aparte de `app/`, que es de Freddy, para que nadie pise al otro mientras los dos commitean:

```
ricardo-artifacts/
├── CONTRATO.md        # compartido: formato de datos y las tres firmas
├── voz/
│   ├── contrato.py    # entender() · hablar() · idioma(), con versiones falsas
│   ├── ingesta.py     # SESIÓN A
│   └── ...            # SESIÓN A
├── salida/            # SESIÓN B
└── reports/           # los números, un JSON por número
```

El código de Ricardo va en la rama `ricardo/voz` y entra a `main` por pull request. `app/` no se toca.

---

## Sesión A · Entender la voz

Dueña de `ricardo-artifacts/voz/`. Riesgo técnico más alto y la que más tarda: arranca primero.

| # | Tarea | Criterio de aprobación |
|---|---|---|
| A1 | **Ingesta** (P1): audios de WhatsApp → 16 kHz mono, nombrados, con su transcripción, y los conjuntos partidos **por hablante** | El conjunto de prueba no comparte ni una voz con el de entrenamiento. Se imprime quién quedó fuera |
| A2 | **Línea base de reconocimiento** (paso 0) con **Omnilingual ASR `quy`** | CER y WER del modelo sin tocar, sobre el conjunto de prueba. Es el número «antes» del pitch |
| A3 | **Sesgo de vocabulario** (P2, paso 1): lista de términos de la posta, números, días, señales de alarma | Mejora medida sobre la línea base. Si no mejora, se dice y se queda la línea base |
| A4 | **Ajuste fino** (P2, paso 2) | Solo si A3 ya está cerrado. Mejora medida sobre el mismo conjunto de prueba |
| A5 | **`entender(audio) → texto`** | Freddy puede llamarla sin saber qué hay adentro. Es el contrato |
| A6 | **Reconocimiento del castellano** (P3 de SOT §7 queda en Freddy; este es el de voz): decidir entre Whisper y Omnilingual `spa` | Se mide la espera por turno, no solo el acierto: es un intérprete en vivo |

**Regla de honestidad de esta sesión:** los tres números de voz (antes, con vocabulario, con ajuste fino)
se miden **sobre la misma voz jamás vista**. Si el ajuste fino no mejora, se reporta que no mejoró.

**Dónde corre el entrenamiento.** La máquina local es un **Apple M4 con 16 GB y 282 GB libres, sin
`torch` instalado**. Sirve para inferencia, línea base y evaluación. Para el ajuste fino, Colab con GPU es
el camino principal y la M4 el respaldo: instalar `torch` con MPS toma minutos, pero un ajuste fino de un
modelo mediano en 16 GB es apretado. **Decidir esto en la primera hora, no a las tres de la mañana.**

---

## Sesión B · Responder y medir

Dueña de `ricardo-artifacts/salida/`. Produce la voz de Chaski, la detección de idioma y los números.

| # | Tarea | Criterio de aprobación |
|---|---|---|
| B1 | **Detección de idioma** (F2): `facebook/mms-lid-512` limitado a `quy` y `spa`, por turno | Precisión medida sobre los audios de las familias **y** sobre castellano. Se reporta qué pasa con las frases mezcladas, que en la posta son normales |
| B2 | **Voz de Chaski** (F5): `facebook/mms-tts-quy`, después ajustado con la voz de la mamá de Freddy | Ella escucha **a ciegas** y dice si se entiende. Su juicio manda sobre cualquier métrica |
| B3 | **Espera por turno**: cuánto tarda cada paso del ciclo (idioma → reconocer → Claude → hablar) | Un intérprete que tarda ocho segundos por turno no se usa en una consulta. Se mide por paso para saber qué recortar |
| B4 | **Métricas y `reports/`**: consolidar los números de A y los de Freddy en los JSON del contrato | Un JSON por número, y la página los lee sin tocar nada más |
| B5 | **Gráficos de la página de resultados** | Reusa el marco de `../Ricardo-idea/viz`: tokens claros, canvas o SVG, sin modo oscuro |

**Lo que ya no existe:** la lectura de receta con abstención. SOT-3 la sacó del producto. Si vuelve, vuelve
como tarea nueva, no como arrastre.

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

Una rama para el código de Ricardo, `ricardo/voz`, que entra a `main` por pull request. Las dos sesiones
trabajan en esa misma rama pero en **carpetas distintas** (`voz/` y `salida/`), así que no se pisan.
La documentación de coordinación, como este archivo, va directo a `main` para que Freddy la lea sin
esperar al PR.

**Antes de abrir el PR:** `uv run --with pytest python -m pytest -q` en `ricardo-artifacts/` tiene que
estar en verde, y el PR no debe duplicar nada de `app/`.

## Qué le dices a la otra sesión al abrirla

> Trabajamos en Chaski, un asistente de WhatsApp que lleva las indicaciones de la posta de Pilpichaca a
> gestantes quechuahablantes, en audio y en quechua chanka. Lee `plan/plan-completo.md`,
> `ideas/producto.md` y `plan/ricardo-dos-sesiones.md`.
> Eres la **sesión [A · voz]** o la **[B · medición]**. Eres dueña de la carpeta `voz/` o `medicion/`.
> No edites la carpeta de la otra sesión, ni `contrato/`, sin avisar. Trabaja contra `contrato/`.

## Orden de arranque

1. Sesión A escribe `contrato/datos.md` y `contrato/entender.py` (versión falsa). **20 minutos.**
2. Sesión A sigue con A1 y A2, que son el camino crítico.
3. Sesión B arranca con B1 en paralelo, contra el `entender` falso.
4. Las dos se encuentran cuando A5 esté listo y se cambie la versión falsa por la real.

## Dónde entrena, con números medidos

`voz/bench_finetune.py` arma el modelo desde su configuración con pesos al azar y cronometra pasos de
entrenamiento reales. No descarga nada, así que responde la pregunta antes de prender la instancia.

Medido en el M4 de 16 GB, con `whisper-small` como referencia:

| Configuración | Resultado |
|---|---|
| batch 2, MPS | **1.378 s por paso** · 1,000 clips × 3 épocas = 1,500 pasos → **34 min** |
| batch 4, MPS | **No termina en 10 minutos.** No entra en 16 GB |

Conclusión: para un modelo de ~185M de parámetros la máquina local alcanza. **La VM de 40 GB se justifica
por el modelo real**, que es Omnilingual, no Whisper, y por correr varias configuraciones a la vez.
**Pendiente:** medir Omnilingual con el mismo script. Es un codificador con CTC, no un modelo de
codificador-decodificador como Whisper, así que su costo sí baja con audios cortos, mientras que el de
Whisper no (procesa 30 s por clip aunque el audio dure 4).

## Lo que no se hace

- Nada de la API de Claude hasta que Ricardo lo diga. Freddy lleva ese lado.
- Nada más en `Ricardo-idea/`. Queda cerrado, commiteado y sirve como antecedente: pipeline, evaluación
  honesta y un resultado negativo reportado.
