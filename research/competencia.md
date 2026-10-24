# Competition and prior work (2026-10-23, 20:20 PT)

## Satellites on Fire (Argentina) — the strongest comparable
- Founded 2020 by three secondary-school students at ORT Buenos Aires after family friends lost their homes to fires in Córdoba. They interviewed 80+ firefighters and rebuilt the first version because it "was not operationally useful". ([G20 Global Land Initiative](https://g20land.org/blog/satellites-on-fire-a-new-era-of-wildfire-detection/), [The Next Web](https://thenextweb.com/news/satellites-on-fire-wildfire-ai-raises-2-7m))
- **$2.7M seed** (April 2026) led by Dalus Capital, with Draper Associates and others. ([The Next Web, 2026-04-06](https://thenextweb.com/news/satellites-on-fire-wildfire-ai-raises-2-7m))
- Product: AI over imagery from "more than eight satellites across NASA, NOAA, and the European Space Agency, updated as frequently as every five minutes", plus tower cameras, fire propagation modelling and real-time alerts. Claims detection "on average 35 minutes ahead of NASA's FIRMS service". (same)
- Business: SaaS, "$0.02 to $10 per hectare annually". Customers: "forestry companies, agricultural enterprises, energy utilities, carbon credit projects, insurers, and government agencies". Parametric insurance product with AON. (same; [G20](https://g20land.org/blog/satellites-on-fire-a-new-era-of-wildfire-detection/))
- Coverage: 21 countries. **Peru not named** in the sources found.
- Not found: alert channel, language support, any free tier for communities.

## FireSat / Earth Fire Alliance × Asháninka communities (Peru, Sep 2026)
- The Central Asháninka del Río Ene (CARE) joined the FireSat Early Adopter Program, a new satellite constellation built to detect fires. **Amazon, not the Andes.** No channel, language or timeline given. ([La República, 2026-09-02](https://larepublica.pe/sociedad/2026/09/02/satelites-ayudaran-a-comunidades-ashaninkas-a-detectar-incendios-forestales-ante-creciente-alerta-94610))
- The article's own warning: **"la detección no garantiza por sí sola una respuesta efectiva"**, citing connectivity and community capacity to act.

## Student/independent projects on Peru 2026 fires
- `av-gomez/incendios-peru-2026` (Oct 2026, a Python course assignment): FIRMS VIIRS → DBSCAN clusters → **Sentinel-2 dNBR burned area** → WorldPop exposure → 3-day weather forecast. No alerts, no LLM, users are analysts. ([GitHub](https://github.com/av-gomez/incendios-peru-2026))
- `42pe/incendios-peru`: independent fire map (INPE/NASA). ([GitHub](https://github.com/42pe/incendios-peru))
- firemaptoday.com/pe: live fire map for Peru. ([site](https://firemaptoday.com/pe))

## What this means for us

1. **Detection is solved, and it's a VC-funded business.** Satellites on Fire beats NASA by 35 minutes and sells per hectare to whoever can pay. A comunidad campesina in Huancavelica isn't that customer. **Don't compete on detection.**
2. **The last mile is the open problem**, and the press says so in plain words: "la detección no garantiza por sí sola una respuesta efectiva". Our product starts where theirs ends: the alert reaches the comunero in Quechua, the comunero answers by voice, and that answer becomes an official record.
3. **Core 1 (burned area) is not novel.** A course assignment already does Sentinel-2 dNBR on these exact fires. It's useful as a feature (and proves the method works this month), but not as our technical headline.
4. **Core 2 stays the technical headline, framed for the Andes**: in the puna most hotspots are *intentional* agricultural burns (98% human-caused). The question that matters there isn't "is there a fire" (everyone answers that) but **"is this a planned burn or one that's escaping"**. That's the false-alarm problem a last-mile system has to solve, or communities stop trusting the alerts.

**Pitch line:** *"An Argentine startup raised $2.7 million to detect fires 35 minutes before NASA. In Huancavelica, the alert still never reaches the comunero. Detection is solved. The last mile isn't."*
