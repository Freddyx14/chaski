# HANDOFF · Ricardo · la voz de Chaski ajustada con la voz de la enfermera (sáb 24-oct, 18:45 PT)

> **PRIORIDAD 1 de Ricardo** (Freddy, 18:43: *«Let's go with this plan … when he finishes, he has to document everything
> and push it so I can pull it, grab it, and give it to my mother»*). Plan acordado en `plan/pitch.md` §11.
> La enfermera (mamá de Freddy) dio permiso para usar su voz.

## Por qué
La voz de Meta (`mms-tts-quy`) suena robótica. Ajustada con la voz de la enfermera, suena como ella. Es el momento
técnico más fuerte del pitch **si lo podemos medir y mostrar**: la misma frase con la voz de Meta, con la voz de Chaski
y con la enfermera real (A/B/C). Y el modo emergencia va a hablar con esa voz.

## Qué hacer, en orden

| # | Tarea | Entregable (todo en `entregables/voz/` + push) |
|---|---|---|
| 1 | **Las 24 frases de emergencia con la voz ajustada.** El texto está en `app/chaski/banco.json` (items con tag `emergencia`, campo `quy`; las 24 ya están revisadas por la enfermera, `revisado: true`). | `entregables/voz/emergencia/<id>.mp3` (24 archivos, nombre = `id` del banco, p. ej. `emg-dolor-donde.mp3`) |
| 2 | **Las mismas 24 con la voz de Meta tal cual**, para comparar. | `entregables/voz/emergencia-base/<id>.mp3` |
| 3 | **Ida y vuelta (se entiende mejor o no):** las 24 de la voz base y las 24 de la ajustada pasan por el reconocimiento (MMS ajustado, `7b57a9b`) y se mide el error contra el texto `quy`. | `entregables/voz/ida-y-vuelta.json`: WER y CER de base vs ajustada, por frase y el promedio |
| 4 | **A/B/C para la lámina y el video:** una frase de emergencia que la enfermera haya grabado de verdad (búscala en sus grabaciones del formulario), dicha por **A** Meta tal cual, **B** voz ajustada, **C** ella. Normalizados a −16 LUFS, misma duración aproximada. | `entregables/voz/abc/A-meta.mp3`, `B-chaski.mp3`, `C-enfermera.mp3` + `abc.md` con la frase en quechua y en castellano |
| 5 | **Prueba a ciegas para la enfermera:** 6 pares (base vs ajustada) de frases distintas, en orden al azar, sin decir cuál es cuál. | `entregables/voz/ciegas/par-1-x.mp3`, `par-1-y.mp3`, … + `clave.json` (cuál es cuál, **Freddy no se la muestra a ella**) |
| 6 | **Documentar y hacer push al terminar** (ver abajo). Freddy hace pull y le manda a su mamá la carpeta `ciegas/` para que elija. | push |

## Al terminar (no lo saltes)
1. `entregables/voz/README.md`: qué modelo, con qué datos (cuántos minutos y frases de la enfermera), cuántos pasos,
   la tabla de ida y vuelta, y cómo regenerar todo.
2. Una línea en `SOT.md` (registro) y marca ✅ en `plan/tareas.md` y en `plan/checklist-acordado.md`.
3. **Poner las URL de los mp3 de `emergencia/` en el campo `audio` del banco** (subirlos a algún lado público, o
   decirle a Freddy y él los sube) para que el modo emergencia de la app suene con esa voz.
4. `git pull --rebase` y `git push`, y avisar por el grupo: **«voz lista, hagan pull»**.

## Reglas
- La voz ajustada solo dice frases **verificadas** (las 24 del banco). Nunca texto que no pasó las barreras.
- En todo lugar se dice que es una voz **entrenada con su permiso**; nunca se presenta B como si fuera ella.
- No entrenes con toda la GPU mientras Freddy prueba la app: usa `--ceder` (tu commit `7b57a9b`).
- Si algo de esto no da, escribe en `entregables/voz/README.md` qué no salió y por qué. Un «no se pudo» documentado
  sirve más que nada.

## Después de la voz (sigue siendo tuyo)
- NLLB-200 ajustado: chrF++ antes y después sobre las 100 `verificadas`, **por dominio** (`plan/tareas.md`).
- Conectar el intérprete a tu servicio: `app/chaski/PARA_RICARDO.md` (~3 líneas por ruta). Avisa por el grupo antes de reiniciar.
