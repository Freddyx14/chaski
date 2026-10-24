# Chaski · pitch strategy (draft 1, Sat Oct 24 11:10 PT)

> Draft built from what we already have in the repo. Two inputs will change it: the interview with Freddy's mother
> (17:00 PT) and Ricardo's baseline numbers. Web research on winning pitches lands in `research/pitch-research.md`
> and gets folded in. **Every number below has its source next to it. Never say one on stage that isn't here.**

## 1 · The format we're pitching into (verified)

| | What | Source |
|---|---|---|
| Where | Expo. Judges walk to our table, 10:30–12:30 Sunday. Table shared by 2–3 teams | hacker guide p.7 |
| Length | Guide: **"prepare a two-minute pitch"**. Devpost: 3 min pitch + 2 min Q&A | guide p.7 · `research/tracks.md` |
| Demo | **Live demo is required** to judge functionality | guide p.7 |
| Team | **Both of us at the table the whole window**, or we aren't judged | guide p.7 |
| Many visits | Different judges per track come separately (general, Anthropic, Cartesia, Microsoft). Same pitch, different emphasis | — |

**So we build three lengths of the same pitch:** a **30 s** hook for anyone walking by, the **2:00 core** (default),
and a **3:00** version when a judge clearly has time. Q&A is where the technical depth lives.

## 2 · What each judge is scoring, and where in the pitch we hit it

| Judge | Criteria (verbatim headings) | Beat that answers it |
|---|---|---|
| **Anthropic** · Claude for Public Benefit | Named community · real problem you lived · works on Monday · thoughtful Claude, knowing where it fails | Pilpichaca health post + Mom (B1) · the refusal moment (B4) · failure modes (Q&A) |
| **General Cal Hacks** | Application · Intentionality · Functionality · Creativity · Technical complexity | Demo (B3–B4) · baseline → fine-tuned chart (B5) |
| **Cartesia** (25% each) | Problem & originality · Use of Cartesia · Execution · Impact & responsibility. Wants **"2-minute, demo-first: one complete user flow, then a brief problem + how you built it"** | Run the **demo-first variant** (§6) for them. Say plainly: Cartesia is the Spanish voice and ears; Quechua is ours because Cartesia doesn't support it |
| **Microsoft** · Built for the Real World | Customer understanding · measurable usefulness · path to production · responsible design · end-to-end | Mom's quotes · baseline numbers · "1812 hotline + MINSA" path (Q&A) |
| **People-First Social Impact** | General criteria | Same as general |

## 3 · The numbers (pick ONE to lead with)

**Correction first:** the stat you remembered isn't about interpreters. It's **126 of 8,441 health facilities (1%)
have intercultural childbirth adaptation** (Salud con Lupa, Feb 2025). True but narrow (childbirth only), so it's a
backup, not the lead.

| # | Number | Source (in `research/problemas-lenguas-originarias.md`) | Use |
|---|---|---|---|
| **★** | **Huancavelica: ~206,000 people whose first language is Quechua · 52 certified bilingual public servants in the whole region. One for every ~4,000 people.** | Census 2017 via UNICEF · El Peruano, 16 Jul 2026 · our own division | **The lead number.** Concrete, local, shocking |
| 2 | **My mother is the only Quechua-speaking nurse at the Pilpichaca health post.** | Freddy | The human version of ★. Say it right after |
| 3 | GPT-4 translating real ER discharge instructions: **at least one error in 16% of sets in Spanish, 24% in Chinese, 56% in Russian**. Errors grow as the language gets rarer | Kong et al. 2026, *BMJ Quality & Safety* | Why "just use ChatGPT" is dangerous. Quechua is far rarer than Russian |
| 4 | 3.7 M people in Peru have Quechua as first language (13.9%) | Census 2017 | Scale, for "is this big?" |
| 5 | Meta's speech model, out of the box on Chanka: **WER 38.5%, CER 10.7%**, fails on Spanish loanwords | Ricardo, `ricardo-artifacts/reports/humo_wer.json` (smoke test, small set) | Today's "before". **Replace with the frozen baseline** once Ricardo has it |
| 6 | Clinicians already fight language barriers by hand with **back-translation, pre-translated phrases and teach-back** | Mehandru et al. 2022, FAccT (20 clinicians) | Our design is that, automated. Great Q&A answer |

**The "after" number is the one that wins the technical judges** (Peel pattern: a cheap measurement + one statistic).
Ricardo's baseline vs fine-tuned, on a speaker the model never heard. Until it exists, we don't claim an improvement.

## 4 · Story arc (2:00 core)

| t | Beat | What happens | Who |
|---|---|---|---|
| 0:00 | **B1 · Hook** | Opens in Quechua (one line, 3 s), then: *"That's how my mother greets her patients. She's a nurse at the Pilpichaca health post in Huancavelica, Peru, and she's the only one there who speaks Quechua."* | Freddy |
| 0:15 | **B2 · Problem** | ★ number. *"When she's off shift, a patient gets a prescription they can't read, explained in a language they don't speak. ChatGPT? Even in Russian, a big language, it got 56% of discharge instructions wrong somewhere. Quechua barely exists in its training data."* | Freddy |
| 0:35 | **B3 · Demo, the flow** | Nurse speaks Spanish → Chaski says it in Quechua → patient answers in Quechua → nurse reads it in Spanish. Chaski the vicuña on screen shows listening / thinking | Freddy as nurse, Ricardo plays the patient audio |
| 1:05 | **B4 · The moment** | A dosage that doesn't survive the audit. *"Claude translated it, translated it back blind, and the dose didn't match. So Chaski refuses to say it and tells the nurse."* Show the block on screen | Freddy |
| 1:25 | **B5 · How it's built** | *"Meta's speech models are the ears and the mouth. We fine-tuned them on recordings from families in Huancavelica: errors went from X to Y on a voice it never heard. Claude is the brain: it corrects what the ears heard, audits every translation, and writes the summary the patient takes home."* | Ricardo (his work, his credibility) |
| 1:45 | **B6 · Close** | *"Works for the nurse and for the patient. Next stop is my mother's health post on Monday."* Then the summary on screen | Freddy |

