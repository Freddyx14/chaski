# Plan de 36 horas

> Entrega en Devpost: **domingo 25 de octubre, 9:00 AM PT**. Estar en el local a las 8:00 AM del sábado.
> El equipo entero se queda en la mesa de 10:30 a 12:30 del domingo.
> Regla del evento: todo el código se empieza en el evento.

## Antes de dormir el viernes (sin escribir código del proyecto)

- [ ] Ricardo: correr las validaciones 1 y 2 de `propuesta/09-validaciones.md` §"Lo que todavía falta
      validar" (grafo con `osmnx` y snap al corredor). Definen si la unidad es el corredor o hay que caer
      a una malla hexagonal, y eso cambia todo lo demás.
- [ ] Ricardo: dejar descargado el grafo OSM de Lima Metropolitana y el CSV ya explorado. Preparar el
      entorno (`uv`, DuckDB) para no perder la mañana en instalación.
- [ ] Freddy: leer `01-propuesta.md` y decir si lo compra. Si no, se discute el sábado temprano, no a
      medio camino.
- [ ] Los dos: conseguir **una conversación con un bodeguero o transportista afectado**. Una llamada de
      diez minutos cambia el pitch entero. Es el criterio 2 de Anthropic.
- [ ] Confirmar el canal de WhatsApp disponible y si hace falta número de prueba.

## Sábado

**08:00–09:00 · Acuerdo.** Cerrar el contrato JSON de `02-diseno-tecnico.md` §6. Nadie escribe código
antes de eso. Crear el repo y las dos ramas.

**09:00–12:00 · Ricardo: datos a corredor.**
DuckDB filtra los tres distritos → `osmnx` arma el grafo → snap de incidentes → corredores → tabla
corredor × semana en Parquet. Al terminar: cuántos incidentes se descartaron por distancia, y cuántos
corredores quedaron.
**Freddy en paralelo:** esqueleto de WhatsApp respondiendo con datos falsos que ya cumplen el contrato
JSON. Así el front no espera al modelo.

**12:00–15:00 · Modelo base.**
Features, etiqueta `y_escala`, partición temporal, gradient boosting, AUC-PR y recall en el top-k contra
el baseline "más extorsión el mes pasado". SHAP. **Punto de control de las 15:00: si el modelo no le gana
al baseline, se corta el escalamiento y el producto pasa a ser corredores análogos + tasa por negocio.**

**15:00–18:00 · Unir.**
API FastAPI con el contrato real. Freddy conecta Claude: las cuatro tareas de `01-propuesta.md`, con las
reglas de qué no decir escritas en el prompt del sistema. Mapa con los corredores y el frente.

**18:00–21:00 · El bucle en vivo.**
`POST /reporte-anonimo` funcionando de punta a punta: el jurado manda un mensaje y el corredor cambia en
el mapa. Esta es la parte que vuelve el demo memorable, y por eso va antes que cualquier mejora de modelo.

**21:00–00:00 · Lo que sobre, en este orden.**
1. Denominador de negocios (OSM, y Open Buildings si está).
2. Corredores análogos.
3. GNN con `torch_geometric`.
4. Hawkes solo si todo lo anterior está cerrado, que probablemente no pase.

## Domingo

**00:00–03:00 · Congelar y pulir.** Nada de features nuevas. Ensayar el demo tres veces seguidas.
Capturar el video de respaldo, que Devpost exige para los jurados asíncronos.

**03:00–06:00 · README, Devpost, láminas.** El README lleva las métricas reales y las fallas declaradas.
Las láminas: una estadística de apertura, la comunidad nombrada, el demo, el modelo con su número honesto,
las fallas con su guarda, el camino a producción.

**06:00–08:00 · Dormir por turnos.** En serio.

**08:00–09:00 · Enviar.** Repo público, imagen, video, opt-in a los tracks.

## División

**Ricardo:** DuckDB, grafo, snap, tabla corredor-semana, modelo, holdout, SHAP, API.
**Freddy:** WhatsApp, voz, capa Claude, mapa, Devpost, pitch.
**Juntos:** el contrato JSON (8:00 sábado), el punto de control de las 15:00, los ensayos del demo.

## Qué se corta primero si el tiempo aprieta

1. Hawkes.
2. GNN.
3. Open Buildings y VIIRS (queda solo el conteo de POIs de OSM, declarado como piso).
4. Corredores análogos.
5. Voz (queda solo texto en WhatsApp).

**Nunca se cortan:** el holdout temporal honesto, el aviso de subregistro en cada respuesta, y el bucle
del reporte anónimo.

## Demo de 3 minutos

1. **0:00–0:20.** La estadística de apertura. 588 denuncias en 2018, 5,755 en medio 2025, 18 registros de
   "cupos laborales" en siete años.
2. **0:20–0:50.** Quién es el usuario, con la voz de la persona con la que hablamos.
3. **0:50–1:50.** El teléfono del jurado manda una ubicación de SJL y recibe la respuesta de Claude. El
   jurado manda un reporte anónimo y el mapa cambia.
4. **1:50–2:30.** El modelo: qué predice, contra qué baseline, con qué recall sobre 2025, y la explicación
   SHAP detrás de la frase que acaba de leer.
5. **2:30–3:00.** Dónde falla y qué guarda tiene cada falla. El riesgo de "lista de compras" se dice en voz
   alta: es lo que separa esto de un mapa de criminalidad más.

## Decisiones ya tomadas

- Comunidad: bodegueros y transportistas de SJL, Comas y SMP.
- Núcleo: escalamiento a violencia armada + corredores análogos. Hawkes es stretch.
- Tracks: Anthropic + People-First Social Impact + Microsoft Real World.
- Sin mapa público de territorios. Sin atribución a bandas. Sin datos de personas.
