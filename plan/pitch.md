# Chaski · pitch playbook (draft 2, Sat Oct 24 11:50 PT)

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

## 4 · Numbers we're allowed to say

**Lead with ★. Say at most two numbers in the 3:00.** The rest live in Q&A.

| # | Number | Source | Use |
|---|---|---|---|
| **★** | **At her health center, 90% of patients speak Quechua. About 20% of the 36 staff do**, and not fluently | Interview with the nurse, 24-Oct (`research/entrevistas/2026-10-24-enfermera-pilpichaca.md`): «el 90% hablan quechua» · «será el 20%. De todo el personal» | **B2, the lead.** First-hand, from our named community |
| ★s | **Only one in seven doctors starting SERUMS (the rural service year) reports even basic Quechua or Aymara** (14.4%, 84 of 584) — so her center's ~20% isn't an exception | Bendezu-Quispe et al., Rev Peru Med Exp Salud Publica 2020;37(4), 2016 survey · `research/personal-salud-quechua.md` | B2 or Q&A «is her center typical?» |
| ★b | Huancavelica: ~206,000 people with Quechua as first language, 52 certified bilingual public servants in the whole region. One per ~4,000 | Census 2017 via UNICEF · El Peruano 16-Jul-2026 · our division (`research/problemas-lenguas-originarias.md`) | Q&A "is it just one clinic?" |
| ★c | **A consultation in Spanish takes 30–40 min; in Quechua, up to an hour or more.** Instructions get repeated up to 4 times | Interview: «un paciente normal, 30 a 40 minutos … será por una hora hasta un poco más» · «Repetirlo 2, 3 veces, hasta 4 veces» | B2 or Q&A. Our measurable "before" for Microsoft |
| ★★ | **Before → after**: Meta's speech model on Chanka, error rate X% → Y% on a speaker it never heard | Ricardo's frozen baseline. **Smoke test today: WER 38.5%, CER 10.7%** (small set, not the baseline) | B5. If Ricardo's number isn't ready, say the smoke test as "before" and *don't* claim an after |
| 2 | ~~Mom is the only Quechua-speaking nurse~~ **Wrong.** She said 3 of the 6 nurses speak Quechua. Today the translator is whoever is on shift: a nurse, a technician, **the driver**, or a relative. Otherwise signs and drawings. Nobody there knew the government's 1812 interpreter line | Interview: «hay 3 enfermeras que hablan quechua» · «Acá también habla el chofer» · «es como una persona muda» · «nunca lo hemos usado» | B1/B2 |
| 3 | GPT-4 on real ER discharge instructions: at least one error in 16% (Spanish), 24% (Chinese), **56% (Russian)** of sets; worse as the language gets rarer | Kong et al. 2026, *BMJ Quality & Safety* | B2 or Q&A |
| 4 | 3.7 M Peruvians have Quechua as first language (13.9%) | Census 2017 | Q&A "is it big?" |
| 5 | Clinicians already fight this by hand with back-translation, pre-translated phrases and teach-back | Mehandru et al. 2022, FAccT | Q&A "why this design?" |
| ✗ | ~~"2% of centers have interpreters"~~ — doesn't exist. The real figure is 126 of 8,441 facilities (1%) with intercultural **childbirth** adaptation | Salud con Lupa, Feb 2025 | Only if asked about childbirth |

---

## 5 · The 3:00 script (draft, English, ~430 words ≈ 3:00 at a calm pace)

> `[brackets]` = stage direction or something we still need. Times are cumulative.

