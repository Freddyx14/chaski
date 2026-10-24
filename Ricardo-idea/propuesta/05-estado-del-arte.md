# Estado del arte — qué valida la propuesta y qué la corrige

> Búsqueda hecha el viernes 23 de octubre de 2026. Fuentes: OpenAlex (`title_and_abstract.search`,
> ordenado por citas), Semantic Scholar y Unpaywall. Los 23 DOI de la bibliografía resolvieron
> correctamente contra OpenAlex. Los PDFs de acceso abierto que se pudieron bajar están en `../papers/`;
> los demás quedan con enlace, porque la editorial bloquea la descarga automática (protección de bots,
> no paywall en todos los casos).

## Resumen: la propuesta se sostiene, con tres correcciones

| Pieza del diseño | Veredicto | Fuente principal |
|---|---|---|
| Corredor (tramo de calle) como unidad de análisis | **Validado y bien establecido** | Weisburd et al. 2004; Lee & Eck 2017 |
| Lags espacio-temporales y contagio como features | **Validado** | Mohler et al. 2011; Ratcliffe & Rengert 2008 |
| Hawkes sobre el grafo | Validado como método, **y ya desplegado en campo** | Mohler et al. 2015; Reinhart 2018 |
| GNN sobre red vial para predecir delito | **Ya existe. No es nuestra novedad** | Gu & Sui 2024; Sui & Chen 2024 |
| Métrica de top-k en vez de accuracy | **Validado, y hay métricas estándar que debemos usar (PAI/PEI)** | Kounadi et al. 2020; Mohler & Porter 2020 |
| Iluminación como covariable | Validado causalmente **a nivel de poste, no de píxel satelital** | Chalfin et al. 2021; Mitre-Becerril et al. 2022 |
| Predecir dónde "se desplaza" el delito | **Corregido: el desplazamiento no se asume, se mide** | Weisburd et al. 2006 |
| Entrenar sobre denuncias policiales | **Riesgo serio y documentado de retroalimentación** | Lum & Isaac 2016; Jaitman & Anauati 2019 |
| Extorsión a escala de tramo | **Hueco real en la literatura** | Nardin et al. 2016 (modelo de agentes, no espacial) |
| Analítica visual de crimen a nivel de calle | **Ya existe y está en TVCG. No es nuestra novedad** | García-Zanabria, Poco et al. 2021 (CriPAV); Raimundo et al. 2025 (CounterCrime) |

## 1 · La unidad correcta es el tramo de calle

Weisburd y colegas siguieron 14 años de incidentes en Seattle y encontraron que una fracción muy pequeña
de los tramos de calle concentra la mitad del delito, y que esos tramos tienen trayectorias propias y
estables en el tiempo, distintas de las de la cuadra de al lado (Weisburd et al. 2004, 858 citas). La
revisión sistemática de Lee & Eck (2017) confirma que la concentración en micro-lugares se repite en
estudios de muchos países y décadas. Braga et al. (2009) muestran lo mismo específicamente para violencia
con arma de fuego en Boston.

**Qué significa para nosotros.** La decisión de §1 de `02-diseno-tecnico.md` —trabajar por corredor y no
por distrito— no es una preferencia estética: es la unidad que la criminología usa desde hace veinte años,
y el distrito es conocido por promediar hasta borrar el fenómeno. Esto se dice en el pitch con la cita.

## 2 · El delito se contagia en espacio y tiempo, y eso se modela

La hipótesis de "repetición cercana" dice que tras un hecho sube la probabilidad de otro hecho cerca y
pronto. Está medida en robo a vivienda (Townsley 2003; Johnson & Bowers 2004; Short et al. 2009) y —lo que
más nos importa— **en balaceras**: Ratcliffe & Rengert (2008) encuentran riesgo elevado de un nuevo disparo
dentro de una manzana y dos semanas en Filadelfia.

