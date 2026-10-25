"""Cost of a FULL turn as the product runs it (Opus decides, Sonnet medium translates, Sonnet critic), from real tokens.

    cd app
    ANTHROPIC_API_KEY="$(secretctl get CHASKI_ANTHROPIC_API_KEY)" uv run python ../evals/latencia/costo_turno.py --n 10

Runs the first N escenarios whose expected action is `traducir` (the most expensive path: decide + translate + critic)
through orquestador.interpretar with the counting client of evals/costo.py. Prices are the list prices recorded in
evals/costo.py (not checked against an invoice). Writes resultados/costo-turno-<fecha>.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import anthropic

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "evals"))
from chaski import orquestador as o  # noqa: E402
from costo import ClienteConUso, imprimir_uso  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    a = ap.parse_args()
    casos = [json.loads(l) for l in (RAIZ / "evals/interprete/escenarios.jsonl").read_text().splitlines() if l.strip()]
    casos = [c for c in casos if c["esperado"]["accion"] == "traducir"][: a.n]
    cli = ClienteConUso(anthropic.Anthropic())
    estados = []
    for c in casos:
        r = o.interpretar(c["turno"], c.get("contexto") or None, **o.dependencias(cli))
        estados.append({"id": c["id"], "estado": r.estado, "accion": r.accion})
        print(c["id"], r.estado, r.accion, flush=True)
    uso = cli.resumen()
    imprimir_uso(uso, len(casos))
    d = Path(__file__).with_name("resultados"); d.mkdir(exist_ok=True)
    (d / f"costo-turno-{datetime.now():%Y%m%d-%H%M}.json").write_text(json.dumps(
        {"turnos": len(casos), "uso": uso, "por_turno_usd": (uso["costo_usd_total"] or 0) / len(casos),
         "estados": estados}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
