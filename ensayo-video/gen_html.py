"""Writes index.html for the Chaski demo rehearsal video from data.js (run build.py first).

Every timed element gets static data-start / data-duration so HyperFrames sees its window (gotcha 6).
The GSAP timeline lives in comp.js and reads window.DATA.
"""
import json, html
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data.js").read_text().split("=", 1)[1].rstrip().rstrip(";"))
EV, PAGES, CAPS = DATA["ev"], {p["id"]: p for p in DATA["pages"]}, DATA["caps"]
TOTAL = EV["TOTAL"]
BLUR = """data-hf-motion-blur='{"shutterAngle":360,"samplesPerFrame":8}'"""
E = html.escape

# ── direction cards per page: (time, kind, tag, body). kind: do | say | warn | file ─────────────────
CARDS = {
    "b1": [(EV["T0"] + 0.3, "do", "QUÉ HACES", "Dale play al video de tu mamá en la laptop. No hables encima de ella."),
           (EV["T0"] + 5.0, "do", "DÓNDE", "Laptop girada hacia el juez, parlante encendido. Sus subtítulos en inglés ya van quemados."),
           (EV["T0"] + 10.0, "file", "ARCHIVO", "data/mama/video/clips/PITCH-B1_problema-profesionales-costa_16s.mp4 · respaldo: el audio de 14 s")],
    "b1b": [(EV["s01"] + 0.2, "do", "QUÉ HACES", "Mira al juez. Nada en pantalla: la laptop ya no importa."),
            (EV["w_one5"], "warn", "NUNCA DIGAS", "«la única enfermera que habla quechua». Son 3 de 6.")],
    "b2": [(EV["s02"] + 0.2, "do", "QUÉ HACES", "Sigue mirando al juez. El celular ya está en el soporte, con Chaski abierto en Consulta."),
           (EV["w_gest"], "file", "DE DÓNDE SALE", "Todo es de la entrevista a tu mamá: el turno, el chofer, las señas, la pastilla partida en cuatro.")],
    "b2b": [(EV["s03"] - 0.2, "do", "QUÉ HACES", "Háblale al celular, en castellano, claro y sin apuro."),
            (EV["think"] + 0.2, "do", "MIENTRAS PIENSA · ~8 s", "Vuelve a mirar al juez y sigue con el problema. Los pasos se ven solos en la pantalla."),
            (EV["think"] + 4.0, "say", "SI TODAVÍA PIENSA CUANDO TERMINAS", "«While we talk, it's checking itself. You can see each step.»"),
            (EV["think_end"] + 0.3, "do", "CUANDO TERMINA", "Termina tu frase y deja que Chaski hable. No lo interrumpas.")],
    "b3": [(PAGES["b3"]["start"] + 0.3, "do", "QUÉ HACES", "Señala el sello «Revisado por el crítico» en la pantalla."),
           (EV["w_back"], "file", "ES VERDAD PORQUE", "La retraducción a ciegas corre en cada turno traducido: chaski/critico.py + hechos.py.")],
    "b3b": [(EV["pac"] - 0.2, "do", "RICARDO", "Pone el audio de la familia junto al micrófono del celular."),
            (EV["pac_es"], "do", "TÚ", "Lee en voz alta el castellano que sale en la pantalla."),
            (EV["pac_es"] + 2.5, "warn", "SI FALLA", "Repite el audio una vez. Si vuelve a fallar, sigue: nunca lo arregles en vivo.")],
    "b3c": [(EV["tap1"] - 0.3, "do", "QUÉ HACES", "Dos toques: Emergencia → ¿Dónde le duele?"),
            (EV["q_em"] + 0.3, "file", "POR QUÉ ES AL INSTANTE", "Ya está traducida, la revisó tu mamá y está grabada. No llama a ningún modelo.")],
    "b4": [(PAGES["b4"]["start"] + 0.3, "warn", "ANTES DE LA MESA", "Prende el modo ensayo en Ajustes. Sin eso no hay atajo."),
           (EV["s08"] + 0.2, "do", "QUÉ HACES", "Toca el atajo de ensayo y DI que es un error simulado."),
           (EV["red"], "do", "EN ROJO", "Deja el rojo en pantalla. Un segundo de silencio. Después hablas.")],
    "b5": [(EV["s10"] - 0.3, "do", "RICARDO", "Una sola lámina en la laptop, con los dos números."),
           (EV["w_184"], "warn", "NUNCA DIGAS", "«under three seconds» ni el 31,7 de NLLB. Es «about three seconds».")],
    "b6": [(EV["s11"] + 0.2, "do", "QUÉ HACES", "Muestra el resumen de ESTA consulta, no el de ejemplo."),
           (EV["w_next"] - 1.5, "say", "LA ÚLTIMA FRASE", "«Next, it goes to my mother's health center.» Si ella ya dijo que sí: «Monday».")],
    "end": [(PAGES["end"]["start"] + 0.6, "do", "DESPUÉS · 2:00 DE PREGUNTAS", "Respuestas de un respiro, en plan/qa-jueces.md."),
            (PAGES["end"]["start"] + 1.6, "do", "ANTES DE CADA JUEZ", "Un turno de calentamiento · hotspot del celular · parlante · modo ensayo prendido."),
            (PAGES["end"]["start"] + 2.6, "warn", f"ESTE ENSAYO DURÓ {int(DATA['pitch_len'] // 60)}:{int(DATA['pitch_len'] % 60):02d}",
             "Recorta unos 6 s: acorta la pausa antes de que Chaski hable en B3, o una frase de B5.")],
}

