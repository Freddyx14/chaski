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

| 9 | dom 03:14 | **Tras la auditoría de la noche** (C1, H1–H3, M1, M3, M5–M8) y la retraducción con sentido de calendario | **183/184 (99,5 %); 100 % de los críticos** | **7/40 (17,5 %)** | 2,6 s (p95 3,8 s) | Ningún arreglo de seguridad costó atrapados; bajó un bloqueo falso | `chaski-2026-10-25-0314.json` |

\* El banco auditado tiene más frases de la familia (nueva participante). De las 7 «correctas» que retuvo, unas 3–4 son
traducciones flojas de verdad (le falta una palabra, agrega algo). Chaski falla del lado seguro: se calla y dice por qué.

## 2 · ¿El intérprete elige bien qué hacer? (48 escenarios reales)

| Hora | Intérprete principal | Acción correcta | Datos clínicos inventados | Tiempo (p50) | Archivo |
|---|---|---|---|---|---|
| 15:00 | Haiku 4.5 | 88 % | 1 | 2,1 s | `claude-haiku-4-5-20251001-2026-10-24-1500.json` |
| 15:04 | Sonnet 5 | 94 % | 1 | 2,3 s | `claude-sonnet-5-2026-10-24-1504.json` |
| 15:08 | **Opus 5** | **98 %** | **0** | 3,7 s | `claude-opus-5-2026-10-24-1508.json` |
| 16:39 | Opus 5 + crítico Sonnet, turno completo | **100 %** | **0** | decidir + crítico ~13 s → **6,5 s** tras acelerar el crítico (sin traducción ni voz: ver la fila de las 21:56) | `claude-opus-5-2026-10-24-1639.json` |

| dom 03:41 | **Opus 5, pensamiento «low» explícito** (antes el del modelo con 800 tokens: a veces gastaba todo pensando y no respondía → 27 s y «no entendí») | **98 %** (el único fallo pide repetir) | **0** | **2,3 s** (p95 3,8 s) | `evals/interprete/resultados/decidir-{no,low,modelo}.txt` (sin pensar 96 %, 2,6 s; el del modelo con espacio 100 %, 4,0 s, p95 9,5 s) |

### 2b · Tiempo de punta a punta, medido (24-oct, 21:56)

16 turnos reales del personal, uno tras otro. El audio de cada uno pasó por el servicio vivo de Ricardo (`/escuchar`, `/voz`) y el intérprete corrió local con los modelos de producción. Archivo: `evals/latencia/resultados/e2e-20261024-2156.json`.

| Turno | p50 | Peor | Dónde se va el tiempo |
|---|---|---|---|
| Instrucción traducida (9) | **17,3 s** | 26,1 s | oír 1,1 · decidir (Opus) 2,9 · **traducir (Sonnet, pensando) 9,0** · barreras 0,03 · crítico 3,1 · voz 1,0 |
| Repregunta o respuesta (6) | 3,8 s | 4,6 s | solo oír + decidir |
| Frase verificada del banco (1) | 4,1 s | — | oír + decidir + audio ya revisado |

**En vivo, modo manos libres (`/turno/vivo`, dom 03:50, tras arreglar el pensamiento de la decisión):** 9 audios
reales (6 de personal con voz sintética peruana, 3 del hablante p16 que el reconocedor nunca oyó). Quién habló y qué se oyó:
**0,5–1 s**. Lo que va a decir en pantalla: **2,7–5,2 s**. Voz lista: **8,5 s típico** (3,5 s una repregunta; 12–18 s una
indicación médica larga). Antes del arreglo: ~25–28 s (la decisión a veces gastaba sus 800 tokens pensando y no respondía).

**El traductor es el paso más lento, y por calidad.** Con el prompt del producto, sobre los 30 pares de referencia de Ricardo (`evals/latencia/traductor_modos.py`):

| Pensamiento del traductor | chrF++ | p50 |
|---|---|---|
| **El del modelo (hoy)** | **51,8** | 5,6 s |
| medium | 45,6 | 3,0 s |
| apagado | 43,1 | 1,7 s |
| low | 41,3 | 2,0 s |

El 42,31 que se venía citando se midió **con el pensamiento apagado** y con otro prompt. El traductor del producto piensa y mide 51,8. Se cambia con `CHASKI_PENSAR_TRADUCIR`; por defecto queda el del modelo (primero la precisión).

### 2c · Jev como respaldo para decidir la acción (24-oct, 22:55)

Pedido de Freddy (22:50): medir Jev (TypeSafe) como respaldo, no como reemplazo. Una llamada por turno con preguntas
tipadas (acción, dato faltante, frase del banco); a quién va se deduce en código. Mismos 48 escenarios que Opus.
Archivo: `evals/jev/resultados/jev-20261024-2255.json` (script `evals/jev/correr.py`).

| | Opus 5 (producto) | Jev |
|---|---|---|
| Acción correcta | 98–100 % | **83 % (40/48)** |
| Tiempo p50 | 2,9 s | **0,4 s** (p95 1,8 s) |
| Costo de los 48 | — | ~$0,002 (precio publicado por TypeSafe, sin verificar en la factura) |
| Frase del banco correcta | — | 4/4 |
| Dato faltante correcto | — | 1/3 |

Por categoría acierta todo en basura, inyección, meta, paciente en quechua y banco. Falla donde más importa: en 3 de 3
casos donde faltaba un dato crítico eligió traducir (`med-04`, `emer-01`, `asr-02`). Ahí las barreras no salvan,
porque la traducción es fiel a una indicación incompleta.

