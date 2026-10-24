# Brainstorm 4 — buscar un núcleo técnico que nadie haya hecho (viernes 23, 20:30 PT)

**Por qué existe este documento:** Freddy no se convenció de incendios. La detección ya la resuelve
Satellites on Fire (US$2.7M, 35 min antes que NASA) y un proyecto de curso ya mide el área quemada.
Si lo difícil ya lo hace otro, lo nuestro queda como «una capa encima».

**Primer principio. El núcleo difícil tiene que cumplir tres cosas:**
1. **Medir algo nuevo** que hoy no se mide barato (lo que hizo ganar a Peel en HackMIT).
2. **Salir del stack de Ricardo**: detección de cambios multitemporal en satélite, visión por computadora, imágenes biomédicas, XAI.
3. **Llegar a una comunidad que hoy no lo recibe.**

Fuentes y verificación: `research/hard-tech-feasibility.md`. Lo marcado *(secundario)* hay que confirmarlo en la fuente primaria antes de ponerlo en una lámina.

---

## Opción 1 · Casas en quebradas de Lima, donde baja el huaico ⭐

**Comunidad:** familias que compran lotes en las laderas y quebradas de Chosica, Chaclacayo y San Juan
de Lurigancho, muchas veces a traficantes de terrenos.

**Por qué ahora:** ENFEN mantiene **alerta de El Niño Costero** (comunicado N°18-2026, 16 de octubre),
de magnitud extraordinaria hasta enero de 2027, con lluvias sobre lo normal en la costa central. En 2017
el Niño Costero dejó **~24,800 personas afectadas por huaicos en Lima**, sobre todo en esos tres distritos.

**El núcleo técnico (es literalmente el trabajo futuro del paper de Ricardo: «detectar construcciones ilegales en Perú»):**
1. **Dónde baja el agua.** Trazar los cauces de huaico desde un modelo de elevación (acumulación de flujo). CENEPRED tiene mapas, pero casi todos en PDF, así que este cálculo es nuestro.
2. **Qué se construyó ahí y cuándo.** Detección de cambios de edificaciones año a año. Google Open Buildings 2.5D Temporal cubre Latinoamérica, **2016–2023, ~4 m**, en Earth Engine. Para 2024–2026, el modelo de Ricardo sobre Sentinel-2 (10 m, ve grupos de casas, no casa por casa).
3. **El cruce:** edificaciones nuevas dentro de cauces activos → riesgo por manzana, con explicación de por qué (XAI, otra línea de Ricardo).

**Claude:**
- Para la familia: manda la ubicación del lote por WhatsApp y recibe en lenguaje claro: «Este lote está dentro de un cauce por donde bajó agua en 2017; estas 40 casas se construyeron ahí desde 2019». Y qué preguntar antes de comprar.
- Para el municipio: el reporte de qué se construyó dónde, listo para Defensa Civil.

**Dónde falla:** decirle a una familia que su casa está en riesgo cuando no lo está, o al revés. La
resolución no da para casa por casa. Protección: el tono es «revise con Defensa Civil», nunca «su
casa se va a caer»; se muestra la imagen y el cauce para que la persona lo vea ella misma.

**Lo que hay que confirmar:** que los tiles de Lima de Open Buildings Temporal tengan datos (una consulta en Earth Engine).

---

## Opción 2 · El agua de Huancavelica que riega Ica, medida desde el espacio

**Comunidad:** las comunidades altoandinas de Huancavelica alrededor de Choclococha, cuyos bofedales se secan.

**El problema:** desde los años 50 se trasvasan unos **150 millones de m³** de agua de Choclococha
(Huancavelica) a Ica, donde riega la agroexportación. Las comunidades de altura dicen que sus bofedales se
secan (LEISA, DESCO, Salud con Lupa, OjoPúblico). En Ica los acuíferos se sobreexplotan. **Une los dos
lugares de Freddy.**

**El núcleo técnico:**
- **Fácil:** detectar campos regados y reservorios nuevos que aparecen en el desierto con Sentinel-2. ANA misma midió 46,434 ha regadas desde satélite.
- **Lo difícil y novedoso:** estimar **cuánta agua consume cada campo** (evapotranspiración desde el satélite) y compararla con el derecho de agua que tiene; del otro lado, medir cómo cambia el verde de los bofedales de Choclococha año a año.

**Claude:** convierte el hallazgo en un pedido de acceso a la información a la ANA o en un resumen para la
comunidad y para un consejero regional.

**Dónde falla:** acusar a alguien de usar agua ilegal. El registro de la ANA no prueba que un derecho no
exista. Protección: se habla de «uso a verificar», nunca de «usuario ilegal».

**Lo que hay que confirmar:** qué tan precisas son las capas de derechos y pozos de la ANA.

---

## Opción 3 · Tamizaje de anemia con una foto del ojo

**Comunidad:** mamás de niños de 6 a 35 meses en Huancavelica. ENDES 2025: **34.9%** de anemia a nivel
nacional; Huancavelica **54.5%** *(secundario)*.

**El núcleo técnico:** modelo sobre fotos del párpado inferior (conjuntiva). Datos: Eyes-defy-anemia
(Kaggle, 218 fotos con hemoglobina de laboratorio, CC BY-SA) y CP-AnemiC (Ghana, 710 niños).

**El problema:** **ya existe en Perú** (AnemiaApp de MIDIS con Cayetano Heredia; DetectAnemia de Lolimsa
con uñas), y la conjuntiva da baja sensibilidad (54% en un estudio de 2024; 0.71 en niños peruanos).
Novedad débil y riesgo médico alto. **Descartada como titular.**

---

## Opción 4 · Reconocimiento de voz en quechua chanka para lectura

Ajustar un modelo de voz a texto al quechua de Huancavelica para medir la fluidez lectora de niños de
escuelas bilingües. Lo más novedoso y lo más difícil, pero casi no hay datos de voz en quechua. **Demasiado
riesgoso para 36 horas.**

---

## Recomendación

1. **Opción 1, quebradas en Lima.** Es la línea de investigación de Ricardo, los datos son abiertos, el
   peligro es de ahora (El Niño activo) y tiene política adentro (traficantes, titulación en zonas de
   riesgo). La demo: un jurado elige un punto del mapa de Chosica y ve las casas apareciendo año a año
   dentro de un cauce.
2. **Opción 2, agua Huancavelica–Ica**, si a los dos les mueve más la historia. Si el núcleo es la
   evapotranspiración por campo, es igual de difícil y más personal para Freddy.

**La decide Ricardo:** ¿cuál puede entrenar y mostrar funcionando en 36 horas?
