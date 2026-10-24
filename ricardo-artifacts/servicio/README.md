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
