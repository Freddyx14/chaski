# Contrato entre las sesiones

> Lo escribe la sesión A (voz) porque es quien recibe los audios. **Nadie lo cambia por su cuenta.**
> Si hace falta un campo, se habla, se cambia en los dos lados y se regeneran los datos de ejemplo.

## 1. Formato de los datos de voz

Un `manifiesto.jsonl`, una línea por audio, en `datos/<conjunto>/manifiesto.jsonl`:

```json
{"persona": "p1", "bloque": "A", "numero": 7, "audio": "datos/entrenamiento/p1_A_007.wav",
 "transcripcion": "sangre kaptinqa posta man hamuy", "castellano": "Si hay sangrado, venga a la posta",
 "segundos": 4.2, "consentimiento": true}
```

| Campo | Tipo | Regla |
|---|---|---|
| `persona` | texto | Identificador corto y anónimo: `p1`, `p2`. **Nunca el nombre real.** |
| `bloque` | `A` o `B` | A: frases de la posta. B: respuestas espontáneas |
| `numero` | entero | Orden dentro del bloque, por persona |
| `audio` | ruta | WAV mono, **16 kHz, 16 bits** |
| `transcripcion` | texto | En quechua chanka, como lo escribió la mamá de Freddy. Vacío si todavía no está |
| `castellano` | texto | La frase de origen. Vacío en el bloque B |
| `segundos` | número | Duración real medida con `ffprobe` |
| `consentimiento` | booleano | **Si es `false`, el audio no entra a ningún conjunto** |

## 2. Partición

Tres conjuntos, en `datos/entrenamiento/`, `datos/validacion/` y `datos/prueba/`.

**La regla que hace honesta la medición: `prueba` contiene a una persona completa que no aparece en
`entrenamiento` ni en `validacion`.** No se parte por frase, se parte por hablante. El manifiesto de
prueba lleva en su primera línea un comentario con quién quedó fuera.

## 3. La función que llama el lado de Claude

```python
from rimay.contrato import entender, Transcripcion

t: Transcripcion = entender("ruta/al/audio.ogg")
t.texto        # str, la transcripción en chanka
t.confianza    # float 0..1
t.segundos     # float
t.modelo       # str, qué modelo la produjo
```

Mientras el modelo real no exista, `entender` devuelve una transcripción fija y `modelo="falso"`.
**La sesión B y Freddy programan contra esa versión desde el minuto cero y no esperan al modelo.**

## 4. Dónde van los números

Un JSON por número, en `reports/`. La página de resultados lee esos archivos y nada más.

| Archivo | Quién lo escribe | Qué lleva |
|---|---|---|
| `reports/asr.json` | sesión A | CER y WER: línea base, con vocabulario, con ajuste fino |
| `reports/tts.json` | sesión A | Juicio a ciegas de la mamá de Freddy sobre la voz |
| `reports/traduccion.json` | sesión B | Claude contra Google Translate, calificado por la enfermera |
| `reports/detector.json` | sesión B | Cuántos errores atrapa el detector de Freddy |
| `reports/receta.json` | sesión B | Aciertos y tasa de abstención de la lectura de receta |

## 5. Las otras dos firmas

```python
from voz.contrato import hablar, idioma, Audio, Idioma

a: Audio = hablar("Mamáy, allillanmi")   # texto chanka -> audio
a.ruta, a.segundos, a.frecuencia, a.modelo

i: Idioma = idioma("turno_007.wav")      # audio -> que lengua es
i.codigo      # "quy" o "spa", nunca otra cosa
i.confianza   # 0.0 en la version falsa, a proposito
```

**Las versiones falsas son usables, no vacías:**

- `hablar` devuelve `muestras/mms-tts-quy/todas.wav`, que es chanka real generado con
  `facebook/mms-tts-quy`. No sintetiza el texto que se le pasa, pero suena, así que la app se arma y se
  escucha completa antes de que exista el modelo servido.
- `idioma` decide **por el nombre del archivo**: si lleva `spa` o `_es`, responde castellano; si no,
  chanka. Es determinista a propósito, para que quien arme la app pruebe las dos ramas sin modelo.
- **La confianza es 0.0 en las dos.** Ningún número de una versión falsa debe terminar en un reporte.

## 6. Con qué se prueban

`uv run python voz/muestras_prueba.py` arma `datos/prueba_minima/` sin descargar nada ni esperar a las
familias: nueve audios de tres clases, que son las tres que el intérprete tiene que distinguir.

| Clase | Cuántos | De dónde sale |
|---|---|---|
| `spa` | 5 | Frases clínicas reales (dosis, control, sangrado, fiebre) dichas con la voz del sistema de macOS |
| `mix` | 3 | Castellano con palabras en quechua: «Mamáy, tome una pastilla cada ocho horas». Así se habla en la posta |
| `quy` | 1 | Las cinco frases de `muestras/mms-tts-quy/todas.wav`, chanka real de MMS-TTS |

Sirven para tres cosas antes de que exista un solo audio de la familia: probar `idioma()` con las tres
clases, medir la espera por turno del ciclo completo, y tener un castellano de referencia. El caso `mix`
es el que más importa: ningún clasificador de idioma lo resuelve bien, y es lo normal en una consulta.
