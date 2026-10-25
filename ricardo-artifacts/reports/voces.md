# Las cuatro voces, y lo que mide cada una

Audios en `reports/voces/<voz>/`. Por voz: `A_base` (Meta sin entrenar), `B_ajustada` (esa persona),
`C_real` (la grabación de la persona). Cuatro frases: dosis, control, alarma, saludo.

| voz | quién | datos | desde |
|---|---|---|---|
| `p24` | familiar de Freddy | 165 clips · 13.7 min | mms-tts-quy |
| `p16` | papá de Ricardo | 175 clips · 11.4 min | mms-tts-quy |
| `mama_freddy` | mamá de Freddy | 13 clips · 1.6 min | **checkpoint de p24** |
| `papa_ricardo` | papá de Ricardo | 15 clips · 0.6 min | **checkpoint de p24** |

`p16` y `papa_ricardo` son la misma persona por dos caminos: formulario con texto verificado contra
nota de WhatsApp con texto del reconocedor. Comparar esos dos dice cuánto vale tener buen texto.

## Ida y vuelta: texto → voz → reconocimiento → texto

| voz | WER |
|---|---|
| **base** | **45.8 %** |
| p16 | 74.6 % |
| p24 | 89.8 % |
| papa_ricardo | 93.2 % |
| mama_freddy | 98.3 % |

**La voz de fábrica gana.** El ajuste acerca el timbre y aleja la claridad, que es justo el fallo que
esta prueba busca: una voz que suena a la persona y hace que se oiga mal una dosis.

Dos límites del número: mide inteligibilidad **para nuestro reconocedor**, entrenado con voz humana,
y el texto del banco no está en la ortografía normalizada con la que se entrenó. Una persona podría
ordenarlas distinto. La prueba a ciegas con una hablante sigue siendo la que decide.

## Qué afirmar y qué no

- **Sí:** A suena a robot, B suena a persona. Se oye en los mp3.
- **No todavía:** que B se entienda mejor. La medición dice lo contrario.
- Para emergencias, donde una palabra mal oída cuesta más: grabación real donde exista, `base` donde no.
