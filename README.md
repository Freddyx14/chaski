# Chaski

**A face-to-face Spanish ↔ Quechua Chanka medical interpreter for the Pilpichaca health center (Huancavelica, Peru).**

At Pilpichaca, about 90 % of patients speak Quechua and about 20 % of the staff do, "not so fluently"
(interview with a nurse at the center, `research/entrevistas/2026-10-24-enfermera-pilpichaca-insights.md`).
Most staff come from the coast and speak no Quechua. Today they borrow whoever is on shift (another nurse, a technician,
the driver), a relative, or gestures and drawings. A consultation that takes 30–40 minutes in Spanish takes an hour
or more in Quechua, and instructions get repeated "2, 3, up to 4 times" (same file).

Chaski runs on an iPhone between the two people. **Who uses it:** staff who don't speak Quechua, and Quechua-speaking
patients, each in their own language (`SOT.md` D27).

Built at Cal Hacks 13.0 for Anthropic *Claude for Public Benefit*, and also submitted to Cartesia, Microsoft
*Built for the Real World* and People-First.

---

## Why this is hard, and why not just ChatGPT

- **Low-resource language, high-stakes content.** Kong et al. (2026, *BMJ Quality & Safety*) translated 316 sentences
  of real emergency discharge instructions with ChatGPT-4. Sentence accuracy was high (Spanish 97 %, Chinese 95 %,
  Russian 89 %), yet **16 %, 24 % and 56 % of whole instruction sets had at least one error**, and accuracy fell as the
  language got less represented (`research/papers.md`). Chanka has far less data than Russian.
- **Our own measurement says the same.** Claude Sonnet 5 with no fine-tuning and thinking off scores **chrF++ 42.31** on 30 verified
  Spanish→Chanka pairs (`ricardo-artifacts/reports/traduccion.json`); the product's translator, which thinks, scores
  **51.8** on the same pairs (`evals/latencia/traductor_modos.py`). It doesn't get the grammar wrong, it gets the register
  wrong (`ricardo-artifacts/reports/metricas.md`).
- **A confident wrong sentence is worse than silence.** "No lo tome con té" losing its "no" is a different instruction.
  A plain chatbot has no way to refuse to speak.
- **No off-the-shelf speech stack.** Cartesia does not support Quechua and its STT has no automatic language ID
  (checked in their docs, `ricardo-artifacts/reports/arquitectura.md`), so the Quechua ears and mouth are open Meta
  models we fine-tune ourselves.

---

## How a turn works

Speech models are the ears and the mouth. **Claude is the brain.** **The model proposes, code decides.** And it
**fails closed**: any exception, timeout or malformed output in any step means Chaski says nothing to the patient and
shows the staff "no pude verificar esto" (`app/chaski/orquestador.py`).

```
 audio
   │
   ▼
 language ID  (mms-lid-512, spa / quy)
   │
   ├─ Spanish ─► Cartesia ink-whisper ───────┐
   └─ Quechua ─► omniASR (N-best + conf.) ───┤
                                             ▼
             INTERPRETER  (Claude Opus 5, one call, structured output)
             picks ONE action:  traducir · repreguntar · responder · no_entendi · usar_frase_banco
             code enforces: who hears it, max one clarifying question, bank id must be a real candidate
                                             │
          usar_frase_banco ─► verified audio from the bank (nothing generated)
                                             │
                                             ▼
             TRANSLATION  (NLLB-200 fine-tuned behind a switch; Claude fallback)
                                             │
                                             ▼
             CODE GUARDS  B1–B4: ASR confidence on critical words, polish kept the facts,
                          nothing new added, numbers / medicines / units / vehicle / negation survive
                                             │
                                             ▼
             CRITIC  (Claude Sonnet 5): blind back-translation + fact extraction + "what was added?"
             code compares the facts (hechos.comparar)
                                             │
                    ┌────────────────────────┴───────────────────────┐
                    ▼                                                ▼
     speak:  Cartesia Sonic (Spanish)                      BLOCK: staff sees which field
             mms-tts-quy (Quechua)                         didn't match; patient hears nothing
     status: dicho | dicho_con_aviso                       status: bloqueado
```