Mohler et al. (2011, 894 citas) formalizaron esto como un proceso de puntos auto-excitante (Hawkes),
prestado de la sismología: cada evento eleva temporalmente la intensidad alrededor. Reinhart (2018) es la
revisión de referencia del método. Y Mohler et al. (2015) lo llevaron a ensayos controlados aleatorizados
en Los Ángeles y Kent: el modelo predijo mejor que los analistas humanos y las patrullas asignadas con él
redujeron delito.

**Qué significa para nosotros.** Los lags propios y de vecinos del grafo (§2 del diseño técnico) son la
versión discreta de ese proceso. Hawkes como stretch está bien fundamentado. **Y hay un giro que la
literatura no cubre:** el contagio que nos interesa es *cruzado* —denuncia de extorsión hoy, disparo o
daño a la fachada después— no extorsión→extorsión.

## 3 · Corrección importante: el desplazamiento no se asume, se mide

Esta es la corrección más fuerte a la idea original. Weisburd et al. (2006, 529 citas) hicieron un estudio
controlado en Jersey City buscando precisamente que el delito "se mueva a la vuelta de la esquina" tras una
intervención, y encontraron **poco desplazamiento y, más bien, difusión de beneficios**: las zonas vecinas
también mejoraron. La revisión sistemática de Braga et al. (2019) sobre *hot spots policing* llega a la
misma conclusión general.

**Qué significa para nosotros.** No podemos vender "el delito se mueve 400 metros" como un hecho. Lo
honesto, y además más interesante, es: *la literatura dice que para delitos de oportunidad el
desplazamiento es menor de lo que la intuición supone; la extorsión es territorial y organizada, así que
la pregunta queda abierta, y nuestro sistema la mide en vez de asumirla.* Eso convierte una debilidad en
un aporte: es una hipótesis contrastable sobre un delito donde nadie la ha contrastado.

## 4 · GNN sobre red vial: ya existe, y hay que decirlo

Gu & Sui (2024, *IJGI*) hacen aprendizaje de representaciones sobre grafos para predicción de delito a
nivel de calle. Sui & Chen (2024) usan una red de atención espacio-temporal para incidentes de llamadas de
emergencia, también a nivel de calle. Hakyemez & Badur (2026) combinan redes profundas sobre red vial con
variables ambientales derivadas de teoría criminológica.

**Qué significa para nosotros.** Nuestra arquitectura no es inédita, y un jurado técnico que conozca el
área lo va a saber. La respuesta correcta no es ocultarlo sino decirlo: **lo nuevo es el objeto (extorsión
en Lima, 35 mil denuncias geolocalizadas), el contagio cruzado hacia violencia armada, el denominador de
negocios, y que el destinatario es la víctima y no la patrulla.**

## 4.b · Analítica visual de crimen: el linaje directo, y un autor peruano

Hay un grupo que lleva años haciendo exactamente la parte visual de lo que queremos: el laboratorio de
**Jorge Poco (FGV, Río de Janeiro)**, con **Germain García-Zanabria** (peruano) y Luis Gustavo Nonato
(USP), más Claudio Silva (NYU) y el Núcleo de Estudos da Violência de la USP.

- **CriPAV: Street-Level Crime Patterns Analysis and Visualization** (TVCG 2021). Es el antecedente más
  cercano a nuestra unidad de análisis. Su planteamiento del problema es el nuestro, en sus palabras: la
  dificultad viene de *"the sparse nature of the crime activity and its spread in large spatial areas"*, y
  esa dispersión impide que los métodos de comparación de series temporales funcionen. Resuelven con un
  mecanismo estocástico que permite analizar patrones **a nivel de calle** en São Paulo.
  **Esto importa mucho para nosotros:** nuestras 8,407 denuncias de extorsión repartidas entre miles de
  corredores son exactamente una serie dispersa, y CriPAV dice cómo tratarla sin que el ruido se coma la
  señal.
