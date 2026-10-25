"""Thin, framework-agnostic handlers for the service's routes. Each FastAPI route calls one of these in ~3 lines
(the ready-to-paste snippet is in PARA_RICARDO.md).

    turno(...)          /turno/enfermera, /turno/paciente  → Resultado.model_dump()
    turno_eventos(...)  /turno/enfermera/vivo (SSE)        → `decision` (~3 s) then `resultado` (or `error`)
    turno_auto(...)     /turno (audio, hands-free loop)    → who spoke + Resultado.model_dump()
    turno_auto_eventos  /turno/vivo (SSE)                  → `oido`, `decision`, `resultado` (or `error`)
    receta(...)         /receta (photo of a box/prescription) → Resultado-shaped dict: the question to the staff
    banco_por_tag(tag)  GET /banco                         → [{id, es, quy, audio, tags, revisado}]

The Anthropic client is built once per process, on first use, from ANTHROPIC_API_KEY. Models come from
CHASKI_MODELO_PRINCIPAL / CHASKI_MODELO_CRITICO (chaski.orquestador).
"""
from __future__ import annotations

import base64
import json
import os
import queue
import threading
import time
from collections.abc import Callable, Iterator

from chaski import orquestador
from chaski.interprete import Contexto

_cliente = None
_cliente_lock = threading.Lock()


def cliente():
    """The shared Anthropic client. Raises if ANTHROPIC_API_KEY is missing (the route should report it)."""
    global _cliente
    with _cliente_lock:
        if _cliente is None:
            import anthropic

            clave = os.environ.get("ANTHROPIC_API_KEY", "").strip()
            if not clave:
                raise RuntimeError("falta la variable ANTHROPIC_API_KEY")
            _cliente = anthropic.Anthropic(api_key=clave)
        return _cliente


def leer_contexto(contexto_json: str | None) -> Contexto | None:
    """The `contexto` form field as the app sends it (JSON of the previous turn's `contexto`). Empty → new consult.
    Malformed JSON raises ValueError: that is an app bug, not a condition to paper over."""
    if contexto_json is None or not contexto_json.strip():
        return None
    try:
        return Contexto.model_validate(json.loads(contexto_json))
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"contexto mal formado: {type(e).__name__}: {e}") from e


def leer_n_mejores(n_mejores_json: str | None) -> list[str]:
    """ASR alternatives, as a JSON list of strings or of [texto, puntaje] pairs (what /entender returns)."""
    if n_mejores_json is None or not n_mejores_json.strip():
        return []
    datos = json.loads(n_mejores_json)
    if not isinstance(datos, list):
        raise ValueError("n_mejores tiene que ser una lista")
    salida = []
    for x in datos:
        texto = x[0] if isinstance(x, (list, tuple)) and x else x
        if isinstance(texto, str) and texto.strip():
            salida.append(texto.strip())
    return salida


def _confianza(confianza) -> float | None:
    if confianza is None or (isinstance(confianza, str) and not confianza.strip()):
        return None
    return float(confianza)


def turno(texto: str, idioma: str, rol: str, contexto_json: str | None, n_mejores_json: str | None = None,
          confianza=None, traduccion_sembrada: str | None = None, *, client=None, dependencias: dict | None = None,
          voz_fn=None) -> dict:
    """One turn. `idioma` is 'spa' | 'quy' and `rol` is who SPOKE: 'personal' | 'paciente'.

    `traduccion_sembrada` (rehearsal only) replaces the translation; guards and critic still run, and the result
    carries `sembrada: true`. `client` / `dependencias` are for tests; the service leaves them out.
    `voz_fn(texto, idioma) -> wav bytes` (optional): the voice is made while the critic runs and comes back as
    `audio_wav_b64` only when every check passed.
    """
    deps = dependencias or orquestador.dependencias(client or cliente())
    sembrada = traduccion_sembrada if traduccion_sembrada and traduccion_sembrada.strip() else None
    entrada = {"texto": texto or "", "idioma": idioma, "rol": rol, "n_mejores": leer_n_mejores(n_mejores_json),
               "confianza": _confianza(confianza)}
    r = orquestador.interpretar(entrada, leer_contexto(contexto_json), traduccion_forzada=sembrada, voz_fn=voz_fn,
                                **deps)
    return r.model_dump()


def _sse(evento: str, datos: dict) -> str:
    return f"event: {evento}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n"


