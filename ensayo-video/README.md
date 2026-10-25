# Ensayo del demo · video guía (dom 25-oct, 01:30 PT)

Cómo se ve el pitch de 3:00, beat por beat. Pedido de Freddy: *«a /motion-apple video on how the demo should
look… use my voice… include the videos of my mom… and if there is a specific thing it is supposed to go, tell it»*.

- **La voz es lo que se dice.** Freddy con su clon de ElevenLabs (`freddy-en`). La parte de Ricardo (B5) va con
  otra voz (`brian`) para que se note que habla él. La frase al celular va en castellano con la voz de Freddy.
- **Las tarjetas son lo que se hace**: qué tocar, dónde mirar, qué nunca decir, qué archivo usar.
- **El reloj de arriba es el tiempo real del pitch**, y se pone rojo pasados los 3:00.
- Guion: `plan/pitch.md` v4 §6, con el traductor D40 (turno de ~8 s, `evals/HISTORIA.md` §2d).

## Qué es real y qué es maqueta

| | |
|---|---|
| Video de la mamá (B1) | Real: `data/mama/video/clips/PITCH-B1_problema-profesionales-costa_16s.mp4`, sus subtítulos en inglés |
| Respuesta del paciente (B3) | Audio real de la familia, `data/formulario/p18/064.webm` («Umaymi nanachkan qayna punchawmanta» = «Me duele la cabeza desde ayer») |
| Voz quechua de Chaski | Meta MMS-TTS `quy` tal cual, generada local. **El quechua de B3 lo armó Claude a partir de las salidas del traductor y nadie lo revisó**: en el pitch sale el que diga la app |
| Pantallas del celular | **Maqueta** con los tokens y los textos reales de la app (`movil/src/chaski/textos.ts`, `ensayo.ts`). Cada pantalla lo dice abajo |
| Frase de emergencia | «¿Mayta nanan?», escrita por la enfermera (`evals/banco/revision_enfermera.json`) |
| La negativa (B4) | `FRASE_NEGATIVA_DEMO` de `movil/src/chaski/ensayo.ts`, motivo «cambió un dato crítico: prohibiciones» |
| Números de B5 | `plan/pitch.md` §0 y §4 |

**Este ensayo dura 3:06.** Hay que recortar ~6 s; la tarjeta final dice dónde.

## Cómo se rehace

```bash
python3 build.py                     # horario, subtítulos y cues.json desde la alineación de la voz
uv run --with numpy --with scipy --with soundfile --with pyloudnorm --with pillow \
  ~/.claude/skills/motion-studio/scripts/score.py cues.json -o assets/audio/mix.wav --emit-js cues.js
python3 gen_html.py                  # index.html (comp.css + comp.js en línea)
uv run ~/.claude/skills/motion-apple/scripts/apple_audit.py . && npx hyperframes check .
PRODUCER_BROWSER_GPU_MODE=hardware npx hyperframes render . --fps 30 --quality delivery -o renders/chaski-ensayo-demo-vN.mp4
```

Voces: `assets/audio/vo/lines.tsv` (una línea por beat) → `eleven-voice tts --timestamps`. Máximo 5 pedidos a la
vez (el plan Creator corta el sexto con 429).

**Nada de `assets/audio/` ni `assets/video/` va a git**: tiene la voz de la familia y el video de la enfermera.

## Versiones

| v | Qué cambió y por qué |
|---|---|
| v1 | Primera versión. 30 fps (guía interna de 3:24; 360° de obturador = la misma exposición que la referencia). Corte cada ~18 s, uno por beat, con el campo alternando claro/oscuro. En el storyboard: el resumen inventaba «paracetamol» (la indicación no nombra ningún medicamento), se quitó; la página B3 pasó a mostrar el celular con el sello del crítico al lado de la cadena de pasos |
