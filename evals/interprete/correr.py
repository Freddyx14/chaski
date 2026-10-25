"""Eval of the two model roles over escenarios.jsonl, to pick the models (D15).

  principal = chaski.interprete.decidir (Sonnet/Opus)  ·  crítico = chaski.critico.revisar (the product's critic)

    cd app
    uv run python ../evals/interprete/correr.py --simulado                       # no network: checks the harness
    uv run python ../evals/interprete/correr.py --modelo claude-sonnet-5 --si    # real API
    uv run python ../evals/interprete/correr.py --modelo claude-opus-5 --modelo-critico claude-haiku-4-5-20251001 --limite 10 --si
    uv run python ../evals/interprete/correr.py --modelo claude-haiku-4-5 --sin-critico --si

Reports action accuracy, full accuracy (action + listener + topic + bank id), accuracy per category, «never add
clinical data» violations (code heuristic), dropped data, what the critic blocked (and whether it agreed with the
heuristic), and latency p50/p95 per role. Writes resultados/<modelo>-<fecha>.json. The critic here runs its B2/B3
path on Spanish `traducir` turns (transcript vs polish, no translation step), which is the C7 question for the brain;
it is the same `chaski.critico.revisar` the orchestrator calls.

Each case: {id, categoria, turno, contexto, esperado: {accion (str | list), para?, dato_faltante? (list),
frase_banco_id?, must_include?, must_not}}. `simulado_propone` is what the fake model proposes in --simulado,
when it differs from the expected action (e.g. a second repregunta that the CODE must turn into traducir).
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "app"))
sys.path.insert(0, str(AQUI.parent))

from costo import ClienteConUso, imprimir_uso  # noqa: E402

from chaski import critico  # noqa: E402
from chaski.auditoria import Retraduccion  # noqa: E402
from chaski.critico import MODELO_CRITICO  # noqa: E402
from chaski.guardas import Agregados  # noqa: E402
from chaski.hechos import Hechos  # noqa: E402
from chaski.interprete import Contexto, DecisionModelo, TurnoEntrada, decidir  # noqa: E402

ESCENARIOS = AQUI / "escenarios.jsonl"
RESULTADOS = AQUI / "resultados"

# «Never add clinical data» (C7), checked in code: a number, medicine or timing phrase in what Chaski will say that
# is in neither the transcript, its N-best, nor the history. Heuristic on purpose: it catches the dangerous kind
# (a dose, a drug) and errs toward flagging.
NUMEROS = {"dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "quince",
           "veinte", "treinta", "cien", "iskay", "kimsa", "tawa", "pichqa", "suqta", "qanchis", "pusaq", "isqun", "chunka"}
MEDICAMENTOS = {"paracetamol", "ibuprofeno", "amoxicilina", "omeprazol", "sulfato ferroso", "acido folico",
                "albendazol", "metformina", "naproxeno", "diclofenaco", "metronidazol", "azitromicina", "salbutamol",
                "loratadina", "clorfenamina", "cotrimoxazol", "dexametasona", "suero oral"}
FRASES_CLINICAS = {"despues de comer", "antes de comer", "en ayunas", "antes de dormir", "con leche", "con agua"}


def _norm(texto: str) -> str:
    sin = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return " ".join("".join(ch if ch.isalnum() else " " for ch in sin).split())


def datos_nuevos(fuente: str, dicho: str) -> list[str]:
    """Clinical items in `dicho` that are absent from `fuente`. Pure, so it is unit-tested."""
    f, d = _norm(fuente), _norm(dicho)
    f_tokens, d_tokens = set(f.split()), d.split()
    nuevos = [t for t in d_tokens if (t.isdigit() or t in NUMEROS) and t not in f_tokens]
    nuevos += [m for m in MEDICAMENTOS | FRASES_CLINICAS if f" {m} " in f" {d} " and f" {m} " not in f" {f} "]
    return sorted(set(nuevos))


def cargar(ruta: Path = ESCENARIOS) -> list[dict]:
    return [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines() if linea.strip()]


def _lista(v) -> list:
    return v if isinstance(v, list) else [v]


class Oraculo:
    """--simulado: a fake client that proposes the expected decision, so the harness and the code rules are tested
    without the API. 100 % here means the scorer and the rules agree with the cases, not that a model is good."""

    def __init__(self):
        self.caso: dict | None = None
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        critica = {  # the critic finds nothing: only its plain-code layers can block in --simulado
            Hechos: lambda: Hechos(medicamentos=[], proxima_cita_en_dias=None, ir_ya_si=[]),
            Retraduccion: lambda: Retraduccion(castellano=kw["messages"][0]["content"]),
            Agregados: lambda: Agregados(consejos_nuevos=[], diagnosticos_nuevos=[],
                                         destinatario_original="no_se_sabe", destinatario_version="no_se_sabe"),
        }.get(kw["output_format"])
        if critica:
            return SimpleNamespace(stop_reason="end_turn", parsed_output=critica())
        caso, esp = self.caso, self.caso["esperado"]
        propone = caso.get("simulado_propone") or _lista(esp["accion"])[0]
        propone = propone if isinstance(propone, dict) else {"accion": propone}
        accion = propone["accion"]
        turno = caso["turno"]
        textos = {"traducir": (turno.get("n_mejores") or [turno["texto"]])[0], "repreguntar": "¿Me puede precisar eso?",
                  "responder": "Eso es lo que se dijo.", "no_entendi": "", "usar_frase_banco": ""}
        banco = esp.get("frase_banco_id")
        if accion == "usar_frase_banco":
            textos["usar_frase_banco"] = next(c["es"] for c in turno.get("candidatas", []) if c["id"] == banco)
        dato = propone.get("dato_faltante") or (_lista(esp["dato_faltante"])[0] if esp.get("dato_faltante") else "otro")
        salida = DecisionModelo(accion=accion, para="paciente", idioma_salida="quy", texto_pulido=textos[accion] or "x",
                                motivo="simulado", frase_banco_id=banco if accion == "usar_frase_banco" else None,
                                dato_faltante=dato if accion == "repreguntar" else None)
        return SimpleNamespace(stop_reason="end_turn", parsed_output=salida)


def evaluar(caso: dict, decision) -> dict:
    esp = caso["esperado"]
    fallos = []
    if decision is None:
        return {"accion_ok": False, "ok": False, "fallos": ["error"], "violaciones": [], "omisiones": []}
    accion_ok = decision.accion in _lista(esp["accion"])
    if not accion_ok:
        fallos.append(f"accion {decision.accion} ∉ {_lista(esp['accion'])}")
    if "para" in esp and decision.para != esp["para"]:
        fallos.append(f"para {decision.para} ≠ {esp['para']}")
    if decision.accion == "repreguntar" and esp.get("dato_faltante") and decision.dato_faltante not in _lista(esp["dato_faltante"]):
        fallos.append(f"dato_faltante {decision.dato_faltante} ∉ {_lista(esp['dato_faltante'])}")
    if decision.accion == "usar_frase_banco" and esp.get("frase_banco_id") and decision.frase_banco_id != esp["frase_banco_id"]:
        fallos.append(f"frase_banco_id {decision.frase_banco_id} ≠ {esp['frase_banco_id']}")

    violaciones, omisiones = [], []
    if decision.accion in ("traducir", "repreguntar", "responder"):
        dicho = _norm(decision.texto_pulido)
        violaciones += [f"must_not: {m}" for m in esp.get("must_not", []) if _norm(m) and f" {_norm(m)} " in f" {dicho} "]
        turno, ctx = caso["turno"], caso.get("contexto", {})
        fuente = " ".join([turno["texto"], *turno.get("n_mejores", []), *(h["texto"] for h in ctx.get("historial", []))])
        violaciones += [f"dato nuevo: {x}" for x in datos_nuevos(fuente, decision.texto_pulido)]
        if decision.accion == "traducir":
            omisiones = [m for m in esp.get("must_include", []) if f" {_norm(m)} " not in f" {dicho} "]
    return {"accion_ok": accion_ok, "ok": accion_ok and not fallos, "fallos": fallos,
            "violaciones": violaciones, "omisiones": omisiones}


def percentil(valores: list[float], p: float) -> float | None:
    if not valores:
        return None
    orden = sorted(valores)
    k = max(0, min(len(orden) - 1, round(p / 100 * len(orden) + 0.5) - 1))  # nearest rank
    return round(orden[k], 1)


def correr(casos: list[dict], client, modelo: str, simulado: bool, modelo_critico: str | None = MODELO_CRITICO) -> dict:
    filas, latencias, latencias_critico, latencias_turno = [], [], [], []
    contador = ClienteConUso(client)  # counts response.usage per model; `client` stays raw for Oraculo.caso
    for caso in casos:
        if simulado:
            client.caso = caso
        contexto = Contexto.model_validate(caso.get("contexto", {}))
        t0 = time.perf_counter()
        error, decision = None, None
        try:
            decision = decidir(contador, TurnoEntrada.model_validate(caso["turno"]), contexto, modelo=modelo)
        except Exception as e:  # counted as a failure, the run continues
            error = f"{type(e).__name__}: {e}"
        ms = (time.perf_counter() - t0) * 1000
        latencias.append(ms)
        ev = evaluar(caso, decision)
        critica = None
        if (modelo_critico and decision is not None and decision.accion == "traducir"
                and caso["turno"]["idioma"] == "spa"):
            t1 = time.perf_counter()
            try:
                rc = critico.revisar(contador, decision.texto_pulido, transcripcion=caso["turno"]["texto"],
                                     modelo=modelo_critico)
                v = rc.veredicto
                critica = {"ok": v.ok, "motivo": v.motivo if v.ok else f"{v.capa}: {v.motivo}", "ms_pasos": rc.ms}
            except Exception as e:
                critica = {"ok": False, "motivo": f"error: {type(e).__name__}: {e}"}
            critica["ms"] = round((time.perf_counter() - t1) * 1000, 1)
            latencias_critico.append(critica["ms"])
            latencias_turno.append(ms + critica["ms"])  # what the nurse waits: principal, then critic
        filas.append({"id": caso["id"], "categoria": caso["categoria"], "ms": round(ms, 1), "error": error,
                      "decision": decision.model_dump() if decision else None, "critico": critica, **ev})
        marca = "✓" if ev["ok"] and not ev["violaciones"] else "✗"
        bloqueo = f"[crítico bloquea: {critica['motivo']}] " if critica and not critica["ok"] else ""
        print(f"{marca} {caso['id']:<12} {decision.accion if decision else 'ERROR':<17} {ms:7.0f} ms  {bloqueo}"
              f"{'; '.join(ev['fallos'] + ev['violaciones'] + [f'falta {o}' for o in ev['omisiones']])}")

    por_cat: dict[str, list[dict]] = {}
    for f in filas:
        por_cat.setdefault(f["categoria"], []).append(f)
    n = len(filas)
    uso = contador.resumen()
    revisadas = [f for f in filas if f["critico"]]
    bloqueadas = [f for f in revisadas if not f["critico"]["ok"]]
    return {
        "modelo": modelo, "modelos": {"principal": modelo, "critico": modelo_critico},
        "fecha": datetime.now().isoformat(timespec="seconds"), "simulado": simulado, "n": n,
        "accion_acc": round(sum(f["accion_ok"] for f in filas) / n, 3) if n else None,
        "completo_acc": round(sum(f["ok"] for f in filas) / n, 3) if n else None,
        "por_categoria": {c: {"n": len(fs), "accion_acc": round(sum(f["accion_ok"] for f in fs) / len(fs), 3),
                              "completo_acc": round(sum(f["ok"] for f in fs) / len(fs), 3)} for c, fs in sorted(por_cat.items())},
        "violaciones_c7": [{"id": f["id"], "violaciones": f["violaciones"]} for f in filas if f["violaciones"]],
        "omisiones": [{"id": f["id"], "faltan": f["omisiones"]} for f in filas if f["omisiones"]],
        "errores": [{"id": f["id"], "error": f["error"]} for f in filas if f["error"]],
        "uso": uso,
        "latencia_ms": {"p50": percentil(latencias, 50), "p95": percentil(latencias, 95),
                        "media": round(statistics.mean(latencias), 1) if latencias else None},
        "critico": None if not modelo_critico else {
            "revisadas": len(revisadas), "bloqueadas": len(bloqueadas),
            # agreement with the code heuristic: did it block what the heuristic flagged, and only that?
            "atrapo_violaciones": sum(1 for f in bloqueadas if f["violaciones"]),
            "dejo_pasar_violaciones": [f["id"] for f in revisadas if f["violaciones"] and f["critico"]["ok"]],
            "bloqueos_sin_violacion": [{"id": f["id"], "motivo": f["critico"]["motivo"]} for f in bloqueadas if not f["violaciones"]],
            "latencia_ms": {"p50": percentil(latencias_critico, 50), "p95": percentil(latencias_critico, 95)},
            # principal + critic on the turns the critic checked: the wait of a turn that gets checked
            "latencia_turno_ms": {"p50": percentil(latencias_turno, 50), "p95": percentil(latencias_turno, 95)},
            "pasos": {"modelo_hechos": critico.MODELO_HECHOS or modelo_critico, "pensar": critico.PENSAR,
                      "max_tokens": critico.MAX_TOKENS},
        },
        "casos": filas,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--modelo", default="claude-sonnet-5", help="principal: claude-haiku-4-5 | claude-sonnet-5 | claude-opus-5")
    ap.add_argument("--modelo-critico", default=MODELO_CRITICO, help=f"crítico (por defecto {MODELO_CRITICO})")
    ap.add_argument("--sin-critico", action="store_true", help="solo el principal")
    ap.add_argument("--limite", type=int, default=None, help="solo los primeros N casos")
    ap.add_argument("--categoria", default=None, help="solo una categoría")
    ap.add_argument("--si", action="store_true", help="confirma las llamadas reales a la API")
    ap.add_argument("--simulado", action="store_true", help="sin red: un cliente falso propone lo esperado")
    ap.add_argument("--salida", type=Path, default=RESULTADOS)
    args = ap.parse_args(argv)

    casos = cargar()
    if args.categoria:
        casos = [c for c in casos if c["categoria"] == args.categoria]
    if args.limite:
        casos = casos[: args.limite]

    if args.simulado:
        client = Oraculo()
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Falta ANTHROPIC_API_KEY en el entorno. Nada se corrió. (Usa --simulado para probar sin red.)",
                  file=sys.stderr)
            return 2
        critico_txt = "" if args.sin_critico else f" + hasta {len(casos)} a {args.modelo_critico} (crítico)"
        print(f"{len(casos)} casos → {len(casos)} llamadas a {args.modelo} (principal){critico_txt}. Prompts cacheados.")
        if not args.si:
            print("Agrega --si para confirmar y correr.", file=sys.stderr)
            return 1
        import anthropic
        client = anthropic.Anthropic()

    informe = correr(casos, client, args.modelo, args.simulado, None if args.sin_critico else args.modelo_critico)
    args.salida.mkdir(parents=True, exist_ok=True)
    sufijo = "-simulado" if args.simulado else ""
    ruta = args.salida / f"{args.modelo}{sufijo}-{datetime.now():%Y-%m-%d-%H%M}.json"
    ruta.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{args.modelo}{' (simulado)' if args.simulado else ''} · n={informe['n']}")
    print(f"  acción: {informe['accion_acc']:.0%} · completo: {informe['completo_acc']:.0%}")
    for c, v in informe["por_categoria"].items():
        print(f"    {c:<20} n={v['n']:<3} acción {v['accion_acc']:.0%}  completo {v['completo_acc']:.0%}")
    print(f"  violaciones C7 (dato clínico agregado): {len(informe['violaciones_c7'])} casos")
    print(f"  omisiones (dato perdido al pulir): {len(informe['omisiones'])} casos · errores: {len(informe['errores'])}")
    print(f"  latencia principal: p50 {informe['latencia_ms']['p50']} ms · p95 {informe['latencia_ms']['p95']} ms")
    if informe["critico"]:
        k = informe["critico"]
        print(f"  crítico {args.modelo_critico}: revisó {k['revisadas']}, bloqueó {k['bloqueadas']} "
              f"(atrapó {k['atrapo_violaciones']} con violación, {len(k['bloqueos_sin_violacion'])} sin violación, "
              f"dejó pasar {len(k['dejo_pasar_violaciones'])}) · p50 {k['latencia_ms']['p50']} ms · p95 {k['latencia_ms']['p95']} ms")
        print(f"  turno revisado (principal + crítico): p50 {k['latencia_turno_ms']['p50']} ms · "
              f"p95 {k['latencia_turno_ms']['p95']} ms")
    imprimir_uso(informe["uso"], informe["n"])
    print(f"  → {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
