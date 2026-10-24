"""Lee una caja de medicamento o una receta y explica para que sirve.

Tres capas, y la tercera es la que importa:
  1. Leer el nombre, la dosis y la presentacion.
  2. Cruzarlo con lo que dijo la enfermera (si lo dijo).
  3. Explicar PARA QUE SIRVE, en castellano y en quechua chanka.

Regla que no se negocia: si no se lee con seguridad, NO se adivina. Una dosis
mal leida es peor que no leer nada. El campo `seguro` manda sobre todo lo demas.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from anthropic import Anthropic

MODELO = os.environ.get("CHASKI_MODELO_VISION", "claude-haiku-4-5")
TIPOS = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
         ".webp": "image/webp", ".gif": "image/gif"}

SISTEMA = """Eres la parte de Chaski que lee medicamentos en una posta de salud rural del Perú.
Te llega la foto de una caja, un blíster o una receta escrita a mano.

Devuelves SOLO un objeto JSON, sin texto alrededor, con estas claves:

{
 "seguro": true|false,
 "no_leido": ["qué no se pudo leer con seguridad"],
 "medicamento": "nombre genérico como aparece, o null",
 "concentracion": "por ejemplo 500 mg, o null",
 "presentacion": "tabletas, jarabe, ampolla, o null",
 "para_que_sirve": "una o dos frases en castellano llano, sin jerga médica",
 "para_que_sirve_chanka": "lo mismo en quechua chanka, o null si no estás seguro",
 "advertencias": ["lo que una persona debe saber antes de tomarlo"],
 "coincide_con_lo_dicho": true|false|null
}

Reglas:
- Si la dosis o el nombre no se leen con seguridad, pon "seguro": false y deja ese campo en null.
  NUNCA inventes una dosis ni completes un nombre a medias. Es una posta, no un juego.
- "para_que_sirve" se lo va a escuchar una persona que no estudió medicina. Nada de "analgésico
  antipirético": di "baja la fiebre y calma el dolor".
- El quechua chanka solo si de verdad lo sabes decir. Si dudas, null. Otro sistema lo va a auditar.
- Si te dan `dicho_por_la_enfermera`, compara el nombre y pon "coincide_con_lo_dicho"."""


@dataclass
class Lectura:
    seguro: bool
    medicamento: str | None
    concentracion: str | None
    presentacion: str | None
    para_que_sirve: str
    para_que_sirve_chanka: str | None
    advertencias: list
    no_leido: list
    coincide_con_lo_dicho: bool | None
    modelo: str
    segundos: float
    tokens_entrada: int
    tokens_salida: int


def _tipo(ruta: Path) -> str:
    return TIPOS.get(ruta.suffix.lower(), "image/jpeg")


def _json_de(texto: str) -> dict:
    bloque = re.search(r"\{.*\}", texto, re.S)
    if not bloque:
        raise ValueError(f"la respuesta no trae JSON: {texto[:200]}")
    return json.loads(bloque.group(0))


def leer(imagen: bytes | str | Path, dicho_por_la_enfermera: str | None = None,
         modelo: str = MODELO) -> Lectura:
    if isinstance(imagen, (str, Path)):
        ruta = Path(imagen)
        datos, tipo = ruta.read_bytes(), _tipo(ruta)
    else:
        datos, tipo = imagen, "image/jpeg"

    pedido = "Lee esta imagen."
    if dicho_por_la_enfermera:
        pedido += f'\nLa enfermera dijo: "{dicho_por_la_enfermera}". Compara el nombre.'

    cliente = Anthropic()
    t0 = time.perf_counter()
    respuesta = cliente.messages.create(
        model=modelo,
        max_tokens=1024,
        system=SISTEMA,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": tipo,
                                         "data": base64.b64encode(datos).decode()}},
            {"type": "text", "text": pedido},
        ]}],
    )
    segundos = round(time.perf_counter() - t0, 2)
    crudo = "".join(b.text for b in respuesta.content if b.type == "text")
    d = _json_de(crudo)

    return Lectura(
        seguro=bool(d.get("seguro")),
        medicamento=d.get("medicamento"),
        concentracion=d.get("concentracion"),
        presentacion=d.get("presentacion"),
        para_que_sirve=d.get("para_que_sirve") or "",
        para_que_sirve_chanka=d.get("para_que_sirve_chanka"),
        advertencias=d.get("advertencias") or [],
        no_leido=d.get("no_leido") or [],
        coincide_con_lo_dicho=d.get("coincide_con_lo_dicho"),
        modelo=modelo, segundos=segundos,
        tokens_entrada=respuesta.usage.input_tokens,
        tokens_salida=respuesta.usage.output_tokens)


def como_json(lectura: Lectura) -> dict:
    return asdict(lectura)
