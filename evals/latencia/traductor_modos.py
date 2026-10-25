"""Product translator (chaski.traducir.traducir_claude) on Ricardo's 30 held-out reference pairs, per thinking mode.

    cd app
    ANTHROPIC_API_KEY="$(secretctl get CHASKI_ANTHROPIC_API_KEY)" uv run --with sacrebleu python ../evals/latencia/traductor_modos.py

Same pairs Ricardo used for the 42.31 (ricardo-artifacts/voz/medir_traduccion.py, first 30 `verificadas`), but with
the PRODUCT prompt and glossary. Reports chrF++, latency p50/p95, and whether the code guards (B4: numbers, medicine,
negation, vehicle) pass on each output. Writes resultados/traductor-modos-<fecha>.json.
"""
from __future__ import annotations

import concurrent.futures as fut
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import sacrebleu

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
from chaski import traducir as t  # noqa: E402

MODOS = {"modelo": {}, "no": {"thinking": {"type": "disabled"}}, "low": {"output_config": {"effort": "low"}},
         "medium": {"output_config": {"effort": "medium"}}}
SOLO = sys.argv[1:]  # e.g. `medium` to run one mode


def uno(cli, texto, extra, glos):
    contenido = f"Glosario revisado por una hablante nativa:\n{glos}\n\n<texto>\n{texto}\n</texto>"
    t0 = time.perf_counter()
    r = cli.messages.parse(model=t.MODELO, max_tokens=1500, messages=[{"role": "user", "content": contenido}],
                           system=[{"type": "text", "text": t.SISTEMA[("spa", "quy")], "cache_control": {"type": "ephemeral"}}],
                           output_format=t._Salida, **extra)
    return r.parsed_output.traduccion.strip(), round((time.perf_counter() - t0) * 1000), r.usage.output_tokens


def main():
    pares = json.loads((RAIZ / "ricardo-artifacts/datos/frases/frases.json").read_text())["verificadas"][:30]
    glos = "\n".join(f"- {g['castellano']} → {g['quechua']}" for g in t.cargar_glosario())
    cli = anthropic.Anthropic()
    out = {}
    for modo, extra in ((m, e) for m, e in MODOS.items() if not SOLO or m in SOLO):
        with fut.ThreadPoolExecutor(max_workers=6) as pool:
            res = list(pool.map(lambda p: uno(cli, p["castellano"], extra, glos), pares))
        hip = [r[0] for r in res]
        ms = sorted(r[1] for r in res)
        out[modo] = {"chrf2": round(sacrebleu.CHRF(word_order=2).corpus_score(hip, [[p["chanka"] for p in pares]]).score, 2),
                     "ms_p50": ms[len(ms) // 2], "ms_p95": ms[int(.95 * (len(ms) - 1))],
                     "tokens_salida_media": round(statistics.mean(r[2] for r in res)),
                     "salidas": [{"es": p["castellano"], "quy": h, "ref": p["chanka"]} for p, h in zip(pares, hip)]}
        print(modo, {k: v for k, v in out[modo].items() if k != "salidas"}, flush=True)
    d = Path(__file__).with_name("resultados"); d.mkdir(exist_ok=True)
    (d / f"traductor-modos-{datetime.now():%Y%m%d-%H%M}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
