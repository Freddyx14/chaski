"""El ciclo completo del intérprete, sobre el servicio de voz de la instancia.

Paciente (quechua):  audio -> /idioma -> /entender -> Claude lo pasa a castellano
Enfermera (castellano): texto -> auditoría de Freddy -> chanka -> /hablar -> audio

`modo_ensayo` existe porque los modelos todavía NO están ajustados: cuando la
auditoría bloquea SOLO por «términos sin traducción segura», en ensayo se deja
pasar con aviso, en vez de callar el sistema entero. Cualquier otro bloqueo
—un dato crítico cambiado— sigue siendo bloqueo, siempre.
"""
from __future__ import annotations

import json
import os
import re
import time

import httpx

INSTANCIA = os.environ.get("CHASKI_VOZ", "http://127.0.0.1:8010")
MODELO_TEXTO = os.environ.get("CHASKI_MODELO_TEXTO", "claude-haiku-4-5")

SISTEMA_QUY_ES = """Pasas al castellano lo que dijo un paciente quechuahablante en la posta de
Pilpichaca. El texto te llega de un reconocimiento de voz que se equivoca, sobre todo en préstamos del
castellano (doctor, pastilla, posta) y en nombres propios.

Devuelves SOLO JSON:
{"castellano": "...", "literal": "...", "dudas": ["lo que no entendiste"], "seguro": true|false}

- "castellano": lo que la persona quiso decir, en castellano llano.
- "literal": palabra por palabra, aunque suene raro. Sirve para que la enfermera compare.
- Si el reconocimiento trae algo que no se entiende, va en "dudas" y NO lo completas.
- Si dudas del sentido general, "seguro": false. Es una posta: callar es mejor que inventar."""


def _json_de(texto: str) -> dict:
    bloque = re.search(r"\{.*\}", texto, re.S)
    if not bloque:
        raise ValueError(f"sin JSON: {texto[:160]}")
    return json.loads(bloque.group(0))


def turno_del_paciente(audio: bytes, nombre: str = "turno.wav") -> dict:
    """Audio en quechua -> lo que la enfermera lee en castellano."""
    pasos = {}
    with httpx.Client(timeout=300) as cli:
        t0 = time.perf_counter()
        lengua = cli.post(f"{INSTANCIA}/idioma",
                          files={"audio": (nombre, audio, "audio/wav")}).json()
        pasos["idioma_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        t0 = time.perf_counter()
        oido = cli.post(f"{INSTANCIA}/entender",
                        files={"audio": (nombre, audio, "audio/wav")},
                        data={"lengua": "quy_Latn"}).json()
        pasos["entender_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    from anthropic import Anthropic
    t0 = time.perf_counter()
    respuesta = Anthropic().messages.create(
        model=MODELO_TEXTO, max_tokens=700, system=SISTEMA_QUY_ES,
        messages=[{"role": "user", "content":
                   f"El reconocimiento oyó esto en chanka:\n\n{oido['texto']}"}])
    pasos["traducir_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    d = _json_de("".join(b.text for b in respuesta.content if b.type == "text"))

    return {"idioma": lengua, "chanka_oido": oido["texto"], "modelo_asr": oido["modelo"],
            "castellano": d.get("castellano", ""), "literal": d.get("literal", ""),
            "dudas": d.get("dudas", []), "seguro": bool(d.get("seguro")),
            "modelo_texto": MODELO_TEXTO, "pasos": pasos,
            "total_ms": round(sum(pasos.values()), 1)}


def turno_de_la_enfermera(texto_es: str, modo_ensayo: bool = True,
                          forzar: bool = False, rapido: bool = True,
                          con_audio: bool = True) -> dict:
    """Castellano -> auditoría -> chanka -> audio.

    `rapido` usa la orquestación en paralelo con modelos mezclados: 5.3 s en vez
    de 26 s. `con_audio=False` devuelve solo el texto, para que la página lo
    muestre YA y pida la voz después.
    """
    import anthropic

    t0 = time.perf_counter()
    if rapido:
        from servicio.auditoria_rapida import auditar_rapido
        d = auditar_rapido(texto_es)
        r = type("R", (), d)
        r.diferencias = d["diferencias"]
        detalle = d["tiempos"]
    else:
        from rimay.auditoria import auditar
        res = auditar(anthropic.Anthropic(), texto_es)
        d = {"quechua": res.quechua, "retraduccion": res.retraduccion, "enviar": res.enviar,
             "motivo": res.motivo, "terminos_inseguros": res.terminos_inseguros,
             "diferencias": [x.model_dump() for x in res.diferencias]}
        r = type("R", (), d)
        r.diferencias = d["diferencias"]
        detalle = {}
    auditoria_ms = round((time.perf_counter() - t0) * 1000, 1)

    solo_terminos = (not r.diferencias) and bool(r.terminos_inseguros)
    # `forzar` es una decision humana explicita en el ensayo, no una regla del
    # sistema: alguien ve el bloqueo, lo lee y decide igual. Nunca por defecto.
    se_dice = r.enviar or (modo_ensayo and solo_terminos) or forzar

    audio_b64, hablar_ms = None, None
    if se_dice and con_audio:
        import base64
        with httpx.Client(timeout=300) as cli:
            t0 = time.perf_counter()
            voz = cli.post(f"{INSTANCIA}/hablar", data={"texto": r.quechua})
            hablar_ms = round((time.perf_counter() - t0) * 1000, 1)
        audio_b64 = base64.b64encode(voz.content).decode()

    return {"quechua": r.quechua, "retraduccion": r.retraduccion,
            "aprobado_por_auditoria": r.enviar, "motivo": r.motivo,
            "terminos_inseguros": r.terminos_inseguros,
            "diferencias": d["diferencias"],
            "se_dice": se_dice,
            "aviso": (("Forzado a mano en ensayo: la auditoría NO lo aprueba y alguien decidió decirlo "
                       "igual. En producción esto no existe.") if (forzar and not r.enviar)
                      else ("La auditoría no lo aprueba, pero en modo ensayo se dice igual porque el "
                            "bloqueo es solo por términos sin traducción segura. Con el modelo ajustado "
                            "esto se corrige.") if (se_dice and not r.enviar) else None),
            "forzado": bool(forzar and not r.enviar),
            "audio_wav_b64": audio_b64,
            "pasos": {"auditoria_ms": auditoria_ms, "hablar_ms": hablar_ms, **detalle},
            "rapido": rapido,
            "total_ms": round(auditoria_ms + (hablar_ms or 0), 1)}


def decir_en_voz(texto_quechua: str) -> tuple[bytes, float]:
    """Solo la voz. La página la pide aparte, cuando ya mostró el texto."""
    with httpx.Client(timeout=300) as cli:
        t0 = time.perf_counter()
        voz = cli.post(f"{INSTANCIA}/hablar", data={"texto": texto_quechua})
    return voz.content, round((time.perf_counter() - t0) * 1000, 1)