def turno_eventos(texto: str, idioma: str, rol: str, contexto_json: str | None, n_mejores_json: str | None = None,
                  confianza=None, traduccion_sembrada: str | None = None, *, client=None,
                  dependencias: dict | None = None, voz_fn=None) -> Iterator[str]:
    """The same turn as `turno`, as Server-Sent Events: `decision` as soon as the interpreter decides (the polished
    Spanish, so the app can show it while translation and the critic run), then `resultado` with exactly what
    `turno` returns. A failure ends with `error`. The `decision` text is never spoken: only `resultado` is."""
    for ev in _eventos_turno(texto, idioma, rol, contexto_json, n_mejores_json, confianza, traduccion_sembrada,
                             client=client, dependencias=dependencias, voz_fn=voz_fn):
        yield _sse(*ev)


def _eventos_turno(texto, idioma, rol, contexto_json, n_mejores_json=None, confianza=None, traduccion_sembrada=None,
                   *, client=None, dependencias=None, voz_fn=None) -> Iterator[tuple[str, dict]]:
    """(event, data) pairs behind `turno_eventos`: interpret in a thread, hand back events as they happen."""
    eventos: queue.Queue = queue.Queue()
    fin = object()

    def correr():
        try:
            deps = dependencias or orquestador.dependencias(client or cliente())
            sembrada = traduccion_sembrada if traduccion_sembrada and traduccion_sembrada.strip() else None
            entrada = {"texto": texto or "", "idioma": idioma, "rol": rol,
                       "n_mejores": leer_n_mejores(n_mejores_json), "confianza": _confianza(confianza)}
            r = orquestador.interpretar(entrada, leer_contexto(contexto_json), traduccion_forzada=sembrada,
                                        al_decidir=lambda d: eventos.put(("decision", d)), voz_fn=voz_fn,
                                        **deps)
            eventos.put(("resultado", r.model_dump(mode="json")))
        except Exception as e:  # noqa: BLE001  reported to the app as an event, never a hung stream
            eventos.put(("error", {"error": f"{type(e).__name__}: {e}"}))
        finally:
            eventos.put(fin)

    threading.Thread(target=correr, daemon=True).start()
    while (ev := eventos.get()) is not fin:
        yield ev


# ── Hands-free turn: audio in, Chaski works out who spoke ───────────────────────────────────────────────────

UMBRAL_IDIOMA = 0.6
ROL_POR_IDIOMA = {"spa": "personal", "quy": "paciente"}
IDIOMA_POR_ROL = {"personal": "spa", "paciente": "quy"}


def decidir_lado(deteccion: dict | None, contexto: Contexto | None) -> tuple[str, str]:
    """Who spoke: (rol, lado_por). The detector decides when it names spa/quy with confidence >= UMBRAL_IDIOMA
    (a missing confidence counts as sure). Otherwise ALTERNATION: the other side of the last person who spoke
    (Chaski's own lines don't count); with no history, the staff opens the consult."""
    codigo = str((deteccion or {}).get("codigo") or "").split("_")[0].lower()
    conf = (deteccion or {}).get("confianza")
    if codigo in ROL_POR_IDIOMA and (conf is None or float(conf) >= UMBRAL_IDIOMA):
        return ROL_POR_IDIOMA[codigo], "detector"
    if contexto is not None and contexto.receta_pendiente:  # Chaski just asked the staff to confirm a prescription
        return "personal", "alternancia"
    for linea in reversed(contexto.historial if contexto else []):
        if linea.rol in ("personal", "paciente"):
            return ("paciente" if linea.rol == "personal" else "personal"), "alternancia"
    return "personal", "alternancia"


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)


def _oir(audio: bytes, nombre: str, contexto_json: str | None, detectar_idioma: Callable, oir_castellano: Callable,
         oir_quechua: Callable) -> dict:
    """Detect the language, pick the side, run that side's recognizer. Recognizer failures propagate."""
    contexto = leer_contexto(contexto_json)  # malformed → ValueError before any network call
    t0 = time.perf_counter()
    try:
        deteccion = detectar_idioma(audio, nombre) or {}
    except Exception:  # noqa: BLE001  a dead detector means alternation, not a lost turn
        deteccion = {}
    ms = {"idioma": _ms(t0)}
    rol, lado_por = decidir_lado(deteccion, contexto)
    idioma = IDIOMA_POR_ROL[rol]
    t0 = time.perf_counter()
    oido = (oir_quechua if idioma == "quy" else oir_castellano)(audio, nombre) or {}
    ms["oir"] = _ms(t0)
    return {"quien_hablo": rol, "idioma": idioma, "texto": oido.get("texto") or "", "lado_por": lado_por,
            "idioma_detectado": deteccion.get("codigo"), "confianza_idioma": deteccion.get("confianza"),
            "n_mejores": json.dumps(oido.get("alternativas") or [], ensure_ascii=False) if idioma == "quy" else None,
            "confianza": oido.get("confianza") if idioma == "quy" else None, "ms": ms}


