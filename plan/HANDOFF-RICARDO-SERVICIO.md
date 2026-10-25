# Ricardo: lo que falta en el servicio (sáb 24-oct, 23:45 PT) · prioridad ahora

## 🔁 Bandeja automática · Ricardo, pega esto UNA vez en tu sesión de Claude Code

```
/loop cada 5 minutos: haz git pull --rebase --autostash en el repo chaski; abre plan/HANDOFF-RICARDO-SERVICIO.md y
ejecuta, en orden, cada tarea de la sección «Bandeja» que siga en [ ]. Por cada una: hazla, verifícala contra la URL
pública con curl, márcala [x] con el hash del commit, despliega con servicio/desplegar.sh y haz push (solo tus
archivos, nunca -f). Si una tarea no se puede, déjala en [ ] y escribe debajo «⚠️ bloqueado: <por qué>». Si no hay
nada en [ ], no hagas nada hasta la próxima vuelta.
```

Así Freddy y las otras sesiones (loopmind-05, ui-ux, pitch-qa) te dejan trabajo acá y tu sesión lo toma sola en
≤ 5 min, sin que nadie lo pase a mano. Escribimos solo en esta Bandeja; lo de abajo es el detalle de cada tarea.

## Bandeja

> Nota sobre cómo verificar `/turno/paciente`: con audio sintetizado no sirve. Generé la frase con
> nuestro TTS y el reconocedor oyó «pos ahora pivo pastilla carcon diez» — habla sintética es fuera de
> dominio para un modelo entrenado con voz humana. El sistema respondió «no entendí» en vez de
> adivinar una dosis, que es la guarda funcionando. Se verifica con grabaciones de `datos/crudo/`.

> Las cuatro primeras quedaron hechas antes de que existiera la Bandeja (dom 00:20–09:10). Dejo el
> hash de cada una para que se pueda comprobar. Lo que encontré de paso y no estaba pedido:
> `/turno/paciente` ya acepta .m4a y .webm (los convierte, antes daba 500), y el WAV de Cartesia
> venía con cabecera de flujo —1,6 s declarando 89 478 s— que rompe a los reproductores que le creen.

| | Tarea | Detalle |
|---|---|---|
| [x] | `git pull` y desplegar: D41, D44 y 6fa2cec (verificado dom 09:10: turno 8,2 s, `motor claude`, «Upyay huk paracetamol pastillata sapa pusaq horasmanta…») | 0851178 |
| [x] | Memoria fuera de lo que se sincroniza. Probado como importa: turno → redespliegue → la línea sigue. 6 líneas ahora | 0851178 |
| [x] | Voz: castellano por Cartesia (Ximena), quechua `mama_freddy` en los dos sitios, `p24` de respaldo. Verificado por frecuencia, no por ausencia de error: castellano 24000 Hz, quechua 16000 Hz, 0 respaldos usados | 9e2075d |
| [x] | D40 → D43 en `app.py`, `desplegar.sh` y `PARA-FREDDY.md` | 0ee64a9 |
| [x] | `git pull` y desplegar da250b1. Verificado con grabaciones reales (dom 02:20): `p16_C_001.wav` → el reconocedor oye «pusaq urapi huk pastillata upyay», `estado dicho`, «Tome una pastilla a las ocho.», **sin paréntesis**. `p18_C_001.wav` → `dicho`, «Tome una pastilla cada ocho horas», sin paréntesis | 1f6b0a4 |
| [ ] | `git pull` y desplegar (dom 02:35, 630a847): **un bloqueo ahora pregunta antes de rendirse** (pedido de Freddy). Si una barrera o el crítico frena la traducción del personal, Chaski le pregunta en castellano «No quiero decir un dato equivocado: la dosis. ¿Me lo repite, por favor?»; si es del paciente, le pide repetir en quechua. Una sola vez; el ensayo y las fallas de sistema siguen siendo bloqueo (`CHASKI_REPREGUNTAR_AL_BLOQUEAR=1`, ya es el valor por defecto) | verificar: un turno bloqueado devuelve `accion: repreguntar`, `para: personal` |


