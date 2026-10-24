# Rimay — plan completo para Cal Hacks 13.0

> Versión del viernes 23 de octubre, 23:00 PT. Entrega: **domingo 25, 9:00 AM PT** (quedan ~34 h).
> Qué es el producto: `ideas/producto.md` · evidencia: `research/papers.md` · voz: `research/voz-quechua-modelos.md`
> · recolección: `plan/recoleccion-de-voz.md` · criterios: `ideas/criterios.md`.

---

## 1. En una página

**Qué construimos.** Rimay lleva las indicaciones de la posta a la casa de la gestante, **en quechua chanka y en
audio**, y comprueba que las entendió. Si no entendió, avisa a la enfermera.

**Para quién.** Las gestantes quechuahablantes de la posta de Pilpichaca (Huancavelica), donde la mamá de Freddy es la
única enfermera que habla quechua.

**Lo técnicamente difícil, en una frase.** Una IA que **sabe cuándo se equivoca** en un idioma que casi no conoce:
1. La primera **evaluación pública de IA en chanka para salud**.
2. Un **detector de errores de traducción** que se mide contra esa evaluación.
3. **Reconocimiento y síntesis de voz en chanka ajustados a la posta**, con voces de nuestras familias, medidos con una voz que el modelo nunca escuchó.
4. **Lectura de la receta** que se abstiene cuando no está segura.

**Lo que va en la página y en el pitch.** Tres números:
- errores de reconocimiento de voz antes y después del ajuste,
- errores de traducción de Claude contra Google Translate, calificados por una enfermera quechuahablante,
- cuántos de esos errores atrapa el detector antes de que lleguen a una paciente.

**Tracks.** Anthropic (principal) · Best People-First · Microsoft «Built for the Real World» (una lámina).

> ⚠️ Pendiente de confirmar entre Freddy y Ricardo: que Rimay reemplaza la propuesta de corredores de extorsión
> (`Ricardo-idea/`). Este plan asume que sí.

---

## 2. Quién hace qué

| | Freddy | Ricardo | Familia (Perú) |
|---|---|---|---|
| **Datos** | Recibe y ordena los audios de WhatsApp | Convierte, segmenta, arma los conjuntos | Graban y la mamá de Freddy transcribe |
| **Voz** | — | Reconocimiento (Omnilingual + vocabulario + ajuste fino) y voz de Rimay (MMS-TTS) | La mamá de Freddy califica la voz a ciegas |
| **Claude** | Traducción, retraducción, detector de errores (T2), «¿me lo repites?», lectura de receta | Mide el detector contra la evaluación | — |
| **Evaluación chanka (T1)** | Arma las indicaciones de prueba y corre Claude y Google | Métricas y gráficos | La mamá de Freddy califica exactitud y riesgo |
| **Producto** | WhatsApp, panel de la enfermera, página de resultados | Gráficos de la página | — |
| **Pitch** | Guion, Devpost, video | Diapositiva técnica, respuestas técnicas | Nota de voz de la mamá (si acepta) |

**El punto de encuentro entre los dos:** el formato de los datos (`{persona, bloque, numero, audio, transcripcion}`) y
una función `entender(audio) → texto` que el lado de Claude llama. Desde ahí cada uno avanza por su lado.

---

## 3. Lo que se construye (piezas)

| # | Pieza | Qué hace | Si sale mal |
|---|---|---|---|
| P1 | **Recolección** | Audios de la familia → 16 kHz mono, nombrados y transcritos | Usar solo lo que llegue; el set de prueba se protege primero |
| P2 | **Reconocimiento de voz** | Paso 0 línea base → paso 1 vocabulario de salud (KenLM + palabras clave) → paso 2 ajuste fino | Quedarse en el paso 1, que ya mejora y cuesta minutos |
| P3 | **Voz de Rimay** | MMS-TTS `quy` ajustado con la voz de la mamá de Freddy | Audios pregrabados por ella para lo fijo (señales de alarma) |
| P4 | **Traducción con auditoría** | Claude traduce al chanka con glosario, retraduce y compara los datos críticos | Si hay duda, no se envía y se avisa a la enfermera |
| P5 | **Lectura de receta** | Foto → medicamento, dosis, frecuencia, con abstención si no está seguro | La enfermera escribe la indicación a mano |
| P6 | **«¿Me lo repites?»** | Respuesta de voz → texto → ¿están los conceptos clave? | Respuesta cerrada («¿cada cuántas horas?») si el reconocimiento no alcanza |
| P7 | **WhatsApp** | Envía audio y texto, recibe la nota de voz | Número de prueba de Meta Cloud API; plan B, simulador en la página |
| P8 | **Panel de la enfermera** | A quién se envió qué, quién entendió, a quién llamar | Una sola pantalla, sin login |
| P9 | **Página de resultados** | Los tres números con sus gráficos y el método | Es lo último que se cae: los números valen aunque falle la demo |

