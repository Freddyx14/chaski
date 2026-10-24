"""Pure-code guards that run before Chaski speaks (plan/arquitectura-interprete.md §2b).

Each guard returns a small `Veredicto`: ok, or a block with the reason. None of them calls a model:
the model extracts, code decides. Every guard is wrapped in `fail_closed`, so an exception or a
malformed result is a block («no pude verificar»), never a pass.

  B1  oido_confiable           low-confidence ASR word on a critical token (number, medicine, body part)
  B2  pulido_conserva_hechos   the polished text changed a critical fact of the transcript
  B3  pulido_conserva_hechos   the polished text added a critical fact that was not said
  B4  terminos_fijos           numbers, medicine names, units and negation survive into the Quechua
"""
from __future__ import annotations

import functools
import re
import unicodedata
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

from chaski.hechos import Hechos, comparar, emparejar

NO_PUDE_VERIFICAR = "no pude verificar"


class Veredicto(BaseModel):
    ok: bool
    capa: str
    motivo: str = ""
    detalle: list[str] = Field(default_factory=list)


def pasa(capa: str) -> Veredicto:
    return Veredicto(ok=True, capa=capa)


def bloqueo(capa: str, motivo: str, detalle: list[str] | None = None) -> Veredicto:
    return Veredicto(ok=False, capa=capa, motivo=motivo, detalle=detalle or [])


def fail_closed(fn):
    """Any exception or any result that is not a Veredicto becomes a block. Never a pass."""
    capa = getattr(fn, "__name__", "guarda")

    @functools.wraps(fn)
    def envuelta(*args, **kwargs):
        try:
            salida = fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001 — failing closed is the whole point
            return bloqueo(capa, NO_PUDE_VERIFICAR, [f"{type(e).__name__}: {e}"])
        if not isinstance(salida, Veredicto):
            return bloqueo(capa, NO_PUDE_VERIFICAR, [f"salida mal formada: {type(salida).__name__}"])
        return salida

    return envuelta


# ---------------------------------------------------------------------------------------------
# Text helpers

