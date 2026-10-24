"""Critical facts of a health instruction, and the deterministic comparison between two of them.

The comparison is plain code on purpose: the model extracts, code decides. If a dose, a frequency,
a duration or a date changed between the original and the back-translation, the message is blocked.
"""
from __future__ import annotations

import unicodedata

from pydantic import BaseModel, Field


class Medicamento(BaseModel):
    nombre: str = Field(description="Nombre del medicamento en minúsculas, sin marca si hay genérico. Ej: 'sulfato ferroso'")
    cantidad: float | None = Field(description="Cuántas unidades por toma. Ej: 1 pastilla → 1. null si no se dice")
    unidad: str | None = Field(description="Unidad de la toma en singular y minúsculas: 'pastilla', 'cucharada', 'ml', 'gota'. null si no se dice")
    cada_horas: float | None = Field(description="Cada cuántas horas se toma. 'una vez al día' → 24, 'tres veces al día' → 8. null si no se dice")
    dias: int | None = Field(description="Durante cuántos días. 'un mes' → 30, 'una semana' → 7. null si no se dice o si es indefinido")
    momento: str | None = Field(description="Momento de la toma en pocas palabras: 'después del almuerzo', 'en ayunas'. null si no se dice")


class Hechos(BaseModel):
    medicamentos: list[Medicamento] = Field(description="Cada medicamento indicado. Lista vacía si no hay")
    proxima_cita_en_dias: int | None = Field(description="En cuántos días debe volver. 'en un mes' → 30. null si no se dice")
    ir_ya_si: list[str] = Field(description="Señales por las que debe volver de inmediato, cada una en 2 a 5 palabras. Lista vacía si no se mencionan")


class Diferencia(BaseModel):
    campo: str
    original: str
    retraducido: str


def _norm(texto: str | None) -> str:
    if texto is None:
        return ""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().split())


# Nombres que no identifican un medicamento: «tome una pastilla» no dice cuál. Con estos el emparejamiento
# entre original y retraducción va por orden, no por nombre (falso bloqueo medido el 24-oct en vivo).
_GENERICOS = {"", "pastilla", "pastillas", "tableta", "tabletas", "comprimido", "medicamento", "medicina",
              "remedio", "jarabe", "gotas"}
# Unidades que son la misma cosa dicha de otra forma (falso bloqueo «tableta» vs «pastilla», 24-oct).
_UNIDADES = {"tableta": "pastilla", "comprimido": "pastilla", "pastillas": "pastilla", "tabletas": "pastilla"}


def _generico(nombre: str | None) -> bool:
    n = _norm(nombre)
    return n in _GENERICOS or not any(c.isalpha() for c in n)


def _unidad(u: str | None) -> str:
    n = _norm(u)
    return _UNIDADES.get(n, n)


def _mismo_numero(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) < 1e-6


def comparar(original: Hechos, retraducido: Hechos) -> list[Diferencia]:
    """Every critical difference between the original instruction and the back-translation.

    Numbers must match exactly. Medicine names are matched after normalising accents and case.
    The free-text 'momento' and the warning-sign wording are not compared here: they are paraphrased
    legitimately in translation, and the fixed warning signs are reviewed by a human instead.
    """
    difs: list[Diferencia] = []

    if not _mismo_numero(original.proxima_cita_en_dias, retraducido.proxima_cita_en_dias):
        difs.append(Diferencia(campo="proxima_cita_en_dias",
                               original=str(original.proxima_cita_en_dias),
                               retraducido=str(retraducido.proxima_cita_en_dias)))

    if len(original.ir_ya_si) != len(retraducido.ir_ya_si):
        difs.append(Diferencia(campo="ir_ya_si (cantidad de señales)",
                               original=str(len(original.ir_ya_si)),
                               retraducido=str(len(retraducido.ir_ya_si))))

    restantes = list(retraducido.medicamentos)
    pares: list[tuple] = []
    sin_par = []
    for med in original.medicamentos:
        otro = next((m for m in restantes if _norm(m.nombre) == _norm(med.nombre)), None)
        if otro is not None:
            restantes.remove(otro)
            pares.append((med, otro))
        else:
            sin_par.append(med)
    # Segundo paso: si un lado no nombra el medicamento, se empareja por orden.
    for med in list(sin_par):
        otro = next((m for m in restantes if _generico(m.nombre) or _generico(med.nombre)), None)
        if otro is not None:
            restantes.remove(otro)
            sin_par.remove(med)
            pares.append((med, otro))
    for med in sin_par:
        difs.append(Diferencia(campo="medicamento", original=med.nombre, retraducido="(falta)"))

    for med, otro in pares:
        nombre = med.nombre if not _generico(med.nombre) else (otro.nombre if not _generico(otro.nombre) else "medicamento")
        for campo in ("cantidad", "cada_horas", "dias"):
            a, b = getattr(med, campo), getattr(otro, campo)
            if not _mismo_numero(a, b):
                difs.append(Diferencia(campo=f"{nombre}.{campo}", original=str(a), retraducido=str(b)))
        if _unidad(med.unidad) != _unidad(otro.unidad):
            difs.append(Diferencia(campo=f"{nombre}.unidad", original=str(med.unidad), retraducido=str(otro.unidad)))

    for sobrante in restantes:
        difs.append(Diferencia(campo="medicamento", original="(no estaba)", retraducido=sobrante.nombre))

    return difs
