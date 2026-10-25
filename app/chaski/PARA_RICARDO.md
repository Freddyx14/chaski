# Para Ricardo: las rutas del intérprete

Todo el turno vive en `chaski.servicio` (intérprete, traducción, barreras B1–B4 en código y el crítico). Tus rutas
solo leen el formulario y llaman a una función. El crítico es **el mismo código** que mide
`evals/ataques/correr.py --modo chaski` (`chaski.critico.revisar`), así que el número del pitch es el del producto.

## Variables de entorno

| Variable | Para qué | Por defecto |
|---|---|---|
| `ANTHROPIC_API_KEY` | el cliente de Claude (se crea una sola vez, la primera vez que se usa) | obligatoria |
| `CHASKI_MODELO_PRINCIPAL` | el intérprete (`decidir`) | `claude-opus-5` |
| `CHASKI_MODELO_CRITICO` | el crítico | `claude-sonnet-5` (160/160 atrapados, 7,5 % de falsos bloqueos) |
| `CHASKI_MODELO_HECHOS` | el crítico, solo la extracción de datos (paso mecánico) | vacía = el del crítico |
| `CHASKI_PENSAR_HECHOS` | pensamiento de la extracción: `no`, `low`, `medium`, `high` o `modelo` | `no` |
| `CHASKI_PENSAR_RETRADUCIR` | pensamiento de la retraducción ciega | `low` |
| `CHASKI_PENSAR_AGREGADOS` | pensamiento del paso «qué agregó» | `low` |
| `CHASKI_PENSAR_TRADUCIR` | pensamiento del traductor Claude: `modelo`, `no`, `low`, `medium`, `high` | `modelo` (chrF++ 51,8 en 5,6 s; `no` 43,1 en 1,7 s) |
| `CHASKI_NLLB_URL` | tu NLLB; sin ella traduce Claude | vacía |

Los `PENSAR` por defecto bajaron el crítico de p50 9 s a ~2-3 s sin perder atrapados (24-oct). `modelo` deja el
pensamiento por defecto de Sonnet 5, que era el camino lento. Detalle en el docstring de `chaski/critico.py`.

Los dos modelos se cambian sin tocar código. Cada respuesta trae `modelos: {principal, critico}`.

## Las rutas (para pegar en `servicio/app.py`)

```python
from fastapi import Form, Query
from chaski import servicio as chaski_servicio


@aplicacion.post("/turno/enfermera")
def turno_enfermera(texto: str = Form(...), contexto: str = Form(""), n_mejores: str = Form(""),
                    confianza: str = Form(""), traduccion_sembrada: str = Form("")):
    try:
        return chaski_servicio.turno(texto, "spa", "personal", contexto, n_mejores, confianza, traduccion_sembrada)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/turno/paciente")
async def turno_paciente(audio: UploadFile = File(...), contexto: str = Form("")):
    try:
        oido = tu_asr_quechua(await audio.read(), audio.filename or "turno.wav")  # tu /entender: {texto, alternativas}
        return chaski_servicio.turno(oido["texto"], "quy", "paciente", contexto,
                                     json.dumps(oido.get("alternativas", [])), oido.get("confianza"))
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


# La misma ruta en vivo (SSE): `decision` a los ~3 s con el castellano pulido, `resultado` al final (o `error`).
# La app la usa para mostrar el texto mientras traduce y revisa. Lo que se dice es solo `resultado`.
@aplicacion.post("/turno/enfermera/vivo")
def turno_enfermera_vivo(texto: str = Form(...), contexto: str = Form(""), n_mejores: str = Form(""),
                         confianza: str = Form(""), traduccion_sembrada: str = Form("")):
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        chaski_servicio.turno_eventos(texto, "spa", "personal", contexto, n_mejores, confianza, traduccion_sembrada),
        media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@aplicacion.get("/banco")
def banco(tag: str | None = Query(default=None)):
    return chaski_servicio.banco_por_tag(tag)
```

La app ya manda `rol`, `modo_ensayo`, `rapido` y `con_audio`; FastAPI ignora los campos que la ruta no declara,
así que no hace falta leerlos.

## Qué entra

- `contexto`: el JSON del `contexto` que devolvió el turno anterior (la app ya lo guarda y lo reenvía, con `modo`
  adentro). Vacío = consulta nueva. Un JSON roto da `ValueError` (es un error de la app, no se tapa).
- `n_mejores`: JSON con una lista de textos, o de pares `[texto, puntaje]` tal como los da `/entender`.
- `confianza`: 0 a 1, del reconocedor. Con ella corre B1: si es menor a 0,6 y lo oído trae un número, un
  medicamento o una parte del cuerpo, el turno se bloquea. Sin ella, B1 no corre.
- `traduccion_sembrada`: **solo el ensayo de la negativa.** Reemplaza la traducción; barreras y crítico corren
  igual, y la respuesta trae `sembrada: true` para que nadie lo confunda con un error real del traductor.

## Qué sale

`Resultado.model_dump()` (`chaski/orquestador.py`): `estado` (`dicho` · `dicho_con_aviso` · `bloqueado`),
`accion`, `motivo`, `para`, `idioma_salida`, `texto_original` (lo que se oyó), `texto_pulido`, `texto_salida`
(lo que se dice; vacío si se bloqueó), `audio`, `aviso`, `motor`, `respaldo`, `sembrada`, `modelos`,
`paso_fallido`, `ms` y `contexto`.

`GET /banco` devuelve `{id, es, quy, audio, tags, revisado}`. Hoy **ninguna frase está revisada**: el intérprete no
dice ninguna (se traduce lo dicho) y la app no las hace sonar. Cuando la enfermera revise una, basta con poner
`"revisado": true` en `app/chaski/banco.json`.

## Al arrancar (opcional)

Si hay frases revisadas, el intérprete busca candidatas con embeddings. Para que el primer turno no pague la
carga del modelo:

```python
@aplicacion.on_event("startup")
def _precargar():
    from chaski import banco as banco_frases
    banco_frases.precargar()
```
