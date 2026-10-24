# Chaski · arquitectura del intérprete agente (sáb 24-oct, 13:10 PT)

> **Acordado por Freddy y Ricardo** en la llamada de las 12:45 (transcript abajo, §9). Sale de la entrevista con la
> enfermera (`research/entrevistas/`) y de la propuesta `plan/propuesta-interprete-agente.md`, que este documento
> reemplaza. Decisiones D32–D36 para el `SOT.md`. **Congelamos funciones a las 19:00.**

---

## 1 · Qué es un intérprete y no un traductor

Un traductor pasa frases. Un intérprete **entiende a quién le habla, piensa cómo decirlo para que el otro lo entienda,
pregunta cuando no entendió y no traduce lo que no era para el otro.** Eso, en reglas que se pueden programar y probar:

| # | Comportamiento | Regla dura |
|---|---|---|
| C1 | **Sabe quién habla** | Cada turno llega con el idioma detectado (`/idioma`) y el rol (personal / paciente) |
| C2 | **Pule antes de traducir** (estilo Wispr Flow, los dos lados) | Quita muletillas, repeticiones y frases a medias. **Nunca cambia un dato** (medicamento, dosis, frecuencia, días, parte del cuerpo) |
| C3 | **Dice las órdenes como indicaciones** | «Dile que se eche» → al paciente: «Échese, por favor». No «ella dice que se eche» |
| C4 | **Repregunta al mismo hablante** cuando falta un dato crítico o algo es ambiguo, en su idioma, antes de traducir | **Máximo una repregunta seguida** por tema; si sigue sin claridad, traduce lo que hay y avisa al personal |
| C5 | **Contesta él cuando la pregunta es para él** | «¿Qué dijo?», «¿entendió?», «repítele» → responde Chaski al que preguntó; **no se le traduce al otro** |
| C6 | **Detecta basura** | Ruido, silencio, frase sin sentido o transcripción de baja confianza → «no le entendí, ¿me lo repite?». Nunca traduce algo sin sentido |
| C7 | **Nunca agrega un dato clínico** | Puede preguntar y reformular. No inventa dosis, diagnóstico ni indicación que nadie dijo |
| C8 | **Se audita antes de hablar** (F4, ya existe) | Retraducción a ciegas + comparación en código de los hechos críticos. Si no coinciden, no lo dice y le explica al personal qué parte falló |
| C9 | **Usa la frase verificada cuando existe** | Si lo que hay que decir ya está en el banco verificado, reproduce ese audio (correcto y al instante) en vez de generar |

---

## 2 · El turno, paso a paso

```
audio ──► /idioma ──► ¿quién habla?
            │
            ├─ castellano ──► Cartesia (oír, /escuchar) ─────────────┐
            └─ quechua ────► omniASR ajustado (N mejores, /entender) ─┤
                                                                       ▼
                                          ┌──────── INTÉRPRETE (Claude, 1 llamada) ────────┐
                                          │ entra: transcripción(es), quién habla, rol,      │
                                          │        historial de la consulta, modo, banco     │
                                          │ decide UNA acción:                               │
                                          │   traducir · repreguntar · responder ·           │
                                          │   no_entendi · usar_frase_banco                  │
                                          └──────────────────────────────────────────────────┘
                                                                       │
             traducir ──► texto pulido ──► TRADUCTOR (NLLB ajustado; Claude de respaldo)
                                                   │
                                                   ▼
                                     AUDITORÍA (Claude retraduce a ciegas + código compara)
                                         │ pasa                      │ falla
                                         ▼                           ▼
                           voz: Cartesia (castellano)      bloqueo + aviso al personal
                                omniTTS/MMS (quechua)
             repreguntar / responder / no_entendi ──► mismo camino de traducción y voz, al MISMO hablante
             usar_frase_banco ──► audio verificado del banco (sin generar, sin esperar)
```

Al cerrar la consulta: **resumen** (`/resumen`, ya existe) + **glosario de palabras nuevas** (C10, abajo).

### El contrato del intérprete (salida estructurada, Pydantic)

