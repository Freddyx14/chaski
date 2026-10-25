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

## Las páginas, por si quieres abrirlas en el navegador

Todo cuelga del mismo dominio. Desde el 24-oct lo sirve la instancia, no la laptop de Ricardo.

| Página | Para qué |
|---|---|
| `/` | índice |
| `/flujo` | la demo del turno completo, con Chaski |
| `/corregir` | el etiquetador: transcribe, se corrige el escrito, se parte y se une |

`/corregir` ya no es local. Corría en la laptop de Ricardo con un túnel SSH; ahora está en la misma
URL que todo lo demás, así que lo pueden abrir los dos.

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


---

## `/ver` ya arma la receta (sáb 24-oct)

Para la feature del medicamento. `/ver` seguía devolviendo qué es y para qué sirve; ahora también
devuelve **la posología y la indicación lista para traducir**, con la misma forma que usa la
auditoría, así que entra por el camino de siempre sin tratarla aparte.

Con la caja de paracetamol de prueba:

```json
{
 "medicamento": "Paracetamol", "concentracion": "500 mg",
 "para_que_sirve": "Baja la fiebre y calma el dolor de cabeza, músculos y otras molestias.",
 "cantidad": 1.0, "cada_horas": 8.0, "dias": null,
 "indicacion": "Tome 1 tableta cada 8 horas.",
 "posologia_de": "caja",
 "confirmar": true,
 "porque_confirmar": "la pauta viene impresa en la caja, es la del fabricante para adultos; confírmela o corríjala para este paciente",
 "advertencias": ["Mantener fuera del alcance de los niños", "No exceder 4 tabletas al día"],
 "faltan": []
}
```

### Los tres campos que te importan para la pantalla

**`posologia_de`** dice de dónde salieron los números, y los tres casos se tratan distinto:

| | Qué significa | Qué debería hacer la app |
|---|---|---|
| `"receta"` | lo recetó alguien para **este** paciente | usarlo |
| `"caja"` | es la pauta del fabricante **para un adulto cualquiera** | **pedir confirmación** |
| `"falta"` | no estaba en ningún lado | pedirle los dos números a la enfermera |

La diferencia entre `receta` y `caja` es la que más importa. La caja dice qué es el medicamento, no
cuánto le toca a quien está enfrente: un niño, una embarazada o alguien que ya toma otra cosa
necesitan otra pauta. Por eso `confirmar: true` y el motivo ya escrito en castellano, listo para
mostrar.

**`faltan`** es la lista de los campos que hay que pedir (`cantidad`, `cada_horas`). Es exactamente
los dos parámetros que decía Ricardo: cada cuántas horas y cuántos días.

**`indicacion`** es la frase lista para traducir. **No la escribe el modelo**: la arma una plantilla
en código a partir de los números ya leídos. Una plantilla no puede cambiar una dosis mientras
redacta. El modelo lee; componer es de código.

Pasa por `/turno/enfermera` como cualquier otro texto, así que la auditoría la revisa igual.

### Lo que no hace, a propósito

No deduce una dosis del nombre del medicamento ni de lo que suele indicarse. Si no está escrita,
`posologia_de: "falta"` y los campos en null. Una dosis inventada que suena razonable es el peor
error que este sistema puede cometer, y es el que más fácil pasa desapercibido.


---

## Las cuatro voces de Chaski (sáb 24-oct, noche)

Hay cuatro voces entrenadas más la de fábrica. Se eligen por nombre, en la misma ruta de siempre.

```sh
curl …/voces
{"voces":["base","mama_freddy","p16","p24","papa_ricardo"],"por_defecto":"p24"}

curl -X POST …/voz -F "texto=Sapa pusaq horapi huk pastillata upyay" -F "voz=p16" -o voz.wav
```

`voz` también funciona en `/hablar` del servicio de voz. Si pides una que no existe, responde con
`base` en vez de dar error: en una demo es mejor una voz robótica que un 500.

| voz | quién | datos | fuente |
|---|---|---|---|
| `base` | Meta, sin entrenar | — | `facebook/mms-tts-quy` |
| `p24` | familiar de Freddy | 165 clips · 13.7 min | formulario, texto verificado |
| `p16` | papá de Ricardo | 175 clips · 11.4 min | formulario, texto verificado |
| `mama_freddy` | mamá de Freddy | 13 clips · 1.6 min | WhatsApp, texto automático |
| `papa_ricardo` | papá de Ricardo | 15 clips · 0.6 min | WhatsApp, texto automático |

