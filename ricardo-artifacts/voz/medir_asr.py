"""Mide el reconocimiento de chanka. Es el número del pitch.

Compara lo que el modelo oye contra la transcripción que una persona corrigió.
Se corre DOS veces, con la misma orden y el mismo conjunto:

  --etiqueta base       con el modelo tal como viene de Meta
  --etiqueta ajustado   después del ajuste fino

Las dos corridas se guardan en el mismo `reports/asr.json`, así la comparación
sale de dos mediciones hechas igual, no de dos recuerdos.

Reglas que hacen honesto el número:
  * Se mide sobre la voz de PRUEBA, que el modelo nunca escuchó al entrenar.
  * Se reporta aparte el error en los préstamos del castellano (paracetamol,
    control, doctor), que es donde el modelo base falla y donde más duele
    equivocarse en una posta.
  * Si un clip no tiene transcripción corregida, no entra: no se mide contra
    lo que nadie verificó.

Uso:
  PYTHONPATH=. uv run --with httpx python voz/medir_asr.py datos/corpus/asr.jsonl --etiqueta base
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import httpx

INSTANCIA = "http://127.0.0.1:8010"
SALIDA = Path("reports/asr.json")


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto.lower().strip())
    return re.sub(r"\s+", " ", re.sub(r"[^\w'áéíóúñ ]", " ", texto)).strip()


def distancia(a: list, b: list) -> int:
    fila = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        nueva = [i]
        for j, y in enumerate(b, 1):
            nueva.append(min(fila[j] + 1, nueva[j - 1] + 1, fila[j - 1] + (x != y)))
        fila = nueva
    return fila[-1]


def tasas(referencia: str, hipotesis: str) -> tuple[int, int, int, int]:
    """Devuelve (errores de palabra, palabras, errores de letra, letras)."""
    r, h = normalizar(referencia), normalizar(hipotesis)
    rp, hp = r.split(), h.split()
    return distancia(rp, hp), len(rp), distancia(list(r), list(h)), len(r)


def prestamos() -> set:
    ruta = Path("datos/frases/frases.json")
    if not ruta.exists():
        return set()
    d = json.loads(ruta.read_text(encoding="utf-8"))
    palabras = set()
    for frase in d.get("medicamentos_y_prestamos", []):
        palabras.update(normalizar(frase).split())
    return {p for p in palabras if len(p) > 3}


def transcribir(ruta_audio: str, cliente: httpx.Client) -> str:
    with open(ruta_audio, "rb") as f:
        r = cliente.post(f"{INSTANCIA}/entender",
                         files={"audio": (Path(ruta_audio).name, f.read(), "audio/wav")},
                         data={"lengua": "quy_Latn"}, timeout=600)
    r.raise_for_status()
    return r.json().get("texto", "")


def medir(origen: str, etiqueta: str, modelo: str = "omniASR_LLM_300M") -> dict:
    filas = [json.loads(l) for l in Path(origen).read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    filas = [f for f in filas if f.get("texto", "").strip() and Path(f["audio"]).exists()]
    if not filas:
        raise SystemExit(f"{origen} no tiene clips con transcripción corregida")

    lista = prestamos()
    acumulado = {"ep": 0, "p": 0, "el": 0, "l": 0}
    por_persona: dict[str, dict] = {}
    aciertos_prestamo = fallos_prestamo = 0
    detalle = []

    with httpx.Client() as cliente:
        for i, f in enumerate(filas, 1):
            oido = transcribir(f["audio"], cliente)
            ep, p, el, l = tasas(f["texto"], oido)
            acumulado["ep"] += ep; acumulado["p"] += p
            acumulado["el"] += el; acumulado["l"] += l
            quien = f.get("persona", "?")
            fila = por_persona.setdefault(quien, {"ep": 0, "p": 0, "el": 0, "l": 0, "clips": 0})
            fila["ep"] += ep; fila["p"] += p; fila["el"] += el; fila["l"] += l; fila["clips"] += 1

            oidas = set(normalizar(oido).split())
            for palabra in set(normalizar(f["texto"]).split()) & lista:
                if palabra in oidas:
                    aciertos_prestamo += 1
                else:
                    fallos_prestamo += 1
            detalle.append({"audio": f["audio"], "referencia": f["texto"], "oido": oido,
                            "wer": round(ep / p, 3) if p else None})
            if i % 10 == 0:
                print(f"  {i}/{len(filas)}…", flush=True)

    total_prestamos = aciertos_prestamo + fallos_prestamo
    corrida = {
        "etiqueta": etiqueta, "modelo": modelo, "cuando": datetime.now(timezone.utc).isoformat(),
        "origen": origen, "clips": len(filas),
        "wer": round(acumulado["ep"] / acumulado["p"], 4) if acumulado["p"] else None,
        "cer": round(acumulado["el"] / acumulado["l"], 4) if acumulado["l"] else None,
        "por_persona": {k: {"clips": v["clips"],
                            "wer": round(v["ep"] / v["p"], 4) if v["p"] else None,
                            "cer": round(v["el"] / v["l"], 4) if v["l"] else None}
                        for k, v in por_persona.items()},
        "prestamos": {"evaluados": total_prestamos,
                      "acertados": aciertos_prestamo,
                      "tasa_acierto": round(aciertos_prestamo / total_prestamos, 4)
                      if total_prestamos else None},
        "detalle": detalle,
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    historial = json.loads(SALIDA.read_text()) if SALIDA.exists() else []
    historial = [c for c in historial if c.get("etiqueta") != etiqueta] + [corrida]
    SALIDA.write_text(json.dumps(historial, ensure_ascii=False, indent=1), encoding="utf-8")
    return corrida


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("origen", help="jsonl con {audio, texto, persona}")
    p.add_argument("--etiqueta", required=True, help="base | vocabulario | ajustado")
    p.add_argument("--modelo", default="omniASR_LLM_300M")
    args = p.parse_args()
    c = medir(args.origen, args.etiqueta, args.modelo)
    print(f"\n{c['etiqueta']} · {c['modelo']} · {c['clips']} clips")
    print(f"  WER {c['wer']:.1%}   CER {c['cer']:.1%}")
    if c["prestamos"]["evaluados"]:
        print(f"  préstamos del castellano: {c['prestamos']['acertados']}"
              f"/{c['prestamos']['evaluados']} bien ({c['prestamos']['tasa_acierto']:.1%})")
    for quien, v in c["por_persona"].items():
        print(f"  {quien}: {v['clips']} clips · WER {v['wer']:.1%}")
    print(f"\nguardado en {SALIDA}")


if __name__ == "__main__":
    main()
