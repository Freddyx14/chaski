"""Thin, framework-agnostic handlers for the service's routes. Each FastAPI route calls one of these in ~3 lines
(the ready-to-paste snippet is in PARA_RICARDO.md).

    turno(...)          /turno/enfermera, /turno/paciente  → Resultado.model_dump()
    turno_eventos(...)  /turno/enfermera/vivo (SSE)        → `decision` (~3 s) then `resultado` (or `error`)
    turno_auto(...)     /turno (audio, hands-free loop)    → who spoke + Resultado.model_dump()
    turno_auto_eventos  /turno/vivo (SSE)                  → `oido`, `decision`, `resultado` (or `error`)
    banco_por_tag(tag)  GET /banco                         → [{id, es, quy, audio, tags, revisado}]

The Anthropic client is built once per process, on first use, from ANTHROPIC_API_KEY. Models come from
CHASKI_MODELO_PRINCIPAL / CHASKI_MODELO_CRITICO (chaski.orquestador).
"""
from __future__ import annotations

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
