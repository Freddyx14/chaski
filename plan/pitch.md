# Chaski · pitch playbook (v3, Sat Oct 24 19:00 PT)

> **We have 3:00 to pitch + 2:00 of questions** (Devpost 13.0, confirmed by the team). Built from what's in the repo
> and the research in `research/pitch-research.md` (every source there). Two inputs still change it: the interview
> with Freddy's mother (17:00 PT) and Ricardo's baseline numbers. **Never say a number on stage that isn't in §4.**

---

## 1 · What the research taught us (the short version)

1. **Judges remember one thing per team.** Expo judges see ~10–30 tables and likely rank a personal top 3 (MLH's
   model). Being memorable beats being complete. Our one thing: *Chaski refuses to say a dose it isn't sure it translated right.*
2. **Every recent winner has the same five parts**: one named population · a lived/insider origin · one before→after
   number · something concrete the user walks away with · privacy and safety said out loud. (EldaAI, Claude prize
   12.0 · Expungo, social impact 12.0 · Peel, HackMIT 2026 · CrossBeam and TARA, Anthropic's own hackathon.)
3. **Show it working early.** Judges' advice: a working flow on screen within ~40–90 s, one flow, one "oh, this is
   possible now" moment. A feature tour loses.
4. **Honesty reads as confidence.** "Judges can tell when you're talking around a feature that doesn't exist yet."
   Say what's real, what's simulated, what doesn't work yet.
5. **Harden the demo, don't gamble.** Pre-load what can stall, cut what's flaky (the 12.0 winner removed a whole
   feature so the demo looked reliable), hotspot instead of venue Wi-Fi, recorded fallback that you *call* a recording.
6. **Domain insiders beat coders** at Anthropic's hackathons. Our insider is Freddy's mother, the nurse. Use her.
7. **Anthropic wrote our pitch for us.** Their 2026 Public Benefit Report: they're working so Claude "performs well in
   languages that are underrepresented in their training data", their standard is "make powerful AI affordable and
   usable in every language and format", and they admit "we have not been active enough in collecting data to measure
   the results." **Chaski is that sentence plus the measurement they say is missing.**
8. **The video is a second pitch.** Devpost requires it, and some sponsors judge only from it.
9. **Expect repeat visits** (12.0 had a final judging round; 13.0 hasn't said). Same quality on the 5th run.
10. **The prize is real now**: "[Anthropic] Claude for Public Benefit", 1 winner, $5,000 Claude credits + 1 year of Max 20x + office hours. Opt in on Devpost.

---

## 2 · The format

| | | |
|---|---|---|
| When / where | Sun 10:30–12:30 at our table (shared by 2–3 teams). Table number after 9:00 | guide |
| Time | **3:00 pitch + 2:00 Q&A** | Devpost |
| Demo | Live, required. Plus a Devpost video | guide · Devpost |
| Team | Both of us at the table the whole window or we're not judged | guide |

Three lengths of the same pitch: **30 s** (someone walking by, or a judge short on time) · **3:00** (default) ·
**2:00** cut (Cartesia's rubric asks for 2-min demo-first, and any judge who says "we're running late").

---

## 3 · What each judge needs to see

| Judge | Their criteria | What we show them | Where |
|---|---|---|---|
| **Anthropic** (our main target) | Named community · real problem you lived · works Monday · thoughtful Claude, knowing where it fails | Pilpichaca + Mom · Claude auditing itself and refusing · the failure modes, said by us before they ask · the report quote | B1, B4, B6 |
| **General** | Application · Intentionality · Functionality · Creativity · Technical complexity | The full two-way flow · the before→after chart · "every design choice has a reason" (why audit, why Chanka, why both roles) | B3–B5 |
| **Cartesia** (25% each) | Problem & originality · Use of Cartesia · Execution · Impact & responsibility | Demo-first order (§6). Cartesia is the Spanish ears and voice; Quechua is ours because Cartesia doesn't support it. README lists features used + limits | §6 |
| **Microsoft** | Customer understanding · measurable usefulness · path to production · responsible design · end-to-end | Mom's real case · what we log to measure impact · who adopts it on Monday | B6, Q&A |
| **People-First** | General criteria | Same as general | — |

**What impresses judges, in order of weight:**
1. **The refusal moment, live.** The only thing no other team has. It's Anthropic's criterion 4 made visible.
2. **A real before→after number on a voice the model never heard.** Turns "we fine-tuned" into evidence.
3. **The insider.** Mom's voice or quote. Turns "a problem" into "her problem".
4. **Both sides of the conversation work**: nurse in Spanish, patient in Quechua, each gets something on screen.
5. **The take-home summary**: a concrete artifact the patient keeps (winners' pattern #4).
6. **Saying the limits first.** Offline doesn't work yet, the Quechua UI was reviewed by one native speaker, etc.

---

## 4 · Numbers we're allowed to say (all from files)

**On stage, three numbers max:** ★ (the problem), ★★ (the ears got better), ★★★ (it never lets a dose error through).

| # | Number | Source | Where |
|---|---|---|---|
| **★** | At her health center **90% of patients speak Quechua; ~20% of the 36 staff do**, not fluently | Interview 24-oct (insights in `research/entrevistas/`) | B1 |
| ★s | Not an exception: **only 1 in 7 doctors starting SERUMS (the rural year) has even basic Quechua or Aymara** (14.4%, 84/584) | Bendezu-Quispe 2020 · `research/personal-salud-quechua.md` | B2 / Q&A |
| ★c | Consultation **30–40 min in Spanish, an hour or more in Quechua**; instructions repeated up to 4× | Interview | B2 |
| **★★** | **Ears fine-tuned on our families' voices: word errors 54% → 41%; perfectly understood sentences 30 → 51 of 175**, on a speaker the model never heard | commit `7b57a9b` · `evals/HISTORIA.md` §4 | B5 |
| **★★★** | **Every dose, day, negation, medicine, unit and "taken with" error caught: 183 of 184 seeded errors**, critic in 2.6 s, $0.008 per turn | `evals/ataques/resultados/chaski-2026-10-24-1740.json` | B4 / B5 |
| — | Asking Claude "is this right?" also catches them but **can't say why**, and held back 1 in 4 correct sentences (Sonnet) to 7 in 10 (Haiku) | `juez_claude-…-1644.json`, `…-1459.json` | Q&A |
| — | Interpreter picks the right action **98–100% (Opus), zero invented clinical data** | `evals/interprete/resultados/` | Q&A |
| — | Verified-phrase RAG finds the right phrase first **88%** (keyword search 70%) | `evals/banco/` | Q&A |
| — | **All 24 emergency phrases reviewed by a nurse from the community** | `evals/banco/revision_enfermera.json` | B3 / Q&A |
| — | **Voice:** judged by human ears, not by a recognizer — a patient hears it, not a machine (Freddy, 20:45). Claim «sounds like her» (audible in the A/B/C); claim «a native speaker understands it» only after her blind test | `evals/HISTORIA.md` §4 | B5 |
| — | **Translation:** we fine-tuned NLLB-200 (chrF++ 25.8 → 31.7) and it still lost to Claude (42.3), so Claude translates — decided by measurement | `bf4a788` | Q&A «why not your own translator?» |
| ✗ | ~~"the only Quechua-speaking nurse"~~ (3 of 6 nurses do) · ~~"2% of centers have interpreters"~~ (doesn't exist) | — | never |

---

## 5 · Run of show: every beat, its asset, its feature

| t | Beat | Who | On screen / in the air | Feature shown | Asset |
|---|---|---|---|---|---|
| 0:00 | **B1 Her voice** | Freddy | Play her saying the problem herself (14 s), subtitled on the laptop | — (the community) | `data/mama/video/clips/PITCH-B1_problema-profesionales-costa_16s.mp4` (respaldo: `data/mama/audio/clips/RESPALDO-PITCH-B1_problema-profesionales_14s.mp3`) |
| 0:20 | **B2 The problem** | Freddy | Nothing, eye contact | — | ★ ★c ★s |
| 0:45 | **B3a Two-way consult** | Freddy + Ricardo | Phone: nurse speaks Spanish → «Pensando» steps → Quechua out loud; patient clip → Spanish on screen | Polish (Wispr-style), translation, language ID, fine-tuned ears | Patient clip from the family set |
| 1:15 | **B3b Emergency mode** | Freddy | Two taps: «¿Dónde le duele?» → plays instantly **in the nurse-trained voice** | Verified phrase bank (RAG), zero wait | 24 reviewed phrases (`entregables/voz/emergencia/` when ready) |
| 1:30 | **B4 The refusal** | Freddy | «Simulamos un error del traductor»: «Tómela con agua, no con té» loses its «no» → red block naming the fact | Code guards + critic | Rehearsal shortcut `FRASE_NEGATIVA_DEMO` |
| 2:00 | **B5 How it's built** | Ricardo | Laptop: one slide with ★★ and ★★★, then the **A/B/C voice** (Meta → Chaski → her) | Fine-tuning, critic, measured | `entregables/voz/abc/` |
| 2:35 | **B6 Close** | Freddy | Phone: summary for nurse + take-home for patient + new Quechua words | Summary, glossary (learn Quechua) | — |

## 6 · The 3:00 script (English, ~440 words)

> `[brackets]` = stage direction. Read it out loud with a timer; cut words, not beats.

**B1 · Her voice (0:00–0:20) · Freddy**
[Play her, 14 s, subtitles on the laptop: «…a veces los profesionales no entienden el quechua; entonces yo ayudo,
hago la traducción».]
"That's my mother. She's a nurse in Pilpichaca, high in the Andes of Huancavelica, and she just told you the problem:
the doctors don't understand Quechua, so she translates. Nine out of ten of her patients speak Quechua. About one in
five of the staff do. When she's not on shift, nobody translates."

**B2 · The problem (0:20–0:45) · Freddy**
"So the interpreter is whoever is around — another nurse, a technician, the ambulance driver. If nobody is, they use
gestures, and break a pill into four in front of the patient to show the dose. A visit that takes forty minutes in
Spanish takes an hour in Quechua. And her center isn't an exception: only one in seven doctors sent to rural Peru
speaks even basic Quechua."

**B3 · Chaski (0:45–1:30) · Freddy + Ricardo**
"This is Chaski." [Phone to the judge.] [Freddy: «Tome una pastilla cada ocho horas, después de comer.»]
"It cleans up what I meant, translates it, then translates it back blind to check nothing changed — and only then
speaks." [Chaski speaks Quechua.] [Ricardo plays the patient's answer.] "The patient answers in Quechua; our
fine-tuned ears transcribe it, Claude fixes it with the context of the visit, and I read it in Spanish."
[Two taps: emergency mode.] "In an emergency there's no time to wait for a model: these questions were reviewed by a
nurse from the community and play instantly — in a nurse's voice [only if her blind test says the trained voice is understood; otherwise Meta's voice]."

**B4 · The moment (1:30–2:00) · Freddy**
"Now let's simulate the translator making a mistake." [Rehearsal shortcut.] [Red.] "The Quechua lost its 'not' — it
now says *take it with tea*. Chaski caught it, didn't say it, and tells me exactly what didn't match. In a clinic, a
confident wrong sentence is worse than silence."

**B5 · How it's built (2:00–2:35) · Ricardo**
"Meta's open models are the ears and the mouth, and there's almost no Chanka data in the world — so our families
recorded it this weekend. On a voice the model never heard, word errors dropped from 54 to 41 percent. And listen:"
[A/B/C, 10 s — only if her blind test passes.] "That's Meta's voice, Chaski's voice trained with her permission, and her. A nurse from the community picked it in a blind test [only if she did]. Claude is the brain: Opus
interprets, Sonnet checks. We seeded 184 errors — wrong doses, flipped negations, swapped medicines. Chaski caught
every critical one, in under three seconds, and always names what failed."

**B6 · Close (2:35–3:00) · Freddy**
[Summary screen.] "At the end, a clinical note for the nurse, instructions to take home for the patient — and the new
Quechua words from that visit, so the staff learn one patient at a time. Anthropic says it wants Claude to work in
languages left out of its training data. We built that, and we measured it. Monday, it goes to my mother's health center."

### The 30-second version
"At my mother's health center in the Peruvian Andes, nine in ten patients speak Quechua and one in five staff do.
Chaski is the interpreter for when nobody is there — and it would rather stay quiet than say a wrong dose: it caught
every dose and negation error we threw at it. Want to see it?"

### The 2:00 demo-first cut (Cartesia, or a judge in a hurry)
B3 (45 s) → B4 (25 s) → B1 line + ★ (15 s) → "Cartesia is the Spanish side: it transcribed 3.5 s of the nurse in
480 ms, and speaks to her. It doesn't support Quechua, so that side is our own fine-tuned model." (15 s) → close (10 s).

---

## 7 · The demo, hardened

**At the table:** iPhone with Chaski (TestFlight) on a stand facing the judge · laptop with ONE slide (★★, ★★★) and the
A/B/C audio + the Devpost video ready · **phone hotspot, not venue Wi-Fi** · a second phone with the patient clip ·
small speaker for the audios · chargers. **Before each judge:** one warm-up turn so the models are hot.

| Step | Risk | Mitigation |
|---|---|---|
| Nurse turn | ~6.5 s typical, ~10 s worst | Narrate over the «Pensando» steps (it's in the script) |
| Patient answer | Loud hall | Pre-recorded family clip played next to the mic |
| Emergency mode | Needs the nurse-voice audio | Until `entregables/voz/emergencia/` exists, the app shows the reviewed Quechua text big; say it's verified |
| The refusal | Must happen every time | `FRASE_NEGATIVA_DEMO` blocked 16/16 in real runs; say out loud it's a simulated error |
| A/B/C | Audio too quiet in the hall | Speaker, files pre-normalized to −16 LUFS |
| Anything breaks | — | One sentence — "the connection dropped, here's the recording from this morning" — then the video |

**Judging is 10:30–12:30 PT = 12:30–14:30 Lima.** If she can join a video call, it's a bonus, not the plan.

---

## 8 · The Devpost video (≈ 2:30, some sponsors only see this)

| t | Image | Audio |
|---|---|---|
| 0:00 | Black → Pilpichaca / Andes stills | Her presentation, 25 s: `clips/final-presentacion-25s.mp3` («¿Están bien, hermanas? Les hablo yo, la enfermera… trabajo en Huancavelica, zona sanitaria de Pilpichaca»), subtitled; cut to 12 s if long |
| 0:12 | Same | The problem in her words, 14 s: `clips/final-problema-profesionales-14s.mp3` |
| 0:12 | Title: *Chaski* · «90% of patients speak Quechua. ~20% of staff do.» | — |
| 0:20 | **The refusal**, screen recording | Freddy narrating (opens on «the moment», as winners do) |
| 0:45 | Two-way consult + emergency mode | App audio |
| 1:20 | A/B/C voice + the two numbers | Ricardo |
| 1:35 | Who she cares for | `clips/final-ninos-adultos-gestantes-emergencias-22s.mp3` («atiendo a los niños, a los adultos, a las gestantes, y en las emergencias ayudo cuando no hablan castellano»), 10 s of it |
| 1:50 | Her welcoming a patient, subtitled | `clips/atencion-casa-de-salud-29s.mp3`: «Aquí, conmigo, va a estar bien… dígame con confianza… siéntese aquí, como en su casa» |
| 2:15 | «That's what care sounds like in your own language. Chaski is for when nobody there speaks it.» | — |

Subtitles: confirm the [?] words with her first (`data/mama/traduccion-claude.md`; «Kati» is the patient's name).

---

## 9 · Q&A bank (both of us know these cold)

| Question | One-breath answer |
|---|---|
| How do you know the Quechua is right? | Blind back-translation + a code check of drug, dose, frequency, negation and what it's taken with. And a nurse from the community reviewed all 24 emergency phrases |
| What happens when it's wrong? | It stays quiet and tells the nurse which fact failed. 183/184 seeded errors caught, 100% of the critical ones |
| Why not just ask Claude "is it right?" | We measured it: it catches errors too, but can't say why, and held back 1 in 4 correct sentences |
| Why Opus and Sonnet, not Haiku? | Measured: Opus 98–100% right action, zero invented data. As critic Sonnet caught everything; Haiku let invented diagnoses through. Anthropic suggested Haiku for speed — we made Sonnet fast instead (9 s → 2.6 s) |
| How do you know the fine-tuning helped? | A speaker the model never heard, same script before and after: 54% → 41% word errors, 30 → 51 perfect sentences |
| Is her voice a deepfake? | It's trained with her permission, we always say so, and it only speaks phrases a nurse verified |
| Privacy? | Consultation audio isn't stored; family recordings were donated with consent and never go in the repo |
| Is her center typical? | It's not an exception: only 1 in 7 doctors starting rural service has even basic Quechua |
| Replacing interpreters? | There's one certified bilingual public servant per ~4,000 Quechua speakers in Huancavelica. It's for when nobody is there |
| Who uses it Monday? | The staff at Pilpichaca who don't speak Quechua (~80% of 36); the health zone has 10 more posts |
| How do you measure impact? | MINSA's daily HIS form already records each patient's language: count Quechua visits and their length; plus our own log of blocks and repeats |
| Offline? | Not yet. Honest limitation; on-device models are next |
| Why Chanka? | It's Huancavelica and Ayacucho's Quechua; models are trained on Cusco's. We found no paper evaluating LLMs on Chanka |

---

## 10 · Assets checklist (what must exist before 22:00)

| Asset | State |
|---|---|
| Her greeting clip (7 s) and presentation (12 s) | ✅ `data/mama/clips/` |
| Her welcoming-a-patient clip (29 s) + confirmed subtitles | ✅ clip · ⏳ subtitles (questions sent to her) |
| Emergency phrases reviewed | ✅ 24/24 |
| Emergency phrases in the nurse-trained voice | ⏳ Ricardo (`plan/HANDOFF-RICARDO-VOZ.md`) |
| A/B/C voice clips | ⏳ Ricardo |
| Refusal shortcut in the app | ✅ ui-ux |
| One slide with ★★ and ★★★ | ⬜ |
| Devpost video | ⬜ Sun 05:00 |
| Ricardo's service running the interpreter (`app/chaski/PARA_RICARDO.md`) | ⬜ |


## 11 · Todos los audios de la mamá y qué dice cada uno (transcritos con MMS de Meta, traducidos con Claude)

Ella eligió el último (20:32) como el mejor. Archivos en `data/mama/` (no van a git); traducciones en
`data/mama/traduccion-claude.md` y `transcripcion-final-traduccion.md`.

| Clip | Dura | Qué dice | Uso |
|---|---|---|---|
| `final-problema-profesionales-14s` | 14 s | «A veces los profesionales no entienden el quechua; entonces yo ayudo, hago la traducción» | **Abre el pitch (B1)** y el video |
| `final-presentacion-25s` | 25 s | «¿Están bien, hermanas? Les hablo yo, la enfermera… trabajo en Huancavelica, zona sanitaria de Pilpichaca» | Abre el video |
| `final-yo-traduzco-25s` | 25 s | «Ayudo trabajando: cuando no hablan castellano, yo hablo quechua, y así me entienden los pacientes» | Video, respaldo |
| `final-ninos-adultos-gestantes-emergencias-22s` | 22 s | «Atiendo a los niños, a los adultos, a las gestantes; en las emergencias ayudo cuando no hablan castellano» | Video |
| `final-saludo-a-eeuu-13s` | 13 s | «Saludo desde Huancavelica, Perú, hasta Estados Unidos» | Cierre del video |
| `atencion-casa-de-salud-29s` | 29 s | Recibiendo a una paciente (Kati): «aquí, conmigo, va a estar bien… dígame con confianza… siéntese como en su casa» | Momento emocional del video |
| Audios 19:57 y 19:59 | 90 s · 108 s | «Hablar quechua es difícil para mí, pero aprendí para ayudar a las mujeres que no hablan castellano» · «aquí los profesionales no hablan runa simi; para mí es bueno hablarlo porque ayudo cuando hay enfermedad o emergencias» | Respaldo; citas para Q&A |

**Su nombre:** en los audios se presenta con nombre y apellido. En pantalla y subtítulos usar «enfermera de Pilpichaca»
salvo que Freddy y ella decidan mostrar su nombre.


## 12 · Video de la enfermera (pedido 19:00) y el reparto de los 3 minutos

Freddy le pidió a su mamá grabar en **video horizontal** lo mismo que dijo en los audios, en 5 tomas cortas (guion
enviado por WhatsApp): 1 saludo y quién es · **2 el problema** · 3 a quiénes atiende · 4 recibiendo a una paciente ·
5 despedida. Subtítulos en inglés. **Puede salir su nombre** (Freddy, 18:59).

**El pitch tiene 3:00 y ella ocupa solo 12–15 s** (la toma 2, el problema). El resto de sus tomas va al video de Devpost.

| Bloque | Tiempo | Qué | De ella |
|---|---|---|---|
| B1 | 0:00–0:15 | **Toma 2 en video** (o el audio de 14 s si el video no llega), subtitulado | ✅ 12–15 s |
| B1→B2 | 0:15–0:45 | Freddy: «Esa es mi mamá…», ★, ★c, ★s | — |
| B3 | 0:45–1:30 | Consulta en los dos sentidos + modo emergencia con la voz entrenada con la suya | su voz (B) |
| B4 | 1:30–2:00 | La negativa simulada | — |
| B5 | 2:00–2:35 | Ricardo: ★★, A/B/C de voz, ★★★ | 3 s de su voz real en el A/B/C |
| B6 | 2:35–3:00 | Resumen y palabras nuevas; cierre | — |

**Video de Devpost (~2:30):** toma 1 → toma 2 → negativa → consulta y emergencia → A/B/C → toma 3 → toma 4 → toma 5.


## 13 · Los videos de la enfermera (llegaron 20:50) · cortes y subtítulos

3 videos horizontales (1024×576), uniforme turquesa (el color de Chaski). Transcritos con MMS de Meta en ventanas de 5 s
y traducidos con Claude. Clips en `data/mama/video/clips/` (no van a git), cada uno con su `.en.srt`; texto completo en
`clips/subtitulos.md`. Ella dice su nombre: **Lic. Norma Choque Guerreros** (Freddy autorizó mostrarlo).

| Clip | Dura | Qué dice (castellano) | Uso |
|---|---|---|---|
| **`A-problema-costa-16s`** | 16 s | «Muchas veces vienen aquí a trabajar profesionales de la costa, y ellos no entienden el quechua» | **Abre el pitch (B1)** |
| `A3-problema-yo-traduzco-21s` | 21 s | «…cuando vienen los profesionales de la costa no hablan quechua; cuando no entienden, yo lo soluciono, yo traduzco» | Video Devpost (más completo que A) |
| `A2-problema-alt-16s` | 16 s | Otra toma del problema | Respaldo |
| `B-presentacion-16s` | 16 s | «Soy la licenciada Norma Choque Guerreros, enfermera de Huancavelica… zona sanitaria de Pilpichaca… hablo quechua, runa simi» | Abre el video Devpost |
| `C-atiende-ninos-emergencias-16s` | 16 s | «Atiendo a los niños, las enfermedades, las emergencias, porque esta población habla quechua» | Video |
| `C2-medicamentos-traduzco-16s` | 16 s | «…cómo lo deben tomar o administrar, qué deben tomar… eso lo ayudo traduciendo» | Video, junto a la función **receta** |
| `D-confianza-pacientes-31s` | 31 s | «Los pacientes me dicen: ayúdame, interprétame… la enfermera sabe quechua, vamos a consultarle… me alegro cuando me dan su confianza» | Momento emocional del video |
| `E-saludo-eeuu-14s` | 14 s | «Me alegra hablar quechua. Mando un saludo desde Huancavelica, Perú, al pueblo de Estados Unidos. Muchas gracias» | Cierre del video |

**Pitch (3:00):** solo `A-problema-costa-16s` en B1, con subtítulos en inglés. Si el video falla en la sala, el audio
`data/mama/video/clips/PITCH-B1_problema-profesionales-costa_16s.mp4` (respaldo: `data/mama/audio/clips/RESPALDO-PITCH-B1_problema-profesionales_14s.mp3`).

**Video Devpost (~2:30):** B (presentación) → A3 (el problema) → negativa → consulta + emergencia → C2 junto a la receta
→ A/B/C de voz → D (confianza) → E (saludo). Los subtítulos se queman con PIL (esta Mac no tiene libass).
