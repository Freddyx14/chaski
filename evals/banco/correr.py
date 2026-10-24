"""Retrieval eval for the phrase bank: lexical vs. embeddings vs. hybrid.

    cd app && uv run python ../evals/banco/correr.py

Runs locally, no API key. Reads paraphrases.jsonl (colloquial nurse wording → acceptable bank ids; an empty
list means "no bank phrase has this intent, abstain"). Each row is in `dev` or `test`.

Metrics, per method:
  - recall@1 / recall@5 over the rows that have a match (threshold-free).
  - Same-intent threshold: tuned on DEV only (maximizes the mean of "accepted and correct" on match rows and
    "abstained" on no-match rows), then reported on TEST, so the abstention number is not tuned on itself.
  - Latency per query (p50 / p95), model already loaded; model load time measured once.
Writes resultados/<YYYY-MM-DD>.json and prints a table.
"""
from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "app"))

import numpy as np  # noqa: E402

from chaski import banco as mod  # noqa: E402

MODOS = ("lexico", "embedding", "hibrido")


def cargar_casos() -> list[dict]:
    return [json.loads(l) for l in (AQUI / "paraphrases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def decidir(top: float, top_id: str, esperado: list[str], umbral: float) -> bool:
    """True if the decision at this threshold is right: accept-and-correct, or abstain on a no-match row."""
    if not esperado:
        return top < umbral
    return top >= umbral and top_id in esperado


def puntaje_umbral(filas: list[dict], umbral: float) -> float:
    con = [f for f in filas if f["esperado"]]
    sin = [f for f in filas if not f["esperado"]]
    a = np.mean([decidir(f["top"], f["top_id"], f["esperado"], umbral) for f in con]) if con else 0.0
    b = np.mean([decidir(f["top"], f["top_id"], f["esperado"], umbral) for f in sin]) if sin else 0.0
    return float((a + b) / 2)


def metricas(filas: list[dict], umbral: float) -> dict:
    con = [f for f in filas if f["esperado"]]
    sin = [f for f in filas if not f["esperado"]]
    return {
        "n_con_match": len(con),
        "n_sin_match": len(sin),
        "recall@1": round(float(np.mean([f["ids"][0] in f["esperado"] for f in con])), 3),
        "recall@5": round(float(np.mean([any(i in f["esperado"] for i in f["ids"][:5]) for f in con])), 3),
        "aceptacion_correcta": round(float(np.mean([decidir(f["top"], f["top_id"], f["esperado"], umbral) for f in con])), 3),
        "abstencion_correcta": round(float(np.mean([f["top"] < umbral for f in sin])), 3) if sin else None,
    }


def main() -> None:
    casos = cargar_casos()

    t0 = time.perf_counter()
    codificador = mod.codificador_fastembed()
    carga_modelo_s = time.perf_counter() - t0

    b = mod.Banco.desde_archivo(codificador=codificador)
    t0 = time.perf_counter()
    b.vectores()
    vectores_s = time.perf_counter() - t0
    b.puntajes("calentamiento")

    resultados: dict = {}
    for modo in MODOS:
        filas, lat = [], []
        for c in casos:
            t = time.perf_counter()
            top = b.buscar(c["texto"], k=5, modo=modo)
            lat.append((time.perf_counter() - t) * 1000)
            filas.append({**c, "ids": [it["id"] for it, _ in top], "top": top[0][1] if top else 0.0,
                          "top_id": top[0][0]["id"] if top else ""})
        dev = [f for f in filas if f["split"] == "dev"]
        test = [f for f in filas if f["split"] == "test"]
        rejilla = np.round(np.arange(0.05, 1.0, 0.01), 2)
        umbral = float(max(rejilla, key=lambda u: (puntaje_umbral(dev, u), -abs(u - 0.5))))
        resultados[modo] = {
            "umbral_dev": umbral,
            "todo": metricas(filas, umbral),
            "test": metricas(test, umbral),
            "latencia_ms": {"p50": round(statistics.median(lat), 2), "p95": round(float(np.percentile(lat, 95)), 2)},
            "fallos_recall@1": [{"texto": f["texto"], "esperado": f["esperado"], "obtenido": f["ids"][:3],
                                 "score": round(f["top"], 3)} for f in filas if f["esperado"] and f["ids"][0] not in f["esperado"]],
        }
        if modo == "hibrido":
            resultados[modo]["con_umbral_del_codigo"] = {
                "umbral": mod.UMBRAL_MISMA_INTENCION, "todo": metricas(filas, mod.UMBRAL_MISMA_INTENCION),
                "test": metricas(test, mod.UMBRAL_MISMA_INTENCION)}

    salida = {
        "fecha": dt.datetime.now().isoformat(timespec="seconds"),
        "modelo": mod.MODELO_EMBEDDING,
        "pesos": {"embedding": mod.PESO_EMBEDDING, "lexico": mod.PESO_LEXICO},
        "banco_items": len(b.items),
        "casos": len(casos),
        "carga_modelo_s": round(carga_modelo_s, 2),
        "vectores_banco_s": round(vectores_s, 3),
        "modos": resultados,
    }
    destino = AQUI / "resultados" / f"{dt.date.today().isoformat()}.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"bank {len(b.items)} items · {len(casos)} cases · model load {carga_modelo_s:.2f}s · bank vectors {vectores_s*1000:.0f} ms")
    print(f"{'method':<10} {'R@1':>6} {'R@5':>6} {'thr(dev)':>9} {'accept✓ test':>13} {'abstain✓ test':>14} {'p50 ms':>7} {'p95 ms':>7}")
    for modo, r in resultados.items():
        print(f"{modo:<10} {r['todo']['recall@1']:>6.3f} {r['todo']['recall@5']:>6.3f} {r['umbral_dev']:>9.2f} "
              f"{r['test']['aceptacion_correcta']:>13.3f} {r['test']['abstencion_correcta']:>14.3f} "
              f"{r['latencia_ms']['p50']:>7.2f} {r['latencia_ms']['p95']:>7.2f}")
    h = resultados["hibrido"]["con_umbral_del_codigo"]
    print(f"hybrid at code threshold {h['umbral']}: accept✓ {h['todo']['aceptacion_correcta']:.3f} · "
          f"abstain✓ {h['todo']['abstencion_correcta']:.3f} (all rows)")
    print(f"→ {destino}")


if __name__ == "__main__":
    main()
