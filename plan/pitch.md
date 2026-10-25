# Chaski · pitch playbook (v5, Sun Oct 25 01:05 PT)

> **We have 3:00 to pitch + 2:00 of questions** (Devpost 13.0, confirmed by the team). Built from what's in the repo
> and the research in `research/pitch-research.md` (every source there). Two inputs still change it: the interview
> with Freddy's mother (17:00 PT) and Ricardo's baseline numbers. **Never say a number on stage that isn't in §4.**

---

## 0 · Claims audit (v4, Sat 23:45) · every sentence in the script against the repo

| Claim on stage | Status | Evidence |
|---|---|---|
| Her quote, «professionals from the coast don't understand Quechua» | ✅ her words, on video, name allowed by Freddy | `plan/medios.md`, clip A |
| 90 % patients / ~20 % staff speak Quechua | ✅ | interview 24-oct |
| Interpreter is whoever is on shift, the driver, gestures, pill broken in 4 | ✅ verbatim | `research/entrevistas/…-insights.md` l.21–23 |
| 40 min vs an hour or more | ✅ | interview |
| 1 in 7 rural doctors with basic Quechua | ✅ 14.4 %, 84/584 | Bendezu-Quispe 2020 |
| Back-translated blind, code compares the facts | ✅ runs on every translated turn (the Sonnet critic IS the blind back-translation) | `app/chaski/critico.py`, `hechos.py`; loopmind-05 23:35 |
| Claude picks the reading from the context | ⚠️ built, **not measured**. Say it qualitatively, never with a number | `interprete.py` `<alternativas_asr>` |
| Emergency questions reviewed by a nurse from the community | ✅ 24/24 (14 approved, 10 written by her) | `evals/banco/revision_enfermera.json` |
| Play «instantly» | ✅ text and audio already stored, no model call | bank |
| The refusal names the fact | ✅ 16/16 blocked in real runs | §7 |
| WER 54 → 41 % on an unheard speaker | ✅ | `7b57a9b`, `evals/HISTORIA.md` §4 |
| 184 seeded errors, every critical one caught, «about three seconds» | ✅ 183/184, 100 % critical, p50 2.6 s / p95 3.4 s. **v3 said "under three seconds", which is false at p95** | `chaski-2026-10-24-1740.json` |
| Opus decides, Sonnet checks | ✅ D39 | SOT |
| "They still miss about four words in ten" | ✅ fine-tuned WER 40.9 % on the held-out speaker | `7b57a9b` · `evals/HISTORIA.md` §4 |
| "My mother wrote and reviewed these" | ✅ 14 approved as they were + 10 written by her | `evals/banco/revision_enfermera.json` |
| Nurse-trained voice, A/B/C, «she picked it blind» | 🔸 **not yet**. No `ciegas/` or `abc/` files in the repo at 23:45; out of the default script | `plan/HANDOFF-RICARDO-VOZ.md` |
| Summary + new words of the visit | ⚠️ screen built; **the summary on stage must be from the live consult**, not the `EJEMPLO` demo data in `movil/src/app/resumen.tsx` | app |
| «Monday, it goes to my mother's health center» | 🔸 **Freddy confirms**. She said she herself wouldn't need it; the users are the ~80 % who don't speak Quechua | interview l.91 |
| Translator = Claude Sonnet 5, medium effort | ✅ **decided D43 (Freddy 23:38)**. 0 of 92 fixed terms damaged (Gemini 3 Flash 4, NLLB 3); best at reading the patient (qu→es chrF++ 50.1 vs Gemini 3 Flash 43.7); whole turn p50 8.3 s, 19/20 said. ⚠️ **The live service still runs NLLB until Ricardo restarts it** (`plan/HANDOFF-RICARDO-SERVICIO.md`): check before rehearsal | `evals/traduccion/resultados/comparar-20261024-2324.json`, `…-2336.json` · `evals/latencia/resultados/configuraciones-20261024-2341-claude-medium.json` · SOT D43 |
| Nurse-reviewed examples improve translation (D41) | ✅ her 24 phrases as examples: es→qu 52.6 → 56.0, qu→es 49.1 → 56.0 on the families' 62 sentences; turn 20/20 said, p50 8.0 s. Lower on greetings from another variety (48.3 → 42.6): never say «improves everything» | `evals/HISTORIA.md` §2d · `evals/moat/resultados/` |
| About two cents per translated turn | ✅ $0.024 measured from real tokens (Opus + Sonnet translator + Sonnet critic), list prices not checked against the invoice. Say "about two cents" | `evals/latencia/resultados/costo-turno-20261024-2345.json` |
| NLLB fine-tuned 25.8 → 31.7 | ✗ **contaminated, never say it**: 58 of the 100 evaluation sentences leaked into training (Ricardo, `2fac55f`) | loopmind-05 23:45 |
| Never say | ✗ "the only Quechua-speaking nurse" · "2 % of centers have interpreters" · "a bad translation hurt someone at her post" (she remembers no case) · chrF "40 = decent, 60 = near-human" (no peer-reviewed source) · "turn in 6.5 s" | — |

