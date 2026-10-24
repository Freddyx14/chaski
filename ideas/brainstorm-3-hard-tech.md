# Brainstorm 3 — the "make it technically hard" filter (2026-10-23, 19:50 PT)

## Input: advice from Héctor (HackMIT judge)

1. Don't build an AI to find friends with similar interests (~20% of teams do it).
2. Don't build an AI CFO (~15% of teams do it).
3. Do something **technically hard**. His examples: fine-tune a model to predict a new kind of
   disease, or **make a satellite photograph only the relevant zones instead of everything**.

## What it changes

**The Anthropic track** doesn't score technical difficulty. It scores community, real problem, working
product, and thoughtful Claude. **The general prizes do** (overall, Most Technically Complex), and so does
every judge's first impression. The best entry is both: **a hard technical core that exists because
the community needs it, with Claude doing the part only a language model can do.**

Run the options through that filter:

| Option | Technical depth | Verdict |
|---|---|---|
| Fires (A) as written | Data join + WhatsApp agent. Medium. | Needs a hard core |
| Promised vs spent (P1+) | CSV + explanation. Shallow. | Falls to Héctor's filter |
| Beca 18 exam prep (E2+) | Adaptive quiz. Shallow, and crowded. | Falls |
| Multigrade teacher (E1) | Prompting. Shallow. | Falls |

Héctor's own example is a satellite problem, and **Ricardo's published research is exactly that**
(multi-temporal satellite change detection, VISAPP 2026). The fire idea is the only one where the hard
part and the community need are the same thing.

## Fires, with a hard core: three candidate cores (Ricardo decides feasibility)

**Core 1 · Burn-scar change detection per community.**
Sentinel-2 images before and after a fire → a change-detection model segments the burned area → hectares
lost per comunidad campesina, independent of whether anyone reported it. That's the official record the
state is missing (COEN counted 51 fires while SERFOR saw 56). Ricardo's paper *is* change detection; the
new part is adapting it to burn scars in the puna.
*Feasibility to check:* a labeled burn-scar dataset to fine-tune on, and cloud-free Sentinel-2 scenes of
Huancavelica in Oct 2026.

**Core 2 · Planned burn or runaway fire?**
Every satellite hotspot looks the same, but a comunero burning pasture and a fire escaping into the
puna are completely different emergencies. Train a classifier on SERFOR's historical records (97,376 fires
and burn scars on its map server) plus weather (wind, humidity) and terrain to predict **which hotspot
becomes a wildfire**. That solves the false-alarm problem from brainstorm 1 with a model instead of a rule.
*Feasibility to check:* whether SERFOR's records carry an outcome label (size, duration, damage) we can
train against.

**Core 3 · Héctor's literal example: decide where to look.**
Score every community's risk each day (dry vegetation index, wind, recent hotspots, burning season) and
pick the few zones worth high-resolution imagery or a field check today. Interesting, but the demo
is harder to show live, and the user is an agency, not the community.

## Recommendation

**Core 2 inside the fire loop** is the best fit. It's a real model trained on real Peruvian data, it
directly decides **whether a family in the puna gets woken up by an alert**, and it gives Claude a
precise job: explain the model's risk call in Quechua and Spanish, take the community's voice reply, and
file the report. **Core 1 as a stretch** if Ricardo has a pretrained change-detection model he can
adapt fast; the "hectares nobody reported" number is the political punchline.

Where it fails, in the pitch: the model misses a runaway fire (false negative). Guardrail: below the
threshold we still log it and show it on the map, we just don't wake anyone. And we report the model's
recall on held-out 2026 fires, honestly.

## Division of work
- **Ricardo:** model (Core 2, then Core 1 if time), SERFOR/FIRMS ingestion, map.
- **Freddy:** Claude layer (risk explanation, Quechua/Spanish, voice-note intake, report filing), WhatsApp, pitch.
- **Meeting point (Saturday 9 AM):** a JSON contract per hotspot `{id, lat, lon, community, risk_score, features, timestamp}`.
