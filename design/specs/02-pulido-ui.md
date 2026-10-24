# Chaski · pulido de UI/UX (D26)

> Sábado 24 de octubre, 09:05 PT. Base elegida por Freddy: **el tablero de Pencil** (`design/chaski-pen.png`).
> Lo que sigue es lo que el tablero no tenía y el flujo real necesita, decidido mirando el backend de Ricardo
> (`ricardo-artifacts/servicio/flujo.py`) y los tiempos medidos. La app (`movil/`) implementa esto.

## La idea que ordena todo

La enfermera mira el celular uno o dos segundos por vez, con un paciente enfrente. Cada pantalla responde a
una sola pregunta: **¿qué está pasando y qué toco ahora?** El paciente no lee: para él están la voz y Chaski.

## Lo que se agrega al tablero

| # | Cambio | Por qué |
|---|---|---|
| 1 | **Estado «Pensando»** con el loop `pensando.mp4` y tres pasos que se van marcando: *Traduciendo · Revisando dosis y horas · Preparando la voz* | El turno de la enfermera tarda ~5 s (modo rápido) y el del paciente ~5.6 s. Sin un estado de espera, la enfermera cree que se colgó y vuelve a hablar. Los pasos le dicen que la auditoría está trabajando, que es justo lo que da confianza |
| 2 | **Texto primero, voz después.** El quechua aparece en pantalla apenas vuelve la auditoría y la voz se pide aparte (`/voz`) | La enfermera ya puede leer mientras se genera el audio. La espera se siente la mitad |
| 3 | **Modo ensayo en ámbar**: si la auditoría solo dudó de términos (posta, carné, en ayunas) se dice igual con una franja ámbar con ícono «Dicho con aviso: revise *posta*» | Hoy la auditoría aprueba 1 de 9 frases por esos términos. Si cada uno bloquea, Chaski se calla siempre. Rojo queda **solo** para un dato crítico cambiado (regla de `tokens.json`) |
| 4 | **Un solo botón de micrófono, tocar para empezar y tocar para terminar** (no «mantener presionado») | El celular está entre dos personas. El paciente no sabe que tiene que sostener un botón, y la enfermera no quiere sostenerlo mientras explica |
| 5 | **Quién habla se ve en el botón**: debajo dice «Habla la enfermera · castellano» o «Habla el paciente · quechua». Después de cada turno cambia solo al otro lado; tocar la etiqueta lo cambia a mano | Detección automática (D11) cuando el servicio la expone por turno; mientras tanto la alternancia acierta casi siempre en una consulta y nunca obliga a elegir idioma |
| 6 | **Franja textil** escalonada (`textileA` + `textileB`) de 6 pt bajo el encabezado, en todas las pantallas | La regla de D24 ya la pedía y el tablero no la tenía. Es la única identidad visual fuera de Chaski |
| 7 | **Encabezado sin paciente ficticio**: «Chaski» + tiempo de consulta + botón de conversación | En la posta no se registra al paciente en la app (no grabamos datos de pacientes, §8 del SOT). El nombre «Don Teodoro» solo existe en la demo |
| 8 | **Historial de la consulta** detrás del botón de documento: cada turno con su idioma, lo que se dijo y si la auditoría lo aprobó | La enfermera necesita volver atrás («¿qué le dije de la hora?») sin repetir el turno |
| 9 | **Chaski «hablando»** alterna `reposo.png` y `hablando.png` según el **volumen real** del audio (envolvente calculada del WAV cada 50 ms) | El loop de video falló en Flow; con la envolvente la boca se mueve cuando hay voz y se cierra en los silencios |
| 10 | **Error sin drama**: si el servicio no responde, Chaski en `no_entendi`, «No pude conectarme. Vuelva a intentarlo» y un botón «Reintentar». Nunca un error técnico en pantalla | La enfermera no tiene que saber qué es un túnel |
| 11 | **Toques grandes y vibración**: botón de micrófono de 96 pt, vibración suave al empezar y al terminar de grabar | Se usa sin mirar |

## Lo que queda igual que Pencil

Pantallas 1 a 6, Chaski en su tarjeta con degradado, etiquetas de idioma, la fila «Auditado antes de hablar»,
la pantalla de bloqueo con la comparación «Usted dijo / La traducción decía», y «¿Me lo repite?» con la lista de lo entendido.
Colores **siempre** desde `design/tokens.json` (el quechua usa `#A85A2A` de D24, no el `#C9763A` del brief viejo).

## Orden de construcción

1. Pantalla de consulta con los estados 1 → 2 → Pensando → 3 / 5 (turno de la enfermera completo).
2. Turno del paciente (4).
3. Historial.
4. Receta con cámara (F9, `/ver`).
5. «¿Me lo repite?» (6) cuando exista el endpoint.
