# Rimay — fuente de verdad (SOT)

> **Versión SOT-4 · sábado 24 de octubre de 2026, 00:20 PT**
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
| **Forma** | **App nativa de iOS**, instalada por TestFlight con la cuenta Apple Developer de Freddy. Los modelos de voz corren en la GPU de Ricardo |
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
| Entender voz castellano | Por decidir: medir Whisper contra Omnilingual `spa` (o el de Cartesia, si tiene) | sábado |
| Detectar idioma | `facebook/mms-lid-512` limitado a `quy`/`spa` | sábado |
| Hablar quechua | `facebook/mms-tts-quy` ajustado (VITS) | base probada |
| Hablar castellano | **Cartesia** (con sus créditos; suma su track) | sábado |
| Entrenar y servir los modelos | VM de Ricardo, GPU de 40 GB | probar hoy |
| App | **iOS nativa con Expo (React Native) + EAS Build → TestFlight**. Plan B: correrla en el iPhone de Freddy con Expo | sábado |
| Conexión app ↔ modelos | La VM de Ricardo expuesta por **HTTPS** (iOS no permite HTTP plano) | sábado temprano |

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
| D14 | sáb 00:14 | **App nativa de iOS por TestFlight** | Freddy tiene la cuenta Apple Developer; se muestra como app de prueba |
| D15 | sáb 00:14 | **El modelo de Claude se elige midiendo**: velocidad y acierto en el mismo set de prueba, y se queda uno | En una conversación en vivo la espera importa tanto como el acierto |
| D16 | sáb 00:14 | **Cartesia para la voz en castellano** | Sus créditos y su track |
| D17 | sáb 00:14 | **Avatar** que presenta Rimay y lo hace cercano | Más familiar para el paciente; lo pidió Freddy (ver §10) |
| D18 | sáb 00:14 | **La mamá de Freddy prueba por videollamada y, si puede, aparece en el pitch** | Usuaria real, voz real |

---

## 7. Por decidir (con recomendación)

| # | Pregunta | Recomendación | Estado |
|---|---|---|---|
| P1 | ¿App web o nativa? | — | ✅ cerrada: nativa iOS (D14) |
| P2 | ¿Qué modelo de Claude en la conversación? | Medir `claude-opus-5`, `claude-sonnet-5` y `claude-haiku-4-5` en el mismo set: segundos por turno y errores atrapados. Quedarse con el más rápido que no pierda acierto en la auditoría | abierta · se decide el sábado con números (D15) |
| P3 | ¿Voz en castellano? | — | ✅ cerrada: Cartesia (D16) |
| P4 | Nombre final | Ver lista abajo; decidirla con la mamá de Freddy | abierta |
| P5 | ¿Cómo es el avatar? | Ver §10 | abierta · Freddy |
| P6 | ¿La mamá de Freddy puede el domingo de 12:30 a 14:30 (hora de Lima)? | Preguntarle hoy | abierta · Freddy |

### Nombres propuestos (P4)
⚠️ **El significado y la escritura en chanka los confirma la mamá de Freddy.** No se usa ninguno en público sin eso.

| Nombre | Lo que entendemos que significa | Por qué podría servir |
|---|---|---|
| **Rimay** | hablar | Corto, dice lo que hace. El favorito de Freddy |
| **Rimanakuy** | conversar, hablar entre dos | Justo lo que pasa: una conversación de ida y vuelta |
| **Uyariy** | escuchar | Pone el foco en entender al paciente |
| **Chaski** | mensajero (los corredores del Tawantinsuyu) | Lleva el mensaje de un lado al otro; fácil de recordar fuera del Perú |
| **Yanapay** | ayudar | Cálido, pero menos específico |
| **Tinkuy** | encuentro | Dos idiomas que se encuentran; pero en algunos lugares es también un combate ritual, confirmar |

## 8. Riesgos

| Riesgo | Qué hacemos |
|---|---|
| El paciente habla libre, no frases de posta | Grabar respuestas espontáneas; si Rimay no entiende, lo dice y pide repetir, nunca inventa |
| Espera por turno de varios segundos | Medir por paso; recortar donde más tarde |
| Mezcla de idiomas en una misma frase | Normal en la posta; se mide aparte |
| La enfermera confía a ciegas | La pantalla siempre muestra lo que Rimay entendió y lo que va a decir |
| Una dosis mal traducida | La auditoría (F4) bloquea antes de hablar |
| TestFlight tarda en procesar el build | Subir el primer build el sábado temprano; plan B: la app en el iPhone de Freddy con Expo |
| La app no llega a la VM | HTTPS público para la VM desde el sábado temprano; probarlo antes de construir encima |
| El wifi del evento falla en el jurado | Video de la demo grabado el domingo temprano; datos del celular como respaldo |
| El avatar se come el tiempo del núcleo | Va después de la conversación completa; si a las 18:00 no está el núcleo, el avatar queda estático |
| Datos de pacientes reales | No se graban pacientes. Solo familia y personal con su consentimiento |

---

## 10. El avatar (D17)

**Para qué sirve:** que el paciente sepa con quién está hablando y le tenga confianza. Rimay se presenta solo, en
quechua: «Allillanchu. Ñuqam Rimay kani…» *(texto a confirmar con la mamá de Freddy)*, y explica que va a ayudar a la
enfermera a entenderle.

