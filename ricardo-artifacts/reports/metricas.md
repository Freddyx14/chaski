# Cómo comparamos las métricas, bloque por bloque de `frases.json`

`datos/frases/frases.json` no es una lista suelta de frases: cada bloque existe
para medir una cosa distinta, y cada finetuning se valida contra el bloque que le
corresponde. Esta es la correspondencia.

| Bloque | Filas | Qué contiene | Qué mide | ¿Sirve hoy? |
|---|---|---|---|---|
| `verificadas` | 100 | castellano + chanka, ya emparejados | traducción | **sí** |
| `clinicas_sin_traducir` | 25 | indicaciones de la posta, solo castellano | ASR + guarda | cuando se graben |
| `medicamentos_y_prestamos` | 31 | nombres de medicamentos | pronunciación de préstamos | cuando se graben |
| `numeros_y_tiempos` | 7 | dosis, horas, fechas | el error que más daño hace | cuando se graben |
| `respuestas_libres` | 12 | habla espontánea del paciente | ASR fuera de guion | cuando se graben |

La diferencia entre las dos últimas columnas es la que importa: **las 100 filas de
`verificadas` ya traen la respuesta correcta escrita**, así que puntúan sin que
nadie grabe ni revise nada. Los otros 75 son guiones de lectura: no valen como
referencia hasta que la familia los grabe y queden corregidos en `/corregir`.

## 1. Traducción — `voz/medir_traduccion.py`

Las 100 verificadas son el único par (castellano, chanka) confiable que existe
hoy. Se reservan como evaluación y **no entran al entrenamiento**; si entran, el
número deja de significar algo.

Métrica: **chrF++**, no BLEU. BLEU cuenta palabras enteras y el quechua es
aglutinante — `pastillata` y `pastillakunata` son un acierto parcial real que
BLEU puntúa como cero. chrF mide n-gramas de caracteres y sí lo recoge. BLEU se
reporta al lado solo como referencia.

Línea base medida hoy (Sonnet sin ajustar, 30 frases):

```
chrF++   42.31
BLEU     17.11
mediana  35.24
```

Las peores salidas dicen exactamente qué va a arreglar el finetuning:

```
«Señor, ¿cómo está?»
  modelo:     Señor, ¿imaynallam kachkanki?
  referencia: Taytáy, ¿allillanchu?

«Adelante, señores»
  modelo:     Haku, señoresniykuna
  referencia: Yaykuykamuychik, taytakuna
```

El modelo no se equivoca de gramática. Se equivoca de **registro**: deja
`señor` en castellano donde la referencia dice `taytáy` o `wiraqucha`, y usa la
forma corta donde la referencia usa la cortés. Eso es precisamente lo que un
finetuning con habla de la familia corrige, y es la razón por la que el número
va a subir por algo real y no por azar.

Comparación antes/después: la misma orden con otra etiqueta.

```
python voz/medir_traduccion.py --etiqueta base      --frases 100
python voz/medir_traduccion.py --etiqueta ajustado  --frases 100
```

Ambas corridas se acumulan en `reports/traduccion.json` y la segunda imprime el
delta. Mismo set, mismo corte, misma métrica: es una comparación honesta.

## 2. ASR — `voz/medir_asr.py`

Aquí la referencia es el texto escrito que acompaña cada audio, el que sale
corregido del etiquetador. Métrica: **WER** y **CER**, con dos cortes extra que
el WER global esconde:

- **acierto en préstamos** (bloque `medicamentos_y_prestamos`): si el modelo
  escribe `paracetamol` cuando se dijo con pronunciación quechua, el WER global
  apenas se mueve, pero la indicación queda mal. Se mide aparte.
- **acierto en números** (bloque `numeros_y_tiempos`): confundir `pusaq` con
  `suqta` es cambiar ocho horas por seis. Un solo token, el peor de todos.

Corte por hablante: entrenar y evaluar con la misma voz infla el resultado. La
partición es por persona, no por frase.

## 3. La guarda — `voz/medir_guarda.py`

Este es el hueco que teníamos: las dos auditorías solo se comparaban **entre
sí**, y si se equivocan igual el acuerdo no prueba nada.

Las 100 verificadas lo resuelven sin esperar a la hablante. Cada par se usa dos
veces:

- **limpio** — el chanka verificado tal cual. La auditoría debe aprobarlo. Si lo
  bloquea es un **falso bloqueo**: la enfermera no puede decir algo que estaba bien.
- **corrompido** — el mismo chanka con un error clínico inyectado a propósito.
  La auditoría debe bloquearlo. Si lo aprueba es una **fuga**, y la fuga manda
  al paciente una indicación equivocada.

Las corrupciones son los tres errores que de verdad hacen daño:

| Tipo | Qué se rompe | Por qué importa |
|---|---|---|
| `numero` | se cambia un numeral chanka (`pusaq` → `suqta`) | ocho horas se vuelven seis |
| `negacion` | se borra `mana` | «no tome con leche» se vuelve «tome con leche» |
| `condicion` | se borra la cláusula tras la coma | «si hay sangrado, venga» queda en «venga» |

Se le entrega el chanka ya hecho, así que mide **la guarda, no al traductor**.
Las dos reglas de decisión se comparan sobre los mismos casos: `decidir` (la de
Freddy, bloquea ante cualquier `termino_inseguro`) y `decidir_separando` (la
mía, que degrada esos términos a aviso).

Las dos cifras son asimétricas y hay que decirlo: **una fuga es peor que un
falso bloqueo**. El falso bloqueo cuesta que la enfermera repita la frase; la
fuga cuesta una dosis mal dicha. Si hay que elegir, se elige la regla con menos
fugas aunque bloquee de más.

## 4. Estabilidad — `voz/medir_auditoria.py`

Antes de preguntarse si una auditoría acierta hay que preguntarse si contesta lo
mismo dos veces. Medimos la misma frase varias corridas:

- **bloqueo** — fracción de frases que se niega a decir. Si bloquea casi todo, la
  enfermera deja de hacerle caso y da igual lo correcta que sea.
- **estabilidad** — fracción de frases con veredicto idéntico en todas las corridas.
- **mediana de tiempo** por frase.

Ya apareció el problema que buscábamos: la auditoría de cuatro llamadas a Opus
da `sí, no, sí` sobre la misma frase. Una guarda que cambia de opinión no es una
guarda.

## Lo que todavía no se puede medir

Si el chanka **suena natural** a una hablante no lo decide ninguna métrica de
este archivo. chrF compara contra una referencia escrita; no sabe si la frase
suena a traducción. Eso llega con la revisión de la mamá de Freddy sobre el
bloque E, y entonces se agrega la quinta métrica: acuerdo entre el veredicto de
la guarda y el de la hablante.
