# -*- coding: utf-8 -*-
"""Saca pares castellano/quechua del Manual de Semiología en Quechua del CMP.

El manual (Dr. Julio Lopera Quiroga, Colegio Médico del Perú, 2020, 80 páginas)
es un interrogatorio clínico completo con las dos lenguas alternadas línea por
línea: filiación, interrogatorio, y preguntas por aparato. Es el único material
de salud en quechua con esa estructura, y el autor autorizó publicarlo.

Dos avisos sobre lo que sale de aquí:

1. Está en quechua **Collao** (Cusco), no Chanka. Se nota en las glotalizadas y
   aspiradas: `qhari`, `hayk'a`, `k'allarin`. El Chanka no las tiene. La función
   `a_chanka()` hace la parte sistemática de la conversión; lo que queda lo
   revisa una hablante. Por eso cada par sale marcado `revisado: false`.

2. Es un borrador para revisión humana, no datos de entrenamiento todavía.

Uso:
  uv run --with pypdf python voz/importar_semiologia.py
  uv run --with pypdf python voz/importar_semiologia.py --pdf /tmp/semiologia.pdf
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

URL = "https://www.cmp.org.pe/wp-content/uploads/2020/07/ManualSemiologiaQuechua-2020.pdf"
SALIDA = Path("datos/frases/semiologia_cmp.jsonl")

# Palabras que delatan al castellano. No hace falta más: las dos lenguas no se
# parecen en nada, así que con una decena de funcionales alcanza para decidir
# cuál de las dos líneas de un par es cuál.
CASTELLANO = {
    "que", "qué", "de", "la", "el", "los", "las", "su", "le", "se", "en", "con",
    "por", "para", "tiene", "tienes", "está", "cómo", "cuándo", "cuánto", "cuántos",
    "dónde", "es", "son", "al", "del", "un", "una", "no", "sí", "y", "o", "usted",
    "dolor", "duele", "señor", "señora", "señorita", "joven", "hijo", "hijos",
    "desde", "ha", "venido", "buenas", "buenos", "días", "noches", "tardes",
    "años", "vives", "vienes", "eres", "llamas", "estás", "tu", "te", "me", "mi",
    "cuánta", "cuántas", "a", "ya", "más", "menos", "veces", "día", "días",
}

# Collao -> Chanka. El orden importa: primero los dígrafos aspirados, después las
# glotalizadas sueltas, porque `chh` tiene que resolverse antes que `ch`.
REGLAS = [
    ("chh", "ch"), ("khh", "kh"),
    ("kh", "k"), ("qh", "q"), ("ph", "p"), ("th", "t"),
    ("ch'", "ch"), ("k'", "k"), ("q'", "q"), ("p'", "p"), ("t'", "t"), ("s'", "s"),
]


def a_chanka(texto: str) -> str:
    """Quita glotalizadas y aspiradas, que el Chanka no tiene.

    Es la parte mecánica de la conversión. Lo que NO hace, a propósito: cambiar
    palabras que en Chanka se dicen distinto aunque se escriban parecido. Eso no
    se puede adivinar con reglas y lo tiene que ver una hablante.
    """
    salida = texto
    for de, a in REGLAS:
        # Tres formas: `qhari`, `QHARI` y `Qhari` al principio de frase. La
        # tercera se escapaba y dejaba «Qhariyki» sin convertir.
        salida = (salida.replace(de, a)
                        .replace(de.upper(), a.upper())
                        .replace(de.capitalize(), a.capitalize()))
    return salida


# Sufijos del quechua. Son los que cargan la gramática, así que aparecen en casi
# cualquier frase larga y sirven de evidencia a favor aunque la frase tenga
# préstamos del castellano («¿Pistachu, sinchitachu o fuertetachu?» lleva «o»).
QUECHUA = ("nki", "nqa", "chu", "yki", "sqa", "ska", "kuna", "nchik", "taq", "tak",
           "wan", "manta", "paq", "rayku", "shan", "chkan", "yman", "sunki", "sunqui",
           "ykin", "niy")


def _puntaje(linea: str) -> tuple[int, int]:
    """(cuánto se parece al castellano, cuánto al quechua)."""
    bajo = linea.lower()
    palabras = re.findall(r"[a-záéíóúñü']+", bajo)
    if not palabras:
        return 0, 0
    es = sum(1 for p in palabras if p in CASTELLANO)
    qu = sum(1 for p in palabras if any(p.endswith(m) or m in p for m in QUECHUA))
    # Las glotalizadas y aspiradas solo existen del lado quechua.
    qu += 2 * len(re.findall(r"[kqpt]'|kh|qh|ph|th", bajo))
    return es, qu


def _limpiar(pagina: str) -> list[str]:
    lineas = []
    for cruda in pagina.splitlines():
        linea = unicodedata.normalize("NFC", cruda).strip()
        if not linea or linea.isdigit():          # números de página
            continue
        if len(linea) < 3 or re.fullmatch(r"[.\s·…]+", linea):
            continue
        lineas.append(linea)
    return lineas


def extraer(ruta: Path) -> list[dict]:
    from pypdf import PdfReader

    paginas = PdfReader(str(ruta)).pages
    # Las primeras páginas son carátula, directivos del CMP, créditos e índice.
    # El contenido empieza en «Filiación», que es la primera sección real.
    empieza = 0
    for k, pagina in enumerate(paginas):
        texto = pagina.extract_text() or ""
        if "Filiación" in texto and "..." not in texto:
            empieza = k
            break
    print(f"el contenido empieza en la página {empieza + 1} de {len(paginas)}")

    pares, sueltas = [], 0
    for numero, pagina in enumerate(paginas[empieza:], start=empieza + 1):
        lineas = _limpiar(pagina.extract_text() or "")

        # Emparejar por columnas (todas las castellanas contra todas las quechuas)
        # parecía más robusto, pero no lo es: hay páginas donde las cuentas
        # cuadran y el orden igual se corre, porque el PDF pierde una línea o
        # parte una frase en dos. Se vuelve a lo literal: una línea castellana
        # seguida de una quechua es un par; cualquier otra cosa se descarta sin
        # consumir la línea siguiente, así un renglón suelto no corre el resto.
        i = 0
        while i + 1 < len(lineas):
            a, b = lineas[i], lineas[i + 1]
            (ea, qa), (eb, qb) = _puntaje(a), _puntaje(b)
            if ea - qa > 0 and qb - eb > 0:
                pares.append({
                    "castellano": a,
                    "collao": b,
                    "chanka_propuesto": a_chanka(b),
                    "pagina": numero,
                    "fuente": "manual-semiologia-cmp-2020",
                    "revisado": False,
                })
                i += 2
            else:
                sueltas += 1
                i += 1

    saltadas = sueltas
    print(f"líneas sin par claro: {saltadas}")
    return pares


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", default="/tmp/semiologia.pdf",
                   help=f"si no existe, bájalo de {URL}")
    args = p.parse_args()

    ruta = Path(args.pdf)
    if not ruta.exists():
        raise SystemExit(f"no está el PDF en {ruta}. Bájalo de:\n  {URL}")

    pares = extraer(ruta)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8") as f:
        for par in pares:
            f.write(json.dumps(par, ensure_ascii=False) + "\n")

    cambiados = sum(1 for x in pares if x["collao"] != x["chanka_propuesto"])
    print(f"\n{len(pares)} pares -> {SALIDA}")
    print(f"{cambiados} necesitaron quitar glotalizadas o aspiradas "
          f"({cambiados / len(pares):.0%})")
    print("\nmuestra:")
    for x in pares[:6]:
        print(f"  {x['castellano'][:46]:<48} {x['chanka_propuesto'][:44]}")


if __name__ == "__main__":
    main()
