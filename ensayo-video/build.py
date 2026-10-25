"""Builds the timing for the Chaski demo rehearsal video.

Reads the ElevenLabs word alignments (assets/audio/vo/sNN.alignment.json), lays every voice line,
clip and phone event on one schedule, and writes:
  - data.js    → window.DATA: pages, captions (word times), events, the pitch clock origin
  - cues.json  → the soundtrack (VO + mom + patient + Chaski's Quechua + a quiet bed + UI blips)
Run: python3 build.py   (then score.py cues.json … --emit-js cues.js)
"""
import json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).parent
VO = ROOT / "assets/audio/vo"


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(p)]).strip())


def words(seg):
    """Word list with absolute-from-segment start/end, from the char alignment."""
    al = json.loads((VO / f"{seg}.alignment.json").read_text())
    chars, starts, ends, off = [], [], [], 0.0
    for chunk in al:  # long texts come in chunks; times restart per chunk
        c, s, e = chunk["characters"], chunk["character_start_times_seconds"], chunk["character_end_times_seconds"]
        chars += c; starts += [x + off for x in s]; ends += [x + off for x in e]
        off = ends[-1] if ends else off
    out, cur = [], None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if cur: out.append(cur); cur = None
            continue
        if cur is None: cur = {"w": "", "t0": s, "t1": e}
        cur["w"] += ch; cur["t1"] = e
    if cur: out.append(cur)
    return out


def chunks(ws, maxw=7):
    """Caption lines: break on . ? ! , ; or at maxw words."""
    lines, cur = [], []
    for w in ws:
        cur.append(w)
        if re.search(r"[.?!,;:]$", w["w"]) and len(cur) >= 3 or len(cur) >= maxw:
            lines.append(cur); cur = []
    if cur:
        if lines and len(cur) <= 2: lines[-1] += cur
        else: lines.append(cur)
    return lines


# ── the schedule (video seconds). T0 = pitch clock 0:00 ──────────────────────────────────────────
D = {s: dur(VO / f"{s}.wav") for s in [f"s{i:02d}" for i in range(12)]}
MAMA = dur(ROOT / "assets/audio/mama-b1.wav")
PAC = dur(ROOT / "assets/audio/paciente-p18-064.wav")
QB3 = dur(ROOT / "assets/audio/quy/b3a-48k.wav")
QEM = dur(ROOT / "assets/audio/quy/emg-48k.wav")

t = {}
t["s00"] = 0.5
T0 = round(t["s00"] + D["s00"] + 0.9, 2)                  # pitch starts
t["mama"] = T0
t["s01"] = T0 + MAMA + 0.5
t["s02"] = t["s01"] + D["s01"] + 0.6
t["s03"] = t["s02"] + D["s02"] + 0.7                      # Freddy talks to the phone (Spanish)
t["think"] = t["s03"] + D["s03"] + 0.2                     # «Pensando» starts
t["think_end"] = t["think"] + 8.0                         # p50 8.0 s (evals/HISTORIA.md §2d)
t["s04"] = t["think"] + 0.6                               # the problem, told while it thinks
t["q_b3"] = max(t["think_end"], t["s04"] + D["s04"]) + 0.5  # Chaski speaks Quechua
t["s05"] = t["q_b3"] + QB3 + 0.5
t["pac"] = t["s05"] + D["s05"] + 0.6                      # Ricardo plays the family clip
t["s06"] = t["pac"] + PAC + 0.4
t["pac_es"] = t["pac"] + PAC + 3.8                        # Spanish on screen (~4 s turn)
t["tap1"] = t["s06"] + D["s06"] + 0.7                     # Emergencia
t["tap2"] = t["tap1"] + 1.1                               # ¿Dónde le duele?
t["q_em"] = t["tap2"] + 0.35
t["s07"] = t["q_em"] + QEM + 0.5
t["s08"] = t["s07"] + D["s07"] + 0.7
t["red"] = t["s08"] + D["s08"] + 0.7
t["s09"] = t["red"] + 1.0
t["s10"] = t["s09"] + D["s09"] + 1.0                      # Ricardo
t["s11"] = t["s10"] + D["s10"] + 0.8
t["end"] = t["s11"] + D["s11"] + 0.7
TOTAL = round(t["end"] + 9.0, 2)
t = {k: round(v, 3) for k, v in t.items()}

