"""Critical facts of a health instruction, and the deterministic comparison between two of them.

The comparison is plain code on purpose: the model extracts, code decides. If a dose, a frequency,
a duration or a date changed between the original and the back-translation, the message is blocked.

B6 (plan/arquitectura-interprete.md §2b) adds the facts that used to slip through: prohibitions
(«no lo tome con té» vs «tómelo con té»), body parts, allergies, the route of each medicine and
pregnancy. The vehicle of each medicine (what it is taken with: agua, leche, té...) was added after a
live audit on 2026-10-24 approved «Unuwan upyaykuy, manan téwanchu» whose back-translation was «Bebe con
uno, no con él»: the water was lost and nothing compared it. They are compared as counts or as
code-normalised canonical values, never as free wording, so a legitimate paraphrase does not block.

Three false blocks of the final eval (2026-10-24 15:49) are fixed here, in the extraction AND in code:
  - strength is not quantity: «pastilla de 500 mg» is cantidad 1 (or unsaid) + concentración 500 mg;
  - fasting is a timing, not a prohibition: «venga en ayunas» / «sin comer» → ayunas, never prohibiciones;
  - a fraction is a quantity, not a name: «kuska tableta» / «media tableta» → cantidad 0.5, nombre ''.
"""
from __future__ import annotations

import unicodedata
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Via = Literal["oral", "piel", "ojos", "oidos", "inyectable", "otra"]


class Medicamento(BaseModel):
    nombre: str = Field(description=(
        "Nombre del medicamento en minúsculas, sin marca si hay genérico. Ej: 'sulfato ferroso'. Una fracción "
        "(media, medio, mitad, kuska, chawpi, un cuarto, tercio) NUNCA es un nombre: es la cantidad. «Media tableta» "
        "o «kuska tableta» → nombre ''"))
    cantidad: float | None = Field(description=(
        "Cuántas unidades se toman en cada toma (pastillas, cucharadas, gotas, ml). Ej: 'una pastilla' → 1, 'dos "
        "cucharadas' → 2, 'media tableta' / 'kuska tableta' / 'chawpi' → 0.5, 'un cuarto' / 'tawa partemanta huk' → "
        "0.25. NO es la concentración: en «pastilla de 500 mg» los 500 mg van en concentracion, no aquí. null si no "
        "se dice cuántas"))
    unidad: str | None = Field(description=(
        "Unidad de la toma en singular y minúsculas: 'pastilla', 'cucharada', 'ml', 'gota'. Nunca 'mg' ni 'g': esas "
        "son de la concentración. null si no se dice"))
    concentracion: float | None = Field(default=None, description=(
        "La concentración o potencia del medicamento, el número impreso en la caja: «pastilla de 500 mg» → 500, "
        "«amoxicilina de 1 gramo» → 1. Es distinta de cantidad (cuántas pastillas por toma). null si no se dice"))
    concentracion_unidad: str | None = Field(default=None, description=(
        "Unidad de la concentración tal como se dice, en minúsculas: 'mg', 'g', 'mcg'. «quinientos miligramos» → "
        "'mg'; «un gramo» → 'g'. null si no hay concentración"))
    cada_horas: float | None = Field(description="Cada cuántas horas se toma. 'una vez al día' → 24, 'tres veces al día' → 8. null si no se dice")
    dias: int | None = Field(description="Durante cuántos días. 'un mes' → 30, 'una semana' → 7. null si no se dice o si es indefinido")
    momento: str | None = Field(description=(
        "Momento de la toma en pocas palabras: 'después del almuerzo', 'en ayunas'. «en ayunas», «sin comer», «sin "
        "desayunar» y «con el estómago vacío» son el mismo momento: escribe 'en ayunas'. null si no se dice"))
    via: Via | None = Field(default=None, description=(
        "Por dónde entra el medicamento: 'oral' (tomar, tragar, beber, por la boca, jarabe), 'piel' (untar, "
        "frotar, crema, pomada), 'ojos' (gotas en los ojos), 'oidos' (gotas en el oído), 'inyectable' "
        "(inyección, ampolla, vacuna), 'otra' (vía distinta a las anteriores). null si el texto no lo dice "
        "ni lo indica el verbo"))
    vehiculo: str | None = Field(default=None, description=(
        "Con qué se toma o se mezcla el medicamento, SOLO si el texto lo indica en positivo, en una palabra y "
        "en minúsculas, usando una de estas: 'agua', 'leche', 'jugo', 'té', 'comida', 'solo' (sin nada). "
        "«tómela con agua» → 'agua'; «con agüita» → 'agua'; «mézclelo en la leche» → 'leche'; «con un mate» → "
        "'té'; «con la comida» → 'comida'. Si el texto dice otra cosa ('con uno', 'con él'), copia esa palabra "
        "tal cual, sin corregirla. Lo que se prohíbe («no con té») NO va aquí, va en prohibiciones. null si el "
        "texto no dice con qué se toma"))

    @model_validator(mode="after")
    def _normalizar(self):
        """Code-side guards, so an extraction slip cannot become a false block (eval 2026-10-24 15:49)."""
        # A fraction word is a quantity, never a name: «kuska» / «media tableta» → cantidad 0.5.
        restantes, fraccion = [], None
        for w in _norm(self.nombre).split():
            if w in _FRACCIONES:
                fraccion = _FRACCIONES[w]
            elif w not in _RELLENO_FRACCION:
                restantes.append(w)
        if fraccion is not None:
            resto = " ".join(restantes)
            if not _generico(resto):
                self.nombre = resto
            else:
                self.nombre = ""
                if self.unidad is None and resto:
                    self.unidad = resto
            if self.cantidad is None or _mismo_numero(self.cantidad, 1):
                self.cantidad = fraccion
        # A strength unit in the dose (cantidad 500, unidad 'mg') is the strength, not the quantity.
        if self.concentracion is None and self.cantidad is not None and _norm(self.unidad) in _MASA_A_MG:
            self.concentracion, self.concentracion_unidad = self.cantidad, self.unidad
            self.cantidad, self.unidad = None, None
        return self