Behavior rules C1–C9 and the eight barrier layers B1–B8 are specified in `plan/arquitectura-interprete.md` §1 and §2b.

---

## Where Claude is used, and why

| Job | Model | Where | Why this model |
|---|---|---|---|
| **Main interpreter**: decides the action, polishes speech (removes filler, never changes a fact), writes the clarifying question or Chaski's answer to the staff | `claude-opus-5` (`CHASKI_MODELO_PRINCIPAL`) | `app/chaski/interprete.py` | Measured on 48 scenarios: Opus 98 %, Sonnet 94 %, Haiku 88 % correct action. Opus was the only one with zero invented data (`evals/interprete/resultados/`). `SOT.md` D39 |
| **Critic**: blind back-translation, fact extraction, detection of added advice / diagnosis / addressee. It never writes what the patient hears | `claude-sonnet-5` (`CHASKI_MODELO_CRITICO`) | `app/chaski/critico.py` | Anthropic's workshop advised a critic on Haiku. On the same 200-case attack sample, Haiku as critic caught 153/160 with 7/40 false blocks (`evals/ataques/resultados/chaski-2026-10-24-1513.json`). Sonnet caught 160/160 with 3/40 (`…/chaski-2026-10-24-1518.json`). Measurement won. `SOT.md` D38–D39 |
| **Translation fallback**: Spanish ↔ Quechua when the fine-tuned NLLB service is missing or fails | `claude-sonnet-5` | `app/chaski/traducir.py` | The result records `motor` and `respaldo`. The critic runs on whichever engine produced the text |
| **Consultation summary + glossary**: clinical note for staff or take-home instructions for the patient, plus up to 8 Quechua words to learn | `claude-sonnet-5` | `app/chaski/resumen.py` | Code puts blocked turns in `no_se_dijo`, never in the instructions. A glossary word survives only if it appears verbatim in a turn that reached the patient |
| **Prescription / box vision** (`POST /ver`): reads the medicine, strength and form, and cross-checks it against what the nurse said | `claude-haiku-4-5` (`CHASKI_MODELO_VISION`) | `ricardo-artifacts/servicio/vision.py` | A legible paracetamol box was read in 2.25 s. A blurred one returned `seguro: false` with nothing invented, in 2.69 s (`ricardo-artifacts/servicio/README.md`). It refuses to write Quechua itself, so all Quechua goes through the audited path |

### Where it can go wrong, and what answers it

| Risk | Guard |
|---|---|
| **Weak Quechua fluency** (low-resource language) | The critic back-translates **blind** (it never sees the original), then plain code compares dose, frequency, days, medicine, unit, route, body part, allergy and pregnancy (`app/chaski/hechos.py`). NLLB fine-tuning is only kept if it beats Claude on chrF++ (`SOT.md` D33) |
| **Negation flips** ("no lo tome con té" → "tómelo con té") | Prohibitions are a compared fact (B6, `hechos.py`). Code also checks that `ama` / `mana` / `-chu` survive into the Quechua (B4, `app/chaski/guardas.py`). 20/20 caught in the final run |
| **Invented advice or diagnosis** | Code requires that the polish's facts are a subset of the transcript's (B2/B3). The critic lists anything the output says that the source didn't (`sin_agregados`). 40/40 appended advice/diagnosis caught in the final run |
| **Prompt injection** ("ignore the above…") | Patient and staff speech is wrapped as data in the prompt. The code derives addressee and language, it doesn't take them from the model (`interprete.py`). Opus handled 4/4 injection scenarios (`evals/interprete/resultados/claude-opus-5-2026-10-24-1508.json`) |
| **ASR mishearing a number** (`pusaq` 8 vs `suqta` 6) | B1: if recognizer confidence is under 0.6 and the turn contains a number, medicine or body part, the turn is blocked and Chaski asks again (`app/chaski/PARA_RICARDO.md`). **B1 only runs when the ASR sends a confidence. Per-word confidence from the Quechua ASR is still pending** (`plan/checklist-acordado.md` §C) |
| **Unreviewed phrases spoken as if verified** | Only bank items with `revisado: true` are ever served or played. Today **0 of 216** are reviewed, so none are spoken (`plan/checklist-acordado.md`, `app/chaski/PARA_RICARDO.md`). The app never plays phrases marked `[revisar…]` (`movil/README.md`) |

