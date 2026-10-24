# Brainstorm 5 — problemas que se resuelven con visión por computadora (viernes 23, 21:15 PT)

Pedido de Freddy, para traer a la conversación con Ricardo. **Todavía sin verificar**: ninguna cifra nueva
entra aquí hasta que se confirme. Cada idea se mide después con `criterios.md`.

El filtro: que use lo que Ricardo ya domina (cambio multitemporal en satélite, imágenes de calle,
imágenes biomédicas, XAI), que toque Huancavelica, Ica o Lima, y que Claude haga algo que importe.

## Las que más prometen

### V1 · Los bofedales que se secan en Huancavelica (satélite, multitemporal) ⭐
- **El problema (de `research/peru-incendios-andes.md` y `hard-tech-feasibility.md`):** desde los años 50 se trasvasan ~150 millones de m³ de agua de Choclococha (Huancavelica) a Ica, y las comunidades de altura dicen que sus bofedales se secan.
- **La visión:** medir con Sentinel-2 (gratis, desde 2017) y Landsat (desde los 80) cuánto bofedal perdió cada comunidad campesina, año por año. Es la especialidad exacta de Ricardo, detección de cambios multitemporal, aplicada a vegetación en vez de edificios.
- **Claude:** convierte el resultado en el documento que la comunidad lleva a la ANA o al gobierno regional, en castellano y quechua.
- **Por qué es fuerte:** une Huancavelica e Ica, tiene política adentro, nadie lo está midiendo por comunidad (por confirmar), y la demo es un mapa que se seca delante del jurado.
- **Riesgo:** los bofedales también cambian por lluvia y temporada. El modelo tiene que separar sequía de tendencia, y eso es justo lo técnicamente difícil.

### V2 · La receta y la caja de medicina, leídas y explicadas en quechua (une con la idea A)
- **El problema:** la paciente sale de la posta con una receta escrita a mano en castellano y una caja de pastillas que no puede leer. La mamá de Freddy es la única enfermera que habla quechua en la posta de Pilpichaca.
- **La visión:** foto de la receta (letra a mano) y de la caja → leer el medicamento, la dosis y la frecuencia.
- **Claude:** lo explica en audio en chanka y le pide que lo repita para comprobar que entendió.
- **Por qué es fuerte:** es la idea A con un núcleo de visión. La prueba la hace la mamá de Freddy con recetas reales (sin datos personales).
- **Riesgo:** leer mal una dosis. Protección: si la confianza es baja no se lee, se pide que la enfermera la confirme.

### V3 · Lengua de señas peruana
- **El problema:** las personas sordas tienen el mismo problema que los quechuahablantes, el Estado no habla su lengua. Por confirmar cuántos intérpretes hay.
- **La visión:** reconocimiento de señas con pose de manos y cuerpo, en video.
- **Por qué es fuerte:** es visión por computadora pura y sigue el tema de «lenguas».
- **Riesgo:** casi no hay datos de la lengua de señas peruana, y ninguno de los dos la vivió.

## Otras, menos fuertes

| Idea | Visión | Por qué baja |
|---|---|---|
| Rancha de la papa (tizón tardío) por foto de la hoja | Clasificación de hojas (hay datasets públicos) | Idea muy repetida en hackathons y ya hay apps; solo sería nueva por el quechua |
| Talla y peso del niño por foto (desnutrición crónica, controles CRED de la posta) | Antropometría desde imagen | Ya existe Child Growth Monitor (por confirmar si sigue vivo); precisión difícil de mostrar en vivo |
| Huaicos y derrumbes en las carreteras de Huancavelica después de lluvia | Cambio en Sentinel-1/2 | La demo depende de que haya llovido |
| Casas en quebradas de Lima | Cambio de edificaciones | Freddy no se convenció |
| Minería informal en Nasca y Palpa | Cambio en satélite | Políticamente cargado, difícil de accionar |
| Mercurio en las casas de adobe | — | El mercurio no se ve en una imagen |
| Puntos de criminalidad desde imágenes de calle (investigación de Ricardo) | Percepción visual | Riesgo de estigmatizar barrios; un jurado de Anthropic lo cuestionaría |

## Para la conversación con Ricardo

- **V1 es su paper aplicado a la tierra de Freddy.**
- **V2 es la idea A con visión.**
- Las dos se pueden medir esta noche con `criterios.md`.
