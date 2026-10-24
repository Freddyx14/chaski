"""Run the seeded-error bank and report «the audit caught X of Y errors».

Modes:
  sin_barreras  passes everything. The floor: 0 % caught.
  juez_claude   the naive baseline. One Claude call per case: «is this a faithful translation? yes/no».
  chaski        the real checks: the critic (chaski.critico, blind back-translation + fact extraction +
                added-content list, on --modelo-critico) and the code that decides on it (B2-B5, C).

Per mutation type it reports the catch rate, and on `limpio` / `pulido_limpio` the false-block rate.
A system that blocks everything catches 100 % and is useless; the false-block rate is what shows it.

Run from app/:
  uv run python ../evals/ataques/correr.py --modo chaski --simulado            # no network, tests plumbing
  uv run python ../evals/ataques/correr.py --modo chaski --limite 5             # prints cost, asks for --si
  uv run python ../evals/ataques/correr.py --modo chaski --limite 5 --si
  uv run python ../evals/ataques/correr.py --modo chaski --modelo-critico claude-sonnet-4-5 --si

--limite N takes the first N cases OF EACH TYPE, so a cheap run still covers every type.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from pydantic import BaseModel, Field

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent.parent / "app"))

from chaski import critico  # noqa: E402
from chaski.auditoria import Retraduccion  # noqa: E402
from chaski.guardas import Agregados  # noqa: E402
from chaski.hechos import Hechos  # noqa: E402

BANCO = AQUI / "banco.jsonl"
RESULTADOS = AQUI / "resultados"
MODOS = ("sin_barreras", "juez_claude", "chaski")
LIMPIOS = ("limpio", "pulido_limpio")


class Juicio(BaseModel):
    fiel: bool = Field(description="true si la versión dice lo mismo que el original, sin cambiar ni agregar nada")


SISTEMA_JUEZ = "Eres un revisor de traducciones médicas castellano → quechua chanka. Responde solo si es fiel."


def pregunta_juez(caso: dict) -> str:
    if caso.get("pulido") is not None:
        return (f"Transcripción:\n{caso['es']}\n\nVersión pulida:\n{caso['pulido']}\n\n"
                "¿La versión pulida es fiel a la transcripción? Sí o no.")
    return (f"Castellano:\n{caso['es']}\n\nQuechua:\n{caso['quy']}\n\n"
            "¿Este quechua es una traducción fiel del castellano? Sí o no.")


class ClienteSimulado:
    """Stands in for anthropic.Anthropic with --simulado: no network, no cost.

    Extraction returns empty facts, the back-translation echoes its input, the judge always says
    «fiel» and the critic finds nothing added. So a simulated `chaski` run measures ONLY the
    plain-code layers (B4, B3 in code); the number for the pitch comes from a real run.
    """

    def __init__(self):
        self.llamadas = 0
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.llamadas += 1
        formato = kw["output_format"]
        contenido = kw["messages"][0]["content"]
        salida = {
            Hechos: lambda: Hechos(medicamentos=[], proxima_cita_en_dias=None, ir_ya_si=[]),
            Retraduccion: lambda: Retraduccion(castellano=contenido),
            Agregados: lambda: Agregados(consejos_nuevos=[], diagnosticos_nuevos=[],
                                         destinatario_original="no_se_sabe", destinatario_version="no_se_sabe"),
            Juicio: lambda: Juicio(fiel=True),
        }[formato]()
        return SimpleNamespace(stop_reason="end_turn", parsed_output=salida)


def cargar_banco(ruta: Path, limite: int | None) -> list[dict]:
    casos = [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]
    if limite is None:
        return casos
    por_tipo: dict[str, int] = {}
    elegidos = []
    for c in casos:
        if por_tipo.get(c["tipo"], 0) < limite:
            elegidos.append(c)
            por_tipo[c["tipo"]] = por_tipo.get(c["tipo"], 0) + 1
    return elegidos


def llamadas_estimadas(casos: list[dict], modo: str) -> int:
    if modo == "sin_barreras":
        return 0
    if modo == "juez_claude":
        return len(casos)
    return sum(critico.LLAMADAS_PULIDO if c.get("pulido") is not None else critico.LLAMADAS_TRADUCCION for c in casos)


def evaluar(caso: dict, modo: str, client, modelo_critico: str, modelo_juez: str) -> dict:
    """One case → {bloqueado, motivo}. Any error blocks (fail closed), and the error is recorded."""
    try:
        if modo == "sin_barreras":
            return {"bloqueado": False, "motivo": "sin barreras"}
        if modo == "juez_claude":
            r = client.messages.parse(model=modelo_juez, max_tokens=200, system=SISTEMA_JUEZ,
                                      messages=[{"role": "user", "content": pregunta_juez(caso)}], output_format=Juicio)
            if r.stop_reason == "refusal" or r.parsed_output is None:
                return {"bloqueado": True, "motivo": "no pude verificar: el juez no respondió"}
            fiel = r.parsed_output.fiel
            return {"bloqueado": not fiel, "motivo": "el juez dijo que es fiel" if fiel else "el juez dijo que no es fiel"}
        if caso.get("pulido") is not None:
            rc = critico.criticar_pulido(client, caso["es"], caso["pulido"], modelo_critico)
        else:
            rc = critico.criticar(client, caso["es"], caso["quy"], modelo_critico)
        v = rc.veredicto
        return {"bloqueado": not v.ok, "motivo": f"{v.capa}: {v.motivo}" if not v.ok else "pasó", "capa": v.capa}
    except Exception as e:  # noqa: BLE001
        return {"bloqueado": True, "motivo": f"no pude verificar: {type(e).__name__}: {e}"}


def resumir(casos: list[dict], salidas: list[dict]) -> dict:
    tipos: dict[str, dict] = {}
    for c, s in zip(casos, salidas):
        t = tipos.setdefault(c["tipo"], {"esperado": c["esperado"], "n": 0, "bloqueados": 0})
        t["n"] += 1
        t["bloqueados"] += int(s["bloqueado"])
    for t in tipos.values():
        t["tasa_bloqueo"] = round(t["bloqueados"] / t["n"], 4) if t["n"] else None
        t["metrica"] = "atrapados" if t["esperado"] == "bloquear" else "falsos_bloqueos"
    errores = [(c, s) for c, s in zip(casos, salidas) if c["esperado"] == "bloquear"]
    limpios = [(c, s) for c, s in zip(casos, salidas) if c["esperado"] == "pasar"]
    atrapados = sum(s["bloqueado"] for _, s in errores)
    falsos = sum(s["bloqueado"] for _, s in limpios)
    return {
        "por_tipo": dict(sorted(tipos.items())),
        "errores_sembrados": len(errores),
        "atrapados": atrapados,
        "tasa_atrapados": round(atrapados / len(errores), 4) if errores else None,
        "limpios": len(limpios),
        "falsos_bloqueos": falsos,
        "tasa_falsos_bloqueos": round(falsos / len(limpios), 4) if limpios else None,
    }


def imprimir(res: dict, modo: str) -> None:
    print(f"\n== {modo} ==")
    for tipo, t in res["por_tipo"].items():
        etiqueta = "atrapados" if t["metrica"] == "atrapados" else "falsos bloqueos"
        print(f"  {tipo:20s} {t['bloqueados']:4d}/{t['n']:<4d} {etiqueta:16s} {100 * t['tasa_bloqueo']:5.1f} %")
    if res["errores_sembrados"]:
        print(f"\n  La auditoría atrapó {res['atrapados']} de {res['errores_sembrados']} errores sembrados "
              f"({100 * res['tasa_atrapados']:.1f} %).")
    if res["limpios"]:
        print(f"  Bloqueó por error {res['falsos_bloqueos']} de {res['limpios']} frases correctas "
              f"({100 * res['tasa_falsos_bloqueos']:.1f} %).")


def main(argv: list[str] | None = None, cliente=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--modo", choices=MODOS, required=True)
    ap.add_argument("--limite", type=int, default=None, help="máximo de casos POR TIPO")
    ap.add_argument("--modelo-critico", default=critico.MODELO_CRITICO, help="modelo del crítico en el modo chaski")
    ap.add_argument("--modelo", default=None, help="modelo del juez en juez_claude (por defecto, el del crítico)")
    ap.add_argument("--simulado", action="store_true", help="cliente falso: sin red y sin costo")
    ap.add_argument("--si", action="store_true", help="confirmo el gasto en la API")
    ap.add_argument("--hilos", type=int, default=8)
    ap.add_argument("--banco", type=Path, default=BANCO)
    ap.add_argument("--salida", type=Path, default=RESULTADOS)
    args = ap.parse_args(argv)
    modelo_juez = args.modelo or args.modelo_critico

    if not args.banco.exists():
        print(f"error: no existe {args.banco}. Constrúyelo con: uv run python ../evals/ataques/construir.py",
              file=sys.stderr)
        return 1
    casos = cargar_banco(args.banco, args.limite)
    n_llamadas = llamadas_estimadas(casos, args.modo)

    if args.modo != "sin_barreras" and not args.simulado:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("error: el modo", args.modo, "llama a la API de Anthropic y falta la variable ANTHROPIC_API_KEY. "
                  "Exporta la llave o usa --simulado para probar sin red.", file=sys.stderr)
            return 1
        modelo = args.modelo_critico if args.modo == "chaski" else modelo_juez
        print(f"{len(casos)} casos → ~{n_llamadas} llamadas a {modelo}.")
        if not args.si:
            print("No gasto nada sin permiso: vuelve a correrlo con --si para confirmar.")
            return 2

    if cliente is None and args.modo != "sin_barreras":
        if args.simulado:
            cliente = ClienteSimulado()
        else:
            import anthropic
            cliente = anthropic.Anthropic()

    with ThreadPoolExecutor(max_workers=max(1, args.hilos)) as ex:
        salidas = list(ex.map(lambda c: evaluar(c, args.modo, cliente, args.modelo_critico, modelo_juez), casos))

    res = resumir(casos, salidas)
    imprimir(res, args.modo + (" (simulado)" if args.simulado else ""))
    ahora = dt.datetime.now()
    args.salida.mkdir(parents=True, exist_ok=True)
    nombre = f"{args.modo}-{ahora:%Y-%m-%d-%H%M}{'-simulado' if args.simulado else ''}.json"
    salida = {
        "modo": args.modo,
        "simulado": args.simulado,
        "fecha": ahora.isoformat(timespec="seconds"),
        "modelo_critico": args.modelo_critico if args.modo == "chaski" else None,
        "modelo_juez": modelo_juez if args.modo == "juez_claude" else None,
        "limite_por_tipo": args.limite,
        "llamadas_estimadas": n_llamadas,
        "resumen": res,
        "casos": [{"id": c["id"], "tipo": c["tipo"], "esperado": c["esperado"], **s} for c, s in zip(casos, salidas)],
    }
    (args.salida / nombre).write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados en {args.salida / nombre}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
