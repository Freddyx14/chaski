# Chaski · judge Q&A (v5, Sun Oct 25 01:35 PT · D43 translator, D41 nurse examples, D44 patient-as-reviewer memory)

> The 2 minutes after the pitch. Built from `SOT.md` (D1–D43), `plan/arquitectura-interprete.md`, `evals/HISTORIA.md`,
> `evals/CRITERIOS.md`, `evals/REFERENCIAS-chrf.md` and the interview. **Every number here has its file. If it's not
> here, don't say it.** Answers are what you say out loud, in English.
>
> **F** = Freddy answers · **R** = Ricardo answers. 🔸 = depends on a decision still open.

---

## 0 · How to use the 2 minutes

1. **One breath, then stop.** Answer in ≤ 15 s: the decision, the number, the file. Let them ask the follow-up.
   Two minutes = 5–6 questions. A 40-second answer costs you two questions.
2. **Lead with the decision, then the measurement.** "We chose X because we measured Y." That's what *Intentionality*
   and Anthropic's criterion 4 reward.
3. **Say the limit before they find it.** "Honestly, that's not measured yet. Here's how we'd measure it."
4. **Don't know → say so.** "We didn't measure that. My guess is X, but I wouldn't put it on a slide." Never invent.
5. **Point at the screen.** If a question has a live answer (the red block, the summary, the steps), show it.
6. **Hand-offs are clean.** Models, voice and fine-tuning → Ricardo. Architecture, guards, evals, product → Freddy.

---

## 1 · The eight most likely questions (know these cold)

| # | Question | Answer | Who | Source |
|---|---|---|---|---|
| 1 | **How do you know the Quechua is right?** | "We don't trust the translator. A second Claude translates the Quechua back *without seeing what I said*, and plain code compares dose, frequency, days, medicine, unit, negation and what it's taken with. If one fact doesn't match, Chaski doesn't speak. And a nurse from the community reviewed every emergency phrase." | F | `app/chaski/critico.py`, `hechos.py` · `evals/banco/revision_enfermera.json` |
| 2 | **What happens when it's wrong?** | "It stays quiet and tells the nurse which fact failed. We seeded 184 errors, it caught 183, and 100 % of the critical ones: dose, days, negation, medicine, unit." | F | `evals/ataques/resultados/chaski-2026-10-24-1740.json` |
| 3 | **What does Claude actually do here?** | "It's the brain, in two roles and no more. Opus decides each turn: translate, ask again, answer, say it didn't understand, or play a verified phrase. Sonnet is the critic that back-translates blind. Plus the summary and reading the prescription. The open speech models are only ears and mouth." | F | D32, D38, D39 · README «Where Claude is used» |
| 4 | **Why not just use Google Translate or ChatGPT?** | "No translator can refuse to speak, and on the public benchmark Google's Quechua scores 34 chrF. A peer-reviewed study gave ChatGPT real discharge instructions: 89–97 % of sentences were right, but 16–56 % of whole instruction sets had at least one error, and it got worse as the language got rarer. Chanka is far rarer than any of those." | F | Kong et al. 2026, *BMJ Qual Saf* · `research/papers.md` · `evals/REFERENCIAS-chrf.md` (Robinson 2023) |
| 5 | **How do you know the fine-tuning helped?** | "A whole person the model never heard, same script before and after. Word errors 54 → 41 %, sentences recognized perfectly 30 → 51 of 175." | R | commit `7b57a9b` · `evals/HISTORIA.md` §4 |
| 6 | **Isn't it slow for a clinic?** | "A translated instruction takes about 8 seconds, and in 20 real turns all 20 were said, and while it waits the screen shows each step. Questions back and verified phrases take about 4, and emergencies are instant. We cut it from 17 by translating while Opus is still deciding, and by choosing a translator effort that kept zero fixed-term errors. Today an instruction gets repeated up to four times and a visit takes an extra 20 minutes." | F | `evals/HISTORIA.md` §2d (p50 8.0 s, p95 10.5 s, 20/20) · interview |
| 7 | **How do you measure impact?** | "The baseline already exists. She told us every visit's language is recorded in MINSA's daily HIS form, so we can count Quechua visits and compare their length, today 40 minutes vs an hour or more. Our own log adds blocks, repeats and 'did the patient understand'." | F | interview (`research/entrevistas/…-insights.md`) |
| 8 | **Who uses it on Monday?** | "The roughly 80 % of the 36 staff at her post who don't speak Quechua. She told us she wouldn't need it herself, but the others need it, 'sí o sí'. Next, we take it to her post, and the health zone covers 10 more." | F | interview l.91 |

