# -*- coding: utf-8 -*-
"""Arma el conjunto de una sola voz para ajustar mms-tts-quy.

La voz de Chaski sale de UNA persona: mezclar hablantes da una voz que no es de
nadie. Este script toma el manifiesto de quien se elija y escribe un dataset de
HuggingFace con audio y texto, que es lo que espera finetune-hf-vits.

El texto va tal como lo escribio la persona, NO normalizado: aqui el modelo
aprende a leer, y tiene que ver la escritura que de verdad va a recibir.

Uso:
  python voz/preparar_tts.py --persona p24 --salida datos/tts/p24
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--persona", required=True)
    p.add_argument("--salida", default="")
    p.add_argument("--minimo-segundos", type=float, default=1.0)
    p.add_argument("--maximo-segundos", type=float, default=20.0)
    args = p.parse_args()

    import shutil

    manifiesto = Path(f"datos/crudo/{args.persona}/manifiesto.jsonl")
    filas = []
    for linea in manifiesto.read_text(encoding="utf-8").splitlines():
        if not linea.strip() or linea.startswith("#"):
            continue
        g = json.loads(linea)
        texto = (g.get("transcripcion") or "").strip()
        audio = g.get("audio") or ""
        if not texto or not Path(audio).exists():
            continue
        if not (args.minimo_segundos <= g.get("segundos", 0) <= args.maximo_segundos):
            continue
        filas.append({"audio": audio, "text": texto, "speaker_id": 0})

    if not filas:
        raise SystemExit(f"no hay clips usables de {args.persona}")

    # Formato `audiofolder`: una carpeta con los wav y un metadata.csv al lado.
    # `save_to_disk` no sirve aqui porque el entrenador llama a `load_dataset`,
    # que no lee ese formato; audiofolder lo detecta solo por el metadata.csv.
    salida = Path(args.salida or f"datos/tts/{args.persona}")
    destino = salida / "data"
    destino.mkdir(parents=True, exist_ok=True)
    # metadata.jsonl y no .csv: con CSV, `datasets` infiere tipos por columna y
    # fallaba con «`file_name` key must be a string». En jsonl cada valor lleva
    # su tipo y no hay nada que adivinar.
    with (salida / "metadata.jsonl").open("w", encoding="utf-8") as f:
        for fila in filas:
            nombre = Path(fila["audio"]).name
            shutil.copy2(fila["audio"], destino / nombre)
            f.write(json.dumps({"file_name": f"data/{nombre}",
                                "text": fila["text"], "speaker_id": 0},
                               ensure_ascii=False) + "\n")
    print(f"{len(filas)} clips -> {salida}")


if __name__ == "__main__":
    main()
