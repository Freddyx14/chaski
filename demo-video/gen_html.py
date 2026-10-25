"""index.html for the Chaski Devpost demo (run build.py first). Timeline in comp.js, styles in comp.css + demo.css."""
import json, html
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data.js").read_text().split("=", 1)[1].rstrip().rstrip(";"))
EV, PAGES, CAPS = DATA["ev"], {p["id"]: p for p in DATA["pages"]}, DATA["caps"]
TOTAL = EV["TOTAL"]
BLUR = """data-hf-motion-blur='{"shutterAngle":360,"samplesPerFrame":8}'"""
E = html.escape

# feature cards (right column): (time, kind, tag, body)
CARDS = {
    "hands": [(EV["w_hands"], "do", "HANDS-FREE", "No buttons. It hears who spoke and in which language."),
              (EV["w_lang"], "file", "UNDER THE HOOD", "Meta MMS language ID · Cartesia ink-whisper for Spanish · fine-tuned Quechua recognizer")],
    "instr": [(EV["v03"], "do", "A HEALTH WORKER SPEAKS", "Any of the staff: doctor, nurse, obstetrician, technician."),
              (EV["w_opus"], "do", "CLAUDE OPUS DECIDES", "Translate · ask back · answer · didn't understand · verified phrase"),
              (EV["w_checks"], "do", "CHECKED BEFORE IT SPEAKS", "Code compares dose, frequency, days, medicine, negation. Claude Sonnet back-translates blind.")],
    "pat": [(EV["pac"], "file", "REAL AUDIO", "A family member, recorded this weekend through our voice form."),
            (EV["w_fine"], "do", "FINE-TUNED EARS", "Meta's Quechua recognizer, adapted on our families' voices.")],
    "ask": [(EV["w_asks"], "do", "ASKS BACK", "Once, in the speaker's language, when a critical fact is missing."),
            (EV["w_repeat"], "do", "NEVER GUESSES", "If a check fails, it asks the speaker to repeat.")],
    "moment": [(EV["v07"], "warn", "SIMULATED ERROR", "We inject a wrong translation on purpose to show the check."),
               (EV["w_catch"], "do", "IT NAMES THE FACT", "“Prohibitions changed”. Never “something went wrong”.")],
    "emg": [(EV["v08"], "do", "NO MODEL IN THE LOOP", "Pre-recorded, verified phrases. Instant."),
            (EV["w_mother8"], "file", "WRITTEN AND REVIEWED BY A NURSE", "24 phrases, in a voice trained on hers, with her permission.")],
    "rx": [(EV["w_photo"], "do", "CLAUDE READS THE BOX", "Medicine, strength, dose. If it's blurry, it asks instead of guessing."),
           (EV["w_yes"], "do", "A SPOKEN YES FIRST", "Nothing reaches the patient until the health worker confirms.")],
    "sum": [(EV["w_note"], "do", "FOR BOTH SIDES", "A clinical note and take-home instructions."),
            (EV["w_confirms"], "do", "THE PATIENT IS THE REVIEWER", "Understood → confirmed. “What did it say?” → flagged."),
            (EV["w_approves"], "do", "THE NURSE TEACHES", "Approved phrases become the translator's examples. No retraining.")],
}

def win(a, b):
    return f'data-start="{a:.3f}" data-duration="{max(0.05, b - a):.3f}"'

def card_html(pid, i, c):
    t0, kind, tag, body = c
    p = PAGES[pid]
    return (f'<div class="card clip k-{kind}" id="c-{pid}-{i}" data-at="{t0:.3f}" {win(p["start"], p["end"])} {BLUR}>'
            f'<div class="ctag">{E(tag)}</div><div class="cbody">{E(body)}</div></div>')

def phone(pid, inner, title="Consulta"):
    return f'''<div class="phone" id="ph-{pid}"><div class="screen">
  <div class="ptop"><span class="ptitle">{E(title)}</span><span class="plang">castellano ⇄ quechua</span></div>
  <div class="ava" id="ava-{pid}">{''.join(f'<img class="st st-{s}" src="assets/img/{s}.png">' for s in ["reposo","pensando","hablando","escuchando","no_entendi"])}</div>
  <div class="msgs">{inner}</div>
  <div class="mic"><i class="r1"></i><i class="r2"></i><i class="r3"></i><i class="r4"></i><b></b></div>
</div><div class="notch"></div></div>'''

def steps(pid, labels):
    return '<div class="steps" id="steps-' + pid + '">' + "".join(
        f'<div class="step" id="st-{pid}-{i}"><i></i><span>{E(l)}</span></div>' for i, l in enumerate(labels)) + "</div>"

def wspans(txt, cls):
    return "".join(f'<span class="{cls}">{E(w)}</span> ' for w in txt.split())

