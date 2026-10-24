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

# Prestamos del castellano. La prueba de humo del 24-oct mostro que ahi falla
# omniASR: "doctor" -> "luctor", "jefelláy" -> "que fillay". Son palabras que NO
# existen en quechua pero se pronuncian distinto cuando las dice un hablante de
# chanka, y son justo las que no se pueden equivocar en una posta.
MEDICAMENTOS = [
    "Tome paracetamol", "Tome ibuprofeno", "Tome amoxicilina", "Tome omeprazol en ayunas",
    "Tome sulfato ferroso", "Tome ácido fólico", "Tome albendazol", "Tome metformina",
    "Tome losartán", "Use el salbutamol", "Dele suero oral", "Tome vitamina C",
    "Tome el jarabe", "Tome una tableta", "Le voy a poner una ampolla", "Póngale tres gotas",
    "Una cucharadita de jarabe", "Cinco mililitros de jarabe", "Pastilla de quinientos miligramos",
    "Media tableta", "El doctor lo va a ver", "La doctora la va a atender",
    "La enfermera le va a explicar", "La obstetra la va a revisar", "Vaya a la posta",
    "Lo vamos a llevar al hospital", "Le voy a medir la presión", "Usted tiene diabetes",
    "Usted tiene anemia", "Venga a su control", "Aquí está su receta",
]

# Numeros y tiempos: de ellos dependen las dosis y los dias, que es lo que no puede fallar.
NUMEROS = [
    "Cuente del uno al diez",
    "Diga los días de la semana, del lunes al domingo",
    "Tome la pastilla en la mañana, en la tarde y en la noche",
    "Tome la pastilla cada ocho horas",
    "Tome la pastilla cada doce horas",
    "Vuelva en una semana",
    "Vuelva en un mes",
]

# Bloque B: lo que dice el PACIENTE. Frases fijas a proposito: asi cada una es un par
# castellano -> chanka (sirve para traducir) y a la vez voz del lado del paciente (sirve para entender).
# Las respuestas abiertas se descartaron el 24-oct: confundian y no daban pares de traduccion.
LIBRES = [
    "Me duele la cabeza desde ayer",
    "Me duele la barriga desde hace tres días",
    "Estoy tomando paracetamol",
    "Mi hijo tiene fiebre desde anoche",
    "Mi hija tiene diarrea desde hace dos días",
    "No entendí, ¿me lo puede repetir?",
    "¿Qué hago si me olvido la pastilla?",
    "¿Cuándo es mi próximo control?",
    "No soy alérgico a ningún remedio",
    "Tengo que tomar una pastilla cada ocho horas, por siete días",
    "Ya me siento mejor",
    "Gracias, señorita",
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
        "titulo": ParagraphStyle("t", parent=base["Title"], fontSize=21, spaceAfter=8),
        "nota": ParagraphStyle("n", parent=base["Normal"], fontSize=11.5, leading=16,
                               textColor=colors.HexColor("#4e4d45"), spaceAfter=10),
        "celda": ParagraphStyle("c", parent=base["Normal"], fontSize=12.5, leading=17),
        "seccion": ParagraphStyle("s", parent=base["Heading2"], fontSize=14, spaceBefore=16,
                                  spaceAfter=4, textColor=colors.HexColor("#16160f")),
    }


