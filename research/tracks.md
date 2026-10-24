# Cal Hacks 13.0 — track research for the Andean wildfire project

> Researched Friday 2026-10-23 (evening, PT). Sources pulled live, URLs inline.
> Hive's prize feed says `updatedAt 2026-10-23T22:47Z`, so tracks marked "Coming soon" may still change over the weekend. **Re-check the Hive feed Saturday morning.**

## Sources

| Source | What it is | URL |
|---|---|---|
| Hive prize feed (JSON) | The official live site's raw data, which is the most current source | https://hive.hackberkeley.org/api/live/prizes |
| Hive prizes page | Same data, rendered (needs JS) | https://hive.hackberkeley.org/prizes |
| Devpost 13.0 | Submission page, prizes as entered, general judging criteria | https://cal-hacks-13-0.devpost.com/ |
| Devpost 13.0 rules | Only the Code of Conduct, nothing about tracks | https://cal-hacks-13-0.devpost.com/rules |
| Local hacker guide | PDF text | `../context/hacker-guide-calhacks-13.md` |
| Fetch.ai event + hackpack | Fetch prizes and weighted criteria | https://www.fetch.ai/events/calhacks-13-0 · https://www.fetch.ai/events/hackathons/calhacks-13-0/hackpack |
| Atlassian challenge doc | Full Atlassian brief | https://docs.google.com/document/d/12Y2Vamxbm9W_l2Eo4AM530R7HfNAYCXI-UI6F6Xnggw |
| Spacetime blog | Sponsor announcement | https://spacetimedb.com/blog/spacetime-at-calhacks |
| Devpost 12.0 + gallery | Calibration, last year's winners | https://cal-hacks-12-0.devpost.com/ · https://cal-hacks-12-0.devpost.com/project-gallery |

> ⚠️ `live.calhacks.io` still serves the **Cal Hacks 12.0** site. The 13.0 live site is **Hive** (`hive.hackberkeley.org`), linked from Devpost.

---

## 1 · The Anthropic track

### What is actually published (verbatim from Hive, 2026-10-23)

- **Title:** `Anthropic` · **Sponsor:** Anthropic · **Prize:** `Coming soon!`
- **Criteria:**

> 1. A named community. "Students" is too broad. "Transfer students at Berkeley trying to find housing" is the right register.
> 2. A real problem. You have lived it, or you talked to someone who has.
> 3. It works. One thing done well and usable on Monday beats a broad demo.
> 4. Thoughtful use of Claude. Claude does something that matters to the solution, and you know where it could go wrong for the people using it.

**Not found anywhere.** The name "Claude for Public Benefit" is not in Hive, Devpost, the hacker guide, or web search. The prize is still "Coming soon!". **There is no Anthropic prize on Devpost yet**, so right now you cannot opt into it there. Ask in `#0-ask-directors` or at the Anthropic table Saturday what it's called and what it pays, and check Devpost again before you submit.

### What the four criteria mean for this project

