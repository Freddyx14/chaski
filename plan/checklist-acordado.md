# Chaski · todo lo acordado y quién hace qué (vivo) · sáb 24-oct, 15:25 PT

> **Por qué existe.** Freddy, 15:13 y 15:15: *«the things I told you and we agreed on are very important … document
> everything, like the checklist … split it into tasks so we don't miss any task»*. Regla: cada cosa que Freddy pide o
> acordamos entra acá **en el mismo turno**, con dueño, hora y estado; lo que le toca a otra sesión se le pasa en el acto.
> Detalle técnico: `plan/arquitectura-interprete.md` · decisiones formales: `SOT.md` · pitch: `plan/pitch.md`.
>
> ✅ hecho · ⏳ en curso · ⬜ falta · 🔁 pasado (a quién, a qué hora)

---

## A · Quién hace qué (reparto acordado, 14:40)

| Quién | Su parte | Cómo se comunica |
|---|---|---|
| **Freddy** | Datos de las familias, ajuste fino junto con Ricardo, la mamá (revisión y voz), pitch, Devpost, decisiones | — |
| **Ricardo** | Modelos: línea base, ajuste fino (NLLB traducción, omniASR oído, voz), servicio FastAPI + túnel, rutas | Por Freddy (mensajes en su portapapeles) y `plan/tareas.md` |
| **El papá de Freddy** | Pide a la familia que grabe en el formulario | Freddy |
| **La mamá de Freddy** (enfermera, Pilpichaca) | Revisa el quechua (emergencia, app, números) y graba su saludo; experta que valida | Freddy |
| **Sesión ui-ux** | Toda la UI/UX y la app iOS (`movil/`), el SOT y la página visual | `SendMessage` a `ui-ux` |
| **Esta sesión (Claude)** | La arquitectura y el flujo agéntico del intérprete, las barreras, la precisión en cada parte, buenas prácticas, los agentes necesarios (y ninguno más), las mediciones con línea base primero, el formulario, la documentación | Worktrees por frente, integración en `main` |

---

## B · Registro de decisiones y pedidos (en orden)

| Hora | Qué se decidió o pidió | Fuente | Estado |
|---|---|---|---|
| vie | Track principal: Anthropic «Claude for Public Benefit». Comunidad: posta de Pilpichaca, Huancavelica | SOT D1–D8 | ✅ |
| vie | Salud general, **no solo gestantes** | Freddy, 2 veces | ✅ |
| sáb 00:30 | **Claude es el núcleo** (D19); app iOS nativa (D14) | SOT | ✅ |
| 09:05 | **Sirve a los dos lados**, personal y paciente; onboarding idioma → nombre → rol (D27) | Freddy | ✅ app |
| 09:20 | Formulario de voz en lugar del PDF; probado de punta a punta en Chrome | Freddy | ✅ |
| 09:40 | Formulario: se guarda solo, sin código, sin «saltar todo», sin «¿escribe en quechua?», pensado para celular, todo visible sin bajar | Freddy | ✅ |
| 10:31 | **El producto se llama Chaski** (D30) | Freddy | ✅ |
| 09:13 | 🔴 **Línea base de cada modelo ANTES del ajuste fino**, para decir cuánto mejoramos | Freddy | ⏳ Ricardo |
| 11:43 | **Pitch de 3 minutos** + 2 de preguntas; estrategia, guion, demo e investigación de lo que gana | Freddy | ✅ `plan/pitch.md` |
| 12:00 | Entrevista a la mamá guardada; 90 % pacientes quechuahablantes, ~20 % personal; no es «la única enfermera» (son 3 de 6) | entrevista | ✅ |
| 12:44 | **El resumen como plataforma para aprender quechua** (el Estado capacita y no aprenden): hoy glosario; plataforma = visión | Freddy | ✅ glosario · ⬜ línea en el pitch |
| 12:45 | **Intérprete agente, no traductor**: pule los dos lados (Wispr), repregunta, contesta lo que es para él, transmite órdenes, razona (D32) | Freddy + Ricardo | ✅ backend · ✅ app |
| 12:45 | **Claude pule; el modelo ajustado traduce** castellano→quechua (D33) | Freddy + Ricardo | ✅ interruptor · ⬜ `/traducir` |
| 12:45 | **Modo emergencia** con audios verificados, crítico para ellos; **receta** es función clave (D35) | Freddy + Ricardo | ✅ app · ⬜ audios · ⬜ revisión mamá |
| 12:45 | La base médica de Ricardo sirve **para ajustar y para el banco**, nunca para la prueba | Freddy + Ricardo | ✅ regla de fuga en el banco |
| 12:59 | 🔴 **Barreras antes de hablar: es lo que define si lo hicimos bien** (D37) | Freddy | ✅ B1–B6 + falla cerrada |
| 13:02 | Borrar las pruebas fantasma de la base del formulario | Freddy | ✅ · ⬜ p20 «Ricardo» |
| 14:06 | Bajar los datos de las familias para Ricardo + llave de exportación | Freddy | ✅ |
| 14:40 | **RAG con embeddings** para el banco (más complejidad técnica) | Freddy | ✅ |
| 14:40 | **Banco de errores sembrados**: primero la línea base (sin barreras / juez simple), después Chaski | Freddy | ✅ |
| 14:40 | **Dividir en worktrees** y trabajar ordenado | Freddy | ✅ 3 worktrees integrados |
| 14:50 | Llave de Anthropic guardada aparte de la otra, para evals y producción | Freddy | ✅ Keychain `CHASKI_ANTHROPIC_API_KEY` |
| 14:50 | **Crítico en Haiku**; solo los agentes necesarios: principal + crítico (D38, consejo de Anthropic) | nota de voz | ✅ · ⏳ Haiku vs Sonnet |
| 14:50 | Documento de Anthropic sobre agentes (Freddy lo iba a pasar) | Freddy | ⬜ pendiente de Freddy |
| 15:13 | **Pasar el diseño a ui-ux en paralelo, siempre**; checklist de todo | Freddy | ✅ 🔁 ui-ux 15:20 |

