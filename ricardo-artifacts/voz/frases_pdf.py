"""Arma el cuadernillo de grabacion: frases cortas, y tres PDF para la familia.

De donde salen las frases:
  1. Pares verificados castellano / chanka de `makitty/quechua-chanka-unified-v2`
     (CC-BY-4.0, calidad alta). Son reales: nadie del equipo escribe quechua.
  2. Frases clinicas en castellano, SIN traducir. La familia las dice en chanka
     como las diria en la posta, y la mama de Freddy escribe la transcripcion.
     Ver plan/recoleccion-de-voz.md: el quechua lo ponen ellos, no nosotros.

Tres PDF:
  frases_quechua.pdf    solo chanka         -> para leer en voz alta
  frases_castellano.pdf solo castellano     -> para decirlas en chanka
  frases_ambos.pdf      las dos columnas    -> para revisar y corregir

Uso:  PYTHONPATH=. uv run --with reportlab python voz/frases_pdf.py
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

FUENTE = ("https://datasets-server.huggingface.co/rows?"
          "dataset=makitty%2Fquechua-chanka-unified-v2&config=default&split=high_quality")
DESTINO = Path("datos/frases")
MAXIMO_VERIFICADAS = 100
LARGO_MAXIMO = 52          # caracteres; frases cortas abaratan el ajuste fino con CTC

# Lo que de verdad se dice en una consulta. En castellano a proposito:
# escribir quechua medico sin hablante nativa es el error que el producto existe
# para evitar.
CLINICAS = [
    "Tome una pastilla cada ocho horas",
    "Tome la pastilla después de comer",
    "Tómela con agua, no con té",
    "No deje la pastilla aunque se sienta bien",
    "Son siete días de tratamiento",
    "Su control es el lunes",
    "Venga en ayunas",
    "Traiga su carné",
    "Vuelva en un mes",
    "Si hay sangrado, venga de inmediato",
    "Si tiene fiebre alta, venga",
    "Si el bebé no se mueve, venga",
    "¿Desde cuándo le duele?",
    "¿Dónde le duele?",
    "¿Tiene fiebre?",
    "¿Está tomando alguna pastilla?",
    "¿Es alérgica a algo?",
    "¿Cuántos años tiene?",
    "Voy a tomarle la presión",
    "Respire hondo, por favor",
    "Tiene treinta y nueve de fiebre",
    "Dele bastante líquido",
    "Media pastilla, no entera",
    "Dos veces al día, mañana y noche",
    "El resultado llega en tres días",
]


def traer_verificadas() -> list[dict]:
    filas: list[dict] = []
    for off in range(0, 600, 100):
        try:
            d = json.load(urllib.request.urlopen(f"{FUENTE}&offset={off}&length=100", timeout=40))
        except Exception:
            break
        filas += [r["row"] for r in d.get("rows", [])]
    vistas, limpias = set(), []
    for f in filas:
        es, qu = f["spanish"].strip(), f["quechua_chanka"].strip()
        if len(es) > LARGO_MAXIMO or len(qu) > LARGO_MAXIMO + 8 or es in vistas:
            continue
        vistas.add(es)
        limpias.append({"castellano": es, "chanka": qu, "fuente": f["source"]})
    return limpias[:MAXIMO_VERIFICADAS]


def estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("t", parent=base["Title"], fontSize=19, spaceAfter=6),
        "nota": ParagraphStyle("n", parent=base["Normal"], fontSize=9.5, leading=13,
                               textColor=colors.HexColor("#4e4d45"), spaceAfter=10),
        "celda": ParagraphStyle("c", parent=base["Normal"], fontSize=10.5, leading=14),
        "seccion": ParagraphStyle("s", parent=base["Heading2"], fontSize=12, spaceBefore=14,
                                  spaceAfter=4, textColor=colors.HexColor("#16160f")),
    }


def tabla(filas, anchos, est):
    t = Table(filas, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#86847a")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#c4c2b6")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#dedcd2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def construir(nombre: str, titulo: str, nota: str, bloques) -> Path:
    est = estilos()
    ruta = DESTINO / nombre
    doc = SimpleDocTemplate(str(ruta), pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                            leftMargin=1.8 * cm, rightMargin=1.8 * cm, title=titulo)
    piezas = [Paragraph(titulo, est["titulo"]), Paragraph(nota, est["nota"])]
    for encabezado, filas, anchos in bloques:
        piezas += [Paragraph(encabezado, est["seccion"]), tabla(filas, anchos, est), Spacer(1, 4)]
    doc.build(piezas)
    return ruta


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    verificadas = traer_verificadas()
    est = estilos()
    P = lambda s: Paragraph(s, est["celda"])
    linea = "_" * 34

    (DESTINO / "frases.json").write_text(json.dumps(
        {"verificadas": verificadas, "clinicas_sin_traducir": CLINICAS},
        ensure_ascii=False, indent=1), encoding="utf-8")

    nota_comun = (f"{len(verificadas)} frases verificadas vienen del conjunto "
                  "<b>makitty/quechua-chanka-unified-v2</b> (CC-BY-4.0). Las "
                  f"{len(CLINICAS)} frases clínicas van <b>sin traducir a propósito</b>: "
                  "el quechua lo pone la familia, no el equipo. "
                  "Grabe cada frase por separado, en un lugar silencioso, y diga el número antes.")

    construir("frases_quechua.pdf", "Rimay · frases en quechua chanka",
              nota_comun + " <b>Este cuadernillo es para leer en voz alta.</b>",
              [("Frases verificadas",
                [["#", "Quechua chanka"]] + [[str(i), P(f["chanka"])]
                                             for i, f in enumerate(verificadas, 1)],
                [1.2 * cm, 15 * cm])])

    construir("frases_castellano.pdf", "Rimay · frases en castellano",
              nota_comun + " <b>Diga cada frase en chanka, como la diría en la posta.</b>",
              [("Frases verificadas",
                [["#", "Castellano"]] + [[str(i), P(f["castellano"])]
                                         for i, f in enumerate(verificadas, 1)],
                [1.2 * cm, 15 * cm]),
               ("Frases de la posta · sin traducción, usted pone el quechua",
                [["#", "Castellano"]] + [[f"C{i}", P(t)] for i, t in enumerate(CLINICAS, 1)],
                [1.2 * cm, 15 * cm])])

    construir("frases_ambos.pdf", "Rimay · castellano y quechua chanka",
              nota_comun + " <b>Revise cada par y corrija el quechua si hace falta.</b>",
              [("Frases verificadas",
                [["#", "Castellano", "Quechua chanka"]] +
                [[str(i), P(f["castellano"]), P(f["chanka"])]
                 for i, f in enumerate(verificadas, 1)],
                [1.1 * cm, 7.4 * cm, 7.7 * cm]),
               ("Frases de la posta · escriba el quechua en la columna vacía",
                [["#", "Castellano", "Quechua chanka"]] +
                [[f"C{i}", P(t), P(linea)] for i, t in enumerate(CLINICAS, 1)],
                [1.1 * cm, 7.4 * cm, 7.7 * cm])])

    total = len(verificadas) + len(CLINICAS)
    print(f"{len(verificadas)} frases verificadas + {len(CLINICAS)} clínicas = {total} por persona")
    for p in sorted(DESTINO.glob("*.pdf")):
        print(f"  {p}  {p.stat().st_size // 1024} KB")
    print(f"\nA 3.5 s por frase: {total * 3.5 / 60:.1f} min de audio por persona.")
    print(f"Con 4 personas: {total * 4} clips, {total * 4 * 3.5 / 60:.0f} min de audio.")


if __name__ == "__main__":
    main()
