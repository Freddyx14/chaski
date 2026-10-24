"""Critical facts of a health instruction, and the deterministic comparison between two of them.

The comparison is plain code on purpose: the model extracts, code decides. If a dose, a frequency,
a duration or a date changed between the original and the back-translation, the message is blocked.

B6 (plan/arquitectura-interprete.md §2b) adds the facts that used to slip through: prohibitions
(«no lo tome con té» vs «tómelo con té»), body parts, allergies, the route of each medicine and
pregnancy. They are compared as counts or as code-normalised canonical values, never as free
wording, so a legitimate paraphrase does not block.
"""
from __future__ import annotations

import unicodedata
from typing import Literal

from pydantic import BaseModel, Field

Via = Literal["oral", "piel", "ojos", "oidos", "inyectable", "otra"]


class Medicamento(BaseModel):
    nombre: str = Field(description="Nombre del medicamento en minúsculas, sin marca si hay genérico. Ej: 'sulfato ferroso'")
    cantidad: float | None = Field(description="Cuántas unidades por toma. Ej: 1 pastilla → 1. null si no se dice")
    unidad: str | None = Field(description="Unidad de la toma en singular y minúsculas: 'pastilla', 'cucharada', 'ml', 'gota'. null si no se dice")
    cada_horas: float | None = Field(description="Cada cuántas horas se toma. 'una vez al día' → 24, 'tres veces al día' → 8. null si no se dice")
    dias: int | None = Field(description="Durante cuántos días. 'un mes' → 30, 'una semana' → 7. null si no se dice o si es indefinido")
    momento: str | None = Field(description="Momento de la toma en pocas palabras: 'después del almuerzo', 'en ayunas'. null si no se dice")
    via: Via | None = Field(default=None, description=(
        "Por dónde entra el medicamento: 'oral' (tomar, tragar, beber, por la boca, jarabe), 'piel' (untar, "
        "frotar, crema, pomada), 'ojos' (gotas en los ojos), 'oidos' (gotas en el oído), 'inyectable' "
        "(inyección, ampolla, vacuna), 'otra' (vía distinta a las anteriores). null si el texto no lo dice "
        "ni lo indica el verbo"))


class Hechos(BaseModel):
    medicamentos: list[Medicamento] = Field(description="Cada medicamento indicado. Lista vacía si no hay")
    proxima_cita_en_dias: int | None = Field(description="En cuántos días debe volver. 'en un mes' → 30. null si no se dice")
    ir_ya_si: list[str] = Field(description="Señales por las que debe volver de inmediato, cada una en 2 a 5 palabras. Lista vacía si no se mencionan")
    prohibiciones: list[str] = Field(default_factory=list, description=(
        "Cada cosa que el texto dice que NO se haga, una por elemento, en infinitivo y sin la palabra 'no': "
        "«no lo tome con té» → 'tomar con té'; «no deje la pastilla» → 'dejar la pastilla'; «tómela con agua, "
        "no con té» → 'tomar con té'. Solo prohibiciones e instrucciones negadas; una pregunta o una "
        "afirmación negativa ('no tengo fiebre') no es prohibición. Lista vacía si no hay"))
    partes_cuerpo: list[str] = Field(default_factory=list, description=(
        "Cada parte del cuerpo que se menciona, en castellano, en singular, sin artículo ni posesivo: "
        "«me duele la barriga» → 'barriga'; «en los ojos» → 'ojo'. Lista vacía si no se menciona ninguna"))
    alergias: list[str] = Field(default_factory=list, description=(
        "Cada cosa a la que el texto dice que la persona SÍ es alérgica, solo el nombre en minúsculas y "
        "singular: «alérgica a la penicilina» → 'penicilina'. «No soy alérgico a nada» o una pregunta "
        "('¿es alérgica a algo?') → lista vacía"))
    embarazo: bool | None = Field(default=None, description=(
        "true si el texto afirma que la paciente está embarazada, false si afirma que no lo está, "
        "null si no se dice. Una pregunta ('¿está embarazada?') es null"))


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


