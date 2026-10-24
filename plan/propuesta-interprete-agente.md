# Propuesta para acordar con Ricardo · Chaski como intérprete agente (sáb 24-oct, 13:00 PT)

> **Estado: PROPUESTA, no decisión.** Sale de la entrevista con la enfermera de Pilpichaca
> (`research/entrevistas/2026-10-24-enfermera-pilpichaca-insights.md`) y de lo que Freddy propuso después.
> Cuando Freddy y Ricardo acuerden qué entra, se registra como decisión en el `SOT.md`.
> Quedan ~8 h útiles hasta el ensayo (22:00) y la entrega es el domingo 9:00.

## Lo que aprendimos en 5 líneas

1. **90 % de los pacientes habla quechua y solo ~20 % del personal lo habla**, y sin fluidez. Hoy traducen el chofer, un técnico, un familiar, o se arreglan con señas y dibujos. Nadie conocía la línea 1812.
2. **Una consulta en quechua toma hasta una hora o más; en castellano, 30–40 min.** Las indicaciones se repiten hasta 4 veces.
3. **Lo más difícil son las emergencias (piden rapidez), la consejería y los medicamentos (piden cuidado).**
4. **El usuario es el personal que NO habla quechua** (llega de la costa). Ella no lo usaría porque habla quechua: es la experta que valida.
5. **Escribir quechua es difícil incluso para quien lo habla.** La voz va primero.

## La idea de Freddy: de traductor a intérprete agente

Un traductor pasa frases de un lado al otro. Un intérprete **entiende, pregunta cuando no entendió y transmite
indicaciones**. Chaski debería:

| Comportamiento | Qué hace | Ejemplo |
|---|---|---|
| **Pulir los dos lados** (estilo Wispr Flow) | Limpia lo que dijo cada uno antes de traducir: muletillas, frases a medias, repeticiones | La enfermera dice «eh, que tome, tome la pastilla, la blanca, cada ocho, ocho horas» → «Tome la pastilla blanca cada ocho horas» |
| **Repreguntar cuando algo no está claro** | Si falta un dato crítico o la respuesta es ambigua, Chaski le pregunta directamente a quien habló, en su idioma, antes de traducir | Paciente: «me duele». Chaski, en quechua: «¿dónde le duele y desde cuándo?» |
| **Transmitir indicaciones** | La enfermera da una orden y Chaski la dice como indicación clara al paciente, no como traducción literal | «Dile que se eche y que respire hondo» → al paciente: «Échese, por favor, y respire hondo» |
| **Razonar sin inventar** | Todo lo anterior pasa por la auditoría: lo que Chaski agrega es una pregunta o una forma de decir, nunca un dato clínico nuevo | Nunca agrega una dosis o un diagnóstico que nadie dijo |

## Funciones candidatas y lo que cuesta cada una

| # | Función | Por qué (de la entrevista) | Quién | Costo | Recomendación |
|---|---|---|---|---|---|
| 1 | **Pulir los dos lados** (F3, en ambos sentidos) | Consejería: «escogiendo las palabras correctas» | sesión ui-ux (prompt en `app/chaski`) | Bajo: un cambio de prompt + pruebas | ✅ **Hacer** |
| 2 | **Repregunta de una vuelta**: si a Claude le falta un dato crítico (dónde, desde cuándo, cuánto), hace UNA pregunta al hablante antes de traducir; se ve en pantalla como «Chaski pregunta» | Emergencias: «tienes que preguntarle dónde duele, qué te duele, en qué parte» | sesión ui-ux (app + `app/chaski`) | Medio: un campo nuevo en la respuesta de Claude + una pantalla | ✅ **Hacer, solo una vuelta**. Es el momento «agente» del pitch |
| 3 | **Modo emergencia**: botones con preguntas ya traducidas y ya grabadas («¿dónde le duele?», «¿desde cuándo?», «¿es alérgico?», «¿está embarazada?», «señale con el dedo»), con la voz de Chaski pre-generada. Cero espera de modelos | «en la emergencia es al instante» · pide rapidez | Ricardo genera los audios con la voz quechua; ui-ux arma la pantalla | Bajo-medio. **El texto quechua lo revisa la enfermera** | ✅ **Hacer**: rápido, seguro y se ve muy bien en la demo |
| 4 | **Receta** (F9): foto de la receta o la caja → cuánto, cada cuánto, cuántos días, en quechua, con «¿me lo repite?» | Medicamentos: «cuánto lo va a tomar, por cucharadas, por tabletas» · repetir hasta 4 veces | ya existe `movil/src/app/receta.tsx` + `/ver` de Ricardo | Lo que falte para terminarlo | ✅ **Terminar** lo que ya está |
| 5 | **Glosario en el resumen**: las palabras quechua nuevas de la consulta, para que el personal aprenda | «me estaría enseñando cómo hablarlo» | sesión ui-ux (`app/chaski/resumen.py`) | Bajo | ✅ Hacer si sobra 1 h |
| 6 | **Intérprete con varias vueltas**, que conduce la conversación y decide solo | Visión de Freddy | todos | Alto, y difícil de auditar | ⏭️ **Backlog**. Se cuenta en el pitch como el siguiente paso |
| 7 | **Voz en streaming** (traducir mientras habla) | Emergencias | Ricardo | Alto, cambia el servicio | ⏭️ **Backlog**. El modo emergencia (#3) cubre la rapidez hoy |
| 8 | **Ajuste fino para salud** (reconocimiento, traducción, voz) | Base técnica del producto | Ricardo | En curso | ✅ Sigue siendo lo principal de Ricardo, con la línea base primero |

**Regla para todo lo nuevo:** Chaski puede preguntar y reformular, nunca agregar un dato clínico. Lo que dice pasa por la
auditoría igual que hoy. Eso es lo que lo hace «agente» sin volverlo peligroso, y es lo que pide el criterio 4 de Anthropic.

## Qué le toca a Ricardo, concretamente

1. **Primero la línea base** (lo crítico de esta mañana, sigue igual).
2. **Audios del modo emergencia**: ~10–15 frases cortas en quechua con la voz de Chaski, generadas con `mms-tts-quy`. El texto lo prepara la sesión ui-ux y lo revisa la enfermera.
3. **`/ver` para la receta**, si la app necesita algo más de esa ruta.
4. Decir si la repregunta (#2) necesita algo del servicio (probablemente no: es Claude en `app/chaski`).

## Para el pitch

- El número nuevo, de primera mano: **«90 % de los pacientes habla quechua; ~20 % del personal lo habla.»**
- Corrección: **no es la única enfermera que habla quechua** (son 3 de 6). La frase correcta es otra (ver `plan/pitch.md`).
- El «antes» medible: una consulta en quechua dura hasta una hora o más, en castellano 30–40 min.
- El momento agente para la demo: Chaski repregunta «¿dónde le duele?» antes de traducir.
