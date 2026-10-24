# Línea base contra ajuste fino — reconocimiento de chanka

> 24-oct-2026. Todo sobre los **mismos 175 clips de p16**, el papá de Ricardo, apartado entero y que
> ningún modelo vio entrenando. El hablante de prueba está fijado en `personas.json` para que el
> «antes» y el «después» sigan siendo comparables aunque etiquetemos más gente.

## Los tres números

| | WER | CER | WER ortogr. | CER ortogr. | clips exactos |
|---|---|---|---|---|---|
| `omniASR_LLM_300M` sin ajustar | 68.9 % | 15.6 % | 54.1 % | 11.6 % | 13/175 |
| `mms-1b-all` (quy) sin ajustar | 76.0 % | 17.1 % | 53.9 % | 11.4 % | 30/175 |
| **`mms-1b-all` + nuestro adaptador** | 82.5 % | 20.2 % | **40.9 %** | **9.5 %** | **51/175** |

**La comparación válida es la de las dos últimas filas**: el mismo modelo contra sí mismo. omniASR
está para situar —es el mejor de fábrica que probamos— pero compararlo con un MMS ajustado diría más
sobre qué modelo es mejor de origen que sobre si nuestro ajuste sirvió.

**Lo que ganamos: 53.9 % → 40.9 % de WER**, 12.9 puntos, una reducción relativa del 24 %. Y los clips
reconocidos perfectos pasan de 30 a 51: **de uno de cada seis a casi uno de cada tres.**

## El número que empeoró, y por qué

El WER estricto subió de 76.0 % a 82.5 %. No es un detalle que convenga callar.

Pasa porque **entrenamos con los textos normalizados**. El modelo aprendió a escribir en la ortografía
normalizada, así que contra las referencias crudas —que cada persona escribió a su manera— se ve peor
de lo que es. Después de entrenar así, la comparación honesta es la normalizada, y por eso están las
dos columnas.

## Lo que hay que arreglar en la próxima vuelta

Mirando lo que produce, el problema se ve claro:

```
ref  pusaq horapi juk pastillata upyay        ajustado  pusaq urapi huk pastilata upiai
ref  Mikuy qhipa pastillakunata japay         ajustado  mikui kipa pastiliukunata hapai
ref  Upyay yacuta manan tehuancho             ajustado  upiai yakuta manam tiwanchu
```

Reconoce bien —`tehuancho` → `tiwanchu` es la misma palabra— pero **escribe en una ortografía que
nadie usa**. `upiai` por `upyay`, `kipa` por `qhipa`. Mi normalizador es agresivo: convierte `y`→`i`,
`e`→`i`, `o`→`u`. Sirve para comparar, no para mostrarle texto a una enfermera.

La corrección es acotada: entrenar contra una normalización **suave** —solo `j`→`h`, `hu`→`w`,
`c`→`k`, que son las variantes de verdad— y dejar quietas las vocales. El reconocimiento no debería
cambiar; lo que cambia es que la salida vuelve a ser legible. Es otra corrida de 9 minutos.

Mientras tanto, para el flujo no es grave: lo que lee esa salida es Claude para traducir, y la entiende.
Para enseñarla en pantalla, sí hay que arreglarlo.

## Cómo se entrenó

| | |
|---|---|
| Base | `facebook/mms-1b-all`, adaptador `quy` |
| Qué se entrena | adaptador + capa de salida: **2.2 M de 965 M (0.2 %)** |
| Datos | 476 clips de 4 personas · p16 apartado |
| Receta | 12 épocas, lote efectivo 4, OneCycle, lr 1e-3 |
| Tiempo | **9.3 min** en la A10G |
| Checkpoint | 8.5 MB (solo el adaptador) |
| Mejor validación | WER 28.3 % en el paso 1000 de 1260 |

Los adaptadores no son un atajo: con 25–30 minutos de audio no se entrena una cabeza CTC desde cero,
y sí se acomoda un modelo que ya reconoce quechua. Además el codificador congelado no guarda
gradientes, así que el entrenamiento convivió con el servicio de voz sin apagarlo.

## Lo que cuesta entrenar mientras alguien usa la app

Medido con el entrenamiento corriendo, contra la URL pública:

| | sin entrenar | entrenando |
|---|---|---|
| `/salud` | 0.34 s | 0.35–0.50 s |
| `/idioma` | 1.34 s | **2.98–3.87 s** |

**El túnel no se cae** —todas las respuestas fueron 200— pero la inferencia va 2.5× más lenta porque
la GPU queda al 99 %. Si la app tiene un tiempo de espera corto, parece caída.

`--ceder 0.05` mete una pausa entre pasos para dejarle huecos a la app. Cuesta tiempo de
entrenamiento y a cambio la UI sigue usable mientras se entrena.
