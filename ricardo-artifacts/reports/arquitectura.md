# Arquitectura de Chaski — modelos y datos

> Sábado 24 de octubre de 2026. Todos los tiempos de este documento están medidos, no estimados:
> `reports/tiempos-instancia.md`, `reports/lid.json`. Los diagramas se regeneran editando los `.svg`.

## 1. Un turno de consulta

![Flujo de un turno](arquitectura-flujo.svg)

Cuatro proveedores, y cada uno hace lo que hace mejor:

| Trabajo | Quién | Dónde corre | ¿Se ajusta? |
|---|---|---|---|
| Detectar el idioma del turno | `facebook/mms-lid-512` | Nuestra GPU | **No.** Ya acierta 6/6 |
| Entender quechua chanka | `omniASR_LLM_300M` | Nuestra GPU | **Sí. Es el núcleo técnico** |
| Entender castellano | Cartesia `ink-whisper` | Nube de Cartesia | No |
| Decidir, corregir, traducir, auditar | Claude | Nube de Anthropic | No |
| Hablar castellano | Cartesia Sonic 3.6 | Nube de Cartesia | No |
| Hablar quechua chanka | `facebook/mms-tts-quy` | Nuestra GPU | **Sí**, con la voz de la mamá de Freddy |

**Por qué Cartesia no puede hacer el lado quechua.** Verificado en su documentación el 24-oct: Sonic 3.6
habla 44 idiomas y **el quechua no está entre ellos**; su STT acepta un parámetro `language` en ISO-639-1
con `en` por defecto y **no tiene detección automática de idioma**. Así que el quechua y la detección son
nuestros por necesidad, no por preferencia.

**Por qué Cartesia sí se gana el castellano.** Es streaming, suena mucho mejor que MMS en castellano, y
usar sus dos mitades (entender y hablar) en vez de solo la voz hace que su track sea defendible.

## 2. La espera por turno

| Paso | Medido |
|---|---|
| Detectar idioma (`mms-lid-512`) | **49 ms** de mediana, 160 ms el peor caso |
| Entender quechua (`omniASR_LLM_300M`) | **1.71 s** para 15.8 s de audio · factor 0.11 |
| Cargar el modelo al arrancar | 20.17 s el ASR, 27.81 s el detector · una sola vez |
| Pico de GPU | 3.41 GB de 23 disponibles |
| Claude y la voz de salida | por medir |

**Esos 49 ms deciden la arquitectura.** Con una detección tan barata, se puede detectar primero y
reconocer después, en serie. No hace falta correr los dos reconocedores en paralelo ni adivinar el idioma
por el turno anterior. Un paso menos, una cosa menos que puede fallar en el demo.

## 3. El caso que no tiene respuesta correcta

«Mamáy, tome una pastilla cada ocho horas» es castellano con quechua adentro, y es exactamente como se
habla en una posta. `mms-lid` lo llama castellano en los tres audios de prueba.

No está mal: el castellano es la lengua matriz de esa frase. Pero **no se cuenta ni como acierto ni como
error**, porque no hay una respuesta única. Se reporta aparte. Si en la consulta real resulta frecuente,
la salida es la alternancia de turnos: en una consulta hablan por turnos, así que el turno que sigue al
de la enfermera es del paciente.

## 4. De la voz de la familia al número del pitch

![Arquitectura de datos](arquitectura-datos.svg)

La regla que sostiene toda la medición: **el conjunto de prueba es una persona completa que el modelo
nunca escuchó.** Si se parte por frase, el modelo aprende la voz y el número deja de significar nada.
Está en el código, no solo en el protocolo: `partir_por_hablante` lanza un error si hay menos de dos
personas, y los tests lo fijan.

Tres pasos, tres números, y se reportan los tres salga lo que salga:

1. El modelo tal cual.
2. Más el vocabulario de la posta.
3. Más el ajuste fino con las voces de las familias.

## 5. Qué ajustamos, y por qué ahí

La prueba de humo mostró dónde falla el modelo base: en los **préstamos del castellano**.
`doctor` → `luctor`, `jefelláy` → `que fillay`. Son palabras que no existen en quechua pero que un
hablante de chanka pronuncia a su manera, y son justo las que no se pueden equivocar en una posta:
los nombres de los medicamentos y las dosis.

Por eso el cuadernillo tiene un bloque de 35 préstamos, con la instrucción de decirlos **como se dicen en
la posta, no como los leería un locutor**.

Y son **dos ajustes distintos**, que conviene no mezclar:

| | Entender (`omniASR`) | Hablar (`mms-tts-quy`) |
|---|---|---|
| Qué mejora | Que el modelo entienda el acento y los préstamos | Que Chaski suene familiar, no robótico |
| Qué datos quiere | **Muchas voces distintas** | **Una sola voz consistente** |
| De quién | Los cuatro: tu papá y los papás de Freddy | Solo la mamá de Freddy |
| Qué número da | CER y WER antes y después | Juicio a ciegas de ella |

Esa tensión es la razón de que el protocolo pida que todos graben el bloque de frases, pero que la voz de
Chaski salga de una sola persona.

## 6. Lo que falta medir

- Cuánto tarda Claude por turno, con los tres modelos candidatos (es la decisión D15 del SOT).
- Cuánto tarda Cartesia en hablar, y si el streaming se nota.
- La línea base real sobre voz humana, no sintética.
- `mms-lid` sobre voz humana con ruido de posta, que es otra cosa que sobre audio limpio.
