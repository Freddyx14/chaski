# Voz en quechua chanka. Qué existe, qué se puede entrenar y qué plan es realista para el domingo

> Investigación técnica del viernes 23 de octubre de 2026, ~22:40 PT. Deadline de Cal Hacks el domingo 25 de octubre, 09:00 PT (~34 h).
> Producto: asistente de WhatsApp para el puesto de salud de Pilpichaca (Huancavelica) que manda instrucciones en AUDIO en quechua chanka (`quy`) a gestantes y entiende su respuesta hablada (teach-back).
> Regla de este documento. Toda afirmación lleva su URL. Lo que no pude comprobar dice **no verificado**.

---

## 0. La descomposición antes de elegir modelos

El problema se reduce a dos cosas, y ninguna de las dos es "TTS y ASR de propósito general en quechua".

1. **Hablarle.** El conjunto de instrucciones es finito y lo escribe el puesto de salud (signos de alarma, controles, sulfato ferroso, plan de parto). Lo dinámico es poco: nombre, fecha, hora, número de semanas. Un set finito se puede **grabar con la voz real de la enfermera**, que suena mejor que cualquier síntesis y no tiene problema de licencia. La síntesis solo hace falta para las piezas dinámicas o para frases nuevas.
2. **Entenderla.** Teach-back no necesita transcripción perfecta. Necesita decidir si la gestante dijo de vuelta las 2 o 3 ideas clave de esa instrucción ("sangrado", "ir al puesto", "no esperar"). Eso es detección de conceptos esperados sobre una hipótesis ruidosa, y tolera un CER alto si las palabras clave salen bien.

Esto cambia lo que conviene entrenar: lo que más mueve la aguja es un ASR con sesgo de dominio (vocabulario de las instrucciones) y una métrica de "conceptos recuperados", no un TTS clonado.

---

## 1. TTS en quechua que existe hoy

### 1.1 Meta MMS-TTS (VITS, un checkpoint por idioma)

