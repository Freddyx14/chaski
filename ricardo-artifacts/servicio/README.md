# Banco de pruebas de visión

No es la app de Freddy. Es para enchufar la visión antes de que la UI exista y probarla entre los dos.

## Arrancar

```bash
cd ricardo-artifacts
set -a; source .env; set +a          # carga las claves; .env no se commitea
PYTHONPATH=. uv run --with fastapi --with uvicorn --with anthropic --with python-multipart \
  uvicorn servicio.app:aplicacion --host 0.0.0.0 --port 8000
```

Abrir `http://localhost:8000`. Desde otro equipo de la misma red, con la IP de la Mac.
La cámara del navegador **solo funciona en `localhost` o por HTTPS**: si Freddy entra por IP y no le
aparece la cámara, que use «Subir foto», o se levanta un túnel.

## Qué hace

Foto de una caja o receta → Claude → qué es, para qué sirve, y si coincide con lo que dijo la enfermera.
La regla es que **si no lo lee con seguridad, no inventa**: `seguro: false` y la lista de lo que no pudo leer.

| Ruta | Qué devuelve |
|---|---|
| `GET /` | La página de prueba |
| `GET /salud` | Qué modelo usa y si están las dos claves |
| `POST /ver` | `imagen`, `dicho` (opcional), `modelo` (opcional) → la lectura en JSON |

## Medido el 24-oct

| Caso | Modelo | Resultado |
|---|---|---|
| Caja legible de paracetamol 500 mg | `claude-haiku-4-5` | Leyó nombre, concentración y presentación; explicó sin jerga; confirmó que coincide con lo dicho. **2.25 s** |
| La misma foto, borrosa y recortada | `claude-haiku-4-5` | `seguro: false`, nada inventado, cinco razones de por qué no pudo. **2.69 s** |

**Haiku 4.5 alcanza para esta tarea.** El selector de la página permite comparar con Sonnet 5 y Opus 5
en vivo, que es como se decide con números y no con opinión.

## Lo que Haiku NO hizo, y está bien

Dejó `para_que_sirve_chanka` en `null`: no se animó a explicarlo en quechua chanka. **Es la respuesta
correcta.** El quechua no sale de aquí: sale de la traducción de Freddy con glosario, pasa por la
auditoría de retraducción, y recién entonces se dice en voz alta con `mms-tts-quy`.

Que el modelo se calle solo, sin que nadie se lo pida, es justo lo que el criterio 4 de Anthropic premia.

## La traducción al quechua no la hace la visión

Haiku deja `para_que_sirve_chanka` en `null` a propósito: el prompt le dice que no se invente quechua.
La traducción la hace **el módulo de Freddy**, que se importa, no se copia:

```python
from rimay.auditoria import auditar      # app/rimay/auditoria.py
```

Si él mejora el glosario o la auditoría, este banco lo hereda sin tocar nada.

`POST /traducir` con `texto` en castellano devuelve el quechua, la retraducción a ciegas, y si la
auditoría lo aprueba. El botón «Traducir y auditar» de la página lo llama con la explicación que leyó
la cámara, así se ve la cadena entera: **foto → castellano → chanka → auditoría**.

### Medido el 24-oct

| Caso | Resultado |
|---|---|
| «Baja la fiebre y calma el dolor.» | `Kayqa rupapakuyta uraykuchin, nanaytapas tanichin.` · **aprobado** · 14.38 s |
| «Baja la fiebre y calma el dolor de cabeza. Tome una tableta cada ocho horas.» | **BLOQUEADO**: «cambió un dato crítico: medicamento». La retraducción decía «Este remedio», que el original no nombraba. Términos inseguros: `tableta` · 25.58 s |

El bloqueo es el comportamiento correcto, pero conviene mirarlo: la retraducción **agregó** un sujeto
(«este remedio») que el original no tenía, y la comparación lo leyó como dato crítico cambiado. Es un
falso positivo del lado seguro. Vale la pena que Freddy lo vea.

**Y hay un problema de reloj: 14 a 25 segundos por traducción.** Son cuatro llamadas a Opus 5 en serie
(extraer hechos, traducir, retraducir, extraer otra vez). Para un intérprete en vivo es demasiado. Esa es
exactamente la decisión D15 del SOT: medir los tres modelos y quedarse con el más rápido que no pierda
acierto en la auditoría. Las llamadas 1 y 2 podrían ir en paralelo con las 3 y 4 de la frase anterior.