---

### The three questions judges ask every team (Kurbaitaev, AngelHack · `research/pitch-research.md` §6)

| Question | Answer | Who |
|---|---|---|
| **What did you build this weekend?** | "All of it. The app, the interpreter, the guards and the critic, the evals, the voice form, and the fine-tuning on voices our families recorded on Saturday. Nothing existed on Friday." | F |
| **What's real and what's mocked?** | "Real: every Claude call, the fine-tuned ears, the family audio, the guards, every number on the slide. Simulated, and we say it on stage: the translator error in the red demo, which we inject on purpose so you can see the refusal every time." | F |
| **What breaks first at scale?** | "Connectivity. Rural posts have patchy signal and it needs the network today. Then the reviewed phrase bank: one nurse reviewed 24 phrases, and each new post needs its own reviewer for its own Quechua." | F |

## 2 · Technical decisions: "why X and not Y?" (the core of this Q&A)

Every row is a decision that is written down with its reason and, where it applies, the measurement that settled it.

### Architecture

| Question | Answer | Who | Source |
|---|---|---|---|
| **Why an agent and not a translator?** | "The nurse described a human interpreter: they understand, ask again when something's missing, and don't pass on half an instruction. So one Claude call picks one of five actions, and code enforces the rules: at most one clarifying question, no new facts, a bank phrase only if it's a real candidate." | F | D32 · `plan/arquitectura-interprete.md` §1–2 |
| **Why only two agents? Why not a team of agents?** | "Anthropic's team told us at the workshop: one critic that checks nothing was invented, and no agent you don't need. So it's two roles, and a third only gets in with a measured failure that justifies it. A third model in the loop is a third place to be wrong and more seconds of wait." | F | D38 |
| **Why does code decide and not the model?** | "The model proposes and code decides. Comparing two numbers is something code never gets wrong and a model sometimes does. Claude extracts the facts, and a plain comparison says whether they match. It also fails closed: any error, timeout or malformed output, and Chaski says nothing." | F | D37 · `orquestador.py` |
| **Why blind back-translation?** | "If the critic sees the original, it reads what it expects. Blind, it can only report what the Quechua actually says. That's how we caught a real case live: 'take it with water, not with tea', where the water had turned into 'one'." | F | `evals/ataques/README.md` («the live case») |
| **Why not just ask Claude 'is this translation right?'** | "We measured exactly that. A strong model asked yes/no catches the errors too, but it blocked 1 in 4 correct sentences and can't say which fact failed. The weak one blocked 2 in 3. A nurse who gets blocked that often goes back to gestures." | F | `juez_claude-2026-10-24-1644.json`, `…-1513.json` |
| **What are the eight barriers?** | "What was heard, a polish that can't change facts, nothing new added, fixed terms for numbers and medicines, the blind round trip, the facts nobody compared before (negation, allergy, pregnancy, body part, route), verified phrases first, and 'did the patient understand'." | F | `plan/arquitectura-interprete.md` §2b |
| **Why a phrase bank with RAG and no vector database?** | "216 phrases fit in memory. A database would be infrastructure with no measured problem behind it. Hybrid search, embeddings plus keywords, finds the right phrase first 88 % of the time vs 70 % with keywords alone." | F | D34 · `evals/banco/resultados/2026-10-24.json` |
| **How do you stop prompt injection?** | "What the patient and the nurse say goes in as data, not instructions, and code decides who hears it and in what language. Opus handled 4 of 4 injection scenarios." | F | `interprete.py` · `evals/interprete/resultados/claude-opus-5-2026-10-24-1508.json` |

### Models

