"""Translate a health instruction to Chanka Quechua and audit it before it reaches a patient.

Flow (T2 in plan/plan-completo.md):
  1. Claude extracts the critical facts from the Spanish original.
  2. Claude translates to Chanka, using the reviewed glossary.
  3. A SEPARATE call, which never sees the original, translates the Quechua back to Spanish.
  4. Claude extracts the critical facts from the back-translation.
  5. Plain code compares both (rimay.hechos.comparar). Any difference blocks the message.

Grounded in Mehandru et al. (2022): clinicians fight language barriers with back-translation and
pre-translated phrases. This automates the first one.
"""
from __future__ import annotations

import json
from pathlib import Path

import anthropic
from pydantic import BaseModel, Field

from rimay.hechos import Diferencia, Hechos, comparar

MODELO = "claude-opus-5"
GLOSARIO = Path(__file__).resolve().parent / "glosario.json"
MARCA_NO_ENTIENDO = "[no entiendo]"


class SinRespuesta(Exception):
    """Claude refused or returned nothing usable. The message must not be sent."""


class Traduccion(BaseModel):
    quechua: str = Field(description="La indicación en quechua chanka")
    terminos_inseguros: list[str] = Field(description="Palabras o frases en castellano que no sabes bien cómo decir en chanka. Lista vacía si ninguna")


class Retraduccion(BaseModel):
    castellano: str = Field(description="Traducción literal al castellano")


class Resultado(BaseModel):
    original: str
    quechua: str
    retraduccion: str
    hechos_original: Hechos
    hechos_retraducido: Hechos
    diferencias: list[Diferencia]
    terminos_inseguros: list[str]
    enviar: bool
    motivo: str


SISTEMA_EXTRAER = (
    "Extraes los datos críticos de una indicación de salud dada en una posta del Perú. "
    "Solo lo que el texto dice. Si un dato no está, va null o lista vacía. No completes nada por tu cuenta."
)

SISTEMA_TRADUCIR = (
    "Traduces indicaciones de una enfermera de la posta de Pilpichaca (Huancavelica, Perú) al quechua chanka "
    "(variedad Ayacucho-Chanka, la que se habla en Huancavelica) para un paciente que la va a escuchar en audio. "
    "Usa un registro oral, simple y respetuoso, como hablaría la enfermera. "
    "No agregues consejos, advertencias ni datos que no estén en el original, y no quites ninguno. "
    "Cada número, dosis, frecuencia y fecha tiene que quedar exacto. "
    "Si existe un término del glosario, úsalo tal cual. "
    "Si no sabes bien cómo decir algo en chanka, dilo en terminos_inseguros en vez de inventarlo."
)

SISTEMA_RETRADUCIR = (
    "Traduces al castellano, de forma literal, un texto en quechua. "
    "No corrijas, no mejores y no completes: si el texto dice algo raro, tradúcelo raro. "
    f"Si no entiendes una parte, escribe {MARCA_NO_ENTIENDO} en su lugar."
)


def cargar_glosario(ruta: Path = GLOSARIO) -> list[dict]:
    """Reviewed Spanish→Chanka terms. Only a native speaker adds entries; the model never does."""
    if not ruta.exists():
        return []
    return json.loads(ruta.read_text(encoding="utf-8"))


def _parse(client: anthropic.Anthropic, sistema: str, contenido: str, formato: type[BaseModel]):
    respuesta = client.messages.parse(
        model=MODELO,
        max_tokens=16000,
        system=sistema,
        messages=[{"role": "user", "content": contenido}],
        output_format=formato,
    )
    if respuesta.stop_reason == "refusal" or respuesta.parsed_output is None:
        raise SinRespuesta(f"stop_reason={respuesta.stop_reason}")
    return respuesta.parsed_output


def extraer_hechos(client: anthropic.Anthropic, texto_es: str) -> Hechos:
    return _parse(client, SISTEMA_EXTRAER, texto_es, Hechos)


def traducir(client: anthropic.Anthropic, texto_es: str, glosario: list[dict]) -> Traduccion:
    contenido = texto_es
    if glosario:
        lineas = "\n".join(f"- {g['castellano']} → {g['quechua']}" for g in glosario)
        contenido = f"Glosario revisado por una hablante nativa:\n{lineas}\n\nIndicación:\n{texto_es}"
    return _parse(client, SISTEMA_TRADUCIR, contenido, Traduccion)


def retraducir(client: anthropic.Anthropic, quechua: str) -> Retraduccion:
    return _parse(client, SISTEMA_RETRADUCIR, quechua, Retraduccion)


def decidir(diferencias: list[Diferencia], terminos_inseguros: list[str], retraduccion: str) -> tuple[bool, str]:
    """The send/no-send rule. Pure function, so it is tested without calling the API."""
    if diferencias:
        return False, f"cambió un dato crítico: {', '.join(d.campo for d in diferencias)}"
    if MARCA_NO_ENTIENDO in retraduccion:
        return False, "la retraducción no entiende una parte del quechua"
    if terminos_inseguros:
        return False, f"términos sin traducción segura: {', '.join(terminos_inseguros)}"
    return True, "los datos críticos coinciden"


def auditar(client: anthropic.Anthropic, texto_es: str, glosario: list[dict] | None = None) -> Resultado:
    glosario = cargar_glosario() if glosario is None else glosario
    hechos_original = extraer_hechos(client, texto_es)
    traduccion = traducir(client, texto_es, glosario)
    retraduccion = retraducir(client, traduccion.quechua)
    hechos_retraducido = extraer_hechos(client, retraduccion.castellano)

    diferencias = comparar(hechos_original, hechos_retraducido)
    enviar, motivo = decidir(diferencias, traduccion.terminos_inseguros, retraduccion.castellano)
    return Resultado(
        original=texto_es,
        quechua=traduccion.quechua,
        retraduccion=retraduccion.castellano,
        hechos_original=hechos_original,
        hechos_retraducido=hechos_retraducido,
        diferencias=diferencias,
        terminos_inseguros=traduccion.terminos_inseguros,
        enviar=enviar,
        motivo=motivo,
    )