## El flujo completo: `/flujo`

```
http://localhost:8000/flujo
```

Antes hay que abrir el túnel a la GPU, porque los modelos de voz viven ahí:

```bash
ssh -i ~/.ssh/id_rsa_aws -N -L 8010:localhost:8000 ubuntu@44.220.107.99
```

### Cómo está desplegado el servicio de voz

Sin tocar el grupo de seguridad y sin certificados:

1. `scp` de `servicio/instancia.py` al NVMe de la instancia.
2. `uvicorn instancia:aplicacion --host 127.0.0.1 --port 8000` — **solo escucha en localhost**, así que
   desde fuera de la instancia no se alcanza.
3. Un túnel de SSH (`-L 8010:localhost:8000`) lo trae a la Mac como si fuera local.
4. El servicio local (`servicio/app.py`) le habla a `http://127.0.0.1:8010`.

Los modelos se cargan **perezosamente**: el primer turno paga la carga, los siguientes no.

### Medido el 24-oct, ciclo completo

**Turno del paciente** (audio en chanka → lo que la enfermera lee):

| Paso | Modelo | Tiempo |
|---|---|---|
| Detectar idioma | `mms-lid-512` | 482 ms (152 ms el modelo; el resto es el túnel) |
| Oír | `omniASR_LLM_300M` | 1,926 ms |
| Pasar a castellano | `claude-haiku-4-5` | 3,169 ms |
| **Total** | | **5.6 s** |

**Turno de la enfermera** (castellano → chanka hablado):

| Paso | Modelo | Tiempo |
|---|---|---|
| Traducir, retraducir a ciegas y auditar | `claude-opus-5` × 4 llamadas | **30,552 ms** |
| Hablar | `mms-tts-quy` | 470 ms |

**La auditoría se come el 98% del turno.** No es el modelo: son cuatro llamadas en serie.

### Dos bloqueos falsos que hay que arreglar

| Caso | Por qué bloqueó | Qué pasa de verdad |
|---|---|---|
| «Tome una tableta cada ocho horas, después de comer» | «cambió un dato crítico: medicamento» | El original dice **tableta**, la retraducción dice **pastilla**. Son sinónimos, y la comparación los lee como medicamentos distintos |
| «Si hay sangrado, venga a la posta» | «términos sin traducción segura: posta» | «posta», «en ayunas» y «carné» van a salir en cada frase de una posta. Si cada una bloquea, el sistema se calla siempre |

Con 9 frases probadas en tres modelos, **la auditoría aprobó 1**. Esto es de Freddy
(`rimay.hechos.comparar` y `rimay.auditoria.decidir`) y es más urgente que elegir modelo.

### Modo ensayo

Mientras los modelos no estén ajustados, la página trae dos salidas, y las dos dejan rastro:

- **Modo ensayo** (activado): si el bloqueo es **solo** por términos sin traducción segura, se dice igual
  con un aviso en pantalla. Un dato crítico cambiado **sigue bloqueando**.
- **«Decirlo igual (solo ensayo)»**: aparece cuando sí hay bloqueo duro. Es una decisión humana explícita,
  se marca como `forzado: true` en la respuesta, y el aviso dice que en producción no existe.

Verificado: forzando «Tome una tableta cada ocho horas» salió
`Huk tabletata upyakunki sapa pusaq horaspi.` con 171 KB de audio en chanka.

## Bajar la espera: de 26 s a 5.1 s

La auditoría eran cuatro llamadas a Opus 5 en fila. Tres cambios, medidos:

| Qué | Mediana |
|---|---|
| Original: Opus 5 × 4 en serie | **26,210 ms** |
| Paralelo + Sonnet traduce + Haiku lo mecánico | **10,174 ms** |
| Paralelo + Haiku en todo | **5,143 ms** |

1. **Paralelo.** Sacar los hechos del original y traducir no dependen una de la otra: salen juntas.
   Tres pasos en vez de cuatro.
2. **Cada llamada con su modelo.** Traducir pide calidad. Sacar hechos de un texto y retraducir son
   mecánicas: Haiku las hace en una fracción.
3. **El glosario va en el `system`, no en el mensaje**, con `cache_control`. Así es prefijo estable y no
   se reprocesa en cada llamada.

Está en `servicio/auditoria_rapida.py`, que **reusa los prompts y los modelos de datos de Freddy**: solo
cambia la orquestación. Su `auditar` original sigue intacto y se puede pedir con `rapido=false`.

