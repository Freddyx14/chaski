# Brainstorm — 2026-10-23 (Friday night)

Built on `research/peru-incendios-andes.md` and `research/tracks.md`. Every number below comes from those files.

## First principles: what's actually broken

Three facts from the research carry the whole thing:

1. **The information exists, it just never reaches the people at the fire.** SERFOR's satellites see the hotspots, but its alerts go to officials only. Comuneros fight fires with buckets, branches and wet clothes. In Chupamarca (Huancavelica, 18 Oct 2026) people used irrigation hoses.
2. **What happens on the ground never becomes an official record.** COEN counted 51 fires while SERFOR saw 56 active, and 34 satellite fires never got into the COEN count. A San Martín official said municipal staff "no registran los incendios". Anything left out of the record gets no resources and no policy.
3. **98% of fires are set by people**, mostly pasture burning and slash-and-burn done without firebreaks. The law answers with prison (4–10 years). Nothing tells a comunero how to burn safely.

So the problem is a **broken loop**: satellite → community → official record → policy. Every link exists and none of them connects to the next. One message channel in Quechua and Spanish could close it.

## The options

### A · The loop: community alert + report  ⭐ recommended
**Community:** the comunidades campesinas of one Huancavelica province (Castrovirreyna, where Chupamarca is), and specifically the person each community already designates, its *presidente comunal* or *teniente gobernador*.

- **Inbound alert.** SERFOR heat point → spatial join against the 3,090 community boundaries on SERFOR's server → Claude writes a short WhatsApp alert in Quechua and Spanish, as text plus audio: "There's a hotspot 2 km north of your community, this is what to do now." The advice comes from a fixed official protocol, and Claude adapts it without inventing it.
- **Outbound report.** The leader replies with a voice note in Quechua: "Yes, it's burning, it's reached the puna, we need help." Claude turns it into a structured incident (location, size, injuries, needs) and files it to the municipality / COEN format.
- **Official view.** A map with satellite fires and community-confirmed fires next to the official count. **The gap itself becomes the evidence** a council member can take to the regional government.
- **Impact metrics:** minutes from hotspot to community notified, the share of satellite fires that have a filed report, and the gap closed against COEN.
- **Ricardo:** the spatial join, SERFOR + FIRMS ingestion, filtering false positives (planned burns versus wildfires), and the map.
- **Freddy:** the WhatsApp agent, Claude prompts, voice, and the pitch.

### B · Safe-burn planner (prevention)
**Community:** comuneros who burn pasture in the dry season.
They ask "can I burn my chacra tomorrow?" and get a yes/no from the wind, humidity and SENAMHI red alerts, plus the steps: firebreak, time of day, people on hand. The burn is logged so the municipality knows it's planned, which also stops it from showing up as a false alarm in option A.
*Strong on root cause, but hard to show a live "moment" in a demo, and the advice carries real liability if it's wrong.* Best as **one feature of A** (the "planned burn" message), not as the product.

### C · Council brief
**Community:** regional council members and district mayors of Huancavelica.
Claude reads satellite data, INDECI emergencies and the laws and plans (the Plan Multisectorial 2025–27, the Sep 2025 law) and writes a one-page district brief: what burned, what was reported, where the budget went, and which gaps the law leaves.
*Directly addresses "legislators don't know what to do", but it's a report generator: judges have seen plenty and nobody "uses it Monday".* Best as **A's official view**.

### D · Ica water (alternative topic)
Over-pumped aquifers, falling water tables, the Ica–Huancavelica water conflict. A real problem and personal for you, but there's no live data stream for a weekend demo. Park it.

## Recommendation

**Build A, take B's "planned burn" message and C's gap view as features, and say no to everything else.**

Why A wins on all four Anthropic criteria:
| Criterion | A |
|---|---|
| Named community | Comunidades campesinas in Castrovirreyna, Huancavelica, and their leaders |
| Real problem | Freddy is from Huancavelica; the Chupamarca fire happened 5 days ago, 2026 is an El Niño year with 12 dead so far |
| Works Monday | Live SERFOR data, a real WhatsApp number, a real alert sent during judging |
| Claude where it matters, and where it fails | Quechua ↔ Spanish both ways, voice-note understanding, incident structuring. Failure modes are named and guarded (below) |

### Where Claude can go wrong (this goes in the pitch, it's criterion 4)
| Risk | Guardrail |
|---|---|
| Bad Quechua (Huancavelica speaks Chanka Quechua) | Always send Spanish alongside; audio for people who don't read; flag low-confidence translation; ask Ricardo/Freddy's family to review the fixed templates |
| False alarm (a planned burn reads as a wildfire) | Message says "hotspot detected, can you confirm?", never "fire"; planned burns logged via B suppress the alert |
| Invented safety advice | Claude may only pick and adapt steps from a fixed, cited protocol (INDECI/SERFOR); no free-form advice |
| Satellite lag / SERFOR going dark (it did, Oct 14) | NASA FIRMS as fallback; timestamp every alert with how old the data is |
| No phone signal in the puna | Out of scope for a weekend; say so honestly (SMS fallback = future work) |
| Report lands in a void | The report goes to a named recipient and shows up on the official view; the community gets a receipt |

**Feedback channel** (how it gets better): every alert ends with "¿Es correcto?" (yes/no/voice). Confirmations train the false-positive filter, and corrections to Quechua improve the templates.

### Track stack
Anthropic (main) · Best Planet-First · Microsoft "Built for the Real World" (path-to-production slide). Cartesia only if voice ends up central and they support Quechua (unverified).

## Open questions for the team
1. Which province/district do we name? Castrovirreyna (Chupamarca, recent fire) or your own district?
2. Do you know anyone in a comunidad we could message for a real quote or test before Sunday? A real voice note from a real leader would be the strongest moment in the demo.
3. WhatsApp channel: Meta Cloud API test number (official, quick to set up) or Evolution on the Oracle VM (we already run it). Recommendation: **Meta Cloud API test number**, because it's clean to show judges and has no shared infra with Servi AI.
