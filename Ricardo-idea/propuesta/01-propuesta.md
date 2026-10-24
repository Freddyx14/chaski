# Propuesta — corredores de extorsión en Lima Norte y Este

> Cal Hacks 13.0 · Equipo: Ricardo y Freddy · Escrito el viernes 23 de octubre de 2026
> Reemplaza la propuesta de incendios andinos (`../../ideas/propuesta.md`), que cae frente a
> Satellites on Fire. Ver `../../research/competencia.md`.

## La frase de apertura

En el primer semestre de 2025 se denunciaron 5,755 extorsiones en Lima Metropolitana: a ese ritmo, 2025
cierra 42% por encima de 2024 y es el peor año del que hay registro. En 2018 fueron 588 en todo el año.
En siete años y medio, el cobro de cupo —la forma que todo el mundo en Lima reconoce— aparece 18 veces
en el registro oficial.

El Estado tiene los 3.1 millones de denuncias geolocalizadas. El bodeguero al que le tocan la puerta no
tiene nada.

## La comunidad, nombrada

**Dueños de bodegas y de pequeñas empresas de transporte en San Juan de Lurigancho, Comas y San Martín de
Porres.** No "los limeños". No "las víctimas de inseguridad". En esos tres distritos hay 8,407 denuncias
de extorsión entre 2018 y junio de 2025, y en SJL la serie pasó de 60 denuncias al año a 803 en seis meses.

Es gente que:

- sabe que en su zona se cobra cupo, pero no sabe si su cuadra ya entró;
- no denuncia porque cree que denunciar es exponerse, y porque la comisaría le pide datos que la delatan;
- se entera de que el frente avanzó cuando le balean la fachada al vecino.

**Advertencia sobre las cifras de esta sección:** los 8,407 son denuncias registradas, pero solo 2,414
tienen coordenada usable tras filtrar los puntos de volcado, y en 2025 el geocodificado se derrumba a 3.2%
(`09-validaciones.md`). El prototipo cubre toda Lima por eso.

**Pendiente antes del sábado:** una conversación real con uno. Un bodeguero, un transportista, un familiar.
El criterio de Anthropic dice "lo has vivido o hablaste con alguien que lo vivió". "Leímos los datos" es
la versión débil.

## Qué construimos

Un sistema que responde una pregunta que hoy nadie responde: **¿mi cuadra está dentro de un tramo con
señal sostenida de extorsión, y hacia dónde está avanzando?**

Un apunte de lenguaje que vale para todo el proyecto: **nosotros no observamos cobro, observamos denuncias
registradas.** La diferencia no es cosmética. Decir "aquí cobran cupo" afirma un hecho que el dato no
sostiene y estigmatiza una zona entera. Las definiciones operacionales están en `02-diseno-tecnico.md` §1.1.

El bodeguero manda su ubicación por WhatsApp. Claude le responde en castellano llano:

1. **Dónde está parado.** En cuántas de las últimas 12 semanas hubo denuncias de extorsión en su corredor,
   y con qué intensidad por cada 100 negocios, no en números crudos que no significan nada. Junto con el
   aviso de que la ausencia de denuncias no es ausencia de cobro.
2. **Hacia dónde avanza el frente.** Los corredores vecinos en el grafo vial que el modelo marca en
   ascenso.
3. **Riesgo de escalamiento.** Probabilidad de que en las próximas 4 semanas haya un hecho con arma de
   fuego o daños en ese corredor, con las tres razones que más pesan, sacadas del modelo y no inventadas.
4. **Qué hacer hoy.** Denuncia anónima, no contestar el número, conservar los mensajes, a quién acudir.
5. **La pregunta de vuelta.** "¿A ti te están cobrando?" El reporte anónimo —sin nombre, sin dirección
   exacta, solo corredor— entra al modelo y corrige el mapa en vivo.

Ese último paso es lo que hace al sistema honesto: los datos de la PNP son el pasado y están
subregistrados; la comunidad es la única fuente del presente.

## Por qué esto no es un dashboard de criminalidad

Ya existen el Observatorio Nacional de Seguridad Ciudadana, Datacrim y los mapas de Lima Cómo Vamos. Todos
agregan por distrito: 43 polígonos para 10 millones de personas. La extorsión no vive en un distrito, vive
en un corredor: el cobro recorre una avenida negocio por negocio y se expande a las vías que la cruzan.

**Qué es un corredor.** Un tramo de vía: la cadena de aristas consecutivas de OpenStreetMap con el mismo
nombre, cortada donde hay una intersección grande. Entre 300 y 800 metros. "Av. Próceres de la
Independencia, cuadras 41 a 44" es un corredor; "San Juan de Lurigancho" no lo es, y "Próceres cuadra 42"
tampoco, porque la coordenada de la PNP no tiene esa precisión. El razonamiento completo está en
`02-diseno-tecnico.md` §1.

