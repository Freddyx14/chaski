# Checklist de todo lo acordado (vivo) · sáb 24-oct, 15:20 PT

> **Por qué existe:** Freddy, 15:13: *«it is supposed that you took notes of all the things I told you … the things I
> told you and we agreed on are very important»*. Cada cosa que Freddy pide o acordamos entra acá con dueño y estado,
> en el mismo turno. Detalle técnico en `plan/arquitectura-interprete.md`, decisiones en `SOT.md`.
>
> Estado: ✅ hecho · ⏳ en curso · ⬜ falta · 🔁 pasado a otra sesión (con hora)

## 1 · Producto

| # | Lo acordado | Dueño | Estado |
|---|---|---|---|
| 1 | Sirve a los dos lados: personal de salud y paciente. Onboarding idioma → nombre → rol (D27) | ui-ux | ✅ |
| 2 | El producto se llama **Chaski** (D30) | ui-ux | ✅ |
| 3 | **El usuario principal es el personal que NO habla quechua** (~80 %, entrevista) | todos | ✅ en docs y pitch |
| 4 | **Intérprete agente, no traductor** (D32): 5 acciones (traducir, repreguntar, responder, no_entendí, frase verificada) | esta sesión (backend) · ui-ux (app) | ✅ backend en `main` · ✅ app · ⬜ conectado al servicio de Ricardo |
| 5 | **Pulir los dos lados, estilo Wispr Flow**, sin cambiar datos | esta sesión | ✅ |
| 6 | Repregunta UNA vez al mismo hablante; contesta él lo que es para él; transmite órdenes como indicaciones | esta sesión | ✅ |
| 7 | **Modo emergencia**: frases ya traducidas y grabadas, toca y suena (D35) | ui-ux (pantalla) · esta sesión (banco) · Ricardo (audios) · mamá (revisión) | ✅ pantalla · ✅ banco (24 frases) · ⬜ **10 frases sin quechua → mamá** · ⬜ audios |
| 8 | **RAG con embeddings** para el banco (pedido de Freddy, más complejidad técnica) | esta sesión | ✅ híbrido 88 % acierto a la primera vs 70 % solo palabras |
| 9 | **Receta**: foto → hechos → indicación → «¿me lo repite?» (D35) | ui-ux · Ricardo (`/ver`) | ✅ app |
| 10 | **Aprender quechua desde las consultas** (D36): hoy glosario en el resumen; plataforma = visión en el pitch | ui-ux | ✅ glosario · ⬜ línea en el pitch |
| 11 | **Barreras antes de hablar** = lo que define si lo hicimos bien (D37) | esta sesión | ✅ B1–B6 + falla cerrada |
| 12 | **Solo dos roles: intérprete principal + crítico en Haiku**, ningún agente de más (D38, consejo de Anthropic) | esta sesión | ✅ · ⏳ elegir crítico Haiku vs Sonnet con números |
| 13 | **Ajuste fino**: NLLB para traducir, omniASR para oír, con los datos de las familias | Ricardo | ⏳ |
| 14 | **Línea base primero** de cada modelo, para decir cuánto mejoramos | Ricardo (modelos) · esta sesión (evals) | ⏳ Ricardo · ✅ evals de intérprete, barreras y RAG |
| 15 | Claude pule y audita; el modelo ajustado traduce; Claude de respaldo (D33) | esta sesión · Ricardo | ✅ interruptor · ⬜ `/traducir` de Ricardo |
| 16 | Modelo principal elegido midiendo (D15): **Opus 98 %, 0 datos inventados** vs Sonnet 94 % vs Haiku 88 % | Freddy decide | ⬜ recomendación: Opus |

## 2 · Mediciones (para el pitch)

| # | Qué | Estado |
|---|---|---|
| 17 | Banco de ataques: sin barreras 0 % → juez simple → Chaski | ✅ Chaski+Haiku 96 % atrapados, 18 % bloqueos falsos · ⏳ juez y Sonnet en la misma muestra |
| 18 | Intérprete: 48 escenarios × 3 modelos | ✅ |
| 19 | RAG: palabras vs embeddings vs híbrido | ✅ |
| 20 | Reconocimiento y traducción antes/después del ajuste fino | ⏳ Ricardo |

