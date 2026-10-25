"""Her two intro clips (no «Buenas noches»: speech starts at «Soy», 1.74 s) with the pauses removed and every sentence complete (Freddy, 07:48).
Speech regions from ffmpeg silencedetect (-32 dB, 0.35 s); keeps ~0.15 s of air around each phrase.
Writes assets/video/mama-intro.mp4 (silent), assets/audio/mama-intro.wav and mama_subs.json (remapped .en.srt)."""
import json, re, subprocess
from pathlib import Path
ROOT = Path(__file__).parent
CL = ROOT.parent / "data/mama/video/clips"
CLIPS = [
    ("VIDEO-01_presentacion-nombre_16s", [(1.62, 2.55), (2.78, 5.4), (6.0, 6.85), (7.85, 9.55), (10.8, 13.9), (14.2, 16.0)]),
    ("PITCH-B1_problema-profesionales-costa_16s", [(0.35, 1.5), (1.9, 7.6), (7.8, 13.0)]),   # ends exactly on «quechua» (whisper word end 13.0, silence from 12.97)
]
def srt(path):
    out = []
    for blk in path.read_text().strip().split("\n\n"):
        L = blk.splitlines()
        a, b = [sum(float(x) * m for x, m in zip(re.split("[:,]", v)[:3], (3600, 60, 1))) + int(re.split("[:,]", v)[3]) / 1000 for v in L[1].split(" --> ")]
        out.append((a, b, " ".join(L[2:])))
    return out
def remap(t, segs, base):
    acc = 0.0
    for a, b in segs:
        if t < a: return base + acc
        if t <= b: return base + acc + (t - a)
        acc += b - a
    return base + acc
parts, subs, base = [], [], 0.0
tmp = ROOT / "assets/video/_tmp"; tmp.mkdir(exist_ok=True)
for k, (name, segs) in enumerate(CLIPS):
    sel = "+".join(f"between(t,{a},{b})" for a, b in segs)
    out = tmp / f"c{k}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(CL / f"{name}.mp4"),
        "-vf", f"select='{sel}',setpts=N/FRAME_RATE/TB,fps=30,scale=1024:576,setsar=1",
        "-af", f"aselect='{sel}',asetpts=N/SR/TB,aresample=48000", "-ac", "1",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)], check=True)
    parts.append(out)
    for a, b, text in srt(CL / f"{name}.en.srt"):
        subs.append({"t0": round(remap(a, segs, base), 3), "t1": round(remap(b, segs, base) + 0.15, 3), "text": text})
    base += sum(b - a for a, b in segs)
(tmp / "list.txt").write_text("".join(f"file '{p.name}'\n" for p in parts))
full = tmp / "full.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-c", "copy", str(full)], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(full), "-an", "-c:v", "copy", str(ROOT / "assets/video/mama-intro.mp4")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(full), "-vn", "-ar", "48000", "-ac", "1", "-af", "afade=t=out:st=%.2f:d=0.06" % (base - 0.06), str(ROOT / "assets/audio/mama-intro.wav")], check=True)
for p in tmp.iterdir(): p.unlink()
tmp.rmdir()
(ROOT / "mama_subs.json").write_text(json.dumps(subs, ensure_ascii=False, indent=1))
print(f"mama intro {base:.2f} s, {len(subs)} subtitles")
for s in subs: print(f"  {s['t0']:6.2f}-{s['t1']:6.2f} {s['text']}")
