# Workplan: EDA of Crime Records in Metropolitan Lima 2018 to 2025

Dataset: delitos_lima_metropolitana_completo_2018-25.csv
Volume: 1.82 GB, 3,137,220 rows, 58 columns
Engine: DuckDB (SQL) and Polars (dataframe API), both used in parallel
Environment: conda env datafest (Python 3.11)

## 1. Purpose of this document

This is the AS IS versus TO BE plan. It states what the data actually is today,
what is broken in it, what we can legitimately build on top of it, and in which
order the work has to happen. Section 6 contains the decision that drives the
whole modeling stage.

## 2. AS IS: what we actually have

### 2.1 Identity and grain

The grain is one police event record. The true primary key is **objectid**
(3,137,220 unique values, zero collisions). The field id_dgc is **not** unique:
2,963,455 distinct values over 3,137,220 rows, with 156,473 identifiers appearing
twice and 8,330 appearing three or more times. One filed complaint can carry
several modalidad rows, so any count of "crimes" that uses id_dgc will
undercount and any count that uses objectid will count modalidades, not events.
This must be decided explicitly before any aggregate is published.

### 2.2 What the file really contains

The name says delitos. The content is wider than that. Breaking down by
es_delito_x:

| Category | Rows | Share |
|---|---|---|
| 1.Delitos | 1,357,510 | 43.3 percent |
| Otros | 824,594 | 26.3 percent |
| 4.Violencia contra la mujer e int | 756,653 | 24.1 percent |
| 2.Faltas | 191,240 | 6.1 percent |
| 3. Ninos y adolescentes | 7,223 | 0.2 percent |

Inside those rows, 478,582 are VISITA REALIZADA POR MEDIDA DE PROTECCION and
138,459 are SERVICIO POLICIAL EFECTUADO. Those are police workload records, not
offences. Roughly one in five rows describes something the police did, not
something that happened to a victim. Treating the row count as a crime count
inflates the series by about 20 percent and the inflation is not constant across
years.

### 2.3 Temporal coverage

Nominal coverage is 2018 to 2025. Real coverage of fecha_hora_hecho spans
48 distinct years, from 1923 to 2025. Records outside the declared window total 9,368
(0.30 percent) and are backlogged or mistyped filings. Two facts break naive
time series work:

1. **2025 is a partial year.** The last event is 30 June 2025. Monthly volume
   inside 2025 falls from 42,214 in January to 33,668 in June, which is partly
   real and partly right censoring caused by reporting lag.
2. **Reporting lag is long tailed.** Median lag between event and registration is
   0 days, p75 is 2 days, p95 is 25 days, p99 is 204 days, and the maximum is 36,525
   days. 11,207 records carry a negative lag of a full day or more, meaning they
   were registered before they happened, which is impossible and marks them as
   corrupted. A larger group carries a sub day negative lag, and that one is not
   corruption: it follows directly from the timestamp rounding described in 2.4,
   so the lag must be measured in whole days rather than hours.

Yearly volume for reference: 2018 307,181; 2019 337,388; 2020 317,006;
2021 414,398; 2022 452,846; 2023 547,304; 2024 516,703; 2025 235,026 (half year).

### 2.4 Timestamp precision is artificial

Minute values are not uniform. 1,279,084 records (40.8 percent) sit exactly on
minute 00 and 637,366 (20.3 percent) on minute 30. Six out of ten timestamps are
rounded to the hour or half hour. The hour histogram peaks at 10h and 11h, which
is police desk opening time, not a crime peak. Hour of day is therefore a mix of
true incident time and administrative artefact. It stays usable as a feature but
cannot be read as a literal crime clock.

### 2.5 Geolocation is the largest structural defect

Column estado_coord splits the file:

| estado_coord | Rows | Share |
|---|---|---|
| CON COORDENADA | 1,798,965 | 57.34 percent |
| SIN COORDENADA | 1,338,255 | 42.66 percent |

