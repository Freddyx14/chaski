# Chaski · app iOS (Expo SDK 58)

Intérprete castellano ↔ quechua chanka para la posta de Pilpichaca. Diseño: tablero de Pencil (D26) con los
ajustes de `../design/specs/02-pulido-ui.md`; para los dos lados, personal de salud o paciente (D27).
Colores **solo** desde `../design/tokens.json`; Chaski desde `../avatar/` (sin copias, por `metro.config.js`).

## Pantallas

| Ruta | Qué |
|---|---|
| `bienvenida` | Onboarding: idioma → nombre → ¿personal de salud o paciente? |
| `index` | La consulta: listo, grabando, pensando, dicho, dicho con aviso, bloqueado, respuesta del paciente, error |
| `receta` | F9 + F6: foto → `/ver` → la enfermera confirma los datos → indicación por plantilla → traducida y auditada → «¿me lo repite?» con lista de lo entendido |
| `emergencia` | Modo emergencia (C11, D35): frases verificadas del banco (`GET /banco?tag=emergencia`, si no `src/chaski/banco-demo.json`), toca y suena. Las frases con quechua pendiente `[revisar…]` no se dicen nunca |
| `historial` | Los turnos de la consulta |
| `resumen` | Nota clínica (personal) o lo que hay que hacer en casa (paciente), con audio en quechua auditado |
| `ajustes` | Dirección del servicio y cambio de perfil. Se entra con un **toque largo en «Chaski»** |

## Correr

```bash
npm install
npx expo start --go --ios          # simulador con Expo Go
npm test                           # lógica pura (node --test)
npx tsc --noEmit
```

## El servicio (HTTPS)

La app habla con `ricardo-artifacts/servicio/app.py`. iOS no acepta HTTP plano, así que en la máquina donde corre
el servicio se abre un túnel:

```bash
# hoy: ngrok fijo en la instancia de Ricardo, publicado en ricardo-artifacts/servicio/url.json
cloudflared tunnel --url http://localhost:8000
```

Copia la dirección `https://….trycloudflare.com` en Ajustes → «Guardar y probar». Cambia cada vez que se abre
el túnel. Rutas que usa: `/idioma` (decide quién habló en cada turno, D11; si falla, manda la alternancia), `/escuchar`, `/turno/enfermera`, `/turno/paciente`, `/voz`, `/ver`, `/resumen`, `/salud`.

## Modo demo (sin servicio)

Cada estado se abre con un enlace, para revisar pantallas o como respaldo si falla el wifi del jurado:

```
chaski:///?demo=listo|grabando|pensando|dicho|aviso|bloqueado|paciente|error   [&idioma=quechua] [&rol=paciente]
chaski:///resumen?demo=1&rol=personal|paciente
chaski:///?demo=pregunta|respuesta|no_entendi|frase      (intérprete agente, D32)
chaski:///receta?demo=datos|dicho|resultado
chaski:///emergencia
```

En el simulador con Expo Go: `xcrun simctl openurl booted "exp://127.0.0.1:8081/--/?demo=dicho"`.

## TestFlight

Por Xcode con la llave de App Store Connect, no por EAS (se traba en preguntas interactivas). Bundle
`lat.loopmind.rimay`, equipo `P7493694QL`.

```bash
npx expo prebuild -p ios --clean
xcodebuild -workspace ios/Chaski.xcworkspace -scheme Chaski -configuration Release \
  -destination 'generic/platform=iOS' -archivePath build/Chaski.xcarchive archive \
  DEVELOPMENT_TEAM=P7493694QL CODE_SIGNING_ALLOWED=NO
xcodebuild -exportArchive -archivePath build/Chaski.xcarchive -exportOptionsPlist ExportOptions.plist \
  -exportPath build/export -allowProvisioningUpdates \
  -authenticationKeyPath ~/.appstoreconnect/private_keys/AuthKey_PB2L3A68T7.p8 \
  -authenticationKeyID PB2L3A68T7 -authenticationKeyIssuerID 4bd118b5-a814-4813-997a-e7a61e89ee82
```

Para cada build nuevo, sube `ios.buildNumber` en `app.json`.

## Pendiente

- `src/chaski/banco-demo.json` es un fixture con el formato del §4: cambiarlo por `app/chaski/banco.json` cuando exista, o servirlo en `GET /banco`.

- Los textos en quechua de `src/chaski/textos.ts` son **borrador**: los revisa la mamá de Freddy.
- «¿Me lo repite?» (F6) espera su ruta en el servicio.

