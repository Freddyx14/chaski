# Plan del ensayo con la UI — mapeado, sin construir todavía

> Sábado 24 de octubre de 2026. **Esto no se construye hasta que Freddy tenga la UI.**
> Este documento existe para que cuando la tenga, sea conectar y no diseñar.

## Qué es el ensayo

Un turno de consulta, pero invertido: **la máquina hace de paciente y nosotros de personal de salud.**

1. Chaski toma **al azar** uno de los audios en chanka que ya tenemos.
2. Lo reproduce como si fuera el paciente hablando.
3. Nosotros, en el papel de la enfermera, escuchamos **la traducción al castellano**.
4. Si no entendimos o suena raro, **le preguntamos a Chaski** y él explica: qué dijo, qué palabras dudó,
   y qué entendió de cada una.
5. Después al revés: hablamos en castellano por el micrófono y Chaski lo dice en chanka.

Sirve para dos cosas distintas, y conviene no confundirlas: **probar que la cadena entera funciona**, y
**ensayar el pitch** con los dos sentidos del intérprete.

## La cadena, paso a paso

| # | Paso | Quién lo hace | Estado |
|---|---|---|---|
| 1 | Elegir un audio chanka al azar | UI | falta |
| 2 | `POST /entender` con ese audio | mi servicio en la instancia | **falta el servicio** |
| 3 | `mms-lid` decide el idioma | ya corre · 49 ms | ✅ |
| 4 | `omniASR` transcribe y devuelve **N mejores** | ya corre · 1.71 s | ✅ |
| 5 | Claude elige entre las N, corrige y traduce al castellano | Freddy | en curso |
| 6 | Claude se audita: retraduce y compara dosis, horas, fechas | Freddy | ✅ construido |
| 7 | Cartesia Sonic lo dice en castellano | falta la clave en el servicio | clave lista |
| 8 | Nosotros preguntamos y Chaski explica | Freddy | falta |
| 9 | Al revés: micrófono → Cartesia STT → Claude → `mms-tts-quy` | los dos | falta |

**El paso 2 es mío y es lo que bloquea todo lo demás.** Mientras no exista, la UI de Freddy no tiene a
qué llamar y seguirá contra las versiones falsas del contrato.

## Lo que mi servicio tiene que exponer

Tres rutas, las mismas tres firmas del contrato que Freddy ya usa en falso:

```
POST /idioma     {audio}                 -> {codigo: "quy"|"spa", confianza}
POST /entender   {audio, n_mejores}      -> {texto, alternativas: [[texto, puntaje]], segundos, modelo}
POST /hablar     {texto, lengua: "quy"}  -> audio/wav
GET  /salud      -> {modelos_cargados, gpu_gb, version}
```

`/hablar` solo acepta quechua. El castellano lo dice Cartesia **desde la app**, no desde mi servicio: así
la voz no hace un viaje extra a la instancia y de vuelta.

Y hace falta HTTPS, porque iOS no acepta HTTP plano (SOT §4). Con `cloudflared tunnel` sale un certificado
válido sin configurar nada; ngrok gratis corta las sesiones.

## Sobre la clave de Cartesia

**Guardada en `ricardo-artifacts/.env`, que git ignora** (línea 9 del `.gitignore`), con permisos 600. En
el repo queda `.env.example` con un valor de mentira. **No rompe nada**: ningún archivo versionado cambia
y el código lee la clave del entorno, así que si no está, lo que falla es la voz en castellano y nada más.

**Rótala cuando termine el hackathon.** La pegaste en un chat, así que vive en ese historial.

**El plan gratuito da 20,000 créditos al mes y una minuto de voz cuesta 750-800**, o sea **unos 27 minutos
de audio en total**, con 2 peticiones de voz en paralelo y 8 de reconocimiento. Para un demo alcanza.
Para generar datos no: **no uses Cartesia para producir conjuntos de audio**, solo en el camino en vivo.
Y revisa si el código de Cal Hacks suma créditos, porque el SOT lo da por hecho.

## Qué audios usamos para el papel del paciente

Hoy tenemos `datos/prueba_minima/quy_todas.wav`, que es voz sintética de MMS-TTS. Sirve para probar la
cadena, **no para el pitch**: un jurado que oiga voz robótica haciendo de paciente no ve una consulta, ve
una demostración de software.

Cuando lleguen las grabaciones de las familias, el papel del paciente lo hace **una voz humana real**, y
de preferencia la de la persona que quedó fuera del entrenamiento. Ahí el ensayo deja de ser una prueba
técnica y se vuelve el demo.

## Cómo sabemos que salió bien

- La cadena entera responde en menos de **4 segundos** por turno. Hoy llevamos 1.76 s medidos (49 ms + 1.71 s)
  y faltan Claude y la voz.
- Los dos sentidos funcionan, no solo quechua → castellano.
- Cuando preguntamos «¿qué dijo?», Chaski muestra **las N mejores hipótesis** y cuál eligió. Eso es lo que
  convierte el demo en una explicación del sistema en vez de un truco.
- Si la auditoría bloquea algo, se ve en pantalla por qué. **Un bloqueo en vivo es mejor demo que una
  traducción perfecta**: demuestra que el sistema sabe cuándo callarse.

## Lo que puede salir mal, y qué hacemos

| Riesgo | Plan B |
|---|---|
| La instancia se cae o el túnel se corta | La UI vuelve a las versiones falsas del contrato; el demo sigue, sin modelo |
| Cartesia se queda sin créditos a media demo | La voz del sistema iOS dice el castellano. Feo, pero vivo |
| El micrófono del venue mete ruido | Tener grabados de antemano los turnos del ensayo |
| Claude tarda más de 3 s por turno | Es la decisión D15: medir los tres modelos y quedarse con el más rápido que no pierda acierto |
