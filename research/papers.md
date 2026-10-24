# Papers — what the literature says about our finalists (2026-10-23, 21:40 PT)

**Method.** Four Scopus searches (CSVs and exact queries below), abstracts pulled from OpenAlex by DOI, plus two
OpenAlex keyword searches for recent ACL/arXiv work Scopus misses. **Selection was by title and abstract only;
none of these papers was read in full.** OpenAlex abstracts drop words, so nothing here is a verbatim quote
except where marked as coming from the full Scopus abstract.

| File | Query | Total in Scopus |
|---|---|---|
| `scopus/a-quechua-nlp.csv` | `TITLE-ABS-KEY(quechua) AND TITLE-ABS-KEY("machine translation" OR "language model" OR "speech recognition" OR "text-to-speech" OR "LLM" OR "natural language processing" OR "low-resource")` | 80 |
| `scopus/a-mt-health.csv` | `TITLE-ABS-KEY(("indigenous language" OR "language barrier" OR "limited English proficiency" OR "interpreter") AND ("machine translation" OR "large language model" OR "ChatGPT" OR "LLM") AND ("health" OR "patient" OR "clinical" OR "maternal")) AND PUBYEAR > 2018` | 175 (top 100 by citations) |
| `scopus/v1-bofedales.csv` | `TITLE-ABS-KEY((bofedal* OR "high-andean wetland*" OR "andean peatland*" OR "andean wetland*") AND ("remote sensing" OR Sentinel OR Landsat OR NDVI OR "change detection"))` | 52 |
| `scopus/v2-prescriptions.csv` | `TITLE-ABS-KEY(("handwritten prescription*" OR "medical prescription*" OR "medication label*" OR "drug label*") AND ("OCR" OR "handwriting recognition" OR "deep learning" OR "computer vision"))` | 193 (top 100) |

---

## A · Chanka interpreter for pregnant women — the literature supports it, and the gap is real

**1. The evaluation method already exists, for big languages only.**
Kong et al. (2026, *BMJ Quality & Safety*) translated 50 real sets of emergency discharge instructions (316 sentences)
with ChatGPT-4 and Google Translate into Spanish, Chinese and Russian, had professionals back-translate them, and had
physicians code accuracy and potential harm. Sentence accuracy for GPT: Spanish 97%, Chinese 95%, Russian 89%. But
**16%, 24% and 56% of whole instruction sets had at least one error**, and accuracy fell as the language got less
represented. Their conclusion asks for "further research ... for other languages".
→ **We can run the same protocol for Spanish → Chanka**, with Freddy's mother as the reviewer. Nobody has, as far as
these searches show.

**2. Clinicians already do by hand what our product automates.**
Mehandru et al. (2022, FAccT) interviewed 20 clinicians, including nurses and midwives. Their strategies against language
barriers: **back-translation, testing the patient's understanding, and pre-translated medical phrases**. They
recommend combining machine translation with pre-translated phrases and interactive support for testing mutual understanding.
→ This is our design almost word for word: fixed MINSA warning signs (pre-translated), Claude's back-translation check,
and the teach-back voice reply.

**3. Machine translation is only good enough for simple or pre-translated messages.**
van Lent et al. (2025, systematic review, 26 studies): a shared language works best, then professional interpreters; digital
tools were only sufficient "with simple messages or when messages were pre-translated".
→ Supports scoping to prenatal instructions and warning signs, never free clinical conversation.

