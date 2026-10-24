# -*- coding: utf-8 -*-
"""Genera los tres .drawio de arquitectura: despliegue, datos y flujo de un turno.

Se corre desde la raíz de ricardo-artifacts:

    python reports/drawio/generar.py

Se escriben sin comprimir a propósito: así el XML se lee en el diff de git y no
hay que abrir draw.io para revisar un cambio.
"""
from pathlib import Path
from xml.sax.saxutils import escape

FONDO = "#F4F3EE"
CAJA = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={b};strokeWidth=2;"
        "align=left;verticalAlign=top;spacingLeft=10;spacingTop=6;fontSize=11;fontColor=#4E4D45;")
TXT = "text;html=1;align=left;verticalAlign=middle;fontSize={s};fontColor={c};fontStyle={f};"


class Lienzo:
    def __init__(self, nombre):
        self.nombre, self.celdas, self.n = nombre, [], 1

    def _html(self, valor):
        lineas = valor.split("\n")
        if len(lineas) > 1 and lineas[0]:
            lineas[0] = f"<b>{lineas[0]}</b>"
        return escape("<br>".join(lineas))

    def caja(self, valor, estilo, x, y, w, h):
        self.n += 1
        i = f"n{self.n}"
        self.celdas.append(
            f'<mxCell id="{i}" value="{self._html(valor)}" style="{estilo}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return i

    def flecha(self, a, b, etiqueta="", estilo=""):
        self.n += 1
        base = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=blockThin;endFill=1;"
                "strokeColor=#8C8C7A;strokeWidth=2;fontSize=11;fontColor=#4E4D45;" + estilo)
        self.celdas.append(
            f'<mxCell id="e{self.n}" value="{escape(etiqueta.replace(chr(10), "<br>"))}" '
            f'style="{base}" edge="1" parent="1" source="{a}" target="{b}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>')

    def guardar(self, ruta, ancho=1700, alto=1000):
        xml = (f'<mxfile host="app.diagrams.net" type="device">\n'
               f'  <diagram id="{self.nombre}" name="{self.nombre}">\n'
               f'    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" '
               f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{ancho}" '
               f'pageHeight="{alto}" math="0" shadow="0" background="{FONDO}">\n'
               f'      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n        '
               + "\n        ".join(self.celdas) +
               '\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n')
        Path(ruta).write_text(xml, encoding="utf-8")
        print("escrito", ruta)


# ---------------------------------------------------------------- datos
d = Lienzo("Datos")
d.caja("De la voz de la familia al número del pitch",
       TXT.format(s=19, c="#16160F", f=1), 40, 20, 700, 28)
d.caja("Arquitectura de datos. La regla que sostiene todo: la voz de prueba nunca entra al entrenamiento.",
       TXT.format(s=12, c="#4E4D45", f=0), 40, 48, 900, 20)

d.caja("1 · Recolección", TXT.format(s=13, c="#16160F", f=1), 40, 92, 300, 20)
cua = d.caja("Cuadernillos\n\n175 frases numeradas\nseis bloques: A B C M N E\nSe escribe primero, se graba después",
             CAJA.format(b="#8C8C7A"), 40, 118, 220, 96)
frm = d.caja("Formulario (Freddy)\n\nVercel · la familia sube audio\ny cómo se escribe\nNo lo tocamos desde aquí",
             CAJA.format(b="#1B9476"), 290, 118, 220, 96)
cor = d.caja("/corregir (Ricardo)\n\nTranscribe, yo corrijo el escrito\nParte y une si cortó mal\nVerifica audio contra texto",
             CAJA.format(b="#1F6FD0"), 540, 118, 230, 96)
man = d.caja("manifiesto.jsonl\n\npersona · bloque · numero\naudio · transcripcion · castellano\nsegundos · consentimiento",
             CAJA.format(b="#8C8C7A"), 800, 118, 240, 96)
d.flecha(cua, frm); d.flecha(frm, cor); d.flecha(cor, man)

d.caja("2 · Partición POR HABLANTE, nunca por frase",
       TXT.format(s=13, c="#16160F", f=1), 40, 240, 520, 20)
tr = d.caja("entrenamiento\n\n3 personas · ~22 min\nAjusta el modelo",
            CAJA.format(b="#1F6FD0"), 40, 266, 230, 76)
va = d.caja("validación\n\n12 % del entrenamiento\nElige hiperparámetros",
            CAJA.format(b="#8C8C7A"), 300, 266, 220, 76)
