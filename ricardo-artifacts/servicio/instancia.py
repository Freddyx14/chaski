"""Servicio de voz en la GPU: oir y hablar quechua.

Corre EN la instancia. La Mac lo alcanza por un tunel de SSH, asi no hay que
tocar el grupo de seguridad ni levantar certificados:

  ssh -i ~/.ssh/id_rsa_aws -N -L 8010:localhost:8000 ubuntu@<ip>

Arranque en la instancia:
  source /opt/dlami/nvme/chaski/venv/bin/activate
  export HF_HOME=/opt/dlami/nvme/chaski/hf XDG_CACHE_HOME=/opt/dlami/nvme/chaski/cache
  uvicorn instancia:aplicacion --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import io
import os
import tempfile
import time

import soundfile as sf
import torch
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse, Response

aplicacion = FastAPI(title="Chaski · voz en la GPU")
DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
_modelos: dict = {}


def asr():
    if "asr" not in _modelos:
        from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline
        t0 = time.perf_counter()
        _modelos["asr"] = ASRInferencePipeline(model_card="omniASR_LLM_300M")
        _modelos["asr_carga_s"] = round(time.perf_counter() - t0, 1)
    return _modelos["asr"]


def lid():
    if "lid" not in _modelos:
        from transformers import AutoFeatureExtractor, Wav2Vec2ForSequenceClassification
        tarjeta = "facebook/mms-lid-512"
        _modelos["lid_ext"] = AutoFeatureExtractor.from_pretrained(tarjeta)
        _modelos["lid"] = Wav2Vec2ForSequenceClassification.from_pretrained(tarjeta).to(DISPOSITIVO).eval()
    return _modelos["lid_ext"], _modelos["lid"]


def tts():
    if "tts" not in _modelos:
        from transformers import AutoTokenizer, VitsModel
        tarjeta = "facebook/mms-tts-quy"
        _modelos["tts_tok"] = AutoTokenizer.from_pretrained(tarjeta)
        _modelos["tts"] = VitsModel.from_pretrained(tarjeta).to(DISPOSITIVO).eval()
    return _modelos["tts_tok"], _modelos["tts"]


def _guardar(datos: bytes) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(datos)
    tmp.close()
    return tmp.name


@aplicacion.get("/salud")
def salud():
    return {"dispositivo": DISPOSITIVO, "cargados": [k for k in _modelos if not k.endswith("_s")],
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}


@aplicacion.post("/idioma")
async def idioma(audio: UploadFile = File(...)):
    ruta = _guardar(await audio.read())
    extractor, modelo = lid()
    onda, fm = sf.read(ruta)
    entrada = extractor(onda, sampling_rate=fm, return_tensors="pt").to(DISPOSITIVO)
    t0 = time.perf_counter()
    with torch.no_grad():
        logits = modelo(**entrada).logits[0]
    etiquetas = modelo.config.id2label
    indices = {c: [i for i, n in etiquetas.items() if n == c] for c in ("spa", "quy")}
    puntajes = {c: float(max(logits[i] for i in v)) for c, v in indices.items() if v}
    total = torch.logsumexp(torch.tensor(list(puntajes.values())), dim=0)
    probabilidades = {c: round(float(torch.exp(torch.tensor(v) - total)), 3) for c, v in puntajes.items()}
    codigo = max(probabilidades, key=probabilidades.get)
    os.unlink(ruta)
    return {"codigo": codigo, "confianza": probabilidades[codigo],
            "probabilidades": probabilidades, "ms": round((time.perf_counter() - t0) * 1000, 1)}


@aplicacion.post("/entender")
async def entender(audio: UploadFile = File(...), lengua: str = Form("quy_Latn")):
    ruta = _guardar(await audio.read())
    pipe = asr()
    t0 = time.perf_counter()
    salida = pipe.transcribe([ruta], lang=[lengua], batch_size=1)
    os.unlink(ruta)
    texto = salida[0] if salida else ""
    return {"texto": texto, "alternativas": [[texto, 1.0]], "modelo": "omniASR_LLM_300M",
            "segundos": round(time.perf_counter() - t0, 2)}


@aplicacion.post("/hablar")
def hablar(texto: str = Form(...)):
    tokenizador, modelo = tts()
    entrada = tokenizador(texto, return_tensors="pt").to(DISPOSITIVO)
    t0 = time.perf_counter()
    with torch.no_grad():
        onda = modelo(**entrada).waveform[0].cpu().numpy()
    buffer = io.BytesIO()
    sf.write(buffer, onda, modelo.config.sampling_rate, format="WAV")
    return Response(content=buffer.getvalue(), media_type="audio/wav",
                    headers={"X-Segundos": str(round(time.perf_counter() - t0, 2)),
                             "X-Modelo": "facebook/mms-tts-quy"})