**Lo que puede hacer el avatar en la app:**
| Estado | Qué hace | Para qué |
|---|---|---|
| Presentarse | Saluda y explica qué es, en quechua | Primera consulta: confianza |
| Escuchando | Se inclina, ondas de sonido | El paciente sabe que puede hablar |
| Pensando | Gesto breve | Cubre la espera de los modelos |
| Hablando | Boca que se mueve con el audio | Se ve quién habla |
| No entendí | Gesto de duda, pide repetir | Nunca inventa (F3) |

**Opciones de diseño, a decidir con la mamá de Freddy (P5):**
1. **Personaje humano**: una técnica o promotora de salud andina, con ropa de posta. Lo más cercano, pero el riesgo es caer en un estereotipo.
2. **Animal andino** (vicuña, alpaca, cuy): juguetón y neutro, gusta a niños y adultos mayores; el riesgo es que se sienta infantil para un adulto.
3. **Forma abstracta con textil andino** (un círculo con iconografía de tejido que late al hablar): elegante, sin estereotipo; menos «personaje».

**Recomendación:** opción 2 o 3, **co-diseñada con la mamá de Freddy**, que sabe cómo lo recibirían sus pacientes.
Se genera la imagen base con IA, se anima con estados simples en la app (sin video pesado), y la boca se mueve
con el volumen del audio. **Va después de la conversación completa**: es lo que se recorta primero si el núcleo no está.

## 11. Pendientes

### Esta noche, antes de dormir (5 minutos cada uno)
- [ ] **Freddy:** mensaje a la familia con `plan/recoleccion-de-voz.md` + pedido de consentimiento por WhatsApp
- [ ] **Freddy:** preguntarle a su mamá si puede videollamada el sábado (prueba) y el domingo 12:30–14:30 hora de Lima (pitch)
- [ ] **Freddy:** mandarle `muestras/mms-tts-quy/todas.wav` y la lista de nombres (P4)
- [ ] **Los dos:** reclamar los créditos de Claude ($50 cada uno) y los de Cartesia
- [ ] **Ricardo:** confirmar que la VM descarga y corre Omnilingual `quy`, `mms-lid-512` y `mms-tts-quy`
- [ ] **Dormir a la 1:00**

### Sábado, en este orden
| PT | Qué | Quién |
|---|---|---|
| 05:00–08:00 | Las familias graban (7–10 AM en Perú) | Familias |
| 07:30 | Recibir audios, convertir, separar al hablante de prueba | Ricardo |
| 07:30 | Crear la app (Expo), probar micrófono y parlante en el iPhone, **primer build a TestFlight** | Freddy |
| 08:30 | **VM con HTTPS público**; la app manda un audio y recibe texto | Ricardo + Freddy |
| 09:00 | Paso 0 y paso 1 del reconocimiento → primer número | Ricardo |
| 09:00 | Cartesia: voz en castellano en la app | Freddy |
| 10:30 | Medir modelos de Claude (P2): velocidad y acierto | Freddy |
| 12:30 | Workshop de Anthropic | Freddy |
| 13:30 | Paso 2 (ajuste fino) + detección de idioma medida | Ricardo |
| 13:30 | Turno completo enfermera → paciente en la app | Freddy |
| 16:00 | Turno paciente → enfermera + «¿me lo repite?» | Freddy + Ricardo |
| 17:00 | **Videollamada con la mamá de Freddy**: prueba real con la app | Los dos |
| 18:00 | **Conversación completa en los dos sentidos.** Si no está, se recorta | Los dos |
| 18:00 | Avatar (solo si lo anterior está) | Freddy |
| 21:00 | Borrador en Devpost, repo público sin `context/photos/`, README con lo de Cartesia | Freddy |
| 22:00 | Ensayo del pitch | Los dos |

### Domingo
| PT | Qué |
|---|---|
| 05:00 | Arreglos finales; **grabar el video de la demo** (respaldo si falla el wifi) |
| 07:00 | Se congelan los números |
| 08:00 | Devpost final |
| 09:00 | **Entrega** |
| 10:30–12:30 | Jurado, los dos en la mesa; la mamá de Freddy por videollamada si puede |

## 12. Mapa de documentos

| Archivo | Qué es | ¿Vigente? |
|---|---|---|
| **`SOT.md`** | Esta fuente de verdad | ✅ |
| `plan/rimay-visual.html` | Página visual, sincronizada con SOT | ✅ si la versión coincide |
| `plan/plan-completo.md` | Plan de recortes y medición | ⚠️ el calendario nuevo está en SOT §11 |
| `plan/recoleccion-de-voz.md` | Protocolo de grabación para las familias | ✅ |
| `ideas/producto.md` | Producto v1 (WhatsApp, gestantes) y su evidencia | ⚠️ la evidencia sí; el producto, no |
| `research/*` | Investigación con fuentes | ✅ |
| `ideas/criterios.md` | Hoja para medir ideas | ✅ |
| Resto de `ideas/` y `Ricardo-idea/` | Historia de cómo llegamos aquí | Solo referencia |