```python
class Decision(BaseModel):
    accion: Literal["traducir", "repreguntar", "responder", "no_entendi", "usar_frase_banco"]
    para: Literal["personal", "paciente"]          # quién va a escuchar
    idioma_salida: Literal["spa", "quy"]
    texto_pulido: str          # lo que se va a decir, en el idioma de ORIGEN, ya pulido (C2/C3)
    motivo: str                # por qué esta acción (se muestra al personal en «repreguntar»)
    frase_banco_id: str | None # solo si accion == usar_frase_banco
    dato_faltante: str | None  # solo si accion == repreguntar: «parte del cuerpo», «desde cuándo»…
```

- **Una sola llamada a Claude decide** (rápido). La traducción y la auditoría son pasos aparte, como hoy.
- El código, no el modelo, impone C4 (máx. una repregunta) y C7 (los hechos del texto pulido tienen que estar en la transcripción original: se comparan con `hechos.comparar`).
- Modelo: el más rápido que pase las pruebas (D15). Medir Haiku 4.5 y Sonnet 5 para el intérprete.

---

## 3 · Traducción: dónde entra el ajuste fino

Acordado: **Claude pule y audita; el modelo ajustado traduce.**

| Paso | Motor | Por qué |
|---|---|---|
| Pulir (los dos lados) | Claude | Entender intención, contexto y basura |
| castellano → quechua | **NLLB-200 ajustado** (Ricardo) · respaldo: Claude | Es donde Claude es más débil; el ajuste fino es para esto |
| quechua → castellano | NLLB-200 ajustado + Claude pule el castellano | El personal tiene que leer castellano claro |
| Auditoría | Claude (retraducción a ciegas) + código | Juez distinto del traductor |

**Interfaz única** `traducir(texto, de, a) -> str` con un interruptor `motor = "nllb" | "claude"`. Si el NLLB ajustado
no le gana a Claude en la medición de Ricardo (chrF++), **el interruptor queda en Claude** y se dice así en el pitch.
Línea base ya medida: Sonnet sin ajuste, 30 frases, **chrF++ 42.31** (`ricardo-artifacts/reports/metricas.md`).

---

## 4 · El banco de frases verificadas (RAG y modo emergencia)

Una sola fuente para dos usos: **frases cuya traducción y audio sabemos que están bien.**

```json
{ "id": "dolor-donde", "es": "¿Dónde le duele?", "quy": "…", "audio": "https://…", "tags": ["emergencia","dolor"],
  "fuente": "familia p4 | base médica | revisado por la enfermera", "split": "banco" }
```

- **Fuentes**: la base de frases médicas que encontró Ricardo (anemia, dolor de estómago…), las frases verificadas que las familias leen en voz alta en el formulario (bloque extra), y lo que la enfermera revise. El audio sale de las grabaciones de la familia; si no hay, de la voz de Chaski.
- **Recuperar sin base vectorial**: el banco es chico (cientos). El intérprete recibe las ~20 candidatas más parecidas (búsqueda simple por palabras sobre `es`) y elige `frase_banco_id` solo si es **la misma intención**. Nada de infraestructura nueva.
- **Modo emergencia (C11)**: una pantalla de botones con las frases `tags: emergencia` (¿dónde le duele?, ¿desde cuándo?, ¿es alérgico?, ¿está embarazada?, señale con el dedo, ¿vino con alguien?…). Toca y suena. **Cero espera de modelos.** Y la respuesta del paciente vuelve por el turno normal.
- ⚠️ **El mismo dato sirve para ajustar y para el banco, pero NUNCA para la prueba.** Ricardo parte cada fuente en `train / banco / test` **antes** de entrenar; las 100 `verificadas` siguen reservadas para medir. Si una frase de prueba entra al banco o al entrenamiento, el número del pitch deja de valer.

---

## 5 · Receta (F9, ya empezada: terminarla)

Foto de la receta o la caja → Claude visión (`/ver`) → hechos: medicamento, cuánto, cada cuánto, cuántos días →
indicación armada desde esos hechos → traducción → auditoría → voz → **«¿me lo repite?»** (el paciente lo dice con sus
palabras y Claude juzga si entendió, F6). Es lo que hoy hacen partiendo la pastilla en 4 y repitiendo hasta 4 veces.

---

## 6 · Aprender quechua desde las consultas (visión; hoy solo el primer paso)