Las dos últimas parten del checkpoint de `p24`, no del modelo de fábrica. Con 1.6 y 0.6 minutos es
probable que suenen más a `p24` que a la persona nueva: el ajuste no tuvo con qué moverlas mucho.

Los audios para comparar están en `ricardo-artifacts/reports/voces/<voz>/`, con el A/B/C de tu §11:
`*_A_base.mp3` (Meta), `*_B_ajustada.mp3` (esa voz) y `C_real.mp3` (la persona), para las frases
`dosis`, `control`, `alarma` y `saludo`.

### 🔴 La medición no respalda «la voz ajustada se entiende mejor»

La prueba de ida y vuelta que pediste —las 24 frases de emergencia pasadas por cada voz y luego por
el reconocimiento ajustado— salió al revés:

| voz | WER de ida y vuelta |
|---|---|
| **base (Meta)** | **45.8 %** |
| p16 | 74.6 % |
| p24 | 89.8 % |
| papa_ricardo | 93.2 % |
| mama_freddy | 98.3 % |

**La voz de fábrica es la más entendible y las ajustadas lo son menos.** Es exactamente el fallo
silencioso que esta prueba existía para encontrar: suena más a la persona y se entiende peor.

Dos cosas antes de sacar conclusiones:

- Mide **inteligible para nuestro reconocedor**, que se entrenó con voces humanas reales. El habla
  sintética le queda fuera de dominio, y las ajustadas puede que se le hayan ido más lejos. Una
  persona podría ordenarlas distinto — por eso la prueba a ciegas con tu mamá sigue siendo la que
  decide.
- El texto del banco no está en la ortografía normalizada con la que entrenamos el reconocedor.

Lo que sí se puede afirmar sin riesgo: **A suena a robot y B suena a persona**, y eso se oye en los
mp3. Lo que **no** se puede afirmar todavía es que B se entienda mejor. Si en el pitch va esa frase,
hay que medirla con personas antes.

Mi recomendación para el modo emergencia: usar **la grabación real** donde exista, y `base` donde no.
Es donde una palabra mal oída cuesta más, y ahí el número manda sobre el timbre.


---

## Todo lo nuevo en una página (sáb 24-oct, noche)

Mismo dominio de siempre. Las cinco rutas nuevas están probadas contra la URL pública.

### `/mt` — traducir sin Claude, en las dos direcciones

```sh
POST /mt  -F "texto=Tome una pastilla cada ocho horas"
{"texto":"Sapa pusaj horaspi uj tabletata tomay.","ms":306}

POST /mt  -F "texto=Sapa pusaq horapi huk pastillata upyay" \
          -F "desde=quy_Latn" -F "hacia=spa_Latn"
{"texto":"Toma una pastilla cada ocho horas","ms":252}
```

NLLB-200-1.3B en la instancia. **Sin red, sin costo por llamada, 2.6× más rápido que Claude.**

`/traducir` sigue siendo Claude con auditoría. Las dos están: el botón para cambiar es decisión tuya.

### `/voces` y `/voz` — cinco voces

```sh
GET  /voces
{"voces":["base","mama_freddy","p16","p24","papa_ricardo"],"por_defecto":"p24"}

POST /voz  -F "texto=Allinllanchu mamay" -F "voz=p16" -o voz.wav
```

### `/emergencia` — el banco con el audio ya resuelto

Lo que le faltaba a tu `banco.json` era el campo `audio`. Aquí viene lleno:

```sh
GET /emergencia?voz=p24
{"voz":"p24",
 "voces":["base","mama_freddy","p16","p24","papa_ricardo"],
 "frases":[{"id":"emg-dolor-donde","es":"¿Dónde le duele?","quy":"¿Mayta nanan?",
            "audio":"/emergencia/audio/p24/emg-dolor-donde.mp3"}, …]}
```

Las 24 están sintetizadas en las cinco voces: **120 archivos ya generados**. La app toca y suena, sin
esperar a ningún modelo. Cambiar `?voz=` cambia las URL de golpe.

### `/medicamento` — foto a quechua en una llamada

`/ver` + traducción auditada + voz, para que el teléfono no encadene tres peticiones.

---

## Por qué NLLB y no Claude, con los números

Medido sobre **62 frases que las familias tradujeron el 24-oct**. Ningún modelo publicado las ha
visto, y cada una lleva **4.8 referencias** —una por persona— así que nadie pierde puntos por elegir
la variante de otro hablante.

| motor | chrF++ | una petición | dónde corre |
|---|---|---|---|
| claude-sonnet-5 | **44.55** | 1496 ms | nube |
| **nllb-1.3B** | 34.72 | **565 ms** | nuestra GPU |
| nllb-600M | 28.58 | 346 ms | nuestra GPU |