class Hechos(BaseModel):
    medicamentos: list[Medicamento] = Field(description=(
        "Cada medicamento indicado. Una instrucción de tomar algo sin nombrarlo («tómela con agua») cuenta como "
        "un medicamento con nombre vacío. Lista vacía si no hay"))
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
    ayunas: bool | None = Field(default=None, description=(
        "true si el texto pide venir o tomar algo en ayunas: «venga en ayunas», «sin comer», «sin desayunar», «con "
        "el estómago vacío», «mana mikuspa». Ayunar es un MOMENTO, nunca una prohibición: no lo pongas en "
        "prohibiciones. false si el texto pide lo contrario («venga después de comer», «tómelo con la comida»). "
        "null si no se dice"))

    @model_validator(mode="after")
    def _ayunas_no_es_prohibicion(self):
        """«no coma nada antes de venir» is the fasting timing, not a prohibition (eval 2026-10-24 15:49).

        Real prohibitions about food («no coma grasa») name what is forbidden, so they are kept.
        """
        quedan = [p for p in self.prohibiciones if not es_prohibicion_de_ayuno(p)]
        if len(quedan) != len(self.prohibiciones):
            self.prohibiciones = quedan
            if self.ayunas is None:
                self.ayunas = True
        return self


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


# Fractions said as a word (Spanish and Chanka: kuska / chawpi = half). Chanka list to be confirmed by the nurse.
_FRACCIONES = {"media": 0.5, "medio": 0.5, "mitad": 0.5, "kuska": 0.5, "kuskan": 0.5, "chawpi": 0.5,
               "chaupi": 0.5, "chawpin": 0.5, "cuarto": 0.25, "tercio": 1 / 3}
_RELLENO_FRACCION = {"un", "una", "la", "el", "de", "nisqa", "nisqata"}
# Strength units → factor to milligrams.
_MASA_A_MG = {"mg": 1.0, "miligramo": 1.0, "miligramos": 1.0,
              "g": 1000.0, "gr": 1000.0, "gramo": 1000.0, "gramos": 1000.0,
              "mcg": 0.001, "ug": 0.001, "microgramo": 0.001, "microgramos": 0.001}


def concentracion_mg(m: "Medicamento") -> float | None:
    """The strength in mg: 1 g → 1000, 500 mg → 500. None if no strength or the unit is not a mass.

    A strength with no unit is read as mg, the unit every tablet strength in the posta is said in.
    """
    if m.concentracion is None:
        return None
    factor = _MASA_A_MG.get(_norm(m.concentracion_unidad) or "mg")
    return None if factor is None else m.concentracion * factor


def _concentracion_canonica(m: "Medicamento") -> str:
    """Comparable strength: '500 mg' for masses, else the raw value and unit (e.g. '5 %'). '' if none."""
    if m.concentracion is None:
        return ""
    mg = concentracion_mg(m)
    if mg is not None:
        return f"{round(mg, 6):g} mg"
    return f"{m.concentracion:g} {_norm(m.concentracion_unidad)}"