| Código | Variedad | Modelo | Licencia |
|---|---|---|---|
| `quy` | Quechua de Ayacucho (chanka) | [facebook/mms-tts-quy](https://huggingface.co/facebook/mms-tts-quy) | **CC-BY-NC 4.0** (model card) |
| `quz` | Quechua del Cusco | [facebook/mms-tts-quz](https://huggingface.co/facebook/mms-tts-quz) | CC-BY-NC 4.0 |
| `qve` | Quechua de Apurímac oriental | listado con TTS en la [tabla de cobertura MMS](https://dl.fbaipublicfiles.com/mms/misc/language_coverage_mms.html) | CC-BY-NC 4.0 |
| `que` | (macro-código) | **no existe** checkpoint `mms-tts-que` en la búsqueda del Hub ([API](https://huggingface.co/api/models?search=mms-tts-qu)) | — |

- Existen también `quh`, `qub`, `qul`, `quf`, `quw` y otros quechuas en el Hub ([búsqueda](https://huggingface.co/api/models?search=mms-tts-qu)).
- Corre en 🤗 Transformers ≥ 4.33, es VITS de ~83M parámetros, y es **no determinista** (fijar semilla) ([model card quy](https://huggingface.co/facebook/mms-tts-quy)).
- Calidad. Los datos de MMS vienen mayoritariamente de lecturas religiosas (paper MMS, [arXiv 2305.13516](https://arxiv.org/abs/2305.13516)). Que la voz de `quy` sea entendible para una hablante de Huancavelica **no está verificado**: hay que ponérsela a la enfermera el viernes en la noche, es la primera prueba del plan.

### 1.2 "Quechua Speech Synthesizers" (Huamán Curo et al., 2026, chanka)

- Capítulo de Springer, [DOI 10.1007/978-3-032-20322-9_12](https://link.springer.com/chapter/10.1007/978-3-032-20322-9_12). Variedad chanka (Andahuaylas, Ayacucho, Huancavelica), cuatro sistemas (Tacotron2+WaveNet, FastPitch+WaveGlow, VITS, XTTS v2), 2,300 grabaciones; XTTS v2 fue el mejor con MOS-N 4.9 y MOS-S 4.8 (según el resumen indexado por la búsqueda; la página de Springer redirige a login y no pude leer el capítulo).
- **¿Modelos o datos liberados?** No encontré repositorio de GitHub ni de Hugging Face asociado (búsquedas en web y en el Hub por "quechua", "chanka", "quy"). **No verificado que existan**; tratarlo como no disponible para el domingo. Un correo a los autores no llega a tiempo.

### 1.3 Otros trabajos de TTS quechua (útiles como receta, no como modelo listo)

- "Giving Voice to the Constitution" (LREC 2026 PoliticalNLP) entrena XTTS v2, F5-TTS y DiFlow-TTS en quechua **sureño/collao** con ~40 h curadas de Siminchik + Lurin; reporta UTMOS 3.22–3.31 y WER 0.16–0.19 del audio sintetizado. La versión de arXiv dice que liberarán datos "upon positive acceptance" y **no trae URL de checkpoints** ([arXiv 2604.13288](https://arxiv.org/html/2604.13288)).
- Un artículo en Frontiers in Robotics and AI (2026) fine-tunea XTTS-v2 para quechua sureño (Cusco-Puno, `qxp`) sobre un corpus de 30.5 h y 77 hablantes publicado en CC0 en Mozilla Data Collective; el entrenamiento tomó ~8–9 h en una A100 40GB, 15 épocas ([Frontiers](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1909076/full)). No reporta checkpoint descargable. **Es otra variedad**, no chanka.
- En el Hub hay intentos comunitarios sin documentación ni licencia: [gmezan/vits-quechua](https://huggingface.co/gmezan/vits-quechua) (subido el 21-oct-2026, card vacía), [pollitoconpapass/quz-tts-model](https://huggingface.co/pollitoconpapass/quz-tts-model) (cusqueño), `ittailup/parler-tts-mini-v0.1-quechua` ([búsqueda](https://huggingface.co/api/models?search=quechua)). Ninguno es chanka verificado.

### 1.4 APIs comerciales

| Servicio | ¿Quechua? | Fuente |
|---|---|---|
| ElevenLabs TTS (v3, Multilingual v2, Flash v2.5) | **No** | [docs de modelos](https://elevenlabs.io/docs/overview/models) |
| ElevenLabs STT (Scribe v2) | **No** | [docs STT](https://elevenlabs.io/docs/capabilities/speech-to-text) |
| Azure Speech (STT y TTS) | **No** | [language support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=stt) |
| Google Cloud STT v2 (Chirp, Chirp 2, Chirp 3) | **No** (tampoco aymara ni guaraní) | [supported languages](https://docs.cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages) |
| Google Cloud TTS | **no verificado** (la página de voces carga por JS, no pude leerla) | [list voices](https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types) |
| Cartesia | **no verificado** | — |

Conclusión: ninguna API comercial verificada sirve. El camino es abierto.

### 1.5 Clonación de voz de la enfermera

- **XTTS v2.** Licencia Coqui Public Model License 1.0.0, solo uso no comercial, y Coqui cerró en enero de 2024, así que no hay a quién comprarle licencia ([localaimaster](https://localaimaster.com/blog/xtts-coqui-commercial-license)). No tiene quechua entre sus idiomas; usarlo exige fine-tune con un idioma "prestado" (español) para el tokenizador, que es lo que hacen los papers de arriba con decenas de horas. Con 30–60 min no hay evidencia publicada de calidad aceptable en quechua. **Riesgo alto para 34 h.**
- **F5-TTS.** Código MIT, pesos CC-BY-NC-4.0 por el dataset Emilia ([GitHub F5-TTS](https://github.com/swivid/f5-tts), [discusión de uso comercial](https://github.com/SWivid/F5-TTS/discussions/1295)). Clonación zero-shot cruzada de idioma existe como línea de investigación ([Cross-Lingual F5-TTS, arXiv 2509.14579](https://arxiv.org/pdf/2509.14579)), pero la pronunciación de un idioma no visto en el preentrenamiento es el punto débil. **No verificado** para quechua.
- **MMS-TTS `quy` + fine-tune con la voz de la enfermera.** Es la opción más barata y con receta probada (ver §3.2).

---

## 2. STT/ASR para quechua

### 2.1 Whisper

- **No soporta quechua.** La lista de idiomas de `whisper/tokenizer.py` no contiene "quechua" ni el código `qu` (revisado con grep sobre [tokenizer.py](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py)).
- Hay fine-tunes comunitarios, casi todos cusqueños y sobre la Biblia, por ejemplo [pollitoconpapass/whisper-small-cuzco-quechua](https://huggingface.co/pollitoconpapass/whisper-small-cuzco-quechua) (Apache-2.0, validation loss 0.0002, sin WER reportado, señal de sobreajuste al dominio bíblico).

### 2.2 Meta Omnilingual ASR (noviembre 2025). **El hallazgo más importante**

- 1,600+ idiomas, **Apache 2.0** para código y modelos ([README](https://github.com/facebookresearch/omnilingual-asr)).
- Soporta `quy_Latn`, `quz_Latn`, `qve_Latn`, `quh_Latn`, `qxu_Latn` ([lang_ids.py](https://github.com/facebookresearch/omnilingual-asr/blob/main/src/omnilingual_asr/models/wav2vec2_llama/lang_ids.py)).
- Tabla oficial por idioma del modelo 7B LLM-ASR ([CSV](https://github.com/facebookresearch/omnilingual-asr/blob/main/per_language_results_table_7B_llm_asr.csv)):

| Idioma | Horas de entrenamiento | CER |
|---|---|---|
| `quy_Latn` (chanka) | **174.2 h** | **2.7** |
| `quz_Latn` (cusqueño) | 141.2 h | 0.2 |
| `qve_Latn` | 29.6 h | 0.2 |

  ⚠️ Un CER de 0.2 es irreal en habla espontánea; casi seguro el test es habla leída del mismo dominio que el entrenamiento. Hay que esperar un CER bastante peor en notas de voz de WhatsApp de una gestante rural. Por eso se mide (§4).
- Tamaños: CTC 300M (~2 GiB VRAM), 1B (~3 GiB), 3B (~8 GiB), 7B (~15 GiB), con versiones `_v2` mejoradas ([README](https://github.com/facebookresearch/omnilingual-asr)). Solo acepta audios < 40 s, perfecto para notas de voz.
- El pipeline LLM-ASR acepta "context examples" (ejemplos audio-texto en contexto) según el README; sirve para sesgarlo con frases de la enfermera **sin entrenar**. Detalle de uso en el [README de inferencia](https://github.com/facebookresearch/omnilingual-asr/blob/main/src/omnilingual_asr/models/inference/README.md) (no lo probé).
- Receta de fine-tune CTC publicada (fairseq2), con presets para idiomas de pocos recursos: `lr 1e-5`, `num_steps 5000`, `ctc-finetune-recommendation.yaml`; el paper dice que afinar los CTC chicos llega a competir con el 7B en el idioma afinado ([recipes README](https://github.com/facebookresearch/omnilingual-asr/blob/main/workflows/recipes/wav2vec2/asr/README.md)). Ojo, Meta usó 32 GPUs para el 300M; en una sola GPU hay que subir la acumulación de gradiente.
- Hay ports listos, incluyendo ONNX para sherpa-onnx y MLX/CoreML para Mac ([búsqueda en el Hub](https://huggingface.co/api/models?search=omnilingual)), útil si el GX10 da problemas.

### 2.3 Meta MMS-1B-all (adapters)

- Tiene adapter para `quy` y `quz` (y `qve`, `qvh`, `qvw`, `qxn`, etc.) según el model card ([facebook/mms-1b-all](https://huggingface.co/facebook/mms-1b-all)) y la [tabla de cobertura](https://dl.fbaipublicfiles.com/mms/misc/language_coverage_mms.html) (ASR ✔ para `quy`).
- Licencia **CC-BY-NC 4.0** ([model card](https://huggingface.co/facebook/mms-1b-all)).
- Referencia comunitaria: [cportoca/MMS_Quechua_finetuned_qve](https://huggingface.co/cportoca/MMS_Quechua_finetuned_qve), adapter afinado desde mms-1b-all, WER 0.32 en su evaluación (dataset no declarado).

### 2.4 AmericasNLP 2022 (wav2vec2 XLS-R)

- [ivangtorre/wav2vec2-xlsr-300m-quechua](https://huggingface.co/ivangtorre/wav2vec2-xlsr-300m-quechua): XLS-R 300M afinado con el train de AmericasNLP 2022, **CER 49.2** en test, CC-BY-4.0.
- El sistema ganador de la competencia llegó a CER 12.14 en quechua, con modelos n-gram y augmentación ([arXiv 2404.08368](https://arxiv.org/html/2404.08368)). Qué variedad tiene el quechua de AmericasNLP: **no verificado**.
- Hoy está superado por Omnilingual y MMS para nuestro caso.

### 2.5 Datasets de habla

| Dataset | Variedad | Tamaño | Licencia | Fuente |
|---|---|---|---|---|
| **Siminchik** | Sureño: **chanka (Ayacucho, Apurímac)** y collao (Cusco, Puno), radio espontánea | 97 h | CC-BY 4.0 | [LREC 2018](http://lrec-conf.org/workshops/lrec2018/W14/pdf/4_W14.pdf), [Zenodo](https://zenodo.org/records/3595354) |
| **Huqariq** | Quechua sureño y central, aymara, shipibo (crowdsourcing) | 220 h en total | no verificada | [arXiv 2207.05498](https://arxiv.org/html/2207.05498v1) |
| Common Voice | Puno (12 h scripted; 35.3 h espontáneo, 5.18 validadas), Santiago del Estero (12 h); 191 h quechuas en total | ver paper | CC0 | [arXiv 2510.13871](https://arxiv.org/abs/2510.13871) |
| Common Voice chanka (`quy`) | — | **no verificado que exista** | — | — |
| [josemercado/quechua-chanka-asr](https://huggingface.co/datasets/josemercado/quechua-chanka-asr) | chanka (según el nombre) | 500 clips, ~103 MB a 16 kHz (≈ 50 min, cálculo mío) | **sin licencia declarada** | card del Hub |
| [makitty/quechua-chanka-unified](https://huggingface.co/datasets/makitty/quechua-chanka-unified) | chanka, **texto** paralelo es↔quy (incluye el manual chanka de justicia del Ministerio de Cultura) | 100K–1M pares | CC-BY-4.0 | card del Hub |
| [Llamacha/monolingual-quechua-iic](https://huggingface.co/datasets/Llamacha/monolingual-quechua-iic) | texto monolingüe | — | no verificada | Hub |
| [facebook/omnilingual-asr-corpus](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus) | multilingüe; si trae `quy` **no verificado** (rate-limit del Hub) | — | CC-BY-4.0 | [README](https://github.com/facebookresearch/omnilingual-asr) |

---

## 3. ¿Qué se puede afinar en ~10–12 h de GPU?

### 3.1 ASR, adaptación de dominio

**a) Adapter MMS.** El blog oficial de Hugging Face afina un adapter de ~2.5M parámetros con ~4 h de turco de Common Voice, en menos de 30 min en una GPU, y llega a WER 0.28 a los 100 pasos y 0.223 a los 400; recomienda "strongly" adapters frente al fine-tune completo en idiomas de pocos recursos ([HF blog, mms_adapters](https://huggingface.co/blog/mms_adapters)). Para nosotros el adapter `quy` ya existe, así que se parte de él y se afina con audio de dominio. Cuántos minutos mínimos hacen falta para ganar sobre el adapter base: **no hay cifra publicada para quechua**. Con 30–60 min de la enfermera más Siminchik chanka es razonable esperar mejora en vocabulario de dominio; el riesgo es sobreajustar a una sola voz (por eso el held-out debe incluir otra voz si se puede).

**b) CTC + n-gram KenLM de dominio.** Lo más barato y con mejor retorno. En el ejemplo oficial de HF, agregar un 5-gram KenLM a wav2vec2 dio **30 % de mejora relativa de WER**, y construir el LM tomó ~2 min ([HF blog, wav2vec2-with-ngram](https://huggingface.co/blog/wav2vec2-with-ngram)). En quechua, con morfología aglutinante, conviene un LM **de caracteres o subpalabras** o un n-gram de palabras pequeño solo con las frases de dominio; el ganador de AmericasNLP probó n-gramas y le rindió más greedy con correcciones heurísticas ([arXiv 2404.08368](https://arxiv.org/html/2404.08368)). Se aplica igual sobre Omnilingual CTC y MMS (ambos CTC). Texto para el LM: las instrucciones de la enfermera, sus variantes de respuesta esperada, más texto chanka general de [makitty/quechua-chanka-unified](https://huggingface.co/datasets/makitty/quechua-chanka-unified).

**c) Hotwords / sesgo contextual.** `pyctcdecode` (el decoder del blog de arriba) acepta `hotwords` con peso ([README de pyctcdecode](https://github.com/kensho-technologies/pyctcdecode)). Para teach-back es exactamente lo que hace falta: subir el peso de las 20–40 palabras clave de las instrucciones. Además el LLM-ASR de Omnilingual acepta ejemplos en contexto (§2.2). Ganancia publicada para quechua: **no verificada**; se mide.

**d) Fine-tune CTC de Omnilingual.** Receta oficial existe (§2.2), Apache 2.0. En una GPU el 300M o el 1B son viables en pocas horas; el riesgo es de tooling (fairseq2), no de cómputo.

### 3.2 TTS

**MMS-TTS `quy` con [ylacombe/finetune-hf-vits](https://github.com/ylacombe/finetune-hf-vits).** El repo dice "as little as 80 to 150 samples" y "an excellent finetuned version ... in 20 minutes" en una GPU; el modelo tiene 83M parámetros. Requisito, convertir una vez el discriminador del checkpoint original de MMS con `convert_original_discriminator_checkpoint.py`. No encontré un checkpoint `mms-tts-quy-train` ya convertido ([búsqueda](https://huggingface.co/api/models?search=mms-tts-quy)). **Es la única ruta de TTS-con-su-voz que entra holgada en el tiempo.** Con 30–60 min de la enfermera hay 300–600 frases, muy por encima del mínimo del repo.

**XTTS v2 / F5-TTS.** La evidencia publicada para quechua usa 30–40 h y 8–9 h de A100 (§1.3), y la licencia es no comercial. Con 30–60 min no hay evidencia. Solo como experimento lateral de Ricardo si sobra GPU.

### 3.3 Texto médico en quechua

- MINSA, "Palabras clave para la atención en salud: Quechua" (salud materna y perinatal, salud sexual y reproductiva). Ficha en [gob.pe](https://www.gob.pe/institucion/minsa/informes-publicaciones/280806-palabras-clave-para-la-atencion-en-salud-quechua) (devolvió 418 al leerla); la edición **Cusco** está en el [Centro de Recursos del Ministerio de Cultura (PDF)](https://centroderecursos.cultura.pe/sites/default/files/rb/pdf/Palabras-Clave%20para%20la%20atencion%20en%20salud%20Quechua%20Cusco.pdf). Una edición **Ayacucho** aparece en [Scribd](https://es.scribd.com/document/526818308/Dokumen-tips-Palabras-Atencion-Salud-Clave-Quechua-Ayacucho) (copia de terceros, contenido no verificado).
- Manual del quechua chanka en la administración de justicia (Ministerio de Cultura, 2014), ya normalizado dentro de [makitty/quechua-chanka-unified](https://huggingface.co/datasets/makitty/quechua-chanka-unified) bajo CC-BY-4.0. Es dominio judicial, sirve para ortografía y morfología chanka, no para vocabulario médico.
- UNICEF u otros materiales de salud materna en chanka: **no verificado**.
- Lo más valioso del corpus de dominio lo produce la enfermera: el guion de instrucciones y 3–5 maneras en que una gestante respondería cada una.

---

## 4. Plan recomendado (viernes 22:40 PT → domingo 09:00 PT)

**Recomendación.** ASR con Omnilingual (`quy_Latn`, Apache 2.0) más sesgo de dominio, TTS con la voz real de la enfermera grabada, y MMS-TTS `quy` afinado con su voz como capa para lo dinámico. La métrica del demo es "conceptos recuperados en el teach-back", con CER/WER como soporte.

### Viernes en la noche (hasta ~01:00 PT)
1. **Prueba de oído, 15 min.** Generar 5 frases con `facebook/mms-tts-quy` y mandárselas a la enfermera por WhatsApp. ¿Se entiende? ¿Suena a chanka? Esto decide si MMS-TTS es base o descarte.
2. **Guion.** Con la enfermera, 15–25 instrucciones cortas (≤ 20 s cada una) en chanka escrito, cada una con 2–3 conceptos clave marcados, y 3–5 respuestas esperadas por instrucción.
3. **Línea base ASR sin entrenar** (en Colab o el GX10) con `omniASR_CTC_1B_v2` y `mms-1b-all` (`target_lang="quy"`) sobre 20 clips de [josemercado/quechua-chanka-asr](https://huggingface.co/datasets/josemercado/quechua-chanka-asr) o de Siminchik.

### Sábado en la mañana. Grabación (la enfermera por teléfono, 1.5–2 h de su tiempo)
4. **Set de entrenamiento TTS.** Ella lee el guion y frases de dominio, 300–600 frases, en un cuarto callado, WAV o nota de voz de WhatsApp (16 kHz mono al convertir).
5. **Set held-out de ASR, separado y nunca usado para entrenar.** 60–100 respuestas tipo teach-back dichas como las diría una gestante (frases incompletas, con español mezclado). Si hay una segunda voz (otra técnica, una familiar), 20–30 clips de esa voz: es lo único que evita reportar un número inflado por mono-hablante.
   Transcripción de referencia escrita por la enfermera.

### Sábado tarde y noche. Entrenar (en paralelo, ~6–8 h GPU en total)
6. **ASR-1 (seguro, 1 h).** KenLM 3–5-gram + hotwords con el texto de dominio, sobre Omnilingual CTC y sobre MMS. Medir.
7. **ASR-2 (Ricardo, 3–5 h).** Fine-tune del adapter MMS `quy` (receta del blog de HF) y, si el tooling coopera, fine-tune CTC de Omnilingual 300M/1B con la receta oficial, usando la parte de entrenamiento de la enfermera + Siminchik chanka. Medir contra el mismo held-out.
8. **TTS (1–2 h).** `finetune-hf-vits` sobre `mms-tts-quy` con la voz de la enfermera.

### Domingo temprano (hasta 07:00 PT). Congelar
9. Elegir la mejor combinación por número, no por oído, y cablearla al bot.

### Cómo se mide (tabla del pitch)

| Qué | Métrica | Antes | Después |
|---|---|---|---|
| ASR | **CER y WER** en el held-out de la enfermera (con `jiwer`) | Omnilingual / MMS sin tocar | + LM/hotwords, + fine-tune |
| Teach-back | **% de conceptos clave recuperados** (match difuso por palabra clave sobre la hipótesis) y falsos positivos | igual | igual |
| TTS | **CER de ida y vuelta** (sintetizar → transcribir con Omnilingual → CER contra el texto) + **MOS 1–5 de la enfermera** a ciegas, 10 frases, sintética vs su grabación | MMS-TTS base | MMS-TTS afinado |

Reportar el número aunque sea feo. Un "CER bajó de X a Y en 80 clips reales de una hablante de Huancavelica" es más creíble que cualquier cifra de paper.

### Respaldo si falla
- **TTS.** Si el fine-tune suena mal, el bot usa **solo las grabaciones de la enfermera** (set finito) y las partes dinámicas se resuelven con frases pregrabadas por bloques ("su control es el día…" + número grabado). Funciona igual en el demo.
- **ASR.** Si ningún fine-tune mejora el held-out, quedarse con Omnilingual zero-shot + hotwords. Si el CER sigue alto, el teach-back cae a **respuestas cerradas** ("diga *arí* si…", o tres opciones), que sí se clasifican bien.
- **Hardware.** El GX10 es ARM64 con CUDA; que fairseq2/omnilingual tenga ruedas para aarch64 **no está verificado**. Tener Colab listo desde el viernes. Para inferencia en Mac existen ports MLX/CoreML de Omnilingual 300M ([Hub](https://huggingface.co/api/models?search=omnilingual)).

---

## 5. Licencias (decirlo en el pitch)

| Pieza | Licencia | Hackathon | Producción en el puesto |
|---|---|---|---|
| Omnilingual ASR (modelos y código) | **Apache 2.0** | ✅ | ✅ la ruta limpia |
| MMS-1B-all y MMS-TTS | **CC-BY-NC 4.0** | ✅ no comercial | Uso por un puesto de salud público sin cobro probablemente es no comercial, pero si un tercero cobra por el servicio deja de serlo. **[REQUIERE ABOGADO]** antes de operar |
| XTTS v2 | CPML, no comercial, sin vendedor de licencia | ✅ | ❌ |
| F5-TTS (pesos) | CC-BY-NC-4.0 | ✅ | ❌ |
| Siminchik | CC-BY 4.0 (atribución) | ✅ | ✅ |
| makitty/quechua-chanka-unified | CC-BY-4.0 | ✅ | ✅ |
| josemercado/quechua-chanka-asr | **sin licencia declarada** | solo evaluación interna | ❌ no usar |
| Voz de la enfermera | lo que ella autorice | pedir consentimiento escrito (WhatsApp vale) para grabar, entrenar y publicar el demo | igual, y aclarar si el modelo con su voz puede seguir usándose |

**Nota de diseño (bucle de mejora).** El producto tiene un canal de feedback natural. Cada respuesta de teach-back que la enfermera corrige en el panel es un par audio-texto chanka de dominio real, que alimenta el held-out y el siguiente fine-tune. Vale decirlo en el pitch: el ASR mejora con el uso del propio puesto de salud.
