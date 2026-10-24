# Brainstorm 2 — education and political decisions (2026-10-23, 19:40 PT)

Freddy asked for more options beyond fires, especially **education** and **political decisions**.
⚠️ Facts marked *(verify)* are being checked by a research agent → `research/peru-educacion-politica.md`.
Nothing marked *(verify)* goes in the pitch until it's confirmed.

**Time budget:** ~37 h to the Sunday 9:00 AM deadline. Anything that needs a partner, a signed
agreement or data we can't get this weekend is out.

## The lens (same four criteria for every idea)

1. Named community · 2. Real problem we lived or heard first-hand · 3. Works Monday + impact metric ·
4. Claude matters, and we know where it fails.

Plus a fifth, our own: **what is the feedback channel** — how the thing gets better from use.

---

## ✅ Verification update (19:40 PT) — sources in `research/peru-educacion-politica.md`

| Idea | What the check found | Effect |
|---|---|---|
| **P1 budget** | MEF spending data is a **downloadable CSV per year, down to each municipality** (datosabiertos.gob.pe). Huancavelica provincial municipalities had **172 of 274 projects (61%) at 0% progress** by mid-2025, with spending from 16% (Huaytará) to 47.2% (Churcampa). Participatory budgeting is mandatory (Ley 28056); a PUCP study calls 15 years of it "participación decepcionante". The transparency law gives a **10 business-day** deadline. | **Stronger.** Real data, a real number for the pitch |
| **P3 elections** | Regional/municipal elections **already happened on 2026-10-04**. New mayors **take office in January 2027**. Huancavelica's regional seat was decided in the first round. | Voto informado is dead. **But it opens a twist for P1** (below) |
| **E2 Beca 18** | Beca 18-2027 registration **closed 2026-10-16**. The **national exam is Sunday 2026-11-22** (30 days away). **2,065 registered in Huancavelica.** 6,000 scholarships nationwide. | Changes shape: no longer a form helper, now **exam prep for a known, dated cohort** |
| **E1 multigrade** | Rural Huancavelica: 53% of primary schools multigrade, 36% single-teacher (old regional document, directional). National EIB teacher gap of 19,745 (2025). | Problem confirmed; still no test user |
| **P2 bills** | No official Congress API; community projects use an undocumented JSON (14,704 bills). | Doable but fragile at 2 AM |
| National context | The two-chamber Congress was installed 2026-07-27. | Background only |

### Two ideas got sharper

**P1+ · "What did they promise, what did they spend?"** The mayors elected on Oct 4 take office in
January 2027. Their government plans are public (JNE Voto Informado, web only). The outgoing mayor's spending is in
the MEF CSV. So for any Huancavelica district: *"The outgoing administration left 61% of its projects at
0%. The incoming mayor promised X, Y, Z. Here are the questions to ask at the first public meeting."* A
transition is the one moment when citizens have leverage, and it's three months away.
Risk: plans aren't machine-readable (PDFs from a website), so we'd load a few districts by hand for the demo.

**E2+ · Beca 18 exam prep for Huancavelica's 2,065.** A dated cohort, a dated exam (Nov 22), and a
measurable outcome (the preselection list comes out Dec 23). WhatsApp practice that adapts to the student's
weak areas and explains each mistake in Spanish or Quechua. Freddy's own scholarship story fits.
Risk: we must confirm the exam's real format and topics from PRONABEC before writing a single question.
Claude inventing exam questions in the wrong format would hurt the students it's meant to help. And
prep tools exist; the novelty is weaker.

---

## Education

### E1 · The multigrade teacher's copilot
**Community:** teachers in rural Huancavelica schools where one teacher teaches several grades in one room
(*multigrado / unidocente*), often in Quechua (EIB schools) *(verify share)*.
**Problem:** they plan lessons for 3–6 grades at once, with few materials in Quechua and no colleague nearby.
**Product:** WhatsApp the topic ("fractions, 3rd and 5th grade, 2 hours") and get a one-page lesson plan
for both grades at once, mapped to the Currículo Nacional competencies, with a Quechua version of the
activity and a printable worksheet.
**Claude matters:** cross-grade design, bilingual material, aligning to the curriculum.
**Fails when:** Quechua variety is off (Chanka vs Cusco-Collao) or the pedagogy is wrong for the age.
Guardrail: the teacher edits and approves, and every plan cites which competency it targets.
**Metric:** plans used per teacher per week, teacher rating per plan.
**Feedback:** the teacher's edits become the next prompt's examples.
**Risk for us:** no teacher to test with this weekend = weak "real problem" evidence, unless we know one.

### E2 · Beca 18 companion for first-generation students in the provinces
**Community:** 5th-year secondary students in Huancavelica applying to Beca 18 (PRONABEC), the main
national university scholarship *(verify 2027 dates)*.
**Problem:** the process is long, paper-heavy, and online; rural students lack someone who has done it.
Freddy's own story with scholarships and applications fits here.
**Product:** a WhatsApp guide that checks the student's eligibility, builds their personal document
checklist, reminds them of the dates, and practices the preselection exam.
**Note:** this is very close to Anthropic's own example ("help first-generation students through financial
aid forms"). That's good for fit, bad for "did we see something new".
**Fails when:** it misstates eligibility, and a student doesn't apply because of it. Guardrail: rules
come from the official bases only, cited per answer, "confirm with PRONABEC" on edge cases.

