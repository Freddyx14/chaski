# Devpost draft · Chaski (Cal Hacks 13.0)

> Paste section by section. Every number has its source in `plan/checklist-acordado.md` §E. Fill the `[brackets]`
> only with numbers that exist in a results file. **Opt into:** [Anthropic] Claude for Public Benefit · Best
> People-First Social Impact Hack · Microsoft Built for the Real World · Best Use of Cartesia.

**Tagline (≤ 60 chars):** A medical interpreter that would rather stay quiet than be wrong

---

## Inspiration
My mother is a nurse at the Pilpichaca health center, in the Andes of Huancavelica, Peru. When I interviewed her this
weekend, she said nine out of ten of her patients speak Quechua, and only about one in five of the 36 staff do. Most
staff come from the coast. So the interpreter is whoever happens to be around: another nurse, a technician, the
ambulance driver, a relative. When nobody is, they use gestures and drawings — "like a mute person", she said — and
break a pill into four in front of the patient to show the dose. A consultation that takes 30–40 minutes in Spanish
takes an hour or more in Quechua. Nobody there had heard of the government's interpreter hotline.

## What it does
Chaski is a face-to-face Spanish ↔ Chanka Quechua interpreter on an iPhone, for the staff who don't speak Quechua
and for patients. It doesn't just translate; it interprets:
- **Polishes** what each side said (filler, false starts) without changing a single fact.
- **Asks back** once when something critical is missing ("where does it hurt?"), in the speaker's language.
- **Answers the nurse** when the question is for Chaski ("what did she say?") instead of translating it to the patient.
- **Emergency mode**: verified, pre-recorded triage questions that play instantly, no model in the loop.
- **Prescription**: photo of the box or prescription → dose, frequency, days → spoken in Quechua → "can you repeat it?"
- **Summary** for both sides, with the new Quechua words from that visit, so staff learn the language one patient at a time.
- **Refuses to speak** when it can't verify what it's about to say, and tells the nurse exactly what didn't match.

## How we built it
- **Ears and mouth (open models, fine-tuned):** Meta MMS language ID, Omnilingual ASR for Quechua, MMS-TTS for the
  Quechua voice, NLLB-200 for translation, fine-tuned on recordings our families made this weekend through a web form
  we built (text + audio, with consent). Cartesia handles the Spanish side (ink-whisper transcribed 3.5 s of speech in 480 ms, and the Spanish voice).
- **Brain (Claude):** Opus 5 is the interpreter: one structured call decides among five actions. Sonnet 5 is the
  critic. Code decides: the model proposes, deterministic guards dispose, and every failure fails closed.
- **Guardrails before speaking:** the polish can't change or add a fact; numbers, medicine names, units, negation and
  what a pill is taken with ("with water, not with tea") must survive into the Quechua; a blind back-translation is
  compared fact by fact in code; the critic flags invented advice, diagnoses or a wrong addressee.
- **Verified phrase bank with RAG:** 216 phrases (Peru's Medical College semiology manual + emergency set), hybrid
  multilingual embeddings + lexical retrieval on-device. A phrase is only spoken after a native nurse reviews it.
- iOS app in Expo/React Native (TestFlight), FastAPI service on an AWS A10G, Neon + Vercel for the data form.

## Measured, not claimed
- **Seeded-error bank** (wrong doses, flipped negations, swapped medicines, units, days, vehicles, invented advice):
  no guards catch 0%; asking Sonnet "is this translation right?" catches errors too but can't say why it blocked;
  **Chaski (audited 952-case bank, final run of 224) caught 183/184 — every dose, day, negation, medicine, unit and
  "taken with" error — in 2.6 s per check (p95 3.4 s), and every block names the fact that failed.** It holds back
  20% of correct sentences; about half of those are genuinely weak family translations.
- **Interpreter**, 48 real scenarios: Opus 98% correct action with zero invented clinical data; Sonnet 94%; Haiku 88%.
- **Retrieval**: hybrid RAG finds the right phrase first 88% of the time vs 70% for keyword search.
- **Speech, fine-tuned on our families' voices** (362 clips; tested on a speaker the model never heard, 175 clips):
  Meta's MMS Quechua recognizer went from **53.9% to 40.9% word error** (24% relative), and sentences recognized
  perfectly went from **30 to 51 of 175**. We also fine-tuned NLLB-200 for translation (chrF++ 25.8 → 31.7 on 100
  held-out pairs), but Claude scored 42.3, so Claude translates — the experiment decided, not our preference. And the Quechua
  voice, fine-tuned on a nurse's voice with her permission, sounds like her instead of a robot; a native speaker's
  blind test, not a machine, decides which voice Chaski uses.

## Challenges we ran into
There is almost no open Chanka Quechua data — Common Voice has three minutes of it — so our families became the
dataset overnight. Writing Quechua is hard even for native speakers, so the form asks them to write and then read
aloud what they wrote. And a live test found a real hole: "take it with water, not tea" came back as "drink with one,
not with him" and still passed, because nothing tracked what a pill is taken with. We added that check in an hour.

## Accomplishments we're proud of
A guard layer we can measure, a critic chosen by data (Anthropic suggested Haiku; Sonnet won on our numbers), and a
product shaped by an interview with the person who actually does this job.

## What we learned
In health, a confident wrong sentence is worse than silence. Low-resource languages are where LLMs sound fluent and
are wrong, so the system has to check itself and say when it can't.

## What's next for Chaski
Native review of the full phrase bank with the nurses of the Pilpichaca health zone (10 more health posts), measuring
the Quechua → Spanish direction, on-device models for posts without signal, and turning the visit summaries into a
Quechua course built from each nurse's own patients.

## Built with
claude-opus-5 · claude-sonnet-5 · anthropic-sdk · python · fastapi · pydantic · meta-omnilingual-asr · mms-lid ·
mms-tts · nllb-200 · fastembed · numpy · cartesia · expo · react-native · typescript · next.js · neon · vercel · aws
