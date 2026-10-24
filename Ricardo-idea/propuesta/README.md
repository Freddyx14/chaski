# Propuesta: corredores de extorsión en Lima

Pivote desde la idea de incendios andinos, que cae frente a Satellites on Fire
(ver `../../research/competencia.md`). Cal Hacks 13.0, equipo de Ricardo y Freddy.

| Archivo | Qué contiene |
|---|---|
| `00-datos-verificados.md` | Números consultados en el CSV de 3.1M denuncias, con cómo reproducirlos |
| `01-propuesta.md` | El problema, la comunidad nombrada, el producto, el rol de Claude, las fallas y los tracks |
| `02-diseno-tecnico.md` | Corredor como unidad, tabla de features, modelos, evaluación, contrato JSON, privacidad |
| `03-plan-36h.md` | Cronograma hora por hora, división del trabajo, qué se corta, guion del demo |
| `04-division-sesiones.md` | Reparto entre las dos sesiones de Claude (Ricardo y Freddy), contrato y ramas |
| `05-estado-del-arte.md` | 37 referencias verificadas: qué valida la propuesta y qué la corrige. PDFs en `../papers/` |
| `06-datos-externos.md` | Qué datos cruzamos, en qué orden, y para qué sirve (y no sirve) el satélite |
| `07-ablation.md` | Diseño del ablation: bloques de features, familias de modelos, protocolo y métricas |
| `08-frontend-d3.md` | Analítica visual en D3 v7: proyección, canvas, cinco vistas, paleta validada |

**En una línea:** predecir a qué tramo de avenida de Lima Norte y Este avanza la extorsión denunciada
antes de que llegue la balacera, y responderle al bodeguero por WhatsApp en castellano llano, con el
modelo explicando por qué.

Dos términos que se usan todo el tiempo y conviene fijar desde aquí:

- **Corredor:** un tramo de vía de 300 a 800 metros, la cadena de aristas de OpenStreetMap con el mismo
  nombre entre dos intersecciones grandes. Es la unidad de análisis, porque la cuadra es más chica que el
  error de geocodificación de la PNP y el distrito borra el fenómeno.
- **Señal sostenida:** denuncias de extorsión en al menos 3 de las últimas 12 semanas, con tasa por
  negocio en el decil superior del distrito. **No decimos "aquí cobran cupo":** eso no lo mide el dato.
  Definiciones completas en `02-diseno-tecnico.md` §1.1.

**El número de apertura:** 588 denuncias de extorsión en 2018, 5,755 en el primer semestre de 2025.
"Cupos laborales" aparece 18 veces en siete años y medio de registro oficial.