pr = d.caja("prueba · una persona entera\n\nVoz que el modelo NUNCA escuchó\nSe toca una sola vez, al final",
            CAJA.format(b="#C8372F") + "strokeWidth=3;", 550, 266, 300, 76)
d.flecha(man, tr)

d.caja("3 · Tres pasos, tres números — se reportan los tres salga lo que salga",
       TXT.format(s=13, c="#16160F", f=1), 40, 368, 700, 20)
p0 = d.caja("0 · El modelo tal cual\n\nLínea base. Sin tocar nada.",
            CAJA.format(b="#8C8C7A"), 40, 394, 250, 70)
p1 = d.caja("1 · + vocabulario de la posta\n\nGlosario y préstamos",
            CAJA.format(b="#1F6FD0"), 320, 394, 250, 70)
p2 = d.caja("2 · + ajuste fino con las voces\n\n~7 min en la A10G",
            CAJA.format(b="#1F6FD0") + "strokeWidth=3;", 600, 394, 250, 70)
d.flecha(p0, p1); d.flecha(p1, p2)

d.caja("4 · Cada cosa se mide contra una verdad distinta",
       TXT.format(s=13, c="#16160F", f=1), 40, 494, 700, 20)
d.caja("Hasta el 24-oct la auditoría no tenía ninguna: solo se comparaba con la de Freddy, y eso no prueba nada si las dos se equivocan igual.",
       TXT.format(s=11, c="#4E4D45", f=0), 40, 514, 1000, 18)

m1 = d.caja("medir_asr.py — entender\n\nVerdad: el escrito corregido en /corregir\nWER y CER · corte por hablante\nAparte: préstamos y números",
            CAJA.format(b="#1F6FD0"), 40, 542, 300, 100)
m2 = d.caja("medir_traduccion.py — traducir\n\nVerdad: 100 pares verificados, fuera del train\nchrF++, no BLEU: el quechua aglutina\nBase sin ajustar: chrF++ 42.31",
            CAJA.format(b="#C8372F"), 370, 542, 320, 100)
m3 = d.caja("medir_guarda.py — no dejar pasar errores\n\nVerdad: se inyecta un error clínico a propósito\nDosis cambiada · negación borrada · condición\n0/6 falsos bloqueos · 3/6 FUGAS",
            CAJA.format(b="#8A4FBD") + "strokeWidth=3;", 720, 542, 330, 100)
m4 = d.caja("medir_auditoria.py — estabilidad\n\nLa misma frase, varias corridas\nBloqueo · estabilidad · mediana\nLa de 4 llamadas da: sí, no, sí",
            CAJA.format(b="#8C8C7A"), 1080, 542, 300, 100)

rep = d.caja("reports/*.json\n\nasr · lid · traduccion · guarda · auditoria\nUn archivo por número",
             CAJA.format(b="#8C8C7A"), 370, 676, 320, 76)
pit = d.caja("La página y el pitch\n\nLeen esos JSON y nada más.\nSi un número sale malo, se muestra igual.",
             CAJA.format(b="#C8372F"), 720, 676, 330, 76)
for m in (m1, m2, m3, m4):
    d.flecha(m, rep, "", "strokeColor=#C8C5B8;")
d.flecha(rep, pit)

d.caja("Qué se ajusta y qué no\n\nSe ajustan los dos modelos de Meta: omniASR (entender chanka) y mms-tts-quy (hablar chanka).\n"
       "mms-lid ya acierta 6/6 y se deja quieto. Cartesia y Claude no se ajustan: se usan como vienen.\n\n"
       "Y son dos ajustes distintos: entender quiere MUCHAS voces; hablar quiere UNA sola voz consistente,\n"
       "la de la mamá de Freddy. Por eso todos graban, pero la voz de Chaski sale de una sola persona.",
       "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C4C2B6;align=left;"
       "verticalAlign=top;spacingLeft=12;spacingTop=8;fontSize=11;fontColor=#4E4D45;",
       40, 786, 1340, 104)
d.guardar("reports/drawio/arquitectura-datos.drawio", 1500, 950)


# ---------------------------------------------------------------- flujo
f = Lienzo("Flujo")
f.caja("Un turno de consulta, de micrófono a parlante",
       TXT.format(s=19, c="#16160F", f=1), 40, 20, 700, 28)
f.caja("Tiempos medidos el 24-oct-2026 en la A10G. Azul: Meta, en nuestra GPU, lo ajustamos. Verde: Cartesia. Rojo: Claude.",
       TXT.format(s=12, c="#4E4D45", f=0), 40, 48, 950, 20)