**B1 · Hook (0:00–0:20) · Freddy**
[Play Mom's recorded greeting in Quechua, 4 s — or Freddy says it.]
"That's my mother. She's a nurse at the health center in Pilpichaca, in the Andes of Huancavelica, Peru. Nine out of
ten of her patients speak Quechua. Only about one in five of the staff do. Most of them come from the coast."

**B2 · Problem (0:20–0:45) · Freddy**
"So today the interpreter is whoever is around. Another nurse, a technician, the ambulance driver. If nobody is, they
use gestures and drawings. My mother told me they break a pill into four in front of the patient to show the dose.
A consultation that takes forty minutes in Spanish takes an hour or more in Quechua. And 'just use ChatGPT' isn't
safe: even in Russian, it got discharge instructions wrong more than half the time. Quechua barely exists in its training data."

**B3 · Demo, the flow (0:45–1:35) · Freddy + Ricardo**
"This is Chaski." [Phone toward the judge. Chaski the vicuña waves.] "The nurse speaks Spanish."
[Freddy: *"Tome una pastilla cada ocho horas, después de comer."* While Chaski thinks:] "Right now Claude is
cleaning up what she meant, translating it, and then translating it *back* without seeing the original, to check
nothing changed." [Chaski speaks Quechua.]
"Now the patient answers in Quechua." [Ricardo plays the family clip.] "Chaski detects it's Quechua, our fine-tuned
model transcribes it, Claude corrects the transcript with the context of the consultation, and the nurse reads it in Spanish."

**B4 · The moment (1:35–2:05) · Freddy**
"Now let's simulate the translator making a mistake." [Rehearsal shortcut: «Tómela con agua, no con té», with the
Quechua «no» removed. Say out loud that it is simulated.] [Red block on screen.]
"The Quechua lost the 'not'. Now it says 'take it with tea'. Chaski caught it before speaking, and tells the nurse
exactly what didn't match. In a clinic, a confident wrong answer is worse than no answer. Chaski would rather stay quiet."

**B5 · How it's built (2:05–2:35) · Ricardo**
"Meta's open speech models are the ears and the mouth; we're fine-tuning them on [N] phrases our families recorded
yesterday [X% → Y% on a voice it never heard — ONLY if Ricardo's results file shows it; otherwise: 'we measured the
baseline and the fine-tune is running']. Claude is the brain: Opus interprets, Sonnet checks. We seeded 165 errors —
wrong doses, flipped negations, swapped medicines. Just asking Claude 'is this right?' catches them too, but can't tell you why it blocked. Chaski caught every dose,
negation and medicine error — 183 of 184 in total — in under three seconds, and always names what failed."

**B6 · Close (2:35–3:00) · Freddy**
[Show the summary screen.] "At the end the nurse gets a clinical note and the patient gets instructions to take home,
in their language, plus the new Quechua words from that visit, so the staff learn the language one patient at a time.
It works for both sides — a nurse or a patient can open it. Anthropic says it wants Claude to work
in languages left out of its training data, and admits it hasn't measured whether that's happening. We built that, and
we measured it. Monday, it goes to my mother's health post."

### The 30-second version
"At my mother's health center in the Peruvian Andes, nine in ten patients speak Quechua and one in five staff do.
Chaski is the interpreter for when nobody is there: the nurse speaks Spanish, the patient hears Quechua, and back. Claude checks every
translation by translating it back blind — and if a dose doesn't match, Chaski refuses to say it. Want to see it?"

---

## 6 · The 2:00 demo-first cut (Cartesia, or a judge in a hurry)

B3 (50 s) → B4 (25 s) → B2 in two sentences (15 s) → **for Cartesia:** "Cartesia is the Spanish side: it hears the
nurse in under half a second [`/escuchar` 0.46 s, measured] and speaks to her [verify Sonic is wired before saying
it]. It doesn't support Quechua, so that side is our own fine-tuned model." (15 s) → one limitation (10 s) → close (5 s).

---

## 7 · The demo, hardened

**At the table:** iPhone with Chaski (TestFlight) on a stand facing the judge · laptop with the before→after chart and
the demo video loaded · **phone hotspot, not venue Wi-Fi** · second phone with the Quechua patient clip · chargers.
**Before each judge:** one warm-up turn so the models are hot.

| Step | Risk | Mitigation |
|---|---|---|
| Nurse turn | **Takes ~15 s today.** Dead air | Narrate over Chaski's "thinking" steps (it's in the script). Push the fast path: measure Haiku/Sonnet for this turn (D15) |
| Patient answer | Loud hall, live mic | Pre-recorded family clip played next to the mic. Language detection already measured at 1.0 on Quechua |
| The refusal | Has to happen every time | Pick the sentence in rehearsal, confirm it blocks **5/5** |
| Summary | `/resumen` is live now (commit f0b752a) | Test it in the 10:15 warm-up |
| Anything breaks | — | One sentence: "the connection dropped, here's the recording from this morning", then the video. Never more than one sentence of apology |

**Mom live (D18):** judging 10:30–12:30 PT = 12:30–14:30 Lima. A live video call in a loud hall is risky. Record her
greeting + one sentence about her work at the 17:00 call, with her consent. If she can join live, it's a bonus.

---

## 8 · Q&A bank (both of us know these cold)

| Question | One-breath answer |
|---|---|
| How do you know the Quechua is right? | Blind back-translation + a code check of drug, dose and frequency. And a native nurse reviewed the glossary and the screens |
| What happens when it's wrong? | It refuses and tells the nurse which part failed. Show it. 183/184 seeded errors caught, 100% of critical ones, 20% of correct sentences held back (half are weak family translations), critic 2.6 s (`evals/ataques/resultados/chaski-2026-10-24-1740.json`) |
| Why Opus and Sonnet, not Haiku? | We measured: Opus picked the right action 98% with zero invented clinical data (Haiku 88%, Sonnet 94%). As critic, Sonnet caught 160/160 vs Haiku 96% with 18% false blocks. Anthropic suggested Haiku for speed; the numbers decided |
| What if a bank phrase is wrong? | A phrase is only spoken after a native nurse reviews it. Today the reviewed set is [N]; the rest show as pending |
| Where does Claude fail here? | It can sound fluent in Quechua and be wrong. So it never speaks unchecked and never fills in a dose |
| Why not Google Translate / ChatGPT? | Errors grow as the language gets rarer (Kong 2026), and neither tells you when it's wrong |
| What does Claude do that plain MT can't? | Corrects the speech transcript with the consultation's context, audits itself, judges whether the patient understood, writes the summary |
| How do you know it improved? | A frozen test speaker the model never heard, same script before and after |
| Privacy / consent? | Recordings are from consenting family volunteers, no patient data. [Decide and say only what's true: are consultation audios stored?] |
| Replacing interpreters? | There's one per ~4,000 people. It's for when nobody is there. The government's 1812 hotline needs staff to call and wait |
| Who uses it Monday? How does it scale? | The staff who don't speak Quechua at the Pilpichaca health center (≈80% of 36). The same health zone covers 10 more posts. Then the regional health office (DIRESA Huancavelica) |
| How would you measure impact there? | MINSA's daily HIS form already records each patient's language. So we can count Quechua consultations and compare their length (today 30–40 min vs up to an hour+) and how often instructions get repeated |
| Has a bad translation hurt someone there? | Honest answer: she couldn't recall one. They avoid it by repeating 3–4 times and taking an hour. The cost today is time and dignity; the risk with AI is Kong 2026 |
| How do you measure impact? | We log blocked translations, nurse corrections and repeat requests per consultation. [Confirm with the ui-ux session what the app logs] |
| Offline? | Not yet, needs signal. Honest limitation, on-device is next |
| Why Chanka? | It's Huancavelica and Ayacucho's Quechua; models are trained on Cusco Quechua. We found no paper evaluating LLMs on Chanka |
| What did you build in 36 h? | iOS app · the audit · a GPU voice service · a data site the families used · fine-tuning + evaluation |

---

## 9 · What we still need (owner · by when)

| Item | Owner | By |
|---|---|---|
| Frozen baseline + fine-tuned numbers (X, Y, N) | Ricardo | 19:00 |
| A dose sentence that blocks 5/5 | Freddy + ui-ux session | 15:00 |
| Nurse turn under ~5 s, or rehearsed narration | ui-ux session + Ricardo (D15) | 16:00 |
| `/resumen` and `/idioma` live | Ricardo | 18:00 |
| ~~Mom's interview~~ done 12:00 (`research/entrevistas/`). Still missing: her recorded greeting, with consent | Freddy | 18:00 |
| Agree with Ricardo which "agentic interpreter" features go in (`plan/propuesta-interprete-agente.md`) | Freddy + Ricardo | 14:00 |
| Decide: are consultation audios stored? | Freddy | 18:00 |
| Opt into Anthropic, People-First, Microsoft, Cartesia on Devpost | Freddy | 21:00 draft |
| README: where Claude is used and why · Cartesia features · known limits · no keys | ui-ux session | 21:00 |
| Rehearse 30 s / 3:00 / 2:00 with a timer, out loud, 3× each | Both | 22:00 |
| Demo video, opening on the refusal moment | Freddy | Sun 05:00 |
