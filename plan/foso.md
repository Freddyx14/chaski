# El foso de Chaski: cómo se vuelve un intérprete de salud de Pilpichaca (dom 25-oct, 00:20 PT)

> Pedido de Freddy (23:49): sin el ajuste de NLLB, ¿cómo hacemos que el traductor sea de salud y de la zona, y que eso
> sea difícil de copiar? Investigación con fuentes + medición propia. Detalle de cada número: `evals/HISTORIA.md` §2d.

## La tesis en una línea
**El foso no es el modelo** (se cambia cada pocos meses, y hoy cambiamos de traductor en una hora con números). Es lo
que nadie más tiene: frases revisadas por hablantes de la zona, un set de prueba honesto que no se filtra, y el lazo
que convierte cada corrección en mejor traducción. (Datos en volumen solos son un foso débil:
[a16z](https://a16z.com/the-empty-promise-of-data-moats/); lo defendible es la comunidad revisora y el lazo:
[Masakhane](https://aclanthology.org/2020.findings-emnlp.195/), [Te Hiku Media](https://spectrum.ieee.org/indigenous-ai-voice-models-maori).)

## Paso 1, hecho y medido: las frases de la enfermera como ejemplos (D41)
Antes de traducir, el código busca las 5 frases revisadas por la enfermera más parecidas y se las da al traductor como
ejemplos. Medido sobre las 62 frases que escribieron las familias (nadie las vio, ~5 referencias cada una), con el
traductor del producto y un filtro contra fugas (se descarta todo ejemplo igual o casi igual a una frase de prueba,
el error que invalidó el ajuste de NLLB):

| | Sin ejemplos | Con los de la enfermera |
|---|---|---|
| castellano → quechua | 52,6 | **56,0** (+3,3) |
| quechua → castellano | 49,1 | **56,0** (+6,9) |
| Turno completo, 20 turnos reales | 19/20 dichos, 8,3 s | **20/20 dichos, 8,0 s** |

Lo que aprendimos: los ejemplos no aportan contenido (las frases son otras), aportan **el quechua de la zona**. Por
eso mejoran lo de las familias de la región y alejan de las 30 de Ricardo, que vienen de otra fuente y otra variedad
(42,6 vs 48,3). Un umbral de parecido no ayudó (52,5). Coincide con la literatura: elegir ejemplos por parecido rinde
más en idiomas con pocos datos ([Zebaze et al. 2025](https://arxiv.org/html/2408.00397)), y lo que más pesa es la
calidad del ejemplo ([Vilar et al. 2023](https://aclanthology.org/2023.acl-long.859/)).

## El lazo (el canal de mejora que todo agente nuestro debe tener)
```
consulta → turno bloqueado o corregido → cola para la enfermera (lo que el crítico dudó + lo más usado)
        → ella lo revisa en /corregir → entra al banco con revisado: true → el próximo turno lo usa de ejemplo
```
Con 24 frases revisadas ya mueve +3 a +7 puntos. Cada frase nueva mejora la siguiente traducción, sin reentrenar nada.
Priorizar la cola por duda del crítico supera elegir al azar ([Chimoto & Bassett 2022](https://aclanthology.org/2022.findings-emnlp.348/)).

## Lo que sigue, en orden (de la investigación)
| # | Qué | Evidencia | Esfuerzo |
|---|---|---|---|
| 2 | Más pares revisados, no más gramática | casi toda la ganancia de un libro de gramática viene de sus ejemplos ([Aycock et al. 2025](https://arxiv.org/abs/2409.19151)) | horas de la enfermera, no de código |
| 3 | La cola de revisión priorizada (el lazo de arriba) | ([Chimoto & Bassett](https://aclanthology.org/2022.findings-emnlp.348/), [Unbabel](https://unbabel.com/a-closer-look-at-unbabels-award-winning-translation-quality-estimation-systems/)) | medio |
| 4 | Simplificar el castellano antes de traducir (Opus ya pule) | la simplificación fue la reescritura más efectiva de 21 ([Ki & Carpuat 2025](https://arxiv.org/abs/2502.16682)) | bajo: medir el pulido vs el texto crudo |
| 5 | Mantener la retraducción a ciegas + hechos en código como compuerta | la retraducción atrapó errores clínicos que la estimación de calidad no ([Mehandru et al. 2023](https://aclanthology.org/2023.emnlp-main.712/)) | ya está |
| 6 | Plantillas revisadas para lo más frecuente | sin estudio médico que lo mida (sin verificar); lo que no se genera no se traduce mal | medio |

## Trampas
- **Fugas al set de prueba**: con ejemplos del mismo manual, un sistema sacó BLEU 21,2; con frases de un hablante real, 4,4
  ([Merx et al. 2024](https://arxiv.org/abs/2404.04809)). Ningún ejemplo puede venir del set de prueba ni del banco de 952 errores.
- **Ejemplos malos dañan más en idiomas con pocos datos** ([2025](https://arxiv.org/abs/2510.00829)): solo `revisado: true`.
- **COMET y similares no están validados para quechua**: no se usan como compuerta; chrF++ como AmericasNLP.