mic = f.caja("Micrófono\n\niPhone o navegador\n16 kHz mono", CAJA.format(b="#8C8C7A"), 40, 170, 170, 76)
lid = f.caja("mms-lid-512\n\n¿quechua o castellano?\n49 ms · 6/6 aciertos\nNo se ajusta: ya acierta",
             CAJA.format(b="#1F6FD0"), 250, 160, 210, 96)
f.flecha(mic, lid)

stt_es = f.caja("Cartesia ink-whisper\n\nEntiende castellano\nNube de Cartesia",
                CAJA.format(b="#1B9476"), 510, 90, 210, 76)
stt_qu = f.caja("omniASR_LLM_300M\n\nEntiende chanka\n1.71 s para 15.8 s de audio\nEL NÚCLEO: esto ajustamos",
                CAJA.format(b="#1F6FD0") + "strokeWidth=3;", 510, 250, 210, 96)
f.flecha(lid, stt_es, "castellano", "strokeColor=#1B9476;fontColor=#1B9476;")
f.flecha(lid, stt_qu, "quechua", "strokeColor=#1F6FD0;fontColor=#1F6FD0;")

cla = f.caja("Claude\n\nTraduce y audita\nsonnet-5 traduce · haiku-4-5 extrae hechos\n7–12 s: el cuello de botella\nGlosario cacheado en el system",
             CAJA.format(b="#C8372F"), 770, 160, 240, 116)
f.flecha(stt_es, cla); f.flecha(stt_qu, cla)

aud = f.caja("La guarda\n\nRetraduce a ciegas y compara los hechos\nSi cambió una dosis, no se dice\nMedido: 0/6 falsos bloqueos, 3/6 fugas",
             CAJA.format(b="#8A4FBD") + "strokeWidth=3;", 770, 320, 240, 110)
f.flecha(cla, aud)

tts_es = f.caja("Cartesia Sonic 3.6\n\nHabla castellano · streaming",
                CAJA.format(b="#1B9476"), 1070, 120, 220, 70)
tts_qu = f.caja("mms-tts-quy\n\nHabla chanka\nSe ajusta con la voz de la mamá de Freddy",
                CAJA.format(b="#1F6FD0") + "strokeWidth=3;", 1070, 230, 220, 90)
f.flecha(aud, tts_es, "a la enfermera", "strokeColor=#1B9476;fontColor=#1B9476;")
f.flecha(aud, tts_qu, "al paciente", "strokeColor=#1F6FD0;fontColor=#1F6FD0;")

par = f.caja("Parlante\n\nTexto primero, audio después:\nse lee antes de que termine de hablar",
             CAJA.format(b="#8C8C7A"), 1340, 170, 210, 90)
f.flecha(tts_es, par); f.flecha(tts_qu, par)

f.caja("Por qué Cartesia no puede hacer el lado quechua\n\n"
       "Verificado en su documentación el 24-oct: Sonic 3.6 habla 44 idiomas y el quechua no está entre ellos.\n"
       "Su STT acepta un parámetro `language` en ISO-639-1 con `en` por defecto, y no detecta el idioma solo.\n"
       "Así que el quechua y la detección son nuestros por necesidad, no por preferencia.\n\n"
       "Y esos 49 ms del detector deciden la arquitectura: siendo tan barato, se detecta primero y se reconoce\n"
       "después, en serie. No hace falta correr los dos reconocedores en paralelo ni adivinar por el turno anterior.",
       "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C4C2B6;align=left;"
       "verticalAlign=top;spacingLeft=12;spacingTop=8;fontSize=11;fontColor=#4E4D45;",
       40, 480, 1250, 124)
f.guardar("reports/drawio/arquitectura-flujo.drawio", 1650, 680)


# ---------------------------------------------------------------- despliegue
g = Lienzo("Despliegue")
g.caja("Chaski — dónde corre cada cosa",
       TXT.format(s=19, c="#16160F", f=1), 40, 20, 620, 28)
g.caja("Arquitectura de despliegue · 24-oct-2026 18:00 UTC · desde hoy la laptop de Ricardo ya no está en la cadena",
       TXT.format(s=12, c="#4E4D45", f=0), 40, 48, 950, 20)

app = g.caja("App de Chaski (Freddy)\n\niOS · consume la URL pública\nNo cambió nada el 24-oct",
             CAJA.format(b="#8C8C7A"), 40, 110, 200, 84)
nav = g.caja("Navegador\n\nGET /flujo · demo y pruebas",
             CAJA.format(b="#8C8C7A"), 40, 214, 200, 64)
