"""Timing for the Chaski Devpost demo video (~2:30). Reads the VO alignments, writes data.js + cues.json.
Run: python3 build.py, then score.py cues.json -o assets/audio/mix.wav --emit-js cues.js, then python3 gen_html.py
"""
import json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).parent
VO = ROOT / "assets/audio/vo"
CLIPS = ROOT.parent / "data/mama/video/clips"


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


def words(seg):
    al = json.loads((VO / f"{seg}.alignment.json").read_text())
    chars, starts, ends, off = [], [], [], 0.0
    for c in al:
        chars += c["characters"]; starts += [x + off for x in c["character_start_times_seconds"]]
        ends += [x + off for x in c["character_end_times_seconds"]]; off = ends[-1] if ends else off
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
    lines, cur = [], []
    for w in ws:
        cur.append(w)
        if re.search(r"[.?!,;:]$", w["w"]) and len(cur) >= 3 or len(cur) >= maxw:
            lines.append(cur); cur = []
    if cur:
        if lines and len(cur) <= 2: lines[-1] += cur
        else: lines.append(cur)
    return lines


SEGS = [f"v{i:02d}" for i in range(1, 14) if i != 7]   # v07 (simulated error) cut by Freddy 08:08
D = {s: dur(VO / f"{s}.wav") for s in SEGS}
MAMA = dur(ROOT / "assets/audio/mama-intro.wav")
PAC = dur(ROOT / "assets/audio/paciente-p18-064.wav")
QB3 = dur(ROOT / "assets/audio/quy/b3a-cut.wav")
QEM = dur(ROOT / "assets/audio/emg-mama.wav")

t = {"mama": 0.0}
t["v01"] = MAMA + 0.4
t["v02"] = t["v01"] + D["v01"] + 0.5
t["v03"] = t["v02"] + D["v02"] + 0.5
t["think"] = t["v03"] + D["v03"] + 0.2
t["v04"] = t["think"] + 0.3
t["q_b3"] = t["v04"] + D["v04"] + 0.3
t["pac"] = t["q_b3"] + QB3 + 0.4
t["v05"] = t["pac"] + PAC + 0.3
t["pac_es"] = t["pac"] + PAC + 2.6
t["v06"] = t["v05"] + D["v05"] + 0.5
t["v08"] = t["v06"] + D["v06"] + 0.6
t["q_em"] = t["v08"] + D["v08"] + 0.25
t["v09"] = t["q_em"] + QEM + 0.5
t["v10"] = t["v09"] + D["v09"] + 0.5
t["v13"] = t["v10"] + D["v10"] + 0.5
t["v11"] = t["v13"] + D["v13"] + 0.5
t["v12"] = t["v11"] + D["v11"] + 0.5
t["end"] = t["v12"] + D["v12"]
TOTAL = round(t["end"] + 2.5, 2)
t = {k: round(v, 3) for k, v in t.items()}


def wt(seg, needle, nth=0):
    hits = [w for w in words(seg) if needle.lower() in w["w"].lower()]
    return round(t[seg] + hits[nth]["t0"], 3)


P = [
    ("her", 0.0, "Her words", ""),
    ("why", t["v01"] - 0.3, "Why we built it", ""),
    ("hands", t["v02"] - 0.3, "Hands-free", ""),
    ("instr", t["v03"] - 0.3, "A health worker speaks", ""),
    ("pat", t["pac"] - 0.4, "The patient answers", ""),
    ("ask", t["v06"] - 0.3, "It asks, like a person would", ""),
    ("emg", t["v08"] - 0.3, "Emergency mode", ""),
    ("rx", t["v09"] - 0.3, "Prescription by voice", ""),
    ("sum", t["v10"] - 0.3, "Every visit teaches it", ""),
    ("arch", t["v13"] - 0.3, "How it is built", ""),
    ("nums", t["v11"] - 0.3, "Measured, not claimed", ""),
    ("end", t["v12"] - 0.3, "The name", ""),
]
pages = []
for i, (pid, st, lab, who) in enumerate(P):
    en = P[i + 1][1] if i + 1 < len(P) else TOTAL
    pages.append({"id": pid, "start": round(st, 3), "end": round(en, 3), "label": lab, "who": who, "dark": i % 2 == 0})

caps = []
for s in SEGS:
    for line in chunks(words(s)):
        caps.append({"seg": s, "who": "", "t0": round(t[s] + line[0]["t0"], 3), "t1": round(t[s] + line[-1]["t1"], 3),
                     "words": [{"w": w["w"], "t": round(t[s] + w["t0"], 3)} for w in line]})
for a, b in zip(caps, caps[1:]):
    a["out"] = round(min(b["t0"] - 0.15, a["t1"] + 0.9), 3)
caps[-1]["out"] = round(caps[-1]["t1"] + 0.9, 3)


def srt(path, off, cut):
    out = []
    for blk in Path(path).read_text().strip().split("\n\n"):
        L = blk.splitlines()
        a, b = [sum(float(x) * m for x, m in zip(re.split("[:,]", v)[:3], (3600, 60, 1))) + int(re.split("[:,]", v)[3]) / 1000 for v in L[1].split(" --> ")]
        if a < cut:
            out.append({"t0": round(off + a, 3), "t1": round(off + min(b, cut), 3), "text": " ".join(L[2:])})
    return out


