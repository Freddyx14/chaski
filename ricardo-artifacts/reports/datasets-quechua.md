# Datasets de quechua que podemos usar, y cuáles nos arruinarían el número

> Sábado 24 de octubre de 2026. Todo verificado contra la fuente, con enlace.
> La pregunta de fondo era doble: **qué datos ayudan al ajuste fino** y **cuáles ya vieron los
> modelos**, porque entrenar con algo que el modelo ya conoce no mejora nada y sí infla el resultado.

## Lo primero: lo que Omnilingual ya vio

El paper de Omnilingual ASR dice de dónde salieron sus datos anotados: unas 15 000 h de recursos
abiertos conocidos —**LibriSpeech, Common Voice, VoxPopuli, FLEURS, MLS**—, más la expansión de
Common Voice que Meta financió vía el Open Multilingual Speech Fund, más un corpus propio encargado
para rellenar huecos, el **Omnilingual ASR Corpus (3 350 h en 348 lenguas)**.

Dos consecuencias para nosotros:

1. **Common Voice está dentro.** Cualquier cosa que venga de ahí no sirve como dato nuevo.
2. **Siminchik, Huqariq y los datos de IWSLT no aparecen en esa lista.** No es una garantía escrita,
   pero son corpus peruanos con licencia restrictiva que no están entre los recursos citados, así que
   son los candidatos con más probabilidad de aportar señal nueva.

Y el dato que ordena todo lo demás: **Common Voice tiene 0.05 horas validadas de quechua de Ayacucho,
de 8 personas.** Tres minutos. Para `quy` —nuestra variedad— el mundo abierto está prácticamente
vacío, y por eso las grabaciones de las familias valen tanto.

## Habla, para ajustar omniASR