**Y la página ya no espera a la voz:** muestra el chanka apenas lo tiene y pide el audio en una segunda
llamada (`POST /voz`, 543 ms). Lo que se siente bajó de 26 s a unos 5 s hasta ver el texto.

## La cámara, en el mismo flujo

`/flujo` tiene ahora el panel 3. Dos caminos, porque los navegadores no se ponen de acuerdo:

- **Cámara en vivo** (`getUserMedia`): funciona en laptop con `localhost`. En teléfono **necesita HTTPS**.
- **«Subir o usar cámara del teléfono»** (`<input capture="environment">`): abre la cámara nativa de
  Android y iOS y **funciona sin HTTPS**.

Lo que lee la caja se puede mandar al paciente en quechua con un botón, así se ve la cadena entera:
foto → castellano → chanka → voz.

## El corrector: `/corregir`

Convierte audios crudos en verdad de referencia, y **una corrección sirve para los tres ajustes**:

```
audio → omniASR transcribe → nosotros corregimos la escritura → (audio, texto correcto) + castellano
```

| Conjunto | Qué par usa | Para qué |
|---|---|---|
| `datos/corpus/asr.jsonl` | audio → texto chanka | que entienda el acento y los préstamos |
| `datos/corpus/tts.jsonl` | texto chanka → audio | que Chaski suene como una persona de verdad |
| `datos/corpus/traduccion.jsonl` | castellano ↔ chanka | que traduzca como se habla en la posta |

La pantalla muestra la frase en castellano del cuadernillo, reproduce el audio, trae lo que oyó el modelo
como borrador y deja corregirlo. `⌘ Enter` guarda y pasa al siguiente; `Espacio` vuelve a escuchar;
«No sirve» descarta el clip. El botón «Exportar corpus» escribe los tres archivos.

**Solo entra al corpus lo que tiene transcripción corregida y consentimiento marcado.**

## Antes de apagar la instancia

Ya está hecho: `~/chaski-respaldo`, **18 GB** en el disco raíz, que sí sobrevive al apagado.
Al encenderla mañana:

```bash
ssh -i ~/.ssh/id_rsa_aws ubuntu@44.220.107.99 'bash ~/restaurar.sh'
```

Copia el entorno de vuelta al NVMe, deja la caché de fairseq2 enlazada y levanta el servicio.
**Unos 2 minutos**, sin descargar nada. Reconstruir desde cero serían 12 a 15.

## Cinco audios de prueba con verdad de referencia

`voz/generar_muestras.py` dice con `mms-tts-quy` los pares verificados del cuadernillo y los pega en
audios de **menos de 45 s**. Como sabemos exactamente qué texto se dijo, **cada audio trae su referencia**
y el error del reconocimiento se mide sin esperar a las familias.

```
quy_01.wav  44.1s  15 frases      quy_04.wav  42.1s  13 frases
quy_02.wav  43.3s  15 frases      quy_05.wav  44.4s  14 frases
quy_03.wav  42.1s  13 frases      216 s en total
```

La página los ofrece en el selector, muestra el castellano de referencia y **calcula el error de palabra
en vivo** contra lo que oyó el modelo.

### `omniASR` no aguanta audios largos

Con 44 s revienta: `RuntimeError: The map function has failed`. Con 16 s pasa. El servicio ahora **parte
el audio en trozos de 20 s cortando en el silencio más cercano** para no romper una palabra, transcribe
cada trozo y los pega. Los 44 s salen en **5.7 s, en 3 trozos**.

Esto importa fuera de la prueba: un paciente que habla cuarenta segundos seguidos es normal en una
consulta, y sin esto el sistema se caía.

### Primer número contra referencia conocida

| | |
|---|---|
| Audio | `quy_01.wav`, 44 s, 33 palabras |
| **WER** | **21.2%** |

Sigue siendo voz sintética, así que no es el número del pitch. Pero ya es una medición reproducible
—mismo audio, misma referencia, mismo comando— contra la que comparar después del ajuste fino.

## Dictado por micrófono: Cartesia

El botón «Dictar» graba con `MediaRecorder` y manda el audio a `POST /escuchar`, que llama a
**Cartesia `ink-whisper`** en castellano. Medido: **480 ms** para 3.5 s de audio, y transcribió
«Tome una pastilla cada 8 horas, después de comer» sin un error.

