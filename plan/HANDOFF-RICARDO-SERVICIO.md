# Ricardo: lo que falta en el servicio (sáb 24-oct, 23:45 PT) · prioridad ahora

> ✅ Pasos 1–6 hechos (cf9de8b). **Nuevo (dom 00:20): `git pull` y vuelve a desplegar** para que el servicio tome D41,
> las frases de la enfermera como ejemplos del traductor (`CHASKI_EJEMPLOS=1`, ya es el valor por defecto; no hay que
> tocar nada más). **Y renombra D40 → D43** en los comentarios de `servicio/app.py` (~l.178), `servicio/desplegar.sh`
> (~l.92) y el título de `servicio/PARA-FREDDY.md` (~l.416): el traductor es D43; D40 es «Chaski sin fondo» de ui-ux.
> **Memoria automática (D44, dom 01:45):** en `desplegar.sh` agrega `export CHASKI_MEMORIA_RUTA=$DESTINO/memoria/memoria_auto.jsonl`
> (y `mkdir -p $DESTINO/memoria`), fuera de la carpeta `chaski/` que se sincroniza con `--delete`; si no, cada
> despliegue borra lo aprendido. Para ver y aprobar: `uv run python -m chaski.memoria` y `… aprobar ID`.
> **Voz robótica (Freddy, 01:47) → ver la sección «🔊 Voz de Chaski: cómo arreglarla» al final de este archivo.**
> Y `/turno/paciente` solo acepta WAV (la app manda WAV, así que anda); con .webm y .m4a da 500.

> Decisión de Freddy (D43, 23:38; se citó como D40 por error, D40 es «Chaski sin fondo»): **traduce Claude Sonnet 5 con esfuerzo medio**, no NLLB. Medido en los mismos sets:
> 0/92 términos fijos dañados (NLLB 3), lo que dice el paciente se lee mejor (qu→es 50,1 vs NLLB 24,7) y el turno
> completo queda en **8,3 s** (`evals/traduccion/`, `evals/latencia/`). NLLB no se tira: queda como modo sin conexión
> y tu ajuste sigue.

## Pasos, en orden

| # | Qué | Cómo | Cómo verificas |
|---|---|---|---|
| 1 | `git pull` | trae `traducir.py` con `medium` por defecto y la traducción anticipada | `cd app && uv run pytest -q` → 350 verdes |
| 2 | **Traducir con Claude** | en `servicio/app.py`, `/turno/enfermera` y `/turno/paciente` tienen `motor: str = Form("nllb")` → cambiar a `Form("claude")`. Y dejar vacía `CHASKI_NLLB_URL` en el entorno de la instancia | `curl -F texto="Tome una pastilla de paracetamol cada ocho horas durante tres días" …/turno/enfermera` → `"motor":"claude"`, `"estado":"dicho"`, `ms.total` ~8 s |
| 3 | **Arreglar `/turno/paciente`** | hoy da 500 porque falla `/entender` en la GPU (`127.0.0.1:8000/entender`) | un audio de `data/formulario/p16/` devuelve 200 |
| 4 | **Ruta en vivo** `/turno/enfermera/vivo` | pegar el bloque de `app/chaski/PARA_RICARDO.md` | la app de ui-ux muestra «Chaski lo dirá así» a los ~3 s |
| 5 | **Voz durante el crítico** | pasar tu síntesis a `chaski_servicio.turno(..., voz_fn=lambda texto, idioma: wav_bytes)` | la respuesta trae `audio_wav_b64` y ~1 s menos |
| 6 | Reiniciar, probar 2 y 3, **push** y avisar por el grupo | | ui-ux y Freddy prueban desde el build 12 |

Variables que deben quedar: `CHASKI_MODELO_PRINCIPAL=claude-opus-5`, `CHASKI_MODELO_CRITICO=claude-sonnet-5`,
`CHASKI_PENSAR_TRADUCIR=medium` (o sin definir: ya es el valor por defecto), `CHASKI_TRADUCIR_ANTICIPADO=1` (ídem),
`CHASKI_NLLB_URL` vacía.


---

## 🔊 Voz de Chaski: cómo arreglarla (pedido de Freddy, dom 25-oct 01:52) · URGENTE antes del jurado

**El problema, en dos partes** (todo en `servicio/app.py`, función `_voz_para_chaski`, ~l.123):

```python
audio, _ = decir_en_voz(texto, voz="p24" if idioma == "quy" else "base")
```

1. **Castellano robótico.** Cuando Chaski le habla al personal (repreguntar, responder), usa `voz="base"`: el modelo
   de quechua de Meta (`mms-tts-quy`) leyendo castellano. Por eso suena a robot. El castellano tiene que ir por
   **Cartesia Sonic**, como dice el diseño (D16). La clave `CARTESIA_API_KEY` ya está en la instancia: la usa `/escuchar`.
2. **Quechua con otra voz.** El quechua sale con `p24`, un familiar, y no con `mama_freddy`, la voz ajustada con la
   enfermera. **Cuál suena en la demo lo decide Freddy.** Por eso va en una variable de entorno, para cambiarla sin
   tocar código.

