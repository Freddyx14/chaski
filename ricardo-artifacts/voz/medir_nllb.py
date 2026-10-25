# -*- coding: utf-8 -*-
"""Compara NLLB-200 —de fabrica y ajustado— contra Claude, sobre el mismo set.

La decision D33 dice que NLLB traduce y Claude pule y audita, pero solo si NLLB
gana. Este script produce el numero que decide. Las 100 frases verificadas son
las mismas que uso `medir_traduccion.py` con Claude, y estan fuera del
entrenamiento de NLLB a proposito.

Uso:
  python voz/medir_nllb.py --ajustado modelos/nllb-chanka
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE = "facebook/nllb-200-distilled-600M"
ORIGEN, DESTINO = "spa_Latn", "quy_Latn"


def traducir(ruta_modelo: str, textos: list, lote: int = 16) -> list:
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(ruta_modelo, src_lang=ORIGEN)
    modelo = AutoModelForSeq2SeqLM.from_pretrained(ruta_modelo)
    if torch.cuda.is_available():
        modelo = modelo.cuda()
    modelo.eval()
    forzado = tok.convert_tokens_to_ids(DESTINO)

    salida = []
    for i in range(0, len(textos), lote):
        trozo = textos[i:i + lote]
        x = tok(trozo, return_tensors="pt", padding=True, truncation=True, max_length=128)
        x = {k: v.to(modelo.device) for k, v in x.items()}
        with torch.no_grad():
            y = modelo.generate(**x, forced_bos_token_id=forzado,
                                max_new_tokens=96, num_beams=4)
        salida.extend(tok.batch_decode(y, skip_special_tokens=True))
    return salida


def main() -> None:
    import sacrebleu

    p = argparse.ArgumentParser()
    p.add_argument("--ajustado", default="modelos/nllb-chanka")
    p.add_argument("--frases", type=int, default=100)
    p.add_argument("--salida", default="reports/nllb.json")
    args = p.parse_args()

    d = json.loads(Path("datos/frases/frases.json").read_text(encoding="utf-8"))
    pares = d["verificadas"][: args.frases]
    fuentes = [f["castellano"] for f in pares]
    referencias = [f["chanka"] for f in pares]

    chrf = sacrebleu.CHRF(word_order=2)
    resultados, salidas = {}, {}
    for etiqueta, ruta in (("nllb_base", BASE), ("nllb_ajustado", args.ajustado)):
        hip = traducir(ruta, fuentes)
        salidas[etiqueta] = hip
        resultados[etiqueta] = {
            "chrf2": round(chrf.corpus_score(hip, [referencias]).score, 2),
            "bleu": round(sacrebleu.BLEU().corpus_score(hip, [referencias]).score, 2)}
        print(f"  {etiqueta:<16}chrF++ {resultados[etiqueta]['chrf2']:>6}  "
              f"BLEU {resultados[etiqueta]['bleu']:>6}")

    claude = Path("reports/traduccion.json")
    if claude.exists():
        c = json.loads(claude.read_text(encoding="utf-8")).get("base")
        if c:
            resultados["claude_sonnet"] = {"chrf2": c["chrf2"], "bleu": c["bleu"]}
            print(f"  {'claude_sonnet':<16}chrF++ {c['chrf2']:>6}  BLEU {c['bleu']:>6}")

    mejor = max(resultados.items(), key=lambda kv: kv[1]["chrf2"])
    print(f"\ngana: {mejor[0]} con chrF++ {mejor[1]['chrf2']}")

    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(json.dumps(
        {"frases": len(pares), "resultados": resultados,
         "ejemplos": [{"castellano": f, "referencia": r,
                       "nllb_base": salidas["nllb_base"][i],
                       "nllb_ajustado": salidas["nllb_ajustado"][i]}
                      for i, (f, r) in enumerate(zip(fuentes, referencias))][:8]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"guardado en {args.salida}")


if __name__ == "__main__":
    main()
