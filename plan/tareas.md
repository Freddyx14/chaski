# Chaski — tareas por persona

> Checklist vivo. Cada tarea apunta a su función (F) o decisión (D) del [`SOT.md`](../SOT.md).
> Marca `[x]` al terminar y haz commit. Si una tarea cambia el producto, el cambio va primero al SOT.
> Estado al sábado 24 de octubre, 00:45 PT.

## Freddy

### Ya hecho
- [x] Consentimiento de la familia para grabar (D5)
- [x] Audio a su mamá con la muestra de voz y la consulta por las videollamadas (D18)
- [x] Créditos de Claude reclamados

### Sábado
- [ ] 07:30 · App iOS con Expo: micrófono, parlante, pantalla de conversación (D14)
- [ ] 07:30 · Primer build a TestFlight; plan B Expo en su iPhone (D14)
- [ ] 08:30 · La app manda un audio a la VM y recibe texto (con Ricardo)
- [ ] 09:00 · Cartesia: voz en castellano en la app (D16)
- [~] 10:00 · **Claude visión** (banco de Ricardo listo, Haiku 4.5 en 2.3 s; falta en la app): foto de la receta y de la caja → medicamento, dosis, frecuencia; cruce con lo que dijo la enfermera (F9, D19)
- [ ] 10:30 · Medir Opus 5, Sonnet 5 y Haiku 4.5: segundos por turno y errores atrapados (D15)
- [ ] 12:30 · Workshop de Anthropic (agentes)
- [ ] 13:30 · Entender a la enfermera, estilo Wispr Flow (F3)
- [ ] 13:30 · Turno enfermera → paciente completo en la app (F3 + F4 + F5)
- [ ] 15:00 · **Claude corrige la transcripción en quechua** con el contexto de la consulta (F10, D19), con Ricardo
- [ ] 16:00 · «¿Me lo repite?» (F6) y resumen de la consulta (F11)
- [ ] 17:00 · Videollamada con su mamá: prueba real (D18)
- [ ] 17:00 · Evaluación chanka-salud: 30–50 indicaciones, Claude vs Google, a su mamá para calificar (F8)
- [x] Elegir el avatar: Chaski, vicuña 3D con audífonos (D22)
- [x] Especificación JSON de Chaski (`avatar/chaski.json`) y sus 5 estados generados (`avatar/estados/`)
- [ ] 18:00 · Avatar en la app con sus 5 estados (D17, D20, D22), solo si lo anterior está
- [ ] 21:00 · Borrador en Devpost · repo público sin `context/photos/` · README con Cartesia y Claude
- [ ] 22:00 · Ensayo del pitch

### Domingo
- [ ] 05:00 · Grabar el video de la demo
- [ ] 08:00 · Devpost final
- [ ] 10:30 · Jurado (con su mamá por videollamada si puede)

## Ricardo

### Esta noche
- [x] La VM corre Omnilingual `quy` y `mms-lid-512` (medido: 49 ms detección, 1.7 s por 16 s de audio; GPU A10G 23 GB, no 40)
- [x] **Preguntas y frases que graban las familias** (`ricardo-artifacts/datos/frases/*.pdf`, con 35 préstamos del castellano): lista final en castellano por tema, bloque A (frases de posta) y bloque B (respuestas libres), sobre `plan/recoleccion-de-voz.md`, y mandarla a Freddy para la familia

### 🔴 CRÍTICO · Línea base ANTES de cualquier ajuste fino (pedido de Freddy, sáb 09:13)
Sin la línea base no hay «cuánto mejoramos», y ese número es el pitch. Ricardo diseña el sistema; lo mínimo que tiene que cumplir:
- **Un conjunto de prueba congelado**: el hablante que el modelo nunca escuchó, separado ANTES de entrenar nada, y no se toca más.
- **Medir cada modelo tal cual viene, sin ajuste**, y guardar sus fallas, no solo el promedio:
  - Reconocimiento (Omnilingual `quy`): CER y WER, con las peores frases y en qué fallan (préstamos del castellano, números, nombres de medicamentos).
  - Traducción (NLLB-200 y Claude): chrF o BLEU, más los **hechos críticos** que se pierden (dosis, frecuencia, medicamento) con la auditoría F4.
  - Voz (`mms-tts-quy`): ida y vuelta, el audio generado pasa por el reconocimiento y se mide su CER; más la nota de la mamá de Freddy.
  - Detección de idioma: acierto castellano/quechua.