| Qué | Cuánto | Variedad | Licencia | ¿Ya lo vio el modelo? |
|---|---|---|---|---|
| [IWSLT 2026 Quechua](https://github.com/johneortega/IWSLT2026_Quechua_data) (Siminchik ampliado) | **48 h transcritas** + 1 h 40 con traducción | **quy** (Ayacucho) y quz | CC BY-NC-ND 3.0 | probablemente no |
| Huqariq, vía el mismo repo | ~8 h con traducción automática post-editada | varias del Perú | idem | probablemente no |
| [Quechua Collao emotion corpus](https://www.nature.com/articles/s41597-022-01855-9) | 15 h 15, 12 420 segmentos | quz | Figshare, abierta | no |
| [Siminchik original](http://lrec-conf.org/workshops/lrec2018/W14/pdf/4_W14.pdf) | 97 h de radio | quy + quz | **sin licencia abierta** | — |
| Common Voice Ayacucho | **0.05 h** | quy | CC0 | sí |
| Common Voice Puno | 35.41 h (5.18 validadas) | qxp | CC0 | casi seguro que sí |

> **Descartado el 24-oct.** Ricardo lo ve inviable para el plazo que tenemos, y tiene razón: hay que
> pedirlo, esperar respuesta, y el ND obliga a una conversación de permisos que no cabe en el fin de
> semana. Queda apuntado para después del hackathon, no para ahora. Lo de abajo explica por qué era
> atractivo, por si se retoma.

**El mejor candidato sería: las 48 h transcritas de IWSLT 2026.** Es habla espontánea de radio, en
nuestra variedad, con transcripción, y es ~130 veces lo que tendríamos con las grabaciones familiares.

**Pero la licencia tiene un ND.** CC BY-NC-**ND** es «sin obras derivadas», y un modelo ajustado con
ese audio es discutiblemente una obra derivada. Para el hackathon y para investigación es lo que hace
todo el mundo y nadie va a objetar. Si Chaski llega a la posta de Pilpichaca de verdad, hay que
pedirle permiso a Siminchikkunarayku y a Llamacha antes, no después. Lo apunto ahora para que no nos
agarre esa pregunta en la demo.

## Texto paralelo, para ajustar la traducción

| Qué | Cuánto | Variedad | Nota |
|---|---|---|---|
| [somosnlp-hackathon-2022/spanish-to-quechua](https://huggingface.co/datasets/somosnlp-hackathon-2022/spanish-to-quechua) | **102 747** pares de entrenamiento | **quy** | la mejor relación tamaño/variedad |
| [AmericasNLP 2023](https://aclanthology.org/2023.americasnlp-1.16/) | 154 008 pares | quechua general | documentos de gobierno y material educativo |
| [Llamacha/monolingual-quechua-iic](https://huggingface.co/datasets/Llamacha/monolingual-quechua-iic) | 373 MB monolingüe | sureño | para un KenLM del paso 1, no para traducir |
| [makitty/quechua-chanka-unified](https://huggingface.co/datasets/makitty/quechua-chanka-unified) | Rosettia + SomosNLP | quy | **ver la advertencia de abajo** |

### 🔴 Esto nos rompería la medición

Nuestras 100 frases de evaluación salen todas de `rosettia-chanka-data`:

```
fuentes de nuestras 100 verificadas: Counter({'rosettia-chanka-data': 100})
```

Y `quechua-chanka-unified` **incluye Rosettia**. Si entrenamos con ese dataset, nuestro conjunto de
prueba entero entra al entrenamiento y el chrF++ 42.31 → «lo que sea» deja de significar nada: el
modelo habría visto las respuestas.

Regla, entonces: **antes de entrenar con cualquier dataset, se le quitan las 100 frases nuestras por
coincidencia exacta del castellano.** Es una línea de código y evita el error que invalida el pitch.

## Salud: aquí está el hueco, y aquí está lo que lo tapa

**No existe un corpus de quechua para salud.** Lo busqué y no hay. Lo que sí existe son materiales
institucionales peruanos, hechos justamente para que el personal de salud hable con pacientes
quechuahablantes:

| Qué | Quién | Contenido |
|---|---|---|
| [Manual de Semiología en Quechua](https://www.cmp.org.pe/wp-content/uploads/2020/07/ManualSemiologiaQuechua-2020.pdf) | Colegio Médico del Perú, 2020 | **80 páginas** de pares castellano/quechua: filiación, interrogatorio, y preguntas por aparato (respiratorio, cardiovascular, digestivo…) |
| [Palabras clave para la atención en salud: Quechua](https://www.gob.pe/institucion/minsa/informes-publicaciones/280806-palabras-clave-para-la-atencion-en-salud-quechua) | MINSA | salud materna, perinatal, sexual y reproductiva |
| [Quechua médico](https://www.gob.pe/institucion/minsa/informes-publicaciones/321798-quechua-medico) | MINSA | vocabulario clínico |
| [Guía de lenguaje quechua para personal de salud](https://www.sil.org/resources/archives/27939) | SIL / Dirección Subregional de Salud, 1997 | frases útiles |

El Manual del CMP viene en el formato que queremos, alternando las dos lenguas línea por línea:

```
¿Desde cuándo está enfermo?        ¿Hayk'akmanta onq'oska kashanky?
¿Qué es lo que le duele?           ¿Imaykin nanan?
¿Cómo es el dolor?                 ¿Imaynatatak nanasunky?
Señale con el dedo                 Dedoykiwan willaway
```

Se parsea a pares con un script simple. Y el autor, el Dr. Julio Lopera Quiroga, **autorizó que su
texto se publicara y se colgara en la web del CMP**, así que no estamos tomando nada a escondidas.

### El problema, y es arreglable

Ese manual está en **quechua Collao (Cusco), no en Chanka**. Se ve a simple vista en las consonantes:
`qhari`, `hayk'a`, `k'allarin`, `onq'oska`. El Chanka no tiene ni glotalizadas (`k'`, `q'`, `p'`) ni
aspiradas (`kh`, `qh`, `ph`). En Chanka serían `qari`, `hayka`, `qallarin`, `unqusqa`.

O sea: la conversión es **mayormente sistemática** —quitar glotalizadas y aspiradas, normalizar la
ortografía vieja (`y` por `i`, `o` por `u`)— más un puñado de cambios de palabra que no se pueden
automatizar. Eso lo revisa la mamá de Freddy, y es una revisión mucho más barata que traducir 80
páginas desde cero.

## El paso 1 ya está hecho

`voz/importar_semiologia.py` baja el manual, lo parsea y escribe
`datos/frases/semiologia_cmp.jsonl`: **243 pares** castellano/Collao, con la conversión a Chanka
propuesta al lado y `revisado: false` en todos.

```
¿Le duele el abdomen?           ¿Wiksachu nanan?
¿Tiene fiebre o escalofríos?    ¿Rupaychu japisunki o chirichu?
¿Desde cuándo está enfermo?     ¿Haykakmanta onqoska kashanky?   (era: ¿Hayk'akmanta onq'oska…?)
```

40 de los 243 necesitaron quitar
glotalizadas o aspiradas. El resto ya se escribía igual en las dos variedades.

Dos cosas aprendidas parseando, que valen para el próximo PDF:

- **Emparejar por columnas no sirve.** Probé juntar todas las líneas castellanas contra todas las
  quechuas de cada página: las cuentas cuadraban y el orden igual se corría, porque el PDF pierde
  renglones y parte frases. Quedó el emparejado literal —una línea castellana seguida de una
  quechua—, descartando sin consumir la siguiente, así un renglón suelto no corre todo el resto.
- **`ñ` no distingue las lenguas.** La tenía como marca de quechua y bastaba «señor / señora /
  señorita» para clasificar una línea castellana como quechua y desalinear la página entera.

Quedan fragmentos de frases partidas por el salto de línea del PDF. Se ven a simple vista y el
revisor los borra; preferí dejarlos a inventar una heurística que borre frases buenas.

## Lo que sigue

1. ~~Bajar el Manual del CMP y parsearlo a pares.~~ **Hecho.**
2. **Convertir Collao → Chanka** con reglas, y pasarle a la hablante solo lo dudoso.
3. **Entrenar la traducción** con `spanish-to-quechua` (102 747 pares, quy) **menos nuestras 100**.
4. ~~Pedir las 48 h de IWSLT 2026.~~ **Descartado para el hackathon** (plazo y permisos). El ajuste de
   omniASR va con las voces de las familias y nada más. Son menos horas, pero son de nuestra variedad
   y de nuestro dominio, que es lo que ninguna de las 48 h tiene.
5. **No tocar Common Voice.** Para `quy` son tres minutos, y ya están dentro del modelo.

Lo que nadie tiene y nosotros sí vamos a tener: **habla clínica real en Chanka, de las familias.**
Ese es el aporte, y los datasets de arriba son el piso sobre el que se apoya, no el reemplazo.


## Candidatos de glosario, ya generados

`voz/glosario_candidatos.py` convierte los 243 pares en
`datos/frases/glosario_candidatos.json`: **152 candidatos**, de dos clases distintas, porque se
revisan distinto.

**111 de tipo `frase`** — el par completo, cuando la frase
castellana es corta y se sostiene sola. Vienen emparejados del manual, así que son los confiables:

```
¿Cómo te llamas?        ¿Iman sutiyki?
¿Tienes esposo?         ¿Qariyki kanchu?
¿De dónde vienes?       ¿Maymanta jamunki?
```

**41 de tipo `termino`** — una palabra castellana con la
quechua que más la acompaña, contada sobre los 243 pares. Esto es coocurrencia, no alineamiento, y se
nota:

```
respire    samay             apoyo 5   ✓
hijo       wawaykita         apoyo 5   ~ está flexionado: «a tu hijo», no «hijo»
dolor      imatawantaq       apoyo 2   ✗ eso significa «¿con qué más?»
```

Dos límites que conviene decir antes de que alguien los descubra revisando:

- **El quechua aglutina, así que la palabra suelta casi nunca aparece.** Lo que coocurre es
  `wawaykita`, no `wawa`. Un glosario de raíces necesita a alguien que sepa quitar los sufijos.
- **Con 243 pares la estadística es pobre.** Un `apoyo 2` es haber visto dos frases. Por eso cada
  candidato sale con su apoyo y con ejemplos: para que se pueda descartar rápido, no para creerle.

Nada de esto toca `app/chaski/glosario.json`. Ese archivo dice en su propia documentación que solo
una hablante agrega entradas, y así se queda: esto es una lista para marcar sí o no.
