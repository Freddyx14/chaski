"""Speed vs. quality: the same real turns through four setups of the full interpreter (guards + critic always on).

    cd app
    ANTHROPIC_API_KEY="$(secretctl get CHASKI_ANTHROPIC_API_KEY)" uv run python ../evals/latencia/configuraciones.py

Setups: translator Claude (thinking, the product default) or NLLB-1.3B (Ricardo's /mt on our GPU), each with and
without the anticipated translation (started during the decision). Cases: every escenario whose expected action is
`traducir` (staff and patient), i.e. turns that SHOULD be said, so every block here is a false block. Reports said /
blocked, why, latency p50/p95, how often the anticipated translation was used, and for patient turns (output in
Spanish) whether the must_include facts survived. Writes resultados/configuraciones-<fecha>.json.
"""
from __future__ import annotations

import concurrent.futures as fut
import json
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import anthropic
import httpx

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
from chaski import orquestador as o  # noqa: E402
from chaski.traducir import TextoTraducido  # noqa: E402

URL = json.loads((RAIZ / "ricardo-artifacts/servicio/url.json").read_text())["url"].rstrip("/")
NLLB = {"spa": "spa_Latn", "quy": "quy_Latn"}


def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def traducir_nllb(texto, de, a):
    r = httpx.post(f"{URL}/mt", data={"texto": texto, "desde": NLLB[de], "hacia": NLLB[a]},
                   headers={"ngrok-skip-browser-warning": "1"}, timeout=60)
    r.raise_for_status()
    return TextoTraducido(texto=r.json()["traduccion"], de=de, a=a, motor="nllb", motor_pedido="nllb")


def pct(xs, p):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))] / 1000, 1) if xs else None


def correr(nombre, casos, deps, anticipar):
    filas = []
    for c in casos:
        r = o.interpretar(c["turno"], c.get("contexto") or None, anticipar=anticipar, **deps)
        fila = {"id": c["id"], "estado": r.estado, "accion": r.accion, "motivo": r.motivo if r.estado == "bloqueado" else None,
                "paso_fallido": r.paso_fallido, "anticipada": r.anticipada, "ms": r.ms, "salida": r.texto_salida}
        if c["turno"]["idioma"] == "quy" and r.estado != "bloqueado":
            faltan = [w for w in c["esperado"].get("must_include", []) if sin_tildes(w) not in sin_tildes(r.texto_salida)]
            fila["faltan"] = faltan
        filas.append(fila)
        print(nombre, json.dumps({k: fila[k] for k in ("id", "estado", "accion", "anticipada")}), round(r.ms["total"] / 1000, 1), flush=True)
    tr = [f for f in filas if f["accion"] == "traducir"]
    return {
        "dichos": sum(f["estado"] != "bloqueado" for f in filas), "bloqueados": sum(f["estado"] == "bloqueado" for f in filas),
        "n": len(filas), "p50_s": pct([f["ms"]["total"] for f in tr], .5), "p95_s": pct([f["ms"]["total"] for f in tr], .95),
        "anticipada_usada": sum(f["anticipada"] for f in filas),
        "paciente_datos_perdidos": sum(bool(f.get("faltan")) for f in filas),
        "filas": filas,
    }


def main():
    casos = [json.loads(l) for l in (RAIZ / "evals/interprete/escenarios.jsonl").read_text().splitlines() if l.strip()]
    casos = [c for c in casos if c["esperado"]["accion"] == "traducir"]
    cli = anthropic.Anthropic()
    base = o.dependencias(cli)
    nllb = {**base, "traducir_fn": traducir_nllb}
    setups = {"claude": (base, False), "claude_anticipado": (base, True), "nllb": (nllb, False), "nllb_anticipado": (nllb, True)}
    with fut.ThreadPoolExecutor(max_workers=4) as pool:
        res = dict(zip(setups, pool.map(lambda kv: correr(kv[0], casos, *kv[1]), setups.items())))
    for k, v in res.items():
        print(k, {x: y for x, y in v.items() if x != "filas"})
    d = Path(__file__).with_name("resultados"); d.mkdir(exist_ok=True)
    (d / f"configuraciones-{datetime.now():%Y%m%d-%H%M}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