**4. Low-resource languages are where LLMs break.**
AmericasNLP shared tasks (Oncevay 2021; Ebrahimi et al. 2024) show Spanish↔Quechua translation is still far from solved;
most systems are trained on Southern Quechua (Cusco-Collao/Ayacucho mix), mostly religious and legal text, no health domain.
OpenAlex adds QueEn (2024, arXiv) and a 2026 AmericasNLP paper on LLM robustness for **Quechua Collao**. **No paper found
evaluating LLMs on Chanka, or on Quechua in any health setting.** (Absence in two databases is evidence about these
searches, not proof the work doesn't exist.)

**5. The voice pieces exist for Chanka specifically.**
- **TTS:** Huamán Curo et al. (2026) built four text-to-speech systems (Tacotron 2, FastPitch, VITS, XTTS v2) for **Chanka
  Quechua (Andahuaylas, Ayacucho, Huancavelica)** from 2,300 recordings, "to provide open resources". → Check tomorrow
  whether the models are actually downloadable.
- **ASR:** Romero et al. (2024) fine-tuned wav2vec2 XLS-R on ~36.65 h for Quechua (AmericasNLP 2022); Zevallos et al. (2022)
  on data augmentation for Quechua ASR. Accuracy depends heavily on data; expect the voice reply to be the weakest link.

**6. Context on indigenous inclusion.** Riemland (2022) on translation technology for Maya languages in Guatemala: tech
alone excludes unless the community leads. → Good line for "where it could go wrong": Freddy's mother reviews, the
community corrects.

## V1 · Bofedales — well studied, the angle would be the water transfer

52 papers. Remote sensing of bofedales with Landsat/Sentinel/NDVI is an established field: Dangles et al. (2017, 1,689
wetlands in Bolivia over 30 years), Chimner et al. (2019, Cordillera Blanca, Peru), Yager et al. (2019, satellite plus
traditional knowledge in Sajama). The closest to our angle is **Chávez et al. (2023)**: NDVI anomalies of 442 bofedales
over 1986–2018 **cross-referenced with water rights granted to mining** in Atacama, Chile.
→ The method is done (in Chile). **Choclococha / Huancavelica does not appear in any title**, so applying Chávez's method
to the Choclococha transfer is new as an application, not as a technique. Lower novelty than A.

## V2 · Reading prescriptions — commodity

193 papers on handwritten prescription and drug-label recognition (CRNN, CNN-BiLSTM, OCR pipelines, 2019–2025), and a 2025
paper already uses generative AI for prescription labels. Today a vision-capable LLM (Claude itself) reads a prescription
photo. **The computer-vision part is not new; the value of V2 is all in the Quechua side**, so it collapses into A.

---

## Bottom line for the decision

- **A gets stronger.** The evaluation protocol is published (Kong 2026), the product design matches what clinicians
  already do (Mehandru 2022), the scope matches what the evidence says is safe (van Lent 2025), Chanka TTS exists
  (Huamán Curo 2026), and **the specific study (LLMs × Chanka × maternal health) doesn't show up anywhere**.
- **V1 is solid but derivative** (Chávez 2023 already did it in Chile).
- **V2 merges into A.**

## References (generated from the Scopus CSV fields; first author only, as Scopus exported them)

- Chávez, R. O., et al. (2023). Andean peatlands at risk? Spatiotemporal patterns of extreme NDVI anomalies, water extraction and drought severity in a large-scale mining area of Atacama, northern Chile. *International Journal of Applied Earth Observation and Geoinformation*. https://doi.org/10.1016/j.jag.2022.103138
- Chimner, R. A., et al. (2019). Mapping mountain peatlands and wet meadows using multi-date, multi-sensor remote sensing in the Cordillera Blanca, Peru. *Wetlands*. https://doi.org/10.1007/s13157-019-01134-1
- Dangles, O., et al. (2017). Ecosystem sentinels for climate change? Evidence of wetland cover changes over the last 30 years in the tropical Andes. *PLOS ONE*. https://doi.org/10.1371/journal.pone.0175814
- Ebrahimi, A., et al. (2024). Findings of the AmericasNLP 2024 shared task on machine translation into indigenous languages. *AmericasNLP 2024*. https://doi.org/10.18653/v1/2024.americasnlp-1.28
- Huamán Curo, E., et al. (2026). Quechua speech synthesizers. *Communications in Computer and Information Science*. https://doi.org/10.1007/978-3-032-20322-9_12
- Kong, M., et al. (2026). Evaluation of the accuracy and safety of machine translation of patient-specific discharge instructions: A comparative analysis. *BMJ Quality and Safety*. https://doi.org/10.1136/bmjqs-2024-018384
- Lomas, A., et al. (2024). Large language models for overcoming language barriers in obstetric anaesthesia: A structured assessment. *International Journal of Obstetric Anesthesia*. https://doi.org/10.1016/j.ijoa.2024.104249
- Mehandru, N., et al. (2022). Reliable and safe use of machine translation in medical settings. *ACM FAccT 2022*. https://doi.org/10.1145/3531146.3533244
- Oncevay, A. (2021). Peru is multilingual, its machine translation should be too? *AmericasNLP 2021*. https://doi.org/10.18653/v1/2021.americasnlp-1.22
- Rao, P., et al. (2024). A comparative assessment of ChatGPT vs. Google Translate for the translation of patient instructions. *Journal of Medical Artificial Intelligence*. https://doi.org/10.21037/jmai-24-24
- Riemland, M. (2022). Translation and technocracy in development: Defining the potentials and limitations of translation technology for Maya inclusion in Guatemalan development. *Linguistica Antverpiensia*. https://doi.org/10.52034/LANSTTS.V21I.729
- Romero, M., et al. (2024). Automatic speech recognition advancements for indigenous languages of the Americas. *Applied Sciences*. https://doi.org/10.3390/app14156497
- van Lent, L. G. G., et al. (2025). Effectiveness of interpreters and other strategies for mitigating language barriers: A systematic review. *Patient Education and Counseling*. https://doi.org/10.1016/j.pec.2025.108767
- Yager, K., et al. (2019). Socio-ecological dimensions of Andean pastoral landscape change: Bridging traditional ecological knowledge and satellite image analysis in Sajama National Park, Bolivia. *Regional Environmental Change*. https://doi.org/10.1007/s10113-019-01466-y
- Zevallos, R., et al. (2022). Data augmentation for low-resource Quechua ASR improvement. *Interspeech 2022*. https://doi.org/10.21437/Interspeech.2022-770

From OpenAlex (not in the Scopus CSVs): QueEn: A large language model for Quechua-English translation (2024, arXiv), https://doi.org/10.48550/arxiv.2412.05184 · On the robustness of morphosyntactic transformation with large language models: The case of Quechua Collao (2026, AmericasNLP), https://doi.org/10.18653/v1/2026.americasnlp-6.12