## 3 · Formulario de las familias

| # | Lo acordado | Estado |
|---|---|---|
| 21 | Guarda texto y audio, probado de punta a punta | ✅ |
| 22 | Sin «¿escribe en quechua?», sin «saltar todo», sin código: se guarda solo | ✅ |
| 23 | Pensado para celular, todo visible sin bajar, empieza arriba | ✅ |
| 24 | Borrar las pruebas fantasma | ✅ (p11, p13, p14, p21–p23) · ⬜ **p20 «Ricardo»: ¿prueba o dato?** |
| 25 | Datos bajados para Ricardo (`data/formulario/`, no se sube) + llave de exportación | ✅ |

## 4 · Pitch y entrega

| # | Lo acordado | Dueño | Estado |
|---|---|---|---|
| 26 | Pitch de **3 minutos** + 2 de preguntas | Freddy + Ricardo | ✅ guion en `plan/pitch.md` |
| 27 | Abrir con 90 % pacientes quechuahablantes / ~20 % personal; **no** «la única enfermera» | — | ✅ corregido |
| 28 | Saludo de la mamá grabado, con permiso | Freddy | ⬜ |
| 29 | Revisión de la mamá: 10 frases de emergencia + textos quechua de la app + tabla de números | Freddy | ⬜ |
| 30 | El momento de la negativa en la demo, que salga 5 de 5 | esta sesión + ui-ux | ⬜ elegir la frase del banco de ataques |
| 31 | Marcar el premio de Anthropic en Devpost (+ People-First, Microsoft, Cartesia) | Freddy | ⬜ |
| 32 | Video de la demo (lo ven sponsors que no pasan por la mesa) | Freddy | ⬜ dom 05:00 |
| 33 | Repo público **sin** `context/photos/` y confirmar si el transcript de la entrevista puede quedar | Freddy | ⬜ |
| 34 | ¿Se guardan los audios de las consultas? (pregunta de privacidad) | Freddy | ⬜ |

## 5 · Pasado a otras sesiones / personas

| Cuándo | A quién | Qué |
|---|---|---|
| 13:10 | ui-ux | 5 acciones, modo emergencia, receta, glosario → ✅ construido |
| 15:20 | ui-ux | Contrato final del orquestador, espera de ~5 s, banco real con frases sin revisar, insignia del crítico, momento de la negativa (ver §6) |
| 13:05 / 13:15 | Ricardo (por Freddy) | Línea base, partir datos, NLLB + `/traducir`, omniASR, audios de emergencia, confianza por palabra en `/entender` |

## 6 · Lo nuevo para la app (enviado a ui-ux a las 15:20)

1. **Contrato final** de `/turno/*` (`app/chaski/orquestador.py`, clase `Resultado`): `estado` (dicho · dicho_con_aviso · bloqueado), `accion`, `motivo`, `aviso`, `texto_salida`, `texto_pulido`, `paso_fallido`, `modelos {principal, critico}`, `ms` por paso, `contexto` (la app lo devuelve en el siguiente turno).
2. **La espera real** con Opus + crítico es ~5–6 s (p95 ~11 s): el «Pensando» muestra pasos reales (Entendiendo → Traduciendo → Revisando) para que no sea silencio.
3. **Bloqueado en palabras simples**: `paso_fallido` + `motivo` → «Chaski no lo dijo: no coincidió la frecuencia». Ámbar para `dicho_con_aviso`, rojo solo para bloqueado.
4. **Banco real** (`app/chaski/banco.json`, 216 frases, 24 de emergencia): **una frase con `revisado: false` o tag `falta_quechua` no se reproduce en modo emergencia**; se muestra como «pendiente de revisión». Sin audio → voz de Chaski cuando Ricardo la genere.
5. **Insignia «revisado por el crítico»** cuando el crítico pasó: es lo que hace visible la seguridad en la demo.
6. **Momento de la negativa**: una frase fija que bloquea siempre, elegida del banco de ataques (negación invertida), cargada como atajo en el modo ensayo.
