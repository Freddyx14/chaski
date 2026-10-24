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
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from servicio.vision import MODELO, como_json, leer

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
            "chaski": CHASKI.exists()}


@aplicacion.post("/ver")
async def ver(imagen: UploadFile = File(...), dicho: str = Form(""),
              modelo: str = Form("")):
    datos = await imagen.read()
    try:
        lectura = leer(datos, dicho_por_la_enfermera=dicho or None, modelo=modelo or MODELO)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return como_json(lectura)
