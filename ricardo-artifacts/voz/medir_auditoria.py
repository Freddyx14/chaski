"""Compara configuraciones de la auditoría sobre las frases reales del cuadernillo.

Hoy NO existe verdad de referencia: si el chanka dice lo mismo que el castellano
solo lo sabe una hablante, y eso llega con la revisión de la mamá de Freddy (F8).
Mientras tanto hay tres cosas que sí se pueden medir sin ella, y las tres
deciden si el sistema sirve:

  bloqueo     qué fracción de frases se niega a decir. Si bloquea casi todo,
              la enfermera deja de hacerle caso y da igual lo correcto que sea.
  estabilidad la misma frase, varias corridas: ¿da siempre el mismo veredicto?
              Una auditoría que cambia de opinión no es una guarda, es un dado.
  tiempo      mediana por frase.

Cuando llegue la revisión de la hablante se agrega la cuarta: acierto real.

Uso:
  PYTHONPATH=. uv run --with anthropic --with pydantic python voz/medir_auditoria.py \
      --frases 5 --repeticiones 3
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

SALIDA = Path("reports/auditoria.json")


def frases(cuantas: int) -> list[str]:
    d = json.loads(Path("datos/frases/frases.json").read_text(encoding="utf-8"))
    # Las frases de la posta son el caso de uso real: dosis, controles, alarmas.
    return d.get("clinicas_sin_traducir", [])[:cuantas]


def configuraciones() -> dict:
    import anthropic

    from servicio.auditoria_rapida import auditar_con_arbitro, auditar_rapido

    cli = anthropic.Anthropic()

    def de_freddy(texto):
        from chaski.auditoria import auditar
        r = auditar(cli, texto)
        return {"enviar": r.enviar, "motivo": r.motivo}

    return {
        "freddy_opus_x4": de_freddy,
        "rapido_sonnet": lambda t: auditar_rapido(t),
        "rapido_con_arbitro": lambda t: auditar_con_arbitro(t),
    }


def medir(cuantas: int, repeticiones: int, solo: list[str]) -> dict:
    lista = frases(cuantas)
    configs = {k: v for k, v in configuraciones().items() if not solo or k in solo}
    resultados = {}

    for nombre, correr in configs.items():
        print(f"\n--- {nombre} ---", flush=True)
        veredictos: dict[str, list] = {}
        tiempos, motivos = [], {}
        for frase in lista:
            for _ in range(repeticiones):
                t0 = time.perf_counter()
                try:
                    r = correr(frase)
                except Exception as e:
                    print(f"  {frase[:28]:<30} FALLO {type(e).__name__}", flush=True)
                    continue
                tiempos.append(time.perf_counter() - t0)
                veredictos.setdefault(frase, []).append(r["enviar"])
                clave = r["motivo"].split(":")[0]
                motivos[clave] = motivos.get(clave, 0) + 1
            v = veredictos.get(frase, [])
            estable = "estable" if len(set(v)) <= 1 else "CAMBIA"
            print(f"  {frase[:30]:<32} {['sí' if x else 'no' for x in v]} {estable}", flush=True)

        todos = [x for v in veredictos.values() for x in v]
        estables = sum(1 for v in veredictos.values() if len(set(v)) <= 1)
        resultados[nombre] = {
            "frases": len(veredictos), "corridas": len(todos),
            "bloqueo": round(1 - sum(todos) / len(todos), 3) if todos else None,
            "estabilidad": round(estables / len(veredictos), 3) if veredictos else None,
            "mediana_s": round(statistics.median(tiempos), 2) if tiempos else None,
            "motivos": motivos,
        }

    salida = {"cuando": datetime.now(timezone.utc).isoformat(),
              "frases_evaluadas": lista, "repeticiones": repeticiones,
              "configuraciones": resultados}
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    return salida


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--frases", type=int, default=5)
    p.add_argument("--repeticiones", type=int, default=3)
    p.add_argument("--config", action="append", default=[])
    args = p.parse_args()
    s = medir(args.frases, args.repeticiones, args.config)
    print(f"\n{'configuración':<24}{'bloqueo':<10}{'estabilidad':<14}{'mediana'}")
    for nombre, r in s["configuraciones"].items():
        print(f"{nombre:<24}{r['bloqueo']:<10.0%}{r['estabilidad']:<14.0%}{r['mediana_s']}s")
    print(f"\nguardado en {SALIDA}")


if __name__ == "__main__":
    main()