**Fuera de alcance este fin de semana:** otras lenguas (aimara, asháninka), otros servicios del hospital, diagnóstico,
funcionamiento sin señal. Van en el pitch como «siguiente paso».

---

## 4. Calendario hora por hora

Perú (Lima) va **2 horas adelante** de California.

### Viernes 23 (esta noche)
| PT | Qué | Quién |
|---|---|---|
| 23:00 | Mensaje a la familia: protocolo, frases en castellano, pedir consentimiento | Freddy |
| 23:00 | Preparar el entorno: probar si el ajuste fino corre en la VM (¿tiene GPU?) y en la M5; Colab como respaldo | Ricardo |
| 23:30 | La mamá de Freddy escucha 5 audios de la voz chanka de Meta: ¿se entiende? | Freddy |
| 23:30 | Línea base del reconocimiento con los datos públicos (`josemercado/quechua-chanka-asr`, solo evaluación) | Ricardo |
| 00:00 | Primer flujo de Claude: castellano → chanka → retraducción, en consola | Freddy |
| **01:00** | **Dormir.** Mañana es el día largo | Los dos |

### Sábado 24
| PT | Qué | Quién |
|---|---|---|
| 05:00–08:00 (07:00–10:00 en Perú) | **La familia graba** bloques A y B | Familia |
| 07:30 | Despertar. Recibir audios, convertir, nombrar | Freddy + Ricardo |
| 08:30 | La mamá de Freddy transcribe; separar **ya** al hablante de prueba | Familia + Ricardo |
| 09:00 | Paso 1 del reconocimiento: KenLM + palabras clave → primer número | Ricardo |
| 09:00 | WhatsApp funcionando: enviar audio, recibir nota de voz | Freddy |
| 11:00 | Evaluación chanka (T1): 30–50 indicaciones, Claude vs Google, a la mamá para calificar | Freddy |
| 12:30–13:30 | **Workshop de Anthropic** (agentes y equipos multiagente, The Theater). Ir al menos uno | Freddy |
| 13:30 | Paso 2: ajuste fino del reconocimiento | Ricardo |
| 13:30 | Detector de errores (T2) + lectura de receta | Freddy |
| 16:00 | Ajuste de la voz de Rimay con la voz de la mamá | Ricardo |
| 16:00 | «¿Me lo repites?» conectado al reconocimiento de Ricardo | Freddy |
| 18:00 | **Flujo completo de punta a punta**, aunque sea feo | Los dos |
| 19:00 | Panel de la enfermera + página de resultados | Freddy |
| 19:00 | Validación rotando hablantes, gráficos | Ricardo |
| 21:00 | **Borrador en Devpost** (la guía lo recomienda), repo público sin `context/photos/` | Freddy |
| 22:00 | Ensayar el pitch una vez | Los dos |
| **00:00** | **Dormir 4–5 horas** | Los dos |

### Domingo 25
| PT | Qué | Quién |
|---|---|---|
| 05:00 | Arreglos finales, grabar el video de la demo | Los dos |
| **07:00** | **Congelar los números.** Lo que no esté medido, no entra | Los dos |
| 08:00 | Devpost final, README, enlaces | Freddy |
| **09:00** | **Entrega** | |
| 10:30–12:30 | Jurado. Los dos en la mesa todo el tiempo | Los dos |

**Regla de recorte:** si a las 18:00 del sábado el flujo completo no anda, se corta en este orden:
1. lectura de receta (P5),
2. voz ajustada (P3, se usan los audios grabados),
3. paso 2 del reconocimiento (queda el paso 1).

Lo que **nunca** se corta: la evaluación chanka (T1) y los números honestos.

---

## 5. La medición (lo que va en la página)

