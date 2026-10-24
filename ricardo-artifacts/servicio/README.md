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
