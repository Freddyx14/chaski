"""Token and cost accounting for the eval runners, without touching product code.

`ClienteConUso(client)` wraps an `anthropic.Anthropic` (or a fake) and adds up `response.usage` per model from
every `messages.parse` / `messages.create` call that goes through it. Product code (chaski.critico, chaski.interprete,
chaski.traducir, ...) only ever calls `client.messages.parse`, so passing the wrapper in is enough to count
every call. Thread-safe: `evals/ataques/correr.py` evaluates cases in a thread pool.

A response with no `usage` (the simulated clients) counts the call and adds zero tokens.
"""
from __future__ import annotations

import threading

# VERIFY against anthropic.com/pricing
# USD per million tokens. Source: the bundled `claude-api` skill of Claude Code 2.1.280, model table «cached:
# 2026-06-24» (input / output), and its prompt-caching notes: cache read ≈ 0.1 × input, cache write 1.25 × input
# (5-minute TTL). Not checked against the live pricing page, so treat every cost printed from this as an estimate.
# A model missing here gets tokens counted and cost reported as unknown (None), never a guessed price.
PRECIOS_USD_POR_MILLON: dict[str, dict[str, float]] = {
    "claude-sonnet-5": {"entrada": 2.00, "salida": 10.00, "cache_lectura": 0.20, "cache_escritura": 2.50},
    "claude-haiku-4-5": {"entrada": 1.00, "salida": 5.00, "cache_lectura": 0.10, "cache_escritura": 1.25},
    "claude-opus-5": {"entrada": 5.00, "salida": 25.00, "cache_lectura": 0.50, "cache_escritura": 6.25},
}
FUENTE_PRECIOS = ("bundled claude-api skill (Claude Code 2.1.280, cached 2026-06-24); "
                  "cache = 0.1x read / 1.25x write; VERIFY against anthropic.com/pricing")

_CAMPOS = {  # our name → field of anthropic.types.Usage
    "entrada": "input_tokens",
    "salida": "output_tokens",
    "cache_lectura": "cache_read_input_tokens",
    "cache_escritura": "cache_creation_input_tokens",
}


def precio_de(modelo: str) -> dict[str, float] | None:
    """Exact id first, then a dated id of a known model (claude-haiku-4-5-20251001 → claude-haiku-4-5)."""
    if modelo in PRECIOS_USD_POR_MILLON:
        return PRECIOS_USD_POR_MILLON[modelo]
    for base in sorted(PRECIOS_USD_POR_MILLON, key=len, reverse=True):
        resto = modelo[len(base):]
        if modelo.startswith(base) and resto.startswith("-") and resto[1:].isdigit():
            return PRECIOS_USD_POR_MILLON[base]
    return None


def costo_usd(modelo: str, tokens: dict[str, int]) -> float | None:
    precio = precio_de(modelo)
    if precio is None:
        return None
    return round(sum(tokens.get(k, 0) * precio[k] for k in _CAMPOS) / 1_000_000, 6)


class _Mensajes:
    def __init__(self, dueño: ClienteConUso, mensajes):
        self._dueño, self._mensajes = dueño, mensajes

    def parse(self, **kw):
        respuesta = self._mensajes.parse(**kw)
        self._dueño.registrar(kw.get("model", "?"), respuesta)
        return respuesta

    def create(self, **kw):
        respuesta = self._mensajes.create(**kw)
        self._dueño.registrar(kw.get("model", "?"), respuesta)
        return respuesta

    def __getattr__(self, nombre):  # stream, count_tokens, ... pass through uncounted
        return getattr(self._mensajes, nombre)


class ClienteConUso:
    """A thin counting wrapper around the client passed to product code."""

    def __init__(self, client):
        self._client = client
        self._lock = threading.Lock()
        self.por_modelo: dict[str, dict[str, int]] = {}
        self.messages = _Mensajes(self, getattr(client, "messages", None))  # client None: counts nothing

    def __getattr__(self, nombre):
        return getattr(self._client, nombre)

    def registrar(self, modelo: str, respuesta) -> None:
        uso = getattr(respuesta, "usage", None)
        with self._lock:
            t = self.por_modelo.setdefault(modelo, {"llamadas": 0, **{k: 0 for k in _CAMPOS}})
            t["llamadas"] += 1
            for nuestro, campo in _CAMPOS.items():
                valor = getattr(uso, campo, None) if uso is not None else None
                t[nuestro] += int(valor or 0)

    def resumen(self) -> dict:
        """{por_modelo: {modelo: tokens + costo_usd}, costo_usd_total, precios_verificados, fuente_precios}."""
        with self._lock:
            por_modelo = {m: {**t, "costo_usd": costo_usd(m, t)} for m, t in sorted(self.por_modelo.items())}
        costos = [t["costo_usd"] for t in por_modelo.values()]
        return {
            "por_modelo": por_modelo,
            "costo_usd_total": None if any(c is None for c in costos) else round(sum(costos), 6),
            "precios_verificados": False,
            "fuente_precios": FUENTE_PRECIOS,
        }


def imprimir_uso(uso: dict, turnos: int | None = None) -> None:
    print("\n  Tokens y costo (precios SIN VERIFICAR, ver evals/costo.py):")
    if not uso["por_modelo"]:
        print("    sin llamadas a la API")
        return
    for modelo, t in uso["por_modelo"].items():
        costo = "precio desconocido" if t["costo_usd"] is None else f"${t['costo_usd']:.4f}"
        print(f"    {modelo:28s} {t['llamadas']:5d} llamadas · entrada {t['entrada']:,} · salida {t['salida']:,} · "
              f"caché leída {t['cache_lectura']:,} · caché escrita {t['cache_escritura']:,} · {costo}")
    total = uso["costo_usd_total"]
    if total is not None:
        por_turno = f" · ${total / turnos:.4f} por turno" if turnos else ""
        print(f"    total ${total:.4f}{por_turno}")