**Before rehearsal, test once on the real phone:** the B2 instruction («…después de comer. No la tome con té.») must
pass **without a false block**. The critic holds back ~1 in 5 correct sentences. If it blocks, change the phrase,
not the critic.

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
| — | **Translation:** five translators on the families' 62 sentences, same set: fixed terms damaged in 92 translations → **Claude medium 0**, Gemini 3 Flash 4, NLLB 3. chrF++ es→qu Gemini 3.8 Flash 63.8 · Claude thinking 58.9 · Claude medium 51.4 · NLLB-1.3B 34.7. Claude medium translates (D43): safety first, and the turn stays at 8.3 s | `evals/traduccion/resultados/` | Q&A «why Claude, why not Gemini?» |
| ✗ | ~~"the only Quechua-speaking nurse"~~ (3 of 6 nurses do) · ~~"2% of centers have interpreters"~~ (doesn't exist) | — | never |

---

## 5 · Run of show (v5, Sun 01:05): demo by 0:25, one flow, one number

**Why v5.** Round-2 research (`research/pitch-research.md` §6). Last year's winner said who it was for in 18 s and spent
~85 % on ONE real flow, with no slides. Judges score a plain "tool for whom" opener, a live demo of ~90 s, one
before→after number, and **a limitation named by the team**. v4 started the demo at 0:45 after 35 s of numbers and ran
3:06 in the rehearsal video. v5 starts the demo at ~0:25, moves the numbers into the wait, and lands at ~2:50.

| t | Beat | Who | On screen / in the air | What it proves |
|---|---|---|---|---|
| 0:00 | **B1 Who it's for** | Freddy | Eye contact, one sentence | The declarative opener judges reward |
| 0:07 | **B1 Her voice** | — | Her clip, first 12.5 s (ends after «…they don't understand Quechua»), subtitled | The insider, the lived problem |
| 0:20 | **B2 Demo starts** | Freddy | Says the instruction to the phone; «Pensando» runs | One real flow, from here to B4 |
| 0:25 | **B2 The problem, during the wait** | Freddy | To the judge, while the steps run (~8 s) | 9 in 10 / 1 in 5 / the pill in four |
| 0:35 | **B3 Chaski speaks** | — | Quechua out loud + «Revisado por el crítico» | The payoff |
| 0:40 | **B3 How it checked** | Freddy | Point at the seal | Blind back-translation + code |
| 0:55 | **B3 The patient answers** | Ricardo plays the family clip | Spanish on screen (~4 s) | Both directions |
| 1:10 | **B3 Emergency** | Freddy | Two taps → instant | Verified bank, zero wait |
| 1:25 | **B4 The moment** | Freddy | Rehearsal shortcut → red, 1 s of silence | It refuses, and says why |
| 1:55 | **B5 How it's built + the limit** | Ricardo | ONE slide: **183 / 184** | Hard tech, honest limit, one number |
| 2:30 | **B6 Close** | Freddy | Summary of THIS consult | The outcome + the line |

## 6 · The script (v5, English, ~360 words, target 2:50)

> `[brackets]` = stage direction. Read it out loud with a timer; cut words, not beats. 🔸 = only if confirmed.

**B1 · Who it's for, then her (0:00–0:20) · Freddy**
"Chaski is a medical interpreter for the Andes. A nurse speaks Spanish, the patient hears Quechua, and it stays
silent rather than say a dose wrong. Here's why we built it." [Her clip, 12.5 s, subtitled.]

**B2 · The demo starts, the problem fills the wait (0:20–0:35) · Freddy**
"That's my mother, a nurse in Pilpichaca. Let me show you." [To the phone: «Tome una pastilla cada ocho horas, después
de comer. No la tome con té.» «Pensando» starts. Turn back to the judge.]
"Nine in ten of her patients speak Quechua. One in five of the staff do. When nobody can translate, she breaks a pill
into four in front of the patient, to show the dose."

**B3 · Chaski (0:35–1:25) · Freddy + Ricardo**
[Chaski speaks.] "Before it spoke, a second model translated the Quechua back without seeing my words, and code
compared the dose, the hours and the 'not with tea'." [Point at the seal.]
[Ricardo plays the patient.] "The patient answers in Quechua — and I read it in Spanish." [Spanish on screen.]
[Two taps: emergency.] "In an emergency there's no time for a model. My mother wrote and reviewed these, and they play
instantly."

**B4 · The moment (1:25–1:55) · Freddy**
"Now let's simulate the translator making a mistake." [Shortcut.] [Red. One second of silence.] "The Quechua lost its
'not' — it now says *take it with tea*. Chaski caught it, didn't say it, and tells me exactly which fact changed. In a
clinic, a confident wrong sentence is worse than silence."

**B5 · How it's built, and its limit (1:55–2:30) · Ricardo**
"There's almost no Chanka speech data, so our families recorded it this weekend and we fine-tuned Meta's models on it.
They still miss about four words in ten. That's exactly why Chaski refuses instead of guessing. Opus decides, Sonnet
checks. We seeded 184 errors — wrong doses, flipped negations, swapped medicines. It caught every critical one, in about
three seconds, and always says which fact failed."

**B6 · Close (2:30–2:50) · Freddy**
[Summary screen.] "At the end: a note for the clinical record, instructions the patient takes home, and the new Quechua
words from that visit. Anthropic says it wants Claude to work in languages left out of its training data. We built
that, we measured it, and 🔸 next it goes to my mother's health center." [Only if she said yes: "Monday".]

### What changed from v4, and why
| v4 | v5 | Source |
|---|---|---|
| 16 s of her clip opens cold | One "who it's for" sentence first, then 12.5 s of her | Kurbaitaev: "tool that does X for Y" |
| Demo at 0:45 | Demo at 0:20 | FaceTimeOS: demo at 0:18 |
| Numbers before the demo | Numbers told during the ~8 s wait | turns dead air into the problem |
| Two numbers on the slide | **One**: 183 / 184 (the word-error number only in Q&A) | research rule 4 |
| No limitation in the pitch | "They still miss about four words in ten. That's exactly why Chaski refuses" (40.9 % WER, `7b57a9b`) | Kurbaitaev: "admitting a limitation raised scores" |
| "These were reviewed by a nurse" | "My mother wrote and reviewed these" (14 approved + 10 written by her) | the insider, made concrete |
| 3:06 in rehearsal | ~2:50 | buffer for a slow turn |

### The 30-second version (and the one-liner for general judges)
"Chaski is a medical interpreter for the Andes: a nurse speaks Spanish, the patient hears Quechua. At my mother's health
center nine in ten patients speak Quechua and one in five staff do. And it would rather stay silent than say a dose
wrong: it caught every critical error we seeded. Want to see it?"

**One-liner:** *"An interpreter that would rather stay silent than be wrong."*

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
| Nurse turn | translated instruction ~8.0 s typical, 10.5 s p95 with D43 + D41 (17 s with the old thinking translator); question back or verified phrase ~4 s | Narrate over the «Pensando» steps (it's in the script). Confirm the live service runs D43, not NLLB |
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

## 9 · Q&A bank

Moved to **[`plan/qa-jueces.md`](qa-jueces.md)** (v1, Sat 23:55): one-breath answers centered on the technical
decisions and the measurements, with who answers and the file behind each number. One home, so the two can't drift.

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