---

## Results

All numbers below come from real API runs committed in the repo. Simulated runs are not committed and not quoted.

### Attack bank: seeded errors the system must refuse to speak

Errors planted on real family-written Chanka pairs: changed number, days, negation, medicine, unit, vehicle, appended
advice/diagnosis, a polish that adds a fact. Next to each we put the number that keeps it honest, which is how many
**correct** sentences were blocked (`evals/ataques/README.md`).

| System | Seeded errors caught | Correct sentences blocked | Source |
|---|---|---|---|
| No guards (floor) | 0 / 160 (0 %) | 0 / 40 | `evals/ataques/resultados/sin_barreras-2026-10-24-1459.json` |
| Naive Claude judge ("is this faithful? yes/no", Haiku 4.5) | 150 / 160 (94 %) | 26 / 40 (65 %) | `evals/ataques/resultados/juez_claude-2026-10-24-1513.json` |
| Naive Claude judge, Sonnet 5 (same 205-case sample as Chaski) | 165 / 165 (100 %) | 11 / 40 (27.5 %) | `evals/ataques/resultados/juez_claude-2026-10-24-1644.json` |
| Chaski, before the bank audit (205 cases) | 165 / 165 (100 %) | 4 / 40 (10 %) | `evals/ataques/resultados/chaski-2026-10-24-1606.json` |
| **Chaski, final** (audited 952-case bank, 224-case run, fast critic: p50 2.6 s, p95 3.4 s) | **183 / 184 (99.5 %); 100 % of dose, day, negation, medicine, unit and vehicle errors** | **8 / 40 (20 %)**, about half genuinely weak family translations | `evals/ataques/resultados/chaski-2026-10-24-1740.json` |

A strong model asked "is this right?" catches the seeded errors too, but blocks more than one in four correct sentences and can't say which fact failed. Chaski blocks one in ten, and every block names the field (dose, negation, vehicle…) so the nurse knows what to fix. The weaker naive judge (Haiku) misses errors and blocks two thirds of correct sentences.
The final run has 205 cases (20 per type, plus 5 `vehiculo`). The extra type came from a real failure: on 2026-10-24
a live audit let "Tómela con agua, no con té" through with the water lost ("unu" back-translated as "uno"), so we added
the vehicle as a compared fact and the case to the bank (`evals/ataques/README.md`). Some "false blocks" are real
errors in the family's own transcription, and the README lists them. The full bank has 790 cases. The full run with
the final critic has not been done yet (`plan/checklist-acordado.md` §C).

### Interpreter: did it pick the right action?

48 scenarios across 11 categories: medicine, emergency, garbage audio, half sentences, meta questions to Chaski,
injection, bank matches, repeated ambiguity (`evals/interprete/escenarios.jsonl`).

| Main model | Correct action | Invented data (C7) | p50 latency | Source |
|---|---|---|---|---|
| **Opus 5** | **97.9 %** | **none** | 3.7 s | `evals/interprete/resultados/claude-opus-5-2026-10-24-1508.json` |
| Sonnet 5 | 93.8 % | 1 (added "paracetamol") | 2.3 s | `…/claude-sonnet-5-2026-10-24-1504.json` |
| Haiku 4.5 | 87.5 % | 1 (same case) | 2.1 s | `…/claude-haiku-4-5-20251001-2026-10-24-1500.json` |

All three runs used Haiku 4.5 as the critic. The weak spot for every model is repeated ambiguity (1/2).

### Verified-phrase retrieval (RAG for the bank and emergency mode)

216 bank phrases, 76 paraphrase queries, a local multilingual embedding model (`paraphrase-multilingual-MiniLM-L12-v2`,
ONNX on CPU) plus a lexical score, with no vector DB (`app/chaski/banco.py`).

