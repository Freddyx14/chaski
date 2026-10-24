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