def _con_oido(r: dict, oido: dict) -> dict:
    """The Resultado plus who spoke and how that was decided; `ms` gains `idioma` and `oir`."""
    return {**r, "quien_hablo": oido["quien_hablo"], "idioma_detectado": oido["idioma_detectado"],
            "confianza_idioma": oido["confianza_idioma"], "lado_por": oido["lado_por"],
            "ms": {**(r.get("ms") or {}), **oido["ms"]}}


def turno_auto(audio: bytes, nombre: str, contexto_json: str | None, *, detectar_idioma: Callable,
               oir_castellano: Callable, oir_quechua: Callable, client=None, dependencias: dict | None = None,
               voz_fn=None) -> dict:
    """One hands-free turn: audio in, Chaski decides who spoke, hears it and interprets it (same path as `turno`).

    `detectar_idioma(audio, nombre) -> {codigo, confianza}`, `oir_castellano(audio, nombre) -> {texto}`,
    `oir_quechua(audio, nombre) -> {texto, alternativas, confianza}` are injected by the service.
    An empty transcript is not an error: the interpreter answers `no_entendi`."""
    oido = _oir(audio, nombre, contexto_json, detectar_idioma, oir_castellano, oir_quechua)
    r = turno(oido["texto"], oido["idioma"], oido["quien_hablo"], contexto_json, oido["n_mejores"], oido["confianza"],
              client=client, dependencias=dependencias, voz_fn=voz_fn)
    return _con_oido(r, oido)


def turno_auto_eventos(audio: bytes, nombre: str, contexto_json: str | None, *, detectar_idioma: Callable,
                       oir_castellano: Callable, oir_quechua: Callable, client=None,
                       dependencias: dict | None = None, voz_fn=None) -> Iterator[str]:
    """`turno_auto` as Server-Sent Events: `oido` (who spoke, language, what was heard; ~1-2 s), then `decision`,
    then `resultado` with what `turno_auto` returns. A failure ends with `error`."""
    try:
        oido = _oir(audio, nombre, contexto_json, detectar_idioma, oir_castellano, oir_quechua)
    except Exception as e:  # noqa: BLE001
        yield _sse("error", {"error": f"{type(e).__name__}: {e}"})
        return
    yield _sse("oido", {k: oido[k] for k in ("quien_hablo", "idioma", "texto", "lado_por", "idioma_detectado",
                                             "confianza_idioma", "ms")})
    for evento, datos in _eventos_turno(oido["texto"], oido["idioma"], oido["quien_hablo"], contexto_json,
                                        oido["n_mejores"], oido["confianza"], client=client,
                                        dependencias=dependencias, voz_fn=voz_fn):
        yield _sse(evento, _con_oido(datos, oido) if evento == "resultado" else datos)


def banco_por_tag(tag: str | None = None) -> list[dict]:
    """Bank phrases with the tag (all of them when tag is empty), with `revisado` so the app never says an
    unreviewed one. No embedding model is loaded for this."""
    from chaski import banco

    b = banco.banco()
    items = b.por_tag(tag) if tag else b.items
    return [{**banco.para_app(it), "revisado": it.get("revisado") is True} for it in items]


# ── Prescription by voice: read from a photo, confirmed aloud by the staff, then said to the patient ───────────