# pages (field flips on every cut). id, start, label, who
P = [
    ("intro", 0.0, "Cómo se ve el demo", ""),
    ("b1", T0 - 0.8, "B1 · Su voz", "MAMÁ · VIDEO"),
    ("b1b", t["s01"] - 0.4, "B1 · Quién es", "FREDDY"),
    ("b2", t["s02"] - 0.4, "B2 · El problema", "FREDDY"),
    ("b2b", t["s03"] - 0.4, "B2 → B3 · Habla al celular", "FREDDY"),
    ("b3", t["s05"] - 0.4, "B3 · Cómo se revisó", "FREDDY"),
    ("b3b", t["pac"] - 0.4, "B3 · Responde el paciente", "RICARDO + FREDDY"),
    ("b3c", t["tap1"] - 0.4, "B3 · Modo emergencia", "FREDDY"),
    ("b4", t["s08"] - 0.4, "B4 · El momento", "FREDDY"),
    ("b5", t["s10"] - 0.5, "B5 · Cómo está hecho", "RICARDO"),
    ("b6", t["s11"] - 0.4, "B6 · Cierre", "FREDDY"),
    ("end", t["end"], "Después del pitch", ""),
]
pages = []
for i, (pid, st, lab, who) in enumerate(P):
    en = P[i + 1][1] if i + 1 < len(P) else TOTAL
    pages.append({"id": pid, "start": round(st, 3), "end": round(en, 3), "label": lab, "who": who,
                  "dark": i % 2 == 0})

# captions: what is said out loud, word by word
caps = []
SPEAKER = {"s00": "", "s03": "FREDDY, al celular", "s10": "RICARDO"}
for s in [f"s{i:02d}" for i in range(12)]:
    ws = words(s)
    for line in chunks(ws):
        caps.append({"seg": s, "who": SPEAKER.get(s, "FREDDY"),
                     "t0": round(t[s] + line[0]["t0"], 3), "t1": round(t[s] + line[-1]["t1"], 3),
                     "words": [{"w": w["w"], "t": round(t[s] + w["t0"], 3)} for w in line]})
# a caption stays until the next one starts (or 0.9 s after it ends, whichever first)
for a, b in zip(caps, caps[1:]):
    a["out"] = round(min(b["t0"] - 0.05, a["t1"] + 0.9), 3)
caps[-1]["out"] = round(caps[-1]["t1"] + 0.9, 3)
# the mom's clip has its own English subtitles (from the .en.srt), shown as captions too
def srt(path, off):
    out = []
    for blk in Path(path).read_text().strip().split("\n\n"):
        L = blk.splitlines()
        a, b = [sum(float(x) * m for x, m in zip(re.split("[:,]", v)[:3], (3600, 60, 1))) + int(re.split("[:,]", v)[3]) / 1000
                for v in L[1].split(" --> ")]
        out.append({"t0": round(off + a, 3), "t1": round(off + b, 3), "text": " ".join(L[2:])})
    return out
mama_subs = srt(ROOT.parent / "data/mama/video/clips/PITCH-B1_problema-profesionales-costa_16s.en.srt", T0)

def word_t(seg, needle, nth=0):
    hits = [w for w in words(seg) if needle.lower() in w["w"].lower()]
    return round(t[seg] + hits[nth]["t0"], 3)

