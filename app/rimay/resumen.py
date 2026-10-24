"""Summary of a consultation (F11), shaped by who is reading it (D27).

The same conversation produces two different documents:
  - personal: a short clinical note in Spanish for the health record, plus what still needs checking.
  - paciente: the instructions to take home, in plain Spanish. The app then sends that text through the
    audited translation (rimay.auditoria) before it is ever said in Quechua, so the summary never
    bypasses the audit.

What the model may NOT decide is decided in code: a turn that the audit blocked was never said to the
patient, so it can never appear as an instruction. It goes to `no_se_dijo` instead.
"""
from __future__ import annotations

from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from rimay.auditoria import SinRespuesta

MODELO = "claude-sonnet-5"

Rol = Literal["personal", "paciente"]


class Turno(BaseModel):
    lado: Literal["castellano", "quechua"]
    castellano: str = ""
    quechua: str = ""
    estado: Literal["dicho", "dicho_con_aviso", "bloqueado", "entendido", "con_dudas"]


class Borrador(BaseModel):
    """What Claude writes. Everything here must come from the turns it was given."""
    resumen: str = Field(description="Dos a cuatro frases sobre la consulta")
    indicaciones: list[str] = Field(description="Cada indicación dicha al paciente, una por línea, con dosis, horario y días exactos. Lista vacía si no hubo")
    senales_de_alarma: list[str] = Field(description="Señales por las que debe volver de inmediato, solo si se dijeron. Lista vacía si no")
    proxima_cita: str | None = Field(description="Cuándo debe volver, solo si se dijo. null si no")
    dudas: list[str] = Field(description="Lo que no quedó claro en la conversación y conviene confirmar. Lista vacía si nada")


class Resumen(Borrador):
    rol: Rol
    no_se_dijo: list[str]


SISTEMA = {
    "personal": (
        "Escribes la nota de una consulta en una posta de salud de Huancavelica, Perú, para la historia clínica. "
        "La conversación fue entre el personal de salud (castellano) y un paciente quechuahablante, con un intérprete. "
        "Castellano clínico, breve y exacto. Solo lo que aparece en los turnos: no agregues diagnósticos, "
        "medicamentos, dosis ni consejos que nadie dijo. Si algo del paciente vino marcado con dudas, va en dudas."
    ),
    "paciente": (
        "Escribes, para un paciente de una posta de salud de Huancavelica, Perú, lo que tiene que hacer en casa "
        "después de su consulta. Castellano muy simple, frases cortas, de tú a tú y con respeto, porque después se "
        "traduce al quechua y se le dice en voz alta. Solo lo que el personal de salud dijo en los turnos: "
        "no agregues consejos, medicamentos ni datos que nadie dijo, y no quites ninguno. Cada número exacto."
    ),
}


def _conversacion(turnos: list[Turno]) -> str:
    lineas = []
    for i, t in enumerate(turnos, 1):
        if t.estado == "bloqueado":
            continue  # nunca llegó al paciente
        quien = "Habla en castellano" if t.lado == "castellano" else "Habla en quechua (lo que quiso decir)"
        marca = " [con dudas]" if t.estado in ("con_dudas", "dicho_con_aviso") else ""
        lineas.append(f"{i}. {quien}{marca}: {t.castellano}")
    return "\n".join(lineas)


def no_se_dijo(turnos: list[Turno]) -> list[str]:
    """Turns the audit blocked. Pure, so it is tested without the API."""
    return [t.castellano for t in turnos if t.estado == "bloqueado"]


def resumir(client: anthropic.Anthropic, turnos: list[Turno], rol: Rol, modelo: str = MODELO) -> Resumen:
    bloqueados = no_se_dijo(turnos)
    conversacion = _conversacion(turnos)
    if not conversacion:
        return Resumen(rol=rol, resumen="La consulta no tuvo turnos que se hayan dicho.", indicaciones=[],
                       senales_de_alarma=[], proxima_cita=None, dudas=[], no_se_dijo=bloqueados)
    respuesta = client.messages.parse(
        model=modelo,
        max_tokens=4000,
        system=SISTEMA[rol],
        messages=[{"role": "user", "content": f"Turnos de la consulta:\n{conversacion}"}],
        output_format=Borrador,
    )
    if respuesta.stop_reason == "refusal" or respuesta.parsed_output is None:
        raise SinRespuesta(f"stop_reason={respuesta.stop_reason}")
    return Resumen(**respuesta.parsed_output.model_dump(), rol=rol, no_se_dijo=bloqueados)


def texto_para_decir(r: Resumen) -> str:
    """The take-home text for the patient, in Spanish, ready for rimay.auditoria. Only what was said."""
    partes = list(r.indicaciones)
    if r.senales_de_alarma:
        partes.append("Venga a la posta de inmediato si: " + ", ".join(r.senales_de_alarma) + ".")
    if r.proxima_cita:
        partes.append(f"Su próximo control: {r.proxima_cita}.")
    return " ".join(p if p.endswith(".") else p + "." for p in partes)
