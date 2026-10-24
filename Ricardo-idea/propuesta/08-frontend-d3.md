# Frontend: analítica visual en D3 v7

> Para la sesión B (Freddy). Depende del contrato JSON de `02-diseno-tecnico.md` §6 y de las reglas de
> privacidad de `01-propuesta.md`. Paleta y reglas de gráfico verificadas con el validador de la skill
> `dataviz` (resultados abajo, §7).

## 0 · Dos rutas, una base de código

| Ruta | Usuario | Qué muestra | Qué NO muestra |
|---|---|---|---|
| `/ciudadano` | Bodeguero, transportista. Teléfono | Su corredor y nada más: señal, riesgo, frente, qué hacer | **Ningún mapa de la ciudad.** Ningún otro corredor. Ningún ranking |
| `/analista` | Municipalidad, Mininter, gobierno regional. Laptop | El mapa completo del distrito, series, desplazamiento, explicabilidad, exportar | Nada a nivel de negocio o persona |

Esa separación no es de producto, es de seguridad: un mapa de corredores marcados en el teléfono de la
víctima es también un mapa para el extorsionador. `01-propuesta.md` lo trata como falla con guarda.

## 1 · Proyección y geometría

**Regla: toda medida en metros se calcula en el pipeline, nunca en el navegador.**
En `pipeline/` se proyecta a **EPSG:32718 (UTM 18S)**, que es la zona de Lima, para longitudes, buffers y
distancias. El navegador recibe GeoJSON en **EPSG:4326 (WGS84)** y solo dibuja.

En D3:

```js
const proj = d3.geoMercator().fitExtent([[16, 16], [w - 16, h - 16]], corredoresGeoJSON);
const path = d3.geoPath(proj);   // para SVG
const pathCanvas = d3.geoPath(proj, ctx);  // mismo generador, contexto canvas
```

`fitExtent` en vez de `fitSize` deja el margen de 16 px que el layout necesita en móvil.

**Sin tiles de mapa base.** Tres razones, en orden de peso:

1. Ya tenemos la geometría vial de OSM; dibujarla nosotros da control total del estilo claro/oscuro.
2. Un demo que depende de un servidor de tiles externo se cae cuando el wifi del venue se satura. Pasa
   siempre.
3. Menos dependencias externas, menos problemas de CSP si esto termina publicado.

Se dibuja el contexto en dos capas grises: la red vial completa como hairline, y encima los corredores con
dato.

**Si en algún momento se agregan tiles**, hay que usar Mercator con `scale = (256 * 2**z) / (2π)` y
`translate` alineado al origen del esquema de tiles, o el dibujo vectorial queda desfasado del raster.

## 2 · Canvas para la red, SVG para la interacción

Tres distritos de Lima son del orden de **10,000 a 30,000 segmentos**. Un `<path>` por segmento mata al
navegador al hacer zoom.

| Capa | Tecnología | Qué lleva |
|---|---|---|
| Fondo | Canvas | Red vial completa, hairline |
| Datos | Canvas | Corredores coloreados por la métrica activa |
| Selección | Canvas oculto (*picking*) | Un color único por `corredor_id`, para saber qué hay bajo el cursor |
| Anotación | SVG encima | Corredor seleccionado, etiquetas directas, flechas del frente, leyenda |

El canvas de *picking* es la parte que la gente no implementa y luego sufre: se dibuja la misma geometría
con `strokeStyle` = un color derivado del índice del corredor, con `lineWidth` más grueso (12 px, para que
el dedo en móvil acierte), y en `mousemove` se lee un pixel con `getImageData(x, y, 1, 1)`. Es exacto y
cuesta O(1), mientras que buscar el segmento más cercano entre 30,000 cuesta cada frame.

Zoom con `d3.zoom()` aplicado al contexto:

```js
ctx.save();
ctx.translate(t.x, t.y); ctx.scale(t.k, t.k);
ctx.lineWidth = 1.5 / t.k;      // grosor constante en pantalla
pathCanvas(geojson); ctx.stroke();
ctx.restore();
```

Redibujar con `requestAnimationFrame`, nunca directo en el evento de zoom.

## 3 · Las cinco vistas, y qué gráfico es cada una

**V1 · Mapa de riesgo.** Magnitud continua → **rampa secuencial de un solo tono, azul claro a oscuro**.
Nunca arcoíris. El corredor sin dato se queda en el gris del fondo, no en el paso más claro de la rampa,
para no confundir "cero" con "no sabemos".

**V2 · Mapa de cambio.** Pregunta: *¿subió o bajó respecto al periodo anterior?* Es polaridad → **paleta
divergente azul ↔ rojo con gris neutro en el medio**. El cero tiene que caer exactamente en el gris.

**V3 · Serie del corredor.** Línea semanal de denuncias de extorsión con los hechos violentos marcados
como puntos encima. **Un solo eje.** Si hace falta mostrar la tasa por 100 negocios además del conteo, son
dos gráficos pequeños apilados, **nunca dos escalas en el mismo eje**.

**V4 · Corredores análogos.** *Small multiples*: 4 a 6 sparklines del mismo tamaño y la misma escala,
con el corredor consultado primero y resaltado. La escala compartida es lo que hace honesta la
comparación.

**V5 · Explicabilidad (SHAP).** Barras horizontales divergentes: hacia la derecha lo que sube el riesgo,
hacia la izquierda lo que lo baja, ordenadas por magnitud, máximo seis. Cada barra lleva la frase en
castellano, no el nombre de la variable: *"subió la extorsión en calles conectadas hace 2 semanas"*, no
`ext_vec1_lag_2`.

