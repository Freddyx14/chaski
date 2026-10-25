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

from pathlib import Path

import soundfile as sf
import torch
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse, Response

aplicacion = FastAPI(title="Chaski · voz en la GPU")
DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
_modelos: dict = {}

# Los dos modelos que ajustamos. Si el archivo no esta, cada funcion cae al
# modelo de fabrica en vez de fallar: asi el servicio arranca igual en una
# maquina donde todavia no se copiaron los pesos.
# Este archivo vive en `servicio/` en el repo y suelto en la raiz de la
# instancia. Se busca `modelos/` en los dos sitios en vez de suponer uno.
_aqui = Path(__file__).resolve().parent
AQUI = _aqui if (_aqui / "modelos").exists() else _aqui.parent
RUTA_ASR_ADAPTADOR = AQUI / "modelos" / "asr-chanka" / "adaptador_mejor.pt"
RUTA_TTS_AJUSTADA = AQUI / "modelos" / "tts-p24"


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


def voces_disponibles() -> dict:
    """Las voces que hay en disco. `base` siempre esta; las demas si se entrenaron."""
    salida = {"base": "facebook/mms-tts-quy"}
    for carpeta in sorted((AQUI / "modelos").glob("tts-*")):
        if (carpeta / "model.safetensors").exists() or (carpeta / "pytorch_model.bin").exists():
            salida[carpeta.name.removeprefix("tts-")] = str(carpeta)
    return salida


def tts(voz: str = "p24"):
    """Carga una voz por nombre y la deja en memoria.

    Si la pedida no existe se cae a `base` en vez de fallar: en una demo es
    preferible una voz robotica a un 500.
    """
    from transformers import AutoTokenizer, VitsModel

    disponibles = voces_disponibles()
    nombre = voz if voz in disponibles else "base"
    clave = f"tts::{nombre}"
    if clave not in _modelos:
        tarjeta = disponibles[nombre]
        _modelos[clave + "_tok"] = AutoTokenizer.from_pretrained(tarjeta)
        _modelos[clave] = VitsModel.from_pretrained(tarjeta).to(DISPOSITIVO).eval()
    return _modelos[clave + "_tok"], _modelos[clave], nombre


def asr_ajustado():
    """MMS con nuestro adaptador. Es el que gano la medicion: 53.9% -> 40.9% de WER."""
    if "mms" not in _modelos:
        from transformers import AutoProcessor, Wav2Vec2ForCTC
        base = "facebook/mms-1b-all"
        proc = AutoProcessor.from_pretrained(base, target_lang="quy")
        modelo = Wav2Vec2ForCTC.from_pretrained(base, target_lang="quy",
                                                ignore_mismatched_sizes=True)
        if RUTA_ASR_ADAPTADOR.exists():
            modelo.load_state_dict(torch.load(RUTA_ASR_ADAPTADOR, map_location="cpu"),
                                   strict=False)
            _modelos["mms_nombre"] = "mms-1b-all + adaptador chanka"
        else:
            _modelos["mms_nombre"] = "mms-1b-all (sin adaptador)"
        _modelos["mms_proc"] = proc
        _modelos["mms"] = modelo.to(DISPOSITIVO).eval()
    return _modelos["mms_proc"], _modelos["mms"], _modelos["mms_nombre"]


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


MAXIMO_TROZO_S = 20.0   # omniASR revienta con audios largos; 44 s falla, 16 s pasa


def _partir(ruta: str) -> list[str]:
    """Parte el audio en trozos de MAXIMO_TROZO_S, cortando en el silencio mas
    cercano para no romper una palabra por la mitad."""
    onda, fm = sf.read(ruta)
    total = len(onda) / fm
    if total <= MAXIMO_TROZO_S:
        return [ruta]
    import numpy as np
    paso = int(MAXIMO_TROZO_S * fm)
    margen = int(2.0 * fm)          # busca silencio hasta 2 s antes del corte
    rutas, inicio = [], 0
    while inicio < len(onda):
        fin = min(inicio + paso, len(onda))
        if fin < len(onda):
            ventana = onda[max(fin - margen, inicio):fin]
            if len(ventana):
                energia = np.abs(ventana)
                corte_relativo = int(np.argmin(
                    np.convolve(energia, np.ones(int(0.05 * fm)) / (0.05 * fm), mode="same")))
                fin = max(fin - margen, inicio) + corte_relativo
        trozo = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(trozo.name, onda[inicio:fin], fm)
        rutas.append(trozo.name)
        inicio = fin
    return rutas


@aplicacion.post("/entender")
async def entender(audio: UploadFile = File(...), lengua: str = Form("quy_Latn"),
                   ajustado: bool = Form(False)):
    """`ajustado=true` usa MMS con nuestro adaptador en vez de omniASR.

    Medido sobre el hablante apartado: omniASR 54.1 % de WER, MMS ajustado
    40.9 %. Va detras de un interruptor y no por defecto porque omniASR sigue
    siendo el que escribe en ortografia legible; el ajustado escribe en la
    normalizada, que es mejor numero y peor lectura.
    """
    datos = await audio.read()
    if ajustado:
        import numpy as np
        proc, modelo, nombre = asr_ajustado()
        ruta = _guardar(datos)
        try:
            onda, frecuencia = sf.read(ruta, dtype="float32")
        finally:
            os.unlink(ruta)
        if onda.ndim > 1:
            onda = onda.mean(axis=1)
        t0 = time.perf_counter()
        entrada = proc(onda, sampling_rate=frecuencia,
                       return_tensors="pt").input_values.to(DISPOSITIVO)
        with torch.no_grad():
            ids = torch.argmax(modelo(entrada).logits, dim=-1)
        texto = proc.batch_decode(ids)[0]
        return {"texto": texto, "alternativas": [[texto, 1.0]], "modelo": nombre,
                "trozos": 1, "segundos": round(time.perf_counter() - t0, 2)}

    ruta = _guardar(datos)
    pipe = asr()
    t0 = time.perf_counter()
    trozos = _partir(ruta)
    try:
        salida = pipe.transcribe(trozos, lang=[lengua] * len(trozos), batch_size=1)
        texto = " ".join(s.strip() for s in salida if s and s.strip())
    finally:
        for t in trozos:
            if t != ruta:
                os.unlink(t)
        os.unlink(ruta)
    return {"texto": texto, "alternativas": [[texto, 1.0]], "modelo": "omniASR_LLM_300M",
            "trozos": len(trozos), "segundos": round(time.perf_counter() - t0, 2)}


@aplicacion.get("/voces")
def voces():
    """Qué voces se pueden pedir en `/hablar`."""
    return {"voces": sorted(voces_disponibles()), "por_defecto": "p24"}


@aplicacion.post("/hablar")
def hablar(texto: str = Form(...), voz: str = Form("p24")):
    """`voz` elige cuál habla: base, p24, p16, mama_freddy, papa_ricardo."""
    tokenizador, modelo, nombre = tts(voz)
    entrada = tokenizador(texto, return_tensors="pt").to(DISPOSITIVO)
    t0 = time.perf_counter()
    with torch.no_grad():
        onda = modelo(**entrada).waveform[0].cpu().numpy()
    buffer = io.BytesIO()
    sf.write(buffer, onda, modelo.config.sampling_rate, format="WAV")
    return Response(content=buffer.getvalue(), media_type="audio/wav",
                    headers={"X-Segundos": str(round(time.perf_counter() - t0, 2)),
                             "X-Modelo": nombre})