Everything marked SIN COORDENADA still carries a latitude and a longitude. Those
values were forced onto the centroid of the police station (observacion equals
GEO FORZADA AL CENTROIDE DE COMISARIA, 1,246,930 rows). The consequence is
measurable: the 500 most frequent coordinate pairs absorb 1,793,846 rows, that is
**57.2 percent of the whole dataset sitting on 500 points**, out of 443,789 distinct points in the file. The single most
frequent point holds 133,151 records.

Worse, the defect grows over time:

| Year | CON COORDENADA | Share with real coordinates |
|---|---|---|
| 2018 | 284,041 | 92.5 percent |
| 2019 | 220,896 | 65.5 percent |
| 2020 | 212,860 | 67.1 percent |
| 2021 | 244,901 | 59.1 percent |
| 2022 | 283,654 | 62.6 percent |
| 2023 | 349,028 | 63.8 percent |
| 2024 | 179,606 | 34.8 percent |
| 2025 | 16,430 | 7.0 percent |

Geocoding quality collapsed from 92 percent to 7 percent. Worse still, the loss
is not neutral with respect to crime type. Measured association between crime
family and geocoding status gives a Cramer V of 0.193, which is the strongest of
every categorical association measured in the notebook, above crime subtype
against shift (0.120) and district against crime family (0.088). So the trusted
geo subset is biased twice over: toward the earlier years, and toward the crime
families that retain a coordinate. Any density map,
any DBSCAN over raw coordinates, and any hotspot series computed on the full file
will describe the location of police stations and will show a fake trend driven
by the collapse itself. This is the single most important finding of the AS IS
review.

### 2.6 Columns that carry no information

Five columns are constant: id_dpto_hecho, departamento_hecho, id_prov_hecho,
provincia_hecho, fuente. One column is entirely empty: tipologias_ia
(100 percent null). One column is nearly empty: cuadra_hecho (98.04 percent null).

Seven columns come from a joined program table and are 96.3 percent null:
barrio, comisaria, departamento, provincia, distrito, indice_priorizacion,
fecha_inaguracion. They only populate for 115,599 rows belonging to the Barrio
Seguro intervention (31 barrios, priority index between 1.03 and 1.89). These are
not missing values to impute. They are a flag for programme membership and must
be converted into a boolean plus a numeric index, never imputed.

### 2.7 Referential inconsistencies

1. ubigeo_hecho_delito disagrees with id_dist_hecho in 535,217 rows
   (17.1 percent). The district of the event and the district code do not always
   match.
2. id_materia_hecho does not map one to one onto materia_hecho. Code 5 appears
   as both LEYES ESPECIALES (842,893 rows) and FUERO COMUN (10,279 rows). There
   are 19 distinct pairs for 5 nominal categories.
3. tipo_via_hecho is 87.9 percent the literal value Otros plus 3.05 percent the
   string NA. Only about 9 percent of rows carry a usable road type. Note that
   this column looks worthless by descriptive statistics and is not: see 2.8
   point 4.

### 2.8 Signal that is genuinely present

Not everything is broken. Three strong, clean signals survive every filter:

1. **Extortion growth.** EXTORSION rises from 588 records in 2018 to 10,136 in
   2023, a 17 fold increase, then 8,118 in 2024 and 5,755 in the first half of
   2025. This is the clearest structural change in the file.
2. **District heterogeneity in crime mix.** Restricted to patrimony offences, the
   share of ROBO (violent or intimidating theft) versus HURTO (stealth theft)
   ranges from 55.4 percent in Villa El Salvador down to 21.4 percent in La
   Molina, a 34 point spread across 43 districts.
3. **Time of day heterogeneity.** The same ROBO share moves from 47.6 percent at
   night down to 33.6 percent in the afternoon, a 14 point spread.
4. **The missingness marker in tipo_via_hecho is highly discriminative.** Among
   patrimony offences, rows whose road type is the string NA carry a 59.84
   percent ROBO rate over 95,622 rows, against 36.26 percent for the dominant
   Otros category over 656,394 rows. A 23.6 point gap. The plausible reading is
   that when the incident happens in motion or with no fixed reference, which is
   the signature of a contact robbery, the intake officer cannot assign a road
   type. The absence of the value is information about the nature of the event.
   This is the column that descriptive statistics would have discarded and that
   the selection funnel in section 5 keeps as the single most valuable
   categorical feature.
