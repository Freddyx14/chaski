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


BLOQUES_CUADERNILLO = {
    "C": "clinicas_sin_traducir",
    "M": "medicamentos_y_prestamos",
    "N": "numeros_y_tiempos",
    "B": "respuestas_libres",
}


def referencias(bloque: str = "") -> dict:
    """Lo que el cuadernillo dice que deberia haberse dicho, por (bloque, numero).

    Las claves siguen los codigos del cuadernillo de Freddy: C1, M5, N3, B2, E7.
    Se MUESTRA al corregir, no se da por bueno: la persona pudo decir otra cosa,
    y lo que manda es lo que de verdad se oye en el audio.
    """
    ruta = Path("datos/frases/frases.json")
    if not ruta.exists():
        return {}
    d = json.loads(ruta.read_text(encoding="utf-8"))
    salida: dict[tuple[str, int], dict] = {}
    for letra, clave in BLOQUES_CUADERNILLO.items():
        for i, t in enumerate(d.get(clave, []), 1):
            salida[(letra, i)] = {"castellano": t, "chanka_esperado": ""}
    for i, f in enumerate(d.get("verificadas", []), 1):
        salida[("E", i)] = {"castellano": f["castellano"], "chanka_esperado": f["chanka"]}
    if bloque:
        return {k[1]: v for k, v in salida.items() if k[0] == bloque}
    return salida


def cuantas(bloque: str) -> int:
    """Cuantas frases trae ese bloque del cuadernillo."""
    return len(referencias(bloque))


def recibir_nota(persona: str, bloque: str, datos: bytes, nombre: str,
                 esperadas: int = 0) -> dict:
    """Una nota de voz larga -> clips numerados + manifiesto, listos para corregir.

    Si la persona ya mando notas antes, los clips nuevos SE AGREGAN y la
    numeracion sigue donde quedo. Nadie manda 160 frases en un solo audio: van a
    llegar en varias tandas, y renumerar desde 1 en cada una destruiria el
    emparejamiento con el cuadernillo.
    """
    import subprocess
    import tempfile

    from voz.segmentar import mejor_particion, recortar
    from voz.ingesta import convertir, duracion

    carpeta = RAIZ / persona
    carpeta.mkdir(parents=True, exist_ok=True)
    crudo = tempfile.NamedTemporaryFile(suffix=Path(nombre).suffix or ".ogg", delete=False)
    crudo.write(datos)
    crudo.close()

    previas = []
    manifiesto = carpeta / "manifiesto.jsonl"
    if manifiesto.exists():
        previas = leer_manifiesto(manifiesto)
    desde = max((g.numero for g in previas), default=0) + 1

    completo = carpeta / f"completo_{desde:03d}.wav"
    total = convertir(crudo.name, completo)
    Path(crudo.name).unlink(missing_ok=True)

    refs = referencias(bloque)
    if not esperadas:
        esperadas = max(len(refs) - desde + 1, 1)
    trozos, diagnostico = mejor_particion(completo, total, esperadas)

    grabaciones = list(previas)
    for j, t in enumerate(trozos):
        i = desde + j
        destino = carpeta / f"{persona}_{bloque}_{i:03d}.wav"
        recortar(completo, destino, t.inicio, t.largo)
        ref = refs.get(i, {})
        grabaciones.append(Grabacion(
            persona=persona, bloque=bloque, numero=i, audio=str(destino),
            transcripcion="", castellano=ref.get("castellano", ""),
            segundos=round(t.largo, 2), consentimiento=False))
    escribir_manifiesto(manifiesto, grabaciones,
                        cabecera="sin revisar: falta transcripcion y consentimiento")
    return {"persona": persona, "clips_nuevos": len(trozos), "clips_total": len(grabaciones),
            "desde": desde, "segundos": total, "esperadas": esperadas,
            "coincide": len(trozos) == esperadas, "umbral": diagnostico["umbral"]}


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
        ref = referencias(g.bloque).get(g.numero, {})
        salida.append({"nombre": g.nombre, "audio": g.audio, "numero": g.numero,
                       "bloque": g.bloque, "castellano": g.castellano or ref.get("castellano", ""),
                       "chanka_esperado": ref.get("chanka_esperado", ""),
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