def win(a, b):
    return f'data-start="{a:.3f}" data-duration="{max(0.05, b - a):.3f}"'

def card_html(pid, i, c):
    t0, kind, tag, body = c
    p = PAGES[pid]
    return (f'<div class="card clip k-{kind}" id="c-{pid}-{i}" data-at="{t0:.3f}" {win(p["start"], p["end"])} {BLUR}>'
            f'<div class="ctag">{E(tag)}</div><div class="cbody">{E(body)}</div></div>')

# ── phone building blocks ─────────────────────────────────────────────────────────────────────────
def phone(pid, inner, avatar="reposo"):
    return f'''<div class="phone" id="ph-{pid}"><div class="screen">
  <div class="ptop"><span class="ptitle">Consulta</span><span class="plang">castellano ⇄ quechua</span></div>
  <div class="ava" id="ava-{pid}">{''.join(f'<img class="st st-{s}" src="assets/img/{s}.png">' for s in ["reposo","pensando","hablando","escuchando","no_entendi"])}</div>
  <div class="msgs">{inner}</div>
  <div class="mic"><i class="r1"></i><i class="r2"></i><i class="r3"></i><i class="r4"></i><b></b></div>
</div><div class="notch"></div></div>'''

def steps(pid, labels):
    return '<div class="steps" id="steps-' + pid + '">' + "".join(
        f'<div class="step" id="st-{pid}-{i}"><i></i><span>{E(l)}</span></div>' for i, l in enumerate(labels)) + "</div>"

QB3 = "Sapa pusaq horasmanta huk pastillata upyay, mikusqaykimanta qhipaman. Ama tewan upyaychu."
def words_html(txt, cls):
    return "".join(f'<span class="{cls}">{E(w)}</span> ' for w in txt.split())

