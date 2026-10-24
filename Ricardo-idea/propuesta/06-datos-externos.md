# Datos externos: qué cruzamos, en qué orden, y si vale la pena bajar satélite

> Pregunta directa de Ricardo: *"¿qué data usaríamos? ¿bajaremos data satelital?"*
> Respuesta corta: **sí, pero el satélite es la tercera prioridad, no la primera.** A escala de corredor
> (300–800 m) hay fuentes abiertas peruanas con mucha mejor resolución que cualquier píxel.
> Todo lo marcado **(por confirmar)** hay que verificarlo antes de ponerlo en una lámina o depender de ello.

## El criterio

Cada fuente tiene que responder una de estas tres preguntas, o no entra:

1. **Denominador** — ¿cuántos negocios hay expuestos en este corredor? Sin esto, el conteo no significa nada.
2. **Intervención** — ¿qué le pasó a este corredor (obra, alumbrado, cámara) y cuándo? Es lo que permite
   preguntar si algo sirvió.
3. **Exposición** — ¿qué hace a este corredor un objetivo? Ruta de transporte, mercado, colegio, grifo.

## Nivel 1 — Indispensable, se baja el viernes o el sábado temprano

| Fuente | Qué da | Formato / acceso | Pregunta |
|---|---|---|---|
| **Denuncias PNP** (ya la tenemos) | 3.1M hechos geolocalizados 2018–2025-06 | CSV 1.8 GB local | la variable objetivo |
| **OpenStreetMap, red vial** | Aristas, nombres, jerarquía, intersecciones → los corredores | `osmnx`, descarga directa, ODbL | la unidad de análisis |
| **OpenStreetMap, POIs** | `shop`, `amenity`, `office` por corredor | `osmnx` / Overpass | denominador, piso bajo |

OSM subregistra la bodega de barrio limeña, así que su conteo es un **piso**, no una medición. Hay que
decirlo así.

## Nivel 2 — Alto valor, peruano y abierto. Esto es lo que de verdad nos diferencia

| Fuente | Qué da | Acceso | Pregunta |
|---|---|---|---|
| **Padrón RUC de SUNAT** | Establecimientos con dirección y ubigeo. **El denominador real de negocios**, bodega por bodega, con actividad económica (CIIU) y estado de actividad | Descarga pública de SUNAT, archivo grande **(por confirmar: formato, si trae dirección completa y si se puede geocodificar a cuadra)** | denominador |
| **INFOBRAS (Contraloría)** | Registro de obras públicas con ubicación, monto, fechas de inicio y fin. **Son los eventos de intervención**: alumbrado, parques, cámaras | Portal de la Contraloría, consulta pública **(por confirmar: si la ubicación es punto o solo distrito)** | intervención |
| **Rutas de transporte, ATU** | Trazas de rutas de combi y corredores. La extorsión a transportistas sigue rutas, no manzanas | ATU / portales de datos abiertos **(por confirmar: si hay GTFS de Lima)** | exposición |
| **Censo de Mercados de Abastos (INEI)** | Mercados con ubicación. Un mercado es un objetivo concentrado de cobro | INEI, datos abiertos | exposición |
| **Censo 2017 (INEI)** por manzana | Población, viviendas, características socioeconómicas | INEI / REDATAM | contexto |
| **Observatorio de Seguridad Ciudadana (Mininter)** | Series oficiales y reportes de extorsión | Portal del Observatorio | validación externa de nuestras cifras |

**El padrón RUC es la pieza más valiosa de esta lista.** Convierte "12 denuncias" en "12 denuncias entre
los 43 negocios registrados de esta cuadra", que es una frase que un bodeguero entiende de inmediato y que
ningún mapa de criminalidad peruano muestra hoy.

## Nivel 3 — Satélite. Sí, pero sabiendo para qué sirve cada uno

| Producto | Resolución | Qué puede y qué no |
|---|---|---|
| **VIIRS / Black Marble (VNP46A3)** | 500 m, mensual, 2012→ | Da contexto de actividad nocturna del barrio. **No mide el alumbrado de una cuadra**: el píxel es más grande que el corredor. Entra como variable de contexto y se declara la limitación |
| **Google Open Buildings** | Huellas de edificación; la versión 2.5D Temporal da altura y año, ~4 m, 2016–2023 | Densidad construida y cambio por corredor. Es el insumo satelital más útil que tenemos. **(por confirmar: cobertura real sobre Lima en Earth Engine)** |
| **Sentinel-2** | 10 m, cada 5 días, gratis | Cambio de uso de suelo y aparición de nuevas manzanas. A 10 m **no distingue bodegas**. Sirve para periferia que crece, no para el centro de SJL |
| **Street View / Mapillary** | Nivel de calle | **Mucho mejor resolución que cualquier satélite para esto.** Es la fuente honesta para desorden físico, rejas, cortinas metálicas, iluminación real. El grupo de Poco ya lo usa para percepción de seguridad (ver `05-estado-del-arte.md` §4.b). Google cobra por la API; **Mapillary es abierto (por confirmar: cobertura en SJL y Comas)** |

**La frase honesta para el pitch:** *"Usamos satélite donde el satélite es la mejor fuente —densidad
construida y crecimiento urbano— y no lo usamos donde es peor que otra cosa. Para saber cuántos negocios
hay en una cuadra, el padrón de SUNAT le gana a cualquier píxel."* Esto suena mucho mejor ante un jurado
técnico que forzar satélite en todas partes, y además es cierto.

**Dónde entra la línea de investigación de Ricardo:** detección de cambios multitemporal sobre Open
Buildings y Sentinel-2 para medir **qué cambió en el corredor y cuándo** —construcción nueva, manzana
nueva, actividad nocturna— y usar ese cambio como variable del modelo y como evento de intervención
cuando coincide con una obra de INFOBRAS.

## Nivel 4 — Si sobra tiempo, que no va a sobrar

- Precios de alquiler comercial o avisos de traspaso de negocios: proxy del efecto económico de la
  extorsión. Requiere raspado de portales, y los términos de uso son un problema.
- Noticias locales geolocalizadas para detectar hechos no denunciados.
- Denuncias de la Fiscalía, si publican con geolocalización.

## Qué se baja esta noche (viernes)

Lo que no dependa de confirmar nada:

1. Grafo OSM de San Juan de Lurigancho, Comas y San Martín de Porres (`osmnx`, minutos).
2. POIs comerciales de OSM de los mismos distritos.
3. Padrón RUC de SUNAT, si el archivo está disponible y se puede filtrar por ubigeo.
4. VIIRS mensual de Lima, 2018–2025, si Earth Engine responde rápido.

Lo demás se decide el sábado con el modelo base ya corriendo. **Ninguna fuente del nivel 2 o 3 justifica
retrasar la tabla corredor-semana**, que es lo que desbloquea todo lo demás.

## Riesgo de este plan

Cruzar muchas fuentes es donde los proyectos de hackathon se mueren: cada cruce trae geocodificación,
nombres que no coinciden, ubigeos cambiados y un día perdido. **La regla es: el modelo base corre con OSM
y las denuncias solamente.** Cada fuente externa entra después, una por una, y solo si mejora el PAI en la
partición de validación. Esa decisión se documenta en el ablation (`07-ablation.md`).