La enfermera: el resumen le serviría porque «me estaría enseñando cómo hablarlo». Freddy: el Estado gasta en cursos
de quechua para el personal y no aprenden.

- **Hoy (C10)**: el resumen trae un **glosario de las palabras quechua nuevas de esa consulta**, con su audio.
- **Después (backlog)**: un cuaderno personal que se arma solo con las consultas de cada uno, repaso espaciado con frases de *sus* pacientes, y medir cuántas frases ya dice sin Chaski. Chaski interpreta hoy y enseña para mañana.
- **En el pitch**: una línea como visión, no como función terminada.

---

## 7 · Reparto de tareas (hasta las 19:00)

| Quién | Qué | Entrega |
|---|---|---|
| **Ricardo** | 1. **Línea base congelada** de reconocimiento y traducción, con el hablante de prueba separado (lo crítico, sigue primero) · 2. Partir los datos en `train / banco / test` · 3. **NLLB-200 ajustado** castellano↔quechua con la base de texto (somosnlp quy + la base médica) y ruta `/traducir` · 4. omniASR ajustado con los audios completos (los de su papá y los del formulario) · 5. Audios del banco de emergencia con la voz de Chaski donde falte grabación | 1–2 a las 15:00 · 3–4 a las 19:00 |
| **Sesión ui-ux** (app) | 1. Pantalla y flujo de las 5 acciones: tarjeta «Chaski pregunta» (repreguntar), respuesta de Chaski al personal (responder), «no le entendí» · 2. **Modo emergencia** (grilla de botones del banco) · 3. Terminar **receta** + «¿me lo repite?» · 4. Glosario en el resumen | 19:00 |
| **Esta sesión** (Claude, con Freddy) | 1. `app/chaski/interprete.py`: la Decisión, el prompt con C1–C9, las reglas en código (C4, C7) y **pruebas con casos reales y basura** (FakeClient, como `auditoria.py`) · 2. `app/chaski/banco.py` + `banco.json` con el formato de §4 · 3. Interfaz `traducir()` con el interruptor de motor · 4. Medir Haiku vs Sonnet para el intérprete · 5. Docs, pitch y Devpost | 1–3 a las 16:00 · 4 a las 17:00 |
| **Freddy** | 1. Pedir a la familia que grabe (el link del formulario) · 2. **Con su mamá**: revisar los textos quechua del modo emergencia y de la app, y grabar su saludo para el pitch · 3. Pitch y Devpost | 1 ya · 2 a las 18:00 |

**Integración 19:00–21:00**: el servicio de Ricardo llama a `interpretar()` dentro de `/turno/enfermera` y
`/turno/paciente` (mismas rutas que ya usa la app, con el campo nuevo `accion`). 21:00 borrador de Devpost. 22:00 ensayo.

**Si a las 19:00 algo no está**: el NLLB ajustado → queda Claude traduciendo; el ASR ajustado → queda el modelo base
(y el pitch muestra la línea base y el plan); la repregunta → se corta de la demo. **El modo emergencia y la receta no
se cortan**: son lo que la enfermera pidió.

---

## 8 · Decisiones para el SOT

| D | Decisión | Por qué |
|---|---|---|
| D32 | **Chaski es un intérprete agente**: una llamada de Claude decide entre traducir, repreguntar, responder, no_entendi o usar una frase verificada (C1–C9) | La enfermera describe a un intérprete humano: entiende, repregunta, transmite indicaciones. Acordado por Freddy y Ricardo |
| D33 | **Claude pule y audita; NLLB ajustado traduce**, con Claude de respaldo detrás de un interruptor | El ajuste fino es donde aporta; Claude es el juez. Si NLLB no gana en chrF++, queda Claude |
| D34 | **Banco de frases verificadas** para RAG y modo emergencia, sin base vectorial; los datos se parten `train / banco / test` antes de entrenar | Rapidez en emergencias, correctitud garantizada y la medición intacta |
| D35 | **Modo emergencia y receta son obligatorios en la demo** | Son los dos dolores que la enfermera nombró: rapidez y medicamentos |
| D36 | **Aprender quechua desde las consultas**: hoy glosario en el resumen; la plataforma de aprendizaje va al backlog y al pitch como visión | La enfermera lo pidió; el Estado capacita y el personal no aprende |