- **Un solo script** que corre lo mismo antes y después y escribe un archivo fechado (p. ej. `reports/linea-base.json` con el commit), para que el «después» sea el mismo comando con otro modelo.
- Paso 0 y paso 1 de abajo SON esta línea base: que queden guardados así, con las fallas, antes de las 13:30.

### 🔴 URGENTE · Dos rutas que la app ya llama (pegar en `servicio/app.py`) — pedido de Freddy, sáb 09:31
La app iOS ya está en TestFlight y sin estas rutas el resumen y la detección de idioma no funcionan. **Cuando las pegues, haz push** (y avisa por el grupo).
- [ ] `/resumen`
- [ ] `/idioma`
- [ ] Levantar el túnel HTTPS donde corre el servicio: `cloudflared tunnel --url http://localhost:8000` y pasarle la dirección a Freddy

La lógica del resumen ya está en `app/chaski/resumen.py` con pruebas; solo falta exponerla. `/idioma` reenvía a la instancia, que ya lo tiene.

```python
@aplicacion.post("/idioma")
async def idioma(audio: UploadFile = File(...)):
    """Solo detección de idioma, sin Claude: la app decide de qué lado va el turno."""
    import httpx
    from servicio.flujo import INSTANCIA
    try:
        with httpx.Client(timeout=30) as cli:
            return cli.post(f"{INSTANCIA}/idioma",
                            files={"audio": (audio.filename or "turno.wav", await audio.read(), "audio/wav")}).json()
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/resumen")
def resumen(turnos: str = Form(...), rol: str = Form("personal")):
    import anthropic
    from chaski.resumen import Turno, resumir, texto_para_decir
    try:
        r = resumir(anthropic.Anthropic(), [Turno(**t) for t in json.loads(turnos)], rol)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return {**r.model_dump(), "texto_para_decir": texto_para_decir(r)}
```
- `/idioma` devuelve `{codigo, confianza}` (lo que dé la instancia).
- `turnos` de `/resumen` es JSON `[{lado: "castellano"|"quechua", castellano, quechua, estado}]`, estado ∈ dicho, dicho_con_aviso, bloqueado, entendido, con_dudas. `rol` ∈ personal, paciente (D27).

### Sábado
- [ ] 07:30 · Recibir audios, convertir a 16 kHz mono, nombrar, separar al hablante de prueba
- [ ] 08:30 · VM con HTTPS público; endpoint de voz → texto para la app
- [ ] 09:00 · Paso 0 (Meta tal cual) y paso 1 (+ vocabulario KenLM) → primeros números (F1)
- [ ] 13:30 · Paso 2: ajuste fino con las voces de las familias (F1)
- [ ] 13:30 · Detección de idioma medida con las grabaciones (F2)
- [ ] 15:00 · Darle a Claude las N mejores transcripciones para que corrija (F10), con Freddy
- [ ] 16:00 · Voz de Chaski ajustada con la voz de la mamá de Freddy (F5)
- [ ] 19:00 · Gráficos de la página de resultados con los números reales
- [ ] 22:00 · Ensayo del pitch: la lámina técnica

### Domingo
- [ ] 07:00 · Congelar los números
- [ ] 10:30 · Jurado: respuestas técnicas

## Familias

- [ ] **Sábado 7–10 AM (Perú):** grabar el bloque A (frases de posta) y el bloque B (respuestas libres)
- [ ] La mamá de Freddy: transcribir sus audios, revisar el glosario, elegir el nombre (P4) y el avatar (P5)
- [ ] La mamá de Freddy: calificar las traducciones y la voz a ciegas (F8)
- [ ] La mamá de Freddy: videollamada de prueba el sábado ~19:00 Lima y, si puede, pitch el domingo 12:30–14:30 Lima