QB3 = "Sapa pusaq horasmanta huk pastillata upyay, mikusqaykimanta qhipaman. Ama tewan upyaychu."
MOCK = '<div class="mock">recreated from the app\'s screens</div>'

def stage(pid):
    if pid == "her":
        return ('<div class="laptop" id="lap"><div class="lscreen"></div><div class="lbase"></div></div>'
                '<div class="who" id="mama-name">Lic. Norma Choque Guerreros · nurse, Pilpichaca health zone</div>')
    if pid == "why":
        return ('<div class="stat" id="st1" ' + BLUR + '><div class="big">9 <small>in</small> 10</div><div class="lab">of her patients speak Quechua</div></div>'
                '<div class="stat dim" id="st2" ' + BLUR + '><div class="big">1 <small>in</small> 7</div><div class="lab">doctors in rural Peru speaks basic Quechua</div></div>'
                '<div class="src" id="st-src">Her interview, Oct 24 · Bendezu-Quispe et al., Rev Peru Med Exp Salud Publica, 2020</div>'
                '<div class="logo" id="why-logo"><img src="assets/img/presentarse.png"><b>Chaski</b></div>')
    if pid == "hands":
        return phone("hands",
            '<div class="det" id="d1"><b>Español</b><span>health worker</span></div>'
            '<div class="det q" id="d2"><b>Quechua</b><span>patient</span></div>' + MOCK)
    if pid == "instr":
        return phone("instr",
            '<div class="bub es" id="m-es"><span class="tagl">CASTELLANO</span><div class="btxt">' +
            wspans("Tome una pastilla cada ocho horas, después de comer. No la tome con té.", "ew") + '</div></div>' +
            steps("instr", ["Entendiendo", "Traduciendo", "Revisando"]) +
            '<div class="bub qu" id="m-qu"><span class="tagl">QUECHUA</span><div class="btxt">' + wspans(QB3, "qw") +
            '</div><div class="chip ok" id="m-ok">✓ Revisado</div></div>' + MOCK)
    if pid == "pat":
        return phone("pat",
            '<div class="bub qu" id="p-qu"><span class="tagl">PACIENTE · QUECHUA</span><div class="btxt">Umaymi nanachkan qayna punchawmanta.</div>'
            '<div class="wave" id="p-wave">' + "".join(f'<i style="--h:{h}"></i>' for h in [8, 18, 30, 22, 36, 14, 26, 40, 20, 12, 28, 34, 16, 24, 10, 30, 18, 8]) + '</div></div>'
            '<div class="bub es" id="p-es"><span class="tagl">CASTELLANO</span><div class="btxt big">Me duele la cabeza desde ayer.</div></div>' + MOCK)
    if pid == "ask":
        return phone("ask",
            '<div class="bub es" id="a-es"><span class="tagl">CASTELLANO</span><div class="btxt">Tome la pastilla después de comer.</div></div>'
            '<div class="askc" id="a-q"><span class="tagl">CHASKI PREGUNTA</span><div class="btxt">¿Qué medicina, y cada cuánto?</div></div>'
            '<div class="askc rep" id="a-r"><span class="tagl">NO LO DIJE</span><div class="btxt">No estoy seguro de la dosis. ¿Me lo repite?</div></div>' + MOCK)
    if pid == "moment":
        return phone("moment",
            '<div class="bub es" id="r-es"><span class="tagl">CASTELLANO</span><div class="btxt">Tómela con agua, no con té.</div></div>'
            '<div class="banner" id="r-ban">Ensayo: simulamos que el traductor se equivocó</div>'
            '<div class="redc" id="r-red"><div class="rt">No lo dije</div><div class="rr">Cambió un dato crítico: prohibiciones</div>'
            '<div class="rrow"><span>Debía decir</span><b>Yakuwan upyay, <u>ama</u> tewan upyay<u>chu</u>.</b></div>'
            '<div class="rrow bad"><span>Iba a decir</span><b>Yakuwan upyay, tewan upyay.</b></div></div>' + MOCK)
    if pid == "emg":
        return phone("emg",
            '<div class="egrid" id="e-grid">' + "".join(f'<div class="eg{" sel" if i == 0 else ""}" id="eg-{i}">{E(x)}</div>' for i, x in enumerate(
                ["¿Dónde le duele?", "¿Desde cuándo?", "¿Tiene fiebre?", "¿Está embarazada?", "¿Vino con alguien?", "No se preocupe"])) + '</div>'
            '<div class="ecard" id="e-card"><div class="eq">¿Mayta nanan?</div><div class="ees">¿Dónde le duele?</div>'
            '<div class="chip ok on2">✓ Revisada · su voz</div></div>' + MOCK, "Emergencia")
    if pid == "rx":
        return phone("rx",
            '<div class="box" id="x-box"><div class="boxl">PARACETAMOL</div><div class="boxs">500 mg · 20 tabletas</div></div>'
            '<div class="askc" id="x-read"><span class="tagl">CHASKI</span><div class="btxt">Leí: paracetamol 500 mg, una tableta cada 8 horas. ¿Se lo digo?</div></div>'
            '<div class="bub es" id="x-yes"><span class="tagl">PERSONAL</span><div class="btxt big">Sí.</div></div>' + MOCK, "Receta")
    if pid == "sum":
        return phone("sum",
            '<div class="sum" id="s-1"><div class="sh">Para la historia clínica</div><div class="sb">1 pastilla cada 8 h, después de comer; no con té. Le duele la cabeza desde ayer.</div></div>'
            '<div class="sum" id="s-2"><div class="sh">Para llevar a casa</div><div class="sb qtxt">Sapa pusaq horasmanta huk pastillata upyay…</div></div>'
            '<div class="sum" id="s-3"><div class="sh">Palabras nuevas</div><div class="gl"><span>upyay · tomar</span><span>pusaq · ocho</span><span>nanan · duele</span></div></div>' + MOCK, "Resumen")
    if pid == "nums":
        return ('<div class="nrow" id="n1" ' + BLUR + '><b>99.5%</b><span>of 184 seeded errors caught · 100% of the critical ones · ~3 s per check</span></div>'
                '<div class="nrow" id="n2" ' + BLUR + '><b>54% → 41%</b><span>word errors, on a speaker the model never heard</span></div>'
                '<div class="nrow" id="n3" ' + BLUR + '><b>95%</b><span>of the time it knew who was speaking, in full voice consultations (21 of 22)</span></div>'
                '<div class="src" id="n-src">evals/ in github.com/Freddyx14/chaski · every number has its results file</div>')
    if pid == "end":
        return ('<div class="stack" id="k1">Claude Opus · Sonnet</div><div class="stack" id="k2">Cartesia</div>'
                '<div class="stack" id="k3">Meta MMS, fine-tuned on our data</div>'
                '<div class="logo big2" id="end-logo"><img src="assets/img/reposo.png"><b>Chaski</b>'
                '<i>A Quechua interpreter for rural health workers</i></div>')
    return ""