- **CrimAnalyzer** (TVCG 2019) descompone los patrones de crimen de São Paulo en componentes locales y
  permite ver cuáles crecen y cuáles se apagan. Es el pariente directo de nuestra idea de "corredores
  análogos".
- **CounterCrime** (TVCG 2025) usa **explicaciones contrafactuales** para explorar escenarios de reducción
  de crimen: qué variables tendrían que cambiar para que una región pase de insegura a segura, organizado
  en tres niveles (ciudad, grupo de regiones, región). **Ese es el producto para el funcionario**, y nos
  da el precedente académico para la vista `/analista`: no solo "aquí hay riesgo" sino "qué cambiaría si".
- **Mirante** (SIBGRAPI 2020) y **17K-Graffiti** (VISAPP 2022) completan la línea; el segundo cruza datos
  de crimen con imágenes urbanas.
- La tesis de García-Zanabria, **Visual Crime Pattern Analysis** (USP, 2021), es el resumen largo de toda
  esta línea.
- Fuera del crimen pero muy útil para la parte visual: **TaxiVis** (TVCG 2013, 521 citas) es el trabajo
  fundacional de consultas visuales sobre datos urbanos espacio-temporales, y **ManyWaves** (CGF 2026) y
  **UrbanClipAtlas** (2026) son lo más reciente del mismo grupo en exploración multivariada
  espacio-temporal.

**Qué significa para nosotros, sin maquillaje.** La analítica visual de crimen a nivel de calle **ya
existe y está publicada en TVCG**. No podemos presentar el mapa como la novedad. Lo que sí es nuestro:

1. El objeto: **extorsión**, no homicidio ni robo, y en **Lima**, no en São Paulo.
2. El destinatario: **la víctima por WhatsApp**, no el analista de la secretaría de seguridad.
3. La predicción de **escalamiento cruzado** (denuncia de extorsión → hecho con arma de fuego).
4. El **denominador de negocios** estimado desde satélite.

Y hay un uso táctico: **citar a CriPAV y a CounterCrime en el pitch nos acredita**. Muestra que sabemos
dónde está el estado del arte, que lo leímos, y que construimos encima en vez de reinventarlo mal. Que uno
de los autores sea peruano y trabaje sobre crimen en Sudamérica refuerza la historia.

**Además hay una pista para el cruce de datos** que no habíamos considerado: este grupo usa
**imágenes de street view** para medir percepción de seguridad y desorden físico urbano
(*Quantifying Urban Safety Perception on Street View Images*, 2021; *What Makes a Place Feel Safe?*, 2024;
*UrbanPhysicalDisorder-4K*, 2025). A nivel de corredor, street view tiene **mucha mejor resolución que
cualquier satélite**, y Google Street View cubre Lima. Ver `06-datos-externos.md`.

Y para el denominador socioeconómico: **Granularity at Scale** (JSTARS 2024) estima indicadores
socioeconómicos de vecindario desde imágenes de alta resolución, que es justo la técnica que necesitamos
para estimar negocios y densidad construida por corredor.

## 5 · Cómo se evalúa esto de verdad

La revisión sistemática de Kounadi et al. (2020) sobre pronóstico espacial de delito fija las prácticas
del área. Mohler & Porter (2018, 2020) tratan el problema explícitamente como **ranking**: lo que importa
es si los k lugares que marcas concentran los hechos.

**Decisión que adoptamos:** además de AUC-PR, reportamos el **PAI** (*Predictive Accuracy Index*), que es
el estándar del campo:

```
PAI = (n/N) / (a/A)
n = hechos ocurridos dentro del área marcada
N = hechos totales del periodo
a = área (o longitud de vía) marcada
A = área (o longitud de vía) total
```

Un PAI de 10 significa que los corredores marcados concentran diez veces más hechos de los que les
tocarían por tamaño. Es el número que un funcionario entiende. Va en el README junto al baseline.

