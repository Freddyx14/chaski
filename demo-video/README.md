# Chaski · Devpost demo video (Sun Oct 25, 04:10 PT)

2:39, 1080p, Freddy's cloned voice (ElevenLabs `freddy-en`), his mother's real clips (with permission), a family
member's real Quechua answer, and Chaski's emergency phrase in the voice trained on the nurse's (`mama_freddy`).
Features follow the SOT (D32–D46). Phone screens are recreations of the app's screens (labelled in-frame).
The instruction's Quechua plays in Meta's stock MMS voice (the only local audio for that sentence).

Rebuild: `python3 build.py` → `score.py cues.json -o assets/audio/mix.wav --emit-js cues.js` → `python3 gen_html.py`
→ `apple_audit.py .` → `npx hyperframes render . --fps 30 --quality delivery -o renders/chaski-demo-vN.mp4` → `deliver.sh`.
**Nothing under `assets/audio/` or `assets/video/` goes to git** (family audio, nurse video).
