# Para Freddy · «Quise decir esto» en vez de trabarse pidiendo repetir

**Qué cambió:** el servicio ya no deja la consulta parada en «¿me lo repite?». Cuando Chaski
bloquea o no entiende, la misma respuesta trae un campo nuevo, `opciones`, con lo que él
mismo habría dicho. La app muestra esos botones y llama a `/confirmar` con el que se elija.

**Nada que ya leas cambió.** `opciones` es un campo añadido. Una app que lo ignore se comporta
exactamente igual que antes.

## El problema que resuelve

Una sola palabra en castellano dentro de una frase en chanka tumba el turno. Caso real,
grabación `p16_B_066`:

```
oído por el reconocedor : upshashkani para sitamulta
acción                  : no_entendi
lo que se decía          : «Pampachaway, ¿manachu kaqmanta rimariwaq?»
```

El paciente dijo «he tomado paracetamol». El reconocedor partió el préstamo en
`para sitamulta` y la consulta se quedó pidiendo repetir, por una palabra, con toda la
frase bien dicha.

## El campo nuevo

```jsonc
{
  "estado": "dicho", "accion": "no_entendi", "texto_original": "upshashkani para sitamulta",
  "opciones": [
    { "id": "repetir", "etiqueta": "Que lo repita", "texto": null },
    { "id": "propuesta", "etiqueta": "Quise decir esto",
      "texto": "he tomado paracetamol",          // esto es lo que se diría
      "idioma": "spa",                            // en qué idioma
      "glosa": "upyashkani paracetamolta",        // cómo lo leyó Chaski, para revisarlo
      "origen": "upshashkani para sitamulta",     // lo que se había oído
      "cambio": "upshashkani → upyashkani; para sitamulta → paracetamolta",
      "confianza": "media", "para": "personal", "verificado": false,
      "motor": "claude-sonnet-5" }
  ]
}
```

Funciona en las dos direcciones. Del lado de la enfermera, con una frase que el crítico
bloqueó por el medicamento:

```
texto    Lloqe mariyanpi influenza vacunata churasunchik.
glosa    Le vamos a poner la vacuna de la influenza en el brazo izquierdo.
conf     alta
```

Aparece en `/turno`, `/turno/vivo`, `/turno/enfermera`, `/turno/enfermera/vivo` y
`/turno/paciente`. En las rutas en vivo va dentro del evento `resultado`, igual que el resto.

Sale solo cuando hay algo que ofrecer: `accion == "no_entendi"` (cualquier estado), o
`repreguntar` con estado `bloqueado` / `dicho_con_aviso`. Una repregunta normal —«¿cada
cuánto?»— **no** trae opciones: es una pregunta de verdad que espera respuesta.
Si no hay ninguna lectura creíble, tampoco: la lista se descarta y todo queda como antes.

## La ruta nueva

`POST /confirmar` (form)

| campo | qué va |
|---|---|
| `texto` | el `texto` de la opción elegida |
| `idioma` | su `idioma` (`quy` \| `spa`) |
| `para` | su `para` (`paciente` \| `personal`) |
| `dicho` | el `origen` de la opción |
| `lectura` | la `glosa` de la opción (queda en el historial en vez de la frase rota) |
| `contexto` | el contexto del turno anterior, como siempre |

Devuelve el mismo contrato de `/turno/*`: `estado: "dicho_con_aviso"`, `accion: "traducir"`,
`texto_salida`, `audio_wav_b64` con la voz ya hecha, `contexto` actualizado y
`confirmada: true`. Medido: **721 ms**, voz incluida.

El `aviso` viene siempre y hay que mostrarlo:

> Lo confirmó una persona. Chaski no pudo comprobar el dato por su cuenta: la lectura de
> vuelta está para revisarla antes de decir que sí.

## Lo que hay que entender antes de poner el botón

**Confirmar NO verifica.** Esa frase ya pasó por las barreras y el crítico, y lo que las hizo
dudar sigue ahí. Lo que cambia es quién responde: la persona que lee la `glosa` y toca el
botón. Es lo que hace un intérprete humano cuando no está seguro: propone su lectura en voz
alta y espera el sí.

Por eso:
- **Muestra la `glosa` tan grande como el `texto`.** Es lo único que la enfermera puede leer
  para decidir; el quechua no lo puede juzgar.
- **El botón de confirmar no es el primero.** «Que lo repita» va primero.
- **`verificado: false` y el `aviso` van en pantalla**, no escondidos.
- `cambio` dice qué palabra arregló Chaski. Enséñalo: es lo que la enfermera revisa primero.

## Cómo se arma la propuesta

La hace **Claude Sonnet 5**, no NLLB. Probado: NLLB traduce letra por letra y de
`upshashkani para sitamulta` sacó «cuando estoy bebiendo en la silla de lluvia», con una
lectura de vuelta trabada repitiendo `ch'akiypi` diecinueve veces. NLLB no sabe que ahí
dentro hay un medicamento mal oído; el intérprete sí. NLLB queda de respaldo para cuando no
hay red, con un filtro que descarta las propuestas que se traban repitiendo una palabra.

El modelo devuelve `confianza`. En `baja` no se ofrece nada: ruido, sílabas sueltas, o una
frase donde para leerla habría que inventar un número o un medicamento que no está.

## Probarlo sin la app

```bash
U=https://unsubmitted-wally-relatable.ngrok-free.dev
curl -s -X POST "$U/turno/enfermera" -H "ngrok-skip-browser-warning: 1" \
  -F "texto=Le vamos a poner la vacuna de la influenza en el brazo izquierdo" -F "contexto=" \
  | python3 -m json.tool | grep -A6 opciones
```

Dónde está: `ricardo-artifacts/servicio/app.py`, funciones `_con_opciones`,
`_lectura_de_chaski`, `_con_opciones_sse` y la ruta `/confirmar`. Ya corre en la instancia.
Ningún archivo de `app/chaski/` fue tocado.