Tres diferencias concretas:

| Lo que existe | Lo que hacemos |
|---|---|
| Conteo por distrito | Serie semanal por corredor del grafo vial, con los corredores vecinos como variable |
| Mapa de dónde pasó | Predicción de dónde escala a violencia en 4 semanas, evaluada contra 2025 |
| Conteo crudo | Tasa por cada 100 negocios expuestos, con el denominador estimado desde satélite |
| Usuario analista | Usuario bodeguero, por WhatsApp, en su idioma |

## El núcleo técnico

Está detallado en `02-diseno-tecnico.md`. En una línea: **predecir el escalamiento de extorsión a violencia
armada a nivel de corredor vial, usando la difusión en el grafo como variable, y explicar cada predicción
con las features que la empujaron.**

Lo que se mide y hoy no se mide:

1. **La ruta de cobro**, como cadena de corredores conectados, en lugar de un hotspot circular.
2. **El frente de expansión**: qué corredor vecino entra el mes que viene.
3. **La tasa por negocio expuesto**, que necesita un denominador que ningún registro público tiene y que
   se estima desde imágenes satelitales y footprints de edificaciones.

Ese tercer punto es donde entra la línea de investigación de Ricardo (detección de cambios multitemporal
en satélite) sin ser un adorno: sin denominador, un corredor con 12 denuncias y 40 bodegas se ve igual que
uno con 12 denuncias y 400.

## Qué hace Claude, y qué podría salir mal

Claude no da formato a texto. Hace cuatro cosas que un modelo de lenguaje es el único que puede hacer aquí:

1. **Traduce el riesgo a alguien asustado.** Ni pánico ni "tranquilo, no pasa nada". El registro importa:
   esta persona puede tomar una decisión económica grave a partir de la respuesta.
2. **Decide qué no decir.** Si el detalle le sirve más al extorsionador que a la víctima, no se dice.
   Claude tiene la regla y la aplica caso por caso.
3. **Clasifica el reporte anónimo** de voz o texto en modalidad y corredor, sin conservar ningún
   identificador.
4. **Redacta la denuncia anónima** lista para presentar.

**Dónde falla, dicho en el pitch, no escondido:**

| Falla | Guarda |
|---|---|
| Recall bajo: el modelo no ve un corredor que sí escaló, y alguien cree que su cuadra está limpia | Se reporta el recall real sobre el holdout de 2025; la respuesta nunca dice "tu zona es segura", dice qué se ve y qué no |
| Subregistro: cero denuncias no es cero cobro | El sistema lo dice literalmente en la respuesta, siempre |
| Reportes falsos que envenenan el mapa | Umbral mínimo de reportes independientes antes de mover el riesgo de un corredor; el reporte anónimo pesa menos que la denuncia registrada |
| **Lista de compras**: un mapa público de corredores marcados le sirve al extorsionador y estigmatiza distritos | No hay mapa público de territorios. La respuesta se da a quien pregunta por su propia ubicación. Nada a nivel de negocio ni de persona. Cero atribución a bandas con nombre |
| Falacia ecológica: el riesgo del corredor no es el riesgo de tu negocio | El lenguaje es siempre de corredor, nunca "a ti te va a pasar" |
| Afirmar cobro donde solo hay denuncias | Ninguna salida dice "aquí cobran". Dice cuántas semanas con denuncias registradas, y que eso no mide el cobro real |

## Tracks

| Track | Encaje | Qué cuesta |
|---|---|---|
| **Anthropic** (primario) | Comunidad nombrada, problema real, un flujo que funciona, Claude con criterio y fallas declaradas | Nada extra |
| **Best People-First Social Impact** | Usuarios desatendidos, impacto directo | Nada extra |
| **Microsoft — Built for the Real World** | Lámina de camino a producción: quién lo opera, costo por consulta | Una lámina |
| Convex o Spacetime | Solo si el mapa en vivo lo pide de verdad | Medio día, decidir el sábado |

Fuera: Fetch.ai (el protocolo de pagos no pinta en un servicio gratuito de seguridad), Bright Data (el
núcleo funciona sin datos web, y su regla dice que debe romperse sin ellos), Atlassian.

## Lo que todavía hay que confirmar

1. Hablar con una persona afectada real antes del sábado por la mañana.
2. Que Google Open Buildings tenga cobertura utilizable en Lima para el denominador de negocios.
3. Que el grafo OSM de los tres distritos se descargue y procese en tiempo razonable.
4. El canal de WhatsApp: API de Meta o un sandbox tipo Twilio.
5. Nombre oficial y premio del track de Anthropic, que seguía como "Coming soon" el viernes.