> ✅ Pasos 1–6 hechos (cf9de8b). **Nuevo (dom 00:20): `git pull` y vuelve a desplegar** para que el servicio tome D41,
> las frases de la enfermera como ejemplos del traductor (`CHASKI_EJEMPLOS=1`, ya es el valor por defecto; no hay que
> tocar nada más). **Y renombra D40 → D43** en los comentarios de `servicio/app.py` (~l.178), `servicio/desplegar.sh`
> (~l.92) y el título de `servicio/PARA-FREDDY.md` (~l.416): el traductor es D43; D40 es «Chaski sin fondo» de ui-ux.
> **Memoria automática (D44, dom 01:45):** en `desplegar.sh` agrega `export CHASKI_MEMORIA_RUTA=$DESTINO/memoria/memoria_auto.jsonl`
> (y `mkdir -p $DESTINO/memoria`), fuera de la carpeta `chaski/` que se sincroniza con `--delete`; si no, cada
> despliegue borra lo aprendido. Para ver y aprobar: `uv run python -m chaski.memoria` y `… aprobar ID`.
> **Voz robótica (Freddy, 01:47) → ver la sección «🔊 Voz de Chaski: cómo arreglarla» al final de este archivo. El quechua va con la voz de la mamá de Freddy (`mama_freddy`), decidido.**
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
   enfermera. **✅ Decidido por Freddy (dom 01:55): Chaski habla quechua con la voz de su mamá, `mama_freddy`.** Es la
   decisión del SOT desde el inicio (F5: «voz chanka de Meta ajustada con la voz de la mamá de Freddy»). Va como valor
   por defecto en el código y en una variable de entorno solo como respaldo.

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
        audio, _ = decir_en_voz(texto, voz=os.environ.get("CHASKI_VOZ_QUY", "mama_freddy"))
        return audio
    try:
        return voz_castellano(texto)
    except Exception:
        audio, _ = decir_en_voz(texto, voz="base")   # respaldo: robótico, pero nunca mudo
        return audio
```

### Paso 2b · La ruta `/voz` también (importante)

**La app pide la voz del quechua aparte, a `POST /voz`**, después de mostrar el texto. Hoy esa ruta llama a
`decir_en_voz(texto, voz)` con `voz: str = Form("p24")` (~l.494). La app no manda `voz`, así que siempre sale `p24`.
Si solo cambias `_voz_para_chaski`, la voz del quechua **no cambia en la app**. En `ruta_voz`:

```python
@aplicacion.post("/voz")
def ruta_voz(texto: str = Form(...), voz: str = Form("")):
    ...
    audio, ms = decir_en_voz(texto, voz or os.environ.get("CHASKI_VOZ_QUY", "mama_freddy"))
```

Lo que Chaski le dice al personal en castellano (repreguntar, responder): la app reproduce el `audio_wav_b64` del turno
si viene, y si no viene usa la voz del iPhone. Así que con el Paso 2 alcanza, siempre que el turno devuelva ese audio.

### Paso 3 · La voz del quechua es la de la mamá de Freddy ✅ (decidido)

- **`mama_freddy` es el valor por defecto** (ya está así en los ejemplos de arriba). La enfermera escucha a Chaski con su
  propia voz: es la decisión del producto (SOT F5) y el momento más fuerte del pitch.
- Verifica que `mama_freddy` aparezca en `GET /voces`. Si todavía no está entrenada o servida, **ese es el pendiente
  número uno**, por encima del castellano.
- `p24` queda solo como respaldo de emergencia (`CHASKI_VOZ_QUY=p24` y reinicio), si `mama_freddy` falla en vivo.

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
| [x] | Voz del quechua: `mama_freddy` (Freddy, dom 01:55) |
| [x] | `mama_freddy` aparece en `GET /voces` y suena en `/voz` (verificado por loopmind-05, dom 01:57: 200, 0,9 s) |
| [ ] | Desplegado, avisado por el grupo y probado con `curl` |
