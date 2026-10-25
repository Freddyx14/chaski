## Inspiration
My mother is a nurse at the Pilpichaca health center, high in the Andes of Huancavelica, Peru. When I interviewed her this weekend, she told us that nine out of ten of her patients speak Quechua, and that most of the staff come from the coast and don't. So the interpreter is whoever happens to be around: another nurse, a technician, the ambulance driver, a relative. When nobody is, they use gestures and drawings, and break a pill into four in front of the patient to show the dose. A visit that takes 30–40 minutes in Spanish takes an hour or more in Quechua.

Her post is not an exception: only **1 in 7 doctors** starting their rural service year in Peru speaks even basic Quechua or Aymara (Bendezu-Quispe et al., 2020). Chaski is the interpreter for when nobody there speaks it.

## What it does
Chaski is a hands-free Quechua (Chanka) ↔ Spanish medical interpreter on an iPhone, for the whole health staff (doctors, nurses, obstetricians, technicians) and for the patient. You turn it on and it listens. Each time someone speaks, it detects who it was and in which language, and then it acts like a human interpreter would:

- **Translates** for the other person, after cleaning up filler and false starts without changing a single fact.
- **Asks back** when a critical fact is missing ("Which medicine, and how often?"), once, in the speaker's own language.
- **Answers** questions meant for Chaski ("What did she say?") instead of translating them to the patient.
- **Checks every instruction before speaking.** Code verifies that every dose, number, day, negation, medicine and "with water" survived, and a second model translates the Quechua back without seeing the original. If something doesn't match, Chaski never says the doubtful version: it asks the speaker to repeat, naming what it wasn't sure of.
- **Emergency mode:** triage questions written and reviewed by a native-speaking nurse, pre-recorded, playing instantly with no model in the loop.
- **Prescription by voice:** a photo of the box or prescription is read back to the health worker ("I read: paracetamol 500 mg, one tablet every 8 hours… shall I tell them?") and only after a spoken "yes" is it said in Quechua.
- **Speaks Quechua in a familiar voice:** a voice trained on a community nurse's recordings, with her permission.
- **Summary** of each visit: a note for the clinical record, take-home instructions for the patient, and the new Quechua words from that visit, so the staff learn the language one patient at a time.

## How we built it
- **Brain (Claude).** Claude Opus 5 is the interpreter: one structured call per turn decides among five actions (translate, ask back, answer, didn't understand, verified phrase). Claude Sonnet 5 translates and is the critic that back-translates blind. No agents beyond interpreter and critic, because every extra agent is another place to be wrong. Claude Haiku reads prescriptions and boxes. The model proposes, code decides, and every failure fails closed.
- **Guards before speaking.** The polish can't add or change a fact; numbers, medicine names, units, negation and what a pill is taken with must survive into the Quechua; the blind back-translation is compared fact by fact in code; the critic flags invented advice, diagnoses or a wrong addressee.
- **Ears and mouth (fine-tuned open models).** Meta's MMS language ID, MMS Quechua speech recognition and MMS-TTS, fine-tuned on recordings our families made this weekend through a web form we built (text + audio, with consent), on an A10G GPU. Cartesia is the Spanish side: ink-whisper hears the health worker (3.5 s of speech in 480 ms) and Sonic speaks to them.
- **RAG over verified phrases.** A bank of 216 clinical phrases with hybrid multilingual-embedding + keyword retrieval, no vector database. The phrases a native nurse approved are also given to the translator as examples, so Chaski speaks more like Pilpichaca with every phrase she reviews.
- **A feedback loop.** Every turn that passed the critic is saved; if the patient answers normally the phrase is confirmed, if they ask "what did it say?" it's flagged. Only what a community nurse approves becomes an example for the translator.
- iOS app in Expo / React Native (TestFlight), FastAPI service with a live streaming route, Next.js + Neon + Vercel Blob for the data form.

## Challenges we ran into
- **There is almost no Chanka Quechua speech data,** so our families became the dataset overnight. Writing Quechua is hard even for native speakers, so the form asks them to write a phrase and then read aloud exactly what they wrote.
- **A live test found a real hole:** "take it with water, not with tea" came back as "drink with one, not with him" and still passed, because nothing tracked what a pill is taken with. We added that check, and the case to our test bank, within the hour.
- **Speed vs. safety.** The first full turn took 17 seconds. Translating while Opus decides, and choosing the translator's effort by measurement, brought it down to about 11 seconds on real audio through the live service, without losing a single critical check, and we are still cutting.
- **Choosing the translator honestly.** We compared five translators on the same 62 sentences our families wrote, including our own fine-tuned model. Claude damaged 0 of 92 critical terms, so Claude translates. We also caught that part of an earlier evaluation set had leaked into training, and threw that number out.

## Accomplishments that we're proud of
- **A safety layer we can measure.** On an audited bank of seeded errors (wrong doses, flipped negations, swapped medicines, units, days, invented advice), Chaski caught **183 of 184, and 100% of the critical ones**, in about 3 seconds per check. Asking a model "is this translation right?" also catches errors but can't say which fact failed, and holds back far more correct sentences.
- **Fine-tuning that helped on a voice the model never heard:** word errors went from 53.9% to 40.9%, and perfectly recognized sentences from 30 to 51 of 175.
- **Model choices made by data, not habit:** Opus picked the right action in 98% of 48 real scenarios with zero invented clinical data; Anthropic suggested Haiku as the critic, but Sonnet won on our numbers, and we made it fast instead.
- **A product shaped by the person who actually does this job,** from the first interview to the emergency phrases she wrote and reviewed herself.

## What we learned
In health, a confident wrong sentence is worse than an honest "could you repeat that?". Low-resource languages are exactly where LLMs sound fluent and are wrong, so the system has to check itself, say what it wasn't sure of, and ask, like a good interpreter does. And the most valuable data wasn't the model: it was a nurse's 24 reviewed phrases, which improved translation more than hundreds of automatic ones.

## What's next for Chaski
Take it to the Pilpichaca health center first, then the 10 health posts in its health zone. Native review of the full phrase bank, measuring the Quechua → Spanish direction, on-device models and a cached emergency bank for posts without signal, and turning the visit summaries into a Quechua course built from each team's own patients.
