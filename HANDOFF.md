# HANDOFF — Chaski (Cal Hacks 13.0) · sábado 24 de octubre de 2026, 08:55 PT

> Punto de retome. **La verdad del producto está en [`SOT.md`](SOT.md)** (versión SOT-9 + D25).
> Tareas por persona: [`plan/tareas.md`](plan/tareas.md). Entrega: **domingo 25, 9:00 AM PT** en Devpost.

## ⏭️ PENDIENTES (empezar por acá)

1. **Datos de voz: todavía no llegó ni una grabación real.** Es lo que bloquea el ajuste fino (el núcleo técnico).
   - Un subagente está construyendo un **formulario web** (Next.js en Vercel + Neon para texto + Vercel Blob para audio) en `form/`:
     cada persona ve la frase en castellano, la escribe en quechua y graba leyéndola. Incluye export JSONL para Ricardo y `/admin`.
     **Al retomar: revisar si terminó** (URL de producción, `form/README.md`) y probarlo en el celular.
   - Mandar el link a **4–8 hablantes de chanka** (mínimo 4: 3 entrenan + 1 de prueba; mezclar mujeres, hombres y mayores).
     Plazo: datos antes de **~13:00 PT** para que Ricardo alcance a ajustar.
   - Plan B si el formulario falla: el cuadernillo PDF `ricardo-artifacts/datos/frases/frases_ambos.pdf` (escribir + leer, foto de las hojas).
2. **La app iOS no existe todavía** (D14). Expo + TestFlight, colores de `design/tokens.json` (D24), loops de Chaski en `avatar/loops/`.
   Conectar a los endpoints de Ricardo `/turno/enfermera` y `/turno/paciente` (`ricardo-artifacts/servicio/`), que hoy corren por IP
   plana: **hace falta HTTPS** (túnel) para iOS.
3. **Entrevista a la mamá de Freddy** (enfermera en Pilpichaca): guía en `plan/entrevista-personal-salud.md`. Videollamada prevista
   ~17:00 PT. Decide para qué situación se diseña (bloque 4) y si sirve F12 (notas + resumen). Confirmar si puede el domingo 12:30–14:30 hora de Lima (pitch).
4. **Medir modelos de Claude** (Opus 5 / Sonnet 5 / Haiku 4.5) en velocidad y acierto para la conversación (D15). Dato de Ricardo:
   Claude traduciendo tarda 7–35 s y la auditoría bloquea mucho → evaluar **NLLB-200** (D25) para traducir y Claude para auditar.
5. **Funciones de Claude por construir:** F3 (entender estilo Wispr Flow), F6 («¿me lo repite?»), F9 en la app (visión: banco de Ricardo ya lee cajas con Haiku en 2.3 s), F10 (Claude corrige la transcripción quechua con las N mejores), F11/F12 (resumen y notas).
6. **Chaski «hablando»:** no hay video (Flow falló). Hacerlo en la app alternando `avatar/estados/reposo.png` y `hablando.png` según el volumen del audio.
7. **OCR de hojas manuscritas** (solo si se usa el PDF): Claude visión lee las fotos y llena la transcripción de cada audio. Avisar a Ricardo.
8. **Cierre:** borrador Devpost 21:00 · repo público **sin `context/photos/`** (QR de créditos) · README con lo que hacen Claude y Cartesia · ensayo 22:00 · video de demo domingo 05:00 · números congelados 07:00.

## ✅ Qué se hizo (viernes 18:30 → sábado 09:00)

- **Idea y producto:** de incendios → quechua en salud → **Chaski, intérprete castellano↔chanka para el personal de la posta** (D1–D25 en el SOT). Investigación con fuentes en `research/` (problemas, papers vía Scopus/OpenAlex, voz quechua, competencia).
- **Código:** auditoría de traducción con retraducción a ciegas (F4), 20 pruebas, `app/chaski/`.
- **Chaski** (vicuña con audífonos de intérprete, D22): especificación `avatar/chaski.json`, 6 cuadros en `avatar/estados/`, loops en `avatar/loops/` (escuchando y presentarse cierran solos; pensando y no_entendi en ping-pong).
- **UI:** dos prototipos con el mismo brief (`design/specs/01-chaski-ui.txt`): Pencil `design/chaski-pen.png` y Claude Design https://claude.ai/artifact/We661RMs5wg16da2sk9tm1. Paleta decidida D24 → `design/tokens.json`.
- **Página visual** sincronizada con el SOT: https://claude.ai/artifact/4E7Si4gN9mpF34eha55jpH (`plan/chaski-visual.html`, privada de Freddy).
- **Cuadernillo de grabación** reescrito (75 frases, escribir + leer, D25) y **entrevista** al personal de salud (Mom Test).
- **Ricardo (noche):** servicio con el ciclo completo de intérprete, medición en GPU (detección 49 ms, ASR 1.7 s por 16 s, A10G 23 GB), WER base 38 % (falla en préstamos del castellano), Cartesia para castellano, banco de visión. Ver `ricardo-artifacts/reports/arquitectura.md`.

## 🔑 Decisiones clave (no relitigar; detalle en SOT §6)

- Usuaria principal = **personal de salud**; app de intérprete cara a cara, **iOS nativa por TestFlight** (D9, D10, D14).
- **Salud general**, no solo gestantes (D8). Comunidad nombrada: pacientes quechuahablantes de la posta de Pilpichaca.
- **Claude es el núcleo** (D19): ve, corrige, entiende, audita, juzga, resume, orquesta. Voz: oídos y boca.
- **Foco del fin de semana:** traducción literal + ajuste fino de reconocimiento y voz (D23). Modos «mediado» y «preguntas al intérprete» al backlog.
- **Medición honesta:** el conjunto de prueba es una persona que el modelo nunca escuchó.
- **Cartesia** para el castellano (D16); el quechua es nuestro porque Cartesia no lo soporta.
- **Datos escritos + audio** (D25): con solo voz habría que transcribir ~450 audios.

## ▶️ Cómo retomar

1. `git pull` en `clients/calhacks-2026` (Ricardo empuja seguido a `main`).
2. Leer el bloque «Qué cambió» al inicio de `SOT.md` y este HANDOFF.
3. Ver si el subagente del formulario terminó (`form/README.md`) → mandar el link a la familia → empezar la app iOS.

## Gastos registrados
fal.ai ~US$3.30 (imágenes de Chaski + pruebas) · Google Flow 600 de 1,050 créditos (6 videos).
