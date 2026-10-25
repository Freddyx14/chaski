# Chaski · guion final de la mesa (dom 25-oct, 10:05) · se dice en inglés

> Estructura de Freddy: el problema (su mamá + datos) → el producto en corto → **en vivo**: ida y vuelta castellano ↔
> quechua, foto de la receta, emergencia → Ricardo: arquitectura y ajuste fino → las mediciones → palabra final.
> ~3:00. **F** = Freddy, **R** = Ricardo. Cada número tiene su archivo (abajo).

---

## 1 · El problema · 0:00–0:35 · F
*[Lámina 2: play al video de su mamá, 12 s]*

That's my mother. She's a nurse in Pilpichaca, high in the Andes of Peru. She just told you the problem: the doctors
who come from the coast don't speak Quechua, the Indigenous language of the Andes.

And the numbers back her up. Nine out of ten of her patients speak Quechua. Only one in seven doctors sent to rural
Peru speaks even basic Quechua. So when nobody can translate, they use gestures. She breaks a pill into four, just to
show the dose.

## 2 · El producto, en corto · 0:35–0:50 · F
*[Lámina 3]*

So we built Chaski. It's not a translator, it's an interpreter. It listens hands-free, it knows who is speaking, and
it checks every instruction before it says it. Let me show you.

## 3 · En vivo · 0:50–1:45 · F (+ R con el audio del paciente)

**Ida y vuelta, una vez.** *[Al celular, en castellano: «Tome una pastilla cada ocho horas, después de comer.»]*
While it thinks, a second AI is translating the Quechua back, to check the dose and the hours didn't change.
*[Chaski habla en quechua.]* *[Ricardo pone el audio del paciente junto al micrófono.]*
The patient answers in Quechua, and I read it in Spanish.

**La receta.** *[Foto de la caja.]* Now I take a photo of the medicine box. Chaski reads it, and reads it back to me
first: *"paracetamol, 500 milligrams, shall I tell them?"* Only after I say yes, it says it in Quechua.

**Emergencia.** *[Dos toques.]* And in an emergency, there's no time to wait. These questions were reviewed by a nurse,
and they play instantly, in my mother's voice.

## 4 · Cómo está hecho · 1:45–2:25 · R
*[Lámina de arquitectura]*

There's almost no recorded Quechua like this in the world: the biggest open dataset has three minutes of it. So our
families recorded it this weekend, 476 clips from four family members. We used them to train Meta's speech model to
understand Chanka Quechua. Training took nine minutes on one GPU, and we only trained 0.2 percent of the model.

Then Claude does the thinking. Claude Opus decides what a good interpreter would do: translate, or ask a question
back. Claude Sonnet translates, and checks. And if anything fails, Chaski stays safe: it asks the person to repeat.

## 5 · Lo que medimos · 2:25–2:50 · F
*[Lámina de mediciones]*

We didn't just build it, we measured it. On a voice the model never heard, word errors went down from 54 to 41
percent. We hid 184 mistakes in translations, wrong doses, missing "nots", and Chaski caught 99.5 percent, and every
dangerous one. In full consultations, it knew who was speaking 21 times out of 22.

## 6 · Palabra final · 2:50–3:00 · F
*[Lámina de cierre]*

Today, when the doctors don't understand, my mother translates. Chaski is for every patient she can't be there for.
Next, it goes to her health post. Thank you.

---

## Auditoría de claridad

| Antes | Ahora |
|---|---|
| "seeded errors" | "we hid 184 mistakes in translations" |
| "fine-tuned an adapter" | "trained Meta's speech model… only 0.2 percent of it" |
| "blind back-translation" | "a second AI is translating the Quechua back" |
| "WER" | "word errors" |
| "100 % of critical errors" | "every dangerous one" |
| "Common Voice: 0.05 h validated" | "the biggest open dataset has three minutes of it" |

## De dónde sale cada número

| Número | Fuente |
|---|---|
| 9 de 10 pacientes | entrevista a la enfermera, 24-oct (`research/entrevistas/`) |
| 1 de 7 médicos | Bendezu-Quispe et al., 2020 (14,4 %, 84 de 584) |
| 3 minutos de quechua abierto | `ricardo-artifacts/reports/datasets-quechua.md` (Common Voice, Ayacucho, 0,05 h validadas) |
| 476 clips, 4 personas, 9,3 min, 0,2 % | `ricardo-artifacts/reports/ajuste-asr.md` («Cómo se entrenó»). ⚠️ El README dice 362 clips: el informe de Ricardo es la fuente |
| 54 % → 41 % | `ricardo-artifacts/reports/ajuste-asr.md` · commit `7b57a9b` |
| 184 / 99,5 % / todos los críticos | `evals/ataques/resultados/` · `docs/measured-results.pdf` |
| 21 de 22 | `evals/conversacion/` · `docs/measured-results.pdf` |
| «paracetamol 500 mg… ¿se lo digo?» | flujo de `/receta` probado con `caja_prueba.jpg` (loopmind-05) |
