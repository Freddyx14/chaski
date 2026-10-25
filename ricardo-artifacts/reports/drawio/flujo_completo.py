# -*- coding: utf-8 -*-
"""El flujo COMPLETO de un turno: la voz (Ricardo) + el intérprete agente, las barreras y el crítico.

Reusa el Lienzo de `generar.py` para que salga con el mismo estilo y en los dos formatos (.svg y .drawio).
Se corre desde la raíz de ricardo-artifacts:

    uv run --with pillow python reports/drawio/flujo_completo.py

Cada número sale de un archivo de resultados (ver `evals/HISTORIA.md` y `README.md` en la raíz del repo).
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("generar", Path(__file__).with_name("generar.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)  # regenera los 3 diagramas de Ricardo tal cual (es determinista)

Lienzo, CAJA, TXT = G.Lienzo, G.CAJA, G.TXT
GRIS, AZUL, VERDE, ROJO, MORADO = "#8C8C7A", "#1F6FD0", "#1B9476", "#C8372F", "#8A4FBD"
BANDA = TXT.format(s=13, c="#16160F", f=1)
NOTA = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C4C2B6;align=left;"
        "verticalAlign=top;spacingLeft=12;spacingTop=8;fontSize=11;fontColor=#4E4D45;")

f = Lienzo("Full flow")
f.caja("Chaski · one full turn: hear, understand, check, and only then speak",
       TXT.format(s=19, c="#16160F", f=1), 40, 20, 1200, 28)
f.caja("Blue: Meta on our GPU, fine-tuned on the families’ voices · Green: Cartesia · Red: Claude · "
       "Purple: guards in code (the model proposes, the code decides) · Measured 24/25-Oct-2026",
       TXT.format(s=12, c="#4E4D45", f=0), 40, 50, 1500, 20)

# ── 1 · Oír ─────────────────────────────────────────────────────────────────────────────
f.caja("1 · Hear and understand", BANDA, 40, 86, 300, 20)
mic = f.caja("Microphone\n\niPhone · 16 kHz mono\nNurse or patient",
             CAJA.format(b=GRIS), 40, 190, 170, 76, icono="micro")
lid = f.caja("mms-lid-512\n\nQuechua or Spanish?\n49 ms · 3/6 on real family voice,\nso it never decides alone",
             CAJA.format(b=AZUL), 245, 180, 200, 90, icono="gpu")
f.flecha(mic, lid)
stt_es = f.caja("Cartesia ink-whisper\n\nHears Spanish\n3.5 s of audio in 480 ms",
                CAJA.format(b=VERDE), 490, 110, 230, 84, icono="cartesia")
stt_qu = f.caja("MMS-1B-all + our adapter\n\nHears Chanka Quechua\nWER 53.9 % → 40.9 % with the families’\nvoices (held-out speaker)\n2.2 M of 965 M parameters trained",
                CAJA.format(b=AZUL) + "strokeWidth=3;", 490, 250, 250, 110, icono="gpu")
f.flecha(lid, stt_es, "Spanish", f"strokeColor={VERDE};fontColor={VERDE};")
f.flecha(lid, stt_qu, "Quechua", f"strokeColor={AZUL};fontColor={AZUL};")
b1 = f.caja("B1 · Was it heard right?\n\nA number, drug or body part\nheard with low confidence\n→ asks again, never guesses",
            CAJA.format(b=MORADO), 770, 175, 230, 110, icono="guarda")
f.flecha(stt_es, b1); f.flecha(stt_qu, b1)
banco = f.caja("Verified phrase bank · RAG\n\n216 phrases · 24 emergency ones reviewed\nby the nurse · embeddings + lexical\ntop-1 88 % (words alone: 70 %)",
               CAJA.format(b=MORADO), 1030, 320, 290, 110, icono="disco")
interp = f.caja("INTERPRETER · Claude Opus 5\n\nOne call picks one of 5 actions:\ntranslate · ask back once ·\nanswer the asker · did not understand ·\nuse a verified phrase\nCleans up both sides before anything is said\n98–100 % correct action · 0 invented clinical facts",
                CAJA.format(b=ROJO) + "strokeWidth=3;", 1340, 140, 290, 170, icono="claude")
f.flecha(b1, interp)
f.flecha(banco, interp, "candidates")
verif = f.caja("Verified phrase\n\nAudio reviewed by the nurse\nGoes straight to the speaker:\nnothing generated, nothing waited for",
               CAJA.format(b=MORADO), 1670, 110, 200, 100, icono="guarda")
f.flecha(interp, verif, "use phrase", f"strokeColor={MORADO};fontColor={MORADO};")

# ── 2 · Revisar antes de hablar (de derecha a izquierda) ─────────────────────────────────
f.caja("2 · Check before speaking (in doubt, Chaski stays quiet)", BANDA, 40, 455, 600, 20)
b23 = f.caja("B2 · B3 · The clean-up\n\nMay not change or add any fact\nIf it did, the raw sentence\nis used instead",
             CAJA.format(b=MORADO), 1620, 495, 230, 110, icono="guarda")
f.flecha(interp, b23, "translate", f"strokeColor={ROJO};fontColor={ROJO};")
trad = f.caja("Translator · Claude Sonnet 5\n\nMedium effort, starts while Opus decides\n0 of 92 fixed terms damaged (NLLB: 3)\nNLLB-1.3B stays as the offline mode",
              CAJA.format(b=ROJO), 1340, 495, 240, 110, icono="claude")
f.flecha(b23, trad)
b4 = f.caja("B4 · Fixed terms\n\nChanka numerals (pusaq = 8)\ndrug · unit · negation\n“with water” must carry unu / yaku",
            CAJA.format(b=MORADO), 1060, 495, 240, 110, icono="guarda")
f.flecha(trad, b4)
crit = f.caja("CRITIC · Claude Sonnet 5\n\nBack-translates blind (never sees the original)\nExtracts the facts from both sides\nFlags invented advice or diagnoses\n2.6 s · was 9 s",
              CAJA.format(b=ROJO) + "strokeWidth=3;", 740, 490, 280, 130, icono="claude")
f.flecha(b4, crit)
b56 = f.caja("B5 · B6 · Code does the comparing\n\nDose · frequency · days · unit\nnegation · what to take it with\nstrength · allergy · pregnancy\nAny mismatch → fails closed",
             CAJA.format(b=MORADO) + "strokeWidth=3;", 430, 490, 270, 130, icono="guarda")
f.flecha(crit, b56)
bloq = f.caja("BLOCKED\n\nChaski says nothing and tells\nthe staff which fact failed:\n“the frequency did not match”",
              CAJA.format(b=ROJO) + "dashed=1;", 70, 500, 300, 100, icono="guarda")
f.flecha(b56, bloq, "mismatch", f"strokeColor={ROJO};fontColor={ROJO};")

# ── 3 · Hablar ──────────────────────────────────────────────────────────────────────────
f.caja("3 · Speak", BANDA, 40, 700, 300, 20)
voz_es = f.caja("Cartesia Sonic 3.6\n\nSpeaks Spanish\nto the nurse",
                CAJA.format(b=VERDE), 300, 740, 220, 84, icono="cartesia")
voz_qu = f.caja("mms-tts-quy, fine-tuned\n\nSpeaks Quechua to the patient\nIn the voice of a woman from the\ncommunity, with her permission",
                CAJA.format(b=AZUL) + "strokeWidth=3;", 560, 740, 250, 100, icono="gpu")
f.flecha(b56, voz_es, "passes", f"strokeColor={VERDE};fontColor={VERDE};")
f.flecha(b56, voz_qu, "passes", f"strokeColor={AZUL};fontColor={AZUL};")
par = f.caja("Speaker and screen\n\nText first, audio after\nRed only when Chaski did not say it",
             CAJA.format(b=GRIS), 440, 880, 240, 76, icono="parlante")
f.flecha(voz_es, par); f.flecha(voz_qu, par)

res = f.caja("When the visit ends · Claude\n\nA clinical note for the staff\nTake-home instructions for the patient\nNew Quechua words from that visit",
             CAJA.format(b=ROJO), 1150, 740, 260, 110, icono="claude")
rec = f.caja("Prescription · Claude vision\n\nPhoto of the box or the script\n→ dose, frequency, days\n→ the same guards → asks again if unsure",
             CAJA.format(b=ROJO), 1450, 740, 280, 110, icono="claude")

f.caja("What was measured\n\n"
       "A bank of 952 seeded errors (changed dose, flipped negation, wrong drug, wrong unit, dropped \u201cwith water\u201d, invented advice): "
       "Chaski caught 183 of 184 and 100 % of the critical ones, and every block names the fact that failed.\n"
       "Asking Claude \u201cis this translated correctly?\u201d also catches errors, but never says why and holds back 1 in 4 correct sentences.\n"
       "Full turn, end to end, live: p50 7.8 s, p95 11.4 s; a whole consultation 49\u201370 s; $0.0084 per turn. Only two Claude roles (interpreter and critic): no agent for its own sake.",
       NOTA, 40, 990, 1830, 110)

f.guardar("reports/drawio/arquitectura-flujo-completo.drawio", 1900, 1130)
G.revisar([("flujo completo", f, (1900, 1130))])
