"""Mide la calidad de la traducción castellano -> chanka contra referencia humana.

Las 100 frases del bloque `verificadas` de frases.json ya traen el par completo
(castellano + chanka verificado). Son la única verdad de referencia que existe
hoy, antes de que la hablante revise nada. Sirven para dos cosas:

  1. puntuar al traductor sin esperar a nadie: chrF++ entre lo que produce el
     modelo y la referencia. chrF se mide sobre n-gramas de caracteres, así que
     no castiga la morfología aglutinante del quechua como lo haría BLEU.
  2. comparar antes y después del finetuning con el mismo set y el mismo corte.

Las 100 referencias están reservadas como evaluación: no entran al
entrenamiento. Entrenar con ellas invalidaría el número.

Uso:
  PYTHONPATH=. uv run --with anthropic --with sacrebleu python voz/medir_traduccion.py \
      --etiqueta base --frases 30
"""
from __future__ import annotations

import argparse
import concurrent.futures as futuros
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

FRASES = Path("datos/frases/frases.json")
SALIDA = Path("reports/traduccion.json")


def pares(cuantas: int) -> list[dict]:
    d = json.loads(FRASES.read_text(encoding="utf-8"))
    return d["verificadas"][:cuantas]


def traducir_con_claude(textos: list[str], modelo: str) -> list[str]:
    import anthropic

    from chaski.auditoria import cargar_glosario

    cli = anthropic.Anthropic()
    glosario = cargar_glosario()
    sistema = [{
        "type": "text",
        "text": ("Traduces del castellano al quechua chanka de Ayacucho. "
                 "Respondes solo con la traducción, una línea, sin comillas ni notas.\n"
                 "Glosario de la posta:\n" +
                 "\n".join(f"- {g['castellano']} = {g['quechua']}" for g in glosario)),
        "cache_control": {"type": "ephemeral"},
    }]

    def uno(t: str) -> str:
        # Sin pensamiento: es una frase corta y el razonamiento se come el
        # presupuesto de tokens antes de llegar a la traducción.
        r = cli.messages.create(model=modelo, max_tokens=400, system=sistema,
                                thinking={"type": "disabled"},
                                messages=[{"role": "user", "content": t}])
        # El modelo puede abrir con un bloque de pensamiento; la traducción es
        # el último bloque de texto.
        return [b for b in r.content if b.type == "text"][-1].text.strip()

    with futuros.ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(uno, textos))


def medir(etiqueta: str, cuantas: int, modelo: str) -> dict:
    import sacrebleu

    filas = pares(cuantas)
    fuentes = [f["castellano"] for f in filas]
    referencias = [f["chanka"] for f in filas]

    t0 = time.perf_counter()
    hipotesis = traducir_con_claude(fuentes, modelo)
    transcurrido = time.perf_counter() - t0

    chrf = sacrebleu.CHRF(word_order=2).corpus_score(hipotesis, [referencias])
    bleu = sacrebleu.BLEU().corpus_score(hipotesis, [referencias])
    por_frase = [sacrebleu.CHRF(word_order=2).sentence_score(h, [r]).score
                 for h, r in zip(hipotesis, referencias)]

    peores = sorted(zip(por_frase, fuentes, hipotesis, referencias))[:5]
    resultado = {
        "etiqueta": etiqueta, "modelo": modelo, "cuando": datetime.now(timezone.utc).isoformat(),
        "frases": len(filas), "chrf2": round(chrf.score, 2), "bleu": round(bleu.score, 2),
        "chrf2_mediana": round(statistics.median(por_frase), 2),
        "segundos_total": round(transcurrido, 1),
        "peores": [{"chrf2": round(s, 1), "castellano": c, "modelo": h, "referencia": r}
                   for s, c, h, r in peores],
        "salidas": [{"castellano": c, "modelo": h, "referencia": r, "chrf2": round(s, 1)}
                    for c, h, r, s in zip(fuentes, hipotesis, referencias, por_frase)],
    }

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    historial = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    historial[etiqueta] = resultado
    SALIDA.write_text(json.dumps(historial, ensure_ascii=False, indent=1), encoding="utf-8")
    return resultado


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--etiqueta", required=True, help="base | ajustado | lo que compares")
    p.add_argument("--frases", type=int, default=100)
    p.add_argument("--modelo", default="claude-sonnet-5")
    args = p.parse_args()

    r = medir(args.etiqueta, args.frases, args.modelo)
    print(f"\n{r['etiqueta']}  ({r['modelo']}, {r['frases']} frases, {r['segundos_total']}s)")
    print(f"  chrF++   {r['chrf2']}")
    print(f"  BLEU     {r['bleu']}")
    print(f"  mediana  {r['chrf2_mediana']}")
    print("\n  peores:")
    for w in r["peores"]:
        print(f"   [{w['chrf2']:>5}] {w['castellano']}")
        print(f"           modelo: {w['modelo']}")
        print(f"        referencia: {w['referencia']}")

    historial = json.loads(SALIDA.read_text(encoding="utf-8"))
    if "base" in historial and "ajustado" in historial:
        b, a = historial["base"]["chrf2"], historial["ajustado"]["chrf2"]
        print(f"\n  base {b} -> ajustado {a}  ({a - b:+.2f} chrF++)")
    print(f"\nguardado en {SALIDA}")


if __name__ == "__main__":
    main()
