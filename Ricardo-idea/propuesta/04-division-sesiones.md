# División del trabajo entre dos sesiones de Claude

> Ricardo y Freddy trabajan cada uno con su propia cuenta de Claude. Este archivo define quién toca qué,
> para que las dos sesiones no se pisen. **Léelo antes de escribir la primera línea de código.**

## Regla única

**El reparto es por carpeta, no por tema.** Dos sesiones editando el mismo archivo producen conflictos de
merge a las tres de la mañana, que es exactamente cuando nadie los sabe resolver. Cada sesión es dueña de
su carpeta y nunca edita la del otro. Si necesitas algo de la otra carpeta, se pide por el contrato.

```
cal-hacks-extorsion/
├── contrato/            # Propiedad COMPARTIDA. Se escribe una vez, a las 8:00 del sábado, entre los dos.
│   ├── schema.json      # El contrato de la API
│   └── fixtures/        # Datos de ejemplo que cumplen el contrato
├── pipeline/            # Sesión A — Ricardo
└── web/                 # Sesión B — Freddy
    └── bot/
```

## Sesión A — Ricardo (datos, modelos, benchmarks)

Dueña de `pipeline/`.

1. Ingesta con DuckDB y filtro a SJL, Comas y SMP.
2. Grafo vial con `osmnx`, construcción de corredores, snap de incidentes.
3. Tabla corredor × semana con los bloques de features.
4. **Ablation study**: bloques de features × familias de modelos, con partición temporal. Ver
   `06-ablation.md`.
5. SHAP y la explicación por corredor.
6. API FastAPI que sirve exactamente el contrato.
7. **Entregable intermedio obligatorio, 10:00 del sábado:** `contrato/fixtures/` con 20 corredores reales
   ya serializados. A partir de ahí la sesión B trabaja sin esperar al modelo.

## Sesión B — Freddy (producto, visualización, Claude)

Dueña de `web/` y `web/bot/`.

1. Visual analytics en D3 v7 sobre el contrato: mapa, serie temporal, vista de desplazamiento. Ver
   `07-frontend-d3.md`.
2. Ruta `/ciudadano`: una pregunta, una respuesta, pensada para un teléfono.
3. Ruta `/analista`: el mapa completo, para municipalidad y Mininter.
4. Bot de WhatsApp y la capa de Claude: las cuatro tareas de `01-propuesta.md` §"Qué hace Claude", con las
   reglas de qué no decir en el prompt de sistema.
5. Devpost, video, láminas.

**Trabaja contra `contrato/fixtures/` desde el minuto cero.** Nunca espera a que el modelo esté listo.

## El contrato, que se escribe primero

`contrato/schema.json` es la versión formal del JSON de `02-diseno-tecnico.md` §6. Reglas:

- Ninguna de las dos sesiones cambia el contrato por su cuenta. Si hace falta un campo, se habla, se cambia
  en los dos lados y se regeneran los fixtures.
- Los fixtures se versionan en git. Son la única fuente de verdad mientras el modelo no esté.
- Nombres de campo en snake_case, sin tildes, en español.

## Ramas y merges

- `main` queda protegida de facto: nadie empuja directo.
- `pipeline/ricardo` y `web/freddy`.
- Merge a `main` solo en las dos integraciones acordadas: **15:00 y 21:00 del sábado**. Fuera de esas dos
  ventanas, cada quien en su rama.
- Mensajes de commit en inglés, formato Conventional Commits.

## Qué le dices a la otra sesión de Claude

El Claude de Freddy no tiene este contexto. Al abrirlo, pásale:

1. `propuesta/README.md`, `01-propuesta.md` y `02-diseno-tecnico.md` §6 (el contrato).
2. `propuesta/07-frontend-d3.md`.
3. La frase: *"Eres dueño de `web/`. No edites `pipeline/` ni `contrato/schema.json`. Trabaja contra
   `contrato/fixtures/`."*

## Los dos usuarios, y por qué no son el mismo producto

| | Ciudadano afectado | Funcionario (Mininter, municipalidad, gobierno regional) |
|---|---|---|
| Canal | WhatsApp, y web responsive como respaldo | Web de escritorio |
| Pregunta | "¿mi cuadra está en esto y qué hago?" | "¿dónde pongo el serenazgo esta semana y sirvió lo que hice el mes pasado?" |
| Unidad | Un corredor, el suyo | Todos los corredores del distrito |
| Detalle permitido | Mínimo. Lo que no le sirve para decidir, no se le dice | Mayor, pero con registro de acceso |
| Métrica que le importa | ¿Me va a pasar algo? | ¿Bajó, o solo se movió a la cuadra de al lado? |
| Riesgo propio | Que la respuesta lo exponga o lo paralice | Que use el mapa para justificar operativos de fachada, o que estigmatice un distrito entero |

**Lo que no se construye:** app nativa iOS o Android. Un bodeguero extorsionado no instala una app de
extorsión en su teléfono, porque el teléfono se lo pueden revisar. WhatsApp no deja rastro distinto del
que ya tiene, y es donde esa persona ya vive. Si hace falta algo instalable, es una PWA.

## Qué NO se delega

Las dos sesiones comparten las mismas reglas de lenguaje y de seguridad, y ninguna las relaja por su
cuenta:

- Nunca "aquí cobran cupo". Siempre "denuncias registradas".
- Siempre el aviso de subregistro.
- Nada a nivel de negocio o persona.
- Sin mapa público de territorios para el ciudadano.
- Cero atribución a bandas con nombre.
