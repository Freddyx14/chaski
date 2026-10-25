"""Regenerate app/chaski/banco.json (and its embedding cache) deterministically.

    cd app && uv run python ../evals/banco/construir.py            # json + embeddings
    cd app && uv run python ../evals/banco/construir.py --sin-embeddings

Sources, in order:
  1. The emergency set below (ids `emg-*`). When the CMP manual has the same phrase, the item IS that manual
     row (its Quechua, `revisado: false`). When it doesn't, `quy` stays empty and the item is tagged
     `falta_quechua` for the nurse / a native speaker. Quechua is never written here.
  2. ricardo-artifacts/datos/frases/semiologia_cmp.jsonl (Colegio Médico del Perú 2020): `castellano` +
     `chanka_propuesto`, `revisado: false`, no audio. Rows broken by the PDF parse are dropped (see `_util`).
  3. Family recordings, block E of the form manifest (verified Quechua read aloud). Lives in the gitignored
     ORIGINAL repo at clients/chaski/data/formulario/manifest.jsonl; only the public Blob URL and the persona
     code are copied, never audio. Missing manifest → skipped with a note.

Leakage rule (ricardo-artifacts/reports/datasets-quechua.md): any item whose normalized Spanish equals one
of the 100 `verificadas` in frases.json is excluded; those are reserved for measuring translation.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "app"))

from chaski.banco import BANCO, CACHE_EMBEDDINGS, Banco, normalizar  # noqa: E402

SEMIOLOGIA = RAIZ / "ricardo-artifacts" / "datos" / "frases" / "semiologia_cmp.jsonl"
FRASES = RAIZ / "ricardo-artifacts" / "datos" / "frases" / "frases.json"
MANIFEST_POR_DEFECTO = Path("/Users/freddy/projects/1-projects-active/loopmind/clients/chaski/data/formulario/manifest.jsonl")
RESUMEN = Path(__file__).resolve().parent / "resumen_construccion.json"

# The PDF parse turned the "fi" ligature into a NUL byte ("¿Tiene \\u0000ebre…", "Pre\\u0000ere", "di\\u0000cultad").
# Repaired here, in the open, so the diff is auditable. Applied to the Spanish only; the Quechua is left as parsed.
REPARACIONES = {"\x00": "fi"}

# (id, Spanish as the nurse needs it, normalized Spanish of the CMP row that says the same thing or None, extra tags)
REVISION = Path(__file__).with_name("revision_enfermera.json")

EMERGENCIA: list[tuple[str, str, str | None, list[str]]] = [
    ("emg-dolor-donde", "¿Dónde le duele?", None, ["dolor"]),
    ("emg-dolor-que", "¿Qué es lo que le duele?", "que es lo que le duele", ["dolor"]),
    ("emg-senale", "Señale con el dedo", "senale con el dedo", ["dolor"]),
    ("emg-desde-cuando", "¿Desde cuándo está enfermo?", "desde cuando esta enfermo", ["motivo_consulta"]),
    ("emg-alergia", "¿Es alérgico a algún medicamento?", None, ["alergias", "medicamentos"]),
    ("emg-embarazo", "¿Está embarazada?", None, ["embarazo"]),
    ("emg-acompanante", "¿Vino con alguien?", None, ["identificacion"]),
    ("emg-familia-aqui", "¿Tiene familia aquí?", "tiene familia aqui", ["identificacion"]),
    ("emg-respira", "¿Puede respirar bien?", None, ["respiratorio"]),
    ("emg-fiebre", "¿Tiene fiebre o escalofríos?", "tiene fiebre o escalofrios", ["fiebre"]),
    ("emg-vomito", "¿Vomitó?", None, ["digestivo"]),
    ("emg-medicamento-tomo", "¿Tomó algún medicamento?", None, ["medicamentos"]),
    ("emg-caida", "¿Se cayó o se golpeó?", None, ["trauma"]),
    ("emg-cabeza", "¿Le duele la cabeza?", "le duele la cabeza", ["dolor", "cabeza"]),
    ("emg-abdomen", "¿Le duele el abdomen?", "le duele el abdomen", ["dolor", "digestivo"]),
    ("emg-mareos", "¿Tiene mareos?", "tiene mareos", ["neurologico"]),
    ("emg-nombre", "¿Cómo te llamas?", "como te llamas", ["identificacion"]),
    ("emg-edad", "¿Cuántos años tienes?", "cuantos anos tienes", ["identificacion"]),
    ("emg-presion", "Voy a tomarle la presión.", "voy a tomarle la presion", ["cardiovascular"]),
    ("emg-via", "Voy a ponerle una vía.", None, ["procedimientos"]),
    ("emg-suero", "Le voy a poner suero.", "le voy a poner suero", ["procedimientos"]),
    ("emg-no-moverse", "No trate de moverse.", "no trate de moverse", ["indicaciones"]),
    ("emg-no-miedo", "No debe tener miedo.", "no debe tener miedo", ["calma"]),
    ("emg-tranquilo", "No se preocupe, estamos aquí para ayudarle.", None, ["calma"]),
]

# Clinical-area tags by keyword on normalized Spanish. Several can apply; none → `general`.
REGLAS_TAGS: list[tuple[str, tuple[str, ...]]] = [
    ("identificacion", ("llamas", "anos tienes", "de donde", "esposa", "esposo", "tienes hijos", "cuantos hijos",
                        "cuantos hombres", "familia")),
    ("motivo_consulta", ("ha venido", "le molesta o por que", "desde cuando esta enfermo", "como le comenzo")),
    ("dolor", ("duele", "dolor", "punza", "le late", "revienta", "irradia", "calma", "ardor")),
    ("cabeza", ("cabeza", "mareo")),
    ("respiratorio", ("tos", "respir", "aire", "agita", "silba", "ronca", "esputo", "almohadas", "ahogand")),
    ("cardiovascular", ("corazon", "presion", "palpita", "pies hinchados", "late bien", "hinchados")),
    ("digestivo", ("abdomen", "vientre", "intestino", "apetito", "comida", "comer", "coma", "mastica", "deposicion",
                   "diarrea", "heces", "dentadura", "diente", "boca", "sed", "comido", "saliva")),
    ("urinario", ("orina", "bano")),
    ("ginecologia", ("regla", "sangre todos los meses", "baja sangre", "genitales", "pene", "le baja poco",
                     "abundante los primeros")),
    ("embarazo", ("embarazada", "espera un hijo", "parto", "lactar", "dando pecho", "mamar", "hinchado en los ultimos")),
    ("neurologico", ("arrastra", "mareo", "pasos cortos", "modo de hablar", "ve luces", "sople", "silbe",
                     "cierre los ojos", "levante las manos", "rodillas", "planta de los pies", "talones")),
    ("salud_mental", ("llorar", "cansado", "hablar con nadie", "no hablar", "encierra", "voces", "demonio", "dios",
                      "matar", "dormir", "renegona", "llama la atencion", "habla solo", "cosas extranas", "duerme")),
    ("examen_fisico", ("examin", "abra la boca", "abre la boca", "quitese la ropa", "saque la lengua", "respire",
                       "deme su", "cierre los ojos", "levante las manos", "cruce", "golpecitos", "toco", "raspar",
                       "apretar", "descubrase", "oir como", "mirarle", "ahora voy a verlo", "mire y vea", "ponga suelto",
                       "pongase de costado")),
    ("procedimientos", ("inyectar", "suero", "sacar sangre", "enema", "operar", "operacion", "cortare", "lavar",
                        "via")),
    ("hospitalizacion", ("hospital", "cama", "sala", "bata", "guarde su ropa", "venda", "herida")),
    ("laboratorio", ("examen de", "frasco", "ayunas", "radiografia", "traer esputo", "traer sus heces",
                     "traer orina", "den sangre")),
    ("indicaciones", ("tiene que", "lavese", "hervir", "dele ", "traiga", "no coma", "no se saque", "no trate",
                      "no hable", "despacio", "cada mes", "puede irse", "no se agarre")),
    ("pediatria", ("hijo", "nino", "vacun", "pesarlo")),
    ("fiebre", ("fiebre", "escalofrio", "frio")),
    ("medicamentos", ("medicamento", "pastilla", "remedio")),
    ("alergias", ("alergic",)),
    ("estado_general", ("como esta", "como se siente", "mejor", "amanecido", "delicado", "comodo", "como estas")),
]


def tags_por_area(es: str) -> list[str]:
    n = f" {normalizar(es)} "
    tags = [tag for tag, claves in REGLAS_TAGS if any(f" {c}" in n for c in claves)]  # word-start match
    return tags or ["general"]


def _util(fila: dict) -> str | None:
    """Spanish of a CMP row if it is a whole Spanish phrase, else None (PDF-parse fragments and swapped columns)."""
    es = fila["castellano"]
    for roto, bien in REPARACIONES.items():
        es = es.replace(roto, bien)
    es = " ".join(es.split())
    primera = next((c for c in es if c.isalpha()), "")
    if not primera or primera.islower():  # starts mid-sentence: the PDF split the line
        return None
    if "'" in es or "’" in es:  # glottal apostrophes: this "Spanish" is Quechua
        return None
    if not fila.get("chanka_propuesto", "").strip():
        return None
    return es


def cargar_verificadas() -> set[str]:
    datos = json.loads(FRASES.read_text(encoding="utf-8"))
    return {normalizar(v["castellano"]) for v in datos["verificadas"]}


def construir(manifest: Path) -> tuple[list[dict], dict]:
    verificadas = cargar_verificadas()
    excluidas: list[dict] = []
    descartadas: list[str] = []
    vistos: set[str] = set()
    items: list[dict] = []

    def agregar(item: dict) -> None:
        clave = normalizar(item["es"])
        if clave in verificadas:
            excluidas.append({"es": item["es"], "fuente": item["fuente"]})
            return
        if clave in vistos:
            return
        vistos.add(clave)
        items.append(item)

    semiologia = [json.loads(l) for l in SEMIOLOGIA.read_text(encoding="utf-8").splitlines() if l.strip()]
    cmp_por_es: dict[str, tuple[int, dict, str]] = {}
    for i, fila in enumerate(semiologia):
        es = _util(fila)
        if es is None:
            descartadas.append(fila["castellano"])
            continue
        cmp_por_es.setdefault(normalizar(es), (i, fila, es))

    usadas: set[int] = set()
    for id_, es, clave_cmp, extra in EMERGENCIA:
        base = cmp_por_es.get(clave_cmp) if clave_cmp else None
        if clave_cmp and base is None:
            raise SystemExit(f"emergency item {id_} points at a CMP row that isn't there: {clave_cmp!r}")
        if base:
            i, fila, es_cmp = base
            usadas.add(i)
            tags = ["emergencia", *dict.fromkeys(extra + [t for t in tags_por_area(es_cmp) if t != "general"])]
            agregar({"id": id_, "es": es_cmp, "quy": fila["chanka_propuesto"].strip(), "audio": None, "tags": tags,
                     "fuente": f"cmp-semiologia-2020 p.{fila['pagina']}", "revisado": False, "split": "banco"})
        else:
            agregar({"id": id_, "es": es, "quy": "", "audio": None,
                     "tags": ["emergencia", *extra, "falta_quechua"],
                     "fuente": "chaski-emergencia (falta quechua, para la enfermera)", "revisado": False,
                     "split": "banco"})

    # The nurse's review (evals/banco/revision_enfermera.json): approved CMP Quechua becomes revisado, and the phrases
    # she wrote replace the empty ones. Only `revisado: true` is ever spoken (chaski.orquestador / the app).
    if REVISION.exists():
        rev = json.loads(REVISION.read_text(encoding="utf-8"))
        por_id = {it["id"]: it for it in items}
        for id_ in rev.get("aprobadas_tal_cual", []):
            if id_ in por_id and por_id[id_]["quy"]:
                por_id[id_]["revisado"] = True
                por_id[id_]["fuente"] += " · revisada por la enfermera"
        for id_, r in rev.get("escritas_por_ella", {}).items():
            if id_ not in por_id:
                continue
            it = por_id[id_]
            it.update({"quy": r["quy"], "quy_original": r["quy_original"], "revisado": bool(r["revisado"]),
                       "fuente": "enfermera de Pilpichaca (escrita por ella, ortografía normalizada)"})
            it["tags"] = [t for t in it["tags"] if t != "falta_quechua"] + ([] if r["revisado"] else ["por_confirmar"])
            if r.get("nota"):
                it["nota"] = r["nota"]

    # The emergency audio Ricardo synthesised (fine-tuned voice p24), served by the instance under
    # /emergencia/audio/p24/<id>.mp3. Only reviewed phrases with an mp3 on disk get one.
    url_servicio = RAIZ / "ricardo-artifacts" / "servicio" / "url.json"
    mp3s = RAIZ / "ricardo-artifacts" / "reports" / "emergencia" / "p24"
    if url_servicio.exists() and mp3s.is_dir():
        base = json.loads(url_servicio.read_text(encoding="utf-8"))["url"].rstrip("/")
        for it in items:
            if "emergencia" in it["tags"] and it.get("revisado") and (mp3s / f"{it['id']}.mp3").exists():
                it["audio"] = f"{base}/emergencia/audio/p24/{it['id']}.mp3"

    for clave, (i, fila, es) in cmp_por_es.items():
        if i in usadas:
            continue
        agregar({"id": f"cmp-{i:03d}", "es": es, "quy": fila["chanka_propuesto"].strip(), "audio": None,
                 "tags": tags_por_area(es), "fuente": f"cmp-semiologia-2020 p.{fila['pagina']}",
                 "revisado": False, "split": "banco"})

    familia_vistas = 0
    if manifest.exists():
        for l in manifest.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("bloque") != "E" or not r.get("consentimiento") or not r.get("audio", "").startswith("https://"):
                continue
            familia_vistas += 1
            agregar({"id": f"fam-{r['persona']}-{int(r['numero_global']):03d}", "es": r["castellano"].strip(),
                     "quy": r["transcripcion"].strip(), "audio": r["audio"], "tags": tags_por_area(r["castellano"]),
                     "fuente": f"familia {r['persona']}", "revisado": True, "split": "banco"})
    else:
        print(f"⚠ manifest not found, family recordings skipped: {manifest}", file=sys.stderr)

    resumen = {
        "total": len(items),
        "por_fuente": dict(Counter(it["fuente"].split(" ")[0] for it in items)),
        "por_tag": dict(sorted(Counter(t for it in items for t in it["tags"]).items())),
        "emergencia_con_quechua": sum(1 for it in items if "emergencia" in it["tags"] and it["quy"]),
        "emergencia_falta_quechua": sum(1 for it in items if "falta_quechua" in it["tags"]),
        "cmp_filas_descartadas_por_parseo": len(descartadas),
        "familia_bloque_E_vistas": familia_vistas,
        "excluidas_por_fuga": excluidas,
        "manifest_leido": manifest.exists(),
    }
    return items, resumen


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--manifest", type=Path, default=MANIFEST_POR_DEFECTO)
    p.add_argument("--sin-embeddings", action="store_true")
    a = p.parse_args()

    items, resumen = construir(a.manifest)
    BANCO.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    RESUMEN.write_text(json.dumps(resumen, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not a.sin_embeddings:
        CACHE_EMBEDDINGS.unlink(missing_ok=True)
        Banco(items, cache=CACHE_EMBEDDINGS).vectores()
    print(json.dumps({k: v for k, v in resumen.items() if k != "excluidas_por_fuga"}, ensure_ascii=False, indent=1))
    print(f"excluidas por fuga: {len(resumen['excluidas_por_fuga'])}")


if __name__ == "__main__":
    main()
