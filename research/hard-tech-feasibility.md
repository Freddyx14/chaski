# Hard-tech feasibility check (Cal Hacks 2026)

- Date: 2026-10-23 (Friday). Deadline: Sunday 2026-10-25, 9:00 AM PT.
- Scope: a quick ~20-minute pass over three ideas that fit Ricardo's CV and remote-sensing background.
- Method: WebSearch and WebFetch. Every claim links to its source. "Not found" means this pass didn't find it, not that it doesn't exist.
- Caveat: some figures come from search-result summaries or press coverage, not the primary PDF. Those are marked *(secondary)*. Open the primary source before putting any of them on a slide.

---

## Idea 1: Screening Andean children for anemia from a phone photo

### Burden (ENDES 2025, INEI)
- **National: 34.9%** of children aged 6–35 months had anemia in 2025. Rural 43.2%, urban 31.5%. Source: [INEI press release, gob.pe](https://www.gob.pe/institucion/inei/noticias/1392685-el-34-9-de-la-poblacion-de-6-a-35-meses-de-edad-sufrio-de-anemia-en-el-2025) and [Infobae 2026-05-18](https://www.infobae.com/peru/2026/05/18/desnutricion-cronica-y-anemia-infantil-en-peru-cifras-estancadas-y-avances-minimos-segun-la-endes-2025/).
- **Huancavelica: 54.5%** (ENDES 2025) *(secondary, from a search summary)*. Source: [UNICEF Peru / INEI Huancavelica report](https://www.unicef.org/peru/comunicados-prensa/unicef-e-inei-presentan-informe-y-plataforma-sobre-ninez-y-adolescencia). Check this against the ENDES 2025 departmental table.
- Watch out: the new WHO hemoglobin cut-offs change how prevalence is counted in Peru. See [PMC12377884](https://pmc.ncbi.nlm.nih.gov/articles/PMC12377884/).

### Public datasets labeled with hemoglobin
| Dataset | Body site | Size | Labels | License | URL |
|---|---|---|---|---|---|
| Eyes-defy-anemia | Conjunctiva (with palpebral/forniceal segmentation masks) | 218 images | Lab Hb, age, sex | CC BY-SA 4.0 (per Kaggle listing) | [Kaggle](https://www.kaggle.com/datasets/harshwardhanfartale/eyes-defy-anemia) · [IEEE DataPort](https://ieee-dataport.org/documents/eyes-defy-anemia) · [paper](https://www.sciencedirect.com/science/article/pii/S0933365722002299) |
| CP-AnemiC (Ghana) | Conjunctiva, **children 6–59 months** | 710 children (424 anemic / 286 non-anemic) | Hb, age, sex | Not verified (ScienceDirect returned 403) | [paper](https://www.sciencedirect.com/science/article/pii/S2590093523000395) · Mendeley Data (2023) |
| Ghana fingernail | Fingernail color | Same 710-subject cohort *(secondary)* | Hb, anemic/non-anemic | Not verified | [Mendeley 2xx4j3kjg2](https://data.mendeley.com/datasets/2xx4j3kjg2/1) |
| Ghana palpable palm | Palm | Same cohort *(secondary)* | Hb | Not verified | Mendeley Data 2022 (URL not captured) |
| Skin + fingernail Hb dataset | Skin, nails | Not found | Hb | Not found | [ResearchGate](https://www.researchgate.net/publication/384572934_Dataset_of_human_skin_and_fingernails_images_for_non-invasive_haemoglobin_level_assessment) |

The Eyes-defy-anemia images were captured with a magnifying attachment that controls the lighting. A model trained on them will probably lose accuracy on uncontrolled field photos.

### Published accuracy
- **Fingernail app** (Mannino et al., *Nature Communications* 2018). Hb within ±2.4 g/dL, **sensitivity 97%** (95% CI 89–100) at Hb <12.5, n=100 adults. With per-person calibration, ±0.92 g/dL. [Nature](https://www.nature.com/articles/s41467-018-07262-2)
- **Same app in the real world** (Emory, 2025). **89% sensitivity, 93% specificity** *(secondary)*. [Emory news](https://news.emory.edu/stories/2025/05/photo-fingernail-can-now-be-used-detect-and-monitor-anemia-emory-research-finds) · [preprint](https://www.researchgate.net/publication/391720146_Real-world_implementation_of_a_noninvasive_AI-augmented_anemia-screening_smartphone_app_and_personalization_for_hemoglobin_level_self-monitoring)
- **Conjunctiva in real time** (PLOS ONE 2024). **Sensitivity 54.3%, specificity 89.7%** for anemia. At <9 g/dL, sensitivity was 58.3% and specificity 96.5%. [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0302883)
- **Peruvian children's data** (UPCH dataset, YOLOv5 mobile app). **Sensitivity 0.71, specificity 0.89** *(secondary)*. [ResearchGate](https://www.researchgate.net/publication/358956092_Anemia_Detection_Using_a_Full_Embedded_Mobile_Application_with_YOLO_Algorithm)
- **No pooled meta-analysis turned up in this pass.** Results vary widely between studies.

### Apps already in Peru
- **AnemiaApp**, built by MIDIS with Universidad Peruana Cayetano Heredia. It photographs the conjunctiva, a neural network estimates Hb, and it records GPS. [SciDev](https://www.scidev.net/america-latina/news/crean-app-para-medir-anemia-en-ninos/) · [El Comercio](https://elcomercio.pe/juntos-contra-anemia/crean-app-detectar-anemia-foto-parpado-inferior-lima-inteligencia-artificial-noticia-647883-noticia/) · [Andina](https://andina.pe/agencia/noticia-aplicacion-movil-permitira-diagnosticar-anemia-fotos-ojos-y-unas-773928.aspx). Whether it is still deployed and at what scale: **not found**.
- **DetectAnemia by Lolimsa**, a free fingernail-photo app from a Peruvian company. [Diario Correo](https://diariocorreo.pe/tecnologia/detectanemia-la-app-gratuita-que-identifica-signos-de-anemia-con-una-fotografia-noticia/)
- **Verdict**: the data exists and the model is easy to build. The weak points are novelty (there is already a Peruvian app, AnemiaApp) and clinical accuracy (conjunctiva sensitivity of 54–71%). It's medical, so the pitch has to say "screening triage", not "diagnosis".

---

## Idea 2: Houses being built in Lima's debris-flow channels (quebradas / huaicos)

### Building and building-change data
- **Google Open Buildings 2.5D Temporal**. Coverage is listed as "Africa, South Asia, South-East Asia, **Latin America and the Caribbean**". **Annual 2016–2023**, built from Sentinel-2. **Effective resolution 4 m**, delivered as 0.5 m rasters. Bands are building presence, fractional count and height. License CC-BY 4.0 or ODbL. Available in Earth Engine as `GOOGLE/Research/open-buildings-temporal/v1`. [GEE catalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings-temporal_v1) · [Google Research blog](https://research.google/blog/open-buildings-25d-temporal-dataset-tracks-building-changes-across-the-global-south/) · [dataset page](https://sites.research.google/gr/open-buildings/temporal/). *Lima tiles weren't checked one by one. Run a 5-minute GEE query over Lima before committing.*
- **PeruSAT-1** (CONIDA, ~0.7 m panchromatic *(resolution not verified in this pass)*). Free for public bodies, universities and non-profit researchers, but you have to register an institutional user, with a holder, an alternate and a custodian. **Not workable within 48 h.** [gob.pe access](https://www.gob.pe/8392-solicitar-acceso-al-portal-de-imagenes-satelitales) · [download guide](https://www.gob.pe/institucion/conida/campa%C3%B1as/4571-guia-de-solicitud-y-descarga-de-imagenes-del-perusat-1)
- **Sentinel-2 at 10 m**. One pixel is about the size of a small self-built house, so you can see a cluster or the expansion edge, not an individual house. That is why the 4 m Open Buildings product is the useful layer. (This is general reasoning from the 10 m GSD. No source was fetched for it.)

### Hazard layers (CENEPRED / SIGRID)
- The SIGRID library has downloadable Lima documents and maps: [Zonas con peligro potencial de huaycos – Perú (PCM)](https://sigrid.cenepred.gob.pe/sigridv3/documento/879), [Mapa de peligros múltiples](https://sigrid.cenepred.gob.pe/sigridv3/documento/1019), [Zonas críticas por peligros geológicos, región Lima (PDF)](http://sigrid.cenepred.gob.pe/sigridv3/storage/biblioteca//5472_informe-tecnico-zonas-criticas-por-peligros-geologicos-en-la-region-lima.pdf), [Puntos críticos huaico 2023 (PDF)](https://sigrid.cenepred.gob.pe/sigridv3/storage/biblioteca/17368_identificacion-de-puntos-criticos-con-peligro-de-inundacion-flujo-de-detritos-huaico-y-erosion-fluvial-en-los-principales-rios-y-quebradas-2023.pdf), plus EVAR reports for Huaycán/Ate ([example](https://sigrid.cenepred.gob.pe/sigridv3/storage/biblioteca//17826_informe-de-evaluacion-de-riesgo-por-flujo-de-detritos-ambito-3-sectores-catastrales-43-48-huaycan-distrito-de-ate-provincia-y-departamento-de-lima.pdf)).
- **A ready shapefile or WMS of debris-flow polygons for Lima was not confirmed.** Most of what turned up is PDF reports. Plan B is to derive drainage channels from a DEM (Copernicus GLO-30 or SRTM) using flow accumulation. That's a few hours of work.

### El Niño, now and in 2017
- **ENFEN Comunicado Oficial N° 18-2026 (2026-10-16): "Alerta de El Niño Costero"**. Expected to stay at **extraordinary magnitude through January 2027**, then strong until early autumn 2027. Rain above normal forecast on the north and central coast. [ENFEN N°18-2026](https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-18-2026/) · [Infobae 2026-10-17](https://www.infobae.com/peru/2026/10/17/el-nino-costero-se-extenderia-hasta-el-otono-de-2027-segun-el-ultimo-reporte-del-enfen/) · [RPP](https://rpp.pe/peru/actualidad/fenomeno-el-nino-enfen-mantiene-alerta-con-pronostico-de-magnitud-extraordinaria-hasta-el-verano-2027-noticia-1713099). **This makes the idea very timely.**
- **2017 Niño Costero in Lima**: about **24,792 people affected by huaicos** in Lima, worst hit in Chaclacayo, Chosica and San Juan de Lurigancho [El Comercio](https://elcomercio.pe/lima/huaicos-lluvias-han-afectado-25-mil-lima-407381-noticia/). A COEN/INDECI March 2017 report gives Lima 4,972 people left homeless (damnificados) and 1,085 houses collapsed *(secondary)* [Mongabay](https://es.mongabay.com/2017/03/peru-ninocostero-rios/). Nationally, 143 dead and 25,700 houses collapsed *(secondary)* [INDECI compendio 2017](https://cdn.www.gob.pe/uploads/document/file/1048401/20180227171454120200726-15599-1ptpifw.pdf).
- **Verdict: strongest fit for Ricardo.** Multi-temporal building change detection is literally his VISAPP work. Open data covers 2016–2023 at 4 m, the hazard is current (an ENFEN alert is active now) and the human story is clear. Main gap: the latest Open Buildings year is 2023, so 2024–2026 would need Sentinel-2 plus his own model.

---

## Idea 3: Detecting unlicensed water use in Ica from space

### Can Sentinel-2 detect new reservoirs and new fields?
- Water bodies and new irrigated green fields against desert are about the easiest contrast remote sensing gets (NDWI / NDVI). Comparable work: [shrimp-pond mapping with S1+S2 in Tumbes, Peru (IJGI 2026)](https://doi.org/10.3390/ijgi15100440), [land-use and land-cover change in Ica 1990–2020, desert to crops (Springer)](https://link.springer.com/article/10.1186/s12302-025-01181-y), [small water-body change detection in Peru (arXiv)](https://arxiv.org/pdf/2206.09365).
- **No paper specifically on detecting Ica's farm reservoirs with Sentinel-2 was found.**
- ANA itself used satellite imagery to estimate **46,434 ha irrigated in Ica (31,310 in the valley, 15,124 in Villacurí)** *(secondary)*, and uses drones to find illegal wells [Diario Correo](https://diariocorreo.pe/edicion/ica/drones-detectan-pozos-ilegales-en-villacuri-798333/). Wells used without a license rose from 694 to 1,271 in Villacurí/Lanchas between 2009 and 2014 *(secondary)* [Redalyc](https://www.redalyc.org/journal/886/88649163005/). The aquifers have been under a drilling ban since R.J. 330-2011 *(secondary)*.

### Is the water-rights registry (RADA) public and geolocated?
- RADA is ANA's administrative registry of water-use rights, created by D.S. 021-2007-AG and kept up to date by DARH. It **is not constitutive**: a right missing from RADA can still exist. [PeruWeek](https://www.peruweek.pe/ana-registro-administrativo-de-derecho-de-uso-de-agua-rada-no-es-constitutivo-de-derechos/)
- The ANA geoportal / SNIRH publishes **"Derecho de uso de Agua"** and **"Pozos"** (ANA-evaluated wells) layers, including WMS [IDEP WMS ANA](https://www.idep.gob.pe/wms/wms_ana1.html) · [SNIRH access](https://www.gob.pe/86460-acceder-al-sistema-nacional-de-informacion-de-recursos-hidricos) · [ANA geoportal note](https://www.ana.gob.pe/noticia/geoportal-de-la-autoridad-nacional-del-agua) (ana.gob.pe refused the connection during this pass). **How complete or precise the per-right geolocation is was not verified.**
- **Legal and framing risk**: since RADA isn't constitutive, "a field with no matching right" doesn't prove the use is illegal. Frame it as "uses to verify", never "illegal users".

### The Ica–Huancavelica conflict (one sourced description)
- Since the 1950s cotton boom, works at Choclococha lagoon in Huancavelica have transferred about 150 million m³ of water to the Ica valley. When Ica's aquifer dropped in 2007–08, Ica pushed for more transfers. Huancavelica's highland communities (Ccarhuancho, Choclococha, Santa Inés, Pilpichaca) say there is no "surplus" water and that their wetlands are drying out. The Latin American Water Tribunal (2007) concluded the transfer didn't respect an ecological flow. Sources: [LEISA](https://leisa-al.org/web/revista/volumen-31-numero-03/un-conflicto-interregional-por-el-agua-en-los-andes/) · [DESCO](https://www.desco.org.pe/recursos/site/files/CONTENIDO/1118/10_Salazar_PHj17.pdf) · [Salud con Lupa](https://saludconlupa.com/medio-ambiente/choclococha-donde-nace-el-agua-y-nada-regresa/) · [OjoPúblico "Acuatenientes"](https://ojo-publico.com/especiales/acuatenientes/poder-e-impunidad-las-empresas-que-controlan-el-agua-en-el-desierto.html).
- **Verdict**: easy to demo technically (Sentinel-2 change detection on desert). Strong story, but you need a hand-made ground truth, and the claims need careful legal and political framing. The RADA cross-check depends on a layer whose quality nobody has confirmed.

---

## Ranking for a 40-hour build
1. **Idea 2 (huaicos)**: best match with Ricardo's research, open 4 m data for 2016–2023, an active ENFEN alert. Risk: getting hazard polygons (fall back to a DEM).
2. **Idea 3 (Ica water)**: technically the easiest, but its value depends on RADA/SNIRH being usable, which isn't verified.
3. **Idea 1 (anemia)**: data is available and the burden is huge (54.5% in Huancavelica), but AnemiaApp (UPCH/MIDIS) already exists, conjunctiva sensitivity is modest, and the medical claim carries risk.
