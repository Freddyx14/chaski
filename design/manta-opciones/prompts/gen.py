"""Generates one pen.dev spec per manta option. Shared screens + one direction block per option.

Run: python3 gen.py  → writes opcion-<x>.txt next to this file.
"""
from pathlib import Path

AQUI = Path(__file__).parent

BASE = """
RIMAY — ANDEAN MANTA DESIGN OPTION {letra}: "{nombre}". THREE iPHONE SCREENS ON ONE BOARD.

WHAT RIMAY IS
Rimay is a pocket interpreter between Spanish and Chanka Quechua for a rural health post in Pilpichaca,
Huancavelica, Peru (3,800 m in the Andes). The nurse holds the iPhone between herself and the patient. She
speaks Spanish; Rimay says it aloud in Quechua; before saying anything Rimay audits its own translation and
refuses to say a dose, time or number of days that changed. The avatar is Chaski, a young vicuña with an
interpreter headset and a teal scarf (attached images chaski-reposo.png, chaski-hablando.png,
chaski-presentarse.png; each has its own soft beige gradient background, top #C5BAB1 to bottom #E2DBD5).

THE BRIEF FOR THIS BOARD
The founder is Peruvian, from Huancavelica. He wants the app to feel unmistakably Peruvian-Andean, inspired by
the woven mantas (lliclla, aguayo) sold in every highland market: the attached manta-ref-6.png (his favourite:
white ground with bright stripe bands — magenta, orange, yellow, green, turquoise, cobalt, purple — and narrow
bands of diamond chains / rombos outlined in black) and manta-ref-4.png (vertical stripes with S-hook chains
and white braided twill lines). The motifs are geometric and built on a pixel grid like a loom: rombo (diamond)
chains, ganchos en S (S-hooks), zigzag escalonado (stepped zigzag), trenza (black-and-white braid), small
llamas. This board is ONE of five options that show a different DOSAGE and APPROACH; it must commit fully to
its own approach (described below) so the founder can compare and choose.

MANTA PALETTE (pure dyes; use only these for textile elements)
magenta #E4007C · pink #F27BB4 · orange #F26B21 · yellow #FFC41F · green #12A150 · lime #8CC63F ·
turquoise #00A6B4 · cobalt #2546B0 · purple #6C2A8C · textile red #D7261E · white #FFFFFF · thread black #1A1A1A

PRODUCT COLORS (never change meaning)
- Ground (unless the option says otherwise) #F6F4F1, surface cards #FFFFFF with 1pt border #E4DED8, radius 20
- Ink #18221F, secondary #5B6A65, tertiary #6F7975
- ACTION teal #0E6B64 (pressed #0A524D, tint #DCEEEB): the ONLY color of primary buttons and the mic
- Quechua language tag: white text on cinnamon #A85A2A, pill 28pt tall radius 14, Inter 600 13pt
- Castellano tag: #18221F on #ECEFEC
- Audit OK: text #1E7A3E on #DDF2E3. Warning: #8A5100 on #FBEBD0 (always with an icon). Blocked: #B02344 on
  #F8DDE4 — RED MEANS ONLY "Rimay did not say it". Therefore textile red #D7261E and magenta must never sit
  directly next to the green audit row or look like a status; keep 12pt+ of plain ground between any textile
  element and a status element.
- Type: Inter only (SF Pro unavailable). Scale 34 / 24 / 20 / 17 / 15 / 13. Quechua text is one step larger
  than its Spanish companion.
- No blurred shadows, depth from 1pt borders only. No gradients except Chaski's own image background.

CANVAS
Board background #E9E6E1. Three iPhone frames 402 x 874 pt, in one row, 72pt gaps, 120pt margin. Above the row,
the option title in Inter 700 40pt #18221F: "{letra} · {nombre}", and under it in Inter 400 20pt #5B6A65,
max 1200pt wide: "{razon}". Above each frame a label Inter 600 18pt #5B6A65: "1 · Idioma", "2 · Rimay habla",
"3 · Listo para hablar". Each frame: status bar area 54pt (time "9:41" Inter 600 17pt, signal/wifi/battery
glyphs), home indicator 134x5pt radius 3 #18221F, 8pt above the bottom edge. 16pt side margins.

SCREEN 1 · "Idioma" (onboarding step 1 of 3) — Chaski image chaski-presentarse.png
Chaski in its card (the image fills the card, corners radius 28, never on bare white). The wordmark "Rimay" Inter
700 34pt #18221F centered. Three progress dots (8pt, first one teal #0E6B64, others #E4DED8). Question in
Inter 700 24pt #18221F centered "¿Qué idioma habla?" and under it, Inter 700 24pt #A85A2A, "¿Ima simitam
rimanki?". Two option rows, full width, 72pt tall, radius 20, white, 1pt #E4DED8 border, chevron right
#6F7975: row 1 "Castellano" Inter 700 20pt #18221F; row 2 "Runasimi" Inter 700 20pt #A85A2A with
"Quechua chanka" Inter 400 13pt #5B6A65 under it. This is the first impression of the app: it is where the
manta identity should be strongest for this option's dosage.

SCREEN 2 · "Rimay habla" (consultation, Rimay just said it in Quechua) — chaski-hablando.png
Header: left "Rimay" Inter 700 20pt and under it "Consulta · 3:12" Inter 400 13pt #5B6A65 tabular; right a
40pt circle button white with 1pt border and a document icon #5B6A65. Chaski card 200pt centered. Quechua tag
centered. White card: "[Indicación en quechua chanka]" Inter 600 24pt #18221F (keep the square brackets: real
Quechua comes from a native speaker), a 1pt #E4DED8 divider, then "Tome una pastilla dos veces al día, en la
mañana y en la noche, durante siete días." Inter 400 15pt #5B6A65, then "Rimay ya lo dijo en voz alta." Inter
400 13pt #6F7975. Then the AUDIT ROW, the most important element: full width, #DDF2E3, radius 16, padding 14,
a shield-check icon and "Auditado antes de hablar" Inter 600 15pt #1E7A3E, under it four checks "✓ Medicamento
✓ Dosis ✓ Horario ✓ Días" Inter 500 13pt #1E7A3E. Bottom: two buttons side by side 52pt tall radius 26:
secondary white with border "Repetir audio" (speaker icon, Inter 600 17pt #0E6B64) and primary teal "Seguir"
(mic icon, white text). The nurse must read the Quechua card and the audit row in one glance: the textile
must never compete with them.

SCREEN 3 · "Listo para hablar" (consultation idle) — chaski-reposo.png
Same header. Chaski card 240pt centered. "Listo para interpretar" Inter 700 24pt centered. Under it, Inter 400
15pt #5B6A65 centered max 300pt: "Hable en castellano. Rimay se lo dirá en quechua al paciente y le avisará si
algo no se entendió." Bottom area: a 96pt teal #0E6B64 circular mic button with a white mic glyph 36pt; left of
it a 56pt white circle with border and a camera icon, label "Receta" 13pt below; right of it a 56pt white circle
with a checklist icon, label "Resumen" 13pt below. Under the mic "Toque para hablar" Inter 600 15pt #0E6B64,
and under that a pill #ECEFEC radius 16 with a swap-arrows icon and "Habla usted · castellano" Inter 600 13pt
#5B6A65.

THIS OPTION'S DIRECTION — follow it fully, it is what makes this board different from the other four:
{direccion}

HOW TO DRAW THE TEXTILE
Draw every textile element as real vector geometry, not as a photo: stripes are rectangles of varied widths in
the manta palette; motifs are built on a square pixel grid (each "thread pixel" 2–4pt) like a loom — rombo
chains (a diamond outlined in thread black with a colored center, repeating), S-hooks, stepped zigzags, the
black-and-white braid (alternating 2x2 pixel checker), small llama silhouettes 7–9 pixels tall. Crisp, aligned
to the grid, no anti-aliased curves. Never use the reference photos themselves as fills.

TASTE AND BANS
Studio-grade, like a premium iOS health app designed in Lima, not a souvenir shop and not a template. Calm
clinical clarity in the content, Andean identity in the textile. No emoji. No lorem. No stock icon grids. No
blurred shadows. No gradients except Chaski's image. Teal is the only action color. Copy verbatim as written.

VERIFY BEFORE FINISHING
Each frame exactly 402 x 874. Chaski never on bare white. No clipped text. Every primary button ≥ 52pt tall.
The audit row is the most legible element of screen 2 and no textile touches it. The bracketed Quechua
placeholder is kept. The option title and rationale are on the board. Report anything you could not do.
""".strip()

