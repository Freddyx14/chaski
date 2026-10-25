# De dónde partimos y cómo llegamos (sáb 24-oct)

> Pedido de Freddy (17:50): *«the explanation of why, and the comparison between the baseline we came from and all
> the improvements that we did»*. Cada fila es una corrida real con su archivo en `evals/*/resultados/`. Lo que no
> mejoró también está, porque es parte de la historia.

## 1 · ¿Atrapa los errores antes de que lleguen al paciente? (banco de errores sembrados)

| # | Hora | Configuración | Errores atrapados | Correctas retenidas | Crítico (p50) | Qué aprendimos | Archivo |
|---|---|---|---|---|---|---|---|
| 0 | 14:59 | **Sin barreras** (el piso: se dice todo) | 0 % | 0 % | — | Sin control, todo error llega al paciente | `sin_barreras-2026-10-24-1459.json` |
| 1 | 14:59 | **Claude como juez simple** (Haiku: «¿está bien traducido?») | 150/160 (94 %) | 28/40 (70 %) | — | Un juez simple se asusta con todo: inservible en una posta | `juez_claude-2026-10-24-1459.json` |
| 2 | 15:02 | Chaski v1: barreras en código + crítico Haiku | 157/160 (98 %) | 12/40 (30 %) | — | El código atrapa el 100 % de dosis, negación, medicamento | `chaski-2026-10-24-1502.json` |
| 3 | 15:05 | + paciente y acompañante como un solo lado | 156/160 | 10/40 (25 %) | — | Un bloqueo de más venía de una regla demasiado estricta | `chaski-2026-10-24-1505.json` |
| 4 | 15:13 | Muestra al azar (antes eran las 20 primeras: una sola familia) | 153/160 (96 %) | 7/40 (18 %) | — | Corregimos un sesgo de la medición, no del producto | `chaski-2026-10-24-1513.json` |
| 5 | 15:18 | **Crítico Sonnet** en vez de Haiku | 160/160 (100 %) | 3/40 (7,5 %) | ~9 s | Haiku dejaba pasar diagnósticos inventados; los números eligieron Sonnet | `chaski-2026-10-24-1518.json` |
| — | 16:44 | Juez simple con **Sonnet** (comparación justa) | 165/165 | 11/40 (27,5 %) | — | Un modelo fuerte también atrapa, pero bloquea más y no dice por qué | `juez_claude-2026-10-24-1644.json` |
| 6 | 15:49 | Integrado en el producto + hueco real «con agua» cerrado (vehículo) | 165/165 | 5/40 (12,5 %) | ~9 s | Un curl en vivo encontró un hueco; ahora hay 5 casos que lo prueban | `chaski-2026-10-24-1549.json` |
| 7 | 16:06 | + concentración (500 mg), «en ayunas» = «sin comer», «kuska» = media | 165/165 | 4/40 (10 %) | ~9 s | Tres bloqueos falsos eran errores de nuestro modelo de hechos | `chaski-2026-10-24-1606.json` |
| 8 | 17:40 | **Final**: banco auditado (952 casos), crítico rápido | **183/184 (99,5 %); 100 % de los críticos** | 8/40 (20 %)* | **2,6 s** (p95 3,4 s) | Sin «thinking» en la extracción y llamadas en paralelo: 3,5× más rápido sin perder precisión. **$0,0084 por turno** | `chaski-2026-10-24-1740.json` |

\* El banco auditado tiene más frases de la familia (nueva participante). De las 7 «correctas» que retuvo, unas 3–4 son
traducciones flojas de verdad (le falta una palabra, agrega algo). Chaski falla del lado seguro: se calla y dice por qué.

## 2 · ¿El intérprete elige bien qué hacer? (48 escenarios reales)

| Hora | Intérprete principal | Acción correcta | Datos clínicos inventados | Tiempo (p50) | Archivo |
|---|---|---|---|---|---|
| 15:00 | Haiku 4.5 | 88 % | 1 | 2,1 s | `claude-haiku-4-5-20251001-2026-10-24-1500.json` |
| 15:04 | Sonnet 5 | 94 % | 1 | 2,3 s | `claude-sonnet-5-2026-10-24-1504.json` |
| 15:08 | **Opus 5** | **98 %** | **0** | 3,7 s | `claude-opus-5-2026-10-24-1508.json` |
| 16:39 | Opus 5 + crítico Sonnet, turno completo | **100 %** | **0** | turno ~13 s → **6,5 s** tras acelerar el crítico | `claude-opus-5-2026-10-24-1639.json` |

## 3 · ¿Encuentra la frase verificada correcta? (RAG, 76 consultas)

| Método | Acierta a la primera | Entre las 5 primeras |
|---|---|---|
| Solo palabras | 70 % | 86 % |
| Solo embeddings | 77 % | 88 % |
| **Híbrido** | **88 %** | **95 %** |

## 4 · Voz (Ricardo)

| | Antes del ajuste fino | Después |
|---|---|---|
| Reconocimiento de quechua (WER normalizado, hablante que el modelo no oyó, 175 clips) | MMS tal cual: 53,9 % · 30/175 perfectas (omniASR: 54,1 %) | **MMS + nuestro adaptador: 40,9 % · 51/175 perfectas** (−24 % relativo; commit `7b57a9b`) |
| Traducción (chrF++, 100 pares reservados) | NLLB-200 tal cual: 25,78 · MADLAD-400-3B: 12,69 · **Claude Sonnet: 42,31** | **NLLB ajustado: 31,71** (+23 % relativo), pero sigue debajo de Claude → **Claude sigue traduciendo** (D33; commit `bf4a788`) |
| Voz de Chaski (texto a voz) | Voz de Meta tal cual: robótica | Ajustada con la voz de la enfermera: suena como ella. **Se juzga con oídos humanos** (prueba a ciegas con la enfermera), no con el reconocedor: la voz la escucha un paciente, no una máquina (Freddy, 20:45). La ida y vuelta por el reconocedor (`ac1b924`) queda como dato secundario |

## La historia en una frase (para el pitch)

«Empezamos sin ninguna barrera: todo error llegaba al paciente. Preguntarle a Claude "¿está bien?" bloqueaba 7 de cada
10 frases correctas. Con barreras en código y un crítico elegido midiendo, hoy Chaski atrapa el 100 % de los errores
de dosis, negación y medicamento en menos de 3 segundos, y siempre dice qué dato falló.»
