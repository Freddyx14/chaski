"""Jev (TypeSafe System One) as Chaski's decision step: one call per turn, typed answers, scored on the same 48
labeled scenarios Opus was measured on (evals/interprete/escenarios.jsonl). A backup study (Freddy, 22:50), not the
product: it answers whether the LABEL part of the interpreter can be deterministic and near-instant.

    cd app
    uv run python ../evals/jev/correr.py

Jev only returns labels, so it is asked: which of the 5 actions, which missing fact (repreguntar), and which bank
candidate (usar_frase_banco). Who it is for is derived in code. It cannot write the polish, the follow-up question or
an answer: in the deterministic design those come from templates (repreguntar), the bank, or an LLM (responder).
The TypeSafe key is read at call time with secretctl and never printed. Writes resultados/jev-<fecha>.json.
"""
from __future__ import annotations

import concurrent.futures as fut
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
from chaski import orquestador as o  # noqa: E402
from chaski.interprete import TEMAS  # noqa: E402

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
SECRETCTL = os.path.expanduser("~/.claude/security/secretctl")

ACCIONES = {
    "traducir": "Lo dicho es para la otra persona (personal ↔ paciente) y está completo: hay que pasarlo a su idioma.",
    "repreguntar": "Le falta un dato crítico (qué medicamento, cuánto, cada cuánto, qué parte del cuerpo…) o hay una "
                   "ambigüedad que cambia la indicación: hay que preguntarle a quien habló antes de traducir.",
    "responder": "La pregunta es para el intérprete Chaski, no para la otra persona: «¿qué dijo?», «¿entendió?», "
                 "«repítele», «¿cómo se dice…?».",
    "no_entendi": "Ruido, silencio, sílabas sueltas, una frase sin sentido, o una frase cortada justo donde iba el dato.",
    "usar_frase_banco": "Habla el personal y una de `candidatas` dice EXACTAMENTE la misma intención (no una parecida).",
}


def clave() -> str:
    return subprocess.run([SECRETCTL if os.path.exists(SECRETCTL) else "secretctl", "get", "TYPESAFE_API_KEY"],
                          capture_output=True, text=True, check=True).stdout.strip()


def preguntar(key, state, questions):
    body = json.dumps({"state": state, "model": "jev-latest", "questions": questions}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r), round((time.perf_counter() - t0) * 1000)


def candidatas(c):
    t = c["turno"]
    if t.get("candidatas"):
        return t["candidatas"]
    if t.get("rol") == "personal" and t.get("idioma") == "spa":
        return [{"id": x["id"], "es": x["es"]} for x in o.candidatos_servibles(t["texto"])][:8]
    return []


def uno(key, c):
    t = c["turno"]
    cands = candidatas(c)
    historial = [f"{h['rol']}: {h['texto']}" for h in (c.get("contexto") or {}).get("historial", [])]
    state = {"habla": t["rol"], "idioma": "castellano" if t["idioma"] == "spa" else "quechua chanka",
             "dicho": t["texto"], "historial": historial, "candidatas": [f"{x['id']}: {x['es']}" for x in cands]}
    q = {
        "accion": {"type": "choice", "criteria": ACCIONES, "instructions":
                   "Eres intérprete en una posta de salud entre personal (castellano) y paciente (quechua). Qué hacer "
                   "con `dicho`, que acaba de decir `habla`. Usa `historial` para saber si es una pregunta para ti."},
        "dato_faltante": {"type": "choice", "instructions": "Si a `dicho` le falta un dato crítico para poder "
                          "traducirlo sin riesgo, cuál es. Si no falta nada, ninguno.",
                          "criteria": {**{x: x.replace("_", " ") for x in TEMAS}, "ninguno": "No falta ningún dato."}},
    }
    if cands:
        q["frase_banco"] = {"type": "choice", "instructions": "Cuál de las `candidatas` dice EXACTAMENTE lo mismo que "
                            "`dicho` (misma intención, no parecida). Si ninguna, ninguna.",
                            "criteria": {**{x["id"]: x["es"] for x in cands}, "ninguna": "Ninguna dice lo mismo."}}
    r, ms = preguntar(key, state, q)
    a = r["answers"]
    accion = a["accion"]["choice"]
    banco = a.get("frase_banco", {}).get("choice")
    final = accion
    if accion == "usar_frase_banco" and (not banco or banco == "ninguna"):
        final = "traducir"  # deterministic rule: no exact phrase → translate what was said
    esperado = c["esperado"]["accion"]
    esperado = esperado if isinstance(esperado, list) else [esperado]
    fila = {"id": c["id"], "categoria": c["categoria"], "esperado": esperado, "jev": accion, "final": final,
            "ok": final in esperado, "confianza": a["accion"].get("confidence"),
            "probabilidades": a["accion"].get("probabilities"), "ms": ms,
            "tokens": r.get("usage", {}).get("input_tokens")}
    if c["esperado"].get("frase_banco_id"):
        fila["banco_ok"] = banco == c["esperado"]["frase_banco_id"]
        fila["banco_jev"] = banco
    if c["esperado"].get("dato_faltante"):
        fila["dato_ok"] = a["dato_faltante"]["choice"] in c["esperado"]["dato_faltante"]
        fila["dato_jev"] = a["dato_faltante"]["choice"]
    return fila


def main():
    casos = [json.loads(l) for l in (RAIZ / "evals/interprete/escenarios.jsonl").read_text().splitlines() if l.strip()]
    key = clave()
    with fut.ThreadPoolExecutor(max_workers=6) as pool:
        filas = list(pool.map(lambda c: uno(key, c), casos))
    ok = sum(f["ok"] for f in filas)
    ms = sorted(f["ms"] for f in filas)
    por_cat = {}
    for f in filas:
        por_cat.setdefault(f["categoria"], []).append(f["ok"])
    resumen = {"casos": len(filas), "accion_correcta": f"{ok}/{len(filas)} = {100 * ok / len(filas):.0f}%",
               "por_categoria": {k: f"{sum(v)}/{len(v)}" for k, v in sorted(por_cat.items())},
               "banco": f"{sum(f['banco_ok'] for f in filas if 'banco_ok' in f)}/{sum('banco_ok' in f for f in filas)}",
               "dato_faltante": f"{sum(f['dato_ok'] for f in filas if 'dato_ok' in f)}/{sum('dato_ok' in f for f in filas)}",
               "ms_p50": ms[len(ms) // 2], "ms_p95": ms[int(.95 * (len(ms) - 1))],
               "tokens_entrada_total": sum(f["tokens"] or 0 for f in filas)}
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    for f in filas:
        if not f["ok"]:
            print("  ✗", f["id"], "esperado", f["esperado"], "jev", f["jev"], "→", f["final"], f"conf {f['confianza']}")
    d = Path(__file__).with_name("resultados"); d.mkdir(exist_ok=True)
    (d / f"jev-{datetime.now():%Y%m%d-%H%M}.json").write_text(json.dumps({"resumen": resumen, "filas": filas},
                                                                       ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
