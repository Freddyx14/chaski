"""Prueba de humo de omniASR en la instancia: carga, transcribe y cronometra.

Corre EN la instancia (Linux + CUDA), no en la Mac. El entorno lo deja
`voz/instancia_setup.sh`.

Uso en la instancia:
  source /opt/dlami/nvme/chaski/venv/bin/activate
  HF_HOME=/opt/dlami/nvme/chaski/hf python omni_humo.py quy_todas.wav
"""
import json
import sys
import time
from pathlib import Path

import torch
from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline

BASE = Path("/opt/dlami/nvme/chaski")
TARJETA = "omniASR_LLM_300M"
LENGUA = "quy_Latn"


def main() -> None:
    audios = [str(BASE / "datos" / a) for a in (sys.argv[1:] or ["quy_todas.wav"])]
    tiempos = {"tarjeta": TARJETA, "lengua": LENGUA, "audios": audios}

    t0 = time.perf_counter()
    pipe = ASRInferencePipeline(model_card=TARJETA)
    tiempos["cargar_modelo_s"] = round(time.perf_counter() - t0, 2)
    print("modelo cargado en", tiempos["cargar_modelo_s"], "s", flush=True)

    for i, marca in enumerate(("primera", "segunda")):
        t0 = time.perf_counter()
        salida = pipe.transcribe(audios, lang=[LENGUA] * len(audios), batch_size=1)
        tiempos[f"transcribir_{marca}_s"] = round(time.perf_counter() - t0, 2)
        print(marca, "pasada:", tiempos[f"transcribir_{marca}_s"], "s ->", salida, flush=True)

    tiempos["salida"] = salida
    if torch.cuda.is_available():
        tiempos["gpu_pico_gb"] = round(torch.cuda.max_memory_allocated() / 2 ** 30, 2)
    (BASE / "humo.json").write_text(json.dumps(tiempos, ensure_ascii=False, indent=1))
    print(json.dumps(tiempos, ensure_ascii=False))


if __name__ == "__main__":
    main()