ev = dict(t)
ev.update({
    "T0": T0, "TOTAL": TOTAL,
    "w_nine": word_t("s01", "Nine"), "w_one5": word_t("s01", "About"),
    "w_nurse": word_t("s02", "nurse"), "w_tech": word_t("s02", "technician"), "w_driver": word_t("s02", "driver"),
    "w_gest": word_t("s02", "gestures"), "w_pill": word_t("s02", "breaks"),
    "w_40": word_t("s04", "forty"), "w_7": word_t("s04", "seven"),
    "w_clean": word_t("s05", "cleaned"), "w_transl": word_t("s05", "translated"), "w_back": word_t("s05", "back"),
    "w_code": word_t("s05", "code"), "w_spoke": word_t("s05", "speak"),
    "w_ears": word_t("s06", "ears"), "w_claude6": word_t("s06", "Claude"),
    "w_lost": word_t("s09", "lost"), "w_caught": word_t("s09", "caught"), "w_worse": word_t("s09", "worse"),
    "w_54": word_t("s10", "fifty"), "w_brain": word_t("s10", "brain"), "w_184": word_t("s10", "hundred"),
    "w_crit": word_t("s10", "critical"),
    "w_note": word_t("s11", "note"), "w_home": word_t("s11", "home"), "w_words": word_t("s11", "words"),
    "w_anth": word_t("s11", "Anthropic"), "w_next": word_t("s11", "Next"),
})
pitch_len = t["s11"] + D["s11"] - T0

(ROOT / "data.js").write_text("window.DATA = " + json.dumps(
    {"pages": pages, "caps": caps, "mama": mama_subs, "ev": ev, "pitch_len": round(pitch_len, 2)},
    ensure_ascii=False) + ";\n")

# ── soundtrack ───────────────────────────────────────────────────────────────────────────────────
fx = []
for s in [f"s{i:02d}" for i in range(12)]:
    fx.append({"type": "sample", "bus": "voice", "file": f"assets/audio/vo/{s}.wav", "at": t[s], "gain_db": 0})
fx += [
    {"type": "sample", "bus": "voice", "file": "assets/audio/mama-b1.wav", "at": T0, "gain_db": 1, "fade_in": 0.05, "fade_out": 0.2},
    {"type": "sample", "bus": "voice", "file": "assets/audio/paciente-p18-064.wav", "at": t["pac"], "gain_db": 0},
    {"type": "sample", "bus": "voice", "file": "assets/audio/quy/b3a-48k.wav", "at": t["q_b3"], "gain_db": -2},
    {"type": "sample", "bus": "voice", "file": "assets/audio/quy/emg-48k.wav", "at": t["q_em"], "gain_db": -2},
]
# UI sounds: a soft page turn on each cut, a blip when a direction card lands
for p in pages[1:]:
    fx.append({"type": "whoosh", "at": max(0, p["start"] - 0.05), "gain_db": -16})
for k in ["think_end", "pac_es", "tap1", "tap2"]:
    fx.append({"type": "blip", "at": t[k], "notes": [0], "gain_db": -12})
fx.append({"type": "blip", "at": t["red"], "notes": [12, 7, 3, 0], "gain_db": -10})

cues = {
    "title": "Chaski — ensayo del demo, beat por beat",
    "bpm": 84, "duration": TOTAL, "lufs": -14.0, "true_peak": -1.0,
    "chords": ["Dmaj7", "Bm7", "Gmaj7", "A"],
    "marks": {k: v for k, v in ev.items() if isinstance(v, (int, float))},
    "shots": [{"id": p["id"], "at": p["id"], "in": "open" if i == 0 else "cut",
               "field": "dark" if p["dark"] else "light", "hold": round(p["end"] - p["start"] - 0.4, 2),
               "idea": p["label"]} for i, p in enumerate(pages)],
    "camera": {"moves": [], "punches": [], "shakes": []},
    "layers": [
        {"inst": "pad", "from_bar": 0, "to_bar": 400, "cutoff": 520, "gain_db": -9},
        {"inst": "sub", "from_bar": 0, "to_bar": 400, "pattern": "X...............", "gain_db": -12},
    ],
    "fx": fx,
    "mix": {"pump_db": 0.0, "voice_duck_db": 9.0, "music_db": -8.0, "voice_db": 2.0},
}
for p in pages:
    cues["marks"][p["id"]] = p["start"]
(ROOT / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1))
print(f"T0 {T0} · total {TOTAL:.1f} s · pitch {int(pitch_len // 60)}:{pitch_len % 60:04.1f} · {len(caps)} caption lines")
for p in pages: print(f"  {p['start']:7.2f} {p['id']:5s} {'dark ' if p['dark'] else 'light'} {p['label']}")