---

## 9 · Transcript de la llamada Freddy–Ricardo (12:45, transcripción automática)

> Meeting Title: Whisperflow y modo emergencia en quechua con fine-tuning · Date: Oct 24

La idea de la gente es primero pulir lo que dice cada lado, así como hacer Whisperflow, o sea, por both sides, tanto si tú hablas como en español, que te haga como una polished version de eso para que se entienda mejor. Si es que necesita hacerse una polished versión, no, normal no, pero tiene que tener ese trabajo agéntico. Y fácil, hay que meterle garbage también para que lo haga bien y no diga nonsense. Que pueden ser peor. Y luego ya recién cuando se hace el translation de Spanish a quechua es ahí cuando recién se utiliza el fine tuning, el modelo fine tuneado. Mira, el modo de emergencia me gusta. O sea, ¿sabes qué podríamos hacer? Los audios que nos lleguen, como sabemos que son correctos, los indexamos, hacemos un wrap. Ya recuperarlo simplemente es llamar al audio, por así decirlo, con preguntas ya traducidas, así simplemente cuando ya no sepa qué decir. Claro, muy emergencia. Es, sí, es eso yo también estaba pensando, pero o sea, como audios pregrabados de como qué te duele, algo así. Claro. Porque, ¿te acuerdas que te dije que encontré una base? Que tiene ese tipo de cosas de tienes anemia, te duele el estómago, o sea, tiene esas cosas traducidas. Entonces creo que podríamos usar esa base que encontré para el modo emergencia en quechua. Ah, ya, pues. Y eso también úsalo para fine-tunear el modelo. Ya uso eso. Aunque depende, porque la idea de eso era que sea indexado, que recuperarlo sea así. Claro, o sea, para las dos cosas, para fine-tunear el modelo, porque es Ya tenés la clave, pero mano, úsalo para las dos cosas, para fine-tunear el modelo y para indexarlo pues en RAG, y lo traes. Pero sí, ese modo de emergencia hay que trabajarlo. Bastante porque es crítico para ellos. The lunch is here. Hace media hora, bueno, casi media hora. Ay, primero empezaba yo desde el D. Y ahorita vamos, mano, hay que terminar de definir esto ya. Available in 30 minutes. Hace 30 minutos dijo eso, a las 12:42 recién. Cuidado, advide spicy, mano. Ya hay que terminar, mano, ya. A terminar lo de la receta que ya está empezado. Ese es KitchenFlap. Feature clave, feature clave. A lo que había, lo que estaba haciendo del esto, ¿no? Pero, ¿de dónde lo tenía abierto? Esta cosa, ¿no? Sí, sí. Ya, chévere, chévere. ¿Qué dice el backlog? Al back lo ponen de varias vueltas que conduce solo a la conversación y la voz en tiempo real. El pitch cuenta como el siguiente paso. La regla es que Chaski pueda preguntar y reformular, pero nunca agregar una que opine y todo así. O sea, lo que yo tenía como idea es que sea inteligente, pues, o sea, que literalmente se comporte como un humano, como un traductor que funcione para both sides, identifique como quién está hablando y lo que tú digas que él piense cómo decírselo de la mejor manera a la otra persona y por ejemplo si tú tienes follow up questions y le preguntas pero qué está diciendo esta persona que sea inteligente para responderte a ti y que no te traduzca eso como a la otra persona. Es que no tiene que ser una traducción directa, claro, tiene que hacerlo en un lenguaje más polite, como dices, que pueda entenderlo. Que sea como literalmente un traductor, pues un traductor hace eso, que se comporte literalmente como un traductor, pero eso hay que traducirlo a código, a features, tools, porque es más agéntico eso, pues hay que meterle garbage también. Eso. Y o sea, igual lo del fine tuning está perfecto porque es literalmente para lo que vamos a usar, para que sea preciso pues en las traducciones, translate y todo eso. Así, de hecho, si tendríamos que fine tunear con el forms Con la base que tengo, eso para lo escrito. Para el audio, con simplemente creo que iban a ser los, bueno, supongo que con los audios mi papá podría hacer porque son los que están completos. Sí, mano. No, para poner dos mo PPT, mano, ahora sí. Ya me gusta. Okay.
