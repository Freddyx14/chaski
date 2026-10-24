# Rimay (nombre de trabajo) — el problema, la solución y sus funciones

> Qué es el producto, no cómo se construye. La arquitectura va en otro documento.
> Las cifras vienen de `research/problemas-lenguas-originarias.md` y los papers de `research/papers.md`.
> «Rimay» significa «hablar» en quechua. Es un nombre de trabajo: lo decidimos con la mamá de Freddy.

---

## 1. El problema

### Una enfermera, un idioma, toda una posta

En la posta de Pilpichaca, en Huancavelica, la mamá de Freddy es **la única enfermera que habla quechua**.
Cuando ella no está de turno, una paciente quechuahablante sale de su control prenatal con indicaciones que
no entendió del todo: qué tomar, cada cuánto, cuándo volver y, lo más grave, **qué señales significan que
tiene que regresar de inmediato**.

No es un caso aislado. Es cómo funciona el sistema:

- Solo **126 de 8,441 establecimientos de salud del país (1%)** tienen atención intercultural.
- En **toda Huancavelica hay 52 servidores públicos bilingües certificados**, cerca de **1 por cada 4,000 quechuahablantes**.
- El **65.2%** de los huancavelicanos tiene el quechua como lengua materna (INEI 2017).
- El **90%** de los quechuahablantes dice que nunca lo atendieron con un intérprete.
- La línea de intérpretes del Estado (1812, desde mayo de 2026) existe, pero **la llama el funcionario, no la paciente**, y no hay cifras de uso.
- Eulogia Guzmán, primer caso peruano de violencia obstétrica ante la CIDH: *«que en los hospitales y centros de salud nos hablen en quechua»*.

### Por qué no basta con «usar Google Translate»

- **Los traductores automáticos fallan más justo en las lenguas con menos datos.** En el estudio más reciente
  sobre indicaciones médicas, ChatGPT acertó el 97% de las oraciones en castellano, pero solo el 89% en ruso, y
  **el 56% de los juegos de indicaciones en ruso tenía al menos un error** (Kong et al., 2026). El quechua tiene
  muchísimos menos datos que el ruso.
- **Google Translate usa quechua chanka sin decirlo y falla más traduciendo del castellano al quechua**, que es
  justo la dirección que necesita una posta.
- **Nadie ha medido qué tan bien manejan el chanka los modelos de lenguaje**, y menos en salud. En las búsquedas de
  Scopus y OpenAlex no aparece ningún estudio así (`research/papers.md`).
- La evidencia dice que la traducción automática **solo alcanza para mensajes simples o ya traducidos de antemano**
  (van Lent et al., 2025, revisión de 26 estudios).

**El problema en una línea:** la información que salva a una gestante existe, pero sale de la posta en un idioma
que ella no habla, y la única persona que la puede traducir no puede estar en todos los turnos.

---

## 2. La comunidad

**Las gestantes quechuahablantes que se atienden en la posta de Pilpichaca (Huancavelica)**, y el personal de
salud que las atiende sin hablar su idioma.

Dos usuarias:
| | Quién | Qué necesita |
|---|---|---|
| **La que envía** | La enfermera u obstetra (hable o no quechua) | Que su indicación llegue entendida, y saber cuándo no llegó |
| **La que recibe** | La gestante quechuahablante, que puede no leer | Escuchar en su idioma qué hacer, en su celular, cuantas veces quiera |

---

## 3. La solución

**Rimay lleva las indicaciones de la posta a la casa de la gestante, en quechua chanka y en audio, y comprueba
que las entendió.**

Lo que hace en una consulta, de punta a punta:

1. La enfermera dicta o escribe la indicación en castellano, y le toma una foto a la receta y a la caja de la medicina.
2. Rimay lee la receta, arma la indicación completa y la traduce al chanka.
3. **Antes de enviarla, Rimay se audita a sí mismo**: retraduce su quechua al castellano y, si no dice lo mismo, no la envía.
4. La gestante recibe por WhatsApp un **audio en chanka** con su texto, más las **señales de alarma** de siempre.
5. Rimay le pide que **lo repita con su voz**, en quechua.
6. Si lo que dijo no coincide con la indicación, **avisa a la enfermera**: «María no entendió cuándo volver».

