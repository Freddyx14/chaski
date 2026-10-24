# Attack bank: does the audit catch the errors we plant?

The barriers of `plan/arquitectura-interprete.md` §2b only matter if they stop wrong sentences. This bank
plants errors on purpose and counts how many get through. It produces the pitch number,
**«the audit caught X of Y seeded errors»**, plus the number that keeps that honest. That second one is
how many CORRECT sentences it blocked by mistake.

## What it measures

`banco.jsonl` has one case per line: `{id, tipo, es, quy, mutacion, esperado, fuente}` (polish cases
also carry `pulido`). Built from real phrase pairs: the family-written Chanka in the form
(`data/formulario/manifest.jsonl`, only rows with a transcription, text only, never audio) and the 100
`verificadas` in `ricardo-artifacts/datos/frases/frases.json`.

| tipo | what was changed (always on the Quechua side) | expected |
|---|---|---|
| `limpio` | nothing, it's the original pair | pass |
| `numero` | a number swapped through the Chanka table (`pusaq` → `suqta`) | block |
| `dias` | the number of a duration swapped (`qanchis punchaw` → `kimsa punchaw`) | block |
| `negacion` | `ama` / `mana` / `-chu` removed | block |
| `medicamento` | the medicine loanword swapped for another | block |
| `unidad` | `pastilla` ↔ `kuchara`, `sutu` → `pastilla` | block |
| `agrega_consejo` / `agrega_diagnostico` | a family-written sentence appended that the Spanish never said | block |
| `pulido_agrega` | the polished Spanish adds a fact (days, frequency, a medicine, «después de comer») | block |
| `pulido_limpio` | the polish only removes filler («eh, este…») | pass |

Current bank (seed 13). 784 cases, 396 seeded errors and 388 correct ones: limpio 326 · numero 29 · dias 21 ·
negacion 21 · medicamento 38 · unidad 33 · agrega_consejo 103 · agrega_diagnostico 95 · pulido_agrega 56 ·
pulido_limpio 62.

## Why the false blocks on `limpio` matter

A system that blocks everything catches 100 % of the errors and never helps a single patient. The catch
rate means nothing without the false-block rate next to it. Every blocked correct sentence is a
nurse who falls back to gestures. Always report both.

## How to run

From `app/` (the uv project):

```bash
uv run python ../evals/ataques/construir.py                                   # rebuild banco.jsonl
uv run python ../evals/ataques/correr.py --modo sin_barreras                  # the floor, 0 % caught
uv run python ../evals/ataques/correr.py --modo chaski --simulado             # no network, tests plumbing
uv run python ../evals/ataques/correr.py --modo juez_claude --limite 5 --si   # naive baseline
uv run python ../evals/ataques/correr.py --modo chaski --limite 5 --si        # the real checks, critic on Haiku
uv run python ../evals/ataques/correr.py --modo chaski --modelo-critico <sonnet-id> --si   # Haiku vs Sonnet
```

- `juez_claude` is one call per case asking «is this a faithful translation? yes/no». That's what most
  teams would do. `chaski` is the critic in `app/chaski/critico.py` (blind back-translation, fact
  extraction, added-content list; 4 calls per translation, 3 per polish) and the plain code that decides on
  it (B2–B5 in `chaski.guardas` / `chaski.hechos`).
- The paid modes need `ANTHROPIC_API_KEY`. Without `--si` they print the estimated call count and stop.
- `--limite N` takes the first N cases **of each type**. A cheap run still covers every type.
- Results go to `resultados/<modo>-<fecha>.json`, with the critic or judge model recorded.
  Simulated runs get a `-simulado` suffix and are not committed.
- `--simulado` returns empty facts and «faithful» to everything. A simulated `chaski` run measures
  only the plain-code layers. **The pitch number comes from a real run, never from a simulated one.**

## Caveats

- **Family transcriptions have spelling variation** (`pusaq/pusac/pusacc`, `kimsa/kinsa/quimsa`,
  `Pareceracetanolta`). The number table and the fuzzy loanword match absorb most of it. The table
  is standard Quechua numerals plus the spellings seen in the form, and it still has to be confirmed by
  the nurse.
- **Some `limpio` pairs really are wrong.** In the simulated run, the 6 "false blocks" are all errors
  in the family's own transcription. Two write *treinta y nueve* as 38 and 19, one writes *ocho* as
  *esqon* (9), one has a *doce* the table can't read, one spells paracetamol beyond recognition, and
  *«Media pastilla, no entera»* is written without the «no entera». Read the blocked `limpio` ids before
  quoting a false-block rate. Some of them are catches.
- The mechanical mutations use the same number table as the B4 guard. So B4 catching them is expected,
  and the honest test of B4 is the false-block rate on `limpio`. The added-content cases and
  «después de comer» can only be caught by the critic, so they need a real run.
- A changed addressee («dele a su hijo» vs «tome usted») is checked by the critic but has no mutation
  in the bank yet.
