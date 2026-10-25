# -*- coding: utf-8 -*-
"""Mide si la voz ajustada se ENTIENDE mejor, no solo si se parece mas.

El riesgo del ajuste de voz es silencioso: el audio suena mas a la persona y al
mismo tiempo se vuelve pastoso, y en una posta eso significa una dosis mal oida.
Parecido no hay como medirlo sin otro modelo; entendible si, y con lo que ya
tenemos.

La prueba es de ida y vuelta:

    texto chanka  ->  voz  ->  reconocimiento  ->  texto

Si la voz es clara, lo que vuelve se parece a lo que entro. Se corre con cada
voz —la de Meta tal cual y las ajustadas— sobre las mismas frases, y se compara.
No dice cual suena mas natural: eso lo decide la hablante a ciegas.

Uso:
  python voz/medir_voz.py --voces facebook/mms-tts-quy modelos/tts-p24 modelos/tts-p16
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from voz.ortografia import distancia, normalizar

BANCO = Path("../app/chaski/banco.json")


def frases(cuantas: int, etiqueta: str) -> list:
    d = json.loads(BANCO.read_text(encoding="utf-8"))
    salida = [f for f in d
              if etiqueta in (f.get("tags") or []) and (f.get("quy") or "").strip()]
    return salida[:cuantas]


def wer(referencias, hipotesis, orto=True):
    err = tot = 0
    for r, h in zip(referencias, hipotesis):
        a = (normalizar(r) if orto else r.lower()).split()
        b = (normalizar(h) if orto else h.lower()).split()
        err += distancia(a, b)
        tot += len(a)
    return round(err / tot, 4) if tot else None


def main() -> None:
    import torch
    from transformers import (AutoProcessor, AutoTokenizer, VitsModel,
                              Wav2Vec2ForCTC)

    p = argparse.ArgumentParser()
    p.add_argument("--voces", nargs="+",
                   default=["facebook/mms-tts-quy", "modelos/tts-p24"])
    p.add_argument("--adaptador", default="modelos/asr-chanka/adaptador_mejor.pt")
    p.add_argument("--etiqueta", default="emergencia")
    p.add_argument("--cuantas", type=int, default=24)
    p.add_argument("--guardar-audio", default="reports/voces")
    p.add_argument("--salida", default="reports/voz_ida_vuelta.json")
    args = p.parse_args()

    filas = frases(args.cuantas, args.etiqueta)
    textos = [f["quy"].strip() for f in filas]
    print(f"{len(textos)} frases con la etiqueta «{args.etiqueta}»")

    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base_asr = "facebook/mms-1b-all"
    proc = AutoProcessor.from_pretrained(base_asr, target_lang="quy")
    oidos = Wav2Vec2ForCTC.from_pretrained(base_asr, target_lang="quy",
                                           ignore_mismatched_sizes=True)
    if Path(args.adaptador).exists():
        oidos.load_state_dict(torch.load(args.adaptador, map_location="cpu"), strict=False)
    oidos = oidos.to(dispositivo).eval()

    import soundfile as sf

    carpeta = Path(args.guardar_audio)
    resultados, detalle = {}, {}
    for ruta in args.voces:
        nombre = Path(ruta).name if "/" in ruta else ruta.split("/")[-1]
        tok = AutoTokenizer.from_pretrained(ruta)
        voz = VitsModel.from_pretrained(ruta).to(dispositivo).eval()
        destino = carpeta / nombre
        destino.mkdir(parents=True, exist_ok=True)

        oido = []
        for fila, texto in zip(filas, textos):
            with torch.no_grad():
                onda = voz(**tok(texto, return_tensors="pt").to(dispositivo)).waveform[0]
            onda = onda.cpu().numpy()
            sf.write(destino / f"{fila['id']}.wav", onda, voz.config.sampling_rate)
            # El reconocedor espera 16 kHz; VITS entrega a su propia frecuencia.
            if voz.config.sampling_rate != 16000:
                import numpy as np
                paso = voz.config.sampling_rate / 16000
                indices = (np.arange(int(len(onda) / paso)) * paso).astype(int)
                onda = onda[indices]
            x = proc(onda, sampling_rate=16000, return_tensors="pt").input_values.to(dispositivo)
            with torch.no_grad():
                oido.append(proc.batch_decode(torch.argmax(oidos(x).logits, dim=-1))[0])

        resultados[nombre] = {"wer": wer(textos, oido), "frases": len(textos)}
        detalle[nombre] = [{"id": f["id"], "es": f.get("es"), "entro": t, "volvio": o}
                           for f, t, o in zip(filas, textos, oido)]
        print(f"  {nombre:<26}WER de ida y vuelta {resultados[nombre]['wer']:.1%}")

    orden = sorted(resultados.items(), key=lambda kv: kv[1]["wer"])
    print(f"\nla mas entendible: {orden[0][0]} ({orden[0][1]['wer']:.1%})")

    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(json.dumps(
        {"etiqueta": args.etiqueta, "resultados": resultados, "detalle": detalle},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"audios en {carpeta}/<voz>/ · números en {args.salida}")


if __name__ == "__main__":
    main()