| Criterion | What it asks for here |
|---|---|
| Named community | Don't say "Andean communities". Name one: e.g. *Quechua-speaking comuneros in [a named district of Cusco/Apurímac/Ayacucho], where farmers burning stubble start most fires in the dry season (Jun–Oct)*. Pick a district with real FIRMS hotspots and say how many. |
| Real problem | Someone on the team has lived it or talked to someone who has. Bring a quote, a news article or a call with someone in the zone. "We read about it" is the weakest version. |
| It works, usable Monday | One flow end to end. A FIRMS hotspot near a named community becomes a Quechua/Spanish alert on WhatsApp or voice, and the person can reply. Leave the legislation summaries and dashboards out unless the main flow is already done. |
| Thoughtful Claude + where it goes wrong | Claude has to do the judgment, not just format text. It decides whether the hotspot is a threat to *this* community (distance, wind, terrain, whether it's a field burn or a wildfire) and writes the alert in plain Quechua/Spanish. **Say the failure modes out loud.** Bad Quechua translation, false alarms that make people ignore alerts, missed fires, FIRMS lag (satellite passes are hours apart), people without signal. Show the guardrail for each one, e.g. a human or municipal brigade confirms before mass send, alerts always state confidence, the source is linked. |

### Calibration — last year's Anthropic winner (Cal Hacks 12.0)

- **12.0 track:** "Claude: Best Use of Claude", **Tungsten Cube + $5000 API credits**. Criteria were Technical Complexity, Creative Use Case and Impact & Practicality, all about **Claude Code** ([Devpost 12.0](https://cal-hacks-12-0.devpost.com/), [12.0 live site](https://live.calhacks.io/prizes)).
- **Winner: EldaAI** ([devpost.com/software/elda-ai](https://devpost.com/software/elda-ai)). Voice-first eldercare app. Claude reads intent and sentiment from speech, Letta keeps behavior memory, Chroma flags changes over time, and it writes daily/monthly health summaries for caregivers. The story started with a grandmother's dementia. It won Claude only.
- **12.0 "Greatest Social Impact" winner: Expungo** ([devpost.com/software/clearpathai](https://devpost.com/software/clearpathai)). Helps a named population (people with old convictions) clear their records. Voice agent, RAG over the statutes of all 50 states, filled-in forms, and it processes everything in memory for privacy. It also won the Promise "Public Impact Prize".
- **Cal Hacks 11.0** had no Anthropic/Claude prize. It was co-hosted by Google and Fetch.ai ([Devpost 11.0](https://cal-hacks-11-0.devpost.com/)).
- **Takeaway.** This year's criteria moved away from "impressive Claude Code use" toward "named community, real problem, works on Monday, knows its failure modes". That's closer to a social-impact rubric than a technical one. EldaAI's pattern still fits: a personal origin story, voice-first, Claude doing the judgment, and a concrete output for a named person.

---

## 2 · "Coming soon" tracks from the guide — current state

| Track | State on Hive / Devpost (2026-10-23) | Prize |
|---|---|---|
| **Convex** | Live now. "The reactive backend platform that keeps up with you and your agents. Database, functions, workflow, sync, search, file storage… All TypeScript, zero glue." No judging criteria. | Hive: **$5,000 cash**. Devpost: Teenage Engineering EP-133 + ESP32-S3 board (shown as $1,308). **They disagree.** Ask. |
| **Elastic** | Hive: "Coming soon!". Devpost names it **"Best use of the Elastic Agent Builder on a Serverless instance"**. Workshop: "Build an Agent That Does the Research: Context Engineering with Elasticsearch". | 1st Meta Quest 3S · 2nd Bose QC |
| **Bright Data** | Live now: **"Best Agent/App Using Public Web Data"**. Bright Data has to be essential ("if live public web data were removed, the product would no longer work"). Must run live and handle blocks, slow responses and empty results. Extra credit for combining tools well. **Disqualified** for scraping behind a login or paywall, non-public personal data, mocked/hardcoded demo data, or a README-only mention. Not on Devpost yet. | 1st $1500 credits + $500 Amazon · 2nd $1000 + $350 · 3rd $500 + $250 |
| **Atlassian** | Live now: **"Best Agent / Best Security Solution for Agents"**. Build a **Forge app** on Jira/Confluence. Track 1 is agents that do the team's work, Track 2 is security for agents. Criteria: Creativity & Quality of Idea · Usefulness & Impact *for Atlassian users and organizations* · Technical Implementation (Forge/Atlassian APIs). 3-min demo video required. Not on Devpost yet. | AirPods Max |
| **AfterQuery** | "Coming soon!" both places. Not on Devpost. | — |
| **Annapurna Labs** | "Coming soon!". Workshop "Technical Domain Talk!". Not on Devpost. In 12.0 it was "Best Use of Annapurna", prize TBD. | — |
| **Fetch.ai** | Live now. Criteria: Functionality & Technical Implementation 25% · **Use of Fetch.ai Technology 20%** (agents registered on Agentverse, Chat Protocol for ASI:One discoverability, **Payment Protocol for monetisation**) · Innovation 20% · Real-World Impact 20% · UX & Presentation 15%. Free month of ASI:One Pro with code `CALHACKS26` / Agentverse Premium with `CALHACKS26AV`. | Hive/Devpost: $1500 / $1000 / $500. Fetch's own page: $1250 / $750 / $500 + 2× $250 Special Recognition. **They disagree.** |
| **Armadin** (Best Security Hack) | Still "Coming soon!". Devpost lists it at $996. | Apple Headphones (maybe hacking tools) |
| **Spacetime** | Live criteria: SpacetimeDB as the **core real-time backend**, with live shared state, multiplayer, or instant sync between users, agents and systems. Examples it names: "shared ops dashboard", "multi-user planning tool", "AI systems coordinating in a persistent world state". "Not just added on the side." No prize amount yet. The blog promises "a special prize for the most impressive use of Spacetime". Not on Devpost yet. | TBD |

### General prizes (Cal Hacks)

- **Best People-First Social Impact Hack** gives an Apple Watch SE 3 per member. **Best Planet-First Social Impact Hack** gives an America the Beautiful Parks Pass per member ([Devpost](https://cal-hacks-13-0.devpost.com/)). **Neither has its own criteria published.** They're judged on the general Devpost criteria below.
- **General Devpost judging criteria, verbatim headings:** **Application** (feasible real-world use; who it helps, what problem, why they'd use it) · **Intentionality** (intuitive, guided by clear first principles, every design choice purposeful) · **Functionality** (live demo without major bugs, *plus a clear video demo on Devpost for sponsors judging asynchronously*) · **Creativity** · **Technical Complexity**.
- Pitch format on Devpost: **3 min pitch + 2 min Q&A**. A pre-recorded or live demo is required. The guide recommends a 2-min pitch and says a live demo is mandatory, so plan on live and keep the video as backup.

---

## 3 · Rules on stacking multiple tracks

- **No published limit was found.** The Devpost rules page holds only the Code of Conduct. The hacker guide says "We highly encourage you to participate in **at least one** sponsor track" and sets no maximum. Hive has nothing on it.
- **What 12.0 shows:** projects won **up to 3 prizes**. Haven won Fetch AI Best Use + YC Iconic Company 1st + LiveKit Best Start-up Idea. Expungo won the Promise Public Impact Prize + Cal Hacks Greatest Social Impact. Several others won 2 (gallery scrape of all 102 winners, [project gallery](https://cal-hacks-12-0.devpost.com/project-gallery)). So stacking sponsor tracks **with** a general prize clearly works.
- Devpost can cap the number of opt-ins per submission. This one may or may not, and you'll only see it on the submission form. **Fill in a draft Saturday night** (the guide recommends this anyway) to see whether there's a cap and which prizes appear. Anthropic, Bright Data, Atlassian and Spacetime aren't on Devpost yet.
- Team size **disagrees between sources.** Devpost says "Team required: 2 to 4 members". The guide says 1–4 and there's a Best Solo Hack. Not a problem if you're 2+.
- Hard rules that apply to every track: all work starts at the event, submit by **Sunday Oct 25, 9:00 AM PT**, be at the venue by 8 AM, and include a GitHub repo and an image. The whole team stays at the table 10:30–12:30.

---

## 4 · Which other tracks to stack, ranked

Base project: Claude turns NASA FIRMS hotspots into Quechua/Spanish alerts by WhatsApp/voice for a named Andean community, with policy summaries as a maybe.

The test for each one: **would this sponsor's judges see their tool as essential, or as glued on?** Every sponsor rubric above explicitly penalizes bolt-ons ("not a bolt-on", "added after the fact", "README only… disqualified", "not just added on the side").

| Rank | Track | Fit | Why (one line) | What you'd need to build |
|---|---|---|---|---|
| 1 | **Anthropic** (primary) | ★★★★★ | The four criteria read like this project's brief: a named community, a real problem, works Monday, knows its failure modes. | Claude does the risk judgment and the Quechua/Spanish alert text. Write the failure modes and their guardrails into the demo and README. |
| 2 | **Best Planet-First Social Impact** (Cal Hacks) | ★★★★★ | Wildfire in the high Andes is a planet-first problem, and it costs no extra integration. | Nothing extra. Lead with the impact numbers: hotspots in the district this season, hectares, people within X km. |
| 3 | **Best People-First Social Impact** (Cal Hacks) | ★★★★ | It also fits, because the users are an underserved Quechua-speaking community. One project probably only wins one of these two, so frame it toward whichever story is stronger. | Nothing extra. The pitch stays on the people. |
| 4 | **Cartesia** | ★★★★ *if* voice is core | Many alert recipients are older or don't read much, and Quechua is mainly spoken. So a voice call is the honest channel and Cartesia's "accessibility" and "impact and responsibility" criteria fit. **⚠️ Check before committing:** whether Cartesia supports Quechua (and Peruvian Spanish) at all. If not, the voice is Spanish-only and the story weakens. Look it up at https://docs.cartesia.ai Saturday morning. | An outbound voice alert that the person can **interrupt and reply to** ("¿es cerca de mi chacra?"), via Twilio or similar plus Cartesia TTS (and STT if available). The README has to list the Cartesia features used. |
| 5 | **Microsoft — Built for the Real World** | ★★★ | "Production-minded AI agent… high-impact domain" and "customer understanding / path to production / responsible design" all fit. No Microsoft-tech requirement is stated. | Nothing technical. A slide on the path to production: who runs it (municipal brigade, COEN/INDECI, SERFOR), cost per alert, how it's deployed. Name one real customer. |
| 6 | **Fetch.ai** | ★★ — risk of bolt-on | It's only credible if you split it into real agents (FIRMS watcher → risk assessor → alert dispatcher) that talk to each other in real time. But 20% of the score is Agentverse registration + Chat Protocol + **Payment Protocol**, and a payment protocol doesn't belong in a free public-safety alert. Judges will notice. | uAgents on Agentverse, Chat Protocol so ASI:One can ask "any fires near Ccatca?", and payment that makes sense somehow (e.g. a municipality paying per subscription). Expect half a day of extra work. |
| 7 | **Bright Data** | ★★ — high bar | Their rule is "if live public web data were removed, the product would no longer work". FIRMS is a NASA API, not web scraping, so the core works without Bright Data and **fails their test**. It only qualifies if scraped data is essential, e.g. live local news, municipal Facebook pages or SENAMHI notices to confirm or dismiss a hotspot. **No mocked data in the demo, or you're disqualified.** | A Bright Data scraper/SERP pulling public Peruvian news and official notices, shown changing a decision live. |
| 8 | **Elastic** (Agent Builder on Serverless) | ★★ | Only fits if the "legislation/policy summaries" part is real. An Elastic Agent Builder agent searching Peruvian wildfire law (Ley Forestal 29763, SERFOR rules, local ordinances) could answer "can I burn my field this week?". That's a second product. | An Elastic Serverless instance with the legal corpus indexed and an Agent Builder agent. It competes with Claude for "who does the reasoning", so be clear about who does what. |
| 9 | **Apify** | ★ | Same problem as Bright Data, and it says "meaningful way". You'd pick one scraping sponsor, not both. Bright Data's rubric is more explicit. | An Apify actor for Peruvian news/alerts. |
| 10 | **Meta — Bringing People Closer Together with AI** | ★ — stretch | WhatsApp is Meta's, but the rubric is "how meaningfully they strengthen human connection". A risk-alert system is about safety, not connection. It could pass only if the core is the *community*: neighbors confirming a fire to each other, brigades coordinating in a group. | WhatsApp Cloud API plus a group/neighbor feature built around connection. The prize is a trip to a Round 2 at Menlo Park. |
| 11 | **Spacetime** | ★ — bolt-on | Real-time shared state would only matter for a live operations dashboard for a brigade. It isn't the core of a push-alert product. | SpacetimeDB as the backend of a brigade dashboard. Skip it. |
| — | **Atlassian** | ✗ | It requires a Forge app on Jira/Confluence for *team workflows*. A rural alert system doesn't live there. Pure bolt-on. | Skip. |
| — | **Convex** | ✗ / ★ | Using it as your backend is legitimate but says nothing about the problem. The rubric is just "use Convex" and the prize amount is disputed ($5k on Hive vs hardware on Devpost). Only enter if you'd use Convex anyway. | Build the backend on Convex. Zero story cost, but zero story gain. |
| — | **Hyphenate, CRS, Visa, Capital One, Coinbase x402, Factory Droid, Notability, Mana, Moss, Bitdeer, SpaceXAI, Creao** | ✗ | They're about finance/commerce, or about a specific dev tool doing the work. All bolt-ons for this project. SpaceXAI (space data + Cursor + Grok API required) mentions NASA data but needs Grok, which conflicts with Claude being the core. | Skip. |

### Recommendation

**Enter 3 + 1.** Anthropic + Best Planet-First (the general social-impact prize that fits the story better) + Microsoft "Built for the Real World" (no extra build, only a production slide). Add **Cartesia** *only if* the voice alert is truly the main channel and Cartesia can handle Quechua or at least natural Peruvian Spanish.

Leave out Fetch, Bright Data and Elastic unless the core flow works by Saturday night. Each one adds about half a day and takes focus away from the one-flow-that-works that Anthropic and the general judges reward. 12.0 shows winners rarely took more than 2–3 prizes, and that came from depth, not from integrating everything.

---

## Open items to confirm on site (Saturday)

1. Anthropic track: official name, prize, and when it gets added to Devpost. Ask at the Anthropic booth or in `#0-ask-directors`.
2. Whether Devpost caps prize opt-ins per submission. Check with a draft submission.
3. Cartesia language support for Quechua (https://docs.cartesia.ai).
4. Convex prize ($5,000 cash vs hardware) and Fetch.ai amounts (Hive vs Fetch page). They only matter if you enter those.