Claude traduce mejor. NLLB responde antes y no depende de la red.

**Lo que hace aceptable el cambio: la auditoría no depende del traductor.** Lo que salga de NLLB pasa
por la misma comparación de dosis, horas y días que lo de Claude. Un traductor más flojo con la misma
guarda no puede decir una dosis equivocada — dirá menos cosas, porque bloqueará más seguido.

### Lo que probamos y descartamos

| modelo | qué pasó |
|---|---|
| `nllb-600M` ajustado por nosotros | **el número estaba contaminado**: nuestro filtro dejó pasar 58 de las 100 frases de evaluación al entrenamiento. Descartado |
| `madlad-400-3B` | chrF++ 12.69 sin entrenar, muy por debajo |
| `Thermostatic/rosettia-chanka-4b` | el checkpoint no carga: `lm_head`, `embed_tokens` y `norm` salen MISSING y escupe ruido. Y 5233 ms por frase, 3.5× más lento que Claude |
| `makitty/QuechuaGPT-chanka-4B-lora-v2` | HTTP 401, es privado |

### 🔴 Dos cosas del banco que son tuyas

```
emg-alergia   ¿Es alérgico a algún medicamento?   →   ¿Ruparin pukyupakunki?
```

`rupay` es calor o fiebre. Eso no parece decir «alérgico». Hay otras entradas con `quy` vacío.

**El texto antes que la voz:** una voz perfecta diciendo algo equivocado es peor que una robótica
diciéndolo bien. Esas frases las tiene que ver tu mamá antes de que suenen en una posta.


---

## D43 aplicado: traduce Claude. Los seis pasos, hechos (dom 25-oct, madrugada)

Todo probado contra la URL pública. Nada que cambies de tu lado salvo lo que digo abajo.

| # | Qué pedías | Estado |
|---|---|---|
| 1 | `git pull` | hecho |
| 2 | Traducir con Claude, `CHASKI_NLLB_URL` vacía | **hecho** · `"motor":"claude"` |
| 3 | `/turno/paciente` sin 500 | **hecho** · devuelve 200 con audio |
| 4 | `/turno/enfermera/vivo` | **hecho** · `decision` a los 4.5 s |
| 5 | Voz durante el crítico (`voz_fn`) | **hecho** · vuelve en `audio_wav_b64` |
| 6 | Reiniciar, probar, push | hecho |

### 2 · Claude traduce

```sh
POST /turno/enfermera -F "texto=Tome una pastilla de paracetamol cada ocho horas durante tres días"
{"estado":"dicho","motor":"claude",
 "texto_salida":"Huk paracetamol pastillata tomay, sapa pusaq horamanta, kimsa p'unchaw…",
 "ms":{"total":13110}}
```

`CHASKI_NLLB_URL` va vacía, como pediste. `motor=nllb` sigue funcionando para el modo sin conexión y
no depende de esa variable: son 483 ms contra 5042, con las mismas barreras y el mismo crítico.

**Sobre los 13.1 s contra los 8.3 s que mediste:** la diferencia es la síntesis de voz, que ahora va
dentro del turno (paso 5). El audio viene listo en la respuesta en vez de pedirse después, así que la
espera que siente la enfermera es menor aunque el número total suba. Si prefieres el turno sin audio,
`con_audio=false` y vuelve a ~8 s.

### 3 · `/turno/paciente` ya responde

```sh
POST /turno/paciente -F "audio=@p16_C_001.wav"
{"estado":"dicho","accion":"traducir",
 "texto_original":"punchaymanta umay nanashqa",
 "texto_pulido":"Punchawmanta umay nanawan.",
 "texto_salida":"Desde hoy me duele la cabeza",
 "audio_wav_b64":"UklGRi…"}
```

Daba 500 porque la ruta vieja llamaba a nuestro propio flujo. Ahora oye con `/entender` de la GPU y
le pasa a `chaski.servicio.turno` el texto crudo **y las N mejores alternativas**, que es lo que B1
necesita para bloquear cuando el reconocedor duda de un número o un medicamento.

### 4 · La ruta en vivo

```sh
POST /turno/enfermera/vivo        # text/event-stream

event: decision
data: {"accion":"repreguntar","texto_pulido":"¿Qué pastilla le digo que tome?","ms_decidir":4482.9}

event: resultado
data: {"estado":"dicho","accion":"repreguntar", …}
```

`decision` es para mostrar; **lo que se dice es solo `resultado`**.

### 5 · La voz se hace mientras el crítico revisa

