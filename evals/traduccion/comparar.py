"""Which translator: Claude Sonnet 5, Gemini 3 Flash, Gemini 3.8 Flash, DeepSeek V3.2, NLLB-1.3B, on the same sets.

    cd app
    ANTHROPIC_API_KEY="$(secretctl get CHASKI_ANTHROPIC_API_KEY)" OPENROUTER_API_KEY="$(secretctl get OPENROUTER_API_KEY)" \
        uv run --with sacrebleu python ../evals/traduccion/comparar.py

Sets (none seen by any published model):
  familias      62 Spanish phrases the families translated on 24-oct, ~4.8 Chanka references each (spa→quy)
  familias_inv  the same 62, first Chanka version → Spanish (quy→spa)
  ricardo30     Ricardo's 30 verified pairs (spa→quy), the set behind the 42.31 / 51.8
Every chat model gets the product prompt and glossary (chaski.traducir). Besides chrF++ it counts how many spa→quy
outputs the code barrier B4 would stop (number, negation, medicine, unit, «con agua» lost): what decides whether the
patient hears it or gets «no pude». Writes resultados/comparar-<fecha>.json.
"""
from __future__ import annotations

import concurrent.futures as fut
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import httpx
import sacrebleu

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
from chaski import guardas as g  # noqa: E402
from chaski import traducir as t  # noqa: E402

URL = json.loads((RAIZ / "ricardo-artifacts/servicio/url.json").read_text())["url"].rstrip("/")
GLOS = "\n".join(f"- {x['castellano']} → {x['quechua']}" for x in t.cargar_glosario())
OPENROUTER = {"gemini-3-flash": "google/gemini-3-flash-preview", "gemini-3.8-flash": "google/gemini-3.8-flash",
              "deepseek-v3.2": "deepseek/deepseek-v3.2"}
NLLB = {"spa": "spa_Latn", "quy": "quy_Latn"}


def contenido(texto):
    return f"Glosario revisado por una hablante nativa:\n{GLOS}\n\n<texto>\n{texto}\n</texto>"


def claude(cli, pensar=None):
    def f(texto, de, a):
        r = cli.messages.parse(model=t.MODELO, max_tokens=1500, output_format=t._Salida, **t.opciones_pensar(pensar),
                               system=[{"type": "text", "text": t.SISTEMA[(de, a)], "cache_control": {"type": "ephemeral"}}],
                               messages=[{"role": "user", "content": contenido(texto)}])
        return r.parsed_output.traduccion.strip(), None
    return f


def openrouter(modelo, http):
    def f(texto, de, a):
        r = http.post("https://openrouter.ai/api/v1/chat/completions", json={
            "model": modelo, "usage": {"include": True},
            "messages": [{"role": "system", "content": t.SISTEMA[(de, a)] + " Responde SOLO con la traducción, en una "
                          "línea, sin comillas ni notas."}, {"role": "user", "content": contenido(texto)}]})
        r.raise_for_status()
        j = r.json()
        return j["choices"][0]["message"]["content"].strip().strip('"'), (j.get("usage") or {}).get("cost")
    return f


def nllb(http):
    def f(texto, de, a):
        r = http.post(f"{URL}/mt", data={"texto": texto, "desde": NLLB[de], "hacia": NLLB[a]},
                      headers={"ngrok-skip-browser-warning": "1"})
        r.raise_for_status()
        return r.json()["traduccion"].strip(), 0.0
    return f


def sets():
    fam = json.loads((RAIZ / "ricardo-artifacts/datos/frases/evaluacion_familias.json").read_text())["pares"]
    r30 = json.loads((RAIZ / "ricardo-artifacts/datos/frases/frases.json").read_text())["verificadas"][:30]
    return {
        "familias": ("spa", "quy", [(p["castellano"], p["referencias"]) for p in fam]),
        "familias_inv": ("quy", "spa", [(p["referencias"][0], [p["castellano"]]) for p in fam]),
        "ricardo30": ("spa", "quy", [(p["castellano"], [p["chanka"]]) for p in r30]),
    }


def puntuar(hips, refs):
    ancho = max(len(r) for r in refs)
    cols = [[r[i] if i < len(r) else r[0] for r in refs] for i in range(ancho)]
    return round(sacrebleu.CHRF(word_order=2).corpus_score(hips, cols).score, 2)


def correr_uno(fn, texto, de, a):
    for intento in range(3):
        t0 = time.perf_counter()
        try:
            salida, costo = fn(texto, de, a)
            return salida, round((time.perf_counter() - t0) * 1000), costo
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"[:200]
            time.sleep(1 + intento)
    return None, None, err


def evaluar(nombre, fn):
    out = {}
    for s, (de, a, filas) in sets().items():
        with fut.ThreadPoolExecutor(max_workers=6) as pool:
            res = list(pool.map(lambda x: correr_uno(fn, x[0], de, a), filas))
        hips = [r[0] or "" for r in res]
        fallos = sum(r[0] is None for r in res)
        ms = sorted(r[1] for r in res if r[1] is not None)
        b4 = None
        if (de, a) == ("spa", "quy"):
            b4 = sum(1 for (es, _), h in zip(filas, hips) if h and not g.terminos_fijos(es, h).ok)
        costos = [r[2] for r in res if isinstance(r[2], (int, float))]
        out[s] = {"chrf2": puntuar(hips, [r for _, r in filas]), "n": len(filas), "fallos_llamada": fallos,
                  "ms_p50": ms[len(ms) // 2] if ms else None, "ms_p95": ms[int(.95 * (len(ms) - 1))] if ms else None,
                  "b4_frenadas": b4, "costo_usd": round(sum(costos), 4) if costos else None,
                  "salidas": [{"src": x[0], "hip": h} for x, h in zip(filas, hips)]}
        print(nombre, s, {k: v for k, v in out[s].items() if k != "salidas"}, flush=True)
    return out


def main():
    http = httpx.Client(timeout=120, headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
    mt = httpx.Client(timeout=120)
    cli = anthropic.Anthropic()
    sistemas = {"claude-sonnet-5": claude(cli), "claude-sonnet-5-sin-pensar": claude(cli, "no"),
                "claude-sonnet-5-medium": claude(cli, "medium"), "nllb-1.3B": nllb(mt),
                **{k: openrouter(v, http) for k, v in OPENROUTER.items()}}
    solo = sys.argv[1:]  # e.g. `claude-sonnet-5-sin-pensar` to run some systems only
    sistemas = {k: v for k, v in sistemas.items() if not solo or k in solo}
    with fut.ThreadPoolExecutor(max_workers=len(sistemas)) as pool:
        res = dict(zip(sistemas, pool.map(lambda kv: evaluar(*kv), sistemas.items())))
    print("\n| sistema | " + " | ".join(f"{s} chrF++" for s in sets()) + " | B4 frenadas (spa→quy) | p50 ms | costo |")
    for k, v in res.items():
        b4 = sum((v[s]["b4_frenadas"] or 0) for s in v if v[s]["b4_frenadas"] is not None)
        n = sum(v[s]["n"] for s in v if v[s]["b4_frenadas"] is not None)
        costo = sum(v[s]["costo_usd"] or 0 for s in v)
        print(f"| {k} | " + " | ".join(str(v[s]["chrf2"]) for s in sets()) + f" | {b4}/{n} | {v['familias']['ms_p50']} | ${costo:.3f} |")
    d = Path(__file__).with_name("resultados"); d.mkdir(exist_ok=True)
    (d / f"comparar-{datetime.now():%Y%m%d-%H%M}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