**Vista de desplazamiento (la que pidió Ricardo).** Es la más delicada. Muestra, para un corredor con
caída reciente, los corredores vecinos cuya serie subió en la ventana siguiente, con un arco del uno al
otro y el desfase en semanas.
**Etiquetarla "co-movimiento observado", nunca "desplazamiento".** La literatura dice que el
desplazamiento espacial es menor de lo que la intuición supone y a veces hay difusión de beneficios
(`05-estado-del-arte.md` §3). Una flecha en un mapa afirma causalidad sin querer. El texto de la vista
dice qué se observó y qué no se puede concluir.

## 4 · Interacción

- **Hover** en todo: tooltip con nombre del corredor, semanas con denuncia, riesgo y percentil. Área de
  acierto más grande que la marca (los 12 px del canvas de picking).
- **Clic** fija la selección y abre el panel lateral con V3, V4 y V5.
- **Línea de tiempo** con `d3.brushX` sobre la serie agregada del distrito; mover el brush repinta el
  mapa. Es el gesto que hace evidente la evolución, que era la idea original de Ricardo.
- **Filtros en una sola fila** encima del mapa: distrito, tipo de hecho, ventana.
- **Teclado**: tab recorre los corredores del ranking, enter selecciona. Sin esto no hay accesibilidad real.
- **Vista de tabla** siempre disponible (botón "ver datos"). Es obligatoria: el verde-agua de la paleta
  queda por debajo de 3:1 de contraste en modo claro, y la regla de alivio exige etiquetas visibles o
  tabla.

## 5 · Tema claro y oscuro

El oscuro no es invertir el claro: son pasos propios de la misma rampa. Se definen como variables CSS
bajo los dos ámbitos (media query del sistema y atributo del usuario), de modo que el interruptor gane
en ambas direcciones:

```css
.viz { color-scheme: light;
  --surface-1:#fcfcfb; --tinta-1:#0b0b0b; --tinta-2:#52514e; --tinta-mute:#898781;
  --grid:#e1e0d9; --eje:#c3c2b7;
  --serie-1:#2a78d6; --serie-2:#eb6834; --serie-3:#1baf7a;
  --seq-100:#cde2fb; --seq-250:#86b6ef; --seq-450:#2a78d6; --seq-700:#0d366b;
  --div-neutro:#f0efec;
  --estado-bueno:#0ca30c; --estado-aviso:#fab219; --estado-serio:#ec835a; --estado-critico:#d03b3b;
}
@media (prefers-color-scheme: dark) { :root:where(:not([data-theme="light"])) .viz {
  color-scheme: dark;
  --surface-1:#1a1a19; --tinta-1:#ffffff; --tinta-2:#c3c2b7; --tinta-mute:#898781;
  --grid:#2c2c2a; --eje:#383835;
  --serie-1:#3987e5; --serie-2:#d95926; --serie-3:#199e70;
  --div-neutro:#383835;
} }
:root[data-theme="dark"] .viz { /* mismos valores oscuros */ }
```

Los cuatro colores de estado no cambian entre temas y **nunca** se usan como color de serie.

## 6 · Reglas que no se rompen

- **Nunca dos ejes Y.** Es el error número uno de los gráficos.
- **El color sigue a la entidad, no al ranking.** Si un filtro deja fuera corredores, los que quedan
  conservan su color.
- **Secuencial = un tono. Divergente = dos tonos con gris en el medio.** Jamás arcoíris para magnitud.
- **Etiquetas directas selectivas**, no un número sobre cada punto.
- **El texto va en tinta**, nunca en el color de la serie.
- Leyenda presente siempre que haya 2 o más series; con una sola serie, el título la nombra.
- Rejilla y ejes recesivos, marcas delgadas (2 px), puntos de 8 px o más.

## 7 · Validación de paleta (hecha, no supuesta)

```
node scripts/validate_palette.js "#2a78d6,#eb6834,#1baf7a" --mode light --pairs all
  [PASS] banda de luminosidad · [PASS] piso de croma
  [PASS] separación CVD   peor par ΔE 9.2 (deutan)
  [PASS] piso visión normal   peor par ΔE 24.0
  [WARN] contraste vs superficie  #1baf7a 2.74:1 → exige etiquetas visibles o vista de tabla

node scripts/validate_palette.js "#3987e5,#d95926,#199e70" --mode dark --pairs all
  TODO PASS, contraste ≥ 3:1
```

Tres series como máximo en vistas donde todos los pares pueden verse a la vez (mapa, dispersión,
*small multiples*). Si hace falta una cuarta categoría, se agrupa en "Otros" o se separa en facetas.
Si Freddy cambia algún color, **vuelve a correr el validador**, no lo decide a ojo.

## 8 · Ruta `/ciudadano`: qué se ve en un teléfono

Una sola columna, sin mapa de ciudad:

1. **Una cifra grande**: en cuántas de las últimas 12 semanas hubo denuncias en su corredor.
2. Una línea de texto de Claude, en castellano llano.
3. Un sparkline de su corredor, sin ejes, con la última semana marcada.
4. El aviso de subregistro, siempre visible, no escondido en un pie de página.
5. Dos botones: **qué puedo hacer** y **reportar de forma anónima**.

Nada más. Cada elemento extra en esa pantalla es un elemento que alguien asustado tiene que descartar.

## 9 · Orden de construcción

1. Cargar `contrato/fixtures/` y pintar la red vial. Sin interacción.
2. V1, el mapa de riesgo, con hover y tooltip.
3. Panel lateral con V3 y V5. Con eso ya hay demo.
4. Línea de tiempo con brush.
5. V4, análogos.
6. Vista de co-movimiento.
7. Vista de tabla y tema oscuro.

Del 1 al 3 es lo que tiene que estar a las 18:00 del sábado. Del 4 en adelante es lo que mejora el demo si
el modelo ya está conectado.