### Paso 1 · Castellano con Cartesia (≈10 min)

En `servicio/flujo.py`, junto a `entender_castellano` (que ya usa Cartesia y la misma `CARTESIA_VERSION`):

```python
CARTESIA_TTS = "https://api.cartesia.ai/tts/bytes"

def voz_castellano(texto: str) -> bytes:
    """Lo que Chaski le dice al personal, en castellano, con Cartesia Sonic. WAV PCM 16 bits."""
    clave = os.environ["CARTESIA_API_KEY"]
    with httpx.Client(timeout=30) as cli:
        r = cli.post(CARTESIA_TTS,
                     headers={"Authorization": f"Bearer {clave}", "Cartesia-Version": CARTESIA_VERSION},
                     json={"model_id": os.environ.get("CHASKI_CARTESIA_MODELO", "sonic-3.6"),
                           "transcript": texto,
                           "voice": {"mode": "id", "id": os.environ["CHASKI_VOZ_ES"]},
                           "language": "es",
                           "output_format": {"container": "wav", "encoding": "pcm_s16le", "sample_rate": 24000}})
    if r.status_code >= 400:
        raise RuntimeError(f"Cartesia TTS {r.status_code}: {r.text[:200]}")
    return r.content
```

Para la voz (`CHASKI_VOZ_ES`): elige una voz latinoamericana, cálida y clara, de la lista de Cartesia
(`GET https://api.cartesia.ai/voices?language=es` con las mismas cabeceras) y pon su `id` en el entorno de la instancia.

Fuente del formato: https://docs.cartesia.ai/api-reference/tts/bytes (ruta `POST /tts/bytes`, `model_id` `sonic-3.6`,
cabecera `Cartesia-Version: 2026-08-14`; verificado el 25-oct).

### Paso 2 · `_voz_para_chaski` con las dos voces y respaldo

```python
def _voz_para_chaski(texto: str, idioma: str) -> bytes:
    from servicio.flujo import decir_en_voz, voz_castellano
    if idioma == "quy":
        audio, _ = decir_en_voz(texto, voz=os.environ.get("CHASKI_VOZ_QUY", "p24"))
        return audio
    try:
        return voz_castellano(texto)
    except Exception:
        audio, _ = decir_en_voz(texto, voz="base")   # respaldo: robótico, pero nunca mudo
        return audio
```

### Paso 2b · La ruta `/voz` también (importante)

**La app pide la voz del quechua aparte, a `POST /voz`**, después de mostrar el texto. Hoy esa ruta llama a
`decir_en_voz(texto)` con su valor por defecto (`p24`). Si solo cambias `_voz_para_chaski`, la voz del quechua
**no cambia en la app**. En `/voz`, usa la misma variable:

```python
audio, ms = decir_en_voz(texto, voz=os.environ.get("CHASKI_VOZ_QUY", "p24"))
```

Lo que Chaski le dice al personal en castellano (repreguntar, responder): la app reproduce el `audio_wav_b64` del turno
si viene, y si no viene usa la voz del iPhone. Así que con el Paso 2 alcanza, siempre que el turno devuelva ese audio.

### Paso 3 · Elegir la voz del quechua (lo decide Freddy)

- `CHASKI_VOZ_QUY=mama_freddy` → la voz ajustada con la enfermera. **Recomendado si la prueba a ciegas con ella sale
  bien** (`plan/HANDOFF-RICARDO-VOZ.md`). Es lo más fuerte para el pitch: la enfermera escucha a Chaski con su voz.
- `CHASKI_VOZ_QUY=p24` → la de hoy.
- Se cambia con la variable y un reinicio, sin desplegar código.

### Paso 4 · Desplegar y verificar

1. `git pull`, despliega con `servicio/desplegar.sh` y **avisa por el grupo antes de reiniciar**: un reinicio corta la
   app en vivo.
2. Castellano: `curl -F "texto=Disculpe, ¿desde cuándo tiene fiebre?" -F "idioma=spa" $URL/voz --output es.wav` y
   escúchalo. Tiene que sonar a persona, no a robot. (Si `/voz` no recibe `idioma`, prueba con un turno real en
   el que Chaski repregunte.)
3. Quechua: `curl -F "texto=Ama llakikuychu, kaypim kachkaniku." $URL/voz --output qu.wav`, con la voz elegida.
4. **La app no cambia nada:** el quechua lo pide a `/voz` (Paso 2b) y el castellano lo toma del `audio_wav_b64` del turno.
5. **Freddy prueba con el build 16** en TestFlight y confirma.

| Hecho | Qué |
|---|---|
| [ ] | `voz_castellano` en `flujo.py` + `CHASKI_VOZ_ES` en la instancia |
| [ ] | `_voz_para_chaski` con `CHASKI_VOZ_QUY` y respaldo |
| [ ] | `/voz` con `CHASKI_VOZ_QUY` (Paso 2b) |
| [ ] | Freddy eligió la voz del quechua (p24 o mama_freddy) |
| [ ] | Desplegado, avisado por el grupo y probado con `curl` |