5. **Police operational divisions separate cleanly.** The ROBO share runs from
   49.70 percent in DIVPOL NORTE 1 down to 27.98 percent in DIVPOL SUR 1, a 21.7
   point spread across 17 divisions whose boundaries match neither districts nor
   coordinates.

Those five facts are what make a model worth building.

## 3. AS IS versus TO BE summary

| Dimension | AS IS | TO BE |
|---|---|---|
| Storage | 1.82 GB single CSV, reparsed on every read | Parquet partitioned by year, plus a Polars categorical schema |
| Memory | 962.3 MB for a 24 column working slice | 290.6 MB after downcasting, a 69.8 percent reduction |
| Key | Ambiguous between id_dgc and objectid | objectid declared as grain, id_dgc kept as complaint identifier |
| Unit of analysis | Row equals crime, which is wrong | Row equals police event, offences isolated by an explicit filter |
| Coordinates | 42.7 percent forced to station centroids, mixed silently | Split into a trusted geo subset and an untrusted subset, never mixed |
| Time | 2025 half year mixed with full years | Analysis window closed at 31 December 2024, 2025 shown separately |
| Empty columns | 13 columns useless or near empty | Dropped or converted to flags before any modeling |
| Target | None defined | Defined and justified in section 6 |

## 4. Pipeline to execute

The notebook eda-generated.ipynb runs these stages in order. Every stage is a
named function, and complete_eda calls all of them.

**Stage 1. Column exploration and data dictionary.**
Profile all 58 columns with DuckDB: dtype, null count, cardinality, top value,
min and max. Emit diccionario_datos.csv with a Spanish description per column and
a keep or drop recommendation. This artefact is the contract for every later
stage.

**Stage 2. Load, in both engines.**
DuckDB reads the CSV through a view and answers profiling questions in SQL
without materialising the file. Polars reads a projected column subset lazily.
Both timings are recorded so the cost of each approach is documented, not assumed.

**Stage 3. Type reduction and memory release.**
Cast floats to Float32, small integers to Int8 and Int16, low cardinality strings
to Categorical, then drop intermediates and call gc.collect. Measure before and
after.

**Stage 4. Descriptive statistics.**
Numeric summary with quantiles and outlier ratio by the interquartile rule.
Categorical summary with cardinality, mode and concentration of the top category.

**Stage 5. Missing value analysis.**
Rank columns by null share, plot it, and classify each column into one of four
buckets: usable, impute, convert to flag, drop.

**Stage 6. Data quality audit.**
Duplicates on both candidate keys, out of window dates, negative reporting lag,
minute rounding, geocoding status by year, coordinate concentration, ubigeo
mismatch. This stage produces the constraints that the modeling stage must respect.

**Stage 7. Univariate distributions.**
Histogram plus boxplot for every numeric column. Horizontal barplot for every
categorical column with cardinality under a threshold, top N otherwise.

**Stage 8. Correlation.**
Pearson and Spearman on the numeric block. Spearman matters here because the
count style variables are not normal.

**Stage 9. Bivariate relations.**
Crime family against turno, against district, and against geocoding status.
Chi squared and Cramer V so that the strength of association is quantified and
not only drawn.

**Stage 10. Temporal evolution.**
Monthly series of total events, series split by crime family, hour by weekday
heatmap, and the extortion series isolated. The 2025 partial year is drawn in a
visually distinct way in every chart.

**Stage 11. Spatial analysis.**
Restricted to the trusted geo subset only. Hexbin density, then KMeans hotspots
with the number of clusters chosen by silhouette.

**Stage 12. Unsupervised model, district profiling.**
Build a district by crime type matrix of row normalised proportions, standardise,
run KMeans, validate with silhouette, project with PCA, and name each cluster from
its dominant crime types.

**Stage 13. Supervised model.**
See section 6 for the target and section 5 for the feature discipline.