_ms = json.loads((ROOT / "mama_subs.json").read_text())   # from recut_mama.py: pauses removed, sentences complete
mama_subs = []
for i, m in enumerate(_ms):                               # each subtitle holds until the next one (she keeps talking)
    nxt = _ms[i + 1]["t0"] - 0.12 if i + 1 < len(_ms) else MAMA - 0.2
    mama_subs.append({"t0": m["t0"], "t1": round(nxt, 3), "text": m["text"]})

ev = dict(t)
ev.update({
    "TOTAL": TOTAL, "MAMA": MAMA,
    "w_nine": wt("v01", "Nine"), "w_seven": wt("v01", "seven"), "w_built": wt("v01", "built"),
    "w_hands": wt("v02", "hands-free"), "w_who": wt("v02", "who"), "w_lang": wt("v02", "language"), "w_follow": wt("v02", "follow-up"), "w_own": wt("v02", "fine-tuned"), "w_google": wt("v02", "Google"),
    "w_opus": wt("v04", "Opus"), "w_checks": wt("v04", "checks"), "w_second": wt("v04", "second"),
    "w_fine": wt("v05", "fine-tuned"),
    "w_asks": wt("v06", "asks"), "w_repeat": wt("v06", "repeat"),
    "w_mother8": wt("v08", "mother"),
    "w_photo": wt("v09", "photo"), "w_reads": wt("v09", "reads"), "w_yes": wt("v09", "yes"), "w_quy9": wt("v09", "Quechua"),
    "w_note": wt("v10", "note"), "w_home": wt("v10", "home"), "w_words": wt("v10", "words"),
    "w_confirms": wt("v10", "confirms"), "w_approves": wt("v10", "approves"), "w_pilpi": wt("v10", "learns"),
    "w_ft13": wt("v13", "fine-tuned"), "w_362": wt("v13", "hundred"), "w_voice13": wt("v13", "voice"),
    "w_opus13": wt("v13", "Opus"), "w_sonnet13": wt("v13", "Sonnet"), "w_code13": wt("v13", "code"), "w_acc13": wt("v13", "accuracy"),
    "w_184": wt("v11", "hundred"), "w_54": wt("v11", "fifty-four"), "w_2122": wt("v11", "ninety-five"),
    "w_built12": wt("v12", "Claude"), "w_cartesia": wt("v12", "Cartesia"), "w_meta": wt("v12", "Meta"), "w_chaski12": wt("v12", "Chaski."),
})
(ROOT / "data.js").write_text("window.DATA = " + json.dumps({"pages": pages, "caps": caps, "mama": mama_subs, "ev": ev}, ensure_ascii=False) + ";\n")

fx = [{"type": "sample", "bus": "voice", "file": f"assets/audio/vo/{s}.wav", "at": t[s]} for s in SEGS]
fx += [
    {"type": "sample", "bus": "music", "file": "assets/audio/music-andes.wav", "at": 0.0, "len": TOTAL, "gain_db": -10, "fade_in": 0.5, "fade_out": 2.5},
    {"type": "sample", "bus": "voice", "file": "assets/audio/mama-intro.wav", "at": 0.0, "gain_db": 1, "fade_out": 0.3},
    {"type": "sample", "bus": "voice", "file": "assets/audio/quy/b3a-cut.wav", "at": t["q_b3"], "gain_db": -2},
    {"type": "sample", "bus": "voice", "file": "assets/audio/paciente-p18-064.wav", "at": t["pac"]},
    {"type": "sample", "bus": "voice", "file": "assets/audio/emg-mama.wav", "at": t["q_em"], "gain_db": 1},
]
for p in pages[1:]:
    fx.append({"type": "whoosh", "at": max(0, p["start"] - 0.05), "gain_db": -16})
for k in ["pac_es", "q_em"]:
    fx.append({"type": "blip", "at": t[k], "notes": [0], "gain_db": -12})
cues = {
    "title": "Chaski — Devpost demo", "bpm": 84, "duration": TOTAL, "lufs": -14.0, "true_peak": -1.0,
    "chords": ["Dmaj7", "Bm7", "Gmaj7", "A"],
    "marks": {k: v for k, v in ev.items() if isinstance(v, (int, float))},
    "shots": [{"id": p["id"], "at": p["id"], "in": "open" if i == 0 else "cut", "field": "dark" if p["dark"] else "light",
               "hold": round(p["end"] - p["start"] - 0.4, 2), "idea": p["label"]} for i, p in enumerate(pages)],
    "camera": {"moves": [], "punches": [], "shakes": []},
    "layers": [],
    "fx": fx,
    "mix": {"pump_db": 0.0, "voice_duck_db": 14.0, "music_db": -14.0, "voice_db": 4.0},
}
for p in pages:
    cues["marks"][p["id"]] = p["start"]
(ROOT / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1))
print(f"total {TOTAL:.1f} s ({int(TOTAL // 60)}:{TOTAL % 60:04.1f}) · {len(caps)} captions")
for p in pages: print(f"  {p['start']:7.2f} {p['id']:6s} {p['label']}")
