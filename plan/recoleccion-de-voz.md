# Recolección de voz en quechua chanka para salud — protocolo (viernes 23, 22:50 PT)

Base técnica: `research/voz-quechua-modelos.md`. Este documento es lo que se le manda a la familia esta noche.

**Quiénes graban:** la mamá de Freddy (enfermera en la posta de Pilpichaca), el papá de Freddy, el papá de
Ricardo y otros familiares que hablan chanka. **Tener varias voces es lo que vuelve creíble la medición.**

---

## 1. La regla que hace honesta la medición

**El set de prueba es de una persona que el modelo nunca escuchó.**

Si entrenamos y medimos con la misma voz, el modelo «mejora» porque aprendió esa voz, no porque entienda
mejor el chanka. Un jurado técnico lo pregunta. Entonces:

| Conjunto | Quién | Para qué |
|---|---|---|
| **Entrenamiento** | Todos menos uno | Ajustar los modelos |
| **Prueba (held-out)** | **Una persona completa que no está en el entrenamiento**, idealmente distinta en edad o sexo | Medir antes y después. **Nunca se usa para entrenar** |
| **Voz de Chaski** | Solo la mamá de Freddy (con su permiso) | La voz con la que Chaski le habla a las pacientes |

Si alcanza el tiempo, se repite rotando quién queda fuera (validación por hablante) y se reporta el promedio.

## 2. Consentimiento (antes de grabar nada)

Un mensaje por WhatsApp de cada persona, guardado como captura, que diga que acepta que su voz se grabe, se use para
entrenar un modelo y se muestre en Cal Hacks, y si acepta o no que se publique después. Sin esto, no se usa su audio.

## 3. Qué graban

### Bloque A · Frases de la posta (entrenamiento y voz de Chaski)
Les mandamos **frases en castellano**; cada persona las dice **en chanka, como lo diría en la posta**.
**Nosotros no escribimos el quechua**: lo dicen ellos. Después la mamá de Freddy escribe la transcripción de cada audio.

Temas (la lista final la ajusta la mamá de Freddy, que sabe qué se dice de verdad en la posta):
1. **Saludo y presentación**: «Buenos días, soy la enfermera de la posta», «¿Cómo se siente hoy?».
2. **Medicinas**: «Tome una pastilla cada día después del almuerzo», «No deje de tomarla aunque se sienta bien», «Tómela con agua, no con té ni café».
3. **Citas**: «Su próximo control es en un mes», «Venga en ayunas», «Traiga su carné».
4. **Señales de «vuelva ya» por tipo de atención** (salud general, decidido el 23-oct): niño con fiebre o diarrea, presión alta, diabetes, embarazo, adulto mayor. Cada lista sale de la fuente oficial del MINSA o de lo que dice la mamá de Freddy en la posta. Son las más importantes: que las graben todas las personas.
5. **Preguntas de la enfermera**: «¿Tiene dolor?», «¿Desde cuándo?», «¿Tiene fiebre?», «¿Está comiendo bien?», «¿El bebé se mueve?».
6. **Números, días y horas**: uno a diez, días de la semana, «en la mañana», «cada ocho horas». Ahí es donde un error es más peligroso.

Meta por persona: **150 a 300 frases** (~20–40 min). Con 4–5 personas: 1,000+ audios.

### Bloque B · Respuestas espontáneas (la prueba de «¿me lo repites?»)
Escuchan una indicación y **la repiten con sus propias palabras**, como lo haría una paciente. Sin guion.
Es lo más parecido al uso real y lo más difícil para el modelo. **La persona de prueba graba sobre todo este bloque.**

Meta: 60 a 100 respuestas de la persona de prueba.

## 4. Cómo graban

- **Nota de voz de WhatsApp**, una frase por audio, al chat de Freddy o Ricardo. Así graban desde su celular, sin instalar nada.
- Lugar silencioso, celular a un palmo de la boca.
- Antes de cada frase, decir el número: «Frase doce» (en castellano), para no perder el orden.
- Nosotros convertimos todo a 16 kHz mono y lo nombramos: `{persona}_{bloque}_{numero}.wav`.

## 5. Qué medimos (lo que va en la página)

**Reconocimiento de voz (lo que dice la paciente)**
| Paso | Qué es |
|---|---|
| 0 · Línea base | Omnilingual ASR de Meta en chanka (`quy`), sin tocar |
| 1 · + vocabulario de salud | Un modelo de lenguaje con las frases de la posta (KenLM) y palabras clave (dosis, días, señales) |
| 2 · + ajuste fino | El modelo entrenado con las voces de la familia |

Métricas sobre la persona de prueba:
- **CER y WER** (errores por carácter y por palabra), antes y después.
- **% de conceptos clave recuperados**: de lo que importa (la dosis, el día, la señal de alarma), ¿cuánto entendió? Es la métrica que de verdad importa para una paciente.

**Voz de Chaski (lo que dice Chaski)**
- **Ida y vuelta**: Chaski habla una frase, el reconocimiento la transcribe, se compara. Menos errores = voz más clara.
- **Prueba a ciegas**: la mamá de Freddy califica de 1 a 5 audios sintéticos mezclados con grabaciones reales, sin saber cuál es cuál.

**La frase para el pitch:** *«Pasamos de X% a Y% de errores al entender quechua chanka hablado en una posta, medido con una
voz que el modelo nunca escuchó.»*

## 6. Calendario

| Cuándo | Qué |
|---|---|
| **Viernes, esta noche** | Mandar este protocolo y las frases a la familia. Consentimientos. La mamá de Freddy escucha 5 audios de la voz chanka de Meta y dice si se entiende |
| **Sábado temprano (Perú va 2 h adelante de California)** | Graban los bloques A y B. Freddy y Ricardo van recibiendo y transcribiendo |
| **Sábado mañana** | Línea base con lo que haya llegado |
| **Sábado tarde** | Paso 1 y paso 2. Ajuste de la voz de Chaski |
| **Domingo 07:00 PT** | Se congelan los números. Lo que no esté, no entra a la página |

## 7. Licencias (para saberlo, no para frenar)

Para el hackathon todo sirve. Para producción después: Omnilingual y Siminchik son libres; las voces MMS de Meta son
no comerciales. Lo grabado por la familia es nuestro, con su consentimiento.
