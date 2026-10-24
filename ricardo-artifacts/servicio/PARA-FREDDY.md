# Los modelos de voz, listos para que los llames

> Escrito el sábado 24 de octubre de 2026. **La URL cambia cada vez que Ricardo reinicia el túnel**:
> si deja de responder, pídesela y actualiza esta línea.

## URL

```
https://prep-lectures-aurora-density.trycloudflare.com
```

Es HTTPS, así que sirve desde la app de iOS (iOS no acepta HTTP plano). No necesitas llave SSH ni
entrar a la instancia: la cadena es **tu app → esta URL → la Mac de Ricardo → su GPU A10G**.

Compruébala primero:

```sh
curl https://prep-lectures-aurora-density.trycloudflare.com/salud
```

## Las rutas que te sirven

| Ruta | Qué le mandas | Qué devuelve |
|---|---|---|
| `POST /turno/paciente` | `audio` (archivo) | idioma, lo que oyó en chanka, el castellano para la enfermera y los tiempos de cada paso |
| `POST /turno/enfermera` | `texto`, `modo_ensayo`, `forzar` | el chanka, la retraducción a ciegas, el veredicto de tu auditoría y el audio en base64 |
| `POST /voz` | `texto` (en chanka) | el WAV, para pedirlo **después** de mostrar el texto |
| `POST /escuchar` | `audio` (castellano) | texto con Cartesia `ink-whisper` |
| `POST /ver` | `imagen`, `dicho` opcional | lee la caja o la receta con Claude |
| `GET /salud` | — | qué modelo de visión usa y si están las claves |

Todo es `multipart/form-data`, como un formulario de siempre.

## Ejemplos

```sh
# el paciente habla chanka -> lo que la enfermera lee
curl -F "audio=@turno.wav" https://prep-lectures-aurora-density.trycloudflare.com/turno/paciente

# la enfermera responde -> chanka auditado + voz
curl -F "texto=Tome una tableta cada ocho horas" -F "modo_ensayo=true" https://prep-lectures-aurora-density.trycloudflare.com/turno/enfermera

# solo la voz, cuando ya mostraste el texto
curl -F "texto=Huk tabletata upyakunki sapa pusaq horaspi" --output voz.wav https://prep-lectures-aurora-density.trycloudflare.com/voz
```

Desde la app:

```ts
const cuerpo = new FormData();
cuerpo.append("audio", archivoDeAudio);
const r = await fetch("https://prep-lectures-aurora-density.trycloudflare.com/turno/paciente", { method: "POST", body: cuerpo });
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

1. `curl https://prep-lectures-aurora-density.trycloudflare.com/salud` — si no contesta, el túnel se cayó.
2. Avísale a Ricardo: relanza `cloudflared` y la URL cambia.
3. Mientras tanto, la app puede seguir contra las versiones falsas del contrato
   (`ricardo-artifacts/voz/contrato.py`): devuelven datos fijos con la misma forma, así la interfaz
   no se cae aunque no haya modelos.
