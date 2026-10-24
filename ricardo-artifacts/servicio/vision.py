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
 "coincide_con_lo_dicho": true|false|null,
 "cantidad": número o null,
 "unidad": "tableta, cucharada, gota, o null",
 "cada_horas": número o null,
 "dias": número o null,
 "posologia_de": "receta" | "caja" | "falta"
}

Reglas:
- Si la dosis o el nombre no se leen con seguridad, pon "seguro": false y deja ese campo en null.
  NUNCA inventes una dosis ni completes un nombre a medias. Es una posta, no un juego.
- "para_que_sirve" se lo va a escuchar una persona que no estudió medicina. Nada de "analgésico
  antipirético": di "baja la fiebre y calma el dolor".
- El quechua chanka solo si de verdad lo sabes decir. Si dudas, null. Otro sistema lo va a auditar.
- Si te dan `dicho_por_la_enfermera`, compara el nombre y pon "coincide_con_lo_dicho".

Sobre la posología (cuánto, cada cuánto, cuántos días):
- Una RECETA la trae escrita: léela y pon "posologia_de": "receta".
- Una CAJA normalmente NO la trae. La caja dice qué es el medicamento, no cuánto le toca a ESTE
  paciente. Si la caja tiene una pauta impresa de fábrica, úsala y pon "posologia_de": "caja".
- Si no está, pon los cuatro campos en null y "posologia_de": "falta". La enfermera la escribe.
  NUNCA deduzcas una dosis del nombre del medicamento ni de lo que suele indicarse. Una dosis
  inventada que suena razonable es el peor error que puede cometer este sistema."""


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
    cantidad: float | None
    unidad: str | None
    cada_horas: float | None
    dias: float | None
    posologia_de: str
    modelo: str
    segundos: float
    tokens_entrada: int
    tokens_salida: int


def _numero(valor) -> float | None:
    """Un numero o nada. Nunca un texto a medias convertido a la fuerza."""
    if valor is None or isinstance(valor, bool):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def indicacion(lectura: "Lectura") -> str | None:
    """Arma la frase en castellano desde los numeros, con una plantilla.

    La frase NO la escribe el modelo. La escribe esta funcion a partir de los
    campos que ya se leyeron, porque una plantilla no puede cambiar una dosis
    mientras redacta. Lo que el modelo aporta es leer; componer es de codigo.

    Devuelve None si falta la posologia: ahi la enfermera tiene que escribir
    cada cuantas horas y cuantos dias, y hasta que lo haga no hay indicacion
    que decir.
    """
    if lectura.cantidad is None or lectura.cada_horas is None:
        return None
    unidad = lectura.unidad or "tableta"
    # «media tableta», no «0,5 tabletas». Media pastilla es lo que de verdad se
    # dice en una posta, y ademas un «0,5» dicho en voz alta se presta a
    # entenderse como otra cosa.
    if lectura.cantidad == 0.5:
        frase_cantidad = f"media {unidad}"
    else:
        if lectura.cantidad != 1:
            unidad += "s"
        frase_cantidad = f"{lectura.cantidad:g}".replace(".", ",") + f" {unidad}"
    partes = [f"Tome {frase_cantidad} cada {lectura.cada_horas:g} horas"]
    if lectura.dias:
        partes.append(f"durante {lectura.dias:g} días")
    return " ".join(partes) + "."


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
        cantidad=_numero(d.get("cantidad")),
        unidad=d.get("unidad"),
        cada_horas=_numero(d.get("cada_horas")),
        dias=_numero(d.get("dias")),
        posologia_de=d.get("posologia_de") or "falta",
        modelo=modelo, segundos=segundos,
        tokens_entrada=respuesta.usage.input_tokens,
        tokens_salida=respuesta.usage.output_tokens)


def como_json(lectura: Lectura) -> dict:
    d = asdict(lectura)
    # La indicacion lista para traducir, y que falta para poder armarla. La app
    # usa `faltan` para saber que preguntarle a la enfermera.
    d["indicacion"] = indicacion(lectura)
    d["faltan"] = [c for c in ("cantidad", "cada_horas")
                   if getattr(lectura, c) is None]
    # Una pauta leida de la CAJA es lo que el laboratorio sugiere para un adulto
    # cualquiera, no lo que le toca a este paciente. Un nino, una embarazada o
    # alguien que ya toma otra cosa necesitan otra. Solo la RECETA es de esta
    # persona. Por eso lo de la caja sale marcado para confirmar: la enfermera
    # lo aprueba o lo corrige antes de que Chaski lo diga.
    d["confirmar"] = lectura.posologia_de == "caja"
    d["porque_confirmar"] = (
        "la pauta viene impresa en la caja, es la del fabricante para adultos; "
        "confírmela o corríjala para este paciente"
        if d["confirmar"] else None)
    return d
