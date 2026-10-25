# -*- coding: utf-8 -*-
"""Ajusta NLLB-200 para traducir castellano -> quechua chanka.

Hoy traduce Claude y su linea base es chrF++ 42.31 con el glosario vacio. La
decision D33 dice que NLLB traduce y Claude pule y audita, PERO solo si NLLB
gana en chrF++ sobre el mismo conjunto. Si no gana, se queda Claude y lo
decimos. Este script produce el numero que decide eso.

Datos: `somosnlp-hackathon-2022/spanish-to-quechua` (quy, ~102 k pares) mas los
243 pares del manual de semiologia del Colegio Medico, que son los unicos de
dominio clinico que tenemos.

La regla que no se negocia: **las 100 frases verificadas se quitan del
entrenamiento**. Salen de `rosettia-chanka-data` y son el conjunto con el que
medimos; si entran, el numero deja de significar nada.

Uso:
  python voz/ajustar_nllb.py --pasos 3000
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ORIGEN = "spa_Latn"
DESTINO = "quy_Latn"
BASE = "facebook/nllb-200-distilled-600M"


def reservadas() -> set:
    """El castellano de las 100 verificadas, normalizado para comparar."""
    d = json.loads(Path("datos/frases/frases.json").read_text(encoding="utf-8"))
    return {f["castellano"].strip().lower() for f in d["verificadas"]}


def pares_clinicos() -> list:
    ruta = Path("datos/frases/semiologia_cmp.jsonl")
    if not ruta.exists():
        return []
    salida = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        g = json.loads(linea)
        es, qu = g["castellano"].strip(), g["chanka_propuesto"].strip()
        if es and qu:
            salida.append({"es": es, "qu": qu})
    return salida


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pasos", type=int, default=3000)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--lr", type=float, default=5e-5)
    p.add_argument("--salida", default="modelos/nllb-chanka")
    p.add_argument("--max-tokens", type=int, default=96)
    args = p.parse_args()

    import torch
    from datasets import Dataset, load_dataset
    from transformers import (AutoModelForSeq2SeqLM, AutoTokenizer,
                              DataCollatorForSeq2Seq, Seq2SeqTrainer,
                              Seq2SeqTrainingArguments)

    fuera = reservadas()
    bruto = load_dataset("somosnlp-hackathon-2022/spanish-to-quechua", split="train")
    columnas = bruto.column_names
    col_es = "es" if "es" in columnas else columnas[0]
    col_qu = "qu" if "qu" in columnas else columnas[1]

    filas, descartadas = [], 0
    for f in bruto:
        es = (f[col_es] or "").strip()
        qu = (f[col_qu] or "").strip()
        if not es or not qu:
            continue
        if es.lower() in fuera:          # el conjunto de evaluacion, fuera
            descartadas += 1
            continue
        filas.append({"es": es, "qu": qu})
    clinicos = pares_clinicos()
    # El dominio clinico pesa poco frente a 100 k pares generales, asi que se
    # repite. No es trampa: es decirle al modelo que esas frases importan mas.
    filas += clinicos * 20
    print(f"{len(filas)} pares · {descartadas} descartados por estar en la evaluacion "
          f"· {len(clinicos)} clinicos x20")

    tok = AutoTokenizer.from_pretrained(BASE, src_lang=ORIGEN, tgt_lang=DESTINO)
    modelo = AutoModelForSeq2SeqLM.from_pretrained(BASE)

    def preparar(lote):
        x = tok(lote["es"], text_target=lote["qu"], max_length=args.max_tokens,
                truncation=True)
        return x

    datos = Dataset.from_list(filas).map(
        preparar, batched=True, remove_columns=["es", "qu"], num_proc=4)

    entrenador = Seq2SeqTrainer(
        model=modelo,
        args=Seq2SeqTrainingArguments(
            output_dir=args.salida, overwrite_output_dir=True,
            per_device_train_batch_size=args.batch,
            gradient_accumulation_steps=2,
            learning_rate=args.lr, warmup_ratio=0.03,
            max_steps=args.pasos, logging_steps=100, save_steps=1000,
            save_total_limit=2, fp16=torch.cuda.is_available(),
            report_to=[], dataloader_num_workers=4),
        train_dataset=datos,
        data_collator=DataCollatorForSeq2Seq(tok, model=modelo))
    entrenador.train()

    modelo.save_pretrained(args.salida)
    tok.save_pretrained(args.salida)
    print(f"guardado en {args.salida}")


if __name__ == "__main__":
    main()
