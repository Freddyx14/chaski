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