PH = {
    "b2b": phone("b2b",
        '<div class="bub es" id="m-es"><span class="tagl">CASTELLANO</span><div class="btxt">' +
        words_html("Tome una pastilla cada ocho horas, después de comer. No la tome con té.", "ew") + '</div></div>' +
        steps("b2b", ["Entendiendo lo que dijo", "Traduciendo al quechua", "Revisando que nada cambió"]) +
        '<div class="bub qu" id="m-qu"><span class="tagl">QUECHUA</span><div class="btxt">' + words_html(QB3, "qw") +
        '</div><div class="chip ok" id="m-ok">✓ Revisado por el crítico</div></div>'
        '<div class="mock">maqueta · en vivo sale el quechua real</div>'),
    "b3b": phone("b3b",
        '<div class="bub qu" id="p-qu"><span class="tagl">PACIENTE · QUECHUA</span><div class="btxt">Umaymi nanachkan qayna punchawmanta.</div>'
        '<div class="wave" id="p-wave">' + "".join(f'<i style="--h:{h}"></i>' for h in [8, 18, 30, 22, 36, 14, 26, 40, 20, 12, 28, 34, 16, 24, 10, 30, 18, 8]) + '</div></div>' +
        steps("b3b", ["Entendiendo en quechua", "Pasándolo al castellano", "Revisando que nada cambió"]) +
        '<div class="bub es" id="p-es"><span class="tagl">CASTELLANO</span><div class="btxt big">Me duele la cabeza desde ayer.</div></div>'
        '<div class="mock">audio real de la familia (p18)</div>', "escuchando"),
    "b3c": phone("b3c",
        '<div class="ebtn" id="e-btn">Emergencia</div>'
        '<div class="egrid" id="e-grid">' + "".join(f'<div class="eg{" sel" if i == 0 else ""}" id="eg-{i}">{E(x)}</div>' for i, x in enumerate(
            ["¿Dónde le duele?", "¿Desde cuándo?", "¿Tiene fiebre?", "¿Está embarazada?", "¿Vino con alguien?", "No se preocupe"])) + '</div>'
        '<div class="ecard" id="e-card"><div class="eq">¿Mayta nanan?</div><div class="ees">¿Dónde le duele?</div>'
        '<div class="chip ok">✓ Revisada · suena sin esperar</div></div>'),
    "b4": phone("b4",
        '<div class="bub es" id="r-es"><span class="tagl">CASTELLANO</span><div class="btxt">Tómela con agua, no con té.</div></div>'
        '<div class="banner" id="r-ban">Ensayo: simulamos que el traductor se equivocó</div>'
        '<div class="redc" id="r-red"><div class="rt">Chaski no lo dijo</div><div class="rr">Cambió un dato crítico: prohibiciones</div>'
        '<div class="rrow"><span>Debía decir</span><b>Yakuwan upyay, <u>ama</u> tewan upyay<u>chu</u>.</b></div>'
        '<div class="rrow bad"><span>Iba a decir</span><b>Yakuwan upyay, tewan upyay.</b></div></div>', "reposo"),
    "b6": phone("b6",
        '<div class="sum" id="s-1"><div class="sh">Para la historia clínica</div><div class="sb">1 pastilla cada 8 h, después de comer; no tomarla con té. Paciente: le duele la cabeza desde ayer.</div></div>'
        '<div class="sum" id="s-2"><div class="sh">Para llevar a casa</div><div class="sb qtxt">Sapa pusaq horasmanta huk pastillata upyay…</div></div>'
        '<div class="sum" id="s-3"><div class="sh">Palabras nuevas</div><div class="gl"><span>upyay · tomar</span><span>pusaq · ocho</span><span>nanan · duele</span></div></div>'
        '<div class="mock">maqueta · en vivo, el de ESTA consulta</div>'),
}

# ── stage content per page ───────────────────────────────────────────────────────────────────────
def stage(pid):
    p = PAGES[pid]
    if pid == "intro":
        return ('<img class="hero" id="i-ava" src="assets/img/presentarse.png">'
                '<div class="ttl" id="i-t1">El demo,</div><div class="ttl" id="i-t2">beat por beat</div>'
                '<div class="leg" id="i-l1"><i class="lg-v"></i>La voz es lo que <b>dices</b></div>'
                '<div class="leg" id="i-l2"><i class="lg-c"></i>Las tarjetas son lo que <b>haces</b></div>'
                '<div class="leg" id="i-l3"><i class="lg-t"></i>El reloj es el tiempo <b>real</b> del pitch</div>')
    if pid == "b1":
        return ('<div class="laptop" id="lap"><div class="lscreen"></div><div class="lbase"></div></div>'
                '<div class="who" id="mama-name">Lic. Norma Choque Guerreros · enfermera, Pilpichaca</div>')
    if pid == "b1b":
        return ('<div class="stat" id="st1" ' + BLUR + '><div class="big">9 <small>de</small> 10</div><div class="lab">pacientes hablan quechua</div></div>'
                '<div class="stat dim" id="st2" ' + BLUR + '><div class="big">1 <small>de</small> 5</div><div class="lab">del personal lo habla</div></div>'
                '<div class="src" id="st-src">Entrevista a la enfermera, 24-oct · posta de Pilpichaca</div>')
    if pid == "b2":
        return ('<div class="pill" id="pl1" ' + BLUR + '>Otra enfermera</div><div class="pill" id="pl2" ' + BLUR + '>Un técnico</div>'
                '<div class="pill" id="pl3" ' + BLUR + '>El chofer de la ambulancia</div><div class="pill acc" id="pl4" ' + BLUR + '>Si no hay nadie: señas</div>'
                '<svg id="pq" viewBox="0 0 200 200"><g id="pq-g">'
                '<path class="q" d="M100 100 L100 20 A80 80 0 0 1 180 100 Z"/><path class="q" d="M100 100 L180 100 A80 80 0 0 1 100 180 Z"/>'
                '<path class="q" d="M100 100 L100 180 A80 80 0 0 1 20 100 Z"/><path class="q" d="M100 100 L20 100 A80 80 0 0 1 100 20 Z"/></g></svg>'
                '<div class="pqlab" id="pq-lab">la pastilla, partida en cuatro</div>')
    if pid in PH:
        return PH[pid]
    if pid == "b3":
        lab = ["1 · Lo limpia", "2 · Lo traduce", "3 · Lo retraduce a ciegas", "4 · El código compara los datos", "5 · Recién habla"]
        held = phone("b3",
            '<div class="bub es on" id="h-es"><span class="tagl">CASTELLANO</span><div class="btxt">Tome una pastilla cada ocho horas, después de comer. No la tome con té.</div></div>'
            '<div class="bub qu on" id="h-qu"><span class="tagl">QUECHUA</span><div class="btxt">' + E(QB3) + '</div>'
            '<div class="chip ok on" id="h-ok">✓ Revisado por el crítico</div></div>'
            '<div class="mock">maqueta · en vivo sale el quechua real</div>')
        return held + "".join(f'<div class="pill chain{" acc" if i == 4 else ""}" id="ch{i}" {BLUR}>{E(x)}</div>' for i, x in enumerate(lab))
    if pid == "b5":
        return ('<div class="slide" id="sl"><div class="sl-h">Lo que medimos</div>'
                '<div class="sl-n" id="sl1"><div class="big">54% → 41%</div><div class="lab">errores por palabra, en una voz que el modelo nunca oyó</div></div>'
                '<div class="sl-p" id="sl2">Opus decide · Sonnet revisa</div>'
                '<div class="sl-n" id="sl3"><div class="big">183 / 184</div><div class="lab">errores sembrados atrapados · 100 % de los críticos · ~3 s</div></div></div>')
    if pid == "end":
        return ('<img class="hero small" id="e-ava" src="assets/img/reposo.png"><div class="ttl" id="e-t1">Chaski</div>'
                '<div class="leg" id="e-l1"><i class="lg-t"></i>Entrega en Devpost: domingo 9:00</div>'
                '<div class="leg" id="e-l2"><i class="lg-c"></i>Jurado: 10:30 a 12:30, los dos en la mesa</div>')
    return ""

