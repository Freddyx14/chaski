"""Thin, framework-agnostic handlers for the service's routes. Each FastAPI route calls one of these in ~3 lines
(the ready-to-paste snippet is in PARA_RICARDO.md).

    turno(...)          /turno/enfermera, /turno/paciente  → Resultado.model_dump()
    turno_eventos(...)  /turno/enfermera/vivo (SSE)        → `decision` (~3 s) then `resultado` (or `error`)
    banco_por_tag(tag)  GET /banco                         → [{id, es, quy, audio, tags, revisado}]

The Anthropic client is built once per process, on first use, from ANTHROPIC_API_KEY. Models come from
CHASKI_MODELO_PRINCIPAL / CHASKI_MODELO_CRITICO (chaski.orquestador).
"""
from __future__ import annotations

import json
import os
import queue
import threading
from collections.abc import Iterator

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
          confianza=None, traduccion_sembrada: str | None = None, *, client=None, dependencias: dict | None = None) -> dict:
    """One turn. `idioma` is 'spa' | 'quy' and `rol` is who SPOKE: 'personal' | 'paciente'.

    `traduccion_sembrada` (rehearsal only) replaces the translation; guards and critic still run, and the result
    carries `sembrada: true`. `client` / `dependencias` are for tests; the service leaves them out.
    """
    deps = dependencias or orquestador.dependencias(client or cliente())
    sembrada = traduccion_sembrada if traduccion_sembrada and traduccion_sembrada.strip() else None
    entrada = {"texto": texto or "", "idioma": idioma, "rol": rol, "n_mejores": leer_n_mejores(n_mejores_json),
               "confianza": _confianza(confianza)}
    r = orquestador.interpretar(entrada, leer_contexto(contexto_json), traduccion_forzada=sembrada, **deps)
    return r.model_dump()


def _sse(evento: str, datos: dict) -> str:
    return f"event: {evento}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n"


def turno_eventos(texto: str, idioma: str, rol: str, contexto_json: str | None, n_mejores_json: str | None = None,
                  confianza=None, traduccion_sembrada: str | None = None, *, client=None,
                  dependencias: dict | None = None) -> Iterator[str]:
    """The same turn as `turno`, as Server-Sent Events: `decision` as soon as the interpreter decides (the polished
    Spanish, so the app can show it while translation and the critic run), then `resultado` with exactly what
    `turno` returns. A failure ends with `error`. The `decision` text is never spoken: only `resultado` is."""
    eventos: queue.Queue = queue.Queue()
    fin = object()

    def correr():
        try:
            deps = dependencias or orquestador.dependencias(client or cliente())
            sembrada = traduccion_sembrada if traduccion_sembrada and traduccion_sembrada.strip() else None
            entrada = {"texto": texto or "", "idioma": idioma, "rol": rol,
                       "n_mejores": leer_n_mejores(n_mejores_json), "confianza": _confianza(confianza)}
            r = orquestador.interpretar(entrada, leer_contexto(contexto_json), traduccion_forzada=sembrada,
                                        al_decidir=lambda d: eventos.put(("decision", d)), **deps)
            eventos.put(("resultado", r.model_dump(mode="json")))
        except Exception as e:  # noqa: BLE001  reported to the app as an event, never a hung stream
            eventos.put(("error", {"error": f"{type(e).__name__}: {e}"}))
        finally:
            eventos.put(fin)

    threading.Thread(target=correr, daemon=True).start()
    while (ev := eventos.get()) is not fin:
        yield _sse(*ev)


def banco_por_tag(tag: str | None = None) -> list[dict]:
    """Bank phrases with the tag (all of them when tag is empty), with `revisado` so the app never says an
    unreviewed one. No embedding model is loaded for this."""
    from chaski import banco

    b = banco.banco()
    items = b.por_tag(tag) if tag else b.items
    return [{**banco.para_app(it), "revisado": it.get("revisado") is True} for it in items]
