"""End to end on the LIVE service with real Quechua audio: what the app does on a patient turn, measured.

    cd app && uv run --with sacrebleu python ../evals/vivo/paciente_real.py --n 40

Audio: speaker p16, the one the fine-tuned recognizer never heard (commit 7b57a9b), from the families' form
(data/formulario/, gitignored). Each clip carries what the person meant in Spanish, which is the reference.
POST /turno/paciente exactly as the app sends it. Reports said / asked to repeat / blocked, chrF++ of the Spanish
against the reference, whether every number in the reference survived, and the wall time.
Writes resultados/paciente-real-<fecha>.json (the transcripts stay local, in data/).
"""
from __future__ import annotations

import argparse
import concurrent.futures as fut
import json
import random
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

import sacrebleu

RAIZ = Path(__file__).resolve().parents[2]
URL = json.loads((RAIZ / "ricardo-artifacts/servicio/url.json").read_text())["url"].rstrip("/")
NUM = {"uno": 1, "una": 1, "un": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
       "nueve": 9, "diez": 10, "once": 11, "doce": 12, "quince": 15, "veinte": 20, "treinta": 30}


def numeros(texto: str) -> set[int]:
    t = texto.lower()
    out = {int(x) for x in re.findall(r"\d+", t)}
    out |= {v for k, v in NUM.items() if re.search(rf"\b{k}\b", t) and v > 1}
    return out


def archivo_de(fila) -> Path:
    """The clip's file. Its number is the one in the audio URL (…/p16/042-xxxx.webm), NOT `numero`, which counts within
    a block: using `numero` sent the wrong clip for most rows (first run, 02:30, discarded)."""
    m = re.search(r"/(\d{3})-", fila.get("audio") or "")
    return RAIZ / "data/formulario" / fila["persona"] / f"{m.group(1) if m else '000'}.webm"


def turno(fila):
    archivo = archivo_de(fila)
    t0 = time.perf_counter()
    out = subprocess.run(["curl", "-s", "-m", "180", "-H", "ngrok-skip-browser-warning: 1", "-X", "POST",
                          f"{URL}/turno/paciente", "-F", f"audio=@{archivo};type=audio/webm"],
                         capture_output=True, text=True).stdout
    s = round(time.perf_counter() - t0, 1)
    try:
        r = json.loads(out)
    except json.JSONDecodeError:
        return {"id": fila["numero"], "estado": "error_red", "s": s}
    estado = r.get("estado") or ("error" if r.get("error") else "?")
    if r.get("accion") in ("no_entendi", "repreguntar") and r.get("para") == "paciente":
        estado = "pidio_repetir"
    salida = r.get("texto_salida") or ""
    ref = fila["castellano"]
    faltan = sorted(numeros(ref) - numeros(salida)) if estado.startswith("dicho") else None
    return {"id": fila["numero"], "estado": estado, "accion": r.get("accion"), "s": s, "ref": ref,
            "oido": r.get("texto_original"), "salida": salida, "motivo": r.get("motivo"),
            "numeros_faltan": faltan, "error": r.get("error")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--persona", default="p16")
    a = ap.parse_args()
    filas = [json.loads(l) for l in (RAIZ / "data/formulario/manifest.jsonl").read_text().splitlines() if l.strip()]
    filas = [f for f in filas if f["persona"] == a.persona and f.get("castellano", "").strip()
             and archivo_de(f).exists()]
    random.Random(25).shuffle(filas)
    filas = filas[: a.n]
    with fut.ThreadPoolExecutor(max_workers=1) as pool:
        res = list(pool.map(turno, filas))
    dichos = [r for r in res if r["estado"].startswith("dicho")]
    cuenta = {}
    for r in res:
        cuenta[r["estado"]] = cuenta.get(r["estado"], 0) + 1
    chrf = round(sacrebleu.CHRF(word_order=2).corpus_score([r["salida"] for r in dichos], [[r["ref"] for r in dichos]]).score, 2) if dichos else None
    con_numero = [r for r in dichos if numeros(r["ref"])]
    s = sorted(r["s"] for r in res if r["estado"] != "error_red")
    resumen = {"turnos": len(res), "estados": cuenta, "chrf2_dichos_vs_lo_que_quiso_decir": chrf,
               "numeros_intactos": f"{sum(not r['numeros_faltan'] for r in con_numero)}/{len(con_numero)}",
               "s_p50": s[len(s) // 2] if s else None, "s_p95": s[int(.95 * (len(s) - 1))] if s else None}
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    for r in res:
        if r["estado"].startswith("dicho") and r["numeros_faltan"]:
            print("  ⚠ número perdido:", r["ref"], "→", r["salida"])
    d = Path(__file__).with_name("resultados"); d.mkdir(exist_ok=True)
    (d / f"paciente-real-{datetime.now():%Y%m%d-%H%M}.json").write_text(
        json.dumps({"resumen": resumen, "turnos": [{k: v for k, v in r.items() if k not in ("oido",)} for r in res]},
                   ensure_ascii=False, indent=1))
    (RAIZ / "data" / f"paciente-real-transcripciones-{datetime.now():%Y%m%d-%H%M}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
