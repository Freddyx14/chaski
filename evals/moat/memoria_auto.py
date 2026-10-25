"""Does an AUTOMATIC memory help or hurt? Chaski translates new clinical sentences, keeps only what passes the code
guards AND the critic, and that memory is used as examples. Compared on the families' 62 unseen phrases against no
memory and the nurse's 24 (evals/moat/ejemplos.py, same leakage guard).

    cd app
    ANTHROPIC_API_KEY="$(secretctl get CHASKI_ANTHROPIC_API_KEY)" uv run --with sacrebleu python ../evals/moat/memoria_auto.py

Source sentences: the Spanish of the bank's CMP 2020 semiology rows (their Quechua is NOT used), 100 at random
(seed 7), minus anything near a test sentence. The patient-understood signal cannot be simulated offline: this measures
the critic filter alone, which is the stricter question (is self-generated memory safe at all?).
Writes resultados/memoria-auto-<fecha>.json.
"""
from __future__ import annotations

import concurrent.futures as fut
import json
import random
import sys
from datetime import datetime
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).parent))
import ejemplos as E  # noqa: E402
from chaski import banco as bmod  # noqa: E402
from chaski import guardas as g  # noqa: E402
from chaski import orquestador as o  # noqa: E402
from chaski.traducir import traducir  # noqa: E402


def construir_memoria(cli, cod, filas_test, n=100):
    fuente = [it for it in bmod.cargar_items() if it.get("revisado") is not True and it["id"].startswith("cmp")]
    random.Random(7).shuffle(fuente)
    limpio, _ = E.sin_fugas([{"id": it["id"], "es": it["es"], "quy": "-", "enfermera": False} for it in fuente],
                            filas_test, cod)
    limpio = limpio[:n]
    auditor = o.auditor(cli)

    def uno(it):
        try:
            ej = bmod.ejemplos_revisados(it["es"], "spa")
            tt = traducir(it["es"], "spa", "quy", client=cli, ejemplos=ej)
            e = o.EntradaRevision(accion="traducir", original=it["es"], fuente=it["es"], pulido=it["es"],
                                  traduccion=tt.texto, de="spa", a="quy")
            ok = o.guardas(e).ok and auditor(e).ok
            return {"id": "auto-" + it["id"], "es": it["es"], "quy": tt.texto, "enfermera": False, "paso": ok}
        except Exception as ex:  # noqa: BLE001
            return {"id": "auto-" + it["id"], "es": it["es"], "quy": "", "paso": False, "error": str(ex)[:120]}

    with fut.ThreadPoolExecutor(max_workers=6) as pool:
        res = list(pool.map(uno, limpio))
    return res


def main():
    cli = anthropic.Anthropic()
    cod = bmod.codificador_fastembed()
    sets = E.sets()
    fam = sets["familias"][2] + sets["familias_inv"][2]
    mem = construir_memoria(cli, cod, fam)
    auto = [m for m in mem if m["paso"]]
    print(f"memoria automática: {len(auto)}/{len(mem)} pasaron barreras + crítico", flush=True)
    todo = E.memoria()
    out = {"memoria": mem}
    for s in ("familias", "familias_inv"):
        de, a, filas = sets[s]
        limpio, _ = E.sin_fugas(todo, filas, cod)
        enf = [it for it in limpio if it["enfermera"]]
        auto_l, _ = E.sin_fugas(auto, filas, cod)
        conds = {"base": None, "enfermera": enf, "auto": auto_l, "enfermera+auto": enf + auto_l}
        lado = "es" if de == "spa" else "quy"
        out[s] = {}
        for cond, pool in conds.items():
            idx = E.indice(pool, lado, cod) if pool else None

            def uno(f):
                ej = [next(p for p in pool if p["id"] == x["id"]) for x, _ in idx.buscar(f[0], k=E.K)] if idx else []
                for _ in range(3):
                    try:
                        return E.traducir(cli, f[0], de, a, ej)[0]
                    except Exception:  # noqa: BLE001
                        pass
                return ""

            with fut.ThreadPoolExecutor(max_workers=6) as p:
                hips = list(p.map(uno, filas))
            b4 = sum(1 for f, h in zip(filas, hips) if h and not g.terminos_fijos(f[0], h).ok) if de == "spa" else None
            out[s][cond] = {"chrf2": E.puntuar(hips, [f[1] for f in filas]), "b4_frenadas": b4, "memoria": len(pool or [])}
            print(s, cond, out[s][cond], flush=True)
    d = Path(__file__).with_name("resultados"); d.mkdir(exist_ok=True)
    (d / f"memoria-auto-{datetime.now():%Y%m%d-%H%M}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
