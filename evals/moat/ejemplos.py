"""Moat step 1: does giving the translator the most similar VERIFIED pairs as examples (retrieval-augmented few-shot)
beat the same translator without them? Same sets and metrics as evals/traduccion/comparar.py.

    cd app
    ANTHROPIC_API_KEY="$(secretctl get CHASKI_ANTHROPIC_API_KEY)" uv run --with sacrebleu python ../evals/moat/ejemplos.py

Conditions (translator = the product's: Claude Sonnet 5, medium effort, product prompt + glossary):
  base         no examples
  enfermera    top-5 from the 24 phrases the nurse reviewed
  verificadas  top-5 from every verified pair: the bank (216, incl. the CMP 2020 semiology text) + Ricardo's verified
               pairs outside the 30 under test (70)
Retrieval is the product's hybrid search (chaski.banco: embeddings + lexical). quy→spa searches the Quechua side.

LEAKAGE GUARD (the failure that voided the NLLB fine-tune, 2fac55f): for each test set, every memory item is dropped if
its Spanish equals a test sentence (normalized), its Quechua equals any test reference, or its Spanish embedding is
≥ 0.92 cosine to any test sentence. The run prints how many were dropped. Writes resultados/ejemplos-<fecha>.json.
"""
from __future__ import annotations

import concurrent.futures as fut
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import numpy as np
import sacrebleu

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
from chaski import banco as bmod  # noqa: E402
from chaski import guardas as g  # noqa: E402
from chaski import traducir as t  # noqa: E402

K = 5
UMBRAL_FUGA = 0.92
GLOS = "\n".join(f"- {x['castellano']} → {x['quechua']}" for x in t.cargar_glosario())


def memoria():
    items = [{"id": it["id"], "es": it["es"], "quy": it["quy"], "enfermera": it.get("revisado") is True}
             for it in bmod.cargar_items() if it.get("quy", "").strip()]
    ver = json.loads((RAIZ / "ricardo-artifacts/datos/frases/frases.json").read_text())["verificadas"]
    items += [{"id": f"ric-{i}", "es": p["castellano"], "quy": p["chanka"], "enfermera": False}
              for i, p in enumerate(ver) if i >= 30]
    return items


def sets():
    fam = json.loads((RAIZ / "ricardo-artifacts/datos/frases/evaluacion_familias.json").read_text())["pares"]
    r30 = json.loads((RAIZ / "ricardo-artifacts/datos/frases/frases.json").read_text())["verificadas"][:30]
    return {
        "familias": ("spa", "quy", [(p["castellano"], p["referencias"], p["castellano"]) for p in fam]),
        "familias_inv": ("quy", "spa", [(p["referencias"][0], [p["castellano"]], p["castellano"]) for p in fam]),
        "ricardo30": ("spa", "quy", [(p["castellano"], [p["chanka"]], p["castellano"]) for p in r30]),
    }


def sin_fugas(items, filas, cod):
    """Drop memory items that are (or nearly are) a test sentence. Returns (kept, dropped_count)."""
    es_test = {bmod.normalizar(f[2]) for f in filas}
    refs = {bmod.normalizar(r) for f in filas for r in (f[1] if f[1] and f[2] != f[1][0] else [])}
    refs |= {bmod.normalizar(f[0]) for f in filas}  # the Quechua sources of the reverse set, too
    vt = bmod._unitarios(cod([f[2] for f in filas]))
    vm = bmod._unitarios(cod([it["es"] for it in items]))
    cerca = (vm @ vt.T).max(axis=1) >= UMBRAL_FUGA
    quedan = [it for it, c in zip(items, cerca)
              if not c and bmod.normalizar(it["es"]) not in es_test and bmod.normalizar(it["quy"]) not in refs]
    return quedan, len(items) - len(quedan)


def indice(items, lado, cod):
    return bmod.Banco([{**it, "es": it[lado]} for it in items], codificador=cod)


def traducir(cli, texto, de, a, ejemplos):
    bloque = ""
    if ejemplos:
        pares = "\n".join(f"- {x['es']} → {x['quy']}" if de == "spa" else f"- {x['quy']} → {x['es']}" for x in ejemplos)
        bloque = ("Ejemplos verificados por hablantes nativos (frases parecidas, ya revisadas). Úsalos para el "
                  f"vocabulario y el registro; no copies datos que el texto no dice:\n{pares}\n\n")
    t0 = time.perf_counter()
    r = cli.messages.parse(model=t.MODELO, max_tokens=1500, output_format=t._Salida, **t.opciones_pensar("medium"),
                           system=[{"type": "text", "text": t.SISTEMA[(de, a)], "cache_control": {"type": "ephemeral"}}],
                           messages=[{"role": "user", "content": f"Glosario revisado por una hablante nativa:\n{GLOS}\n\n"
                                      f"{bloque}<texto>\n{texto}\n</texto>"}])
    return r.parsed_output.traduccion.strip(), round((time.perf_counter() - t0) * 1000)


def puntuar(hips, refs):
    ancho = max(len(r) for r in refs)
    cols = [[r[i] if i < len(r) else r[0] for r in refs] for i in range(ancho)]
    return round(sacrebleu.CHRF(word_order=2).corpus_score(hips, cols).score, 2)


def main():
    cli = anthropic.Anthropic()
    cod = bmod.codificador_fastembed()
    todo = memoria()
    out = {}
    for s, (de, a, filas) in sets().items():
        limpio, caidos = sin_fugas(todo, filas, cod)
        pools = {"base": None, "enfermera": [it for it in limpio if it["enfermera"]], "verificadas": limpio}
        lado = "es" if de == "spa" else "quy"
        out[s] = {"memoria_descartada_por_fuga": caidos}
        for cond, pool in pools.items():
            idx = indice(pool, lado, cod) if pool else None

            def uno(f):
                ej = [it for it, _ in idx.buscar(f[0], k=K)] if idx else []
                ej = [next(p for p in pool if p["id"] == e["id"]) for e in ej]
                for intento in range(3):
                    try:
                        h, ms = traducir(cli, f[0], de, a, ej)
                        return h, ms, [e["id"] for e in ej]
                    except Exception:  # noqa: BLE001
                        time.sleep(2 + intento)
                return "", None, [e["id"] for e in ej]

            with fut.ThreadPoolExecutor(max_workers=6) as pool_:
                res = list(pool_.map(uno, filas))
            hips = [r[0] for r in res]
            ms = sorted(r[1] for r in res if r[1])
            b4 = sum(1 for f, h in zip(filas, hips) if h and not g.terminos_fijos(f[0], h).ok) if de == "spa" else None
            out[s][cond] = {"chrf2": puntuar(hips, [f[1] for f in filas]), "b4_frenadas": b4,
                            "ms_p50": ms[len(ms) // 2] if ms else None, "memoria": len(pool or []),
                            "salidas": [{"src": f[0], "hip": h, "ejemplos": r[2]} for f, h, r in zip(filas, hips, res)]}
            print(s, cond, {k: v for k, v in out[s][cond].items() if k != "salidas"}, "fugas descartadas:", caidos, flush=True)
    d = Path(__file__).with_name("resultados"); d.mkdir(exist_ok=True)
    (d / f"ejemplos-{datetime.now():%Y%m%d-%H%M}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
