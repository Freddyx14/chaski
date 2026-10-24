# Los modelos de voz, listos para que los llames

> **La URL de abajo se actualiza sola.** Ricardo corre `bash servicio/publicar_url.sh` y el cambio llega
> por git, con la hora, en `servicio/url.json`. Si deja de responder, haz `git pull` antes de preguntar.
>
> El dominio está reservado en la cuenta de ngrok, así que no cambia aunque se reinicie el túnel.

## URL

```
https://unsubmitted-wally-relatable.ngrok-free.dev
```

Es HTTPS, así que sirve desde la app de iOS (iOS no acepta HTTP plano). No necesitas llave SSH ni
entrar a la instancia.

**Cambió lo que hay detrás (24-oct, 18:00 UTC). La URL es la misma.** Antes la cadena pasaba por la
Mac de Ricardo; si él cerraba la laptop, se te caía. Ahora es **tu app → esta URL → la instancia**, y
nada más: el orquestador y los modelos corren en la misma máquina y se hablan por `127.0.0.1`. No
tienes que cambiar una sola línea.

Un efecto secundario bueno: el turno del paciente ya no cruza internet para llegar a la GPU. Antes
el audio iba Mac → instancia → Mac; ahora no sale de la instancia.

Compruébala primero:

```sh
curl https://unsubmitted-wally-relatable.ngrok-free.dev/salud
```

## Las rutas que te sirven

| Ruta | Qué le mandas | Qué devuelve |
|---|---|---|
| `POST /turno/paciente` | `audio` (archivo) | idioma, lo que oyó en chanka, el castellano para la enfermera y los tiempos de cada paso |
| `POST /turno/enfermera` | `texto`, `modo_ensayo`, `forzar` | el chanka, la retraducción a ciegas, el veredicto de tu auditoría y el audio en base64 |
| `POST /voz` | `texto` (en chanka) | el WAV, para pedirlo **después** de mostrar el texto |
| `POST /escuchar` | `audio` (castellano) | texto con Cartesia `ink-whisper` |
| `POST /ver` | `imagen`, `dicho` opcional | lee la caja o la receta con Claude |
| `POST /idioma` | `audio` (archivo) | `{codigo, confianza, probabilidades, ms}` — solo el detector, sin Claude |
| `POST /resumen` | `turnos` (JSON), `rol` | el resumen de la consulta según quién lo lee |
| `GET /salud` | — | qué modelo de visión usa y si están las claves |

Todo es `multipart/form-data`, como un formulario de siempre.

## Ejemplos

```sh
# el paciente habla chanka -> lo que la enfermera lee
curl -F "audio=@turno.wav" https://unsubmitted-wally-relatable.ngrok-free.dev/turno/paciente

# la enfermera responde -> chanka auditado + voz
curl -F "texto=Tome una tableta cada ocho horas" -F "modo_ensayo=true" https://unsubmitted-wally-relatable.ngrok-free.dev/turno/enfermera

# solo la voz, cuando ya mostraste el texto
curl -F "texto=Huk tabletata upyakunki sapa pusaq horaspi" --output voz.wav https://unsubmitted-wally-relatable.ngrok-free.dev/voz
```

Desde la app:

```ts
const cuerpo = new FormData();
cuerpo.append("audio", archivoDeAudio);
const r = await fetch("https://unsubmitted-wally-relatable.ngrok-free.dev/turno/paciente", { method: "POST", body: cuerpo });
const d = await r.json();   // d.chanka_oido, d.castellano, d.pasos
```

## Lo que tarda cada cosa, medido

| Paso | Tiempo |
|---|---|
| Detectar idioma | 49 ms |
| Oír chanka (`omniASR_LLM_300M`) | 1.7 s por cada 16 s de audio |
| Traducir y auditar, **rápido** | **5.1 s** (era 26 s con Opus en serie) |
| Hablar chanka (`mms-tts-quy`) | 0.5 s |
| Leer una caja con Claude | 2.3 s |

La primera llamada después de un reinicio tarda 20 s más: es el modelo cargando en la GPU. Las
siguientes van a velocidad normal.

## Dos cosas que conviene que sepas

**`/turno/enfermera` usa tu propia auditoría**, importada de `app/rimay/auditoria.py`. Pero la corre
en paralelo y con modelos mezclados (`servicio/auditoria_rapida.py`): Sonnet traduce, Haiku saca los
hechos y retraduce, y el glosario viaja en el `system` con caché. De ahí los 5.1 s. Si prefieres tu
versión original, manda `rapido=false`.

**`/voz` existe aparte a propósito.** Pide primero el texto y muéstralo; pide el audio después. Así el
usuario ve el chanka en 5 s en vez de esperar 5.6 s a que además se genere la voz.

