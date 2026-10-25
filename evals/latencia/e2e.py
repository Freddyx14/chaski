"""Real end-to-end turn latency: the voice legs on Ricardo's live service + the interpreter run locally.

    cd app
    ANTHROPIC_API_KEY="$(secretctl get CHASKI_ANTHROPIC_API_KEY)" uv run python ../evals/latencia/e2e.py --n 16

Staff turn  = /escuchar (Spanish audio -> text, Cartesia) + interpretar() (Opus decide, translate, guards, critic)
              + /voz (Quechua text -> wav, fine-tuned MMS-TTS).
Patient turn = /idioma + /turno/paciente (Quechua audio -> Spanish text), measured warm.
Turns run one at a time (that is what a person waits for). Writes resultados/e2e-<fecha>.json.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import anthropic
import httpx

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
from chaski import orquestador as o  # noqa: E402

URL = json.loads((RAIZ / "ricardo-artifacts/servicio/url.json").read_text())["url"].rstrip("/")
CAB = {"ngrok-skip-browser-warning": "1"}


def pct(xs: list[float], p: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))], 1)


def audio_es(texto: str, carpeta: Path, i: int) -> bytes:
    """Spanish speech for the staff leg: macOS `say` (es_MX) -> 16 kHz mono wav."""
    aiff, wav = carpeta / f"{i}.aiff", carpeta / f"{i}.wav"
    subprocess.run(["say", "-v", "Paulina", "-o", str(aiff), texto], check=True)
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", str(aiff), str(wav)], check=True)
    return wav.read_bytes()


class Fallo:
    status_code = 0
    headers: dict = {}

    def json(self):
        return {}


def cronometrar(fn):
    """Time one call; a network error is recorded as a failed call (None ms), not a crash."""
    t0 = time.perf_counter()
    try:
        r = fn()
    except httpx.HTTPError as e:
        print(f"  ! {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return Fallo(), None
    return r, round((time.perf_counter() - t0) * 1000, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=16)
    ap.add_argument("--pacientes", type=int, default=5)
    a = ap.parse_args()

    casos = [json.loads(l) for l in (RAIZ / "evals/interprete/escenarios.jsonl").read_text().splitlines() if l.strip()]
    casos = [c for c in casos if c["turno"].get("idioma") == "spa" and c["turno"].get("rol") == "personal"][: a.n]
    deps = o.dependencias(anthropic.Anthropic())
    cli = httpx.Client(timeout=120, headers=CAB)
    filas = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for i, c in enumerate(casos):
            fila = {"id": c["id"], "categoria": c["categoria"]}
            wav = audio_es(c["turno"]["texto"], tmp, i)
            r, fila["escuchar_ms"] = cronometrar(lambda: cli.post(f"{URL}/escuchar", files={"audio": ("t.wav", wav, "audio/wav")}))
            fila["escuchar_ok"] = r.status_code == 200
            res = o.interpretar(c["turno"], c.get("contexto") or None, **deps)
            fila.update(estado=res.estado, accion=res.accion, idioma_salida=res.idioma_salida,
                        pasos={k: v for k, v in res.ms.items()})
            if res.estado != "bloqueado" and res.texto_salida and res.idioma_salida == "quy" and not res.audio:
                r, fila["voz_ms"] = cronometrar(lambda: cli.post(f"{URL}/voz", data={"texto": res.texto_salida}))
                fila["voz_ok"] = r.status_code == 200
                fila["voz_x_ms"] = r.headers.get("X-Ms")
            if fila["escuchar_ms"] is not None and (fila.get("voz_ms", 0) is not None):
                fila["e2e_ms"] = round(fila["escuchar_ms"] + res.ms.get("total", 0) + (fila.get("voz_ms") or 0), 1)
            print(json.dumps(fila, ensure_ascii=False), flush=True)
            filas.append(fila)

    clips = sorted((RAIZ / "data/formulario").rglob("*.webm"))[: a.pacientes]
    pacientes = []
    for p in clips:
        audio = p.read_bytes()
        _, idioma = cronometrar(lambda: cli.post(f"{URL}/idioma", files={"audio": (p.name, audio, "audio/webm")}))
        r, turno = cronometrar(lambda: cli.post(f"{URL}/turno/paciente", files={"audio": (p.name, audio, "audio/webm")},
                                                data={"lengua": "quy"}))
        fila = {"clip": p.parent.name + "/" + p.name, "idioma_ms": idioma, "turno_paciente_ms": turno,
                "ok": r.status_code == 200, "pasos": (r.json().get("pasos") if r.status_code == 200 else None)}
        print(json.dumps(fila, ensure_ascii=False), flush=True)
        pacientes.append(fila)

    def col(k, filas=filas):
        return [f[k] for f in filas if isinstance(f.get(k), (int, float))]

    pasos = sorted({k for f in filas for k in f["pasos"]})
    resumen = {"turnos_personal": len(filas),
               "escuchar": {"p50": pct(col("escuchar_ms"), .5), "p95": pct(col("escuchar_ms"), .95)},
               "interprete": {k: {"p50": pct([f["pasos"][k] for f in filas if k in f["pasos"]], .5),
                                  "p95": pct([f["pasos"][k] for f in filas if k in f["pasos"]], .95)} for k in pasos},
               "voz": {"p50": pct(col("voz_ms"), .5), "p95": pct(col("voz_ms"), .95), "n": len(col("voz_ms"))},
               "e2e_personal": {"p50": pct(col("e2e_ms"), .5), "p95": pct(col("e2e_ms"), .95)},
               "paciente": {"idioma_p50": pct(col("idioma_ms", pacientes), .5),
                            "turno_p50": pct(col("turno_paciente_ms", pacientes), .5),
                            "turno_p95": pct(col("turno_paciente_ms", pacientes), .95)}}
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    out = Path(__file__).with_name("resultados")
    out.mkdir(exist_ok=True)
    (out / f"e2e-{datetime.now():%Y%m%d-%H%M}.json").write_text(
        json.dumps({"resumen": resumen, "personal": filas, "pacientes": pacientes, "modelos": {
            "principal": deps["modelo"], "critico": getattr(deps["auditar_fn"], "modelo", None)}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