Cada paso tiene respaldo en lo que el personal de salud ya hace a mano. Mehandru et al. (2022) entrevistaron a 20
clínicos, entre ellos enfermeras y obstetras. Contra la barrera del idioma usan tres estrategias: **retraducir para
comprobar, probar si la paciente entendió y usar frases traducidas de antemano**. Y recomiendan sistemas que combinen
las tres. **Rimay es esas tres estrategias, automatizadas.**

---

## 4. Las funciones

### F1 · Indicaciones en chanka, en audio
La enfermera escribe o dicta en castellano y la gestante recibe la indicación en **audio en quechua chanka** más texto,
por WhatsApp.
- **Por qué audio:** en zona rural, el 33.6% de los mayores de 60 no sabe leer, y mucha gente que habla quechua no lo lee.
- **Respaldo:** ya existe síntesis de voz para el chanka de Andahuaylas, Ayacucho y Huancavelica (Huamán Curo et al., 2026, cuatro sintetizadores entrenados con 2,300 grabaciones). *Por confirmar que los modelos se puedan descargar.*

### F2 · Foto de la receta y de la caja (visión por computadora)
La enfermera, o la misma paciente en casa, toma una foto de la **receta escrita a mano** y de la **caja del medicamento**.
Rimay identifica el medicamento, la dosis y la frecuencia, y lo agrega a la indicación en chanka.
- **Por qué:** la receta escrita a mano en castellano es justo lo que la paciente no puede leer, y es donde un error de dosis hace daño.
- **Protección:** si la lectura no es segura, Rimay **no adivina**: le pide a la enfermera que confirme ese dato.
- **Respaldo:** leer recetas a mano es un problema estudiado (hay 193 papers en Scopus). Lo nuevo aquí no es leer la receta, es **lo que pasa después**, cuando la indicación llega en el idioma de la paciente.
- **Extra posible:** foto del **carné de control prenatal** para leer la fecha de la próxima cita y recordársela en quechua.

### F3 · Señales de alarma, fijas y revisadas por una hablante
Las señales de alarma del embarazo **no las traduce la IA cada vez**. Son un contenido fijo, tomado de la fuente oficial
del MINSA, traducido y grabado una vez y **revisado por la mamá de Freddy**. Cada indicación las incluye.
- **Respaldo:** la traducción automática solo alcanza para mensajes simples o traducidos de antemano (van Lent et al., 2025). Lo que más importa no puede quedar a merced del modelo.
- *Por confirmar:* la lista oficial del MINSA, con su fuente.

### F4 · Rimay se audita antes de enviar (retraducción)
Antes de enviar algo, Rimay vuelve a traducir su propio quechua al castellano y lo compara con la indicación original.
Si cambió el sentido, una dosis o una fecha, **no la envía** y le pide revisión a la enfermera.
- **Respaldo:** es la estrategia que usan los clínicos a mano (Mehandru et al., 2022), y es el método con que se evalúa la traducción médica (Kong et al., 2026).

### F5 · «¿Me lo repites?» (comprobación de lo que entendió)
Después del audio, Rimay le pide a la gestante que **repita con su voz, en quechua**, qué tiene que hacer. Compara su
respuesta con la indicación. Si falta algo importante, se lo vuelve a explicar y **avisa a la enfermera**.
- **Por qué:** es la técnica de *teach-back*, la que el personal de salud usa para saber si una paciente entendió (Mehandru et al., 2022).
- **Riesgo conocido:** el reconocimiento de voz en quechua todavía es débil y depende mucho de los datos (Romero et al., 2024; Zevallos et al., 2022). Si no se entiende su respuesta, Rimay **no da por entendido nada**: lo marca para la enfermera.

### F6 · El panel de la enfermera
Una sola pantalla: a quién se le envió qué, quién confirmó que entendió y **quién necesita una llamada**.
Desde ahí también se corrige el quechua de Rimay.

