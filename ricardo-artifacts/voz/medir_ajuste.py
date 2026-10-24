# -*- coding: utf-8 -*-
"""Mide el mismo modelo con y sin nuestro adaptador, sobre el hablante apartado.

La comparacion tiene que ser contra SI MISMO. La linea base que ya teniamos es
de omniASR, y lo que ajustamos es MMS: poner un numero al lado del otro diria
mas sobre que modelo es mejor de fabrica que sobre si nuestro ajuste sirvio.
Asi que aqui se corre `facebook/mms-1b-all` dos veces sobre los mismos 175
clips de p16 —sin adaptador y con el nuestro— y esa diferencia es nuestra.

Uso:
  python voz/medir_ajuste.py --adaptador modelos/asr-chanka/adaptador_mejor.pt
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch

from voz.ortografia import distancia, normalizar

BASE = "facebook/mms-1b-all"
IDIOMA = "quy"


def tasas(refs, hips):
    def calcular(por_caracter, orto):
        err = tot = 0
        for r, h in zip(refs, hips):
            a, b = (normalizar(r), normalizar(h)) if orto else (r.lower(), h.lower())
            x = list(a) if por_caracter else a.split()
            y = list(b) if por_caracter else b.split()
            err += distancia(x, y); tot += len(x)
        return round(err / tot, 4) if tot else None
    return {"wer": calcular(False, False), "cer": calcular(True, False),
            "wer_ortografia": calcular(False, True),
            "cer_ortografia": calcular(True, True),
            "exactos": sum(1 for r, h in zip(refs, hips)
                           if normalizar(r) == normalizar(h))}


@torch.no_grad()
def transcribir_todo(modelo, procesador, filas, dispositivo):
    import soundfile as sf

    hips = []
    for f in filas:
        onda, frecuencia = sf.read(f["audio"], dtype="float32")
        if onda.ndim > 1:
            onda = onda.mean(axis=1)
        entrada = procesador(onda, sampling_rate=frecuencia,
                             return_tensors="pt").input_values.to(dispositivo)
        ids = torch.argmax(modelo(entrada).logits, dim=-1)
        hips.append(procesador.batch_decode(ids)[0])
    return hips


def main() -> None:
    from transformers import AutoProcessor, Wav2Vec2ForCTC

    p = argparse.ArgumentParser()
    p.add_argument("--prueba", default="datos/corpus/prueba.jsonl")
    p.add_argument("--adaptador", default="modelos/asr-chanka/adaptador_mejor.pt")
    p.add_argument("--salida", default="reports/ajuste_asr.json")
    args = p.parse_args()

    filas = [json.loads(l) for l in Path(args.prueba).read_text(encoding="utf-8").splitlines()
             if l.strip()]
    filas = [f for f in filas if Path(f["audio"]).exists()]
    refs = [f["texto"] for f in filas]
    print(f"{len(filas)} clips de {filas[0].get('persona', '?')}")

    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    procesador = AutoProcessor.from_pretrained(BASE, target_lang=IDIOMA)
    modelo = Wav2Vec2ForCTC.from_pretrained(
        BASE, target_lang=IDIOMA, ignore_mismatched_sizes=True).to(dispositivo).eval()

    resultados = {}
    t0 = time.perf_counter()
    resultados["sin_ajustar"] = tasas(refs, transcribir_todo(modelo, procesador, filas, dispositivo))
    print(f"  sin ajustar     {resultados['sin_ajustar']}  ({(time.perf_counter()-t0)/60:.1f} min)")

    pesos = torch.load(args.adaptador, map_location=dispositivo)
    faltan = modelo.load_state_dict(pesos, strict=False)
    cargados = len(pesos) - len(set(faltan.unexpected_keys))
    print(f"  adaptador: {cargados}/{len(pesos)} tensores cargados")

    hips = transcribir_todo(modelo, procesador, filas, dispositivo)
    resultados["ajustado"] = tasas(refs, hips)
    print(f"  ajustado        {resultados['ajustado']}")

    a, b = resultados["sin_ajustar"], resultados["ajustado"]
    print(f"\n{'':18}{'sin ajustar':>14}{'ajustado':>12}{'cambio':>12}")
    for clave in ("wer", "cer", "wer_ortografia", "cer_ortografia"):
        print(f"{clave:<18}{a[clave]:>13.1%}{b[clave]:>12.1%}{b[clave]-a[clave]:>+12.1%}")
    print(f"{'clips exactos':<18}{a['exactos']:>13}{b['exactos']:>12}"
          f"{b['exactos']-a['exactos']:>+12}")

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(
        {"base": BASE, "idioma": IDIOMA, "adaptador": args.adaptador,
         "clips": len(filas), "hablante": filas[0].get("persona"),
         "resultados": resultados,
         "ejemplos": [{"referencia": r, "ajustado": h}
                      for r, h in list(zip(refs, hips))[:8]]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nguardado en {salida}")


if __name__ == "__main__":
    main()
