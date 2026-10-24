# -*- coding: utf-8 -*-
"""Propone entradas de glosario a partir de los pares del Manual de Semiología.

No escribe `app/chaski/glosario.json`. Ese archivo dice, en su propia
documentación, que solo una hablante nativa agrega entradas y que el modelo
nunca lo hace. Así que esto escribe un archivo aparte, de candidatos, para que
la revisión sea marcar sí o no en vez de traducir desde cero.

Salen dos clases de candidato, y la diferencia importa para quien revisa:

  frase     el par completo, cuando la frase castellana es corta y se sostiene
            sola («¿Le duele el abdomen?»). Es el candidato confiable: viene
            emparejado del manual, no lo inventó nadie aquí.

  termino   una palabra castellana y la palabra quechua que más se le asocia,
            contando en qué pares aparecen juntas. Con 243 pares esto es débil
            —es coocurrencia, no alineamiento— así que cada candidato sale con
            cuántas veces se vio y con ejemplos, para que se pueda juzgar. Hay
            que esperar que varios estén mal: ese es el precio de proponer.

Todo sale en Chanka propuesto, no en el Collao del manual, y con
`revisado: false`.

Uso:
  python voz/glosario_candidatos.py
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ENTRADA = Path("datos/frases/semiologia_cmp.jsonl")
SALIDA = Path("datos/frases/glosario_candidatos.json")

VACIAS = {
    "que", "qué", "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
    "su", "sus", "le", "les", "se", "en", "con", "por", "para", "y", "o", "a",
    "al", "del", "es", "son", "está", "están", "ha", "has", "tiene", "tienes",
    "cómo", "cuándo", "cuánto", "cuántos", "cuánta", "cuántas", "dónde", "qué",
    "no", "sí", "te", "tu", "me", "mi", "usted", "lo", "ya", "más", "menos",
    "cuando", "donde", "como", "si", "hay", "ser", "estar", "muy", "también",
    "este", "esta", "eso", "esto", "ese", "algo", "nada", "todo", "toda",
    "desde", "hasta", "sobre", "entre", "porque", "pero", "señor", "señora",
    "joven", "señorita", "voy", "vas", "va", "favor", "por favor",
}
# Partículas y auxiliares del quechua: aparecen en casi cualquier frase, así que
# nunca son la traducción de nada en particular.
QUECHUA_VACIAS = {
    "imayna", "iman", "ima", "imatak", "imataq", "kanchu", "kanki", "kashanky",
    "kashanki", "chu", "o", "y", "mana", "manachu", "icha", "hina", "kay",
    "chay", "allin", "allinta", "qam", "qan", "noqa", "ñoqa", "paykuna",
}

TIPO_FRASE_MAX = 5     # palabras del lado castellano para considerarlo «frase»
MINIMO_APOYO = 2       # veces que una palabra quechua tiene que coocurrir


def _palabras(texto: str) -> list[str]:
    return re.findall(r"[a-záéíóúñü']+", texto.lower())


def candidatos_frase(pares: list[dict]) -> list[dict]:
    vistos, salida = set(), []
    for par in pares:
        es, qu = par["castellano"].strip(), par["chanka_propuesto"].strip()
        if len(_palabras(es)) > TIPO_FRASE_MAX or len(_palabras(qu)) > TIPO_FRASE_MAX:
            continue
        if not es or not qu or es.lower() in vistos:
            continue
        # Fragmentos que el PDF partió a la mitad: no empiezan como una frase.
        if es[0].islower() and not es.startswith("¿"):
            continue
        vistos.add(es.lower())
        salida.append({"castellano": es, "quechua": qu, "tipo": "frase",
                       "apoyo": 1, "pagina": par["pagina"],
                       "fuente": par["fuente"], "revisado": False})
    return salida


def candidatos_termino(pares: list[dict]) -> list[dict]:
    """Empareja una palabra castellana con la quechua que más la acompaña."""
    con_palabra: dict[str, list[dict]] = defaultdict(list)
    total_quechua: Counter = Counter()

    for par in pares:
        qus = [q for q in _palabras(par["chanka_propuesto"]) if q not in QUECHUA_VACIAS]
        total_quechua.update(set(qus))
        for es in set(_palabras(par["castellano"])):
            if es not in VACIAS and len(es) > 3:
                con_palabra[es].append(par)

    salida = []
    for es, suyos in con_palabra.items():
        if len(suyos) < MINIMO_APOYO:
            continue
        cuenta: Counter = Counter()
        for par in suyos:
            cuenta.update({q for q in _palabras(par["chanka_propuesto"])
                           if q not in QUECHUA_VACIAS})
        # Se prefiere la palabra que aparece mucho CON esta y poco sin ella.
        mejor, puntaje = None, 0.0
        for qu, veces in cuenta.items():
            if veces < MINIMO_APOYO:
                continue
            p = veces / (total_quechua[qu] + 1)
            if p > puntaje or (p == puntaje and mejor and len(qu) > len(mejor)):
                mejor, puntaje = qu, p
        if mejor is None:
            continue
        salida.append({
            "castellano": es, "quechua": mejor, "tipo": "termino",
            "apoyo": cuenta[mejor], "veces_en_total": total_quechua[mejor],
            "confianza": round(puntaje, 2),
            "ejemplos": [{"castellano": s["castellano"], "quechua": s["chanka_propuesto"]}
                         for s in suyos[:2]],
            "fuente": "manual-semiologia-cmp-2020", "revisado": False,
        })
    return sorted(salida, key=lambda x: (-x["confianza"], -x["apoyo"]))


def main() -> None:
    pares = [json.loads(l) for l in ENTRADA.open(encoding="utf-8")]
    frases = candidatos_frase(pares)
    terminos = candidatos_termino(pares)
    todo = frases + terminos

    SALIDA.write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(pares)} pares leídos")
    print(f"  {len(frases):>3} candidatos de tipo frase   (emparejados por el manual)")
    print(f"  {len(terminos):>3} candidatos de tipo término (coocurrencia: esperar errores)")
    print(f"\n-> {SALIDA}")
    print("\nfrases, las confiables:")
    for c in frases[:8]:
        print(f"  {c['castellano'][:40]:<42}{c['quechua'][:36]}")
    print("\ntérminos, los de mayor confianza:")
    for c in terminos[:10]:
        print(f"  {c['castellano'][:18]:<20}{c['quechua'][:18]:<20}"
              f"apoyo {c['apoyo']}  confianza {c['confianza']}")


if __name__ == "__main__":
    main()