`voz_fn` sintetiza en paralelo con la revisión. Si el crítico bloquea, el audio se descarta y nunca
suena: generar no es decir. Usa la voz `p24` para quechua y la base para castellano.

### El banco ya suena

`GET /banco?tag=emergencia` devuelve las 24 con su `audio` apuntando a mp3 que ya existen. Toca y
suena, sin modelo en el camino. Cambiar la voz es cambiar `p24` por `p16`, `mama_freddy`, `papa_ricardo`
o `base` en la URL: los 120 archivos están generados.

### 🔴 Lo que sigue siendo tuyo

```
emg-alergia   ¿Es alérgico a algún medicamento?   →   ¿Ruparin pukyupakunki?
```

`rupay` es calor o fiebre. Eso no dice «alérgico». Que lo vea tu mamá antes del pitch: una voz
perfecta diciendo algo equivocado es peor que una robótica diciéndolo bien.


---

## Redespliegue del dom 00:20

Las tres cosas que pediste, hechas y probadas contra la URL pública.

**D41 activo.** El servicio volvió a desplegarse con tu `chaski` al día, así que el traductor ya recibe
las frases revisadas de la enfermera como ejemplos. `CHASKI_EJEMPLOS` va sin definir: su valor por
defecto es 1 y la lee tu propio código.

El entorno de la instancia quedó así:

```
CHASKI_MODELO_PRINCIPAL=claude-opus-5
CHASKI_MODELO_CRITICO=claude-sonnet-5
CHASKI_PENSAR_TRADUCIR=medium
CHASKI_TRADUCIR_ANTICIPADO=1
CHASKI_NLLB_URL=          (vacía)
```

**D40 → D43** corregido en `servicio/app.py`, `servicio/desplegar.sh` y el título de este archivo.

**`/turno/paciente` ya no se cae con .m4a ni .webm.** En vez de documentar que solo acepta WAV, lo
convierte: ffmpeg a 16 kHz mono antes de mandárselo al reconocedor. Probado con los tres:

```
wav    200
m4a    200   oído: «punchaymanta umay nanashqa»
webm   200   oído: «punchaymanta umay nanashqa»
```

Misma transcripción en los tres. La app manda WAV y seguía funcionando, pero un iPhone graba .m4a y
un navegador .webm: era un 500 esperando a que alguien probara desde otro lado.


---

## D44: memoria automática (dom 08:30)

Puesta y probada. Vive **fuera** de lo que `desplegar.sh` sincroniza, que era el punto:

```
CHASKI_MEMORIA_AUTO=1
CHASKI_MEMORIA_RUTA=/opt/dlami/nvme/chaski/orquestador/memoria/memoria_auto.jsonl
```

Comprobado que sobrevive: se corrió un turno, se volvió a desplegar, y la línea sigue ahí.

```
turno  →  memoria: 1 línea
redespliegue  →  memoria: 1 línea
```

Para ver y aprobar, desde la instancia:

```sh
cd /opt/dlami/nvme/chaski/orquestador
PYTHONPATH=$PWD ./venv/bin/python -m chaski.memoria
PYTHONPATH=$PWD ./venv/bin/python -m chaski.memoria aprobar <ID>
```

### El turno volvió a ~8 s

```
estado dicho · motor claude · total 7649 ms
```

Con `CHASKI_EJEMPLOS` y la traducción anticipada activos, el turno queda donde lo mediste. Los 13.1 s
de antes eran el despliegue viejo, sin esas dos.

### Lo que quedó verificado después del último despliegue

```
GET  /salud                  200
GET  /banco?tag=emergencia   200   24 frases con audio
GET  /voces                  200   5 voces
POST /turno/enfermera        200   motor claude, 7.6 s
POST /turno/enfermera/vivo   200   decision + resultado
POST /turno/paciente         200   wav, m4a y webm
```

### Dos cosas de tu documento que ya no aplican

- **`/turno/paciente` con .webm y .m4a ya no da 500.** Los convierte con ffmpeg antes de reconocer.
- **`chaski/` no se sincroniza con `--delete`** desde acá, así que la memoria no corría ese riesgo ni
  antes. Igual la puse fuera: que dependa de un detalle de mi script es exactamente lo que no quieres.


---

## 🔊 La voz arreglada (dom 25-oct, mañana)

Los tres pasos de tu sección, hechos y verificados contra la URL pública.

| Hecho | Qué |
|---|---|
| ✅ | `voz_castellano` en `flujo.py` con Cartesia Sonic + `CHASKI_VOZ_ES` |
| ✅ | `_voz_para_chaski` con `CHASKI_VOZ_QUY` y respaldo |
| ✅ | `/voz` con `CHASKI_VOZ_QUY` (paso 2b) |
| ✅ | Quechua con `mama_freddy` |
| ✅ | Desplegado y probado |

