# Chaski — pitch research for Cal Hacks 13.0 judging

> Researched Saturday 2026-10-24, ~10:50 PT. Every claim cites its source inline. **[UNVERIFIED]** marks anything I could not confirm against a primary source.
> Complements `tracks.md` (Friday night). The big change since then is in §1: **the Anthropic prize is now live on Devpost**.

---

## 1 · Cal Hacks 13.0 judging format, verified now

### The Anthropic prize exists now
- Devpost now lists **"[Anthropic] Claude for Public Benefit"**, 1 winner, prize **"$5000 in Claude credits and 1 year of Claude Max 20x + Office Hours"**. Devpost shows a value of "$4,998 in cash", but that's Devpost's value field. The prize itself is credits + Max + office hours, not cash ([Devpost 13.0](https://cal-hacks-13-0.devpost.com/), fetched 10:53 PT).
- The criteria haven't changed. Still the four on the Hive feed (`updatedAt 2026-10-24T17:46Z`): named community · real problem you lived or heard first-hand · works, "usable on Monday beats a broad demo" · thoughtful use of Claude and "you know where it could go wrong for the people using it" ([Hive prize feed](https://hive.hackberkeley.org/api/live/prizes)). Hive still shows the prize as "Coming soon!". Devpost is ahead of it.
- **Action.** Opt into "Claude for Public Benefit" on the Devpost submission.

### Pitch length: the two sources disagree
| Source | What it says |
|---|---|
| Devpost 13.0 Requirements | "**You will have three minutes to pitch and two minutes for judges to ask questions.** You must have a pre-recorded or live demonstration." ([Devpost](https://cal-hacks-13-0.devpost.com/)) |
| Hacker guide (local PDF) | "We recommend preparing a **two-minute pitch** and any answers to possible questions" … "your pitch will require a **live demo**" (`../context/hacker-guide-calhacks-13.md`, lines 279–294) |
| Past editions | 12.0 and 11.0 both said "two minutes to pitch and two minutes for judges to ask questions" ([12.0](https://cal-hacks-12-0.devpost.com/), [11.0](https://cal-hacks-11-0.devpost.com/)) |
| Cartesia track | "A **2-minute, demo-first** presentation: one complete user flow, then a brief problem + how you built it" ([Hive](https://hive.hackberkeley.org/api/live/prizes)) |

**What to do.** Build a 2:00 core that finishes cleanly. Keep a 3:00 version with the extras (impact metric, failure modes) ready for judges who let you run long. Never plan for 3:00 and get cut off at 2:00.

### Logistics (hacker guide + Devpost)
- Submit on Devpost by **Sun Oct 25, 9:00 AM PT**. It's a hard deadline. Devpost also says "Get to the venue by October 25th @ 8 AM" ([Devpost](https://cal-hacks-13-0.devpost.com/)).
- Table numbers get assigned after 9:00. Be at the table by **10:30**. **2–3 teams share each table.** Judges circulate **10:30–12:30**. You **must stay the whole window**, and if the **whole team isn't there when a judge arrives, you aren't judged** (guide, lines 264–282).
- Devpost needs an image of the project plus the GitHub repo. All work has to be done during the event ([Devpost](https://cal-hacks-13-0.devpost.com/)).
- **A video demo on Devpost is effectively required.** The Functionality criterion says submissions "should also include a clear, meaningful video demo on devpost **for sponsors evaluating asynchronously**" ([Devpost](https://cal-hacks-13-0.devpost.com/)). Some sponsor judges may only ever see the video.
- Closing ceremony is **2:00–4:00 PM** Sunday (guide, line 161).

### General judging criteria (Devpost 13.0, new wording this year)
**Application** (who you help, why they'd actually adopt it) · **Intentionality** ("every design choice should feel purposeful… guided by clear first principles") · **Functionality** (live demo with no major bugs, plus a video) · **Creativity** · **Technical Complexity** ([Devpost](https://cal-hacks-13-0.devpost.com/)). The guide adds that judges "care more about the idea, genuine effort, and thought process behind the project than the final product" (line 290).

### Other tracks we're targeting
- **People-First Social Impact.** Apple Watch SE 3 per member, no specific criteria published, so the general ones apply ([Devpost](https://cal-hacks-13-0.devpost.com/)).
- **Microsoft "Built for the Real World".** 1st place gets a Surface per member, a remote talk to Microsoft's Delta/Frontier FDE team and 1:1 FDE mentorship (Devpost lists $3,800). 2nd is the "Customer Impact Award" (talk + mentorship). Criteria: **customer understanding · measurable usefulness · path from prototype to production · responsible design · end-to-end functionality**. Domains named: "finance, productivity, **healthcare**" ([Hive](https://hive.hackberkeley.org/api/live/prizes), [Devpost](https://cal-hacks-13-0.devpost.com/)).
- **Cartesia.** Prize is "Meta glasses (still TBD)". Four criteria at 25% each: problem & originality · use of Cartesia (core, clear, responsive voice) · execution (main flow works, edge cases) · **impact & responsibility (accessibility, privacy, responsible use)**. Submit a README listing the "Cartesia features used, known limitations", with no keys in the repo. "Live coach or translator" is one of their own suggested ideas ([Hive](https://hive.hackberkeley.org/api/live/prizes)).

### Is there a stage round for finalists?
- **13.0: nothing published.** Neither Devpost, Hive nor the guide mentions finalists or stage pitches. The schedule goes judging 10:30–12:30, then closing 2:00–4:00 (guide).
- **12.0:** "Cal Hacks culminated Sunday with a **final judging round**, where teams of sponsors could listen to project pitches" before winners were picked ([Daily Californian](https://www.dailycal.org/news/campus/world-s-largest-collegiate-hackathon-thousands-of-students-join-12th-annual-cal-hacks/article_9eddbcfc-e3ae-4226-aba0-9a77ea9b8f4f.html)). The 12.0 1st-place team writes that they "didn't get as many judges as the teams around us—which likely meant we didn't make it to the final judging rounds" ([Dylan Lu blog](https://blog.dylanlu.com/cal-hacks-12/)). Read together, this points to multiple judge waves at the table, with strong projects getting callbacks. That's the MLH model, see §3. **[UNVERIFIED for 13.0: whether a callback or second round exists, and how long it runs. Ask in #ask-directors.]**
- So expect **repeat visits**, and give the same pitch at the same quality the 3rd and 5th time.

---

## 2 · What wins

### Cal Hacks
- **12.0 Best Use of Claude: EldaAI** ([devpost.com/software/elda-ai](https://devpost.com/software/elda-ai)). It opens on a lived story: "When my grandmother was diagnosed with dementia…" Voice-first. Claude reads intent and sentiment, and the concrete artifact is daily and monthly summaries for doctors and caregivers. It won only the Claude prize.
- **12.0 Greatest Social Impact + Promise Public Impact Prize: Expungo** ([devpost.com/software/clearpathai](https://devpost.com/software/clearpathai)). Serves a named population (people clearing old convictions). Voice agent plus RAG over statutes, it fills in the actual forms, and privacy is stated outright: "All data is processed entirely in memory."
- **12.0 1st Overall: FaceTimeOS** ([blog.dylanlu.com/cal-hacks-12](https://blog.dylanlu.com/cal-hacks-12/)). The lessons the winner draws: research last year's winners and build something cooler; "have a guy primarily focus on the UI and demo"; and they **cut a flaky feature (clicking) so the demo looked reliable**. The video was recorded 30 min before the deadline.
- **11.0 1st Overall: Duet** (EEG → music). Winner's advice: "Make something that you think is really cool… it will show, and the judges will see it" ([Stanford Daily](https://stanforddaily.com/2024/11/20/stanford-students-win-cal-hacks/)).

### Other majors (health / accessibility / impact)
- **HackMIT 2026 Grand Prize ($8,000) + Elastic: Peel.** A $30 optical dissolution tester for counterfeit pills. It's framed with one WHO statistic ("one in ten medicines in low- and middle-income countries are substandard or falsified"), plus evidence-engine numbers (22,000 recalls, 138,000 NDC products, 84,000 reference pills) and a **$30** BOM against lab equipment that costs "tens of thousands" ([RIT News](https://www.rit.edu/news/rit-student-wins-hackmit-low-cost-medicine-testing-device), [Northwestern](https://www.mccormick.northwestern.edu/news/articles/2026/10/northwestern-engineering-student-wins-overall-track-first-place-at-hack-mit/)).
- **TreeHacks 2026 Grand Prize: Shephard**, a smart cane that steers visually impaired users with computer vision ([Stanford Daily](https://stanforddaily.com/2026/02/15/12th-annual-treehacks/), via search snippet; **[UNVERIFIED in full text]**).
- **PennApps.** Not researched (time budget).

### Anthropic's own hackathons (closest signal for this judge)
- **Built with Opus 4.6** (Feb 2026), judged by the Claude Code team ([claude.com blog](https://claude.com/blog/meet-the-winners-of-our-built-with-opus-4-6-claude-code-hackathon)). 4 of the 5 winners weren't professional developers. Each one opens on a **domain insider's problem with a hard number**:
  - CrossBeam (permits): "90%+ rejection rates… 6-month delays costing $30,000". Its line: "We don't [have a housing crisis]. We have a permit crisis."
  - PostVisit.ai (a cardiologist): "Medicine is based on evidence."
  - TARA (a Ugandan road engineer, **Keep Thinking Prize**): feasibility studies cost "$1–4M, take 9–14 months"; "TARA does it in five hours."
- **Opus 4.8 Build Day** (Jun 2026). The winners stood out on verifiable evidence. Tekton has an "evidence chain" from source to model, and Sim Francisco forecasts elections "within 2–3 percentage points" ([claude.com blog](https://claude.com/blog/meet-the-winners-of-our-claude-opus-4-8-build-day-hackathon)).
- An analysis of the 4.6 results: "expertise trumps coding" ([GIGAZINE](https://gigazine.net/gsc_news/en/20260425-anthropic-hackathon/), secondary source).

**Pattern across all of these.** One named population, a lived or insider origin, one striking number (cost, time or error rate before vs after), a concrete artifact the user walks away with, and explicit privacy and safety handling.

---

## 3 · Pitch craft for 2–3 minute expo judging

**How judging probably works mechanically.** MLH's recommended science-fair format gives **4 min per project per judge** (2 present+demo, 1 Q&A+scoring, 1 travel), **3 judging rounds per project**, and stack ranking where each judge reports their **top 3** ([MLH Judging Plan](https://guide.mlh.com/general-information/judging-and-submissions/judging-plan)). The consequence: you have to land in a judge's personal top 3 out of the ~10–30 tables they see, and being memorable matters more than being comprehensive. **[Cal Hacks 13.0's exact method: UNVERIFIED]**

**Open with the problem, felt.** "Say what the problem is… get your audience of judges sharing your frustration" (Jono Bacon). "Always be very clear about what problem you're solving… often people skip it" (Avi Press, Scarf). YC: "A common error is to avoid describing what you do until far into the presentation," so say it plainly in the first sentence ([JetBrains, notes from the judging table](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/), [YC Demo Day guide](https://www.ycombinator.com/blog/guide-to-demo-day-pitches/)).

**Demo early, and make it the pitch.** "Show something working within about 90 seconds." "Put the judge in the shoes of the user and walk them through what happens." "It should show what your app does in **one flow**. If it's too long, cut down on your features." Bonnie Xu (OpenAI): one clear "oh, this is possible now" moment beats a feature tour, so show the before and after side by side ([JetBrains](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)). The Cartesia track asks for exactly this order: flow first, then the problem and how it was built ([Hive](https://hive.hackberkeley.org/api/live/prizes)).

**Honesty reads as confidence.** "Be very direct about what works, what doesn't, how it works, and how it could be extended. Judges can tell when you're talking around a feature that doesn't exist yet" ([JetBrains](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)).

**De-risk the live demo.** "Mock everything you can… Pre-fill the data. Mock the slow API call. Remove every place the demo could stall" (Colin Lowenberg, Nebius, [JetBrains](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)). The FaceTimeOS team removed the flaky feature outright ([Dylan Lu](https://blog.dylanlu.com/cal-hacks-12/)). YC goes further and says "demos seldom work" on stage ([YC](https://www.ycombinator.com/blog/guide-to-demo-day-pitches/)), but Cal Hacks *requires* a live demo, so the fix is a hardened path, not skipping the demo. Practitioner sources, lower authority: bring a phone hotspot (venue Wi-Fi is the most common failure), warm up model calls before each judge, keep a recorded fallback and *say* it's a recording, and if something breaks, name what failed in one sentence and move on calmly ([Reskilll](https://reskilll.com/blogs/hackathon-demo-presentation-tips-pitch-3-minutes-win-2026/), [DEV checklist](https://dev.to/pranjulrathour/the-hackathon-demo-that-works-live-a-technical-checklist-4k1)) **[low-authority sources]**.

**One number.** YC: "Don't bury the lead," open with your strongest number, "a slide should have one main point," max ~7 words per slide ([YC](https://www.ycombinator.com/blog/guide-to-demo-day-pitches/)). Peel and TARA both ran on a single before/after figure (§2).

**Rehearse out loud, timed.** "Run it out loud at least once… and be sure to time it. The pitch is part of the product" ([JetBrains](https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/)). YC: "Practice. And after you've practiced, practice some more" ([YC](https://www.ycombinator.com/blog/guide-to-demo-day-pitches/)).

**The video counts.** Devpost judges: "The demo video gives the most amount of scope" (Richard, Square). "Ambiguity is a red flag" (Karen, Databricks). Meet every listed requirement, because "it's not sufficient to just build the app" (Warren, Atlassian) ([Devpost blog](https://info.devpost.com/blog/hackathon-judging-tips)).

**Q&A prep.** No authoritative source gives a Q&A protocol. From the criteria, the predictable questions are: how do you know the translation is right · what happens when it's wrong · who is the user on Monday and how do they get it · how do you measure impact · what does Claude do that a plain MT model can't · privacy of patient audio. **[Inference, not sourced]**

---

## 4 · What Anthropic says it values (public statements)

- **The rubric itself** asks you to know "where it could go wrong for the people using it" ([Hive](https://hive.hackberkeley.org/api/live/prizes)). A Claude Builder Club social-impact hackathon (Anthropic-inspired, Devpost) spells out the same idea as **"Ethical Alignment… Did your team think critically about what could go wrong?… intentional design choices to address them"**, next to "Claude is core… not just bolted on" and "whether the solution could realistically reach the people who need it" ([SoCal CBC Hackathon](https://socal-cbc-hackathon.devpost.com/)). It's not Anthropic staff writing for Cal Hacks, but it's the same register.
- **Anthropic 2026 Public Benefit Report** ([PDF](https://www-cdn.anthropic.com/a9ceec76a54d28d27affffcdab6faf7c142cd587.pdf)). The lines that apply directly to Chaski:
  - Under "The work ahead": they are "working to ensure that **Claude models perform well in languages that are underrepresented in their training data**", and AI use is "heavily concentrated in wealthier countries".
  - One of their published standards: "**Make powerful AI affordable and usable in every language and format.**"
  - On their own gap: "we don't yet have evidence that these efforts have had their intended effects… **we have not been active enough in collecting data to measure the results.**" So a project that ships with a way to measure its impact answers a weakness Anthropic admits in writing.
  - Health examples they chose to highlight: IRC in Burkina Faso turning **clinic registers** into dashboards (25,000-case pneumonia spike; 6,000 prenatal visits vs 1,762 attended deliveries), and WHO Africa's Ebola situation reports going "from up to a full day" to "under an hour". Low-resource clinics plus a concrete time or count number is their own storytelling template.
- **Anthropic's own hackathon winners** (§2) reward domain insiders with one hard before/after number, and the "Keep Thinking" prize went to a public-sector tool in Uganda ([claude.com](https://claude.com/blog/meet-the-winners-of-our-built-with-opus-4-6-claude-code-hackathon)).
- Context: Claude for Nonprofits (Aug 2026), Claude Corps, a $200M Gates Foundation partnership covering global health ([search results](https://www.anthropic.com/news/claude-corps); Gates figure **[UNVERIFIED, search snippet only]**).
- **Not found:** any public statement from Anthropic specifically about Cal Hacks 13.0 judging, or any write-up of the 12.0 Claude prize decision.

---

## Implications for our pitch

1. **Opt into "[Anthropic] Claude for Public Benefit" on Devpost now.** It went live today ($5K credits + 1 yr Max 20x + office hours). Also opt into People-First, Microsoft and Cartesia.
2. **Script 2:00 hard, with a 3:00 extension.** Devpost says 3+2, the guide says 2. The 2-minute version has to stand on its own, and the third minute is for measurement plus failure modes.
3. **First 10 seconds: the named community and the lived problem.** For example: "The health post in [district], [N] Quechua-Chanka-speaking patients, one nurse who speaks Spanish." No "rural Peru" abstraction. EldaAI's and CrossBeam's openings are the template.
4. **Demo by 0:30–0:40, one complete flow.** Patient speaks Quechua → nurse sees Spanish → nurse replies → patient hears Quechua. Then the **"oh, this is possible now" moment**: Claude's blind back-translation catches a mistranslation and flags it live. That's the moment the rubric ("knows where it goes wrong") and the Anthropic report (underrepresented languages) both point at.
5. **One number, before vs after.** Pick a single verified figure, e.g. share of patients who can't be attended in their own language, or minutes per consult with vs without an interpreter. Every number must be sourced, and any number we can't source gets cut.
6. **State the failure modes out loud, with the guardrail for each.** ASR errors on Chanka, Claude being confidently wrong in a low-resource language, a medical term with no equivalent, no connectivity. The back-translation audit, confidence shown to the nurse, and "repeat or confirm" fallbacks are the answer. This is criterion 4 and Cartesia's "responsibility" 25%.
7. **"Works on Monday" plus a measurement plan in one sentence.** Who installs it, on what device, offline or online, and what we log (flagged-translation rate, nurse corrections) so impact is measurable. This answers Anthropic's admitted gap ("not active enough in collecting data to measure the results") and Microsoft's "measurable usefulness / path to production".
8. **Harden the demo, don't gamble on it.** Pre-loaded audio clips as a fallback, a phone hotspot, warm the model calls before each judge, cut any flaky feature (the FaceTimeOS move). If something breaks, one calm sentence about what failed, then the backup.
9. **Devpost video and README are pitches too.** Sponsors judge asynchronously from the video. Open the video on the flow and the catch moment. README: where Claude is used and why, Cartesia features used, known limitations, no keys in the repo.
10. **Expect repeat judges and keep the whole team at the table 10:30–12:30.** Same energy on the 5th run. Prep answers to the likely questions: how do you know the Quechua is right · privacy of patient audio · why Claude and not plain MT · who pays and how it scales to other health posts.