# Body-part synonyms → one canonical value, so «barriga» and «estómago» compare equal (B6).
_PARTES = {
    "barriga": "abdomen", "estomago": "abdomen", "panza": "abdomen", "vientre": "abdomen", "guata": "abdomen",
    "tripa": "abdomen", "abdomen": "abdomen", "boca del estomago": "abdomen",
    "cabeza": "cabeza", "craneo": "cabeza",
    "ojo": "ojo", "ojos": "ojo", "vista": "ojo",
    "oido": "oido", "oidos": "oido", "oreja": "oido", "orejas": "oido",
    "garganta": "garganta", "pecho": "pecho", "torax": "pecho",
    "diente": "diente", "dientes": "diente", "muela": "diente", "muelas": "diente",
    "riñon": "riñon", "rinon": "riñon", "riñones": "riñon", "rinones": "riñon",
    "pulmon": "pulmon", "pulmones": "pulmon", "utero": "utero", "matriz": "utero",
}
_ARTICULOS = ("a la ", "a los ", "a las ", "al ", "del ", "de la ", "la ", "el ", "los ", "las ", "mi ", "mis ",
              "su ", "sus ", "a ", "un ", "una ")
_NADA = {"", "nada", "ninguna", "ninguno", "ningun", "ningun remedio", "ninguna cosa"}


def _sin_articulo(texto: str | None) -> str:
    n = _norm(texto)
    cambiado = True
    while cambiado:
        cambiado = False
        for art in _ARTICULOS:
            if n.startswith(art):
                n, cambiado = n[len(art):], True
    return n


def _singular(n: str) -> str:
    if len(n) > 4 and n.endswith("es") and n[-3] in "lnrd":
        return n[:-2]
    if len(n) > 3 and n.endswith("s") and not n.endswith("is"):
        return n[:-1]
    return n


def parte_canonica(parte: str | None) -> str:
    """'la barriga' → 'abdomen'. Unknown parts fall back to the accent-free singular."""
    n = _sin_articulo(parte)
    if n in _PARTES:
        return _PARTES[n]
    return _PARTES.get(_singular(n), _singular(n))


def alergia_canonica(alergia: str | None) -> str:
    """'a la Penicilina' → 'penicilina'. 'nada' / 'ninguna' → ''."""
    n = _sin_articulo(alergia)
    return "" if n in _NADA else _singular(n)


def conjunto_partes(h: Hechos) -> set[str]:
    return {p for p in (parte_canonica(x) for x in h.partes_cuerpo) if p}


def conjunto_alergias(h: Hechos) -> set[str]:
    return {a for a in (alergia_canonica(x) for x in h.alergias) if a}


def _mismo_numero(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) < 1e-6


def emparejar(a: list[Medicamento], b: list[Medicamento]):
    """Pair medicines by normalised name, then, if one side does not name it, by order.

    Returns (pairs, unmatched from a, unmatched from b).
    """
    restantes = list(b)
    pares: list[tuple] = []
    sin_par = []
    for med in a:
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
    return pares, sin_par, restantes


def comparar(original: Hechos, retraducido: Hechos) -> list[Diferencia]:
    """Every critical difference between the original instruction and the back-translation.

    Numbers must match exactly. Medicine names are matched after normalising accents and case.
    The free-text 'momento' and the warning-sign wording are not compared here: they are paraphrased
    legitimately in translation, and the fixed warning signs are reviewed by a human instead.
    B6: prohibitions by count, body parts and allergies as sets of canonical values, the route of
    each paired medicine when both sides state one, and pregnancy exactly.
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

    pares, sin_par, restantes = emparejar(original.medicamentos, retraducido.medicamentos)
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
        # A missing route is not a change: «tome» often implies oral and one side may leave it null.
        # Two different stated routes are (oral vs piel, ojos vs oídos).
        if med.via is not None and otro.via is not None and med.via != otro.via:
            difs.append(Diferencia(campo=f"{nombre}.via", original=med.via, retraducido=otro.via))

    for sobrante in restantes:
        difs.append(Diferencia(campo="medicamento", original="(no estaba)", retraducido=sobrante.nombre))

    # B6. Prohibitions are compared by count: the wording of «no lo tome con té» varies, but a
    # prohibition that vanishes (the negation was dropped) or appears is always a change.
    if len(original.prohibiciones) != len(retraducido.prohibiciones):
        difs.append(Diferencia(campo="prohibiciones (cantidad)",
                               original=str(len(original.prohibiciones)),
                               retraducido=str(len(retraducido.prohibiciones))))
    for campo, conjunto in (("partes_cuerpo", conjunto_partes), ("alergias", conjunto_alergias)):
        a, b = conjunto(original), conjunto(retraducido)
        if a != b:
            difs.append(Diferencia(campo=campo, original=", ".join(sorted(a)) or "(ninguna)",
                                   retraducido=", ".join(sorted(b)) or "(ninguna)"))
    if original.embarazo != retraducido.embarazo:
        difs.append(Diferencia(campo="embarazo", original=str(original.embarazo), retraducido=str(retraducido.embarazo)))

    return difs