pages_html = []
for p in DATA["pages"]:
    pid = p["id"]
    cards = "".join(card_html(pid, i, c) for i, c in enumerate(CARDS.get(pid, [])))
    pages_html.append(f'<div class="page clip {"dark" if p["dark"] else "light"}" id="pg-{pid}" {win(p["start"], p["end"])}>'
                      f'<div class="stage">{stage(pid)}</div><div class="col">{cards}</div></div>')

caps_html = "".join(
    f'<div class="cap clip" id="cap{i}" {win(c["t0"] - 0.05, c["out"])}>' +
    (f'<span class="cwho">{E(c["who"])}</span>' if c["who"] else "") +
    "".join(f'<span class="w" data-t="{w["t"]:.3f}">{E(w["w"])}</span>' for w in c["words"]) + "</div>"
    for i, c in enumerate(CAPS))

hud_labels = "".join(
    f'<div class="blab clip" {win(p["start"], p["end"])}>{E(p["label"])}' +
    (f'<span class="whochip">{E(p["who"])}</span>' if p["who"] else "") + "</div>" for p in DATA["pages"] if p["id"] != "intro")

page = f'''<!doctype html>
<html lang="es"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1920, height=1080" />
<title>Chaski — ensayo del demo</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="cues.js"></script><script src="data.js"></script><script src="lib/engine.js"></script>
<link rel="stylesheet" href="comp.css" />
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-width="1920" data-height="1080" data-duration="{TOTAL:.3f}" data-fps="30">
  <div id="field" class="full"></div><div id="glow" class="full"></div>
  {''.join(pages_html)}
  <video id="mama" class="clip" src="assets/video/mama-b1.mp4" muted playsinline {win(EV["T0"], EV["T0"] + 16.0)}></video>
  {"".join(f'<div class="msub clip" id="msub{i}" {win(s["t0"], s["t1"] + 0.3)}>{E(s["text"])}</div>' for i, s in enumerate(DATA["mama"]))}
  <div id="hud"><div id="brand">CHASKI · ENSAYO DEL DEMO</div><div id="blabs">{hud_labels}</div>
    <div id="clock"><span id="clk">0:00</span><small>/ 3:00</small></div><div id="bar"><i id="barfill"></i><b id="bar3"></b></div></div>
  <div id="caps">{caps_html}</div>
  <audio id="score" src="assets/audio/mix.wav" data-start="0" data-duration="{TOTAL:.3f}"></audio>
</div>
<script>\n{(ROOT / "comp.js").read_text()}\n</script>
<script src="lib/motion-blur.js"></script>
</body></html>
'''
(ROOT / "index.html").write_text(page)
print("index.html", len(page), "bytes ·", sum(len(v) for v in CARDS.values()), "cards ·", len(CAPS), "captions")