| Method | Recall@1 | Recall@5 | p50 latency |
|---|---|---|---|
| Lexical only | 70.3 % | 85.9 % | 0.04 ms |
| Embeddings only | 76.6 % | 87.5 % | 1.86 ms |
| **Hybrid (0.7 / 0.3, set before the eval)** | **87.5 %** | **95.3 %** | 1.9 ms |

Source: `evals/banco/resultados/2026-10-24.json`.

### Speech models: what is measured and what is pending

| What | Measured | Source |
|---|---|---|
| Language ID, `facebook/mms-lid-512` | 6/6 on the synthetic test clips (`datos/prueba_minima/`), 49 ms median. Not yet measured on real clinic audio | `ricardo-artifacts/reports/arquitectura.md` |
| Quechua ASR baseline, `omniASR_LLM_300M`, 175 clips from one family speaker held out of training | WER 68.9 % / CER 15.6 % as written. **54.1 % / 11.6 %** with spelling normalized on both sides. Loanwords 5/6 | `ricardo-artifacts/reports/asr.json`, `metricas.md` |
| **Quechua ASR fine-tuned**: `mms-1b-all` quy + our adapter trained on the families' recordings (362 clips), same held-out speaker | **WER 53.9 % → 40.9 %** (normalized), a 24 % relative reduction; clips recognized perfectly **30 → 51 of 175**. Strict WER went 76.0 → 82.5 % because the model now writes normalized spelling; both are reported | commit `7b57a9b`, `ricardo-artifacts/` |
| **Translation, NLLB-200 600M fine-tuned** vs Claude, 100 held-out verified pairs | NLLB 25.78 → **31.71** chrF++ after fine-tuning (MADLAD-400-3B zero-shot: 12.69); Claude Sonnet 5: **42.31** with thinking off, **51.8** as the product runs it. Claude keeps translating (decided by this measurement) | commit `bf4a788` |
| **Quechua voice (MMS-TTS) fine-tuned** on four family speakers, including the nurse | Sounds like the speaker instead of a robot. A voice is for a patient to hear, so it is judged by a native speaker's blind test, not by our recognizer (a round trip through the recognizer, trained on human speech, scored the stock voice higher: 45.8 % vs 74.6–98.3 % WER; kept as a secondary note) | commit `ac1b924`, `ricardo-artifacts/reports/voces/` |
| Quechua ASR speed | 1.71 s for 15.8 s of audio on an A10G, 3.41 GB GPU peak | `ricardo-artifacts/reports/arquitectura.md` |
| Translation baseline (Sonnet 5, no fine-tuning) | chrF++ 42.31, BLEU 17.11, 30 pairs | `ricardo-artifacts/reports/traduccion.json` |
| **Fine-tuned ASR, NLLB and TTS** | **Pending.** Trainers exist (`ricardo-artifacts/voz/ajustar_asr.py`), but no committed results file shows an improvement yet, so we don't claim one | — |
| Whether the Chanka sounds natural | Pending. No metric covers it. The nurse decides | `ricardo-artifacts/reports/metricas.md` |

Both ASR numbers are reported on purpose. Quechua has no settled spelling, so the strict number is the
conservative one, and 14.8 WER points of it were spelling, not recognition (`metricas.md`). The test set is a whole person the model never
heard: `partir_por_hablante` raises if there are fewer than two speakers (`ricardo-artifacts/reports/arquitectura.md`).

---

## Cartesia

Cartesia is the **Spanish side**, both halves of it:

- **Ears:** `ink-whisper` behind `POST /escuchar`. Measured at **480 ms for 3.5 s of audio**, transcribing "Tome una
  pastilla cada 8 horas, después de comer" with no errors (`ricardo-artifacts/servicio/README.md`). It replaced browser
  dictation, which doesn't exist in Safari or Firefox.
- **Voice:** Sonic 3.6 speaks the Spanish output to the staff (`ricardo-artifacts/reports/arquitectura.md`).

Cartesia doesn't support Quechua, and its STT has no automatic language ID. So language ID, Quechua recognition and the
Quechua voice are our own fine-tuned Meta models, by necessity (`ricardo-artifacts/reports/arquitectura.md`).
Cartesia's speaking latency is not measured yet (same file, §8).

---

## Data, consent and known limits

