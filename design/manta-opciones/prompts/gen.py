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
    "G": ("Fiesta geométrica",
          "D sobre E: los motivos hechos interfaz encima de los fondos de color de la manta.",
          """D + E, FREDDY'S EXPLICIT ASK. Take option E's grounds — screen 1 deep magenta #B0005F, screen 2 cobalt
#1F3A94, screen 3 purple #55216F, each with a subtle tone-on-tone rombo lattice (same hue +8% lightness, 12%
coverage) — and put option D's motif-as-interface components on top: onboarding progress = three rombos (current
filled yellow #FFC41F with thread-black outline, others white outline); Chaski's card has stepped (escalonado)
corners instead of round ones, with a 4pt white stepped frame; the quechua tag has a tiny rombo at its left;
dividers inside cards are a 4pt stepped zigzag in #E4DED8; the mic (teal #0E6B64, 96pt, 2pt white outline) is
wrapped by a ring of 12 small rombos in yellow/turquoise/pink/white; the side buttons are white stepped octagons;
the onboarding option rows carry a 6pt rombo chain on their left edge (cobalt for Castellano, cinnamon #A85A2A for
Runasimi). Every text on a colored ground is white (≥4.5:1). All medical content stays in white cards (radius 24),
and the audit row sits on its own white card with 12pt of white around it, no motif touching it. Festive AND
geometric: the founder's two favourites in one."""),
    "H": ("Tocapu",
          "Cada componente vive en una celda de tocapu: la cuadrícula inca de símbolos, multicolor.",
          """TOCAPU GRID AS THE COMPONENT LANGUAGE. Tocapus are the square symbol cells of Inca tunics: a grid of
squares, each holding a different small geometric sign (stepped cross, checkerboard, concentric square, diagonal
bands, small rombo, S-hook), each cell a different solid manta color (magenta, yellow, turquoise, cobalt, orange,
green, purple) with thread-black or white signs. Use this everywhere, sparsely but clearly: a header row of 8
tocapu cells (each 20pt) under the header instead of a stripe; Chaski's card sits inside a 6pt tocapu border
(cells of 6pt); the onboarding progress is three tocapu cells (current filled, others outlined); the quechua
tag carries a tocapu cell as its leading icon; the Receta and Resumen side buttons are 56pt square tocapu cells
(rounded 10) with the camera and checklist glyphs inside; the mic stays a teal circle but stands on a 3x3 tocapu
plinth band beneath it; the onboarding option rows each start with a 40pt tocapu cell icon (cobalt cell with a
white stepped sign for Castellano, cinnamon cell with a white rombo for Runasimi). Ground stays #F6F4F1 with white
cards. More colors and more signs than D, organized in a strict grid so it stays calm."""),
    "I": ("Chakana",
          "La cruz andina escalonada ordena todo: el anillo del micrófono, el marco de Chaski y el progreso.",
          """CHAKANA + ESCALONADO. The chakana (stepped Andean cross, three steps per arm, with a central circle or
square) is the hero sign. The mic button: the teal #0E6B64 circle (96pt) sits at the center of a 150pt chakana
outline drawn in 4pt stepped lines of alternating turquoise #00A6B4 and yellow #FFC41F, with a magenta #E4007C
inner step. Chaski's card is a stepped (escalonado) frame: corners cut in 3 steps, 4pt multicolor stepped border
(cobalt, yellow, magenta per step). The onboarding progress is a single chakana whose arms fill in color as the
steps advance (1 of 3 arms + center filled). The header has a small 18pt chakana glyph before "Rimay". Dividers
inside cards are a thin stepped line (escalera) in #E4DED8. The onboarding option rows have a stepped left edge
(three steps) in cobalt / cinnamon. Section labels and the "Habla usted · castellano" pill use stepped ends
instead of round ends. Ground #F6F4F1, white cards, the audit row untouched. More color than D (four manta
colors in every stepped element), one disciplined motif family."""),
    "J": ("Pallay",
          "La densidad del cinturón tejido aplicada a los componentes: bordes llenos de motivos en botones y etiquetas.",
          """PALLAY DENSITY. Pallay is the dense pick-up weave of belts and mantas: tight rows of tiny motifs.
Apply that density as BORDERS of the components themselves, not as background: the primary "Seguir" button and the
mic button get a 6pt pallay rim (micro rombos and S-hooks in yellow/magenta/turquoise on thread black, pixel 2pt);
the onboarding option rows get a 6pt pallay band along their top edge (each row a different color family:
cobalt/turquoise for Castellano, orange/magenta for Runasimi); the quechua tag is a short woven pallay strip with
the label on a cinnamon center; the audio/level elements and the progress become pallay strips that fill with
color as they advance (3 segments, current filled multicolor, rest #E4DED8 checker); Chaski's card has a 10pt pallay
band along its bottom with small llamas and q'antu flowers (pixel motifs) on thread black; a 12pt pallay belt with
ganchos en S runs under the header. Ground #F6F4F1, white cards, the audit row plain and untouched with 12pt of
calm around it. The most motif-dense option, but every motif lives on an edge so text areas stay clean."""),
    "K": ("Lliclla geométrica",
          "D más C: componentes de motivo y un héroe de lliclla repleto de figuras andinas.",
          """D + C, MY BEST BET. Screen 1 gets a big lliclla hero covering the top 44% (full bleed): white ground with
bright stripe bands and FIVE different motif bands, each a different family — rombo chain, ganchos en S, stepped
zigzag (qenqo/river), a row of small llamas with q'antu flowers, an eight-pointed star (estrella de ocho puntas)
band — drawn crisp on a pixel grid in the manta palette with thread-black outlines; Chaski's card (220pt, stepped
corners) overlaps its lower edge with a 6pt white frame. Screens 2 and 3 get a shorter lliclla (top 140pt behind the
header, header text on a white pill) with two motif bands. Then D's component language below: progress as three
rombos, the quechua tag with a tiny rombo, stepped-zigzag dividers in #E4DED8, the mic wrapped in a ring of 12
rombos (turquoise/yellow/magenta), stepped-octagon side buttons, option rows with a 6pt rombo chain on the left
edge. Calm #F6F4F1 ground and white cards below the hero; the audit row untouched with 12pt of calm."""),
}


def main() -> None:
    import sys
    solo = set(sys.argv[1:])
    for letra, (nombre, razon, direccion) in OPCIONES.items():
        if solo and letra not in solo:
            continue
        texto = BASE.format(letra=letra, nombre=nombre, razon=razon, direccion=direccion)
        (AQUI / f"opcion-{letra}.txt").write_text(texto, encoding="utf-8")
        print(letra, len(texto))


if __name__ == "__main__":
    main()
