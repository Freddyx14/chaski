# Chaski · instrucciones para cualquier sesión de Claude en este repo

## 🔴 PRIORIDAD AHORA (sáb 24-oct, 23:45 PT) · si eres la sesión de Ricardo, empieza por acá

**Lee y ejecuta `plan/HANDOFF-RICARDO-SERVICIO.md`**: el servicio vuelve a traducir con Claude (D40), arreglar
`/turno/paciente`, la ruta en vivo y la voz durante el crítico. Al terminar, push y avisa por el grupo.
(La voz de la enfermera, `plan/HANDOFF-RICARDO-VOZ.md`, ya se entregó.)

## Dónde está cada cosa
| | |
|---|---|
| `SOT.md` | La fuente de verdad: producto y decisiones (D1–D39). Toda decisión nueva va primero acá |
| `plan/checklist-acordado.md` | Todo lo acordado, quién hace qué y a qué hora, hasta la entrega (dom 9:00 PT) |
| `plan/tareas.md` | Tareas por persona (la sección de Ricardo tiene las críticas) |
| `plan/arquitectura-interprete.md` | Cómo funciona el intérprete, las barreras y el crítico |
| `plan/pitch.md` · `plan/devpost.md` · `README.md` | Pitch, texto de Devpost y README público, con números de archivos reales |
| `evals/HISTORIA.md` | De la línea base al resultado final, con cada medición |
| `plan/medios.md` | Videos y audios de la enfermera: archivo, qué dice y dónde va (pitch, video Devpost) |

## Reglas del repo
- Varias sesiones trabajan a la vez: `git pull --rebase` antes de cada push, stagea solo tus archivos, nunca `push -f`.
- Ningún número en el pitch, el Devpost o el README sin un archivo de resultados que lo respalde.
- Nunca subas llaves, audios de la familia (`data/` está en `.gitignore`) ni el transcript de la entrevista.
- Lo que el paciente escucha pasa siempre por las barreras; una frase del banco solo se dice si `revisado: true`.