---

## C · Tareas por persona, con hora

### Freddy
| | Tarea | Para |
|---|---|---|
| ✅ | Modelo principal: **Opus** (Freddy, 16:13: «if it gives the best accuracy, yes») | — |
| ✅ | Crítico: **Sonnet** (Freddy, 16:13) · 🔁 ui-ux D39 en el SOT | — |
| ✅ | p20 «Ricardo» era prueba: borrada de la base y de `data/formulario/` | — |
| ⏳ | ¿Se guardan los audios de las consultas? ¿Hace falta base de datos? (SpacetimeDB propuesto por Freddy) · recomendación dada 17:00 | ya |
| 🔁 | Mensaje a la mamá en el portapapeles (16:28): revisar las 14 con quechua y escribir las **10 frases de emergencia sin quechua** (dónde le duele, alergia, embarazo, vino con alguien, respirar, vomitó, tomó medicamento, se cayó, vía, no se preocupe) + textos quechua de la app (`movil/src/rimay/textos.ts`) + la tabla de números | 18:00 |
| ⬜ | Mamá: grabar su saludo en quechua para abrir el pitch, con permiso | 18:00 |
| ⏳ | Papá y familia: más grabaciones en el formulario | continuo |
| ⬜ | Pasar el documento de Anthropic sobre agentes | cuando lo tenga |
| ⬜ | Devpost: borrador, marcar Anthropic + People-First + Microsoft + Cartesia | 21:00 |
| ✅ | Repo: se queda este. Fotos y transcript de la entrevista a `.gitignore` (Freddy 16:51: el historial no importa, los créditos vencen) | — |
| ⬜ | Ensayo del pitch con cronómetro (30 s / 3:00 / 2:00) | 22:00 |
| ⬜ | Video de la demo, abre con el momento de la negativa | dom 05:00 |