**Stage 14. Conclusions and call to action.**

## 5. Feature discipline for the supervised stage

The rule that governs every feature decision: **a feature is admissible only if
its value is knowable before the offence is classified.** The columns
materia_hecho, tipo_hecho, subtipo_hecho, modalidad_hecho, id_materia_hecho,
id_tipo_hecho, id_subtipo_hecho and id_modalidad_hecho all encode the answer.
They are the label, in five levels of granularity. Including any of them produces
an AUC near 1.0 and a worthless model. They are excluded by construction and the
exclusion is asserted in code, not just in prose.

Admissible features are limited to: when it happened (hour, weekday, month, day
of month, day of year, weekend flag, turno), where it happened (district, police
station, latitude, longitude, road type), and how it was recorded (geocoding
precision flag, solo_denuncia flag).

Encoding follows the instructions: label encoding backed by an explicit dictionary
so the original category can always be recovered, kept as an artefact
(mapas_categoricos.json). Optimal binning is applied to numeric features only when
it raises discriminative power, measured, not assumed.

Validation is a **temporal split**, not a random split. Train on 2018 to 2023,
test on 2024 to 2025. A random split would leak the future into the past and
would also hide the distribution shift, which is large: the positive rate falls
from 41.8 percent in the training window to 34.7 percent in the test window.
Reporting an honest number under shift is the point.

## 6. The target decision, and its justification

The question the instructions ask is whether this data is sufficient to build a
predictive model. The honest answer has three parts.

### 6.1 What cannot be done

**Predicting whether a crime will occur at a place and time is not possible with
this file alone.** The reason is structural, not technical. The dataset contains
only positive cases. There is no record of a street corner at an hour where
nothing happened, and there is no denominator: no population, no floating
population, no commercial density, no street lighting, no police deployment. Any
model of the form "will there be a crime here" would need negative sampling over
a space and time grid, and the resulting rate would confound crime with reporting
propensity and with the geocoding collapse documented in 2.5. Building it would
produce a number that looks like a prediction and is actually a map of where
people file complaints. That is stated here so it is not attempted later.

To make that question answerable the data must be joined with: INEI population
and household projections by district, economic census establishment density,
street lighting and CCTV inventories from each municipality, public transport
network geometry, and police station staffing. Those are named in section 7 as
the required external indicators.

### 6.2 What can be done without a target, and why it comes first

The file is an unlabelled event register. The natural first model is therefore
unsupervised. Two clusterings are run:

1. **District profiling.** 43 districts described by their crime mix proportions.
   This answers a question a security office actually asks: which districts
   should share a strategy, given that they have the same kind of crime problem,
   independently of their size.
2. **Spatial hotspots.** KMeans over the trusted geo subset only, to locate
   concentration cores that are not police station artefacts.

Clustering is defensible here because it requires no label, is robust to the
absence of a denominator when applied to proportions rather than counts, and
produces an output that is directly actionable.

### 6.3 The supervised target that is defensible

Among the questions this data can answer with a label it already contains, one is
both well posed and operationally useful:

> Given a patrimony offence reported at a known place and time, was it a ROBO
> (taken with violence or intimidation, direct contact with the victim) or a
> HURTO (taken by stealth, no confrontation)?

Formally: binary classification, target equals 1 when subtipo_hecho is ROBO,
0 when it is HURTO, restricted to those two subtypes.

This target is justified on six grounds.

1. **It is already labelled**, by the police, at the moment of filing. No proxy,
   no construction, no leakage from a derived variable.
2. **Volume and balance are excellent.** 855,609 usable rows, 40.1 percent
   positive. No resampling needed.
3. **It is semantically meaningful.** ROBO involves contact with the victim and
   therefore risk to physical integrity. HURTO does not. The two demand different
   responses: visible patrol and deterrence against ROBO, environmental
   prevention and public awareness against HURTO. The prediction maps onto a
   decision.
4. **The confounders that ruin the occurrence question do not apply.** The model
   is conditional on an offence having been reported. Population, reporting
   propensity and geocoding coverage affect whether a row exists, but they affect
   both classes of the ratio in the same direction, so the conditional
   probability is far more stable than a raw rate.
