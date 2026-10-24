# Peru: civic data, elections and education in Huancavelica (fact-check)

Fact-check for Cal Hacks 13.0, Anthropic "Claude for Public Benefit" track. Researched Friday 2026-10-23 (~25 min budget). Every fact has its URL inline. Where something is marked **NOT FOUND** or **UNVERIFIED**, don't put it on a slide as fact.

Caveat on method. Most sources are press articles found by web search. Several primary government sites (umc.minedu.gob.pe, datosabiertos.gob.pe, gob.pe/pronabec) were blocked from this machine during the session by a firewall page, DNS failure or HTTP 418. So some primary figures could not be opened directly. Each one is flagged below.

---

## 1. Elections

**Regional and municipal elections (ERM 2026): ALREADY HAPPENED, Sunday 2026-10-04.**
- They elected 25 regional governors, 25 regional councils, 196 provincial mayors and 1,696 district mayors, all for the 2027–2030 term. Source: [Wikipedia ERM 2026](https://es.wikipedia.org/wiki/Elecciones_regionales_y_municipales_de_Per%C3%BA_de_2026), [Infobae guide](https://www.infobae.com/peru/2026/08/31/elecciones-municipales-y-regionales-2026-guia-completa-de-los-comicios-del-domingo-4-de-octubre-en-peru/), official site [erm2026.onpe.gob.pe](https://erm2026.onpe.gob.pe/).
- More than 26 million voters. Source: [Infobae](https://www.infobae.com/peru/2026/08/31/elecciones-municipales-y-regionales-2026-guia-completa-de-los-comicios-del-domingo-4-de-octubre-en-peru/).
- **Regional runoff (Segunda Elección Regional): Sunday 2026-12-06.** It applies only where no governor ticket got ≥30% of valid votes. The JNE moved it from Nov 29 at ONPE's request. Source: [El Peruano](https://elperuano.pe/noticia/306580-jne-oficializa-el-6-de-diciembre-como-fecha-de-la-segunda-vuelta-regional), [RPP](https://rpp.pe/politica/elecciones/elecciones-2026-jne-acordo-que-el-6-de-diciembre-se-realizara-la-segunda-vuelta-regional-noticia-1711821).
- **Huancavelica**:
  - The early flash count had Juan Carlos Común (Alianza para el Progreso) at 29.5% and Samuel Morán (Perú Primero) at 29.3%, which pointed to a runoff ([Caretas](https://caretas.pe/politica/jne-fija-fecha-para-la-segunda-vuelta-que-regiones-podrian-definir-a-sus-gobernadores-en-diciembre/)).
  - The full ONPE count reported by La República gives APP 33.95%, Perú Primero 31.39% and Acción Popular 16.71%. That makes Común the "virtual" governor, above the 30% line, so **probably no runoff** ([La República](https://larepublica.pe/politica/2026/10/04/resultados-onpe-huancavelica-2026-quien-es-el-virtual-gobernador-regional-55658)).
  - UNVERIFIED: JNE proclamation status. Check the ONPE/JNE results before claiming it.
- Pitch implication: the new authorities take office in **January 2027**. The four-year term starting then is when a civic-accountability tool for municipalities would matter.

**General election 2026**
- First round was in April 2026. The presidential runoff was Sunday 2026-06-07, Keiko Fujimori vs Roberto Sánchez. Source: [El Comercio](https://elcomercio.pe/politica/elecciones/resultados-segunda-vuelta-elecciones-peru-2026-en-vivo-conteo-onpe-flash-electoral-y-quien-gana-entre-keiko-fujimori-y-roberto-sanchez-hoy-7-de-junio-noticia/).
- At 100% of tally sheets counted, Fujimori had 50.14% and Sánchez 49.87% of valid votes ([TV Perú](https://tvperu.gob.pe/noticias/politica/resultados-elecciones-2026-segunda-vuelta-keiko-fujimori-roberto-sanchez)). The JNE proclaimed Fujimori on July 3 ([Wikipedia EG 2026](https://es.wikipedia.org/wiki/Elecciones_generales_de_Per%C3%BA_de_2026)).
- The new Congress is bicameral: **60 senators and 130 deputies**, period 2026–2031.
  - It was formally installed on **Monday 2026-07-27**. Senators were sworn in on July 24 and the chambers elected their boards on July 26.
  - This ends 33 years of a single-chamber Congress, under constitutional reform Ley 31988.
  - Sources: [Infobae](https://www.infobae.com/peru/2026/07/27/instalacion-del-congreso-de-la-republica-en-vivo-hoy-lunes-27-de-julio-camara-de-senadores-y-diputados-inician-funciones/), [El Peruano](https://elperuano.pe/noticia/301040-instalan-el-congreso-bicameral).
  - Fujimori took office one day later, on 2026-07-28 ([Infobae/agencias](https://www.infobae.com/america/agencias/2026/07/27/senado-y-camara-de-diputados-de-peru-se-instalan-un-dia-antes-de-toma-de-mando-de-fujimori/)).

## 2. JNE Voto Informado / Declara+

- **Voto Informado** ([votoinformado.jne.gob.pe](https://votoinformado.jne.gob.pe)) is a free public **web** platform. It has each candidate's hoja de vida (sworn CV), the government plans and their summaries, and the party, and you can filter by your electoral district. It was live for ERM 2026. Sources: [JNE on gob.pe](https://www.gob.pe/institucion/jne/noticias/1396232-jne-presenta-la-plataforma-voto-informado-con-hojas-de-vida-de-candidatos-y-planes-de-gobierno), [Andina](https://andina.pe/agencia/noticia-elecciones-2026-jne-habilita-plataforma-voto-informado-datos-candidatos-1059098.aspx).
- The **Declaración Jurada de Hoja de Vida** is mandatory under Ley 28094 and is filed through **Declara+** at [declara.jne.gob.pe](https://declara.jne.gob.pe) ([gob.pe orientación](https://www.gob.pe/99085-declaracion-jurada-de-hoja-de-vida)). The historical CVs are on [plataformahistorico.jne.gob.pe](https://plataformahistorico.jne.gob.pe/OrganizacionesPoliticas/HVCandidato). Electoral history going back to 1931 is on **Infogob** (infogob.jne.gob.pe).
- **Form**:
  - Web pages per candidate, plus government plans as PDFs.
  - **NOT FOUND:** an official documented public API or bulk CSV download for candidate CVs. Assume scraping the web platform's JSON is the path, and verify ToS and robots before the demo.

## 3. MEF budget data

- **Consulta Amigable** (MEF's web tool for querying budget execution) can be browsed by level of government → municipality → PIA/PIM (opening and modified budget), compromiso, devengado (accrued spend) and girado (disbursed). The MEF portal is mef.gob.pe → Seguimiento de la Ejecución Presupuestal.
  - UNVERIFIED: the exact deep link wasn't opened this session. It is usually `https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx`. Confirm it before citing.
- **Bulk CSV: YES.** The dataset "Presupuesto y Ejecución de Gasto – Devengado Mensual" is on the national open-data portal.
  - One CSV per year, 2012 to the current year, for the national, regional and **local governments (municipalities)**.
  - Fields include PIA, PIM, compromiso, devengado and girado by executing unit. The source is Consulta Amigable itself.
  - Dataset: [datosabiertos.gob.pe dataset](https://datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto-%E2%80%93-devengado-mensual).
  - Example file: [2025-Gasto-Devengado-Mensual.csv](https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto-%E2%80%93-devengado-mensual/resource/b748a24e-1511-476d-852b).
  - MEF mirror: [datosabiertos.mef.gob.pe](https://datosabiertos.mef.gob.pe/organization/presupuesto-publico?page=3).
  - Files are large because they are national. Pre-filter to Huancavelica's department code.
- **API**:
  - The portals are CKAN/DKAN-style, and a CKAN `datastore_search`-type API is *reported* by third parties ([gestionpublicaperu.com.pe](https://gestionpublicaperu.com.pe/abierto/)).
  - UNVERIFIED: no official API documentation was opened. For a hackathon, download the CSV.
  - There is also a community MCP server for MEF subnational efficiency ([glama.ai listing](https://glama.ai/mcp/servers/JL-VALERO/mef_subnational_efficiency_mcp)). It is unvetted.
- **Huancavelica figures (sourced)**:
  - By 2025-06-30, the 7 provincial municipalities had 274 investment projects planned, and **172 (61%) were at 0% progress**. Source is MEF data reported by [Infoandes, 2025-07-03](https://infoandes.pe/archivos/huancavelica-municipios-con-baja-ejecucion-de-gasto-tienen-172-de-proyectos-de-inversion-con-0-de-avance/).
  - Mid-year execution by province, all below 50%:

    | Province | Execution | PIM |
    |---|---|---|
    | Huaytará | 16% | S/9.47M |
    | Castrovirreyna | 25% | — |
    | Huancavelica | 28% | — |
    | Angaraes | 29.5% | — |
    | Tayacaja | 30.1% | — |
    | Acobamba | 32.5% | — |
    | Churcampa | 47.2% | — |

  - Same source: the investment budget of Huancavelica's local governments rose 53.3% versus 2024, and 2024 execution was **54.3%**, among the lowest in the country.
  - National context: at mid-2025, municipalities had executed only 30.3% of their investment budget, and 358 municipalities were below 10% ([Gestión](https://gestion.pe/economia/a-falta-de-seis-meses-para-que-acabe-el-2025-hay-358-municipalidades-que-no-ejecutan-ni-el-10-de-sus-recursos-para-proyectos-noticia/)).
  - Canon: Huancavelica received only **S/417 thousand** in mining canon (the share of mining revenue transferred to regions) in Jan–Apr 2026, per the MINEM bulletin ([Infobae](https://www.infobae.com/peru/2026/07/08/ancash-arequipa-y-tacna-lideran-lista-de-regiones-que-recibieron-mas-canon-minero-entre-enero-y-abril-de-2026/)). So Huancavelica is **not** canon-rich, and the framing should be execution capacity, not canon dependence.
  - Nationally in 2021, canon, sobrecanon and regalías were 34% of local governments' budget ([ComexPerú canon report](https://www.comexperu.org.pe/upload/articles/reportes/reporte-canon-001.pdf), via search snippet).

## 4. Presupuesto participativo and rendición de cuentas

- **Legal requirement: YES.**
  - **Ley 28056**, Ley Marco del Presupuesto Participativo ([text, OAS](https://www.oas.org/juridico/spanish/per_res19.pdf)), regulated by D.S. 142-2009-EF ([MEF](https://www.mef.gob.pe/es/normatividad-sp-9867/por-tema/presupuesto-participativo/7364-d-s-n-142-2009-ef-4/file)).
  - Regional and local governments must run the participatory process.
  - The head of the budget is **obligated to report back periodically** to the participatory bodies on the agreed projects and the total budget.
  - Civil society elects oversight committees (Comités de Vigilancia).
  - UNVERIFIED: the regional "audiencias públicas" (at least two a year) come from Ley 27867, the regional governments law. The source was not opened this session.
- **Does participation happen? Weakly. Sourced critiques:**
  - PUCP study: *"Participación decepcionante: una evaluación de quince años de la Ley Nacional del Presupuesto Participativo"* ([PUCP repositorio](https://repositorio.pucp.edu.pe/items/2560dfc3-9257-4ecb-9629-fcdb3ab928ad)). It attributes the limited results to problematic design that restricts civil-society participation, low political support from authorities, and the law's origin as a technocratic tool.
  - Local evidence: in 2014–2016 processes, participating agents averaged about **50 people**, and there was gradual "disenchantment" and falling participation ([PUCP thesis, Mariano Melgar case](https://tesis.pucp.edu.pe/items/ff164261-de22-4388-b0a6-49bd7b4b5a30), via search snippet). Agents only *prioritize* projects. Execution can differ, and decisions fall to social leaders rather than citizens.

## 5. Education in Huancavelica

**Learning results (ENLA 2024, 4th grade primary, census)**
- National: **32.8% satisfactory in Reading** (33% in 2023) and **29.5% in Math** (22.5% in 2023). Sources: [Infobae](https://www.infobae.com/peru/2025/04/09/solo-3-de-cada-10-escolares-de-4-grado-entienden-lo-que-leen-segun-evaluacion-nacional-de-aprendizaje-2024/), [Minedu](https://www.gob.pe/institucion/minedu/noticias/1142140-enla-2024-532-000-escolares-de-4-de-primaria-muestran-recuperacion-sin-precedentes-en-lectura-y-matematica), UMC [ENLA executive summary](http://umc.minedu.gob.pe/wp-content/uploads/2025/04/Resumen-ejecutivo-ENLA-2024.pdf).
- Huancavelica took part with 178 schools and 2,685 4th-grade students, 98.1% coverage. Source: UMC [technical report RT_ENLA2024](http://umc.minedu.gob.pe/wp-content/uploads/2025/07/RT_ENLA2024.pdf), which covers logistics only, no results.
- **Huancavelica % satisfactory: NOT VERIFIED.**
  - Two search snippets disagree. One says Reading averaged 460 and Math 471 (DRE Huancavelica). Another says 36.2% satisfactory in Reading with an average of 498, which would be *above* national and looks doubtful.
  - The regional results page (umc.minedu.gob.pe/resultadosenla2024/) was blocked from this machine.
  - **Open it in a browser before quoting any Huancavelica ENLA number.**

**Multigrade and single-teacher schools (rural)**
- 80.5% of Huancavelica's 2,501 schools are rural.
- In rural areas:
  - Initial education: 87% single-teacher (unidocente), 9% multigrade.
  - Primary: 36% single-teacher, 53% multigrade.
  - Only 4% of initial and 11% of primary are complete multi-teacher schools.
- The single-teacher share is 35% in Huancavelica vs a national average of 25%.
- Source: Gobierno Regional de Huancavelica, [Diagnóstico Educativo Regional](https://old.regionhuancavelica.gob.pe/descargas/upload/DOCUMENTOS%20DE%20GESTION/Planes%20Regionales/2175176_diagnostico_educativo_regional.pdf).
- ⚠️ **The figures are old.** The document is from the regional archive and is probably ~2008–2010. Treat them as directional. The current ESCALE figure was NOT FOUND (the ESCALE profile PDF was blocked).

**EIB (Educación Intercultural Bilingüe)**
- National teacher gap (Minedu data to the Foro Educativo EIB commission, 2025): 76,228 teachers work in EIB schools, but only 56,753 are EIB teachers. That is a **gap of 19,745**:
  - 9,851 in secondary
  - 6,411 in primary
  - 3,213 in initial
- Source: [La República, 2026-02-20](https://larepublica.pe/sociedad/2026/02/20/una-brecha-que-no-cierra-faltan-mas-de-19000-maestros-de-lenguas-originarias-en-peru-578000).
- Older figure: 61% of posts in 26,862 EIB schools were held by Spanish-only teachers ([Servindi, 2022](https://www.servindi.org/actualidad-noticias/18/01/2022/docentes-bilingues-una-antigua-deuda-del-peru-con-los-pueblos)).
- Huancavelica EIB school count: **UNVERIFIED.** A search snippet says ~2,000 EIB schools (7.04% of the national total), and UGEL Huancavelica had 450. The originating document couldn't be confirmed (possibly [Congreso NIR 20](https://www3.congreso.gob.pe/Docs/DGP/DIDP/files/nir_20_educaci%C3%93n_biling%C3%9Ce_intercultural_en_el_peru.pdf)).
- Local press: "only 3% of students study in Quechua in Huancavelica" ([Correo Huancavelica](https://diariocorreo.pe/edicion/huancavelica/huancavelica-solo-el-3-de-alumnos-estudia-en-quechua-en-huancavelica-noticia/), headline only, undated).
- Materials shortage in Quechua: **NOT FOUND** as a specific Huancavelica figure.

## 6. Beca 18 (PRONABEC), convocatoria 2027

- **6,000 scholarships**, with at least 50% reserved for public higher-education institutions. Nine application modalities. 0.5% of places are reserved for people with disabilities. Source: [Andina](https://andina.pe/agencia/noticia-beca-18-pronabec-ofrece-6000-nuevas-vacantes-cuya-inscripcion-vence-viernes-16-1096127.aspx).
- **Dates**:

  | Stage | Date |
  |---|---|
  | Registration closed (online, free) | Friday 2026-10-16, 23:59 |
  | Eligible list | 2026-11-11 |
  | **Examen Nacional de Preselección** (in person, 60 questions on math and reading) | **Sunday 2026-11-22** |
  | Pre-selected list | 2026-12-23 |
  | Scholarship application, first window | 2027-01-07 → 2027-02-25 |
  | Scholarship application, second window | 2027-04-07 → 2027-04-30 |

  - Sources: [Andina](https://andina.pe/agencia/noticia-beca-18-pronabec-ofrece-6000-nuevas-vacantes-cuya-inscripcion-vence-viernes-16-1096127.aspx), [La República](https://larepublica.pe/sociedad/2026/10/10/pronabec-lanza-convocatoria-de-beca-182027-con-6000-vacantes-requisitos-inscripciones-y-plazos-103380).
  - The application-window dates are from the search summary of the La República article. Confirm them against the official bases.
- Requirements: last year of secondary school or graduated, high grades in the last two school years, and proof of vulnerability or a special situation ([El Peruano](https://elperuano.pe/noticia/306716-beca-18-2027-estos-son-los-requisitos-para-postular-a-una-de-las-6000-vacantes-hasta-el-16-de-octubre)).
- **Huancavelica**:
  - PRONABEC reported Huancavelica leading regions in **exam attendance: 2,065 registered, 94.9% attended** ([gob.pe/pronabec](https://www.gob.pe/institucion/pronabec/noticias/1293322-huancavelica-arequipa-y-callao-alcanzan-mayor-nivel-de-asistencia-al-examen-nacional-de-beca-18)).
  - ⚠️ The page returned HTTP 418. The year of the convocatoria is unconfirmed, probably Beca 18-2026.
  - Per-region preselected lists exist as PDFs ([Anexo 1](https://www.pronabec.gob.pe/wp-content/uploads/2026/02/Anexo-n.%C2%B0-1-Relacion-de-postulantes-preseleccionados.pdf)).
- **Documented barriers for rural applicants** (exam, paperwork, internet): **NOT FOUND** as a sourced study in this pass. Don't claim it without a source. Inference only: online-only registration plus an in-person exam plus proof-of-vulnerability paperwork are the plausible friction points.

## 7. Ley de Transparencia y Acceso a la Información Pública (TUO, Ley 27806, D.S. 021-2019-JUS)

All quotes are from the [TUO text, Congreso](https://www2.congreso.gob.pe/sicr/cendocbib/con5_uibd.nsf/DE0722775AABAAC9052586DB001D51FA/$FILE/TUO-LEY27806.pdf).
- **Anyone can request, and no reason is needed.** Art. 7: *"Toda persona tiene derecho a solicitar y recibir información de cualquier entidad de la Administración Pública. En ningún caso se exige expresión de causa."* Municipalities are public administration entities.
- **Deadline.** Art. 11(b), as amended by D. Leg. 1353: *"debe otorgarla en un plazo no mayor de diez (10) días hábiles"* (10 business days). Some secondary sources cite 12 days, but the TUO text says **10**. If the entity doesn't respond, the applicant can appeal to the Autoridad Nacional de Transparencia.
- **Is it used in rural areas?**
  - Defensoría del Pueblo: of 15,775 access-to-information complaints over 20 years, **53.7% were against local governments**, 60% in 2013–2022. **31% of 2019–2022 complaints came from vulnerable people**, and 76% of those were against local governments ([Defensoría](https://www.defensoria.gob.pe/defensoria-del-pueblo-casi-la-tercera-parte-de-quejas-por-falta-de-acceso-a-informacion-en-periodo-2019-2022-fueron-presentadas-por-personas-vulnerables/)).
  - Defensoría report on active transparency in local and regional governments: [PDF](https://www.defensoria.gob.pe/wp-content/uploads/2023/07/Informe-Transparencia-Activa-de-los-GL-y-GR.pdf).
  - **Direct evidence that rural citizens rarely use the right: NOT FOUND.** The data shows municipalities are the main violators, not a rural usage rate.

## 8. Congress bills (proyectos de ley)

- Official bill search portal (SPLEY): [wb2server.congreso.gob.pe/spley-portal/#/expediente/search](https://wb2server.congreso.gob.pe/spley-portal/#/expediente/search). Archive of laws: [Archivo Digital de la Legislación](https://wb2server.congreso.gob.pe/adlp-visor/).
- **No documented official open-data API found.**
  - The SPLEY portal is a single-page app backed by JSON endpoints, which community projects consume directly.
  - [unimauro/congreso-abierto-peru](https://github.com/unimauro/congreso-abierto-peru) says it uses the "API oficial confirmada" and downloaded 14,704 bills from 2021–2026. The README doesn't print the endpoint; see its `docs/DATA_SOURCES.md`.
  - Also [DecideBienpe/peru-congreso](https://github.com/DecideBienpe/peru-congreso) and [proyectosdeley.pe](http://www.proyectosdeley.pe/about/).
  - Treat the endpoint as undocumented and unstable.

---

## Things NOT to claim without checking first
- Any Huancavelica ENLA % (conflicting snippets).
- Current ESCALE multigrade/single-teacher percentages (only an old regional diagnostic was found).
- Huancavelica EIB school count.
- Rural Beca 18 barriers.
- Rural under-use of the transparency law.
- An official JNE or Congress API.
- Whether Huancavelica's governor has been formally proclaimed (no runoff expected, 33.95% > 30%).