### Ricardo (los mensajes van por Freddy)
| | Tarea | Para |
|---|---|---|
| ✅ | Línea base: ASR WER 68,9 % (54,1 % normalizado), 175 clips, hablante aparte · traducción chrF++ 42,31 | — |
| 🔴 | **TAREA MUY IMPORTANTE (Freddy, 16:51): el número de DESPUÉS del ajuste fino** (mismo hablante de prueba, mismo script), para el pitch y el Devpost | al terminar el entrenamiento |
| ⏳ | Partir los datos en entrenamiento / banco / prueba antes de entrenar | 15:00 |
| ⏳ | NLLB-200 ajustado + ruta `/traducir` (`texto, de, a` → `{traduccion}`) | 19:00 |
| ⏳ | omniASR ajustado con los audios completos (papá + formulario) | 19:00 |
| ⬜ | Confianza por palabra o N mejores en `/entender` (barrera B1) | 19:00 |
| ⬜ | Audios de emergencia con la voz de Chaski donde no haya grabación | 19:00 |
| ⬜ | Ruta `GET /banco?tag=` (lista en `evals/banco/RUTA_PARA_RICARDO.md`) | 19:00 |
| ⬜ | **Integración**: pegar lo de `app/chaski/PARA_RICARDO.md` (~3 líneas por ruta) y avisar por el grupo antes de reiniciar · 🔁 mensaje 15:40 | 19:00 |
| ✅ | `/resumen` y `/idioma` vivos · túnel fijo | — |

### Sesión ui-ux (🔁 15:20, plazo 19:00)
| | Tarea |
|---|---|
| ✅ | 5 acciones, modo emergencia, receta + «¿me lo repite?», glosario, onboarding de dos lados |
| ⏳ | Contrato final de `Resultado` en la app (estado, aviso, paso_fallido, modelos, ms, contexto) |
| ⏳ | «Pensando» con pasos reales (≈ 5–6 s con Opus + crítico) |
| ⏳ | Bloqueo explicado en palabras simples; ámbar = aviso, rojo = bloqueado |
| ⏳ | Banco real; **nunca reproducir frases sin revisar** (`revisado:false` / `falta_quechua`) |
| ⏳ | Sello «revisado por el crítico» |
| ⏳ | Atajo de ensayo con `FRASE_NEGATIVA_DEMO` («Tómela con agua, no con té», error simulado y dicho como tal) |
| ⬜ | README: dónde se usa Claude y por qué, funciones de Cartesia, límites conocidos, sin llaves |

### Esta sesión (Claude)
| | Tarea | Para |
|---|---|---|
| ✅ | Arquitectura del intérprete (`plan/arquitectura-interprete.md`) | — |
| ✅ | Intérprete, traductor con interruptor, orquestador con falla cerrada | — |
| ✅ | Barreras B1–B6, crítico Haiku, banco de ataques (784 casos) | — |
| ✅ | Banco de frases + RAG híbrido (216 frases, 88 % / 95 %) | — |
| ✅ | Mediciones: intérprete × 3 modelos, ataques (piso / juez / Chaski), RAG | — |
| ✅ | Juez simple y Sonnet como crítico en la misma muestra → **Sonnet: 160/160 y 7,5 % de bloqueos falsos** | — |
| ✅ | Conectar barreras, banco y **el mismo crítico que medimos** dentro del orquestador (había un crítico duplicado sin medir) + `servicio.py` y `PARA_RICARDO.md` | 17:15 |
| ✅ | Ensayo de la negativa: `traduccion_sembrada` → `Resultado.sembrada` · `Resultado.texto_original` (pedidos de ui-ux 15:25) | 17:15 |
| ✅ | 🔴 Hueco real (curl de ui-ux): se perdió «con agua» y pasó. Agregar el **vehículo** (agua, leche, té, comida) a los hechos + barrera en código + caso en el banco de ataques | 16:45 |
| ✅ | Banco de ataques con todo integrado, crítico Sonnet: **165/165 atrapados, 5/40 bloqueos falsos (12,5 %)** | — |
| ✅ | 3 de esos 5 bloqueos son errores del modelo de hechos (500 mg vs cantidad, «en ayunas» = «sin comer», «kuska» = media); los otros 2 son traducciones flojas de la familia y deben bloquearse | 16:40 |
| ⬜ | Bajar los bloqueos falsos (18 %): revisar uno por uno cuáles son errores reales de la familia | 17:30 |
| ⬜ | Correr el banco de ataques completo (784) con el crítico elegido para el número final | 18:00 |
| ✅ | Pitch con los números finales, la negativa simulada y la línea de aprender quechua (`plan/pitch.md`) | — |
| ✅ | Borrador de Devpost listo para pegar (`plan/devpost.md`) | — |
| ⏳ | README público para los jueces | 17:30 |
| ⏳ | Medir el turno completo (Opus + Sonnet + traducción con Claude) para saber la espera real | 17:00 |
| ⬜ | Ayudar a integrar con Ricardo | 19:00–21:00 |