# Fasting. A prohibition made only of eating words and filler («comer antes de venir», «desayunar»)
# is the fasting timing; one that names something else («comer grasa», «tomar con té») is a real one.
_COMER = {"comer", "desayunar", "ingerir", "probar", "alimentarse", "ayunar", "ayunas", "ayuno", "desayuno",
          "comida", "alimento", "alimentos", "bocado"}
_RELLENO_AYUNO = {"nada", "ningun", "ninguna", "algo", "antes", "de", "del", "la", "el", "su", "venir", "llegar",
                  "cita", "analisis", "examen", "manana", "tomar", "estar", "hasta", "que", "sin", "en", "un", "ni"}


def es_prohibicion_de_ayuno(prohibicion: str | None) -> bool:
    ws = _norm(prohibicion).split()
    return bool(ws) and any(w in _COMER for w in ws) and all(w in _COMER or w in _RELLENO_AYUNO for w in ws)


_AYUNAS_PALABRAS = {"ayunas", "ayuna", "ayuno", "ayunar", "ayunando"}
_AYUNAS_FRASES = ("sin comer", "sin desayunar", "sin probar", "sin alimento", "estomago vacio", "sin haber comido",
                  "mana mikuspa")
_COMIDA_PALABRAS = {"comer", "comida", "comidas", "comiendo", "desayuno", "desayunar", "almuerzo", "almorzar",
                    "cena", "cenar", "alimento", "alimentos", "comido"}


def momento_comida(momento: str | None) -> str | None:
    """'en ayunas' / 'sin comer' → 'ayunas'; 'después de comer' / 'con el almuerzo' → 'comida'; else None."""
    n = _norm(momento)
    if not n:
        return None
    if _AYUNAS_PALABRAS & set(n.split()) or any(f in n for f in _AYUNAS_FRASES):
        return "ayunas"
    if _COMIDA_PALABRAS & set(n.split()):
        return "comida"
    return None


def estado_ayunas(h: "Hechos") -> bool:
    """Does this side say «en ayunas» anywhere: the flag, a fasting prohibition, or a medicine's momento?"""
    return (h.ayunas is True or any(es_prohibicion_de_ayuno(p) for p in h.prohibiciones)
            or any(momento_comida(m.momento) == "ayunas" for m in h.medicamentos))


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


# Vehicle synonyms → one canonical value (accent-free, lowercase). Spanish words plus the Chanka ones
# a translation may leave untranslated (unu / yaku = agua, lichi = leche). Chanka list to be confirmed
# by the nurse. «uno» is deliberately NOT agua: it is the misreading of «unu» measured on 2026-10-24.
_VEHICULOS = {
    "agua": "agua", "aguita": "agua", "agua hervida": "agua", "agua tibia": "agua", "agua fria": "agua",
    "unu": "agua", "yaku": "agua", "yacu": "agua",
    "leche": "leche", "lechita": "leche", "lechi": "leche", "lichi": "leche",
    "jugo": "jugo", "juguito": "jugo", "zumo": "jugo",
    "te": "te", "tecito": "te", "mate": "te", "matecito": "te", "infusion": "te", "agua de hierbas": "te",
    "comida": "comida", "comidas": "comida", "alimento": "comida", "alimentos": "comida",
    "solo": "solo", "sola": "solo", "sin nada": "solo", "nada": "solo",
}
_CANONICOS_PROHIBIBLES = set(_VEHICULOS.values()) - {"solo"}
# Words between the preposition and the vehicle: «con un poco de leche», «en su jugo».
_RELLENO_VEHICULO = {"el", "la", "los", "las", "un", "una", "su", "sus", "poco", "de", "del", "bastante", "mucho",
                     "mucha", "algo"}


def vehiculo_canonico(vehiculo: str | None) -> str | None:
    """'con agüita' → 'agua', 'un mate' → 'te', 'uno' → 'uno' (unknown kept, so it differs), '' → None."""
    n = _sin_articulo(vehiculo)
    while n.startswith(("con ", "en ")):
        n = _sin_articulo(n.split(" ", 1)[1])
    if not n:
        return None
    if n in _VEHICULOS:
        return _VEHICULOS[n]
    primera = n.split()[0]
    return _VEHICULOS.get(primera, _VEHICULOS.get(_singular(primera), n))


