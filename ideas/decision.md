# Decisión — ¿qué construimos? (viernes 23, 21:00 PT)

Medido contra `ideas/criterios.md`. Fuentes en `research/`.

**La decisión:** qué idea construir en ~36 horas para ganar el track de Anthropic (y si se puede, uno general),
con un equipo donde Freddy hace producto, agentes y pitch, y Ricardo hace visión por computadora y ML.

## Las 3 opciones finalistas

**A · El intérprete chanka para gestantes.** Las gestantes quechuahablantes de los centros de salud de
Huancavelica salen de su control prenatal sin entender del todo las indicaciones. La obstetra dicta en
castellano; Claude genera un audio en quechua chanka con las indicaciones y las **señales de alarma del
embarazo**, se lo manda por WhatsApp, y le pide que lo repita con su voz para comprobar que entendió (técnica
de *teach-back*). Si no entendió, avisa a la obstetra. **El núcleo técnico es medir algo que nadie midió:
qué tan bien manejan Claude y los demás modelos el quechua chanka en salud**, y construir la verificación que
detecta cuándo Claude se equivoca.

**B · Mercurio en las casas de Huancavelica.** ~25 mil personas viven en casas de adobe hecho con tierra
contaminada. Un mapa de riesgo por casa (con los estudios publicados y la visión por computadora de Ricardo
sobre imágenes de calle), y Claude que explica a la familia qué hacer y redacta el pedido de análisis
toxicológico a la DIRESA (solo se hicieron 22).

**C · Fuego, la última milla.** La que ya está escrita en `propuesta.md`: satélite → modelo «¿quema
planificada o se escapa?» → alerta en quechua por WhatsApp → nota de voz → reporte oficial.

## Análisis

### A · El intérprete chanka para gestantes

- **Comunidad (5).** Se puede contar y encontrar: gestantes quechuahablantes atendidas en los centros de salud de Huancavelica, y las obstetras que las atienden.
- **Problema (4).** Solo el 1% de los establecimientos de salud del país (126 de 8,441) tiene atención intercultural. Hay 52 servidores bilingües certificados en toda Huancavelica. Y está la cita de Eulogia Guzmán: «que en los hospitales y centros de salud nos hablen en quechua». Sube a 5 si alguien de la familia de Freddy lo vivió.
- **Funciona el lunes (4).** Una obstetra puede usarlo el lunes con su propio celular. La métrica: % de gestantes que repiten bien las señales de alarma, y en cuántos casos el sistema avisó a la obstetra.
- **Claude central (5).** Claude hace la interpretación, que es todo el producto, y la tabla de fallas es la más clara posible. Si traduce mal una dosis o una señal de alarma, el daño es real. Protecciones:
  1. Las señales de alarma son contenido fijo del MINSA, revisado por un hablante.
  2. Claude retraduce al castellano su propio quechua y, si no coincide, no envía y avisa.
  3. Glosario médico chanka fijo.
  4. Nada de diagnósticos, solo indicaciones que ya dio la obstetra.
  5. Si duda, deriva a la Línea 1812, la línea de intérpretes del Estado.
- **Difícil y nuevo (4).** No hay una evaluación pública de modelos en chanka; Google Translate usa chanka sin decirlo y falla más traduciendo del castellano al quechua. Construir el primer set de prueba médico en chanka, medir a Claude contra Google y mejorar con glosario y retraducción es investigación de verdad. Es un 4 y no un 5 porque no es visión por computadora: Ricardo aporta métricas y ML, pero no su especialidad.
- **Demo (4).** El jurado escucha el audio en quechua, un hablante responde con su voz, la pantalla muestra si entendió. Más el gráfico: «así de mal está cada modelo en chanka, así lo corregimos».
- **Factible (3).** Este es el punto débil. Depende de dos cosas que no tenemos confirmadas:
  1. **Un hablante de chanka** que escriba y revise las frases del set de prueba el sábado. Puede ser alguien de la familia de Freddy por teléfono.
  2. **La voz en quechua.** Que exista síntesis de voz y reconocimiento para el quechua de Ayacucho-Chanka. *Sin verificar.* Se resuelve con 1 hora de prueba mañana temprano; si falla, el texto en WhatsApp + audio grabado por el hablante para las señales fijas sigue funcionando.
- **Mejora con el uso (5).** Cada repetición mal entendida y cada corrección del hablante entran al set de prueba y al glosario.
- **Total: 85.**

### B · Mercurio en las casas

- **Comunidad (5)** y **problema (4).** Es el problema más grave y desatendido de Huancavelica: emergencia declarada en 2024, solo 22 análisis.
- **Pero falla donde importa.** El mercurio no se ve desde un satélite ni desde una foto de calle. La medición real exige un analizador de vapor de mercurio. Sin datos por casa, el «mapa de riesgo» es una adivinanza, y decirle a una familia que su casa es tóxica, o peor, que no lo es, sin medir es justo el daño que el criterio 4 nos pide evitar.
- Lo que queda es Claude explicando y redactando pedidos. Útil, pero técnicamente poco profundo (criterio 5 en 3).
- **Factible (2):** no sabemos si hay datos georreferenciados de los estudios, ni si hay fotos de calle de Huancavelica.
- **Total: 67.** Es el mejor «siguiente proyecto», no el de este fin de semana.