| Question | Answer | Who | Source |
|---|---|---|---|
| **Why Opus as the main model? It's the expensive one.** | "We measured all three on 48 real scenarios: Opus 98 %, Sonnet 94 %, Haiku 88 % right action. Only Opus invented zero clinical data. Sonnet added 'paracetamol' that nobody said. In a clinic that settles it." | F | `evals/interprete/resultados/` · D39 |
| **Anthropic suggested Haiku for the critic. Why Sonnet?** | "We tried Haiku first. It caught 153 of 160 and let invented diagnoses through. Sonnet caught 160 of 160. Haiku's advantage was speed, so we made Sonnet fast instead, from 9 s to 2.6 s, by cutting thinking in the extraction and running calls in parallel, with the same accuracy." | F | `chaski-…-1513.json` vs `…-1518.json` · `…-1740.json` |
| **Did you try a cheaper or faster decision model?** | "Yes, Jev, a typed decision model, as a backup. 0.4 s instead of 2.9, but 83 % right vs Opus's 98, and it failed the three cases that matter most: a critical fact was missing and it translated anyway. It's a fallback, not a replacement." | F | `evals/jev/resultados/jev-20261024-2255.json` |
| **You fine-tuned your own translator. Why does Claude translate?** | "We put five translators on the same 62 sentences our families wrote, including our own NLLB. What decided it was the fixed terms, the numbers and medicine names that must survive: Claude damaged zero of them in 92 translations, NLLB three. NLLB stays for the offline work. We decided by measurement, not by pride." | R → F | `evals/traduccion/resultados/` · SOT D43 |
| **Why not Gemini? It scored higher.** | "Gemini 3.8 Flash had the best character score, 63.8, but it damaged a fixed term and took 8.6 seconds just to translate, 20 at the slow end. The faster Gemini damaged four. Claude on medium damaged zero and reads the patient best, 50 vs 44 on Quechua to Spanish. A character score can't tell 'eight' from 'six'. Our guards can." | F | `evals/traduccion/resultados/comparar-20261024-2324.json`, `…-2336.json` |

### Speech and data

| Question | Answer | Who | Source |
|---|---|---|---|
| **Where did the Chanka data come from?** | "Our families. We built a web form on Friday night: you see a Spanish phrase, write it in Quechua and record yourself reading it. 362 clips trained the recognizer, with consent, and the recordings never go in the repo." | R | `form/` · README «Data, consent» |
| **Why write it down too, and not just record?** | "Translating, understanding and speaking all need text. With voice only, someone would have had to transcribe about 450 audios by hand this weekend." | R | D25 |
| **Why Chanka specifically?** | "It's the Quechua of Huancavelica and Ayacucho, and models are trained mostly on Cusco's. We found no paper that evaluates large language models on Chanka." | F/R | `research/papers.md` |
| **Why is your test set one person?** | "On purpose. Testing on a voice the model already heard would inflate the number. The split code refuses to run with fewer than two speakers. One held-out speaker is small, and we say so. It's honest, not big." | R | `partir_por_hablante` · README |
| **Your WER went up on one metric?** | "Strict WER went from 76 to 82 % because the model now writes normalized spelling. Quechua has no settled spelling, so we report both, and 15 points of the strict number are spelling, not recognition." | R | README «Speech models» |
| **Is that your mother's voice? Isn't that a deepfake?** | "It's a voice trained on her recordings, with her permission, and we always say so. Patients hear a nurse from their own valley instead of a robot. And it only ever speaks Quechua that passed the guards and the critic, or phrases she reviewed herself." 🔸 *Claim "she picked it in a blind test" only after she has done it.* | R | Freddy 01:55 · `evals/HISTORIA.md` §4 |

---

## 3 · The measurements: how they were done (when a judge pushes on a number)

