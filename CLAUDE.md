# Chaski · instrucciones para cualquier sesión de Claude en este repo

## 🔴 PRIORIDAD AHORA (sáb 24-oct, 18:45 PT) · si eres la sesión de Ricardo, empieza por acá

**Lee y ejecuta `plan/HANDOFF-RICARDO-VOZ.md`**: la voz de Chaski ajustada con la voz de la enfermera.
Las 24 frases de emergencia con esa voz, la comparación con la voz de Meta (ida y vuelta + A/B/C), una prueba a
ciegas para la enfermera, y **al terminar: documentar y hacer push** para que Freddy haga pull y se lo mande a su mamá.
Avisa por el grupo cuando esté.

## Dónde está cada cosa
| | |
|---|---|
| `SOT.md` | La fuente de verdad: producto y decisiones (D1–D39). Toda decisión nueva va primero acá |
| `plan/checklist-acordado.md` | Todo lo acordado, quién hace qué y a qué hora, hasta la entrega (dom 9:00 PT) |
| `plan/tareas.md` | Tareas por persona (la sección de Ricardo tiene las críticas) |
| `plan/arquitectura-interprete.md` | Cómo funciona el intérprete, las barreras y el crítico |
| `plan/pitch.md` · `plan/devpost.md` · `README.md` | Pitch, texto de Devpost y README público, con números de archivos reales |
| `evals/HISTORIA.md` | De la línea base al resultado final, con cada medición |

## Reglas del repo
- Varias sesiones trabajan a la vez: `git pull --rebase` antes de cada push, stagea solo tus archivos, nunca `push -f`.
- Ningún número en el pitch, el Devpost o el README sin un archivo de resultados que lo respalde.
- Nunca subas llaves, audios de la familia (`data/` está en `.gitignore`) ni el transcript de la entrevista.
- Lo que el paciente escucha pasa siempre por las barreras; una frase del banco solo se dice si `revisado: true`.
