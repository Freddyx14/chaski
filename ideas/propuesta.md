# Propuesta — Cal Hacks 13.0 (versión al viernes 23 de octubre, 20:00 PT)

> Documento para alinear al equipo (Freddy + Ricardo). Resume todo lo avanzado hasta ahora.
> Las fuentes de cada dato están en `research/`. El detalle de cada idea descartada, en los otros archivos de `ideas/`.

---

## 1. El reto

**Track de Anthropic: «Claude for Public Benefit».** *Build something your community needs.*
Elegir una comunidad (gente que comparte un lugar, una circunstancia o una necesidad), encontrar un
problema real y construir algo con Claude que ayude. **Mientras más específica la comunidad, mejor.**

Lo que evalúa el jurado (lámina de Anthropic en el evento):

1. **Una comunidad con nombre.** «Estudiantes» es muy amplio; «estudiantes transferidos en Berkeley buscando vivienda» es el nivel correcto.
2. **Un problema real.** Lo viviste o hablaste con alguien que lo vivió.
3. **Un producto que funciona y tiene impacto.** Una cosa bien hecha y usable el lunes vale más que una demo amplia. Hay que decir **cómo vamos a medir el impacto**.
4. **Uso pensado de Claude.** Claude hace algo que importa, y **sabemos dónde podría fallarle a la gente que lo usa**.

**Fechas:** entrega en Devpost el **domingo 25, 9:00 AM**. Jurado de 10:30 a 12:30, los dos en la mesa,
demo en vivo, pitch de ~3 min + 2 de preguntas. Todo el código tiene que empezar en el evento.

**Créditos:** $50 de API de Claude por persona (QR en la lámina, registrarse con el correo de Cal Hacks).
**Workshop de Anthropic** sobre agentes: sábado 12:30 PM, The Theater.

**Calibración:**
- Ganador de Claude en Cal Hacks 12.0: EldaAI, cuidado de adultos mayores por voz, nacido de la demencia de la abuela del fundador. **La historia personal pesa.**
- Consejo de Héctor (jurado de HackMIT): no hacer «IA para encontrar amigos» ni «IA CFO» (35% de los equipos), **hacer algo técnicamente difícil**. Su ejemplo: que un satélite tome fotos solo en las zonas relevantes.
- Ganador de HackMIT 2026 (Peel): un sensor barato + un motor de evidencia sobre 100K registros + una sola estadística que enmarca todo + la tecnología del sponsor como cerebro del producto.

---

## 2. El problema: incendios en los Andes

Freddy es de Huancavelica. Estos datos están verificados (fuentes en `research/peru-incendios-andes.md`):

- **2026 es año El Niño.** Al 23 de octubre: 479 emergencias por incendio, **12 muertos**, 832 personas con quemaduras, 13,838 ha de vegetación perdidas en 16 regiones. 8 de los primeros 10 muertos tenían 70 años o más.
- **Huancavelica, 18 de octubre:** un incendio en Chupamarca quemó la casa del alcalde e hirió a 4 personas. Lo combatieron con baldes y mangueras de riego. SENAMHI mantuvo a Huancavelica en alerta roja.
- **2024 fue el año récord:** ~20 muertos, 22 de 24 regiones afectadas, 262,100 ha quemadas. Huancavelica fue 3.ª a nivel nacional.
- **El 98% de los incendios los causa la gente:** quema de pastos para que rebrote, roce y quema, rastrojos, sin cortafuegos.
- **La alerta no llega a quien está en el incendio.** Las alertas satelitales de SERFOR van solo a funcionarios, nunca a las comunidades. Los comuneros apagan con ramas, baldes y ropa mojada.
- **Lo que pasa en el campo no llega al registro oficial.** COEN contó 51 incendios mientras SERFOR veía 56 activos; 34 focos satelitales nunca entraron al conteo. Lo que no se registra no recibe recursos ni política.
- **El visor público de SERFOR se cayó en plena temporada** («Access denied» desde el 14 de octubre, ~1 semana).
- **La ley responde con cárcel** (4 a 10 años) pero no hay una ley de manejo integral del fuego ni reglas de quema segura.
- **En Huancavelica el 65.2% tiene el quechua como lengua materna** (INEI 2017).

**El problema en una línea:** cada eslabón existe (satélite → comunidad → registro oficial → política),
pero ninguno se conecta con el siguiente.

