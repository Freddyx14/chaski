"""Servicio de prueba de Chaski: cámara o foto -> Claude -> qué es y para qué sirve.

Esto NO es la app de Freddy. Es el banco de pruebas para enchufar la visión
antes de que la UI exista, y para que los dos podamos probarla desde el navegador.

Arranque:
  cd ricardo-artifacts
  set -a; source .env; set +a
  uv run --with fastapi --with uvicorn --with anthropic --with python-multipart \
      uvicorn servicio.app:aplicacion --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# El modulo de traduccion y auditoria es de Freddy. Se IMPORTA, no se copia ni
# se toca: si el mejora el glosario o la auditoria, esto lo hereda solo.
APP_DE_FREDDY = (Path(__file__).resolve().parents[2] / "app")
if APP_DE_FREDDY.exists() and str(APP_DE_FREDDY) not in sys.path:
    sys.path.insert(0, str(APP_DE_FREDDY))

from fastapi import FastAPI, File, Form, UploadFile
from fastapi import Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from servicio.vision import MODELO, como_json, leer

try:
    import anthropic
    from rimay.auditoria import auditar
    HAY_TRADUCTOR = True
except Exception as _e:          # el repo puede no tener app/ al lado
    HAY_TRADUCTOR = False
    _FALLO_TRADUCTOR = str(_e)

AQUI = Path(__file__).parent
CHASKI = Path("../design/chaski")

aplicacion = FastAPI(title="Chaski · banco de pruebas de visión")
aplicacion.mount("/estatico", StaticFiles(directory=AQUI / "static"), name="estatico")
if CHASKI.exists():
    aplicacion.mount("/chaski", StaticFiles(directory=CHASKI), name="chaski")


@aplicacion.get("/")
def portada():
    return FileResponse(AQUI / "static" / "index.html")


@aplicacion.get("/salud")
def salud():
    return {"modelo_vision": MODELO,
            "clave_anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "clave_cartesia": bool(os.environ.get("CARTESIA_API_KEY")),
            "chaski": CHASKI.exists(),
            "traductor_de_freddy": HAY_TRADUCTOR}


@aplicacion.get("/flujo")
def pagina_flujo():
    return FileResponse(AQUI / "static" / "flujo.html")


CARPETAS_MUESTRAS = (Path("datos/muestras_quy"), Path("datos/prueba_minima"))


@aplicacion.get("/muestras")
def muestras():
    """Los audios en chanka que pueden hacer de paciente, con su texto de referencia."""
    salida = []
    for carpeta in CARPETAS_MUESTRAS:
        if not carpeta.exists():
            continue
        fichas = {}
        ficha = carpeta / "fichas.json"
        if ficha.exists():
            for f in json.loads(ficha.read_text(encoding="utf-8")):
                fichas[f.get("archivo", "")] = f
        for wav in sorted(carpeta.glob("quy_*.wav")):
            f = fichas.get(wav.name, {})
            salida.append({"nombre": wav.name, "carpeta": carpeta.name,
                           "segundos": f.get("segundos"),
                           "frases": f.get("frases"),
                           "referencia": f.get("chanka", ""),
                           "castellano": f.get("castellano", "")})
    return {"audios": salida}


@aplicacion.get("/muestras/{nombre}")
def muestra(nombre: str):
    for carpeta in CARPETAS_MUESTRAS:
        ruta = carpeta / nombre
        if ruta.exists():
            return FileResponse(ruta)
    return JSONResponse({"error": "no existe"}, 404)


@aplicacion.post("/escuchar")
async def escuchar(audio: UploadFile = File(...)):
    """Voz de la enfermera en castellano -> texto, con Cartesia."""
    from servicio.flujo import entender_castellano
    try:
        return entender_castellano(await audio.read(), audio.filename or "turno.webm")
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/turno/paciente")
async def turno_paciente(audio: UploadFile = File(...)):
    from servicio.flujo import turno_del_paciente
    try:
        return turno_del_paciente(await audio.read(), audio.filename or "turno.wav")
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/turno/enfermera")
def turno_enfermera(texto: str = Form(...), modo_ensayo: bool = Form(True),
                    forzar: bool = Form(False), rapido: bool = Form(True),
                    con_audio: bool = Form(False)):
    from servicio.flujo import turno_de_la_enfermera
    try:
        return turno_de_la_enfermera(texto, modo_ensayo=modo_ensayo, forzar=forzar,
                                     rapido=rapido, con_audio=con_audio)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.get("/corregir")
def pagina_corregir():
    return FileResponse(AQUI / "static" / "corregir.html")


@aplicacion.get("/corpus/personas")
def corpus_personas():
    from servicio.corpus import personas
    return {"personas": personas()}


@aplicacion.get("/corpus/clips")
def corpus_clips(persona: str):
    from servicio.corpus import clips
    return {"clips": clips(persona)}


@aplicacion.get("/corpus/audio")
def corpus_audio(ruta: str):
    p = Path(ruta)
    return FileResponse(p) if p.exists() else JSONResponse({"error": "no existe"}, 404)


@aplicacion.post("/corpus/subir")
async def corpus_subir(audio: UploadFile = File(...), persona: str = Form(...),
                       bloque: str = Form("A"), esperadas: int = Form(0)):
    """Nota de voz larga -> clips numerados listos para corregir."""
    from servicio.corpus import recibir_nota
    try:
        return recibir_nota(persona, bloque, await audio.read(), audio.filename or "nota.ogg",
                            esperadas=esperadas)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/transcribir")
def corpus_transcribir(ruta: str = Form(...)):
    from servicio.corpus import transcribir
    try:
        return transcribir(ruta)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/codigo")
def corpus_codigo(ruta: str = Form(...)):
    """Detecta el identificador (C1, M5...) oyendo el principio del clip."""
    from servicio.corpus import detectar_codigo
    try:
        return detectar_codigo(ruta)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/recodificar")
def corpus_recodificar(persona: str = Form(...), bloque_actual: str = Form(...),
                       numero_actual: int = Form(...), bloque_nuevo: str = Form(...),
                       numero_nuevo: int = Form(...)):
    from servicio.corpus import recodificar
    try:
        return recodificar(persona, numero_actual, bloque_actual, bloque_nuevo, numero_nuevo)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/guardar")
def corpus_guardar(persona: str = Form(...), numero: int = Form(...),
                   transcripcion: str = Form(""), consentimiento: bool = Form(True),
                   descartar: bool = Form(False)):
    from servicio.corpus import guardar
    try:
        return guardar(persona, numero, transcripcion, consentimiento, descartar)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/exportar")
def corpus_exportar(persona: str = Form("")):
    from servicio.corpus import exportar
    return exportar(persona or None)


@aplicacion.post("/voz")
def voz(texto: str = Form(...)):
    """Solo la voz, para pedirla DESPUÉS de mostrar el texto."""
    from servicio.flujo import decir_en_voz
    try:
        audio, ms = decir_en_voz(texto)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return Response(content=audio, media_type="audio/wav", headers={"X-Ms": str(ms)})


@aplicacion.post("/traducir")
def traducir(texto: str = Form(...)):
    """Castellano -> chanka, con la auditoria de retraduccion de Freddy.

    No traduce Haiku: traduce `rimay.auditoria`, que usa Opus 5 con glosario,
    retraduce A CIEGAS y compara los datos criticos con codigo. Si algo cambio,
    `enviar` viene en false y NO se dice en voz alta.
    """
    if not HAY_TRADUCTOR:
        return JSONResponse({"error": f"falta el modulo de Freddy: {_FALLO_TRADUCTOR}"},
                            status_code=503)
    t0 = time.perf_counter()
    try:
        r = auditar(anthropic.Anthropic(), texto)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return {"quechua": r.quechua, "retraduccion": r.retraduccion, "enviar": r.enviar,
            "motivo": r.motivo, "terminos_inseguros": r.terminos_inseguros,
            "diferencias": [d.model_dump() for d in r.diferencias],
            "segundos": round(time.perf_counter() - t0, 2)}


@aplicacion.post("/ver")
async def ver(imagen: UploadFile = File(...), dicho: str = Form(""),
              modelo: str = Form("")):
    datos = await imagen.read()
    try:
        lectura = leer(datos, dicho_por_la_enfermera=dicho or None, modelo=modelo or MODELO)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return como_json(lectura)