| Question | Answer | Who | Source |
|---|---|---|---|
| **Your 184 errors are synthetic. How do you know it catches real ones?** | "They're planted on real sentences our families wrote, one change each, the kind that matters clinically. And the bank grew from a real failure: the 'water' case we caught live is in it now. Synthetic, yes, but each one is a real sentence with one real-world mistake." | F | `evals/ataques/README.md` |
| **What did you check before trusting the bank?** | "We audited it before optimizing. Every mutation has to really change the meaning, a 'correct' sentence has to really be correct, and nothing comes from the 100 sentences we reserved to measure translation. Labels that lie give numbers that lie." | F | `evals/CRITERIOS.md` §4 · `AUDITORIA.md` |
| **You block 1 in 5 correct sentences. Won't the nurse stop using it?** | "That's the number we watch most, and it's a gate: above 20 % a configuration is out. About half of those 8 are weak translations in the family data that *should* be blocked. On the 20 live turns we ran end to end, only 1 was blocked." | F | `chaski-…-1740.json` · `evals/CRITERIOS.md` §1, §5 |
| **Does it get better with use? What's the feedback loop?** | "Yes, and the patient is the reviewer. Chaski keeps every turn that passed the critic. If the patient answers normally, that phrase is confirmed; if they ask 'what did it say?', it's flagged. Only what a community nurse approves becomes an example for the translator, and from the next turn on Chaski speaks a little more like Pilpichaca. Zero extra seconds per turn." *If pushed, why not use everything automatically:* "We measured it. 85 of 100 auto-translated phrases passed the critic. As examples they beat nothing, 54.9 → 56.2, but never beat the nurse's 24, 57.4. So the machine filters and the human teaches." | F | `evals/HISTORIA.md` §2d–§2e · D41, D44 · `plan/foso.md` |
| **Is a 3-point gain just noise?** | "Fair question. Runs vary by about 2 points, so we decide by the direction that repeats, not one figure. The nurse's phrases beat the automatic ones in all three mixes we tried, and on the patient's side the gain is about 7 points." | F | `evals/HISTORIA.md` §2e |
| **How did you choose between configurations?** | "We wrote the rules before measuring. Three gates: 100 % of critical errors, at most 20 % false blocks, zero fail-open cases. Then a score: accuracy 65, speed 25, cost 10. In a clinic an error costs more than a wait, but a 40-second wait kills adoption." | F | `evals/CRITERIOS.md` |
| **Is 51 chrF good?** | "Only comparable on the same test set. On ours, Claude is about 17 points above NLLB, and a published study says 3 points is enough for 90 % of people to agree which system is better. For a public reference, the best shared-task system for this language scored about 39 on its own set." | R | `evals/REFERENCIAS-chrf.md` (Kocmi 2024, AmericasNLP) · `evals/traduccion/` |
| **How much did the evals cost?** | "The final attack run was $1.89, about 856 Sonnet calls with caching. We set a $30 budget for all measurement." | F | `plan/checklist-acordado.md` · `evals/CRITERIOS.md` §3 |
| **What does a turn cost?** | "About two cents per translated instruction, measured from real tokens: Opus deciding, Sonnet translating and Sonnet checking. Questions back and verified phrases cost less, only Opus. So a full consultation costs cents, not dollars." | F | `evals/latencia/resultados/costo-turno-20261024-2345.json` (list prices, not checked against the invoice) |

---

## 4 · Where it can go wrong (Anthropic's criterion 4, say these before they ask)

| Limit | How to say it |
|---|---|
| **No offline mode** | "It needs a connection today: Claude, Cartesia and the GPU. Rural posts often have patchy signal. On-device speech models and a cached emergency bank are the next step." |
| **Quechua → Spanish not measured** | "The patient's side goes through the same critic, but we only measured the nurse → patient direction, where a wrong dose hurts most." |
| **Chaski's own replies skip the critic** | "When Chaski asks the nurse a question back in Spanish, only the code guards check it, not the critic." |
| **Per-word confidence missing** | "The 'don't guess a number you barely heard' guard needs per-word confidence from the Quechua recognizer, which isn't wired yet." |
| **Bank mostly unreviewed** | "Of 216 bank phrases, only the 24 emergency ones are reviewed by a native speaker, and the others are never played until they are." |
| **One reviewer** | "The Quechua UI and the emergency phrases were reviewed by one nurse. One expert is a start, not a validation." |
| **Not a medical device** | "It doesn't diagnose or prescribe. It only carries what the nurse said, and refuses when it can't verify that." |

---

## 5 · Product, impact and adoption (Microsoft, People-First, general)

| Question | Answer | Who | Source |
|---|---|---|---|
| **Doesn't Peru have an interpreter phone line?** | "Line 1812, launched in May, from the Ministry of Culture. She'd never heard of it and they've never used it. And it depends on staff deciding to call. What she asked for in an emergency was speed." | F | interview · `research/problemas-lenguas-originarias.md` |
| **Are you replacing interpreters?** | "There's about one certified bilingual public servant per 4,000 Quechua speakers in Huancavelica. Chaski is for when nobody's there, which is most of the time." | F | `research/problemas-lenguas-originarias.md` |
| **Is her post typical?** | "It's not an exception. Only 1 in 7 doctors starting their rural year has even basic Quechua or Aymara." | F | Bendezu-Quispe 2020 |
| **Has a bad translation actually hurt someone there?** | "She doesn't remember a case, and we won't invent one. The cost she described is time, repeating up to four times, and the risk is what the BMJ study measured." | F | interview «Lo que NO dijo» |
| **Who pays for it?** | "Today, nobody. It's built for public benefit. A translated turn costs about two cents. The natural buyer is the regional health system, but we haven't talked to them, and I won't pretend we have." | F | — |
| **Path to production?** | "Three steps: try it at her post with the staff who don't speak Quechua, get the 216 bank phrases reviewed, and make the emergency bank work offline. Then the 10 posts in her health zone." | F | interview · README limits |
| **Privacy?** | "No patient was recorded this weekend. Family recordings were donated with consent and never go in the repo." 🔸 *Whether consultation audio is stored in production: not confirmed, don't claim either way.* | F | README «Data, consent» |
| **Why both roles, staff and patient?** | "The patient should be able to start the conversation too. It's one app, and the role only changes some screen text, the agent's instructions and the type of summary: a clinical note or take-home instructions." | F | D27 |
| **Why the vicuña?** | "Chaski were the Inca messengers. A friendly face makes a machine speaking your language feel less cold, especially for older patients." | F | D22, D30 |
| **What's the summary for?** | "A note for the clinical record, instructions the patient takes home, and the new Quechua words from that visit. She said it would teach her words she doesn't know, so the staff learn one patient at a time." | F | D36 · interview |