---

## 3. La idea

**Comunidad:** las comunidades campesinas de Huancavelica (propuesta: provincia de Castrovirreyna, donde
está Chupamarca), y en concreto la persona que cada comunidad ya designa, el **presidente comunal o el
teniente gobernador**.

### El circuito, de punta a punta

```
Satélite (SERFOR / NASA FIRMS)
   │  foco de calor
   ▼
Cruce espacial con los límites de las 3,090 comunidades  ──►  ¿qué comunidad está cerca?
   │
   ▼
MODELO (Ricardo): ¿quema planificada o incendio que se va a descontrolar?  ──►  riesgo 0–1
   │
   ├── riesgo bajo  → se registra y se muestra en el mapa, no se despierta a nadie
   └── riesgo alto  ▼
CLAUDE: alerta por WhatsApp en quechua y castellano (texto + audio)
   «Hay un foco de calor a 2 km al norte de su comunidad. ¿Pueden confirmar?»
   + pasos del protocolo oficial (Claude los adapta, no los inventa)
   │
   ▼
El dirigente responde con NOTA DE VOZ en quechua: «Sí, está quemando, llegó a la puna, necesitamos apoyo»
   │
   ▼
CLAUDE: convierte la nota de voz en un reporte estructurado (lugar, tamaño, heridos, necesidades)
   → lo presenta a la municipalidad / COEN, y la comunidad recibe una constancia
   │
   ▼
MAPA OFICIAL: incendios del satélite vs confirmados por la comunidad vs conteo oficial
   → la brecha es la evidencia que un consejero regional lleva al gobierno regional
```

**Prevención (extra):** un comunero avisa «mañana quemo mi chacra», la quema queda registrada y ese foco
deja de disparar una falsa alarma.

### El núcleo técnico (lo difícil, lo que llama la atención)

**Núcleo 2 · ¿Quema planificada o incendio que se escapa?** ⭐ recomendado
Para el satélite, todo foco de calor se ve igual. Pero un comunero quemando pasto y un fuego que se
escapa hacia la puna son emergencias completamente distintas. Entrenar un clasificador con los
**97,376 incendios y cicatrices históricas** del servidor de SERFOR, más viento, humedad y terreno, para
predecir **qué foco se convierte en incendio forestal**. Resuelve las falsas alarmas con un modelo en vez
de con una regla, y decide si se despierta o no a una familia en la puna.

**Núcleo 1 · Cicatriz de quema por comunidad** (extra si da el tiempo)
Imágenes Sentinel-2 antes y después → modelo de detección de cambios segmenta el área quemada →
**hectáreas perdidas por comunidad, aunque nadie las haya reportado**. Es justo la línea de investigación
de Ricardo (detección de cambios multitemporal). Es el remate político: «estas hectáreas no existen
para el Estado».

**Núcleo 3 · Decidir dónde mirar** (el ejemplo literal de Héctor). Interesante, pero difícil de mostrar en
vivo y su usuario es una entidad, no la comunidad. Lo dejamos como «siguiente paso».

### Dónde puede fallar Claude (criterio 4, va en el pitch)

| Riesgo | Protección |
|---|---|
| Quechua mal escrito (en Huancavelica se habla quechua chanka) | Siempre va el castellano al lado; audio para quien no lee; plantillas fijas revisadas por gente que lo habla |
| Falsa alarma (una quema planificada parece incendio) | El modelo filtra; el mensaje dice «foco detectado, ¿pueden confirmar?», nunca «incendio» |
| Consejo inventado | Claude solo elige y adapta pasos de un protocolo oficial citado (INDECI/SERFOR) |
| El modelo no detecta un incendio real (falso negativo) | Bajo el umbral igual se registra y aparece en el mapa; reportamos el recall del modelo con incendios de 2026 que no vio en el entrenamiento |
| Datos atrasados o SERFOR caído (pasó el 14 de octubre) | NASA FIRMS de respaldo; cada alerta dice qué tan viejo es el dato |
| Sin señal en la puna | Fuera de alcance este fin de semana; lo decimos con honestidad (SMS como siguiente paso) |

### Cómo medimos el impacto
- Minutos desde que aparece el foco hasta que la comunidad recibe la alerta.
- % de focos satelitales con un reporte presentado.
- Brecha cerrada contra el conteo de COEN.
- Precisión y recall del modelo sobre incendios de 2026.

