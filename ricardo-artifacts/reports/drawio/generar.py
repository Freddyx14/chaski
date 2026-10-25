# -*- coding: utf-8 -*-
"""Genera los tres diagramas de arquitectura: despliegue, datos y flujo de un turno.

Cada diagrama se escribe DOS veces desde el mismo modelo en memoria:

  reports/drawio/*.drawio   editable en app.diagrams.net o en VS Code
  reports/*.svg             lo que se ve en arquitectura.md y en GitHub

Que salgan del mismo sitio es el punto: antes el .svg estaba escrito a mano y el
.drawio aparte, así que cualquiera de los dos podía quedar viejo sin que se notara.
Ahora no pueden desincronizarse, porque son dos salidas del mismo objeto.

El XML del .drawio va sin comprimir a propósito: draw.io por defecto lo guarda
comprimido en base64 y entonces el diff de git es ilegible.

Se corre desde la raíz de ricardo-artifacts (Pillow es para reducir el arte de
Chaski a 64 px):

    uv run --with pillow python reports/drawio/generar.py
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from iconos import cargar as cargar_iconos  # noqa: E402

ICONOS = cargar_iconos()
LADO_ICONO = 26
SANGRIA_ICONO = 42

FONDO = "#F4F3EE"
CAJA = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={b};strokeWidth=2;"
        "align=left;verticalAlign=top;spacingLeft=10;spacingTop=6;fontSize=11;fontColor=#4E4D45;")
TXT = "text;html=1;align=left;verticalAlign=middle;fontSize={s};fontColor={c};fontStyle={f};"

# Ancho medio de carácter como fracción del tamaño de fuente. Sirve para partir
# las líneas largas en el SVG; draw.io envuelve solo con whiteSpace=wrap.
ANCHO_CARACTER = 0.53
TIPOGRAFIA = "Archivo, Helvetica, Arial, sans-serif"


def _estilo(cadena: str) -> dict:
    d = {}
    for parte in cadena.split(";"):
        if "=" in parte:
            k, _, v = parte.partition("=")
            d[k] = v
        elif parte:
            d[parte] = "1"
    return d


def _partir(linea: str, ancho_px: float, tam: float) -> list:
    """Parte una línea para que quepa, respetando las palabras."""
    cabe = max(8, int(ancho_px / (tam * ANCHO_CARACTER)))
    if len(linea) <= cabe:
        return [linea]
    salida, actual = [], ""
    for palabra in linea.split(" "):
        tentativa = f"{actual} {palabra}".strip()
        if len(tentativa) <= cabe:
            actual = tentativa
        else:
            if actual:
                salida.append(actual)
            actual = palabra
    if actual:
        salida.append(actual)
    return salida


class Lienzo:
    """Un diagrama. Se le agregan cajas y flechas, y sabe escribirse en los dos formatos."""

    def __init__(self, nombre):
        self.nombre, self.nodos, self.aristas, self.n = nombre, [], [], 1

    def _html(self, valor):
        lineas = valor.split("\n")
        if len(lineas) > 1 and lineas[0]:
            lineas[0] = f"<b>{lineas[0]}</b>"
        return escape("<br>".join(lineas))

    def _alto_minimo(self, valor, d, w):
        """Alto que hace falta para que el texto entre, ya envuelto.

        Se calcula aquí y no a ojo porque el .svg no envuelve solo: si una caja
        queda corta, en draw.io el texto se desborda y en el .svg se sale de la
        figura. Mejor que el modelo sepa cuánto mide lo que le pusimos.
        """
        tam = float(d.get("fontSize", 11))
        sangria = 0 if "text" in d else float(d.get("spacingLeft", 10))
        util = w if "text" in d else w - sangria - 10
        lineas = 0
        for cruda in valor.split("\n"):
            lineas += 1 if not cruda else len(_partir(cruda, util, tam))
        return float(d.get("spacingTop", 6)) + lineas * tam * 1.45 + 6

    def caja(self, valor, estilo, x, y, w, h, icono=None):
        """Una caja. Con `icono`, el dibujo va arriba a la izquierda y el texto se corre.

        En draw.io eso es `shape=label` con una imagen; en el SVG es un <image>
        y una sangría. La imagen viaja incrustada en los dos, no por archivo.
        """
        self.n += 1
        i = f"n{self.n}"
        if icono and icono in ICONOS:
            estilo = estilo + (f"shape=label;image={ICONOS[icono]['drawio']};"
                               f"imageWidth={LADO_ICONO};imageHeight={LADO_ICONO};"
                               f"imageAlign=left;imageVerticalAlign=top;"
                               f"spacingLeft={SANGRIA_ICONO};")
        d = _estilo(estilo)
        if valor and not d.get("shape") or icono:
            h = max(h, round(self._alto_minimo(valor, d, w)))
        self.nodos.append({"id": i, "valor": valor, "estilo": estilo, "d": d, "icono": icono,
                           "x": x, "y": y, "w": w, "h": h})
        return i

    def flecha(self, a, b, etiqueta="", estilo=""):
        self.n += 1
        self.aristas.append({"id": f"e{self.n}", "src": a, "dst": b,
                             "etiqueta": etiqueta, "estilo": estilo, "d": _estilo(estilo)})

    # ------------------------------------------------------------ drawio
    def _xml(self, ancho, alto):
        celdas = []
        for nd in self.nodos:
            celdas.append(
                f'<mxCell id="{nd["id"]}" value="{self._html(nd["valor"])}" style="{nd["estilo"]}" '
                f'vertex="1" parent="1"><mxGeometry x="{nd["x"]}" y="{nd["y"]}" width="{nd["w"]}" '
                f'height="{nd["h"]}" as="geometry"/></mxCell>')
        for ar in self.aristas:
            base = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=blockThin;endFill=1;"
                    "strokeColor=#8C8C7A;strokeWidth=2;fontSize=11;fontColor=#4E4D45;" + ar["estilo"])
            celdas.append(
                f'<mxCell id="{ar["id"]}" value="{escape(ar["etiqueta"].replace(chr(10), "<br>"))}" '
                f'style="{base}" edge="1" parent="1" source="{ar["src"]}" target="{ar["dst"]}">'
                f'<mxGeometry relative="1" as="geometry"/></mxCell>')
        return (f'<mxfile host="app.diagrams.net" type="device">\n'
                f'  <diagram id="{self.nombre}" name="{self.nombre}">\n'
                f'    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" '
                f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{ancho}" '
                f'pageHeight="{alto}" math="0" shadow="0" background="{FONDO}">\n'
                f'      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n        '
                + "\n        ".join(celdas) + '\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n')

    # --------------------------------------------------------------- svg
    def _buscar(self, ident):
        return next(n for n in self.nodos if n["id"] == ident)

    def _ruta(self, a, b):
        """Camino ortogonal entre dos cajas, por el lado que queda enfrentado."""
        ax, ay, aw, ah = a["x"], a["y"], a["w"], a["h"]
        bx, by, bw, bh = b["x"], b["y"], b["w"], b["h"]
        if bx >= ax + aw - 1:                      # el destino está a la derecha
            p0 = (ax + aw, ay + ah / 2)
            p3 = (bx, by + bh / 2)
            medio = (p0[0] + p3[0]) / 2
            return [p0, (medio, p0[1]), (medio, p3[1]), p3]
        if by >= ay + ah - 1:                      # el destino está abajo
            p0 = (ax + aw / 2, ay + ah)
            p3 = (bx + bw / 2, by)
            medio = (p0[1] + p3[1]) / 2
            return [p0, (p0[0], medio), (p3[0], medio), p3]
        p0 = (ax, ay + ah / 2)                     # a la izquierda
        p3 = (bx + bw, by + bh / 2)
        medio = (p0[0] + p3[0]) / 2
        return [p0, (medio, p0[1]), (medio, p3[1]), p3]

    def _texto(self, nd, partes):
        d = nd["d"]
        tam = float(d.get("fontSize", 11))
        color = d.get("fontColor", "#4E4D45")
        es_texto = "text" in d
        sangria = 0 if es_texto else float(d.get("spacingLeft", 10))
        arriba = float(d.get("spacingTop", 6))
        ancho_util = nd["w"] - sangria - 10 if not es_texto else nd["w"]

        lineas = []
        crudas = nd["valor"].split("\n")
        for idx, cruda in enumerate(crudas):
            if not cruda:
                lineas.append(("", False))
                continue
            negrita = idx == 0 and (len(crudas) > 1 or d.get("fontStyle") == "1")
            for trozo in _partir(cruda, ancho_util, tam):
                lineas.append((trozo, negrita))

        alto_linea = tam * 1.45
        if es_texto:
            y0 = nd["y"] + nd["h"] / 2 + tam * 0.36 - (len(lineas) - 1) * alto_linea / 2
        else:
            y0 = nd["y"] + arriba + tam
        for k, (linea, negrita) in enumerate(lineas):
            if not linea:
                continue
            peso = ' font-weight="700"' if negrita else ""
            partes.append(f'<text x="{nd["x"] + sangria:.0f}" y="{y0 + k * alto_linea:.1f}" '
                          f'font-size="{tam}" fill="{color}"{peso}>{escape(linea)}</text>')

    def _svg(self, ancho, alto):
        partes = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" '
                  f'width="{ancho}" height="{alto}" font-family="{TIPOGRAFIA}">',
                  f'<rect width="{ancho}" height="{alto}" fill="{FONDO}"/>']
        marcadores = {}

        for nd in self.nodos:
            d, x, y, w, h = nd["d"], nd["x"], nd["y"], nd["w"], nd["h"]
            relleno = d.get("fillColor", "none")
            borde = d.get("strokeColor", "#8C8C7A")
            grosor = d.get("strokeWidth", "1")
            guion = ' stroke-dasharray="8 4"' if d.get("dashed") == "1" else ""
            forma = d.get("shape", "")

            if "text" in d:
                pass
            elif forma == "label" or not forma:
                partes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{relleno}" '
                              f'stroke="{borde}" stroke-width="{grosor}"{guion}/>')
                partes.append(f'<rect x="{x}" y="{y}" width="{w}" height="4" fill="{borde}"/>')
                if nd.get("icono") in ICONOS:
                    partes.append(f'<image href="{ICONOS[nd["icono"]]["svg"]}" x="{x + 10}" '
                                  f'y="{y + 10}" width="{LADO_ICONO}" height="{LADO_ICONO}"/>')
            elif forma == "cylinder3":
                r = 9
                partes.append(
                    f'<path d="M{x} {y + r} a{w / 2} {r} 0 0 1 {w} 0 v{h - 2 * r} '
                    f'a{w / 2} {r} 0 0 1 {-w} 0 z" fill="{relleno}" stroke="{borde}" '
                    f'stroke-width="{grosor}"/>'
                    f'<path d="M{x} {y + r} a{w / 2} {r} 0 0 0 {w} 0" fill="none" '
                    f'stroke="{borde}" stroke-width="{grosor}"/>')
            elif forma.startswith("mxgraph.aws4"):
                partes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" '
                              f'fill="#D05C17" stroke="#FFFFFF" stroke-width="2"/>'
                              f'<text x="{x + w / 2}" y="{y + h / 2 + 4}" font-size="11" '
                              f'font-weight="700" fill="#FFFFFF" text-anchor="middle">EC2</text>')
            if nd["valor"] and not forma.startswith("mxgraph.aws4"):
                if forma == "cylinder3":
                    tam = float(d.get("fontSize", 11))
                    lineas = nd["valor"].split("\n")
                    y0 = y + 10 + h / 2 - (len(lineas) - 1) * tam * 0.72
                    for k, linea in enumerate(lineas):
                        peso = ' font-weight="700"' if k == 0 else ""
                        partes.append(f'<text x="{x + w / 2}" y="{y0 + k * tam * 1.45:.1f}" '
                                      f'font-size="{tam}" fill="{d.get("fontColor", "#4E4D45")}" '
                                      f'text-anchor="middle"{peso}>{escape(linea)}</text>')
                else:
                    self._texto(nd, partes)

        for ar in self.aristas:
            color = ar["d"].get("strokeColor", "#8C8C7A")
            grosor = ar["d"].get("strokeWidth", "2")
            guion = ' stroke-dasharray="6 4"' if ar["d"].get("dashed") == "1" else ""
            clave = color.replace("#", "")
            if clave not in marcadores:
                marcadores[clave] = (f'<marker id="m{clave}" viewBox="0 0 10 10" refX="9" refY="5" '
                                     f'markerWidth="6" markerHeight="6" orient="auto">'
                                     f'<path d="M0 0 L10 5 L0 10 z" fill="{color}"/></marker>')
            puntos = self._ruta(self._buscar(ar["src"]), self._buscar(ar["dst"]))
            trazo = " ".join(f"{'M' if k == 0 else 'L'}{px:.0f} {py:.0f}"
                             for k, (px, py) in enumerate(puntos))
            partes.append(f'<path d="{trazo}" fill="none" stroke="{color}" stroke-width="{grosor}"'
                          f'{guion} marker-end="url(#m{clave})"/>')
            if ar["etiqueta"]:
                mx = (puntos[1][0] + puntos[2][0]) / 2
                my = (puntos[1][1] + puntos[2][1]) / 2
                tam = float(ar["d"].get("fontSize", 11))
                tc = ar["d"].get("fontColor", "#4E4D45")
                for k, linea in enumerate(ar["etiqueta"].split("\n")):
                    partes.append(f'<text x="{mx:.0f}" y="{my - 6 + k * tam * 1.3:.0f}" '
                                  f'font-size="{tam}" fill="{tc}" text-anchor="middle">'
                                  f'{escape(linea)}</text>')

        partes.insert(1, "<defs>" + "".join(marcadores.values()) + "</defs>")
        partes.append("</svg>")
        return "\n".join(partes) + "\n"

    def guardar(self, ruta, ancho=1700, alto=1000):
        Path(ruta).write_text(self._xml(ancho, alto), encoding="utf-8")
        svg = Path("reports") / (Path(ruta).stem + ".svg")
        svg.write_text(self._svg(ancho, alto), encoding="utf-8")
        print("escrito", ruta, "y", svg)


# ---------------------------------------------------------------- datos
d = Lienzo("Data")
d.caja("From a family's voice to a number we can defend",
       TXT.format(s=19, c="#16160F", f=1), 40, 20, 700, 28)
d.caja("Data architecture. The one rule everything rests on: the test speaker never enters training.",
       TXT.format(s=12, c="#4E4D45", f=0), 40, 48, 900, 20)

d.caja("1 · Collection", TXT.format(s=13, c="#16160F", f=1), 40, 92, 300, 20)
cua = d.caja("Printed booklets\n\n175 numbered sentences\nsix blocks: A B C M N E\nWritten first, recorded after",
             CAJA.format(b="#8C8C7A"), 40, 118, 220, 96, icono="cuaderno")
frm = d.caja("Web form (Freddy)\n\nVercel · families upload audio\nand how it is spelled\nNot touched from this side",
             CAJA.format(b="#1B9476"), 290, 118, 220, 96, icono="formulario")
cor = d.caja("/corregir (Ricardo)\n\nTranscribes, a human fixes the text\nSplits and joins bad cuts\nChecks audio against text",
             CAJA.format(b="#1F6FD0"), 540, 118, 230, 96, icono="etiqueta")
man = d.caja("manifiesto.jsonl\n\nspeaker · block · number\naudio · transcript · Spanish\nseconds · consent",
             CAJA.format(b="#8C8C7A"), 800, 118, 240, 96, icono="disco")
d.flecha(cua, frm); d.flecha(frm, cor); d.flecha(cor, man)

d.caja("2 · Split BY SPEAKER, never by sentence",
       TXT.format(s=13, c="#16160F", f=1), 40, 240, 520, 20)
tr = d.caja("train\n\n4 speakers · 476 clips\nFits the adapter",
            CAJA.format(b="#1F6FD0"), 40, 266, 230, 76)
va = d.caja("validation\n\n12 % of train\nPicks hyperparameters",
            CAJA.format(b="#8C8C7A"), 300, 266, 220, 76)
pr = d.caja("test · one whole speaker\n\nA voice the model NEVER heard\nTouched once, at the end",
            CAJA.format(b="#C8372F") + "strokeWidth=3;", 550, 266, 300, 76)

d.caja("3 · Three steps, three numbers — all three reported, whatever they say",
       TXT.format(s=13, c="#16160F", f=1), 40, 368, 700, 20)
p0 = d.caja("0 · The model as shipped\n\nBaseline. Nothing touched.",
            CAJA.format(b="#8C8C7A"), 40, 394, 250, 70)
p1 = d.caja("1 · + clinic vocabulary\n\nGlossary and loanwords",
            CAJA.format(b="#1F6FD0"), 320, 394, 250, 70)
p2 = d.caja("2 · + fine-tuning on the voices\n\nASR: 476 clips, 12 epochs, 9.3 min\n2.2 M of 965 M params (0.2 %)\nTTS: 50 epochs, ~20 min · on the A10G",
            CAJA.format(b="#1F6FD0") + "strokeWidth=3;", 600, 394, 250, 70)
d.flecha(p0, p1); d.flecha(p1, p2)

d.caja("4 · Each thing is measured against its own ground truth",
       TXT.format(s=13, c="#16160F", f=1), 40, 494, 700, 20)
d.caja("Until Oct 24 the audit had none: it only compared against Freddy's, which proves nothing if both are wrong the same way.",
       TXT.format(s=11, c="#4E4D45", f=0), 40, 514, 1000, 18)

m1 = d.caja("medir_asr.py — understanding\n\nTruth: the text corrected in /corregir\nWER and CER · speaker-held-out\nScored apart: loanwords and numbers",
            CAJA.format(b="#1F6FD0"), 40, 542, 300, 100, icono="medir")
m2 = d.caja("medir_traduccion.py — translation\n\nTruth: 62 pairs the families wrote on hackathon day\nchrF++, not BLEU: Quechua is agglutinative\nSonnet 5 44.6 · NLLB-1.3B 34.7 · 600M 28.6",
            CAJA.format(b="#C8372F"), 370, 542, 320, 100, icono="medir")
m3 = d.caja("medir_guarda.py — catching errors\n\nTruth: a clinical error is injected on purpose\nChanged dose · dropped negation · condition\n183/184 caught · 100 % of the critical ones",
            CAJA.format(b="#8A4FBD") + "strokeWidth=3;", 720, 542, 330, 100, icono="guarda")
m4 = d.caja("medir_auditoria.py — stability\n\nSame sentence, several runs\nBlocked · stability · median\nThe 4-call variant gives: yes, no, yes",
            CAJA.format(b="#8C8C7A"), 1080, 542, 300, 100, icono="medir")

rep = d.caja("reports/*.json\n\nasr · lid · translation · guard · audit\nOne file per number",
             CAJA.format(b="#8C8C7A"), 370, 676, 320, 76, icono="disco")
pit = d.caja("The page and the pitch\n\nRead those JSON files and nothing else.\nA bad number is shown anyway.",
             CAJA.format(b="#C8372F"), 720, 676, 330, 76)
for m in (m1, m2, m3, m4):
    d.flecha(m, rep, "", "strokeColor=#C8C5B8;")
d.flecha(rep, pit)

d.caja("What we fine-tune, and what we leave alone\n\nTwo Meta models are fine-tuned: MMS-1B-all (understanding Chanka) and mms-tts-quy (speaking it).\n"
       "mms-lid is used as shipped. Cartesia and Claude are not fine-tuned at all.\n\n"
       "They are two different jobs: understanding wants MANY voices; speaking wants ONE consistent voice,\n"
       "Freddy\u2019s mother. That is why everyone records, but Chaski speaks with a single person\u2019s voice.",
       "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C4C2B6;align=left;"
       "verticalAlign=top;spacingLeft=12;spacingTop=8;fontSize=11;fontColor=#4E4D45;",
       40, 786, 1340, 104)
d.guardar("reports/drawio/arquitectura-datos.drawio", 1500, 950)


# ---------------------------------------------------------------- flujo
f = Lienzo("Flow")
f.caja("One turn of a consultation, microphone to speaker",
       TXT.format(s=19, c="#16160F", f=1), 40, 20, 700, 28)
f.caja("Times measured 24-Oct-2026 on the A10G. Blue: Meta, on our GPU, fine-tuned by us. Green: Cartesia. Red: Claude.",
       TXT.format(s=12, c="#4E4D45", f=0), 40, 48, 950, 20)

mic = f.caja("Microphone\n\niPhone or browser\n16 kHz mono", CAJA.format(b="#8C8C7A"), 40, 170, 170, 76, icono="micro")
lid = f.caja("mms-lid-512\n\nQuechua or Spanish?\n49 ms · used as shipped\nOnly 3/6 on real family voice:\nwe never trust it alone",
             CAJA.format(b="#1F6FD0"), 250, 160, 210, 96, icono="gpu")
f.flecha(mic, lid)

stt_es = f.caja("Cartesia ink-whisper\n\nUnderstands Spanish\nCartesia cloud",
                CAJA.format(b="#1B9476"), 510, 90, 210, 76, icono="cartesia")
stt_qu = f.caja("MMS-1B-all + our adapter\n\nUnderstands Chanka Quechua\nWER 53.9 % → 40.9 % on a speaker\nthe model never heard\nTHE CORE: this is what we fine-tune",
                CAJA.format(b="#1F6FD0") + "strokeWidth=3;", 510, 250, 210, 96, icono="gpu")
f.flecha(lid, stt_es, "Spanish", "strokeColor=#1B9476;fontColor=#1B9476;")
f.flecha(lid, stt_qu, "Quechua", "strokeColor=#1F6FD0;fontColor=#1F6FD0;")

cla = f.caja("Claude\n\nTranslates and audits\nOpus 5 decides · Sonnet 5 translates and criticises\nThe slowest step, and on purpose\nGlossary cached in the system prompt",
             CAJA.format(b="#C8372F"), 770, 160, 240, 116, icono="claude")
f.flecha(stt_es, cla); f.flecha(stt_qu, cla)

aud = f.caja("The guard\n\nBlind back-translation, then facts compared in code\nIf a dose moved, nothing is spoken\n183/184 seeded errors caught, 2.6 s",
             CAJA.format(b="#8A4FBD") + "strokeWidth=3;", 770, 320, 240, 110, icono="guarda")
f.flecha(cla, aud)

tts_es = f.caja("Cartesia Sonic 3.6\n\nSpeaks Spanish · streaming",
                CAJA.format(b="#1B9476"), 1070, 120, 220, 70, icono="cartesia")
tts_qu = f.caja("mms-tts-quy + our fine-tune\n\nSpeaks Chanka\nTrained on Freddy’s mother’s voice,\nwith her permission",
                CAJA.format(b="#1F6FD0") + "strokeWidth=3;", 1070, 230, 220, 90, icono="gpu")
f.flecha(aud, tts_es, "to the nurse", "strokeColor=#1B9476;fontColor=#1B9476;")
f.flecha(aud, tts_qu, "to the patient", "strokeColor=#1F6FD0;fontColor=#1F6FD0;")

par = f.caja("Speaker\n\nText first, audio after:\nit can be read before it finishes speaking",
             CAJA.format(b="#8C8C7A"), 1340, 170, 210, 90, icono="parlante")
f.flecha(tts_es, par); f.flecha(tts_qu, par)

f.caja("Why Cartesia cannot cover the Quechua side\n\n"
       "Checked in their docs on 24-Oct: Sonic 3.6 speaks 44 languages and Quechua is not one of them.\n"
       "Their STT takes a `language` parameter in ISO-639-1, defaults to `en`, and does not detect language itself.\n"
       "So Quechua and the detection are ours out of necessity, not preference.\n\n"
       "And those 49 ms of detection shape the architecture: being that cheap, we detect first and recognise\n"
       "second, in series. No need to run both recognisers in parallel or guess from the previous turn.",
       "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C4C2B6;align=left;"
       "verticalAlign=top;spacingLeft=12;spacingTop=8;fontSize=11;fontColor=#4E4D45;",
       40, 480, 1250, 124)
f.guardar("reports/drawio/arquitectura-flujo.drawio", 1650, 680)


# ---------------------------------------------------------------- despliegue
g = Lienzo("Deployment")
g.caja("Chaski — where each piece runs",
       TXT.format(s=19, c="#16160F", f=1), 40, 20, 620, 28)
g.caja("Deployment architecture · 24-Oct-2026 18:00 UTC · no laptop in the chain any more",
       TXT.format(s=12, c="#4E4D45", f=0), 40, 48, 950, 20)

app = g.caja("Chaski app (Freddy)\n\niOS · calls the public URL\nNothing changed on its side",
             CAJA.format(b="#8C8C7A"), 40, 110, 200, 84, icono="chaski")
nav = g.caja("Browser\n\nGET /flujo · demo and testing",
             CAJA.format(b="#8C8C7A"), 40, 214, 200, 64, icono="navegador")
g.caja("Labelling UI /corregir\n\nStill on the laptop: reads local audio.\nOpens its own SSH tunnel.",
       CAJA.format(b="#8C8C7A") + "dashed=1;", 40, 298, 200, 84, icono="etiqueta")

ng = g.caja("ngrok · HTTPS edge\n\nunsubmitted-wally-relatable\n.ngrok-free.dev\n\n"
            "Reserved domain: survives\nevery restart",
            CAJA.format(b="#5A5A52"), 290, 110, 210, 140, icono="ngrok")
g.flecha(app, ng); g.flecha(nav, ng)

g.caja("EC2 g5.xlarge · 44.220.107.99 · NVIDIA A10G 23 GB",
       "rounded=0;html=1;fillColor=#FAF9F5;strokeColor=#8A4FBD;strokeWidth=2;dashed=1;dashPattern=8 4;"
       "verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;fontSize=12;fontStyle=1;fontColor=#8A4FBD;",
       550, 92, 450, 560)
g.caja("", "rounded=0;html=1;fillColor=none;strokeColor=none;", 930, 100, 40, 40,
       icono="ec2")

g.caja("ngrok agent\n\nRuns in here, not on the laptop",
       CAJA.format(b="#5A5A52"), 578, 150, 320, 56, icono="ngrok")
orq = g.caja("Orchestrator · port 8080\n\nservicio/app.py · FastAPI\n"
             "/turno/paciente · /turno/enfermera · /ver · /escuchar\n"
             "own venv: fastapi · anthropic · httpx\n\n"
             "venv kept SEPARATE from the models, on purpose",
             CAJA.format(b="#8A4FBD"), 578, 228, 394, 130, icono="servidor")
voz = g.caja("Speech service · port 8000\n\ninstancia.py · the Meta models, on the GPU\n"
             "MMS-1B-all + adapter · mms-lid-512 · mms-tts-quy\n"
             "torch==2.8.0 · fairseq2 · numpy~=1.23 — pinned\n"
             "One pip install on top breaks it. It happened once.\n"
             "LID 49 ms · ASR 1.71 s for 15.8 s · peak 3.41 GB of 23",
             CAJA.format(b="#1F6FD0"), 578, 404, 394, 136, icono="gpu")
g.flecha(ng, orq)
g.flecha(orq, voz, "127.0.0.1\nnever leaves the box",
         "strokeColor=#8A4FBD;strokeWidth=3;fontColor=#8A4FBD;fontStyle=1;")

CIL = ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;"
       "fillColor=#FFFFFF;strokeColor={b};strokeWidth=2;fontSize=10;fontColor=#4E4D45;align=center;")
g.caja("/ · 145 GB\n90 % full\nPut nothing here\nSurvives a stop",
       CIL.format(b="#C8372F"), 578, 556, 180, 86)
g.caja("/opt/dlami/nvme\n229 GB · 9 %\nEverything lives here\nEPHEMERAL: wiped on stop",
       CIL.format(b="#1B9476"), 792, 556, 180, 86)

ant = g.caja("Anthropic API\n\ndecide · translate · criticise · read boxes\nopus-5 · sonnet-5 · haiku-4-5\n\n"
             "The slowest step of a turn, and the one we refuse to cut",
             CAJA.format(b="#C8372F"), 1050, 228, 220, 130, icono="claude")
car = g.caja("Cartesia API\n\nSonic 3.6 · speaks Spanish\nink-whisper · understands it\n\n"
             "No Quechua: that is why Quechua is ours",
             CAJA.format(b="#1B9476"), 1050, 404, 220, 136, icono="cartesia")
g.flecha(orq, ant, "", "strokeColor=#C8C5B8;dashed=1;")
g.flecha(orq, car, "", "strokeColor=#C8C5B8;dashed=1;")

g.caja("What changed\n\nBefore: app \u2192 ngrok \u2192 a laptop \u2192 SSH tunnel \u2192\n"
       "instance, and all the way back again.\nClosing the laptop took it down.\n\n"
       "Now the patient\u2019s audio never leaves the instance.\n"
       "Same URL, so the app did not change a line.\n\n"
       "Deployed with `bash servicio/desplegar.sh`, re-runnable.\n"
       "Keys go over stdin into .env, chmod 600; never through git.",
       "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#8A4FBD;strokeWidth=2;align=left;"
       "verticalAlign=top;spacingLeft=12;spacingTop=8;fontSize=11;fontColor=#4E4D45;",
       40, 412, 470, 112)
g.guardar("reports/drawio/arquitectura-despliegue.drawio", 1500, 700)


# ---------------------------------------------------------------- revisión
def revisar(diagramas):
    """Avisa si una caja se sale de la página o pisa a otra.

    El .svg no tiene a nadie que acomode las cajas: lo que diga el modelo es lo
    que sale. Esta pasada evita publicar un diagrama con dos cajas encimadas,
    que es justo lo que pasó al crecer un recuadro de nota.
    """
    def solapan(a, b):
        return not (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]
                    or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"])

    problemas = 0
    for nombre, lienzo, (ancho, alto) in diagramas:
        # El contenedor de la instancia envuelve a los demás a propósito.
        cajas = [n for n in lienzo.nodos
                 if "text" not in n["d"] and not n["d"].get("shape") and n["w"] < 440]
        for i, a in enumerate(cajas):
            for b in cajas[i + 1:]:
                if solapan(a, b):
                    problemas += 1
                    print(f"  {nombre}: se pisan {a['valor'].splitlines()[0][:34]!r} "
                          f"y {b['valor'].splitlines()[0][:34]!r}")
        for n in lienzo.nodos:
            if n["x"] + n["w"] > ancho or n["y"] + n["h"] > alto:
                problemas += 1
                print(f"  {nombre}: se sale de la página {n['valor'].splitlines()[0][:34]!r}")
    print("revisión: todo en su sitio" if not problemas else f"revisión: {problemas} problemas")


revisar([("despliegue", g, (1500, 700)), ("datos", d, (1500, 950)), ("flujo", f, (1650, 680))])