### Cómo sé que de verdad es Cartesia y no el respaldo

La frecuencia lo delata, y por eso la miré en vez de confiar en que no hubo excepción:

```
castellano   24000 Hz   ← Cartesia
quechua      16000 Hz   ← mms-tts-quy ajustado con tu mamá
respaldos usados: 0
```

Si el castellano saliera a 16 kHz sería Meta leyendo español otra vez, que es justo el ruido que
veníamos a quitar.

**Voz castellana: Ximena** (`3597a26f-80ef-4bd5-8101-9699bc764917`), latina, clara y pausada. Está en
el entorno como `CHASKI_VOZ_ES`, así que cambiarla es una variable y un reinicio.

### Un problema que no estaba en tu lista

El WAV de Cartesia venía con la cabecera de un flujo: **un audio de 1.6 s declaraba durar 89 478 s.**
Cartesia la escribe antes de saber cuánto va a durar. Un reproductor que le crea muestra una pista de
24 horas o no deja moverse por ella.

Se reescriben los tamaños con los bytes que de verdad hay, después de recibir. Ahora:

```
castellano: 24000 Hz · 1.6s · 76878 bytes
```

### El entorno quedó así

```
CHASKI_VOZ_QUY=mama_freddy
CHASKI_VOZ_ES=3597a26f-80ef-4bd5-8101-9699bc764917
CHASKI_MEMORIA_AUTO=1
CHASKI_MEMORIA_RUTA=…/orquestador/memoria/memoria_auto.jsonl
CHASKI_NLLB_URL=        (vacía)
```

`p24` sigue como respaldo: `CHASKI_VOZ_QUY=p24` y reiniciar, si `mama_freddy` falla en vivo.

### De tu lado no cambia nada

El quechua lo pide la app a `/voz` sin mandar `voz`, y ahora eso devuelve `mama_freddy` en vez de
`p24`. El castellano viene en el `audio_wav_b64` del turno. Build 16 debería sonar bien sin tocar la app.


---

## La foto ahora devuelve una receta corta para el paciente (dom 03:10)

`/medicamento` ya no devuelve solo qué es y para qué sirve: arma **la receta en frases cortas**, lista
para que el paciente se la lleve.

```sh
POST /medicamento -F "imagen=@caja.jpg" -F "con_audio=true"
```

```json
{
 "se_dice_en_voz": ["Tome 1 tableta de Paracetamol de 500 mg.", "Cada 8 horas."],
 "solo_se_muestra": ["Es para esto: Baja la fiebre y calma el dolor de cabeza, muscular…",
                     "No exceder 4 tabletas al día.",
                     "Mantener fuera del alcance de los niños."],
 "receta_corta": [ …las dos listas juntas, por si quieres mostrarlas en orden… ],
 "faltan": [],
 "quechua": "Paracetamol 500 mg nisqamanta huk tabletata tomay, sapa pusaq…",
 "aprobado_por_auditoria": true,
 "audio_wav_b64": "…"
}
```

### Los dos campos que importan para la pantalla

**`se_dice_en_voz`** es la dosis. Pasa por la auditoría y es lo que suena.
**`solo_se_muestra`** es el contexto: para qué sirve y las advertencias de la caja. Se muestra, no se dice.

Están separados por una razón concreta, y la encontré probando: con todo junto la auditoría **bloqueaba**.

```
motivo: cambió un dato crítico: partes_cuerpo
```

«Calma el dolor de cabeza» trae una parte del cuerpo, la retraducción la pierde, y el comparador la
marca como dato cambiado. Pero eso no es una indicación: nadie se hace daño porque la explicación de
para qué sirve pierda un matiz. La guarda revisa **lo que puede hacer daño** —la dosis— y el resto se
muestra, que es lo que de verdad es.

### Lo que la receta NO hace

- **No inventa una dosis.** Sin posología escrita, `receta_corta` viene en `null` y `faltan` dice qué
  pedirle a la enfermera. Una receta inventada que suena razonable es el peor error posible aquí.
- **No agrega consejos.** Ni «no la deje aunque se sienta bien» ni «tómela con agua». Son buenos
  consejos que nadie dijo, y agregar una indicación clínica que no dio el personal es justo lo que
  este sistema no debe hacer.
- **Las advertencias se copian tal cual** de la caja: son del fabricante, no nuestras.

La arma una plantilla en código desde los números ya leídos, igual que `indicacion`. El modelo lee;
componer es de código.