### Cómo mejora con el uso (canal de retroalimentación)
Cada alerta termina con «¿Es correcto?». La respuesta de la comunidad (sí / no / nota de voz) se vuelve
una etiqueta nueva para el modelo, y las correcciones al quechua mejoran las plantillas.

---

## 4. Los datos (lo que ya se probó)

- **Servidor de mapas de SERFOR:** respondió en vivo, **sin llave**: 155 focos de calor de las últimas 24 h, 97,376 incendios y cicatrices históricas, **3,090 límites de comunidades campesinas**.
- **NASA FIRMS** (VIIRS/MODIS): llave gratis, respaldo si SERFOR se cae.
- **INDECI** (historial de emergencias): en el portal de datos abiertos, hay que bajarlo a mano.
- **SENAMHI:** avisos en HTML/PDF, sin API.
- **Sentinel-2:** pendiente de confirmar escenas sin nubes de Huancavelica en octubre.

---

## 5. División del trabajo

| Ricardo | Freddy |
|---|---|
| Ingesta de SERFOR + FIRMS | Capa de Claude: explicar el riesgo, quechua/castellano, entender notas de voz, armar el reporte |
| Cruce espacial foco ↔ comunidad | Agente de WhatsApp (número de prueba de Meta Cloud API) |
| **Modelo (núcleo 2)**, luego núcleo 1 si hay tiempo | Mapa / vista oficial (o lo hacemos juntos) |
| Métricas del modelo | Pitch, demo, Devpost |

**Punto de encuentro (sábado 9:00 AM):** un JSON por foco de calor
`{id, lat, lon, comunidad, riesgo, variables, timestamp}`. Desde ahí cada uno avanza por su lado.

---

## 6. Lo que necesitamos de Ricardo esta noche

1. **¿Los registros de SERFOR tienen cómo creció cada incendio?** (tamaño, duración o daño). Sin una etiqueta de resultado no hay con qué entrenar el núcleo 2.
2. **¿Tienes un modelo de detección de cambios ya entrenado que se pueda adaptar a cicatrices de quema?** Decide si el núcleo 1 entra.
3. **¿Te convence el núcleo 2 como lo técnico principal, o ves otro más viable en 36 horas?**

## 7. Lo que necesitamos de los dos

1. **¿Qué distrito nombramos?** Propuesta: Castrovirreyna (Chupamarca, incendio de hace 5 días).
2. **¿Conocemos a algún dirigente o comunero** al que podamos escribirle antes del domingo? Una nota de voz real en quechua sería el mejor momento de la demo.

---

## 8. Tracks

- **Principal:** Anthropic (Claude for Public Benefit).
- **Sumar:** Best Planet-First Hack (criterios generales, sin construir nada extra) y Microsoft «Built for the Real World» (una lámina de cómo llega a producción).
- **Tal vez:** Elastic, solo si el motor de evidencia (registros de incendios + leyes + protocolo) corre sobre él, como hizo Peel. Después de tener el núcleo funcionando.
- **No:** Bright Data, Apify, Fetch.ai, Meta y los de finanzas. Serían agregados a la fuerza y el jurado lo nota.

---

## 9. Ideas que evaluamos y descartamos (por qué)

| Idea | Por qué no |
|---|---|
| «¿En qué se gastó mi distrito?» (presupuesto del MEF explicado en quechua, preguntas para el alcalde) | Buenos datos (61% de proyectos en Huancavelica al 0%), pero técnicamente poco profunda. Queda como «siguiente paso» |
| Preparación para el examen de Beca 18 (2,065 inscritos de Huancavelica, examen el 22 de noviembre) | Muy personal, pero poco novedosa y es casi el ejemplo de Anthropic |
| Copiloto para docentes de aulas multigrado (53% de las primarias rurales de Huancavelica) | Problema real, pero sin un docente para probar este fin de semana y técnicamente simple |
| Información de candidatos | Las elecciones regionales y municipales ya fueron (4 de octubre) |
| Agua en Ica | Problema real y personal, pero sin datos en vivo para una demo |

Detalle completo: `ideas/brainstorm.md`, `ideas/brainstorm-2-educacion-politica.md`, `ideas/brainstorm-3-hard-tech.md`.