Se eligió sobre el dictado del navegador porque ese no existe en Safari ni en Firefox, depende de los
servidores de Google y falla sin aviso. Éste funciona igual en los tres navegadores y en el teléfono, y
de paso usa la mitad de Cartesia que faltaba: entender, no solo hablar.

## La cascada en D3

El presupuesto de espera dejó de ser una lista de números: es una **cascada** donde cada paso es un
bloque proporcional a lo que tardó, con la **meta de 4 s** marcada en rojo. De un vistazo se ve qué paso
se come el turno. Arriba, cuatro medidas: turno del paciente, turno tuyo, ciclo completo y error del
reconocimiento.

## El formulario cambia de dónde vienen los datos

Freddy está construyendo un formulario web (`form/`, Next.js + Neon + Vercel Blob): cada persona ve la
frase en castellano, **la escribe en quechua y graba leyéndola**. El audio y el texto llegan **ya
emparejados**.

Eso borra de un golpe los tres sitios donde el emparejamiento se rompía: no hay que partir por silencios,
ni deducir el número de lo que se oye, ni cruzar fotos de hojas con audios sueltos.

`voz/importar_formulario.py` trae ese export al corpus:

```bash
PYTHONPATH=. uv run --with httpx python voz/importar_formulario.py <archivo-o-url>
```

o desde `/corregir`, en la caja «Del formulario». Baja cada audio, lo normaliza a 16 kHz mono y arma el
manifiesto. **Las filas sin consentimiento no entran**, y se reportan aparte. El formato está en
`CONTRATO.md` §7, publicado para que el formulario apunte a algo concreto.

### Qué hace ahora el etiquetador

Cuando el texto ya viene escrito, el trabajo deja de ser teclear y pasa a ser **comprobar que el audio
dice eso**. El botón «¿El audio dice esto?» transcribe el clip y mide la diferencia en palabras:

| Diferencia | Veredicto |
|---|---|
| ≤ 34% | coincide |
| ≤ 70% | se parece, conviene escucharlo |
| > 70% | muy distinto: o leyó otra frase, o el modelo no entiende esa voz |

**La sugerencia es mirar, no descartar.** Hoy el reconocimiento no está ajustado y falla en los préstamos
del castellano, así que una diferencia alta suele ser culpa del modelo, no de la persona. Descartar por
el número sería tirar justo los clips que más falta hacen para entrenar.

Las notas de voz de WhatsApp siguen funcionando como plan B: subir el archivo, grabar desde la página,
partir, unir y mover los cortes.

## Cómo sale el número del pitch

`voz/medir_asr.py` mide el reconocimiento contra las transcripciones que una persona corrigió. Se corre
**dos veces, con la misma orden y el mismo conjunto**:

```bash
# antes de ajustar nada
PYTHONPATH=. uv run --with httpx python voz/medir_asr.py datos/corpus/asr.jsonl --etiqueta base

# después del ajuste fino
PYTHONPATH=. uv run --with httpx python voz/medir_asr.py datos/corpus/asr.jsonl --etiqueta ajustado
```

Las dos corridas se acumulan en `reports/asr.json`, así la comparación sale de dos mediciones hechas
igual y no de dos recuerdos. Devuelve WER, CER, el desglose por persona y, aparte, **el acierto en los
préstamos del castellano** — paracetamol, control, doctor — que es donde el modelo base falla y donde
equivocarse en una posta hace daño.

Tres reglas que lo hacen honesto:

1. **Se mide sobre la voz de prueba**, la persona que el modelo nunca escuchó al entrenar.
2. **Un clip sin transcripción corregida no entra**: no se mide contra lo que nadie verificó.
3. El mismo conjunto y el mismo comando en las dos corridas. Cambiar el conjunto entre el «antes» y el
   «después» es la forma más fácil de mentirse.

### Primera corrida, de humo

Con las cinco muestras sintéticas, que sí traen referencia:

| | |
|---|---|
| WER | **32.8%** |
| CER | **9.0%** |
| Préstamos acertados | **2 de 4 (50%)** |

No es el número del pitch —es voz sintética, no humana— pero demuestra que la medición corre de punta a
punta y ya enseña el patrón: **el CER es bajo y el WER alto**, o sea que el modelo oye bien los sonidos
y se equivoca en las palabras. Y la mitad de los préstamos sale mal, que es exactamente lo que el ajuste
fino tiene que arreglar.
