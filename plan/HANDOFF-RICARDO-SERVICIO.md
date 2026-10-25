# Ricardo: lo que falta en el servicio (sáb 24-oct, 23:45 PT) · prioridad ahora

> ✅ Pasos 1–6 hechos (cf9de8b). **Nuevo (dom 00:20): `git pull` y vuelve a desplegar** para que el servicio tome D41,
> las frases de la enfermera como ejemplos del traductor (`CHASKI_EJEMPLOS=1`, ya es el valor por defecto; no hay que
> tocar nada más). **Y renombra D40 → D43** en los comentarios de `servicio/app.py` (~l.178), `servicio/desplegar.sh`
> (~l.92) y el título de `servicio/PARA-FREDDY.md` (~l.416): el traductor es D43; D40 es «Chaski sin fondo» de ui-ux.
> **Memoria automática (D44, dom 01:45):** en `desplegar.sh` agrega `export CHASKI_MEMORIA_RUTA=$DESTINO/memoria/memoria_auto.jsonl`
> (y `mkdir -p $DESTINO/memoria`), fuera de la carpeta `chaski/` que se sincroniza con `--delete`; si no, cada
> despliegue borra lo aprendido. Para ver y aprobar: `uv run python -m chaski.memoria` y `… aprobar ID`.
> Y `/turno/paciente` solo acepta WAV (la app manda WAV, así que anda); con .webm y .m4a da 500.

> Decisión de Freddy (D43, 23:38; se citó como D40 por error, D40 es «Chaski sin fondo»): **traduce Claude Sonnet 5 con esfuerzo medio**, no NLLB. Medido en los mismos sets:
> 0/92 términos fijos dañados (NLLB 3), lo que dice el paciente se lee mejor (qu→es 50,1 vs NLLB 24,7) y el turno
> completo queda en **8,3 s** (`evals/traduccion/`, `evals/latencia/`). NLLB no se tira: queda como modo sin conexión
> y tu ajuste sigue.

## Pasos, en orden

| # | Qué | Cómo | Cómo verificas |
|---|---|---|---|
| 1 | `git pull` | trae `traducir.py` con `medium` por defecto y la traducción anticipada | `cd app && uv run pytest -q` → 350 verdes |
| 2 | **Traducir con Claude** | en `servicio/app.py`, `/turno/enfermera` y `/turno/paciente` tienen `motor: str = Form("nllb")` → cambiar a `Form("claude")`. Y dejar vacía `CHASKI_NLLB_URL` en el entorno de la instancia | `curl -F texto="Tome una pastilla de paracetamol cada ocho horas durante tres días" …/turno/enfermera` → `"motor":"claude"`, `"estado":"dicho"`, `ms.total` ~8 s |
| 3 | **Arreglar `/turno/paciente`** | hoy da 500 porque falla `/entender` en la GPU (`127.0.0.1:8000/entender`) | un audio de `data/formulario/p16/` devuelve 200 |
| 4 | **Ruta en vivo** `/turno/enfermera/vivo` | pegar el bloque de `app/chaski/PARA_RICARDO.md` | la app de ui-ux muestra «Chaski lo dirá así» a los ~3 s |
| 5 | **Voz durante el crítico** | pasar tu síntesis a `chaski_servicio.turno(..., voz_fn=lambda texto, idioma: wav_bytes)` | la respuesta trae `audio_wav_b64` y ~1 s menos |
| 6 | Reiniciar, probar 2 y 3, **push** y avisar por el grupo | | ui-ux y Freddy prueban desde el build 12 |

Variables que deben quedar: `CHASKI_MODELO_PRINCIPAL=claude-opus-5`, `CHASKI_MODELO_CRITICO=claude-sonnet-5`,
`CHASKI_PENSAR_TRADUCIR=medium` (o sin definir: ya es el valor por defecto), `CHASKI_TRADUCIR_ANTICIPADO=1` (ídem),
`CHASKI_NLLB_URL` vacía.