OPCIONES = {
    "A": ("Hilo fino",
          "Una sola hebra tejida y los motivos como íconos: la manta se insinúa, la consulta manda.",
          """MINIMAL ACCENT. The ground stays #F6F4F1 and calm. The manta appears as ONE thin woven line only:
a 6pt band directly under the header (two rows of 3pt thread pixels: a tiny rombo chain in cobalt/turquoise/
yellow on white with black outline) — nothing else striped. The motifs become small marks: a single 12pt rombo
glyph (black outline, magenta center) as the bullet before "Rimay" in the header and as the separator dot in
"Consulta · 3:12"; the three onboarding progress dots become three tiny rombos (filled teal for current,
outlined #E4DED8 for the rest). On screen 1 a 6pt rombo band runs along the bottom edge of the Chaski card,
like the fringe of a lliclla. Total textile area on any screen under 3%. This is the most restrained option:
the founder should see that even a whisper of the manta makes it feel Peruvian."""),
    "B": ("Orillo",
          "La pantalla entera enmarcada por el orillo de una manta: bordes tejidos, interior en calma.",
          """WOVEN FRAME / SELVAGE. Each screen is framed like the edge (orillo) of a manta: a 10pt woven border
runs down the LEFT and RIGHT edges of the screen, full height below the status bar (vertical stripes: 2pt
magenta, 2pt yellow, 3pt black-and-white braid, 3pt turquoise), and a 14pt horizontal woven band sits at the
very bottom above the home indicator (stripes plus a small S-hook chain in yellow on purple). The content area
inside stays white #FFFFFF (not off-white), so the frame reads like a cloth laid around a clean page. The Chaski
card gets a 4pt woven inner border in the same selvage. Side margins grow to 26pt so nothing touches the frame.
Onboarding (screen 1) also gets a 40pt woven band across the top under the status bar, matching the frame.
The founder should feel he is holding a phone wrapped in a manta."""),
    "C": ("Lliclla en la mesa",
          "Un bloque grande de manta arriba, como una lliclla extendida, y tarjetas blancas encima.",
          """BOLD HERO. The top part of every screen is a big block of manta, like a lliclla spread on the
table of the health post: on screen 1 the manta covers the top 46% of the screen (full bleed, from the status
bar down), built faithfully from manta-ref-6: white ground bands alternating with 6–14pt bright stripes and two
18pt motif bands of rombo chains outlined in black; Chaski's card (220pt) sits overlapping the lower edge of the
manta, half on the cloth half on the ground, with a 6pt white outline. On screens 2 and 3 the manta block is
shorter (top 150pt, behind the header and the upper half of Chaski's card); the header text sits on a white
pill so it stays legible. Below the manta everything is calm #F6F4F1 with white cards. The status bar sits on
white. This is the boldest identity of the five while keeping the consultation content untouched."""),
    "D": ("El motivo es la interfaz",
          "Los rombos y zigzags se vuelven los componentes: progreso, medidor de audio, etiquetas, divisores.",
          """MOTIF AS UI. No stripe bands at all. Instead the Andean motifs ARE the interface components, drawn on
the pixel grid in the manta palette but sparse: the onboarding progress is three rombos (current filled
magenta with black outline, others outlined); dividers inside cards are a 4pt stepped-zigzag line in #E4DED8
(quiet); the quechua tag gets a tiny rombo at its left; the Chaski card's corners carry small stepped-corner
notches (escalonado) instead of plain radius; the mic button (still teal #0E6B64, still 96pt) is wrapped by a
ring of 12 small rombos in turquoise/yellow/magenta like a woven medallion; the side buttons are octagonal
stepped shapes instead of circles; the onboarding option rows have a 6pt rombo chain on their left edge (cobalt
for Castellano, cinnamon #A85A2A for Runasimi). On screen 2 the audit row keeps its green, but its four checks
are inside tiny stepped badges. Typography and spacing stay calm. The founder should see the culture in every
component, not as decoration."""),
    "E": ("Fiesta",
          "Fondos de color de la manta con tarjetas blancas encima: cálido y festivo, sin perder la lectura.",
          """FULL COLOR WARMTH. The ground of each screen is a deep manta color instead of off-white: screen 1
deep magenta #B0005F, screen 2 cobalt #1F3A94, screen 3 purple #55216F — each overlaid with a very subtle
tone-on-tone rombo lattice (same hue, +8% lightness, 12% coverage) so the ground feels woven. A 10pt bright
stripe band (yellow/orange/green/turquoise/white) runs under the header. All text on the colored ground is
white; all content sits in white cards (radius 24) so the medical content keeps its calm. The audit row stays
green on its own white card with 12pt of white around it. The primary buttons stay teal #0E6B64 but get a 2pt
white outline so they read on dark grounds; secondary buttons are white. The status bar text is white. Chaski's
card gets a 6pt white frame. This is the warmest, most festive option; it must still pass contrast (white text on
the grounds ≥ 4.5:1)."""),
    "F": ("Faja chumpi",
          "Una faja tejida vertical recorre el costado como un chumpi: identidad fuerte sin tocar el contenido.",
          """VERTICAL SASH (CHUMPI). Inspired by the chumpi (woven belt) and by manta-ref-4's vertical stripes:
a single vertical woven sash 28pt wide runs along the LEFT edge of every screen, full height below the status
bar: vertical stripes (magenta, yellow, turquoise, purple, orange) with a central column of S-hooks in yellow
on purple and a white braid line. Content shifts right (left margin 44pt, right 16pt). On screen 1 the sash
widens to 64pt and shows a column of small white llamas walking up between rombo chains. On screens 2 and 3
the sash carries, at the height of the current step, a small white rombo marker as a "you are here" indicator.
Everything else is calm #F6F4F1 with white cards. Distinctive, asymmetric, unmistakably Andean."""),
}


def main() -> None:
    for letra, (nombre, razon, direccion) in OPCIONES.items():
        texto = BASE.format(letra=letra, nombre=nombre, razon=razon, direccion=direccion)
        (AQUI / f"opcion-{letra}.txt").write_text(texto, encoding="utf-8")
        print(letra, len(texto))


if __name__ == "__main__":
    main()
