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
import re
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


MAXIMO_CODIGO_S = 1.8      # «ce uno» dura menos de dos segundos
HUECO_CODIGO_S = 1.6       # el silencio entre el codigo y su frase


def unir_codigo_con_frase(trozos: list) -> tuple[list, int]:
    """Junta «C1» con la frase que le sigue.

    La familia graba: codigo, pausa, frase. Esa pausa hace que el corte por
    silencios produzca DOS trozos por frase. Aqui se vuelven a unir: un trozo
    corto seguido de cerca por otro es un codigo y su frase, y se guardan como
    un solo clip. Asi el conteo cuadra con el cuadernillo y el codigo queda
    grabado dentro del audio, que sirve para verificar al corregir.
    """
    unidos, i, juntados = [], 0, 0
    while i < len(trozos):
        actual = trozos[i]
        siguiente = trozos[i + 1] if i + 1 < len(trozos) else None
        es_codigo = (actual.largo <= MAXIMO_CODIGO_S and siguiente is not None
                     and siguiente.inicio - actual.fin <= HUECO_CODIGO_S)
        if es_codigo:
            unidos.append(type(actual)(inicio=actual.inicio, fin=siguiente.fin))
            juntados += 1
            i += 2
        else:
            unidos.append(actual)
            i += 1
    return unidos, juntados


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
    # Se busca el doble de trozos: cada frase llega como «codigo + frase».
    trozos, diagnostico = mejor_particion(completo, total, esperadas * 2)
    trozos, juntados = unir_codigo_con_frase(trozos)
    if abs(len(trozos) - esperadas) > abs(len(trozos) + juntados - esperadas):
        # Si unir empeoro el conteo, la nota no traia codigos: se deshace.
        trozos, diagnostico = mejor_particion(completo, total, esperadas)
        juntados = 0

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
    return {"persona": persona, "bloque": bloque, "clips_nuevos": len(trozos),
            "clips_total": len(grabaciones), "desde": desde, "segundos": total,
            "esperadas": esperadas, "coincide": len(trozos) == esperadas,
            "codigos_unidos": juntados, "umbral": diagnostico["umbral"]}


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


# --- el codigo sale del audio, no de la posicion ---------------------------

LETRAS_HABLADAS = {"ce": "C", "se": "C", "c": "C", "eme": "M", "m": "M",
                   "ene": "N", "n": "N", "be": "B", "ve": "B", "b": "B", "e": "E"}
NUMEROS_HABLADOS = {
    "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
    "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
    "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16, "dieciséis": 16,
    "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20,
}


def leer_codigo(texto: str) -> tuple[str, int] | None:
    """Saca «C1» de lo que se oye al principio del clip.

    Cartesia suele devolver ya «C1.» en cifra, pero tambien puede escribir
    «ce uno». Se aceptan las dos formas, y solo al principio: un numero en
    medio de la frase no es un codigo.
    """
    limpio = texto.strip().lower()
    cifra = re.match(r"^\s*([cmnbe])\s*[\.\-:]?\s*(\d{1,3})\b", limpio)
    if cifra:
        return cifra.group(1).upper(), int(cifra.group(2))
    palabras = re.split(r"[\s,\.]+", limpio)[:3]
    if len(palabras) >= 2 and palabras[0] in LETRAS_HABLADAS:
        for p in palabras[1:]:
            if p in NUMEROS_HABLADOS:
                return LETRAS_HABLADAS[palabras[0]], NUMEROS_HABLADOS[p]
            if p.isdigit():
                return LETRAS_HABLADAS[palabras[0]], int(p)
    return None


def detectar_codigo(ruta_audio: str) -> dict:
    """Transcribe el clip en castellano y busca el codigo al inicio."""
    from servicio.flujo import entender_castellano

    datos = Path(ruta_audio).read_bytes()
    oido = entender_castellano(datos, Path(ruta_audio).name)
    codigo = leer_codigo(oido["texto"])
    return {"texto": oido["texto"], "ms": oido["ms"],
            "bloque": codigo[0] if codigo else None,
            "numero": codigo[1] if codigo else None}


def recodificar(persona: str, numero_actual: int, bloque_actual: str,
                bloque_nuevo: str, numero_nuevo: int) -> dict:
    """Cambia el identificador de un clip. El audio no se toca, solo su etiqueta."""
    manifiesto = RAIZ / persona / "manifiesto.jsonl"
    grabaciones = leer_manifiesto(manifiesto)
    chocado = [g for g in grabaciones
               if g.bloque == bloque_nuevo and g.numero == numero_nuevo
               and not (g.bloque == bloque_actual and g.numero == numero_actual)]
    nuevas = []
    for g in grabaciones:
        if g.bloque == bloque_actual and g.numero == numero_actual:
            g = Grabacion(persona=g.persona, bloque=bloque_nuevo, numero=numero_nuevo,
                          audio=g.audio, transcripcion=g.transcripcion,
                          castellano=referencias(bloque_nuevo).get(numero_nuevo, {})
                          .get("castellano", ""),
                          segundos=g.segundos, consentimiento=g.consentimiento)
        nuevas.append(g)
    escribir_manifiesto(manifiesto, nuevas, cabecera="identificadores revisados a mano")
    return {"hecho": True, "choca_con": f"{bloque_nuevo}{numero_nuevo}" if chocado else None}