### F7 · Mejora con cada corrección
Cada vez que la enfermera corrige una traducción, o una paciente no entiende algo, eso entra al **glosario chanka** y a
la evaluación. Rimay se equivoca una vez, no dos.

### F8 · La primera evaluación pública de IA en quechua chanka para salud (el núcleo técnico)
Antes de confiar en Rimay, lo medimos. Con el mismo método de Kong et al. (2026): un set de **indicaciones prenatales
reales**, traducidas al chanka por Claude y por Google Translate, retraducidas, y **calificadas por una hablante nativa
que trabaja en una posta** según exactitud y riesgo de daño.
- **Por qué importa:** responde la pregunta de Anthropic, «¿dónde falla Claude para esta gente?», **con números y no con una opinión**.
- **Lo nuevo:** en las búsquedas no aparece ningún estudio que haga esto en chanka ni en quechua para salud. Kong et al. piden expresamente investigar «otras lenguas».
- **Lo que queda:** un set de prueba que cualquiera puede usar para medir otros modelos en chanka.

---

## 5. Lo que Rimay NO hace (alcance)

- **No diagnostica.** Solo transmite lo que ya indicó el personal de salud.
- **No reemplaza a la enfermera ni al intérprete.** Les avisa cuándo hacen falta.
- **No conversa libremente sobre salud.** Los mensajes simples o traducidos de antemano son los únicos donde la evidencia dice que la traducción automática alcanza (van Lent et al., 2025).
- **No funciona sin señal.** Si la paciente no tiene datos, el mensaje espera; es una limitación que decimos en voz alta.

---

## 6. Dónde puede fallar, y qué hacemos (criterio 4 de Anthropic)

| Falla | Qué le pasa a la gestante | Protección |
|---|---|---|
| Traduce mal una dosis o una fecha | Toma de más, de menos o no vuelve | Retraducción antes de enviar (F4); si cambia algo, no se envía |
| Traduce mal una señal de alarma | No reconoce una emergencia | Las señales de alarma son fijas y revisadas por una hablante (F3) |
| Lee mal la receta | Dosis equivocada | Si la lectura no es segura, la confirma la enfermera (F2) |
| Quechua «de libro» o de otra variedad | No le suena a su idioma | Revisión de la mamá de Freddy; glosario que se corrige con el uso (F7) |
| No entiende la respuesta de voz | Se da por entendido algo que no se entendió | Si no hay certeza, se marca para la enfermera; nunca «entendió» por defecto (F5) |
| La paciente confía demasiado en el audio | Deja de preguntar | Cada audio termina con «si tiene dudas, vuelva a la posta» y avisa a la enfermera |

---

## 7. Cómo medimos el impacto

1. **% de gestantes que repiten bien las señales de alarma** (con y sin Rimay).
2. **Errores por indicación** en la evaluación chanka (F8): exactitud y riesgo de daño, Claude contra Google Translate.
3. **Casos marcados para la enfermera**: cuántas veces Rimay detectó que alguien no entendió.
4. **Tiempo de la enfermera**: cuántas consultas se pudieron dar en quechua sin que ella tuviera que estar presente.

---

## 8. El momento de la demo

1. El jurado ve a la enfermera escribir una indicación y tomar una foto de una receta.
2. Un celular recibe el audio **en quechua chanka**, en vivo.
3. Una voz responde en quechua, a medias. Rimay detecta lo que faltó y aparece el aviso: «no entendió cuándo volver».
4. En pantalla: **«así falla cada modelo en chanka, y así lo corregimos»**, con los números de la evaluación.
5. Si tenemos su permiso, una nota de voz de la mamá de Freddy contando lo que pasa cuando ella no está de turno.

---

## 9. Apertura del pitch (idea de Freddy y su amigo, 23-oct 22:20)

1. Freddy dice una frase en quechua chanka directo al jurado, sin traducir. **La frase es una señal de alarma real del
   embarazo**, dicha como la diría la enfermera (texto exacto y grabación: los da la mamá de Freddy, no la inventamos).