## 6 · Iluminación y entorno construido: evidencia causal, con un límite de resolución

Chalfin et al. (2021) hicieron un experimento aleatorizado de iluminación en complejos de vivienda pública
de Nueva York y encontraron reducciones grandes de delito nocturno; Mitre-Becerril et al. (2022) muestran
que parte del efecto persiste a largo plazo. Kaplan & Chalfin (2021) miden además el efecto sobre la
percepción de seguridad y el uso del espacio público. Dugato, Calderoni et al. (2017) hacen *Risk Terrain
Modeling* para pronosticar **homicidios de crimen organizado** de la Camorra en Nápoles a partir de
características del lugar: es el antecedente más cercano a lo que queremos hacer con extorsión.

**Límite que hay que declarar:** esos experimentos manipulan postes de luz reales. VIIRS tiene 500 metros
de resolución, que es más grueso que un corredor. Por eso VIIRS entra **como contexto, no como medición de
alumbrado de la cuadra**, y así se dice en el pitch. Si queremos iluminación a escala de calle, la fuente
honesta son imágenes nocturnas de calle o el inventario municipal, no el satélite.

## 7 · El riesgo que más puede hundir el proyecto: el sesgo del dato policial

Lum & Isaac (2016, 611 citas) es el trabajo de referencia: entrenaron PredPol con registros de drogas de
Oakland y mostraron que el modelo manda a la policía a los mismos barrios que ya vigilaba, porque el dato
mide **dónde patrulla la policía**, no dónde ocurre el delito. Con eso se crea un ciclo de
retroalimentación. Jaitman & Anauati (2019) documentan el tamaño de la cifra negra en América Latina, y
González de la Rosa & Sánchez-Martínez (2026) analizan justamente la relación entre homicidios y denuncias
policiales **en Perú**.

**Tres decisiones de diseño que salen de aquí, y que son argumento a favor en el pitch:**

1. **El producto no dirige patrullas.** Le habla a la víctima. El ciclo de retroalimentación de Lum & Isaac
   necesita que la salida del modelo cambie dónde se despliega la policía; el nuestro no hace eso.
2. **Predecimos violencia armada, no extorsión.** La extorsión está subregistrada entre 75% y 90%. Los
   hechos con arma de fuego, daños y homicidio se registran mucho mejor, porque hay herido, disparo o
   destrozo. **Usar extorsión como entrada y violencia como objetivo es metodológicamente más sólido que
   predecir la extorsión misma**, y es una decisión defendible frente a un jurado técnico.
3. **El aviso de subregistro es obligatorio en cada respuesta**, y no es un descargo legal: es la
   traducción directa de lo que dice esta literatura.

## 8 · Explicabilidad

Khalfa et al. (2025) comparan técnicas de XAI para predicciones de robo a corto plazo en micro-lugares, que
es casi exactamente nuestro caso de uso, y es uno de los PDF que sí se descargó. Caveat obligatorio: Slack
et al. (2021) muestran que las atribuciones de features pueden manipularse, así que SHAP explica el modelo,
no el mundo. La frase que Claude le dice al bodeguero debe decir "el modelo pesa esto", no "esto causa
aquello".

## 9 · El hueco: extorsión

Buscando extorsión en OpenAlex, lo cuantitativo casi no existe. Nardin et al. (2016) construyen un modelo
basado en agentes del racket de extorsión (proyecto GLODERS, 3 citas), que simula pero no predice sobre
datos reales georreferenciados. Dugato et al. (2017) es lo más cercano, y es sobre homicidios de la Camorra,
no sobre cobro de cupo.

Una búsqueda con el filtro `title_and_abstract.search:"remote sensing satellite imagery crime prediction
urban"` devolvió **cero resultados** en OpenAlex. Es evidencia débil —depende de cómo se escriba la
consulta— pero apunta en la misma dirección que el análisis de competencia: cruzar percepción remota con
registros de denuncias a escala de tramo es territorio poco pisado.

