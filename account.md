# Cal Hacks 13.0 — hackathon project

> Not a client. A hackathon entry by Freddy + Ricardo, built from this workspace so we can use the
> Loopmind skills and agents (`/software-dept`, `/copywriter`, `/loopmind-pres`, research agents).

## 📍 Estado actual (act. 2026-10-23, Friday 18:30 PT)

- **Product chosen by Freddy (21:30 PT):** A + V2 → "Rimay" (working name), Chanka interpreter for pregnant
  women at the Pilpichaca health post with prescription-photo reading. Product doc: `ideas/producto.md`;
  evidence: `research/papers.md`. Architecture not written yet.
- **Before that:** finalists A (Chanka interpreter for pregnant women) and C (fire last mile), scored
  with `ideas/criterios.md`; analysis in `ideas/decision.md`. Ricardo brings another idea; decided with him.
- **Key fact (2026-10-23):** Freddy's parents speak Quechua; his mother is a nurse at a health post in
  Pilpichaca (Huancavelica), the only Quechua-speaking nurse there. Possible first user, reviewer and
  source of testimony (quote only with her permission).
- **Next milestone:** pick ONE idea tonight (Friday) so Saturday is pure build.
- **Hard deadline:** ✅ VERIFICADA — Devpost submission **Sunday 2026-10-25, 9:00 AM PT**. Judging 10:30–12:30, whole team at the table, live demo required, 2-minute pitch. Source: `context/hacker-guide-calhacks-13.md`.
- **Recommended:** a Devpost draft by Saturday night (the guide says so).
- **Rule that matters:** all code must be started during the event. Nothing pre-built goes in `app/`.

## The event

- Cal Hacks 13.0, Palace of Fine Arts, San Francisco. Fri 2026-10-23 → Sun 2026-10-25.
- Teams of 1–4, add teammates on Devpost.
- General judging: impact, quality, technical complexity, creativity.
- Relevant general prizes: **Best Planet-First Hack**, **Best People-First Hack**.

## Main target — Anthropic track: "Claude for Public Benefit"

*"Build something your community needs. Pick a community: people who share a place, a circumstance or a
need. Find a real problem its people face, then build something with Claude that helps. The narrower,
the better."* (slide, `context/photos/IMG_4766.jpg`)

What they judge (slide `IMG_4767.jpg`):

1. **A named community.** "Students" is too broad; "transfer students at Berkeley trying to find housing" is the register.
2. **A real problem.** You lived it, or you talked to someone who has.
3. **A working high-impact product.** One thing done well and usable on Monday beats a broad demo. **How you plan to measure impact should also be clear.**
4. **Thoughtful use of Claude.** Claude does something that matters to the solution, and **you know where it could go wrong for the people using it.**

Resources: $50 Claude API credits per hacker (QR on the slide, sign up with the Cal Hacks email).
Workshop "Building agents and multi-agent teams with Claude", **Saturday 2026-10-24, 12:30–1:30 PM, The Theater**.
Contact: students@anthropic.com.

## Team

- **Freddy** — from Huancavelica, has lived in Ica and Lima. Builder: full-stack, agents on WhatsApp in
  production (Servi AI), product and pitch.
- **Ricardo Amiel Acuña Villogas** — Data Science at UTEC (Dean's List). AI & Computer Vision Engineer at
  MistiAI. Research on **multi-temporal satellite imagery change detection** (VISAPP 2026 paper, CCIS
  extension), **urban analytics**, crime hotspot detection from street imagery validated against INEI
  and PNP data, XAI, ex-Interbank DS intern. → He owns the data/geo/remote-sensing layer.

## Problem space (Freddy's brief)

Fires in the Peruvian Andes where Freddy is from. Communities didn't know what to do, and neither did
legislators. Interest in the intersection of environmental and political problems, something the team
genuinely cares about because it's home. Ica and other Peruvian cities also on the table.

Research: `research/peru-incendios-andes.md` · tracks to stack: `research/tracks.md` · ideas: `ideas/`.

## Layout

| Path | What |
|---|---|
| `context/` | Hacker guide (PDF + md), photos of the Anthropic slides |
| `research/` | Problem research and sponsor-track research, sourced |
| `ideas/` | Brainstorm and the chosen idea |
| `app/` | The code |

**This whole folder is its own git repo** → `github.com/Freddyx14/cal-hacks` (Freddy's personal account,
private for now; **make public before judging**, and drop `context/photos/` first since they carry the
Claude credits QR). Collaborators invited 2026-10-23: `ricardoamielmai`, `ricardoamiel` (write). The
Loopmind repo ignores the folder. Docs get pushed as they're written (Freddy, 2026-10-23).