pages_html = []
for p in DATA["pages"]:
    pid = p["id"]
    cards = "".join(card_html(pid, i, c) for i, c in enumerate(CARDS.get(pid, [])))
    pages_html.append(f'<div class="page clip {"dark" if p["dark"] else "light"}" id="pg-{pid}" {win(p["start"], p["end"])}>'
                      f'<div class="stage">{stage(pid)}</div><div class="col">{cards}</div></div>')

caps_html = "".join(f'<div class="cap clip" id="cap{i}" {win(c["t0"] - 0.05, c["out"])}>' +
                    "".join(f'<span class="w" data-t="{w["t"]:.3f}">{E(w["w"])}</span>' for w in c["words"]) + "</div>" for i, c in enumerate(CAPS))
hud_labels = "".join(f'<div class="blab clip" {win(p["start"], p["end"])}>{E(p["label"])}</div>' for p in DATA["pages"] if p["id"] not in ("her", "end"))

page = f'''<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1920, height=1080" />
<title>Chaski — demo</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="cues.js"></script><script src="data.js"></script><script src="lib/engine.js"></script>
<link rel="stylesheet" href="comp.css" /><link rel="stylesheet" href="demo.css" />
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-width="1920" data-height="1080" data-duration="{TOTAL:.3f}" data-fps="30">
  <div id="field" class="full"></div><div id="glow" class="full"></div>
  {''.join(pages_html)}
  <video id="mama" class="clip" src="assets/video/mama-intro.mp4" muted playsinline {win(0.0, EV["MAMA"] - 0.02)}></video>
  {"".join(f'<div class="msub clip" id="msub{i}" {win(s["t0"], s["t1"] + 0.3)}>{E(s["text"])}</div>' for i, s in enumerate(DATA["mama"]))}
  <div id="hud"><div id="brand">CHASKI</div><div id="blabs">{hud_labels}</div></div>
  <div id="caps">{caps_html}</div>
  <audio id="score" src="assets/audio/mix.wav" data-start="0" data-duration="{TOTAL:.3f}"></audio>
</div>
<script>
{(ROOT / "comp.js").read_text()}
</script>
<script src="lib/motion-blur.js"></script>
</body></html>
'''
(ROOT / "index.html").write_text(page)
print("index.html", len(page), "bytes ·", sum(len(v) for v in CARDS.values()), "cards ·", len(CAPS), "captions")