def _num(valor) -> float | None:
    if valor is None or isinstance(valor, bool):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _cifra(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def _texto(valor) -> str | None:
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def _dosis(cantidad: float, unidad: str) -> str:
    """«una tableta», «media cucharada», «2 tabletas». Only the unit that was read; never a default one."""
    if cantidad == 0.5:
        return f"media {unidad}"
    if cantidad == 1:
        return f"{'una' if unidad.endswith('a') else 'un'} {unidad}"
    return f"{_cifra(cantidad)} {unidad if unidad.endswith('s') else unidad + 's'}"


def instruccion_de_receta(lectura: dict) -> tuple[str | None, str, list[str]]:
    """(instruction to say to the patient or None, what was read in short, missing fields).

    Built in code ONLY from the fields vision actually read. The instruction exists only when the medicine, the dose
    (amount AND unit) and how often are all there; otherwise it is None and `faltan` says what to ask for."""
    medicamento = _texto(lectura.get("medicamento"))
    concentracion = _texto(lectura.get("concentracion"))
    unidad = _texto(lectura.get("unidad"))
    cantidad, cada, dias = _num(lectura.get("cantidad")), _num(lectura.get("cada_horas")), _num(lectura.get("dias"))

    faltan = [c for c, falta in (("medicamento", medicamento is None), ("dosis", cantidad is None or unidad is None),
                                 ("frecuencia", cada is None)) if falta]
    nombre = " ".join(x for x in (medicamento, concentracion) if x)
    leido = [nombre] if nombre else []
    if cantidad is not None and unidad:
        leido.append(_dosis(cantidad, unidad) + (f" cada {_cifra(cada)} horas" if cada is not None else ""))
    elif cada is not None:
        leido.append(f"cada {_cifra(cada)} horas")
    if dias:
        leido.append(f"por {_cifra(dias)} días")
    resumen = ", ".join(leido)

    if faltan:
        return None, resumen, faltan
    frase = f"Tome {_dosis(cantidad, unidad)} de {nombre} cada {_cifra(cada)} horas"
    if dias:
        frase += f", por {_cifra(dias)} días"
    return frase + ".", resumen, faltan


def advertencias_de(lectura: dict) -> list[str]:
    """Vision's `advertencias` are WRITTEN by the vision model («lo que una persona debe saber»), not copied from the
    box, so they never go into what the patient hears (rule: no clinical datum nobody said). They go to the staff
    screen as `aviso`; if the nurse wants one said, she says it, and it is a normal turn."""
    return [a.strip().rstrip(".") for a in (lectura.get("advertencias") or []) if isinstance(a, str) and a.strip()][:2]


_PEDIR = {"medicamento": "el nombre del medicamento", "dosis": "la dosis",
          "frecuencia": "cada cuántas horas se toma"}


def receta(lectura, contexto_json: str | None, *, voz_fn=None) -> dict:
    """POST /receta: what vision read (`vision.como_json(leer(...))`) becomes a question to the STAFF, never words to
    the patient. With a complete instruction it is kept in `contexto.receta_pendiente`; the staff's spoken «sí» on the
    next turn says it to the patient through the guards and the critic (orquestador.interpretar). With the dose or the
    frequency missing nothing is kept, and the question asks for what is missing."""
    from dataclasses import asdict, is_dataclass

    from chaski.orquestador import Resultado

    lectura = asdict(lectura) if is_dataclass(lectura) else dict(lectura or {})
    t0 = time.perf_counter()
    contexto = leer_contexto(contexto_json) or Contexto()
    contexto.modo = "receta"
    frase, resumen, faltan = instruccion_de_receta(lectura)
    contexto.receta_pendiente = frase
    contexto.repreguntas_seguidas.clear()

    leido = f"Leí: {resumen}." if resumen else "No pude leer la receta."
    if frase:
        caja = lectura.get("posologia_de") == "caja"
        pregunta = f"{leido} {'Es la pauta de la caja. ' if caja else ''}¿Se lo digo?"
        motivo = "receta leída de la foto; espera el «sí» del personal"
        aviso = lectura.get("porque_confirmar") if caja else None
    else:
        pedir = [_PEDIR[c] for c in faltan]
        pedir_txt = pedir[0] if len(pedir) == 1 else ", ".join(pedir[:-1]) + " y " + pedir[-1]
        pregunta = f"{leido} Me falta {pedir_txt}. ¿Me lo dice, por favor?"
        motivo = "receta incompleta en la foto: falta " + ", ".join(faltan)
        aviso = None
    avisos = [a for a in (aviso, *(f"Advertencia leída (no se le dice): {x}" for x in advertencias_de(lectura))) if a]
    aviso = " · ".join(avisos) or None
    contexto.agregar("chaski", pregunta)

    audio_b64 = None
    ms: dict[str, float] = {}
    if voz_fn:
        try:
            t_voz = time.perf_counter()
            wav = voz_fn(pregunta, "spa")
            ms["voz"] = _ms(t_voz)
            audio_b64 = base64.b64encode(wav).decode() if wav else None
        except Exception:  # noqa: BLE001  no voice is not a failure: the question is still shown
            audio_b64 = None
    ms["total"] = _ms(t0)
    dato = "dosis" if "dosis" in faltan else "frecuencia" if "frecuencia" in faltan else (
        "medicamento" if faltan else None)
    return Resultado(estado="dicho", accion="repreguntar", motivo=motivo, dato_faltante=dato, para="personal",
                     idioma_salida="spa", texto_pulido=frase or "", texto_salida=pregunta, audio_wav_b64=audio_b64,
                     aviso=aviso, ms=ms, contexto=contexto).model_dump(mode="json")