---

## 6 · Cartesia judges

| Question | Answer | Who |
|---|---|---|
| **How do you use Cartesia?** | "It's the whole Spanish side. Ink-whisper hears the nurse, 3.5 s of speech in 480 ms with no errors, and Sonic speaks to her." | R |
| **Why not Cartesia for Quechua?** | "It doesn't support Quechua, and its speech-to-text has no automatic language ID. So language ID, the Quechua ears and the Quechua voice are our own fine-tuned Meta models, by necessity." | R |
| **Limits?** | "We haven't measured Cartesia's speaking latency yet. It's in the README." | R |

---

## 7 · Hard or hostile questions

| Question | Answer |
|---|---|
| **"This is just a wrapper around Claude."** | "Claude is the brain, by design. But the ears and the voice are our fine-tuned models on data we collected this weekend, the safety layer is code, and every choice, including where *not* to use Claude, was measured. We dropped Haiku as critic and our own NLLB as translator because of numbers." |
| **"What's your moat? Anyone can call Claude."** | "The moat isn't the model. Tonight we swapped translators in an hour, with numbers. It's the Quechua of the zone. Before translating, Chaski shows the translator the five most similar phrases the nurse reviewed. With only her 24 phrases, Spanish→Quechua went from 52.6 to 56.0 and the patient's side from 49.1 to 56.0, on 62 sentences nobody had seen. Every phrase she reviews improves the next translation, with no retraining." *If pushed:* "Her 24 beat 286 generic verified phrases. Local beats more. On greetings from another variety it went down, 48 → 43, which is exactly why it's a moat: it learns her Quechua." | F | `evals/HISTORIA.md` §2d · `evals/moat/resultados/` · `plan/foso.md` · D41 |
| **"Your mother reviewed it, isn't that biased?"** | "She's the domain expert, and she's also the reason we know the problem. One reviewer is a limit we say out loud. The numbers don't depend on her: they come from the attack bank and a held-out speaker." |
| **"Why should we believe 99.5 %?"** | "Don't believe it, check it. The run file is in the repo with every case, and the false-block rate sits next to it, because catching 100 % is easy if you block everything." |
| **"What if the patient doesn't speak Chanka but another variant?"** | "We built and measured Chanka only. Other variants would need their own data and their own test speaker. We wouldn't claim them." |
| **"What happens with no signal in an emergency?"** | "Today it doesn't work offline. That's the first thing we'd fix, starting with the emergency phrases, which are just stored audio." |

---

## 8 · Never say

- "The only Quechua-speaking nurse" (3 of 6 nurses speak it).
- "A bad translation hurt someone at her post."
- "2 % of centers have interpreters" (no source).
- "chrF 40 is decent, 60 is near-human" (no peer-reviewed source).
- "A turn takes 6.5 s" (that was without translation and voice).
- "Claude reduces transcription errors by X" (built, not measured).
- "The automatic memory improves translation by itself" (it doesn't: only nurse-approved phrases are measured to help, §2d–§2e).
- "The examples improve everything" (on greetings from another variety they lowered the score, 48.3 → 42.6).
- "NLLB fine-tuned 25.8 → 31.7" (contaminated, 58 of 100 test sentences leaked into training).
- "A turn takes 17 s" (that was the old thinking translator; with D43 it's ~8 s).
- "Under three seconds" for the critic (p95 is 3.4 s; say "about three").
- Any number for the voice blind test before she has done it.