def vehiculos_prohibidos(h: Hechos) -> set[str]:
    """Canonical vehicles named inside the prohibitions after «con» / «en»: «tomar con té» → {'te'}.

    Requiring the preposition keeps the pronoun «te» («no te olvides») from reading as té.
    """
    salida = set()
    for p in h.prohibiciones:
        ws = _norm(p).split()
        for i, w in enumerate(ws):
            if w not in ("con", "en"):
                continue
            resto = [x for x in ws[i + 1:] if x not in _RELLENO_VEHICULO]
            if resto and (v := vehiculo_canonico(" ".join(resto[:2]))) in _CANONICOS_PROHIBIBLES:
                salida.add(v)
    return salida


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
    each paired medicine when both sides state one, and pregnancy exactly. The vehicle of each paired
    medicine is compared canonically and also when it vanishes on one side; the vehicles named inside
    the prohibitions are compared as a set. The strength of each paired medicine is compared exactly in
    mg, and fasting («en ayunas» vs «después de comer») as a yes/no: the only part of 'momento' compared.
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
            # «la pastilla» and «una pastilla» are the same dose: an unsaid quantity equals 1, nothing else.
            if campo == "cantidad" and {a, b} <= {None, 1} and _unidad(med.unidad) == _unidad(otro.unidad):
                continue
            if not _mismo_numero(a, b):
                difs.append(Diferencia(campo=f"{nombre}.{campo}", original=str(a), retraducido=str(b)))
        # Strength exactly, after g → mg: 500 mg vs 250 mg blocks, 1 g vs 1000 mg does not.
        ca, cb = _concentracion_canonica(med), _concentracion_canonica(otro)
        if ca != cb:
            difs.append(Diferencia(campo=f"{nombre}.concentracion", original=ca or "None", retraducido=cb or "None"))
        # «en ayunas» swapped for «después de comer» on the same medicine, when both sides state a timing.
        # A timing lost or moved elsewhere is caught by the side-level fasting check below.
        ma, mb = momento_comida(med.momento), momento_comida(otro.momento)
        if ma and mb and ma != mb:
            difs.append(Diferencia(campo=f"{nombre}.momento", original=str(med.momento), retraducido=str(otro.momento)))
        if _unidad(med.unidad) != _unidad(otro.unidad):
            difs.append(Diferencia(campo=f"{nombre}.unidad", original=str(med.unidad), retraducido=str(otro.unidad)))
        # A missing route is not a change: «tome» often implies oral and one side may leave it null.
        # Two different stated routes are (oral vs piel, ojos vs oídos).
        if med.via is not None and otro.via is not None and med.via != otro.via:
            difs.append(Diferencia(campo=f"{nombre}.via", original=med.via, retraducido=otro.via))
        # Unlike the route, a vehicle that disappears IS a change: «con agua» → «con uno» / nothing.
        va, vb = vehiculo_canonico(med.vehiculo), vehiculo_canonico(otro.vehiculo)
        if va != vb:
            difs.append(Diferencia(campo=f"{nombre}.vehiculo", original=str(va), retraducido=str(vb)))

    for sobrante in restantes:
        difs.append(Diferencia(campo="medicamento", original="(no estaba)", retraducido=sobrante.nombre))

    # B6. Prohibitions are compared by count: the wording of «no lo tome con té» varies, but a
    # prohibition that vanishes (the negation was dropped) or appears is always a change.
    if len(original.prohibiciones) != len(retraducido.prohibiciones):
        difs.append(Diferencia(campo="prohibiciones (cantidad)",
                               original=str(len(original.prohibiciones)),
                               retraducido=str(len(retraducido.prohibiciones))))
    # «no con té» → «no con él»: same count, but the forbidden vehicle was lost. Only checked when
    # the counts match; a different count already blocks.
    pa, pb = vehiculos_prohibidos(original), vehiculos_prohibidos(retraducido)
    mismo_conteo = len(original.prohibiciones) == len(retraducido.prohibiciones)
    if mismo_conteo and pa != pb:
        difs.append(Diferencia(campo="prohibiciones (vehículo)", original=", ".join(sorted(pa)) or "(ninguno)",
                               retraducido=", ".join(sorted(pb)) or "(ninguno)"))
    for campo, conjunto in (("partes_cuerpo", conjunto_partes), ("alergias", conjunto_alergias)):
        a, b = conjunto(original), conjunto(retraducido)
        if a != b:
            difs.append(Diferencia(campo=campo, original=", ".join(sorted(a)) or "(ninguna)",
                                   retraducido=", ".join(sorted(b)) or "(ninguna)"))
    # Fasting is compared as a yes/no for the whole instruction, wherever the extraction put it.
    if estado_ayunas(original) != estado_ayunas(retraducido):
        difs.append(Diferencia(campo="ayunas", original=str(estado_ayunas(original)),
                               retraducido=str(estado_ayunas(retraducido))))
    if original.embarazo != retraducido.embarazo:
        difs.append(Diferencia(campo="embarazo", original=str(original.embarazo), retraducido=str(retraducido.embarazo)))

    return difs