### C · Fuego, la última milla

- **Lo mejor que tiene:** los datos están verificados y responden en vivo (SERFOR sin llave, 3,090 límites de comunidades), y la demo es la más física, una alerta real que llega al celular del jurado. Factibilidad 4, demo 5.
- **Lo peor:** la detección ya la vende Satellites on Fire, el área quemada ya la calcula un proyecto de curso, y **Freddy no está convencido**. Treinta y seis horas sin convicción es el riesgo más grande de todos, aunque no aparezca en ninguna tabla.
- **Total: 85**, pero entra con la compuerta G4 débil.

## Tabla comparativa

| Dimensión | A · Intérprete chanka | B · Mercurio | C · Fuego |
|---|---|---|---|
| Comunidad con nombre | Fuerte (gestantes de Huancavelica) | Fuerte (25K en casas de adobe) | Fuerte (comunidades de Castrovirreyna) |
| Problema real | Fuerte (1% intercultural, cita de Eulogia) | Fuerte (emergencia, 22 análisis) | Fuerte (12 muertos en 2026) |
| Funciona el lunes | Fuerte (una obstetra, un celular) | Débil (sin medición real) | Fuerte (datos en vivo) |
| Claude central + fallas | Fuerte (traducir ES el producto) | Moderado (explica y redacta) | Moderado (alerta y reporte) |
| Difícil y nuevo | Fuerte (nadie midió el chanka) | Débil (no se mide a distancia) | Débil (la detección ya existe) |
| Demo | Fuerte (audio quechua en vivo) | Moderado (mapa) | Fuerte (alerta al celular) |
| Factible en 36 h | Moderado (falta hablante y voz) | Débil (datos por casa dudosos) | Fuerte (datos ya probados) |
| Costo (créditos, cuentas) | Fuerte ($100 en créditos alcanzan) | Fuerte | Fuerte |
| Convicción del equipo | Fuerte (es lo que Freddy pidió) | Moderado | Débil (Freddy no se convenció) |

**Lo que muestra la tabla:** A y C empatan en puntos. A gana en novedad, en el criterio de Anthropic que
más pesa en su track (saber dónde falla Claude) y en la convicción del equipo. C solo gana en certeza de los datos.

## Recomendación

**A · El intérprete chanka para gestantes.** Es lo único de la lista que nadie ha hecho, convierte la
pregunta de Anthropic («¿dónde falla Claude para esta gente?») en el producto mismo, y es el tema que
Freddy eligió.

**Segundo lugar: C, fuego.** Datos garantizados y la mejor demo.

**Esto cambia a C si:** el sábado a las 10 AM no tenemos un hablante de chanka disponible para revisar las
frases, o si la prueba de 1 hora de voz en quechua falla y el texto solo no alcanza para una demo convincente.

## Actualización (21:10 PT) — lo que cambió con la respuesta de Freddy

- **Estado:** A y C siguen en carrera. Ricardo trae otra idea; se define con él, y su idea se mide con la misma hoja (`criterios.md`).
- **Dato nuevo, y cambia A:** los padres de Freddy hablan quechua. **Su mamá trabaja en una posta de Pilpichaca (Huancavelica) y es la única enfermera que habla quechua en su centro de salud.**
  - **Criterio 2, problema real:** sube a 5. Ya no es una cifra nacional, es la mamá de Freddy siendo el único puente entre el idioma de sus pacientes y el centro de salud.
  - **Criterio 1, comunidad:** la comunidad con nombre puede ser **las pacientes quechuahablantes de la posta de Pilpichaca**. Es lo más específico posible.
  - **Factibilidad:** el hablante de chanka está resuelto, y además es alguien que conoce el vocabulario de una posta. Es también la primera usuaria posible el lunes, y la fuente del testimonio para el pitch.
  - **A sube de 85 a ~91.** Lo único que sigue abierto es la prueba de voz en quechua.
- **Cuidado:** lo que diga la mamá de Freddy entra al pitch como cita **solo con su permiso** y con sus palabras exactas.

## Lo primero que hay que hacer (si sale A)

1. **Esta noche:** ¿quién habla chanka? Freddy, su familia, la familia de Ricardo, alguien del Slack de Cal Hacks.
2. **Sábado 8:00:** prueba de 1 hora de voz en quechua chanka, en las dos direcciones (texto a audio y audio a texto).
3. **Sábado 9:00:** el set de 50 frases médicas reales (indicaciones de control prenatal y señales de alarma del MINSA), traducidas por el hablante. Es la base de la evaluación y del glosario.