**Rules for the script:**
- One number on stage (★). Everything else is for questions.
- Say "Chanka Quechua" once, then "Quechua".
- Never claim something works that we haven't run on the phone that morning.
- Ricardo speaks B5. Two voices make a team; judges score the team.

## 5 · The demo, beat by beat

**Setup at the table:** iPhone running Chaski (TestFlight) on a stand facing the judge · laptop showing the
baseline → fine-tuned chart · Ricardo's service + tunnel up and tested at 10:15 · phone on charge.

| Step | Input | What the judge sees | Risk → mitigation |
|---|---|---|---|
| 1 | Freddy (nurse) taps, says in Spanish: *"Tome una pastilla cada ocho horas, después de comer."* | Chaski "thinking" with its steps, then speaks Quechua, Quechua text on screen | **Nurse turn takes ~15 s today** (ui-ux measured). Dead air kills a 2-min pitch. → Narrate over the "thinking" steps; push for the fast path (D15: measure Haiku/Sonnet for this turn) |
| 2 | Patient answers in Quechua: a pre-recorded clip by a family member (or Mom live) | Language detected as Quechua (1.0 confidence measured), Spanish text for the nurse | Live mic in a loud hall. → Play the clip from a second phone held near the mic, rehearsed |
| 3 | The refusal: a scripted instruction whose dose fails the audit | Red block: "Chaski didn't say this", with the field that didn't match | Must be **deterministic**. → Pick the sentence at the rehearsal and confirm it blocks 5/5 times |
| 4 | End the consultation | Summary: clinical note for the nurse, take-home instructions for the patient | `/resumen` route still missing on Ricardo's side |

**Backups, in order:** (1) app in rehearsal mode on cached turns, (2) the demo video (Sunday 05:00) on the laptop, ready to play.
Say *"here's the recording from this morning"*, never apologize for more than one sentence.

**Mom on video (D18):** judging 10:30–12:30 PT = **12:30–14:30 Lima**, the window she might have. Live cameo is high
risk in a hall. Recommend: record her saying the Quechua greeting + one sentence about her work at the 17:00 call
(with her consent) and use it as the B1 opener. If she's free live, a 20-s video call is a bonus, not the plan.

## 6 · The Cartesia variant (demo-first, as their rubric asks)

B3 → B4 (the flow first, 60 s) → then B2 problem in 20 s → then *"Cartesia is the Spanish side: ink-whisper hears
the nurse in 0.46 s and Sonic speaks to her [verify Sonic is wired in the app before saying it]. It doesn't speak Quechua, so that side is our own fine-tuned model."*
→ limitations in one line. README must list the Cartesia features used and known limitations.

## 7 · Q&A bank (both of us know these cold)

| Question | Answer in one breath |
|---|---|
| Why not Google Translate / ChatGPT? | Error rates grow as the language gets rarer (Kong 2026). And neither tells you when it's wrong. Ours checks itself and refuses |
| What if the translation is wrong? | Blind back-translation + a code comparison of the critical facts (drug, dose, frequency). Any mismatch blocks the message and tells the nurse. Show it |
| Where does Claude fail here? | Quechua is low-resource: Claude can sound fluent and be wrong. That's why it never speaks unchecked, never invents a dose, and a native nurse reviewed the glossary |
| How do you know it improved? | A frozen test speaker the model never heard; same script before and after; WER/CER + facts lost in translation |
| Data / consent? | Every recording with consent, family volunteers, no patient data. [Decide: are consultation audios stored? Say only what's true] |
| Isn't this replacing interpreters? | There's one per ~4,000 people. It's for when nobody is there. The 1812 hotline exists but needs a staff member to call and wait |
| Path to production / who pays? | Health posts under MINSA/SIS; regional health office (DIRESA Huancavelica) as first buyer; the 1812 line as a partner. **[needs Mom's interview]** |
| Why Chanka specifically? | It's what Huancavelica and Ayacucho speak; models are trained on Southern/Cusco Quechua. No paper evaluates LLMs on Chanka (our Scopus/OpenAlex search) |
| Offline? | Not yet: needs signal. Honest limitation; on-device models are the next step |
| What did you build in 36 h? | iOS app, the audit, the voice service on a GPU, a data-collection site families used, fine-tuning + evaluation |

## 8 · What we still need (owner · by when)

| Item | Owner | By |
|---|---|---|
| Frozen baseline + fine-tuned numbers (the "Y" in B5) | Ricardo | 19:00 |
| A dose sentence that blocks deterministically | Freddy + ui-ux session | 15:00 |
| Nurse turn under ~5 s, or a narration that covers it | ui-ux session + Ricardo (D15) | 16:00 |
| Mom: a quote about a real case + the recorded greeting, with consent | Freddy, interview 17:00 | 18:00 |
| The 30 s / 2:00 / 3:00 scripts rehearsed with a timer | Both | 22:00 |
| Demo video | Freddy | Sun 05:00 |