- **Data comes from family volunteers who gave consent** through a mobile web form (`form/`, live at
  rimay-datos.vercel.app). Each person reads a Spanish phrase, types it in Quechua and records themselves reading it.
  The export skips anyone without consent (`form/README.md`).
- **The family voice recordings are not in this repo.** They're excluded in `.gitignore` and live on the laptop and the
  GPU instance. The `.jsonl` manifests (text only) are committed for review. The `.wav` files that are committed are
  synthetic or test samples.
- **No patient data.** No patients are recorded. Only family and staff, with their consent (`SOT.md` §8).
- **Limits we know about:**
  - Quechua bank phrases that a native speaker hasn't reviewed are never spoken. Right now that's all 216 of them.
  - The **Quechua → Spanish** direction goes through the same critic, but it **is not measured yet**.
  - Chaski's own replies to the staff (clarifying question, answer) only go through the code guards, not the critic
    (`plan/checklist-acordado.md`).
  - B1 (ASR confidence) needs per-word confidence from the Quechua ASR, which is still pending.
  - **No offline mode.** Claude, Cartesia and the GPU instance all need a network connection.
  - The Chanka number and vehicle tables in the guards still need confirmation from the nurse (`evals/ataques/README.md`).

---

## Repo map

| Path | What |
|---|---|
| `app/chaski/` | The interpreter in Python: `interprete.py` (decision), `orquestador.py` (turn, fails closed), `guardas.py` + `hechos.py` (code guards), `critico.py`, `traducir.py`, `banco.py` (RAG), `resumen.py`, `servicio.py` (route handlers) |
| `app/tests/` | Unit tests, with fake Claude clients |
| `evals/ataques/` | Attack bank (seeded errors) and results |
| `evals/interprete/` | 48 interpreter scenarios and per-model results |
| `evals/banco/` | Retrieval eval: lexical vs embeddings vs hybrid |
| `ricardo-artifacts/` | Speech models: language ID, ASR, TTS, FastAPI service (`servicio/`), vision (`/ver`), measurement scripts (`voz/`) and reports (`reports/`) |
| `movil/` | iOS app (Expo SDK 58, React Native): onboarding, consultation, prescription, emergency mode, summary |
| `form/` | Voice and text collection form (Next.js + Neon + Vercel Blob) |
| `plan/arquitectura-interprete.md` | Architecture, behavior rules C1–C9, barriers B1–B8 |
| `SOT.md` | Source of truth: product and every decision (D1–D39), in Spanish |
| `design/`, `avatar/` | Design tokens and specs. Chaski the vicuña |

## Run it

```bash
cd app && uv run pytest -q          # 306 passed in 7 s on 2026-10-24, no API calls
cd movil && npm install && npm test # app logic (node --test)
```

Evals, from `app/` (the uv project). The paid modes need `ANTHROPIC_API_KEY` in your environment and print the
estimated call count until you pass `--si`:

```bash
# attack bank (evals/ataques/README.md)
uv run python ../evals/ataques/correr.py --modo sin_barreras
uv run python ../evals/ataques/correr.py --modo juez_claude --limite 5 --si
uv run python ../evals/ataques/correr.py --modo chaski --modelo-critico claude-sonnet-5 --si

# interpreter (evals/interprete/correr.py)
uv run python ../evals/interprete/correr.py --simulado
uv run python ../evals/interprete/correr.py --modelo claude-opus-5 --si

# retrieval, local, no API (evals/banco/correr.py)
uv run python ../evals/banco/correr.py
```

`--simulado` checks the plumbing with no network, and its numbers are never quoted. **Never commit a key.** `.env` and
`.env.*` are gitignored.

---

## Team

- **Freddy Ñañez**: interpreter, guards, critic, evals, iOS app, data form.
- **Ricardo Acuña**: speech models (language ID, ASR, TTS, NLLB), fine-tuning, GPU service, measurements.

Freddy's mother is a nurse at the Pilpichaca health center. She validated the problem in an interview, and she is the
native-speaker reviewer for the Quechua that Chaski is allowed to say. Freddy's and Ricardo's parents speak Chanka and
recorded the training data.