2. «¿Entendieron?». Silencio.
3. «Les acabo de decir [traducción]. Si ustedes fueran una gestante en Pilpichaca, acaban de perderse la indicación
   que les podía salvar la vida. Eso le pasa a [cifra] personas, y en toda Huancavelica hay 52 servidores públicos
   que hablan su idioma».
4. Mejor aún: la frase sale de la **voz grabada de la mamá de Freddy**. Abre con la persona real.

## 10. Alcance: ¿solo gestantes? ¿otras lenguas?

**Visión (para el pitch):** Rimay es para **postas y hospitales**, y para **todas las lenguas originarias**.

**Lo que construimos este fin de semana:** gestantes, Pilpichaca, chanka. Tres razones:
1. **Anthropic premia lo específico** («the narrower, the better») y «una cosa bien hecha y usable el lunes».
2. **La seguridad de Rimay depende de una hablante que revise** (F3, F4, F8). Para chanka la tenemos; para aimara o
   asháninka no, y lanzar una lengua sin revisión es justo la falla que decimos evitar.
3. Las señales de alarma del embarazo son un contenido **fijo y oficial**: el mejor primer caso para probar el método.

**Cómo lo mostramos sin construirlo:** el idioma es un parámetro del sistema, no está fijo en el código. En el pitch:
«el mismo método sirve para aimara o asháninka; lo único que falta es una revisora nativa como la que ya tenemos para chanka».

## 11. Dónde está lo técnicamente difícil

No es «traducir con Claude». Es **lograr que una IA sepa cuándo se equivoca en un idioma que casi no conoce**. Cuatro piezas:

| # | Pieza | Por qué es difícil | Quién |
|---|---|---|---|
| T1 | **Evaluación chanka-salud** (F8) | No existe. Hay que crear el set con indicaciones reales, calificar con una hablante nativa con el protocolo de Kong et al. (2026), y medir a Claude contra Google Translate | Ricardo (métricas) + mamá de Freddy (calificación) |
| T2 | **Detector de errores de traducción sin referencia** (F4) | En el uso real no hay traducción correcta para comparar. Hay que detectar cuándo cambió una dosis, una fecha o una señal de alarma usando retraducción y comparación de los datos críticos. **Se mide**: de los errores que la hablante encontró en T1, ¿cuántos atrapó el detector? | Freddy (Claude) + Ricardo (medición) |
| T3 | **Voz en quechua** (F1, F5) | Síntesis de voz chanka (modelos de Huamán Curo et al., 2026) y, lo más difícil, **entender la respuesta hablada** de la paciente con reconocimiento de voz para una lengua con muy pocos datos (Romero et al., 2024) | Ricardo |
| T4 | **Leer la receta y saber cuándo no está seguro** (F2) | Leer la receta ya está resuelto; lo difícil es que el sistema **se abstenga** cuando su lectura no es confiable, con un umbral medido | Ricardo (visión) |

**La frase técnica del pitch:** *«Construimos la primera evaluación de IA en quechua chanka para salud, y un detector
que atrapa X de cada 10 errores de traducción antes de que lleguen a una paciente.»* (X sale de T2.)

## Pendientes antes de construir

- [ ] Que la mamá de Freddy acepte revisar las traducciones y, si quiere, aparecer en el pitch con sus palabras.
- [ ] La lista oficial de señales de alarma del MINSA, con su fuente.
- [ ] Confirmar que los modelos de voz chanka de Huamán Curo et al. (2026) se pueden descargar.
- [ ] Cuántas gestantes atiende la posta de Pilpichaca (para la métrica de impacto); preguntarle a ella.
- [ ] El nombre: Rimay es de trabajo.

## Referencias

En `research/papers.md`: Kong et al. (2026), Mehandru et al. (2022), van Lent et al. (2025), Huamán Curo et al. (2026),
Romero et al. (2024), Zevallos et al. (2022), Ebrahimi et al. (2024), Oncevay (2021).
