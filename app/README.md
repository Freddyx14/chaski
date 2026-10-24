# Rimay — app

Health-post instructions in Chanka Quechua, audited before they reach a patient. Product: `../ideas/producto.md`.

## Run

```bash
cd app
export ANTHROPIC_API_KEY=...        # the Cal Hacks credits key; never commit it
uv run pytest -q                    # no network, no cost
uv run python -m rimay.cli "Tome una pastilla de sulfato ferroso cada día después del almuerzo, durante un mes."
```

## What's here

| Path | What |
|---|---|
| `rimay/hechos.py` | Critical facts of an instruction (medicine, dose, frequency, days, next visit, warning signs) and the **deterministic** comparison |
| `rimay/auditoria.py` | Extract → translate to Chanka → back-translate blind → extract → compare → send or block |
| `rimay/cli.py` | Try it from the terminal |
| `rimay/glosario.json` | Spanish → Chanka terms **reviewed by a native speaker**. Only a human adds entries |

Model: `claude-opus-5` via `messages.parse` (structured outputs). A refusal or empty output raises `SinRespuesta` and nothing is sent.