## Si deja de responder

1. `curl https://unsubmitted-wally-relatable.ngrok-free.dev/salud` — si no contesta, el túnel se cayó.
2. Avísale a Ricardo: relanza `cloudflared` y la URL cambia.
3. Mientras tanto, la app puede seguir contra las versiones falsas del contrato
   (`ricardo-artifacts/voz/contrato.py`): devuelven datos fijos con la misma forma, así la interfaz
   no se cae aunque no haya modelos.


---

## Dos cosas medidas el 24-oct que te tocan a ti

### 1. `proxima_cita_en_dias` se inventa un número

Medido así:

```
original      : Su control es el lunes
chanka        : Controlniykiqa lunesmi kanqa.      <- correcto
retraducción  : Tu control será el lunes.          <- correcto
DIFF proxima_cita_en_dias: None -> 3
```

La traducción está bien y dice el mismo día. Lo que pasa es que el extractor convierte «lunes» en un
número de días en la vuelta y no en la ida. Nadie puede sacar días de un nombre de día sin saber la
fecha de hoy, así que ese 3 es ruido y bloquea una frase correcta.

Lo tapé solo de mi lado (`artefacto_de_dia` en `servicio/auditoria_rapida.py`), con una regla
estrecha: solo ese campo, y solo cuando los dos textos nombran el mismo día. No toqué tu esquema
porque es tuyo. La solución de fondo es tuya: o el extractor recibe la fecha de hoy, o
`proxima_cita_en_dias` no se deduce de un nombre de día.

### 2. La guarda solo protege los campos que existen en `Hechos`

Prueba con verdad de referencia (`voz/medir_guarda.py`): se toma el chanka correcto, se le inyecta un
error clínico a propósito y se mira si la auditoría lo atrapa. Resultado sobre indicaciones de posta:

```
falsos bloqueos  0/6
fugas            3/6
```

Las tres fugas, con su retraducción:

| Original | Lo que dijo el quechua roto | ¿Bloqueó? |
|---|---|---|
| Son siete días de tratamiento | «Cuatro días será tu curación» | no |
| Venga en ayunas | «Ven habiendo comido, algo comerás» | no |
| Si el bebé no se mueve, venga | «Cuando el bebito se mueva, ven» | no |

Lo importante: **la retraducción captó el error en castellano las tres veces.** La información estaba
ahí. Lo que la perdió fue la extracción a `Hechos`, porque no hay campo para duración del
tratamiento, ni para ayuno, ni la negación de una condición de alarma sobrevive a `ir_ya_si`.

La tercera es la grave: invierte cuándo traer a un bebé que no se mueve.

Propuesta, y queda en tus manos porque el esquema es tuyo: además de comparar por campos, comparar la
retraducción contra el original directamente. Los campos atrapan dosis y horas, que es para lo que
están; lo demás se les escapa entero.


---

## `/idioma` y `/resumen`, listas (sáb 24-oct)

Las dos que pediste. Están puestas, desplegadas en la instancia y probadas contra la URL pública.
No cambia nada de tu lado: son las rutas que tu app ya llamaba.

**`/idioma`** reenvía al servicio de voz, que ya tenía `mms-lid-512` cargado:

```
POST /idioma  (audio)
{"codigo":"quy","confianza":1.0,"probabilidades":{"spa":0.0,"quy":1.0},"ms":517.2}
```

517 ms ahí son el modelo con el audio largo de prueba; con un turno corto son los 49 ms de siempre.
Se puede preguntar en cada turno en vez de alternar los lados a mano.

**`/resumen`** expone `chaski.resumen` tal cual. Probada con una consulta de cuatro turnos donde uno
venía `bloqueado`, que es el caso que importa:

```
turno bloqueado : «Si hay sangrado, venga de inmediato a la posta»

indicaciones      ['Tomar una pastilla cada ocho horas por tres días']
senales_de_alarma []
no_se_dijo        ['Si hay sangrado, venga de inmediato a la posta']
```

La regla aguanta: lo bloqueado no salió como indicación ni como señal de alarma, salió en `no_se_dijo`.
Es lo correcto — al paciente nunca se le dijo, y la enfermera tiene que enterarse de eso.

Rol `personal` escribe en castellano clínico; rol `paciente` tutea y arma el `texto_para_decir`.
Tardan 2.8 s y 4.7 s.

**Una cosa para que decidas tú.** Un turno `dicho_con_aviso` («Su control es el lunes») no salió en
`proxima_cita` sino en `dudas`, y en el resumen de paciente sí apareció en `texto_para_decir`. Puede
ser lo que querías —se dijo con aviso, así que dudar es razonable— pero son dos criterios distintos
entre roles. El prompt es tuyo; yo no lo toqué.