g.caja("Etiquetador /corregir\n\nSigue en la laptop: lee audio local.\nAbre su propio túnel SSH.",
       CAJA.format(b="#8C8C7A") + "dashed=1;", 40, 298, 200, 84)

ng = g.caja("ngrok · borde HTTPS\n\nunsubmitted-wally-relatable\n.ngrok-free.dev\n\n"
            "Dominio reservado: no cambia\nentre reinicios",
            CAJA.format(b="#5A5A52"), 290, 110, 210, 140)
g.flecha(app, ng); g.flecha(nav, ng)

g.caja("Instancia EC2 g5.xlarge · 44.220.107.99 · NVIDIA A10G 23 GB",
       "rounded=0;html=1;fillColor=#FAF9F5;strokeColor=#8A4FBD;strokeWidth=2;dashed=1;dashPattern=8 4;"
       "verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;fontSize=12;fontStyle=1;fontColor=#8A4FBD;",
       550, 92, 450, 560)
g.caja("", "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=#F78E04;gradientDirection=north;"
       "fillColor=#D05C17;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;"
       "align=center;html=1;fontSize=10;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;",
       930, 100, 52, 52)

g.caja("Agente de ngrok\n\nCorre aquí dentro, no en la laptop",
       CAJA.format(b="#5A5A52"), 578, 150, 320, 56)
orq = g.caja("Orquestador · puerto 8080\n\nservicio/app.py · FastAPI\n"
             "/turno/paciente · /turno/enfermera · /ver · /escuchar\n"
             "venv propio: fastapi · anthropic · httpx\n\n"
             "venv SEPARADO del de los modelos, a propósito",
             CAJA.format(b="#8A4FBD"), 578, 228, 394, 130)
voz = g.caja("Servicio de voz · puerto 8000\n\ninstancia.py · los tres modelos de Meta en GPU\n"
             "omniASR_LLM_300M · mms-lid-512 · mms-tts-quy\n"
             "torch==2.8.0 · fairseq2 · numpy~=1.23 — clavados\n"
             "Un pip install encima lo rompe. Ya pasó una vez.\n"
             "LID 49 ms · ASR 1.71 s para 15.8 s · pico 3.41 GB de 23",
             CAJA.format(b="#1F6FD0"), 578, 404, 394, 136)
g.flecha(ng, orq)
g.flecha(orq, voz, "127.0.0.1\nno sale a internet",
         "strokeColor=#8A4FBD;strokeWidth=3;fontColor=#8A4FBD;fontStyle=1;")

CIL = ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;"
       "fillColor=#FFFFFF;strokeColor={b};strokeWidth=2;fontSize=10;fontColor=#4E4D45;align=center;")
g.caja("/ · 145 GB\n90 % lleno\nNo poner nada aquí\nPersiste al parar",
       CIL.format(b="#C8372F"), 578, 556, 180, 86)
g.caja("/opt/dlami/nvme\n229 GB · 9 %\nTodo vive aquí\nEFÍMERO: se borra al parar",
       CIL.format(b="#1B9476"), 792, 556, 180, 86)

ant = g.caja("API de Anthropic\n\ntraducir · auditar · leer cajas\nsonnet-5 · haiku-4-5\n\n"
             "7–12 s por turno: el cuello de botella real",
             CAJA.format(b="#C8372F"), 1050, 228, 220, 130)
car = g.caja("API de Cartesia\n\nSonic 3.6 · habla castellano\nink-whisper · lo entiende\n\n"
             "Sin quechua: por eso el quechua es nuestro",
             CAJA.format(b="#1B9476"), 1050, 404, 220, 136)
g.flecha(orq, ant, "", "strokeColor=#C8C5B8;dashed=1;")
g.flecha(orq, car, "", "strokeColor=#C8C5B8;dashed=1;")

g.caja("Lo que cambió hoy\n\nAntes: app → ngrok → laptop de Ricardo → túnel SSH →\n"
       "instancia, y todo de vuelta por el mismo camino.\nSi cerraba la laptop, se caía.\n\n"
       "Ahora el audio del paciente no sale de la instancia.\n"
       "La URL es la misma: Freddy no cambia una línea.\n\n"
       "Se despliega con `bash servicio/desplegar.sh`, re-ejecutable.\n"
       "Las claves viajan por stdin a .env con chmod 600; nunca por git.",
       "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#8A4FBD;strokeWidth=2;align=left;"
       "verticalAlign=top;spacingLeft=12;spacingTop=8;fontSize=11;fontColor=#4E4D45;",
       1050, 92, 300, 112)
g.guardar("reports/drawio/arquitectura-despliegue.drawio", 1500, 720)
