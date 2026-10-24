# Rimay — fuente de verdad (SOT)

> **Versión SOT-3 · viernes 23 de octubre de 2026, 23:50 PT**
>
> **Regla:** toda decisión nueva entra aquí primero. Si otro documento contradice este, **gana este** y el otro
> está desactualizado. La página visual (`plan/rimay-visual.html`, https://claude.ai/artifact/4E7Si4gN9mpF34eha55jpH)
> se regenera desde este archivo y lleva **el mismo número de versión**: si los números no coinciden, no están sincronizados.

---

## 1. El producto, hoy

**Rimay es un intérprete castellano ↔ quechua chanka que el personal de salud tiene en su celular.** La enfermera
habla y Rimay lo dice en quechua; el paciente responde y Rimay detecta que es quechua y se lo dice a ella en castellano.
Antes de decir algo, Rimay se audita: si una dosis, una hora o una fecha cambió en la traducción, no lo dice.

| | |
|---|---|
| **Usuaria principal** | El personal de salud de la posta (enfermera, técnico, obstetra) |
| **Quien se beneficia** | Los pacientes quechuahablantes de la **posta de Pilpichaca (Huancavelica)**, en cualquier atención: niño, fiebre, diarrea, presión, diabetes, embarazo, adulto mayor |
| **Dónde** | En la consulta, cara a cara, con el celular entre los dos |
| **Forma** | App web en el celular (se instala en la pantalla de inicio). Los modelos de voz corren en la GPU de Ricardo |
| **Inspiración** | Wispr Flow: un modelo que entiende lo que quisiste decir y lo deja claro |

### Una consulta, paso a paso
1. La enfermera habla en castellano.
2. Rimay **entiende lo que quiso decir**: limpia muletillas y frases a medias, deja los números explícitos.
3. **Auditoría**: traduce al chanka, retraduce a ciegas, compara dosis, horas, días y citas con código. Si algo cambió, no lo dice y le muestra a la enfermera qué revisar. *(construido)*
4. Rimay **lo dice en quechua chanka**, en voz alta; la enfermera lo ve en pantalla.
5. El paciente responde. Rimay **detecta el idioma** solo.
6. Rimay **entiende lo que quiso decir el paciente** y se lo dice a la enfermera en castellano, avisando si no está seguro.
7. Al final: **«¿Me lo repite?»**. Rimay marca qué entendió el paciente y qué no.

### Por qué importa
Una indicación que no se entiende es un tratamiento que no funciona: dosis equivocada, pastilla que se deja, control
al que no se vuelve. En Pilpichaca, la mamá de Freddy es la única enfermera que habla quechua. En toda Huancavelica hay
**52 servidores públicos bilingües certificados** (~1 por cada 4,000 quechuahablantes). Solo el **1%** de los
establecimientos de salud del país tiene atención intercultural. Fuentes: `research/problemas-lenguas-originarias.md`.

---

## 2. Funciones

| # | Función | Lo difícil | Estado |
|---|---|---|---|
| F1 | **Entender quechua hablado** | Casi no hay datos de voz en chanka. Se ajusta con las voces de las familias y se mide con una voz que el modelo nunca escuchó | por hacer · Ricardo |
| F2 | **Detectar el idioma solo** | Quechua o castellano en cada turno, sin botones. `facebook/mms-lid-512` incluye `quy` y `spa` (verificado 23-oct); precisión por medir | por hacer · Ricardo |
| F3 | **Entender lo que quiso decir** | Claude limpia la voz de la enfermera y el texto ruidoso del quechua, sin inventar ni quitar datos | por hacer · Freddy |
| F4 | **Auditar antes de hablar** | Retraducción a ciegas + comparación por código | ✅ construido, 20 pruebas · `app/rimay/` |
| F5 | **Hablar quechua** | Voz chanka de Meta (`facebook/mms-tts-quy`), ajustada con la voz de la mamá de Freddy | voz base probada 23-oct · `muestras/` |
| F6 | **«¿Me lo repite?»** | Comparar lo repetido con la indicación | por hacer · Freddy |
| F7 | **Mejora con el uso** | Cada corrección de la enfermera entra al glosario y a los datos del siguiente ajuste | por hacer |
| F8 | **Evaluación chanka-salud** | Claude vs Google Translate en indicaciones reales, calificado por la enfermera (método Kong et al., 2026) | por hacer · Freddy + mamá |

---

## 3. Lo técnicamente difícil (lo que ve el jurado)

Tres números, medidos con honestidad, aunque salgan malos:
1. **Errores al entender chanka hablado**: modelo de Meta tal cual → + vocabulario de la posta → + ajuste fino con las familias. Medido con una persona que no está en el entrenamiento.
2. **Errores al traducir al chanka**: Claude contra Google Translate, calificados por la enfermera.
3. **Errores que la auditoría atrapa** antes de que Rimay hable.

Más: precisión de la detección de idioma, y la espera por turno.

---

## 4. Tecnología

| Pieza | Qué usamos | Estado |
|---|---|---|
| Traducir, entender, auditar | Claude (`claude-opus-5`) vía SDK de Python, salida estructurada | auditoría hecha |
| Entender voz quechua | Meta Omnilingual ASR `quy` + vocabulario KenLM + ajuste fino | sábado |
| Entender voz castellano | Por decidir (Whisper u Omnilingual `spa`) | sábado |
| Detectar idioma | `facebook/mms-lid-512` limitado a `quy`/`spa` | sábado |
| Hablar quechua | `facebook/mms-tts-quy` ajustado (VITS) | base probada |
| Hablar castellano | Por decidir (Cartesia es candidato, y abre su track) | sábado |
| Entrenar y servir los modelos | VM de Ricardo, GPU de 40 GB | probar hoy |
| App | Web en el celular, micrófono y parlante | sábado |

Licencias: Omnilingual y Siminchik libres; MMS-TTS y MMS-LID no comerciales (bien para el hackathon). Detalle: `research/voz-quechua-modelos.md`.

---

## 5. Equipo

| Freddy | Ricardo | Familias |
|---|---|---|
| Claude: entender, traducir, auditar, «¿me lo repite?» · app · evaluación chanka con su mamá · pitch y Devpost | Datos de voz · reconocimiento (pasos 0-1-2) · detección de idioma · voz de Rimay · métricas y gráficos | Graban frases de posta y respuestas libres en chanka · la mamá de Freddy transcribe, revisa el glosario y califica |

Protocolo de grabación: `plan/recoleccion-de-voz.md`. Calendario hora por hora: `plan/plan-completo.md`.

---

## 6. Registro de decisiones

| # | Cuándo (PT) | Decisión | Por qué |
|---|---|---|---|
| D1 | vie 18:30 | Track principal: Anthropic «Claude for Public Benefit» | Freddy y Ricardo son peruanos; el track premia una comunidad concreta |
| D2 | vie 19:30 | Repo en la cuenta personal `Freddyx14/cal-hacks`, Ricardo invitado | No es un cliente de Loopmind |
| D3 | vie 20:20 | Se descarta incendios | La detección ya la resuelve Satellites on Fire (US$2.7M) |
| D4 | vie 21:10 | Rumbo: quechua en salud | La mamá de Freddy es la única enfermera quechuahablante de la posta de Pilpichaca |
| D5 | vie 22:40 | Ajuste fino de voz con las familias, medido antes y después | Padres de Freddy y papá de Ricardo hablan chanka; da el núcleo técnico |
| D6 | vie 23:08 | Rimay sobre corredores de extorsión | El propio análisis de Ricardo mostró que el modelo de escalamiento no le gana al baseline |
| D7 | vie 23:08 | El entrenamiento corre en la VM de Ricardo (GPU 40 GB) | Confirmado que es memoria de GPU |
| D8 | vie 23:33 | Salud general, no solo gestantes | Más voces familiares = más datos; la comunidad es la posta, no una condición |
| D9 | vie 23:41 | **Usuaria principal: el personal de salud**, no el paciente | Lo usan en la consulta, cara a cara |
| D10 | vie 23:41 | **App de intérprete con voz en los dos sentidos**, no WhatsApp | Conversación en vivo; la enfermera habla, Rimay habla en quechua, el paciente responde |
| D11 | vie 23:41 | **Detección automática de idioma** en cada turno | Nadie debería tocar un botón para cambiar de idioma |
| D12 | vie 23:41 | **Entender la intención, estilo Wispr Flow** | Que lo dicho a medias llegue claro de los dos lados |
| D13 | vie 23:50 | Este archivo es la fuente de verdad; la página visual se sincroniza con él | Pedido de Freddy |

---

## 7. Por decidir (con recomendación)

| # | Pregunta | Recomendación | Quién decide |
|---|---|---|---|
| P1 | ¿App web o nativa? | **Web en el celular**: misma experiencia, ahorra el día que cuesta compilar y firmar una app | Freddy + Ricardo |
| P2 | ¿Qué modelo de Claude en la conversación? | Medir la espera el sábado. Si Opus tarda mucho por turno, uno más rápido para limpiar y Opus para la auditoría | Freddy |
| P3 | ¿Voz en castellano? | Cartesia si suena bien y la espera es baja (suma su track); si no, la del sistema | Freddy |
| P4 | Nombre final | «Rimay» es de trabajo; decidirlo con la mamá de Freddy | Freddy |

---

## 8. Riesgos

| Riesgo | Qué hacemos |
|---|---|
| El paciente habla libre, no frases de posta | Grabar respuestas espontáneas; si Rimay no entiende, lo dice y pide repetir, nunca inventa |
| Espera por turno de varios segundos | Medir por paso; recortar donde más tarde |
| Mezcla de idiomas en una misma frase | Normal en la posta; se mide aparte |
| La enfermera confía a ciegas | La pantalla siempre muestra lo que Rimay entendió y lo que va a decir |
| Una dosis mal traducida | La auditoría (F4) bloquea antes de hablar |

---

## 9. Mapa de documentos

| Archivo | Qué es | ¿Vigente? |
|---|---|---|
| **`SOT.md`** | Esta fuente de verdad | ✅ |
| `plan/rimay-visual.html` | Página visual, sincronizada con SOT | ✅ si la versión coincide |
| `plan/plan-completo.md` | Calendario hora por hora y plan de recortes | ✅ el calendario; lo de producto, ver SOT |
| `plan/recoleccion-de-voz.md` | Protocolo de grabación para las familias | ✅ |
| `ideas/producto.md` | Producto v1 (WhatsApp, gestantes) y su evidencia | ⚠️ la evidencia sí; el producto, no |
| `research/*` | Investigación con fuentes | ✅ |
| `ideas/criterios.md` | Hoja para medir ideas | ✅ |
| Resto de `ideas/` y `Ricardo-idea/` | Historia de cómo llegamos aquí | Solo referencia |