### Reconocimiento de voz
| Paso | Qué es | Métricas |
|---|---|---|
| 0 | Omnilingual ASR `quy`, sin tocar | CER, WER, % conceptos clave |
| 1 | + vocabulario de la posta (KenLM) + palabras clave | ídem |
| 2 | + ajuste fino con las voces de la familia | ídem |

Todo medido sobre **una persona que no está en el entrenamiento**. Si hay tiempo, rotando y promediando.

### Voz de Rimay
- **Ida y vuelta**: Rimay habla, el reconocimiento transcribe, se compara.
- **Prueba a ciegas**: la mamá de Freddy califica de 1 a 5, mezclando audios sintéticos y reales.

### Traducción (T1) y detector (T2)
- Método de Kong et al. (2026): indicaciones reales → Claude y Google Translate → retraducción → la enfermera califica **exactitud** y **riesgo de daño**.
- Detector: de los errores que encontró la enfermera, **¿cuántos atrapó Rimay antes de enviar?** (sensibilidad), y **¿cuántas falsas alarmas dio?**

### Los tres números del pitch
1. *«Bajamos los errores al entender chanka hablado de X% a Y%.»*
2. *«Claude se equivoca en X de cada 10 indicaciones médicas en chanka; Google en Y.»*
3. *«Rimay atrapa X de cada 10 de esos errores antes de que lleguen a una paciente.»*

Si un número sale malo, **se muestra igual**. Es la respuesta honesta a «¿dónde falla Claude?», que es lo que pide Anthropic.

---

## 6. El pitch (3 minutos + 2 de preguntas)

| Tiempo | Qué |
|---|---|
| 0:00 | **Frase en chanka** al jurado (una señal de alarma real; texto y audio de la mamá de Freddy). «¿Entendieron?» |
| 0:20 | «Les acabo de decir [traducción]. En Pilpichaca, mi mamá es la única enfermera que habla quechua. Cuando no está, esto se pierde.» Cifra: 52 servidores bilingües en toda Huancavelica |
| 0:45 | Demo en vivo: la enfermera escribe, foto de la receta, el celular recibe el audio en chanka, una voz responde a medias, aparece el aviso «no entendió cuándo volver» |
| 1:45 | Lo técnico: los tres números, y que se midió con una voz que el modelo nunca escuchó |
| 2:30 | Dónde falla y qué hicimos. Siguiente paso: aimara, asháninka, hospitales; solo hace falta una revisora nativa |
| 2:50 | Cierre con la voz de la mamá de Freddy (si acepta) |

---

## 7. Riesgos y qué hacemos

| Riesgo | Señal temprana | Plan B |
|---|---|---|
| La familia no alcanza a grabar | A las 09:00 PT hay menos de 300 audios | Usar los datos públicos para entrenar y la familia solo para la prueba |
| La VM no tiene GPU | Ricardo lo sabe esta noche | M5 para inferencia y vocabulario (paso 1); Colab o una GPU de ASUS para el paso 2 |
| La voz de Meta no se entiende | La mamá de Freddy lo dice esta noche | Audios grabados por ella para todo lo fijo |
| El reconocimiento no entiende las respuestas | CER muy alto en el paso 1 | Preguntas cerradas en el «¿me lo repites?» |
| WhatsApp no aprueba el número | El sábado a las 10:00 no envía | Simulador de chat en la página |
| Cansancio | — | Dormir las horas del calendario. Un número honesto a las 7:00 vale más que una función más a las 4:00 |

---

## 8. Checklist de esta noche

- [ ] Freddy: mensaje a la familia con `plan/recoleccion-de-voz.md`, la lista de frases en castellano y el pedido de consentimiento
- [ ] Freddy: la mamá escucha 5 audios de `facebook/mms-tts-quy` y opina
- [ ] Freddy: conseguir la lista oficial de señales de alarma del MINSA (o que la mamá diga cuál usan en la posta)
- [ ] Ricardo: ¿la VM de 40 GB tiene GPU? Si es solo RAM, el ajuste fino va a Colab o a ASUS
- [ ] Ricardo: probar Omnilingual ASR `quy` en la M5 o la VM con un audio
- [ ] Los dos: confirmar que vamos con Rimay y no con los corredores de extorsión
- [ ] Reclamar los $50 de créditos de Claude cada uno (QR de la lámina, correo de Cal Hacks)