def tabla(filas, anchos, est):
    t = Table(filas, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 12.5),
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

    # Lo que ve la persona: numeros simples, 1, 2, 3... Lo que usa el etiquetador: (bloque, numero).
    numeracion, n = {}, 0
    for letra, lista in (("C", CLINICAS), ("M", MEDICAMENTOS), ("N", NUMEROS), ("B", LIBRES), ("E", verificadas)):
        for i in range(1, len(lista) + 1):
            n += 1
            numeracion[str(n)] = [letra, i]
    rango = {}
    n = 0
    for letra, lista in (("C", CLINICAS), ("M", MEDICAMENTOS), ("N", NUMEROS), ("B", LIBRES), ("E", verificadas)):
        rango[letra] = (n + 1, n + len(lista)); n += len(lista)

    (DESTINO / "frases.json").write_text(json.dumps(
        {"verificadas": verificadas, "clinicas_sin_traducir": CLINICAS,
         "medicamentos_y_prestamos": MEDICAMENTOS, "numeros_y_tiempos": NUMEROS,
         "respuestas_libres": LIBRES,
         "numeracion": numeracion},
        ensure_ascii=False, indent=1), encoding="utf-8")

    nota_comun = (
        "<b>¿Para qué sirve?</b> Estamos haciendo una app para que el personal de las postas pueda hablar "
        "con los pacientes en quechua. Cada frase que usted grabe le enseña dos cosas: a <b>traducir</b> "
        "bien del castellano al quechua en temas de salud, y a <b>entender y pronunciar</b> el quechua chanka.<br/><br/>"
        "<b>Cómo grabar, en 4 pasos</b><br/>"
        "1. Lea la frase en castellano.<br/>"
        "2. En WhatsApp, mantenga presionado el micrófono para grabar una nota de voz.<br/>"
        "3. Diga el <b>número</b> en castellano y después la frase <b>en quechua</b>, como usted la diría "
        "en la posta, con sus propias palabras.<br/>"
        "4. Suelte y envíe. <b>Una nota de voz por frase</b>, a la persona que le pasó este documento.<br/><br/>"
        "<b>Ejemplo.</b> Usted ve: «3 · Tómela con agua, no con té». Graba: «tres» y luego la frase en quechua.<br/><br/>"
        "<b>No tiene que escribir nada.</b> Si no sabe cómo se dice algo, sáltelo. "
        "Lugar tranquilo, el celular cerca de la boca. Las partes 1 a 4 toman unos 25 minutos; "
        "la parte 5 es solo si le queda tiempo.")

    def parte(titulo, letra, lista, texto=lambda x: x):
        ini, _ = rango[letra]
        return (titulo, [["N.º", "Frase en castellano"]] +
                [[str(ini + i), P(texto(x))] for i, x in enumerate(lista)], [1.4 * cm, 15 * cm])

    bloques = [
        parte("Parte 1 · Lo que dice la enfermera · dígalo en quechua", "C", CLINICAS),
        parte("Parte 2 · Medicinas · dígalo en quechua (el nombre de la medicina, como lo dice la gente)", "M", MEDICAMENTOS),
        parte("Parte 3 · Números y días · dígalo en quechua", "N", NUMEROS),
        parte("Parte 4 · Lo que dice el paciente · dígalo en quechua", "B", LIBRES),
        ("Parte 5 · Extra, solo si le queda tiempo · lea en voz alta la columna en quechua",
         [["N.º", "Castellano", "Quechua chanka"]] +
         [[str(rango["E"][0] + i), P(f["castellano"]), P(f["chanka"])] for i, f in enumerate(verificadas)],
         [1.4 * cm, 7.2 * cm, 7.6 * cm]),
    ]
    construir("frases_ambos.pdf", "Ayúdenos a enseñarle quechua a Rimay", nota_comun, bloques)
    construir("frases_castellano.pdf", "Ayúdenos a enseñarle quechua a Rimay", nota_comun, bloques[:4])
    construir("frases_quechua.pdf", "Rimay · frases para leer en quechua chanka",
              "Lea en voz alta cada frase. Una nota de voz por frase: diga el número y después la frase.",
              [bloques[4]])

    total = len(CLINICAS) + len(MEDICAMENTOS) + len(NUMEROS) + len(LIBRES)
    print(f"{len(CLINICAS)} clínicas + {len(MEDICAMENTOS)} medicamentos + {len(NUMEROS)} números + "
          f"{len(LIBRES)} libres = {total} por persona (+ {len(verificadas)} extra opcionales)")
    for p in sorted(DESTINO.glob("*.pdf")):
        print(f"  {p}  {p.stat().st_size // 1024} KB")
    print(f"\nA 3.5 s por frase: {total * 3.5 / 60:.1f} min de audio por persona.")
    print(f"Con 4 personas: {total * 4} clips, {total * 4 * 3.5 / 60:.0f} min de audio.")


if __name__ == "__main__":
    main()
