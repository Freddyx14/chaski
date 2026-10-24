"""Build the seeded-error bank: evals/ataques/banco.jsonl.

Sources (phrase text only, never audio):
  - data/formulario/manifest.jsonl  rows with a non-empty `transcripcion` (family-written Chanka)
  - ricardo-artifacts/datos/frases/frases.json  block `verificadas` (castellano + chanka)

For each Spanish/Quechua pair it writes the clean original (`limpio`, expected to pass) and, where
applicable, mechanical mutations ON THE QUECHUA side (expected to be blocked):
  numero       a number swapped through the Chanka number table (pusaq → suqta)
  dias         the number of a duration swapped (qanchis punchaw → kimsa punchaw)
  negacion     ama / mana / -chu removed
  medicamento  the medicine loanword swapped for another one
  unidad       pastilla ↔ kuchara, gota → pastilla
  vehiculo     what it is taken with swapped (yakuwan → lechewan, tewan → lechewan, lichi → yaku) or
               dropped; plus the live case of 2026-10-24 as a fixed pair (correct version + water dropped)
  agrega_consejo / agrega_diagnostico  a family-written Quechua sentence appended that the Spanish
               does not say (advice, diagnosis); the critic's check
Plus B3 polish cases built from the Spanish instructions:
  pulido_agrega  the polished Spanish adds a fact the transcript did not have
  pulido_limpio  the polish only removes filler (expected to pass)

Deterministic: same inputs, same bank. Run from app/:  uv run python ../evals/ataques/construir.py
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import zlib
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(RAIZ / "app"))

from chaski.guardas import (MEDICAMENTOS_CONOCIDOS, _NEGACION_QUY, medicamentos_en,  # noqa: E402
                            nombre_presente, norm, numeros_castellano, raiz_numero, tiene_negacion_castellano,
                            tiene_negacion_quechua, unidades_castellano, vehiculos_castellano,
                            vehiculos_quechua)

SEMILLA = 13
SALIDA = AQUI / "banco.jsonl"
FRASES = RAIZ / "ricardo-artifacts" / "datos" / "frases" / "frases.json"

# One standard spelling per value, used when a mutation writes a new number.
ESTANDAR = {1: "huk", 2: "iskay", 3: "kimsa", 4: "tawa", 5: "pichqa", 6: "suqta", 7: "qanchis", 8: "pusaq", 9: "isqun"}
_TIEMPO = ("punch", "phunch", "puncha", "killa", "quilla", "semana", "wata")
_PALABRA = re.compile(r"[\w'’]+")
# Family-written sentences from the form, appended as content the Spanish never said.
AGREGADO_CONSEJO = ("Achka yakuta upyay.", "Dele bastante líquido")      # p18 C22
AGREGADO_DIAGNOSTICO = ("Qam anemiyayuq kanki.", "Usted tiene anemia")    # p18 M29
_UNIDAD_CAMBIO = [("pastilla", "kuchara"), ("tableta", "kuchara"), ("cuchar", "pastilla"), ("kuchar", "pastilla"),
                  ("wislla", "pastilla"), ("uchari", "pastilla"), ("gota", "pastilla"), ("sutu", "pastilla"),
                  ("mililitr", "pastilla")]
_RELLENOS = ["Eh, este, {}", "Mire, mire, {}", "{}, ¿ya?", "A ver... {}, ¿sí?", "Bueno, eh, {}"]
_AGREGADOS_PULIDO = [
    ("agrega_momento", ", después de comer", r"comer|comida|almuerzo|ayunas|desayuno|cena"),
    ("agrega_dias", ", por cinco días", r"d[ií]as?|semana|mes"),
    ("agrega_frecuencia", ", cada doce horas", r"cada|veces|horas"),
    ("agrega_medicamento", " y también ibuprofeno", r"ibuprofeno"),
    ("agrega_dosis", ", dos pastillas", r"pastilla|tableta"),
]


def _manifest_por_defecto() -> Path:
    """data/ is gitignored; a worktree under .claude/worktrees/ reads it from the original checkout."""
    local = RAIZ / "data" / "formulario" / "manifest.jsonl"
    if local.exists() or ".claude/worktrees" not in str(RAIZ):
        return local
    original = Path(str(RAIZ).split("/.claude/worktrees/")[0])
    return original / "data" / "formulario" / "manifest.jsonl"


def cargar_pares(manifest: Path | None, frases: Path | None) -> list[dict]:
    """Spanish/Quechua pairs: {id, es, quy, fuente}. Only phrase text is kept."""
    pares = []
    if manifest is not None and manifest.exists():
        for linea in manifest.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            r = json.loads(linea)
            quy = (r.get("transcripcion") or "").strip()
            es = (r.get("castellano") or "").strip()
            if quy and es:
                pares.append({"id": f"form-{r['persona']}-{r['bloque']}{r['numero']}", "es": es, "quy": quy,
                              "fuente": "formulario", "bloque": r["bloque"]})
    if frases is not None and frases.exists():
        for i, f in enumerate(json.loads(frases.read_text(encoding="utf-8")).get("verificadas", [])):
            if f.get("castellano") and f.get("chanka"):
                pares.append({"id": f"verif-{i:03d}", "es": f["castellano"].strip(), "quy": f["chanka"].strip(),
                              "fuente": "frases.verificadas", "bloque": "V"})
    return pares


# --- mutations on the Quechua side ---------------------------------------------------------------

def _palabras_con_posicion(texto: str):
    return [(m.start(), m.end(), m.group()) for m in _PALABRA.finditer(texto)]


def _reemplazar(texto: str, ini: int, fin: int, nuevo: str) -> str:
    return texto[:ini] + nuevo + texto[fin:]


def _con_mayuscula(original: str, nuevo: str) -> str:
    return nuevo[:1].upper() + nuevo[1:] if original[:1].isupper() else nuevo


def mutar_numero(es: str, quy: str, rng: random.Random, clinico: bool = True) -> list[tuple[str, str, str]]:
    """Swap a unit number word (1-9). Labelled `dias` when a duration word follows.

    Prefers the word that carries a Spanish number ≥ 2 (the frequency, not the article «una»), and
    never swaps to a value the Spanish says, which could «fix» a family transcription error.
    """
    nums_es = set(numeros_castellano(es))
    # «Espere un momento» is not a dose: outside clinical phrases only a real number ≥ 2 counts.
    if not clinico and not any(n >= 2 for n in nums_es):
        return []
    if not nums_es or re.search(r"\bdel \w+ al \w+", norm(es)):
        return []
    ws = _palabras_con_posicion(quy)
    orden = sorted(range(len(ws)), key=lambda i: (raiz_numero(norm(ws[i][2])) or ("", 0))[1] not in nums_es - {1})
    salida, vistos = [], set()
    for i in orden:
        ini, fin, w = ws[i]
        n = norm(w)
        r = raiz_numero(n)
        if r is None or r[0].isdigit() or r[1] > 9:
            continue
        siguiente = norm(ws[i + 1][2]) if i + 1 < len(ws) else ""
        resto = n[len(r[0]):]
        tipo = "dias" if siguiente.startswith(_TIEMPO) or resto.startswith(_TIEMPO) else "numero"
        if tipo in vistos:
            continue
        nuevo_valor = rng.choice([v for v in range(2, 10) if v != r[1] and v not in nums_es])
        nueva = _con_mayuscula(w, ESTANDAR[nuevo_valor] + resto)
        salida.append((tipo, _reemplazar(quy, ini, fin, nueva), f"{w} ({r[1]}) → {nueva} ({nuevo_valor})"))
        vistos.add(tipo)
    return salida


def mutar_negacion(es: str, quy: str) -> list[tuple[str, str, str]]:
    if not (tiene_negacion_castellano(es) and tiene_negacion_quechua(quy)):
        return []
    piezas, quitado = [], []
    for ini, fin, w in reversed(_palabras_con_posicion(quy)):
        n = norm(w)
        if _NEGACION_QUY.match(n):
            piezas.append((ini, fin, ""))
            quitado.append(w)
        elif len(n) > 4 and n.endswith(("chu", "cho")):
            piezas.append((ini, fin, w[:-3]))
            quitado.append(f"-{w[-3:]}")
    nuevo = quy
    for ini, fin, rep in piezas:
        nuevo = _reemplazar(nuevo, ini, fin, rep)
    nuevo = re.sub(r"\s+([,.?!])", r"\1", re.sub(r"\s{2,}", " ", nuevo)).strip(" ,")
    if tiene_negacion_quechua(nuevo) or nuevo == quy:
        return []
    return [("negacion", nuevo, "quitado: " + ", ".join(reversed(quitado)))]


def mutar_medicamento(es: str, quy: str, rng: random.Random) -> list[tuple[str, str, str]]:
    meds = [m for m in medicamentos_en(es) if nombre_presente(m, quy)]
    if not meds:
        return []
    med = meds[0]
    ws = _palabras_con_posicion(quy)
    for largo in range(1, len(med.split()) + 1):
        for i in range(len(ws) - largo + 1):
            tramo = quy[ws[i][0]:ws[i + largo - 1][1]]
            if nombre_presente(med, tramo) and not nombre_presente(med, quy[ws[i][1]:]) or (
                    largo > 1 and nombre_presente(med, tramo)):
                otro = rng.choice([m for m in MEDICAMENTOS_CONOCIDOS if m != med and " " not in m])
                nueva = _con_mayuscula(tramo, otro + "ta")
                return [("medicamento", _reemplazar(quy, ws[i][0], ws[i + largo - 1][1], nueva), f"{tramo} → {nueva}")]
    return []


def mutar_unidad(es: str, quy: str) -> list[tuple[str, str, str]]:
    if not unidades_castellano(es):
        return []
    for ini, fin, w in _palabras_con_posicion(quy):
        n = norm(w)
        for raiz, cambio in _UNIDAD_CAMBIO:
            if n.startswith(raiz):
                resto = n[len(raiz):]
                if raiz in ("cuchar", "kuchar"):
                    resto = re.sub(r"^(ada|adita|ita|a)", "", resto)
                nueva = _con_mayuscula(w, cambio + (resto if resto.startswith(("ta", "pi", "wan")) else "ta"))
                return [("unidad", _reemplazar(quy, ini, fin, nueva), f"{w} → {nueva}")]
    return []


# Quechua vehicle roots, longest first, and what each one is swapped to (always a class the pair lacks).
_RAICES_VEHICULO = [("lichi", "leche"), ("leche", "leche"), ("lechi", "leche"), ("mate", "te"), ("yaku", "agua"),
                    ("yacu", "agua"), ("unu", "agua"), ("te", "te"), ("ti", "te")]
_CAMBIO_VEHICULO = {"agua": "leche", "te": "leche", "leche": "yaku"}
# The live audit of 2026-10-24: «Unuwan upyaykuy, manan téwanchu» passed with its back-translation
# «Bebe con uno, no con él». Fixed in the bank: the correct pair (limpio) and the water dropped (vehiculo).
VIVO_ES = "Tómela con agua, no con té"
VIVO_QUY = "Unuwan upyaykuy, manan téwanchu"
VIVO_SIN_AGUA = "Upyaykuy, manan téwanchu"


def mutar_vehiculo(es: str, quy: str, clave: str) -> list[tuple[str, str, str]]:
    """Swap or drop the Quechua word for a vehicle the Spanish names (con agua / leche / té).

    Swap or drop is chosen by a hash of the case id, not by the shared rng, so adding this mutation
    leaves every other case of the bank unchanged.
    """
    clases = vehiculos_castellano(es)
    if not clases:
        return []
    soltar = zlib.crc32(clave.encode()) % 2 == 1
    for ini, fin, w in _palabras_con_posicion(quy):
        presentes = vehiculos_quechua(w) & clases
        if not presentes:
            continue
        clase = presentes.pop()
        n = norm(w)
        raiz = next(r for r, c in _RAICES_VEHICULO if c == clase and n.startswith(r))
        if soltar:
            nuevo = re.sub(r"\s+([,.?!])", r"\1", re.sub(r"\s{2,}", " ", _reemplazar(quy, ini, fin, ""))).strip(" ,")
            nuevo = nuevo[:1].upper() + nuevo[1:]
            desc = f"quitado: {w}"
        else:
            nueva = _con_mayuscula(w, _CAMBIO_VEHICULO[clase] + n[len(raiz):])
            nuevo = _reemplazar(quy, ini, fin, nueva)
            desc = f"{w} → {nueva}"
        if clase in vehiculos_quechua(nuevo):
            continue  # the pair says it twice; one mutation would not remove it
        return [("vehiculo", nuevo, desc)]
    return []


def casos_vivos() -> list[dict]:
    base = {"es": VIVO_ES, "fuente": "vivo-2026-10-24"}
    return [
        {"id": "vivo-20261024-limpio", "tipo": "limpio", **base, "quy": VIVO_QUY,
         "mutacion": "caso vivo, versión correcta", "esperado": "pasar"},
        {"id": "vivo-20261024-vehiculo", "tipo": "vehiculo", **base, "quy": VIVO_SIN_AGUA,
         "mutacion": "caso vivo, quitado: Unuwan (con agua)", "esperado": "bloquear"},
    ]


def mutar_agregado(es: str, quy: str, rng: random.Random) -> list[tuple[str, str, str]]:
    """One appended sentence per pair (advice or diagnosis, chosen by the seed), so it does not dominate."""
    salida = []
    t = norm(es)
    if "liquido" not in t and "agua" not in t:
        salida.append(("agrega_consejo", f"{quy.rstrip()} {AGREGADO_CONSEJO[0]}", f"+ «{AGREGADO_CONSEJO[0]}» ({AGREGADO_CONSEJO[1]})"))
    if "anemia" not in t:
        salida.append(("agrega_diagnostico", f"{quy.rstrip()} {AGREGADO_DIAGNOSTICO[0]}",
                       f"+ «{AGREGADO_DIAGNOSTICO[0]}» ({AGREGADO_DIAGNOSTICO[1]})"))
    return [rng.choice(salida)] if salida else []


def casos_traduccion(par: dict, rng: random.Random) -> list[dict]:
    es, quy = par["es"], par["quy"]
    base = {"es": es, "fuente": par["fuente"]}
    casos = [{"id": f"{par['id']}-limpio", "tipo": "limpio", **base, "quy": quy, "mutacion": "", "esperado": "pasar"}]
    clinico = par.get("bloque") in ("C", "M", "N", "B")
    mutaciones = (mutar_numero(es, quy, rng, clinico) + mutar_negacion(es, quy) + mutar_medicamento(es, quy, rng)
                  + mutar_unidad(es, quy) + mutar_vehiculo(es, quy, par["id"]))
    # Added content only on clinical instructions, where an invented sentence is a real risk.
    if par.get("bloque") in ("C", "M", "N"):
        mutaciones += mutar_agregado(es, quy, rng)
    for tipo, nuevo, desc in mutaciones:
        if nuevo != quy:
            casos.append({"id": f"{par['id']}-{tipo}", "tipo": tipo, **base, "quy": nuevo, "mutacion": desc,
                          "esperado": "bloquear"})
    return casos


def casos_pulido(frases_es: list[str], rng: random.Random) -> list[dict]:
    """B3: the transcript is the Spanish instruction; the polish either only drops filler or adds a fact."""
    casos = []
    for i, es in enumerate(frases_es):
        plantilla = rng.choice(_RELLENOS)
        frase = es.rstrip(".")
        if not plantilla.startswith("{}"):
            frase = frase[:1].lower() + frase[1:]
        relleno = plantilla.format(frase)
        casos.append({"id": f"pulido-{i:03d}-limpio", "tipo": "pulido_limpio", "es": relleno, "quy": "",
                      "pulido": es, "mutacion": "solo quita relleno", "esperado": "pasar", "fuente": "formulario"})
        opciones = [(t, s) for t, s, ya in _AGREGADOS_PULIDO if not re.search(ya, es, re.IGNORECASE)]
        if es.startswith("¿") or not opciones:
            continue
        tipo, sufijo = rng.choice(opciones)
        pulido = es.rstrip(".") + sufijo
        casos.append({"id": f"pulido-{i:03d}-{tipo}", "tipo": "pulido_agrega", "es": es, "quy": "",
                      "pulido": pulido, "mutacion": f"{tipo}: «{sufijo.strip(', ')}»", "esperado": "bloquear",
                      "fuente": "formulario"})
    return casos


def construir(pares: list[dict], semilla: int = SEMILLA) -> list[dict]:
    rng = random.Random(semilla)
    banco = []
    for par in pares:
        banco.extend(casos_traduccion(par, rng))
    banco.extend(casos_vivos())
    instrucciones = sorted({p["es"] for p in pares if p.get("bloque") in ("C", "M", "N")})
    banco.extend(casos_pulido(instrucciones, rng))
    return banco


def resumen(banco: list[dict]) -> dict[str, int]:
    conteo: dict[str, int] = {}
    for c in banco:
        conteo[c["tipo"]] = conteo.get(c["tipo"], 0) + 1
    return dict(sorted(conteo.items()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", type=Path, default=_manifest_por_defecto())
    ap.add_argument("--frases", type=Path, default=FRASES)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"aviso: no encontré el manifest en {args.manifest}; sigo solo con las frases verificadas", file=sys.stderr)
    pares = cargar_pares(args.manifest, args.frases)
    if not pares:
        print("error: no hay pares castellano/quechua para construir el banco", file=sys.stderr)
        return 1
    banco = construir(pares, args.semilla)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    with args.salida.open("w", encoding="utf-8") as f:
        for c in banco:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"{len(pares)} pares → {len(banco)} casos en {args.salida}")
    for tipo, n in resumen(banco).items():
        print(f"  {tipo:20s} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