---

## D · Calendario hasta la entrega

| Hora (PT) | Qué |
|---|---|
| 19:00 | **Congelar funciones.** Lo que no esté: traducción → Claude; oído → modelo base; repregunta → fuera de la demo. Emergencia y receta **no** se cortan |
| 19:00–21:00 | Integración servicio ↔ intérprete ↔ app |
| 21:00 | Borrador de Devpost |
| 22:00 | Ensayo del pitch |
| dom 05:00 | Video de la demo |
| dom 07:00 | Congelar los números |
| dom 09:00 | **Entrega** |
| dom 10:30–12:30 | Jurado en la mesa (los dos, todo el tiempo) |

---

## Mediciones: criterios y presupuesto (Freddy 16:51)

| | Tarea | Para |
|---|---|---|
| ✅ | Criterios con pesos y compuertas: `evals/CRITERIOS.md` | — |
| ⏳ | Auditar el banco de ataques + registrar costo real por corrida + `puntuar.py` (sin gastar API) | 18:00 |
| ✅ | Tiempo del crítico: p50 9 s → ~2,7 s, p95 34 s → ~3,6 s, misma precisión; turno completo p50 6,5 s · 🔁 ui-ux 17:00 | — |
| ⬜ | Afinar dentro del tope de **$30** (ver estimación de lo gastado) | — |

## Pendientes conocidos del intérprete

- 0 de 216 frases del banco revisadas: el intérprete no reproduce ninguna hasta que la mamá revise.
- Las respuestas de Chaski al personal en castellano (repreguntar / responder) solo pasan por las barreras de código, no por el crítico.
- La dirección quechua → castellano usa el mismo crítico, pero no está medida.

## E · Números que ya podemos decir (con su archivo)

| Qué | Número | Fuente |
|---|---|---|
| **Chaski integrado, crítico Sonnet, versión final** (205 casos, incluye agua/té) | **165 de 165 errores atrapados (100 %) · 4 de 40 frases correctas bloqueadas (10 %)** | `evals/ataques/resultados/chaski-2026-10-24-1606.json` |
| Chaski, crítico Sonnet, antes de integrar (200 casos) | 160 de 160 · 3 de 40 (7,5 %) | `…/chaski-2026-10-24-1518.json` |
| Chaski, crítico Haiku + código (misma muestra) | 153 de 160 (96 %) · 7 de 40 bloqueos falsos (18 %); falla en diagnósticos agregados (14/20) | `…/chaski-2026-10-24-1513.json` |
| Claude como juez simple, Haiku | 150 de 160 (94 %) · 26 de 40 bloqueos falsos (65 %) | `…/juez_claude-2026-10-24-1513.json` |
| **Claude como juez simple, Sonnet (misma muestra final)** | **165 de 165 · 11 de 40 bloqueos falsos (27,5 %)**, sin decir qué falló | `…/juez_claude-2026-10-24-1644.json` |
| Sin barreras (piso) | 0 % | `…/sin_barreras-…` |
| Intérprete, acción correcta | Opus 98 % · Sonnet 94 % · Haiku 88 % | `evals/interprete/resultados/` |
| RAG, acierto a la primera | híbrido 88 % vs palabras 70 % | `evals/banco/resultados/` |
| Pacientes quechuahablantes / personal que habla quechua | 90 % / ~20 % | entrevista |
| Consulta en castellano / en quechua | 30–40 min / hasta 1 h o más | entrevista |
| Médicos que empiezan el SERUMS con al menos quechua o aimara básico | 14,4 % (84 de 584, encuesta 2016) | Bendezu-Quispe 2020 · `research/personal-salud-quechua.md` |
