# Lo que pasó mientras dormías (dom 25-oct, 02:30–04:00 PT)

> Para leer en 3 minutos. Todo lo de abajo está construido, probado y **desplegado en el servicio vivo** salvo donde
> dice lo contrario. Los números salen de `evals/HISTORIA.md`.

## Lo que pediste, y cómo quedó
| Pediste | Estado |
|---|---|
| Que funcione como el modo voz de ChatGPT: lo prendes y solo | ✅ **Build 19** en TestFlight (ui-ux): un toque y escucha; detecta cuándo terminaste de hablar, quién habló y en qué idioma; cierra el micrófono mientras Chaski habla y vuelve a escuchar solo |
| Que pregunte cuando no está seguro, no que se calle | ✅ Si una barrera frena algo, le pregunta al que habló, en su idioma, nombrando el dato: «No quiero decir un dato equivocado: la dosis. ¿Me lo repite?». Una sola vez |
| Que hable en el idioma correcto a la persona correcta | ✅ 18 de 18 en consultas completas simuladas |
| La receta | ✅ Foto → «Leí: Paracetamol 500 mg, una tableta cada 8 horas. ¿Se lo digo?» → «sí» → en quechua con todas las barreras. Foto borrosa → pregunta, no adivina |
| Auditar el trabajo | ✅ Revisor con ojos frescos: 1 crítico + 3 altos + 8 medios. Arreglados el crítico, los 3 altos y 6 medios (`evals/auditoria/revision-2026-10-25.md`) |
| Evals con los datos que ya tenemos | ✅ Audio real de la familia (p16, la voz que el reconocedor nunca oyó) + voz peruana de ElevenLabs para el personal |

## Los números de hoy (medidos en el servicio vivo)
- **Consulta completa en modo voz** (22 turnos, nadie le dice quién habla): quién habló 21/22 · a quién y en qué idioma 18/18 · 0 números perdidos · **7,8 s por turno** · consulta de 6–9 turnos en 49–70 s.
- **Tiempo de un turno:** quién habló 0,5–1 s · lo que va a decir en pantalla 3–5 s · **voz lista ~8,5 s** (antes ~25 s).
- **Quechua real de p16:** 24 de 30 dichos, 6 pidió repetir, **0 bloqueados**, números intactos (antes 9 dichos, 12 repetir).
- **Banco de 952 errores sembrados:** 183/184 atrapados, **100 % de los críticos**, 7/40 frases buenas frenadas (antes 8/40).
- **Costo:** ~2 centavos por turno.

## Lo que encontré y arreglé de paso (lo importante)
1. **La decisión a veces «pensaba» hasta quedarse sin espacio y no respondía** → 27 s y «no entendí» en frases claras. Era la causa de los 25 s que veía ui-ux.
2. **Pedía repetir frases de cortesía** («yanapasaykiku» = le vamos a ayudar) creyendo que eran errores. Ahora se traducen.
3. **«killa» = mes, no luna:** «vuelva en un mes» se bloqueaba siempre.
4. **El hallazgo crítico de la auditoría:** si el detector de idioma dudaba justo después de que Chaski pidiera repetir, el quechua del paciente podía ir al reconocedor de castellano y traducirse como orden del personal. Ahora un lado adivinado no puede llevar números, medicamentos ni partes del cuerpo.

## Lo que queda (nada bloquea la demo)
- La auditoría dejó 7 puntos menores (rendimiento y orden), anotados en el archivo de la auditoría.
- El reconocedor de quechua sigue siendo el límite: con una voz que no conoce, pide repetir 1 de cada 5 frases. Es lo seguro.
- Para la demo: que nadie más use el servicio mientras presentas (una sola GPU; con carga, el turno se alarga).