**Conclusión:** la metodología que usamos está bien establecida; lo que no existe es aplicarla a la
extorsión en Lima con la víctima como destinataria.

## 10 · Contexto peruano (prensa y fuentes oficiales, 2026)

> Esto viene de prensa y de búsquedas, no de una consulta a la base. **Verificar en la fuente primaria
> (Observatorio Nacional de Seguridad Ciudadana del Mininter) antes de ponerlo en una lámina.**

- El Ministerio Público registró **13,892 denuncias de extorsión entre enero y julio de 2026**
  ([Altavoz](https://altavoz.pe/locales/peru-registra-13-892-denuncias-por-extorsion-entre-enero-y-julio-de-2026/),
  [Infobae](https://www.infobae.com/america/agencias/2026/09/02/peru-registra-mas-de-13000-denuncias-por-extorsion-entre-enero-y-julio-de-2026/)).
- Serie de denuncias a la PNP citada por prensa: 11,642 (2022), 21,242 (2023), 21,746 (2024), **27,584
  (2025)**. Son cifras nacionales; nuestra base es solo Lima Metropolitana y llega a junio de 2025, así que
  **no se comparan de frente**.
- Reparto en Lima en ese periodo de 2026: Lima Este 1,806 · Lima Sur 1,346 · Lima Norte 1,305 · Lima Centro
  1,178.
- **Estado de emergencia en Lima y Callao desde mediados de octubre de 2026**, con militares en calle.
  El proyecto se presenta durante esa emergencia.
- **Las cifras oficiales no coinciden entre sí**, y es una controversia pública
  ([La República, julio 2026](https://larepublica.pe/politica/2026/07/18/polemica-no-coinciden-los-datos-oficiales-sobre-las-extorsiones-que-se-registran-en-el-peru-extorsion-hnews-496314)).
  En enero de 2026 se reportó una caída fuerte de denuncias
  ([France24](https://www.france24.com/es/minuto-a-minuto/20260123-per%C3%BA-registra-una-fuerte-ca%C3%ADda-de-las-denuncias-por-extorsi%C3%B3n-en-los-%C3%BAltimos-meses)).
  **Esto es argumento a favor del proyecto:** cuando las cifras agregadas se disputan políticamente, una
  medición reproducible a nivel de corredor, con el código abierto, vale más.
- Subregistro: según ENAPRES del INEI, de cada 10 víctimas solo una o dos denuncian; se cita también que
  **el 75% de las extorsiones no se denuncia**
  ([RPP](https://rpp.pe/politica/gobierno/por-que-las-victimas-de-extorsion-no-denuncian-los-hechos-esto-dicen-dos-expertos-en-seguridad-ciudadana-noticia-1587609),
  [Mininter](https://observatorio.mininter.gob.pe/sites/default/files/proyecto/archivos/REPORTE-Reporte%20de%20Cifras%20de%20Extorsi%C3%B3n%20en%20el%20Per%C3%BA.pdf)).

## 11 · Qué citar en el pitch, y en qué orden

1. **Apertura:** nuestras propias cifras (588 → 5,755 en medio año; "cupos laborales" 18 veces) y el estado
   de emergencia vigente.
2. **Por qué corredor:** Weisburd et al. 2004 en una línea.
3. **Por qué predecimos violencia y no extorsión:** Lum & Isaac 2016 más el 75% que no denuncia. Esta es la
   diapositiva que convence a un jurado técnico de que sabemos lo que hacemos.
4. **Qué tan bien funciona:** PAI y recall en top-k contra el baseline, sobre 2025.
5. **Dónde falla:** la tabla de `01-propuesta.md`, con Lum & Isaac como fuente del riesgo principal.


## Bibliografía

Todos los DOI resolvieron contra OpenAlex el 2026-10-23. ✅ = PDF en `../papers/`. Los PDFs del laboratorio
de Poco se bajaron de `files.visualdslab.com`.

| Autores | Título | Venue | Citas | DOI | PDF |
|---|---|---|---|---|---|
| George Mohler, Martin B. Short et al. (2011) | Self-Exciting Point Process Modeling of Crime | Journal of the American Statistical Association | 894 | `10.1198/jasa.2011.ap09546` | cerrado |
| David L. Weisburd, Shawn David Bushway et al. (2004) | TRAJECTORIES OF CRIME AT PLACES: A LONGITUDINAL STUDY OF STREET SEGMENTS IN THE CITY OF SE | Criminology | 858 | `10.1111/j.1745-9125.2004.tb00521.x` | cerrado |
| Kristian Lum, William Samuel Isaac (2016) | To Predict and Serve? | Significance | 611 | `10.1111/j.1740-9713.2016.00960.x` | [enlace](https://rss.onlinelibrary.wiley.com/doi/pdfdirect/10.1111/j.1740-9713.2016.00960.x) |
| David L. Weisburd, Laura Wyckoff et al. (2006) | DOES CRIME JUST MOVE AROUND THE CORNER? A CONTROLLED STUDY OF SPATIAL DISPLACEMENT AND DIF | Criminology | 529 | `10.1111/j.1745-9125.2006.00057.x` | cerrado |
| Nivan Roberto Ferreira Júnior, Jorge Poco et al. (2013) | Visual Exploration of Big Spatio-Temporal Urban Data: A Study of New York City Taxi Trips | IEEE Transactions on Visualization and Computer Graphics | 521 | `10.1109/tvcg.2013.226` | cerrado |
| George Mohler, Martin B. Short et al. (2015) | Randomized Controlled Field Trials of Predictive Policing | Journal of the American Statistical Association | 381 | `10.1080/01621459.2015.1077710` | ✅ `papers/mohler2015_rct.pdf` |
| Maria Rita D'Orsogna, Matjaž Perc (2014) | Statistical physics of crime: A review | Physics of Life Reviews | 280 | `10.1016/j.plrev.2014.11.001` | ✅ `papers/dorsogna2015_fisica_crimen.pdf` |
| Jerry H. Ratcliffe, George F. Rengert (2008) | Near-Repeat Patterns in Philadelphia Shootings | Security Journal | 272 | `10.1057/palgrave.sj.8350068` | cerrado |
| Martin B. Short, Maria Rita D'Orsogna et al. (2009) | Measuring and Modeling Repeat and Near-Repeat Burglary Effects | Journal of Quantitative Criminology | 194 | `10.1007/s10940-009-9068-8` | ✅ `papers/short2009_nearrepeat.pdf` |
| YongJei Lee, John E. Eck et al. (2017) | How concentrated is crime at places? A systematic review from 1970 to 2015 | Crime Science | 174 | `10.1186/s40163-017-0069-x` | [enlace](https://crimesciencejournal.biomedcentral.com/track/pdf/10.1186/s40163-017-0069-x) |
| Alex Reinhart (2018) | A Review of Self-Exciting Spatio-Temporal Point Processes and Their Applications | Statistical Science | 172 | `10.1214/17-sts629` | ✅ `papers/reinhart2018_review.pdf` |
| Aaron J. Chalfin, Benjamin Hansen et al. (2021) | Reducing Crime Through Environmental Design: Evidence from a Randomized Experiment of Stre | Journal of Quantitative Criminology | 145 | `10.1007/s10940-020-09490-6` | cerrado |
| Ourania Kounadi, Alina Ristea et al. (2020) | A systematic review on spatial crime forecasting | Crime Science | 123 | `10.1186/s40163-020-00116-7` | [enlace](https://crimesciencejournal.biomedcentral.com/track/pdf/10.1186/s40163-020-00116-7) |
| Jacob Kaplan, Aaron J. Chalfin (2021) | Ambient lighting, use of outdoor spaces and perceptions of public safety: evidence from a  | Security Journal | 60 | `10.1057/s41284-021-00296-0` | [enlace](https://link.springer.com/content/pdf/10.1057/s41284-021-00296-0.pdf) |
| Germain Garcia-Zanabria, Jaqueline Silveira et al. (2019) | CrimAnalyzer: Understanding Crime Patterns in São Paulo | IEEE Transactions on Visualization and Computer Graphics | 41 | `10.1109/tvcg.2019.2947515` | ✅ `papers/crimanalyzer2019.pdf` |
| Marco Dugato, Francesco Calderoni et al. (2017) | Forecasting Organized Crime Homicides: Risk Terrain Modeling of Camorra Violence in Naples | Journal of Interpersonal Violence | 40 | `10.1177/0886260517712275` | [enlace](http://hdl.handle.net/10807/104293) |
| Germain Garcia-Zanabria, Marcos M. Raimundo et al. (2021) | CriPAV: Street-Level Crime Patterns Analysis and Visualization | IEEE Transactions on Visualization and Computer Graphics | 30 | `10.1109/tvcg.2021.3111146` | cerrado |
| David Mitre‐Becerril, Sarah Tahamont et al. (2022) | Can deterrence persist? Long‐term evidence from a randomized experiment in street lighting | Criminology & Public Policy | 26 | `10.1111/1745-9133.12599` | [enlace](https://doi.org/10.1111/1745-9133.12599) |
| Laura Jaitman, María Victoria Anauati (2019) | The Dark Figure of Crime in Latin America and the Caribbean | Journal of Economics Race and Policy | 24 | `10.1007/s41996-019-00042-0` | cerrado |
| George Mohler, Michael D. Porter et al. (2020) | Learning to rank spatio-temporal event hotspots | Crime Science | 22 | `10.1186/s40163-020-00112-x` | [enlace](https://crimesciencejournal.biomedcentral.com/track/pdf/10.1186/s40163-020-00112-x) |
| Germain Garcia-Zanabria, Erick Gomez-Nieto et al. (2020) | Mirante: A visualization tool for analyzing urban crimes | SIBGRAPI Conference on Graphics, Patterns and Images (SIBGRAPI) | 18 | `10.1109/sibgrapi51738.2020.00028` | [enlace](https://hdl.handle.net/10438/31627) |
| Felipe Moreno-Vera, Bahram Lavi et al. (2021) | Quantifying Urban Safety Perception on Street View Images | IEEE/WIC/ACM International Conference on Web Intelligence | 11 | `10.1145/3486622.3493975` | cerrado |
| Haishuo Gu, Jinguang Sui et al. (2024) | Graph Representation Learning for Street-Level Crime Prediction | ISPRS International Journal of Geo-Information | 9 | `10.3390/ijgi13070229` | [enlace](https://www.mdpi.com/2220-9964/13/7/229/pdf?version=1719814861) |
| Jinguang Sui, Peng Chen et al. (2024) | Deep Spatio-Temporal Graph Attention Network for Street-Level 110 Call Incident Prediction | Applied Sciences | 8 | `10.3390/app14209334` | [enlace](https://doi.org/10.3390/app14209334) |
| Robin Khalfa, Naomi Theinert et al. (2025) | Comparing XAI techniques for interpreting short-term burglary predictions at micro-places | Computational Urban Science | 6 | `10.1007/s43762-025-00185-x` | ✅ `papers/khalfa2025_xai.pdf` |
| Bahram Lavi, Eric K. Tokuda et al. (2022) | 17K-Graffiti: Spatial and Crime Data Assessments in São Paulo City | International Joint Conference on Computer Vision, Imaging and Computer Graphics Theory and Applications (VISIGRAPP) | 6 | `10.5220/0010883300003124` | [enlace](https://doi.org/10.5220/0010883300003124) |
| Silveira, Jaqueline, Germain Garcia-Zanabria et al. (2022) | TensorAnalyzer: Identification of Urban Patterns in Big Cities using Non-Negative Tensor F | arXiv (Cornell University) | 4 | `10.48550/arxiv.2210.02623` | ✅ `papers/tensoranalyzer2022.pdf` |
| Luis G. Nardin, Giulia Andrighetto et al. (2016) | An Agent-Based Model of Extortion Racketeering | Computational social sciences | 3 | `10.1007/978-3-319-45169-5_7` | cerrado |
| Marcos M. Raimundo, Germain Garcia-Zanabria et al. (2025) | CounterCrime - Using Counterfactual Explanations to Explore Crime Reduction Scenarios | IEEE Transactions on Visualization and Computer Graphics | 3 | `10.1109/tvcg.2025.3586202` | [enlace](https://doi.org/10.1109/tvcg.2025.3586202) |
| Juanpablo Heredia, Leighton Estrada-Rayme et al. (2025) | Interactive Exploration and Explanation of Spatio-Temporal Anomalies with Graph-LLM Integr | SIBGRAPI Conference on Graphics, Patterns and Images (SIBGRAPI) | 3 | `10.1109/sibgrapi67909.2025.11223398` | cerrado |
| Tuğrul Cabir Hakyemez, Bertan Badur (2026) | Enhancing Deep Learning-based Crime Hotspot Predictions With Theory-based Environmental Ri | Applied Spatial Analysis and Policy | 2 | `10.1007/s12061-025-09789-6` | ✅ `papers/hakyemez2026_teoria.pdf` |
| Luz Anamar González de la Rosa, Luis Javier Sánchez-Martínez (2026) | Analyzing the relationship between homicides and police reports in Peru: A multivariate an | International journal of law, crime and justice | 1 | `10.1016/j.ijlcj.2026.100859` | [enlace](https://doi.org/10.1016/j.ijlcj.2026.100859) |
| Ethan Brewer, Giovani Valdrighi et al. (2024) | Granularity at Scale: Estimating Neighborhood Socioeconomic Indicators From High-Resolutio | IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing | 1 | `10.1109/jstars.2024.3368018` | ✅ `papers/granularidad_satelital2024.pdf` |
| Juanpablo Heredia, Leighton Leandro Estrada-Rayme et al. (2026) | GroundSTory: Interactive Storytelling for Grounded Spatiotemporal Anomaly Explanations wit | ACM Transactions on Intelligent Systems and Technology | 0 | `10.1145/3856820` | cerrado |
| Giovani Valdrighi, Germain Garcia-Zanabria et al. (2026) | ManyWaves: A Visual Analytics Approach for Exploring Multivariate Spatiotemporal Data Base | Computer Graphics Forum | 0 | `10.1111/cgf.70653` | [enlace](https://doi.org/10.1111/cgf.70653) |
| Joel Perca, Luis Sante et al. (2026) | UrbanClipAtlas: A Visual Analytics Framework for Event and Scene Retrieval in Urban Videos | arXiv (Cornell University) | 0 | `10.48550/arxiv.2604.15225` | ✅ `papers/urbanclipatlas2026.pdf` |
|  (None) |  |  | None | `10.11606/t.55.2021.tde-09042021-1614` | cerrado |

**Citados en el texto pero sin DOI verificado en esta sesión** (verificar antes de ponerlos en una lámina):
Townsley (2003), robos infecciosos; Johnson & Bowers (2004); Braga et al. (2009), concentración de violencia
armada en micro-lugares en Boston; Braga et al. (2019), revisión sistemática de *hot spots policing*;
Slack et al. (2021), manipulación de atribuciones de features; García-Zanabria (2021), tesis
*Visual Crime Pattern Analysis*, USP, DOI `10.11606/t.55.2021.tde-09042021-1614`.
