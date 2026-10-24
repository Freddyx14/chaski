"""Corre el ciclo del interprete sobre el set minimo y cronometra cada paso.

Hoy corre con las versiones falsas del contrato, asi que los tiempos son el
piso: lo que cuesta el armazon sin modelos. Cuando `entender`, `idioma` y
`hablar` sean reales, este mismo script da la espera por turno (tarea B3) sin
cambiar una linea.

Uso:  PYTHONPATH=. uv run python voz/ciclo.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from voz.contrato import entender, hablar, idioma

RAIZ = Path("datos/prueba_minima")


def un_turno(audio: Path) -> dict:
    pasos = {}
    t0 = time.perf_counter()
    lengua = idioma(audio)
    pasos["idioma"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    texto = entender(audio)
    pasos["entender"] = time.perf_counter() - t0

    # Si el paciente hablo chanka, Rimay le responde a la enfermera en castellano
    # y no sintetiza nada; si la enfermera hablo castellano, Rimay habla chanka.
    t0 = time.perf_counter()
    salida = hablar(texto.texto) if lengua.codigo == "spa" else None
    pasos["hablar"] = time.perf_counter() - t0

    return {"archivo": audio.name, "idioma": lengua.codigo, "confianza": lengua.confianza,
            "texto": texto.texto, "modelo_asr": texto.modelo,
            "audio_salida": salida.ruta if salida else None,
            "pasos": {k: round(v * 1000, 2) for k, v in pasos.items()},
            "total_ms": round(sum(pasos.values()) * 1000, 2)}


def main() -> None:
    fichas = json.loads((RAIZ / "fichas.json").read_text(encoding="utf-8"))
    esperado = {f["archivo"]: f["idioma"] for f in fichas}
    turnos = [un_turno(RAIZ / f["archivo"]) for f in fichas]

    print(f"{'archivo':<16}{'esperado':<10}{'detectado':<11}{'total':>8}   texto")
    aciertos = 0
    for t in turnos:
        esp = esperado[t["archivo"]]
        # 'mix' no tiene respuesta correcta unica: se cuenta aparte
        ok = "·" if esp == "mix" else ("ok" if esp == t["idioma"] else "NO")
        aciertos += 1 if ok == "ok" else 0
        print(f"{t['archivo']:<16}{esp:<10}{t['idioma']:<11}{t['total_ms']:>6.2f}ms   {t['texto'][:34]}")

    puros = [f for f in fichas if f["idioma"] != "mix"]
    print(f"\nidioma, solo casos puros: {aciertos}/{len(puros)}")
    print(f"espera por turno, mediana: "
          f"{sorted(t['total_ms'] for t in turnos)[len(turnos)//2]:.2f} ms (versiones falsas)")
    destino = Path("reports/ciclo.json")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(turnos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"detalle por paso en {destino}")


if __name__ == "__main__":
    main()