### E3 · ECE results the parents can read
**Community:** parents at one school in Huancavelica.
**Problem:** standardized test results (ECE/ENLA) exist per school but are written for specialists.
**Product:** "Your child's school: 3 in 10 kids read at grade level, here is what you can do at home in 15 minutes."
**Weak:** low urgency, nobody acts on Monday. Parked.

---

## Political decisions

### P1 · "¿En qué se gastó mi distrito?" — budget in plain Quechua and Spanish  ⭐
**Community:** comuneros and *dirigentes* in one Huancavelica district who attend the public budget
meetings (*presupuesto participativo*, *audiencias de rendición de cuentas*) *(verify legal requirement)*.
**Problem:** the district gets money (often canon/royalties) and doesn't spend it, or spends it on what
nobody asked for, and the community can't read the MEF data to ask. *(verify Huancavelica figures)*
**Product:**
- Pick your district → Claude reads its real MEF budget execution (MEF publishes it per municipality,
  *verify CSV/API*) and explains it in Spanish and Quechua (audio): what was budgeted, what was spent,
  what's stalled.
- Generate the 3 questions to ask the mayor at the next public meeting, each with its number and source.
- One tap → a formal **access-to-information request** (Ley de Transparencia, Ley 27806 *(verify deadline)*) drafted and ready to file.
**Claude matters:** turns a 40-column budget table into a question a comunero can ask out loud, and
drafts a valid legal request.
**Fails when:** it misreads a number (mixes up budgeted vs spent), and a citizen accuses the mayor on
wrong data. That damages the person, not us. Guardrail: Claude never computes. Code computes and Claude
only explains, every number links to the MEF source row, and the tool never says "corruption", only "not spent".
**Metric:** questions generated and asked, information requests filed, replies received.
**Feedback:** "did the mayor answer?" → what kinds of question get answers.
**Why it's strong:** live real data, a demo works with any district a judge names, and it's politics
from the ground up instead of "chat with the law".

### P2 · The bill that touches my comunidad
**Community:** comunidad leaders in Huancavelica.
**Problem:** Congress passes laws that change their land, water, mining or burning rules, and they find
out after. The new bicameral Congress *(verify)* is producing a new wave of bills.
**Product:** weekly WhatsApp digest in Quechua and Spanish: "3 bills this week that touch comunidades
campesinas, what they change, who proposed them, how to send a comment."
**Data risk:** depends on whether Congress has usable open data *(verify)*. Scraping the Congress site at
2 AM is a weekend-killer.

### P3 · Voto informado for the regional/municipal election
**Community:** first-time voters in Huancavelica.
**Product:** compare candidates' government plans and backgrounds (JNE data) in plain language and Quechua.
**Depends entirely on when the next regional/municipal election is** *(verify)*. If it's not close, it's a
museum piece. Also high-stakes: an AI summarizing candidates touches election neutrality. A judge will
ask about it.

### P4 · The council member's brief (from brainstorm 1, option C)
Kept as an add-on: any of the products above can produce a one-page brief for a regional council member.

---

## Hybrids worth naming

- **Fires × politics (A + P1):** the fire loop from brainstorm 1, plus "your district was budgeted
  S/X for fire prevention and spent S/Y". Strongest emotionally, two data pipelines = more risk.
- **Education × politics (E2 + P1):** the same "explain official stuff in Quechua" engine pointed at two
  audiences. Tempting, but two products is a broad demo. The track rewards **one thing done well**.

---

## Scorecard (my judgment, 1–5)

| Idea | Named community | Lived problem | Live data this weekend | Demo "moment" | Novel | Build risk (5 = safe) |
|---|---|---|---|---|---|---|
| **A · Fire loop** (bs-1) | 5 | 5 | 5 (SERFOR verified) | 5 (alert arrives live) | 4 | 3 |
| **P1+ · Promised vs spent** | 4 | 4 | 5 (MEF CSV verified) | 4 (judge picks a district) | 4 | 4 |
| **E2+ · Beca 18 exam prep** | 5 | 5 | 3 (exam format to confirm) | 3 | 2 | 4 |
| **E1 · Multigrade teacher** | 5 | 3 | 2 | 3 | 3 | 4 |
| P2 · Bills digest | 4 | 3 | 2 (no official API) | 3 | 3 | 2 |
| ~~P3 · Voto informado~~ | — | — | — | — | — | election already happened |

## Recommendation (provisional, until the verification comes back)

1. **Still A (fires)** if you want the strongest story and a live moment. It happened 5 days ago, in your
   region, during an El Niño year, and nobody connects the satellite to the community.
2. **P1 (district budget)** if you two would rather do political decisions. It's the safest build, it uses
   real data, and it has a clean "where Claude fails" story.
3. Don't build a hybrid. Pick one; mention the other as "what's next" in the pitch.

**The question that decides it** isn't which idea is better on paper. It's **which one you two can
put a real person behind by Sunday**: a comunidad leader who receives a fire alert, a comunero who asks
about the budget, or a teacher who tries the planner. One real voice note beats any slide.