5. **The signal is present and was measured before the model was written.** The
   ROBO share moves 14 points across turno and 34 points across districts. There
   is something to learn.
6. **It is falsifiable under a temporal split.** Train on the past, test on the
   future, and accept the number that comes out.

The measured result is AUC 0.6956 and average precision 0.5388 against a 0.3471
baseline on the 2024 to 2025 holdout, a 55.2 percent gain over the trivial
prediction. That is moderate, and it is reported as
moderate. It is enough to rank incidents by violence risk and is not enough to
classify an individual case with confidence. Saying so is part of the deliverable.

### 6.4 Alternatives considered and rejected

| Candidate target | Why rejected |
|---|---|
| Crime occurrence on a space and time grid | No negative class, no denominator, confounded with reporting and geocoding (see 6.1) |
| Multiclass over tipo_hecho, 52 classes | Extreme imbalance, several classes under 30 rows, and the top class is an administrative artefact |
| Reporting lag as a regression target | Interesting operationally but the label is corrupted: 11,207 negative values of a full day or more, and a maximum of 36,525 days |
| Monthly count forecast per district | Legitimate, but 2025 is censored and the 2020 pandemic break is unmodelled. Listed in section 7 as future work, not attempted here |
| es_delito_x as a target | Nearly deterministic given tipo_hecho, so it is a relabelling of the label |

## 7. TO BE: what the data must be joined with

Ordered by expected marginal value.

1. INEI population, household count and age structure by district and by census
   block. Converts counts into rates and unlocks the occurrence question.
2. Economic census establishment density. Crime concentrates on commercial
   activity, and this is the strongest single missing covariate.
3. Municipal CCTV and street lighting inventories, geolocated. Directly
   actionable and directly testable.
4. Public transport network, including corridors and informal stops. ROBO
   concentrates on transit corridors and the road type column is too degraded to
   proxy this.
5. Police station staffing and patrol schedules. Needed to separate crime from
   police presence and to correct the reporting propensity bias.
6. SIDPOL or Ministerio Publico case outcomes. Adds the resolution dimension the
   file completely lacks.

## 8. Deliverables

| File | Content |
|---|---|
| readme-workplan.md | This document |
| readme-guide.md | Reusable EDA template, supervised and unsupervised variants |
| eda-generated.ipynb | Executed notebook implementing the template on this dataset |
| diccionario_datos.csv | Data dictionary in Spanish, generated by stage 1 |
| mapas_categoricos.json | Label encoding dictionaries, reversible |

## 9. Risk register

| Risk | Impact | Control |
|---|---|---|
| Reading the file as a crime count | Every published figure inflated about 20 percent | Explicit offence filter, stated at the top of every aggregate |
| Mapping the full coordinate set | Maps police stations, not crime | Trusted geo subset only, and the split is enforced in the loading function |
| Including a taxonomy column as a feature | AUC near 1.0, model is worthless | Hard exclusion list asserted in code |
| Random train test split | Leakage and hidden distribution shift | Temporal split, 2018 to 2023 against 2024 to 2025 |
| Including 2025 in yearly trends | False decline of about 50 percent | Window closed at 31 December 2024, 2025 plotted separately |
| Treating Barrio Seguro nulls as missing | 96 percent imputation on a programme flag | Converted to boolean plus index, never imputed |
| Reading the hour histogram literally | Peak at 10h read as a crime peak | Rounding artefact documented next to every hour chart |
| Dropping a column because one category dominates it | tipo_via_hecho is 88 percent one value and is the best categorical feature in the model | Selection decided by measured AUC gain, never by pct_moda |
| Ranking features by tree gain | Gain favours high cardinality: it ranks latitude first and tipo_via_hecho sixth, SHAP reverses both | SHAP as the ranking authority, cross checked against measured AUC gain |
| Treating the trusted geo subset as neutral | It is biased by year and by crime type (Cramer V 0.193) | Bias declared next to every map built on it |