def norm(texto: str | None) -> str:
    """Lowercase, accents and apostrophes removed (p'unchaw → punchaw, pisq'a → pisqa)."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", texto.replace("ñ", "\x00").replace("Ñ", "\x00"))
    t = t.encode("ascii", "ignore").decode().replace("\x00", "ñ").lower()
    return re.sub(r"[’'`´]", "", t)


def palabras(texto: str | None) -> list[str]:
    """Words, with commas and other punctuation kept as '|' separators so «iskay, kimsa» are two numbers."""
    t = re.sub(r"[,;.:!?¡¿()\"\-–—/]", " | ", norm(texto))
    return t.split()


# ---------------------------------------------------------------------------------------------
# Number tables

# Standard Quechua numerals (Ayacucho-Chanka) plus the spellings families actually wrote in the
# form (data/formulario/manifest.jsonl): pusac/pusaj/pusak, kinsa/quimsa, esqon/isjon, chunca...
# Source: standard Quechua numerals; to be confirmed by the nurse.
NUMEROS_QUY: dict[str, int] = {}
for _valor, _formas in {
    1: ["huk", "huq", "juk", "uk", "uq", "hok"],
    2: ["iskay", "isqay", "iskai", "ishkay", "iscay", "ishcay", "iskaj"],
    3: ["kimsa", "kinsa", "quimsa", "quinsa", "kimza", "kinza", "quinza", "quimza"],
    4: ["tawa", "tahua", "tagua"],
    5: ["pichqa", "pisqa", "pichka", "pischqa", "pichcca", "piskcca", "pichca", "pishqa", "pisca", "pischa", "pichqha"],
    6: ["suqta", "soqta", "sukta", "socta", "soqhta", "suqhta", "sojta", "sujta"],
    7: ["qanchis", "qanchik", "kanchis", "canchis", "qannchis", "qanchus", "qanchiz", "qanchiq"],
    8: ["pusaq", "pusac", "pusaj", "pusak", "pusacc", "pusaqq", "pusag"],
    9: ["isqun", "isqon", "esqon", "iskun", "isjon", "jisqun", "hisqun", "isccon", "escon", "isqun", "esqun"],
    10: ["chunka", "chunca", "chunga", "chonqa", "chunqa"],
    100: ["pachak", "pachaq", "pachac", "pachaj"],
    1000: ["waranqa", "waranka", "huaranca", "waranqa"],
}.items():
    for _f in _formas:
        NUMEROS_QUY[_f] = _valor
# Longest first, so «pusacc» wins over «pusac» and «kimsa» is not read as «kim».
_RAICES_QUY = sorted(NUMEROS_QUY, key=len, reverse=True)
_MULTIPLICADORES = {10, 100, 1000}

NUMEROS_ES = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
    "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
    "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiuno": 21, "veintidos": 22,
    "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "treinta": 30, "cuarenta": 40, "cincuenta": 50,
    "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90, "cien": 100, "ciento": 100, "doscientos": 200,
    "trescientos": 300, "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600, "setecientos": 700,
    "ochocientos": 800, "novecientos": 900, "mil": 1000,
}
# Time words that carry an implicit number: «una semana» is said «qanchis punchaw» (seven days).
_IMPLICITOS_ES = {"semana": 7, "semanas": 7, "quincena": 15, "mes": 30, "meses": 30, "ano": 365}


def raiz_numero(palabra: str) -> tuple[str, int] | None:
    """The Quechua number root a word starts with: 'pusaqniyuq' → ('pusaq', 8)."""
    if palabra.isdigit():
        return palabra, int(palabra)
    for raiz in _RAICES_QUY:
        if palabra.startswith(raiz):
            # «uk»/«uq» are too short to trust as a prefix of a longer word (ukhu = inside).
            if len(raiz) <= 2 and palabra != raiz and not palabra[len(raiz):].startswith(("ta", "lla", "pi", "manta")):
                continue
            return raiz, NUMEROS_QUY[raiz]
    return None


def numeros_quechua(texto: str) -> list[int]:
    """Numbers said in a Quechua text, composing «kimsa chunka isqunniyuq» → 39, «pichqa pachak» → 500.

    Fused forms are split: «kinsachunka» → 3 × 10. A comma or a non-number word ends a number.
    """
    salida: list[int] = []
    total, actual, abierto = 0, 0, False

    def cerrar():
        nonlocal total, actual, abierto
        if abierto:
            salida.append(total + actual)
        total, actual, abierto = 0, 0, False

    for p in palabras(texto):
        # A word is one number root plus a suffix, except a fused unit + multiplier
        # («kinsachunka» = 3 × 10). «huktawan» (again) is huk + -tawan, not 1 and 4.
        piezas = []
        r = raiz_numero(p)
        if r is not None:
            piezas.append(r[1])
            resto = p[len(r[0]):]
            while resto:
                r = raiz_numero(resto)
                if r is None or r[1] not in _MULTIPLICADORES:
                    break
                piezas.append(r[1])
                resto = resto[len(r[0]):]
        if not piezas:
            cerrar()
            continue
        for v in piezas:
            if v in _MULTIPLICADORES:
                base = actual if actual else 1
                if v == 1000:
                    total, actual = (total + base) * 1000, 0
                else:
                    actual = base * v
                abierto = True
            elif abierto and actual and actual % 10 == 0 and actual >= 10:
                actual += v  # chunka iskayniyuq → 12
            else:
                cerrar()
                actual, abierto = v, True
    cerrar()
    return salida


def numeros_castellano(texto: str) -> list[int]:
    """Numbers said in Spanish, digits or words: «treinta y nueve» → 39, «quinientos» → 500."""
    salida: list[int] = []
    total, actual, abierto = 0, 0, False

    def cerrar():
        nonlocal total, actual, abierto
        if abierto:
            salida.append(total + actual)
        total, actual, abierto = 0, 0, False

    ps = palabras(texto)
    for i, p in enumerate(ps):
        if p.isdigit():
            cerrar()
            salida.append(int(p))
            continue
        if p == "y" and abierto and i + 1 < len(ps) and ps[i + 1] in NUMEROS_ES and NUMEROS_ES[ps[i + 1]] < 10:
            continue
        v = NUMEROS_ES.get(p)
        if v is None:
            cerrar()
            continue
        if v == 1000:
            total, actual = (total + (actual or 1)) * 1000, 0
        elif abierto and actual >= 20 and actual % 10 == 0 and v < 10:
            actual += v
        elif abierto and actual >= 100 and actual % 100 == 0 and v < 100:
            actual += v
        else:
            cerrar()
            actual = v
        abierto = True
    cerrar()
    return salida


# ---------------------------------------------------------------------------------------------
# Medicines, units, negation, body parts

# Medicines that appear in the form and the clinical phrase list. Used to spot a medicine the
# Quechua names that the Spanish did not (a swap), and to flag them as critical ASR tokens.
MEDICAMENTOS_CONOCIDOS = [
    "paracetamol", "ibuprofeno", "amoxicilina", "omeprazol", "sulfato ferroso", "acido folico", "albendazol",
    "metformina", "losartan", "salbutamol", "suero", "vitamina c", "penicilina", "naproxeno",
    "diclofenaco", "clorfenamina", "azitromicina", "cotrimoxazol", "metronidazol", "dexametasona",
]
_UMBRAL_NOMBRE = 0.8

_UNIDADES_ES = {
    "pastilla": "pastilla", "pastillas": "pastilla", "tableta": "pastilla", "tabletas": "pastilla",
    "comprimido": "pastilla", "comprimidos": "pastilla", "capsula": "pastilla", "capsulas": "pastilla",
    "cucharada": "cuchara", "cucharadas": "cuchara", "cucharadita": "cuchara", "cucharaditas": "cuchara",
    "cuchara": "cuchara", "cucharita": "cuchara",
    "gota": "gota", "gotas": "gota", "ml": "ml", "mililitro": "ml", "mililitros": "ml",
}
# Quechua unit stems: loanwords and native words (sutu = drop, wislla = ladle/spoon).
_UNIDADES_QUY = [
    ("pastilla", "pastilla"), ("pasitilla", "pastilla"), ("tableta", "pastilla"), ("capsula", "pastilla"),
    ("cuchar", "cuchara"), ("kuchar", "cuchara"), ("wislla", "cuchara"), ("uchari", "cuchara"),
    ("gota", "gota"), ("sutu", "gota"), ("sotu", "gota"), ("sutha", "gota"),
    ("mililitr", "ml"),
]

_NEGACION_ES = re.compile(r"\b(no|nunca|jamas|ni|tampoco)\b")
# Fixed expressions with «no» that carry no negated instruction.
_NO_ES_NEGACION = ("no hay de que", "no tiene por que")
_NEGACION_QUY = re.compile(r"^(ama|mana)(n|m|y|puni|raq|taq|lla|llam|llan|tak|ña|ñam)?$")

_PARTES_ES = {"cabeza", "barriga", "estomago", "panza", "vientre", "abdomen", "ojo", "ojos", "oido", "oidos",
              "oreja", "orejas", "garganta", "pecho", "espalda", "brazo", "brazos", "pierna", "piernas", "pie",
              "pies", "mano", "manos", "diente", "dientes", "muela", "muelas", "piel", "corazon", "rodilla",
              "rodillas", "cuello", "rinon", "rinones", "pulmon", "pulmones", "utero", "vagina", "boca", "nariz"}
# Quechua body-part stems (uma head, wiksa belly, ñawi eye, rinri ear, kunka throat, qasqu chest...).
_PARTES_QUY = ("uma", "wiksa", "wiqsa", "wixa", "wisa", "ñawi", "nawi", "rinri", "ninri", "kunka", "qasqu",
               "sunqu", "sonqo", "wasa", "maki", "chaki", "kiru", "siki", "chanka", "muqu", "ñuñu", "sinqa",
               "simi", "qara", "rurun", "wawa tiyana")


def tiene_negacion_quechua(texto: str) -> bool:
    return any(_NEGACION_QUY.match(p) or p.endswith(("chu", "cho")) for p in palabras(texto))


def tiene_negacion_castellano(texto: str) -> bool:
    t = " ".join(palabras(texto))
    for fija in _NO_ES_NEGACION:
        t = t.replace(fija, " ")
    return bool(_NEGACION_ES.search(t))


# Qualifiers dropped from a medicine name before matching: «suero oral» is said «sueruta upyachiy».
_CALIFICADORES = {"oral", "en", "de", "jarabe", "tabletas", "tableta", "gotas", "crema"}


def _compacto(texto: str) -> str:
    return re.sub(r"[^a-zñ]", "", norm(texto))


def _nombre_compacto(nombre: str) -> str:
    partes = [p for p in palabras(nombre) if p not in _CALIFICADORES] or palabras(nombre)
    return _compacto(" ".join(partes))


def nombre_presente(nombre: str, texto: str, umbral: float = _UMBRAL_NOMBRE) -> bool:
    """Is the medicine name in the text as a loanword, allowing a Quechua suffix and small spelling drift?

    «sulfato ferroso» is found in «Sulfatoferrosuta upyay»; «paracetamol» is NOT found in «Ibuprofenota».
    """
    objetivo = _nombre_compacto(nombre)
    if not objetivo:
        return True
    ps = [re.sub(r"[^a-zñ]", "", p) for p in palabras(texto)]
    ps = [p for p in ps if p]
    for i in range(len(ps)):
        tramo = "".join(ps[i:i + 4])
        for largo in range(max(1, len(objetivo) - 2), len(objetivo) + 3):
            if SequenceMatcher(None, objetivo, tramo[:largo]).ratio() >= umbral:
                return True
    return False


def medicamentos_en(texto: str) -> list[str]:
    return [m for m in MEDICAMENTOS_CONOCIDOS if nombre_presente(m, texto)]


def unidades_castellano(texto: str) -> set[str]:
    return {_UNIDADES_ES[p] for p in palabras(texto) if p in _UNIDADES_ES}


def unidades_quechua(texto: str) -> set[str]:
    return {clase for p in palabras(texto) for raiz, clase in _UNIDADES_QUY if p.startswith(raiz)}


def _es_generico(nombre: str) -> bool:
    return _compacto(nombre) in {"", "pastilla", "pastillas", "tableta", "tabletas", "medicamento", "medicina",
                                 "remedio", "jarabe", "gotas", "comprimido"}


# ---------------------------------------------------------------------------------------------
# B4

@fail_closed
def terminos_fijos(texto_es: str, texto_quy: str, hechos: Hechos | None = None) -> Veredicto:
    """B4. The fixed terms of the Spanish must survive into the Quechua.

    - Numbers: every Spanish number ≥ 2 must be said in the Quechua (number table above), and the
      Quechua must not say a number ≥ 2 that the Spanish (or its extracted facts) does not have.
      «un/una» is skipped: it is usually an article and Quechua often drops it.
    - Medicines: each medicine named in Spanish appears as a loanword; the Quechua names no other
      known medicine.
    - Units: if the Quechua names a unit (pastilla, kuchara, sutu...), it is one the Spanish said.
    - Negation: a negated instruction in Spanish needs ama / mana / -chu in the Quechua.
    """
    capa = "B4 términos fijos"
    problemas: list[str] = []

    es_nums = numeros_castellano(texto_es)
    requeridos = {n for n in es_nums if n >= 2}
    permitidos = set(requeridos)
    for p in palabras(texto_es):
        if p in _IMPLICITOS_ES:
            permitidos.add(_IMPLICITOS_ES[p])
    rango = re.search(r"\bdel (\w+) al (\w+)\b", " ".join(palabras(texto_es)))
    if rango and rango.group(1) in NUMEROS_ES and rango.group(2) in NUMEROS_ES:
        permitidos.update(range(NUMEROS_ES[rango.group(1)], NUMEROS_ES[rango.group(2)] + 1))
    if hechos is not None:
        for m in hechos.medicamentos:
            permitidos.update(int(x) for x in (m.cantidad, m.cada_horas, m.dias) if x is not None and float(x).is_integer())
        if hechos.proxima_cita_en_dias is not None:
            permitidos.add(hechos.proxima_cita_en_dias)
    quy_nums = set(numeros_quechua(texto_quy))
    for n in sorted(requeridos - quy_nums):
        problemas.append(f"número {n} no aparece en el quechua")
    for n in sorted(x for x in quy_nums if x >= 2 and x not in permitidos):
        problemas.append(f"el quechua dice {n}, que no está en el castellano")

    nombres_es = set(medicamentos_en(texto_es))
    if hechos is not None:
        nombres_es.update(m.nombre for m in hechos.medicamentos if not _es_generico(m.nombre))
    for nombre in sorted(nombres_es):
        if not nombre_presente(nombre, texto_quy):
            problemas.append(f"medicamento «{nombre}» no aparece tal cual en el quechua")
    compactos_es = {_nombre_compacto(n) for n in nombres_es}
    for otro in medicamentos_en(texto_quy):
        if _nombre_compacto(otro) not in compactos_es and not nombre_presente(otro, texto_es):
            problemas.append(f"el quechua nombra «{otro}», que no está en el castellano")

    u_es, u_quy = unidades_castellano(texto_es), unidades_quechua(texto_quy)
    if u_es:
        for u in sorted(u_quy - u_es):
            problemas.append(f"unidad «{u}» en el quechua, el castellano dice {', '.join(sorted(u_es))}")

    negado = tiene_negacion_castellano(texto_es) or bool(hechos is not None and hechos.prohibiciones)
    if negado and not tiene_negacion_quechua(texto_quy):
        problemas.append("el castellano tiene una negación y el quechua no (ama / mana / -chu)")

    if problemas:
        return bloqueo(capa, problemas[0], problemas)
    return pasa(capa)


# ---------------------------------------------------------------------------------------------
# B2 / B3

@fail_closed
def pulido_conserva_hechos(hechos_transcripcion: Hechos, hechos_pulido: Hechos) -> Veredicto:
    """B2 + B3. The polished text keeps every critical fact of the transcript and adds none.

    Dropping filler («eh», «este», repetitions) changes no fact, so it passes. Any difference in the
    facts blocks, and the reason says whether the polish ADDED something (B3, «el intérprete
    inventó») or CHANGED it (B2). On a block the caller discards the polish and uses the literal
    transcript (§2b). Also catches an invented 'momento' («después de comer»), which `comparar`
    leaves out because it is free text.
    """
    agregados: list[str] = []
    cambiados: list[str] = []
    for d in comparar(hechos_transcripcion, hechos_pulido):
        texto = f"{d.campo}: {d.original} → {d.retraducido}"
        es_conteo = d.campo.endswith("(cantidad)") or "cantidad de señales" in d.campo
        nuevo = (d.original in ("(no estaba)", "None", "(ninguna)")
                 or (es_conteo and _num(d.retraducido) > _num(d.original)))
        (agregados if nuevo else cambiados).append(texto)
    pares, _, _ = emparejar(hechos_transcripcion.medicamentos, hechos_pulido.medicamentos)
    for a, b in pares:
        if not a.momento and b.momento:
            agregados.append(f"{b.nombre or 'medicamento'}.momento: (no estaba) → {b.momento}")
    if agregados:
        return bloqueo("B3 nada nuevo", f"el pulido agregó un dato: {agregados[0]}", agregados + cambiados)
    if cambiados:
        return bloqueo("B2 el pulido no cambia hechos", f"el pulido cambió un dato: {cambiados[0]}", cambiados)
    return pasa("B2/B3 pulido")


def _num(texto: str) -> float:
    try:
        return float(texto)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------------------------
# B1

def es_critica(palabra: str) -> bool:
    """A token whose mishearing changes a fact: a number, a medicine, a body part (Spanish or Quechua)."""
    p = re.sub(r"[^a-zñ0-9]", "", norm(palabra))
    if not p:
        return False
    if p.isdigit() or p in NUMEROS_ES or raiz_numero(p) is not None:
        return True
    if p in _PARTES_ES or p.startswith(_PARTES_QUY):
        return True
    return len(p) >= 5 and any(SequenceMatcher(None, _compacto(m), p[:len(_compacto(m))]).ratio() >= _UMBRAL_NOMBRE
                               for m in MEDICAMENTOS_CONOCIDOS)


@fail_closed
def oido_confiable(palabras_asr: list[dict], umbral: float = 0.6) -> Veredicto:
    """B1. Block if a low-confidence ASR word is a critical token. Never guess a number.

    `palabras_asr` is [{"texto": str, "confianza": float 0-1}, ...]. An empty list (silence) blocks:
    there is nothing to translate and Chaski asks again.
    """
    capa = "B1 lo que se oyó"
    if not palabras_asr:
        return bloqueo(capa, "no se oyó nada")
    dudosas = []
    for w in palabras_asr:
        texto, confianza = w["texto"], float(w["confianza"])
        if not 0.0 <= confianza <= 1.0:
            raise ValueError(f"confianza fuera de rango: {confianza}")
        if confianza < umbral and es_critica(texto):
            dudosas.append(f"«{texto}» ({confianza:.2f})")
    if dudosas:
        return bloqueo(capa, f"no se oyó bien un dato crítico: {dudosas[0]}", dudosas)
    return pasa(capa)
