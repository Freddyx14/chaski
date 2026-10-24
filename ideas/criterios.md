# Criterios — con esto medimos cada idea

Cada idea se mide contra esta hoja **antes** de escribir una línea de código. Si una idea nueva aparece a
medianoche, pasa por aquí primero.

De dónde sale cada criterio:
- **Anthropic** (lámina del track, `context/photos/IMG_4767.jpg`): los 4 criterios del track.
- **Cal Hacks** (guía, `context/hacker-guide-calhacks-13.md`): impacto, calidad, complejidad técnica, creatividad; demo en vivo obligatoria.
- **Héctor**, jurado de HackMIT: que sea técnicamente difícil y no una categoría repetida.
- **Peel**, ganador de HackMIT 2026: una medición nueva, una sola cifra que enmarca todo, una demo física.
- **Freddy**: que nos importe de verdad y que el sistema mejore con el uso.

---

## Paso 1 · Compuertas (si falla una, la idea muere)

| # | Compuerta | Pregunta |
|---|---|---|
| G1 | **Se puede hacer este fin de semana** | ¿Los datos, modelos y APIs están accesibles **hoy**, sin convenios ni registros que tarden días? ¿Hay demo en vivo el domingo a las 10:30? |
| G2 | **No existe ya para esta comunidad** | ¿Alguien ya le da esto a **este mismo grupo**? Que exista en otro país o para otro cliente está bien; para la misma gente, no |
| G3 | **El peor error tiene techo** | Si el sistema se equivoca, ¿el daño se puede contener con una protección concreta? |
| G4 | **Nos importa** | ¿Al menos uno de los dos lo vivió, o lo vivió alguien cercano? Son 36 horas sin dormir; sin eso, se abandona el sábado a las 3 AM |

## Paso 2 · Puntaje (100 puntos)

Cada criterio se califica de 1 a 5. Puntos = nota ÷ 5 × peso.

| # | Criterio | Peso | Qué es un 5 | Qué es un 1 |
|---|---|---|---|---|
| 1 | **Comunidad con nombre** (Anthropic 1) | 15 | Un grupo que se puede contar y encontrar: «gestantes quechuahablantes de los centros de salud de Huancavelica» | «Peruanos», «estudiantes», «comunidades» |
| 2 | **Problema real, con testimonio** (Anthropic 2) | 15 | Lo vivimos o tenemos una cita textual de alguien que lo vivió, más una cifra verificada | Una suposición de escritorio |
| 3 | **Funciona el lunes y el impacto se mide** (Anthropic 3) | 15 | Una sola cosa que una persona real puede usar el lunes, con una métrica concreta (minutos, %, casos) | Demo amplia que solo vive en láminas |
| 4 | **Claude es central y sabemos dónde falla** (Anthropic 4) | 15 | Sin Claude no hay producto, y tenemos una tabla de fallas con su protección, medida | Claude como envoltorio de chat |
| 5 | **Difícil técnicamente y nuevo** (Héctor, Cal Hacks) | 15 | Medimos o construimos algo que nadie ha hecho públicamente | Un CSV + un prompt; o algo que una startup ya vende |
| 6 | **Momento de demo** (Peel) | 10 | Un jurado lo toca, lo oye o lo ve pasar en vivo en 30 segundos | Hay que explicarlo con diapositivas |
| 7 | **Factible con nuestro equipo en 36 h** | 10 | Usa lo que Ricardo y Freddy ya dominan; el riesgo técnico se resuelve en una prueba de 1 hora | Depende de algo que nunca hemos hecho y que puede no funcionar |
| 8 | **Mejora con el uso** (Freddy) | 5 | Cada uso deja una señal que corrige al sistema (canal de retroalimentación) | No aprende nada |

**Desempate:** tracks adicionales creíbles (Planet-First, People-First, Microsoft, Cartesia, Elastic), sin agregados a la fuerza.

## Paso 3 · Lo que el pitch tiene que poder decir en una frase cada uno

1. **Quién**: la comunidad, con su número.
2. **La cifra**: una sola, verificada, que enmarca todo.
3. **El momento**: lo que el jurado ve pasar en vivo.
4. **Dónde falla Claude** y qué hicimos al respecto.
5. **Cómo medimos el impacto** el lunes.

Si alguna de las cinco no sale en una frase, la idea todavía no está lista.

---

## Ideas ya medidas

| Idea | Compuertas | Puntaje | Nota |
|---|---|---|---|
| Fuego, última milla (`propuesta.md`) | G2 a medias: la detección ya existe; G4 débil, Freddy no está convencido | 85 | Los mejores datos; poca novedad |
| Intérprete chanka en salud materna (`decision.md`) | Pasa, **si** conseguimos un hablante de chanka y la voz en quechua funciona en una prueba de 1 h | 85 | El más nuevo y el que más nos importa |
| Mercurio en las casas de Huancavelica | G1 dudosa: no hay datos por casa | 67 | El problema más desatendido; difícil de medir a distancia |
| Quebradas en Lima | Pasa | — | Freddy no se convenció |
| Presupuesto del distrito, Beca 18, docente multigrado | Pasan | — | Fallan el criterio 5 (poco difíciles técnicamente) |
| Anemia por foto del ojo | **Falla G2**: AnemiaApp ya existe en Perú | — | |
| Información de candidatos | **Falla G1**: las elecciones ya fueron | — | |
