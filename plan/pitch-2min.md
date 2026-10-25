# Chaski · pitch de 2 minutos (dom 25-oct, 09:55) · se dice en inglés

> ~270 palabras ≈ 2:00 a ritmo tranquilo. Cada bloque dice qué lámina va. **F** = Freddy, **R** = Ricardo.
> El video del demo (lámina 4) va **sin sonido**: tú hablas encima.

---

**[Lámina 1 · Chaski] · 0:00–0:10 · F**
Hi, I'm Freddy, and this is Ricardo. This is Chaski: a medical interpreter for clinics in the Andes, where the patients speak Quechua and the doctors don't.

**[Lámina 2 · su mamá] · 0:10–0:30 · F**
That's my mother. She's a nurse in Pilpichaca, in the highlands of Peru. Nine out of ten of her patients speak Quechua, the Indigenous language of the Andes. But only one in seven doctors sent to rural Peru speaks it. When nobody can translate, they use gestures. She breaks a pill into four, just to show the dose.

**[Lámina 3 · intérprete] · 0:30–0:45 · F**
Chaski is not Google Translate. It works like a real interpreter. It knows who is speaking. It asks a question back when something important is missing. And it checks every instruction before it says it.

**[Lámina 4 · demo, video sin sonido] · 0:45–1:20 · F**
Here, a health worker gives an instruction in Spanish. Chaski says it in Quechua. But first, a second AI translates it back, and checks the dose, the hours, and every "not". If something changed, Chaski doesn't say it. It asks the person to repeat. The patient answers in Quechua, and the health worker reads it in Spanish. In an emergency, Chaski plays phrases a nurse already checked, right away, in my mother's voice.

**[Lámina 6 · cómo está hecho] · 1:20–1:42 · R**
There's almost no recorded Quechua in the world. So our families recorded it this weekend: 362 recordings. We used them to train Meta's speech models to understand Chanka Quechua. Claude Opus decides what to do. Claude Sonnet translates, and checks.

**[Lámina 8 · medido] · 1:42–2:00 · F**
We tested it with 184 hidden mistakes: wrong doses, missing "nots". Chaski caught 99.5 percent, and every dangerous one. Next, it goes to my mother's health post.

---

## Auditoría de claridad (para un juez que oye esto una sola vez)

| Antes | Ahora | Por qué |
|---|---|---|
| "seeded errors" | "hidden mistakes: wrong doses, missing 'nots'" | Nadie fuera de ML sabe qué es "seeded" |
| "fine-tuned on our data" | "used them to train Meta's speech models" | Verbo común, el juez entiende qué hicimos |
| "blind back-translation" | "a second AI translates it back" | Se entiende sin jerga |
| "100 % of critical errors" | "every dangerous one" | Dice lo que importa en una clínica |
| "Chanka" sola | "Quechua… Chanka Quechua" una vez | La variante se nombra después de explicar el idioma |
| "health workers" | "doctors", "a health worker" | Concreto; D45: nunca "for nurses" |
| Oraciones de 25+ palabras | Máximo ~15 palabras | Se dicen de un respiro |

**Números, todos con archivo:** 9 de 10 (entrevista) · 1 de 7 (Bendezu-Quispe 2020) · 362 grabaciones (README) ·
184 / 99,5 % / 100 % críticos (`evals/ataques/`, `docs/measured-results.pdf`).