**Cascada por confianza:** si Jev decide solo cuando su confianza es ≥ 0,85, decide 16 de 48 turnos sin ningún error y
Opus decide el resto: ~0,8 s menos en promedio. El umbral está ajustado sobre solo 48 casos, así que es una pista, no
un número para el pitch. Veredicto: **no reemplaza a Opus**; sirve como respaldo si Opus falla, y como primer filtro
cuando confía mucho.

### 2d · El foso, paso 1: las frases de la enfermera como ejemplos (dom 25-oct, 00:15)

Traductor del producto (Sonnet 5 medium), las 5 más parecidas por búsqueda híbrida, filtro contra fugas (iguales,
referencias y coseno ≥ 0,92 fuera). Archivo `evals/moat/resultados/`, script `evals/moat/ejemplos.py`.

| Ejemplos | Familias es→qu | Familias qu→es | 30 de Ricardo (saludos, 1 referencia) |
|---|---|---|---|
| Ninguno | 52,6 | 49,1 | 48,3 |
| **Las 24 de la enfermera** | **56,0** | **56,0** | 42,6 |
| Las 286 verificadas | 53,3 | 56,0 | 40,4 |
| La enfermera, solo si parecido ≥ 0,45 | 52,5 | 54,5 | 45,0 |

Turno completo con los ejemplos (20 turnos reales): **20/20 dichos, p50 8,0 s, p95 10,5 s** (sin ellos: 19/20, 8,3 s,
14,3 s). Queda prendido (D41). Por qué bajan las de Ricardo: los ejemplos enseñan el quechua de la zona, y esas 30
vienen de otra fuente y variedad; las de las familias son de la región y tienen ~5 referencias, por eso mandan.

### 2e · ¿Memoria automática como ejemplos? (dom 25-oct, 01:35)

100 frases clínicas nuevas traducidas por Chaski; 85 pasaron barreras + crítico. Archivo `evals/moat/resultados/memoria-auto-*.json`.

| Ejemplos | Familias es→qu | Familias qu→es |
|---|---|---|
| Ninguno | 54,9 | 51,2 |
| **Enfermera (24)** | **57,4** | **56,3** |
| Automática (85) | 56,2 | 54,3 |
| Enfermera + automática | 56,6 | 54,8 |
| Enfermera 5 + automática 2 | 56,4 | 54,8 |

La base salió 54,9 acá y 52,6 en §2d: el ruido entre corridas es de ~2 puntos, por eso se decide por la dirección
repetida (la automática nunca superó a la enfermera en 3 mezclas), no por una cifra. Decisión D44: se guarda todo,
solo lo aprobado es ejemplo.

### 2f · Consultas completas en modo manos libres, en vivo (dom 25-oct)

Tres consultas (dolor de cabeza, niño con fiebre, barriga), 22 turnos, nadie le dice a Chaski quién habla. Personal con voz
sintética peruana (ElevenLabs), paciente con audio real de p16 (el hablante que el reconocedor nunca oyó).
Script `evals/conversacion/simular.py`, resultados en `evals/conversacion/resultados/`.

| | 02:50 (antes de los arreglos) | **03:54 (todo desplegado)** |
|---|---|---|
| Quién habló | 20/22 | **21/22** |
| A quién y en qué idioma | 14/14 | **18/18** |
| Números perdidos | 0 | **0** |
| Turno p50 / p95 | 13,9 s / 38,8 s | **7,8 s / 11,4 s** |
| Consulta completa | 64–192 s | **49–70 s** |

Y con 30 frases reales de p16 por `/turno/paciente` (`evals/vivo/`): de 9 dichos / 12 pidió repetir / 2 bloqueados
(02:44) a **24 dichos / 6 pidió repetir / 0 bloqueados**, números intactos 3/3, p50 10,7 s (03:25).

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
| Traducción (chrF++, 100 pares reservados) | NLLB-200 tal cual: 25,78 · MADLAD-400-3B: 12,69 · **Claude Sonnet: 42,31** sin pensar (el traductor del producto, que piensa: **51,8**, §2b) | ~~NLLB ajustado: 31,71~~ **no vale: 58 de las 100 frases de evaluación entraron al entrenamiento** (Ricardo, `2fac55f`). Comparación limpia de cinco traductores: `evals/traduccion/` y D43. Antes se leía: NLLB ajustado 31,71 (+23 % relativo), pero sigue debajo de Claude → **Claude sigue traduciendo** (D33; commit `bf4a788`) |
| Voz de Chaski (texto a voz) | Voz de Meta tal cual: robótica | Ajustada con la voz de la enfermera: suena como ella. **Se juzga con oídos humanos** (prueba a ciegas con la enfermera), no con el reconocedor: la voz la escucha un paciente, no una máquina (Freddy, 20:45). La ida y vuelta por el reconocedor (`ac1b924`) queda como dato secundario |

## La historia en una frase (para el pitch)

«Empezamos sin ninguna barrera: todo error llegaba al paciente. Preguntarle a Claude "¿está bien?" bloqueaba 7 de cada
10 frases correctas. Con barreras en código y un crítico elegido midiendo, hoy Chaski atrapa el 100 % de los errores
de dosis, negación y medicamento en menos de 3 segundos, y siempre dice qué dato falló.»
