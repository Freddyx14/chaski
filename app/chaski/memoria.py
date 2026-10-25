"""Chaski's automatic memory: every turn that passed the guards and the critic is saved, and the NEXT turn tells us if
the listener understood it. Moat step 2 (plan/foso.md, D44).

Why it does not feed the translator directly (evals/moat/memoria_auto.py, 25-oct 01:30): 85 of 100 self-translated
sentences passed the critic, and as examples they beat no memory (es→qu 54.9 → 56.2, qu→es 51.2 → 54.3) but always
LOST to the nurse's reviewed phrases alone (57.4 / 56.3), mixed in any way. So the memory is the queue that decides
what deserves approval, and only `aprobada` entries become examples (chaski.banco.ejemplos_revisados).

Storage is an append-only JSONL of events (no database): {"tipo": "turno", ...} when a turn is said, and
{"tipo": "senal", "id", "estado"} for confirmada (the other side answered normally) / dudosa (they asked Chaski what was
said) / aprobada (a reviewer said yes). The state of an entry is its last event. Writes run in the background and an
error never reaches the turn.

    uv run python -m chaski.memoria             # confirmed candidates, best first
    uv run python -m chaski.memoria aprobar ID  # it becomes an example from the next turn on
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path

RUTA_POR_DEFECTO = Path(__file__).with_name("memoria_auto.jsonl")
_lock = threading.Lock()


def activa() -> bool:
    return os.environ.get("CHASKI_MEMORIA_AUTO", "1").strip() not in ("0", "no", "false", "")


def ruta() -> Path:
    return Path(os.environ.get("CHASKI_MEMORIA_RUTA", "").strip() or RUTA_POR_DEFECTO)


def clave(rol: str, texto: str) -> str:
    return hashlib.sha1(f"{rol}\x00{texto.strip()}".encode()).hexdigest()[:12]


def _escribir(evento: dict) -> None:
    with _lock:
        with ruta().open("a", encoding="utf-8") as f:
            f.write(json.dumps({**evento, "ts": round(time.time())}, ensure_ascii=False) + "\n")


def guardar_turno(rol: str, texto_historial: str, original: str, pulido: str, traduccion: str, de: str,
                  a: str) -> None:
    """A said turn: what it meant in Spanish and how it is said in Quechua. Keyed by who spoke and the line the
    conversation history keeps for it, which is what the next turn sees."""
    es, quy = (pulido, traduccion) if de == "spa" else (traduccion, original)
    _escribir({"tipo": "turno", "id": clave(rol, texto_historial), "rol": rol, "es": es.strip(), "quy": quy.strip(),
               "de": de, "a": a})


def senal_de_respuesta(ultimo_rol: str | None, ultimo_texto: str | None, rol_actual: str, accion: str) -> None:
    """The turn after a said one is the evidence. The other side translating or being answered normally means they
    understood; asking Chaski what was said (`responder`) means doubt. Anything else says nothing."""
    if not ultimo_rol or not ultimo_texto or ultimo_rol in ("chaski", rol_actual):
        return
    estado = {"traducir": "confirmada", "responder": "dudosa"}.get(accion)
    if estado:
        _escribir({"tipo": "senal", "id": clave(ultimo_rol, ultimo_texto), "estado": estado})


def senal(id_: str, estado: str) -> None:
    _escribir({"tipo": "senal", "id": id_, "estado": estado})


def leer() -> dict[str, dict]:
    """Fold the log: {id: entry with its last `estado` and how many times it was confirmed}.

    Writes run in background threads, so a turn's signal can land in the file before the turn itself. Signals are
    therefore applied after every turn is known, in file order, instead of being dropped when they come first.
    """
    entradas: dict[str, dict] = {}
    senales: list[dict] = []
    if not ruta().exists():
        return entradas
    for linea in ruta().read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if e.get("tipo") == "turno":
            previa = entradas.get(e["id"], {})
            entradas[e["id"]] = {**e, "estado": "pendiente", "confirmaciones": 0, "usos": previa.get("usos", 0) + 1}
        elif e.get("tipo") == "senal":
            senales.append(e)
    for e in senales:
        x = entradas.get(e.get("id"))
        if x is None:
            continue
        if x["estado"] != "aprobada":  # an approval is final; later doubts are kept as a count
            x["estado"] = e["estado"]
        if e["estado"] == "confirmada":
            x["confirmaciones"] += 1
    return entradas


def aprobadas() -> list[dict]:
    return [{"es": e["es"], "quy": e["quy"]} for e in leer().values() if e["estado"] == "aprobada" and e["quy"]]


def candidatas() -> list[dict]:
    """What a reviewer should look at first: confirmed by real listeners, most confirmed and most used first."""
    xs = [e for e in leer().values() if e["estado"] == "confirmada"]
    return sorted(xs, key=lambda e: (-e["confirmaciones"], -e["usos"]))


def _main(argv: list[str]) -> None:
    if argv[:1] == ["aprobar"] and len(argv) == 2:
        senal(argv[1], "aprobada")
        print(f"aprobada {argv[1]}: desde el próximo turno es un ejemplo del traductor")
        return
    for e in candidatas():
        print(f"{e['id']}  ×{e['confirmaciones']} confirmada · {e['usos']} usos  |  {e['es']}  →  {e['quy']}")


if __name__ == "__main__":
    _main(sys.argv[1:])
