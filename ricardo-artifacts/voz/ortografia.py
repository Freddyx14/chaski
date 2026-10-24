# -*- coding: utf-8 -*-
"""Normaliza la escritura del quechua, para que el WER mida reconocer y no deletrear.

El problema que resuelve, medido el 24-oct. Cuatro personas leyeron la misma
indicacion castellana y escribieron cuatro cosas distintas:

    p16  pusaq horapi juk pastillata upyay
    p17  Sapa pusaq horamanta huk pastillata upyana
    p18  Huk pastillata upyay, sapa pusaq horaspi
    p19  Sapa pusaq ura pasaqtin, huk pastillata upyay

Hay tres clases de diferencia ahi, y solo una es ruido:

  1. ORTOGRAFIA   `juk` y `huk` son la misma palabra escrita distinto. El quechua
                  no tiene norma asentada y cada quien escribe como le enseñaron.
                  Esto no es un error del modelo y no deberia contar como tal.
  2. ORDEN        p18 pone el objeto primero. Es la misma indicacion.
  3. LEXICO       `horapi` / `horamanta` / `ura pasaqtin` son maneras distintas
                  de decir «cada ocho horas». Las cuatro estan bien.

Esto solo arregla la 1. Las otras dos son variacion real del habla, y cada
referencia es correcta PARA SU PROPIO AUDIO: cada persona transcribio lo que
ella misma dijo. Por eso la verdad de referencia es por hablante y esta bien
que lo sea; el problema aparece solo si se comparan personas entre si.

Las reglas van hacia la ortografia trivocalica del quechua sureño, que es la
oficial: a i u, w en vez de hu, h en vez de j, k/q en vez de c/qu.

Se aplica A LOS DOS LADOS, hipotesis y referencia. Si se aplicara a uno solo
seria hacer trampa con el numero.
"""
from __future__ import annotations

import re
import unicodedata

# El orden importa: `hua` tiene que volverse `wa` antes de que `u` toque nada.
REGLAS = [
    (r"hu([aeiou])", r"w\1"),      # huasi -> wasi, huawa -> wawa
    (r"\bj", "h"),                  # juk -> huk, jamuy -> hamuy
    (r"([aeiou])j([aeiou])", r"\1h\2"),
    (r"qu([ei])", r"k\1"),          # quechua: qu ante e/i suena k
    (r"c([aou])", r"k\1"),          # cay -> kay
    (r"\bc\b", "k"),
    (r"ch", "ĉ"),                   # se protege ch antes de tocar la h suelta
    (r"ĉ", "ch"),
    (r"e", "i"),                    # trivocalico: el quechua sureño tiene a i u
    (r"o", "u"),
    (r"y\b", "i"),                  # kanky -> kanki
    (r"(.)\1+", r"\1"),             # letras repetidas
]


def normalizar(texto: str) -> str:
    """Escritura comparable. No cambia que palabra se dijo, solo como se escribe."""
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")   # quita tildes
    t = re.sub(r"[^\w' ]", " ", t)
    for patron, reemplazo in REGLAS:
        t = re.sub(patron, reemplazo, t)
    return re.sub(r"\s+", " ", t).strip()


def distancia(a: list, b: list) -> int:
    previa = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        actual = [i]
        for j, y in enumerate(b, 1):
            actual.append(min(previa[j] + 1, actual[j - 1] + 1,
                              previa[j - 1] + (x != y)))
        previa = actual
    return previa[-1]


def tasa(referencias: list, hipotesis: list, por_caracter: bool = False,
         ortografia: bool = False) -> float:
    erroneos = total = 0
    for r, h in zip(referencias, hipotesis):
        if ortografia:
            r, h = normalizar(r), normalizar(h)
        else:
            r, h = r.lower().strip(), h.lower().strip()
        a = list(r) if por_caracter else r.split()
        b = list(h) if por_caracter else h.split()
        erroneos += distancia(a, b)
        total += len(a)
    return erroneos / total if total else 0.0
