"""Listen to Meta MMS-TTS Chanka (quy). Phrases from makitty/quechua-chanka-unified-v2 (CC-BY-4.0)."""
import sys
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wav
import torch
from transformers import AutoTokenizer, VitsModel

FRASES = [
    ("¿Está bien, señora?", "¿Allinllanchu, mamáy?"),
    ("¿Cómo está, señor?", "¿Imaynallam kachkanki, taytáy?"),
    ("¿Habla quechua, doctor?", "¿Runasimita rimankichu, doctor?"),
    ("Estoy esperando a mi hija, jefe", "Wawata suyarichkani, jefelláy"),
    ("Señora, estoy bien", "Mamáy, allillanmi"),
]

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
tok = AutoTokenizer.from_pretrained("facebook/mms-tts-quy")
model = VitsModel.from_pretrained("facebook/mms-tts-quy")
rate = model.config.sampling_rate
pausa = np.zeros(int(rate * 0.8), dtype=np.float32)
todo = []
for i, (es, qu) in enumerate(FRASES, 1):
    torch.manual_seed(0)
    with torch.no_grad():
        audio = model(**tok(qu, return_tensors="pt")).waveform[0].numpy()
    wav.write(out / f"{i:02d}.wav", rate, audio)
    todo += [audio, pausa]
    print(f"{i:02d}  {qu}   ({es})")
wav.write(out / "todas.wav", rate, np.concatenate(todo))
print(out / "todas.wav")
