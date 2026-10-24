"""El corrector: convierte audios crudos en verdad de referencia.

El flujo que pidió Ricardo, y por qué sirve para los tres ajustes a la vez:

  audio -> omniASR transcribe -> NOSOTROS corregimos la escritura -> queda un par
  (audio, texto correcto) + el castellano del cuadernillo.

De ahí salen tres conjuntos con los MISMOS datos:
  1. Reconocimiento (todas las voces):   audio -> texto chanka
  2. Voz de Chaski (solo una persona):   texto chanka -> audio
  3. Traducción (los pares del cuadernillo): castellano <-> chanka

Por eso corregir una vez vale por tres.
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx

from voz.contrato import Grabacion, escribir_manifiesto, leer_manifiesto

RAIZ = Path("datos/crudo")
INSTANCIA = "http://127.0.0.1:8010"


def personas() -> list[str]:
    if not RAIZ.exists():
        return []
    return sorted(p.name for p in RAIZ.iterdir() if (p / "manifiesto.jsonl").exists())


def clips(persona: str) -> list[dict]:
    manifiesto = RAIZ / persona / "manifiesto.jsonl"
    if not manifiesto.exists():
        return []
    salida = []
    for g in leer_manifiesto(manifiesto):
        salida.append({"nombre": g.nombre, "audio": g.audio, "numero": g.numero,
                       "bloque": g.bloque, "castellano": g.castellano,
                       "transcripcion": g.transcripcion, "segundos": g.segundos,
                       "consentimiento": g.consentimiento,
                       "revisado": bool(g.transcripcion.strip() and g.consentimiento)})
    return salida


def transcribir(ruta_audio: str) -> dict:
    """Lo que el modelo oye hoy. Es el borrador que nosotros corregimos."""
    with open(ruta_audio, "rb") as f:
        with httpx.Client(timeout=300) as cli:
            r = cli.post(f"{INSTANCIA}/entender",
                         files={"audio": (Path(ruta_audio).name, f.read(), "audio/wav")},
                         data={"lengua": "quy_Latn"})
    return r.json()


def guardar(persona: str, numero: int, transcripcion: str, consentimiento: bool,
            descartar: bool = False) -> dict:
    manifiesto = RAIZ / persona / "manifiesto.jsonl"
    grabaciones = leer_manifiesto(manifiesto)
    nuevas, encontrado = [], False
    for g in grabaciones:
        if g.numero == numero:
            encontrado = True
            if descartar:
                continue        # fuera del manifiesto: audio inservible
            g = Grabacion(persona=g.persona, bloque=g.bloque, numero=g.numero, audio=g.audio,
                          transcripcion=transcripcion.strip(), castellano=g.castellano,
                          segundos=g.segundos, consentimiento=consentimiento)
        nuevas.append(g)
    escribir_manifiesto(manifiesto, nuevas,
                        cabecera="revisado a mano: la transcripcion es verdad de referencia")
    listos = sum(1 for g in nuevas if g.transcripcion.strip() and g.consentimiento)
    return {"guardado": encontrado, "total": len(nuevas), "revisados": listos}


def exportar(persona: str | None = None) -> dict:
    """Los tres conjuntos que alimentan los tres ajustes."""
    destino = Path("datos/corpus")
    destino.mkdir(parents=True, exist_ok=True)
    asr, tts, traduccion = [], [], []
    for p in ([persona] if persona else personas()):
        for g in leer_manifiesto(RAIZ / p / "manifiesto.jsonl"):
            if not (g.transcripcion.strip() and g.consentimiento):
                continue
            asr.append({"audio": g.audio, "texto": g.transcripcion, "persona": g.persona})
            tts.append({"texto": g.transcripcion, "audio": g.audio, "persona": g.persona})
            if g.castellano.strip():
                traduccion.append({"castellano": g.castellano, "chanka": g.transcripcion,
                                   "persona": g.persona})
    for nombre, filas in (("asr", asr), ("tts", tts), ("traduccion", traduccion)):
        (destino / f"{nombre}.jsonl").write_text(
            "\n".join(json.dumps(f, ensure_ascii=False) for f in filas) + "\n", encoding="utf-8")
    return {"asr": len(asr), "tts": len(tts), "traduccion": len(traduccion),
            "carpeta": str(destino)}
