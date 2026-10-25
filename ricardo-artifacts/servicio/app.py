"""Servicio de prueba de Chaski: cámara o foto -> Claude -> qué es y para qué sirve.

Esto NO es la app de Freddy. Es el banco de pruebas para enchufar la visión
antes de que la UI exista, y para que los dos podamos probarla desde el navegador.

Arranque:
  cd ricardo-artifacts
  set -a; source .env; set +a
  uv run --with fastapi --with uvicorn --with anthropic --with python-multipart \
      uvicorn servicio.app:aplicacion --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

# El modulo de traduccion y auditoria es de Freddy. Se IMPORTA, no se copia ni
# se toca: si el mejora el glosario o la auditoria, esto lo hereda solo.
APP_DE_FREDDY = (Path(__file__).resolve().parents[2] / "app")
if APP_DE_FREDDY.exists() and str(APP_DE_FREDDY) not in sys.path:
    sys.path.insert(0, str(APP_DE_FREDDY))

from fastapi import FastAPI, File, Form, UploadFile
from fastapi import Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from servicio.vision import MODELO, como_json, leer

try:
    import anthropic
    from chaski.auditoria import auditar
    HAY_TRADUCTOR = True
except Exception as _e:          # el repo puede no tener app/ al lado
    HAY_TRADUCTOR = False
    _FALLO_TRADUCTOR = str(_e)

AQUI = Path(__file__).parent
CHASKI = Path("../design/chaski")

aplicacion = FastAPI(title="Chaski · banco de pruebas de visión")
aplicacion.mount("/estatico", StaticFiles(directory=AQUI / "static"), name="estatico")
if CHASKI.exists():
    aplicacion.mount("/chaski", StaticFiles(directory=CHASKI), name="chaski")


@aplicacion.get("/")
def portada():
    return FileResponse(AQUI / "static" / "index.html")


@aplicacion.on_event("startup")
def _precargar_banco():
    """Los embeddings del banco tardan en cargar; que los pague el arranque."""
    try:
        from chaski import banco as banco_frases
        banco_frases.precargar()
    except Exception as e:
        print(f"banco sin precargar: {type(e).__name__}: {e}", flush=True)


@aplicacion.get("/salud")
def salud():
    return {"modelo_vision": MODELO,
            "clave_anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "clave_cartesia": bool(os.environ.get("CARTESIA_API_KEY")),
            "chaski": CHASKI.exists(),
            "traductor_de_freddy": HAY_TRADUCTOR}


@aplicacion.get("/flujo")
def pagina_flujo():
    return FileResponse(AQUI / "static" / "flujo.html")


CARPETAS_MUESTRAS = (Path("datos/muestras_quy"), Path("datos/prueba_minima"))


@aplicacion.get("/muestras")
def muestras():
    """Los audios en chanka que pueden hacer de paciente, con su texto de referencia."""
    salida = []
    for carpeta in CARPETAS_MUESTRAS:
        if not carpeta.exists():
            continue
        fichas = {}
        ficha = carpeta / "fichas.json"
        if ficha.exists():
            for f in json.loads(ficha.read_text(encoding="utf-8")):
                fichas[f.get("archivo", "")] = f
        for wav in sorted(carpeta.glob("quy_*.wav")):
            f = fichas.get(wav.name, {})
            salida.append({"nombre": wav.name, "carpeta": carpeta.name,
                           "segundos": f.get("segundos"),
                           "frases": f.get("frases"),
                           "referencia": f.get("chanka", ""),
                           "castellano": f.get("castellano", "")})
    return {"audios": salida}


@aplicacion.get("/muestras/{nombre}")
def muestra(nombre: str):
    for carpeta in CARPETAS_MUESTRAS:
        ruta = carpeta / nombre
        if ruta.exists():
            return FileResponse(ruta)
    return JSONResponse({"error": "no existe"}, 404)


@aplicacion.post("/escuchar")
async def escuchar(audio: UploadFile = File(...)):
    """Voz de la enfermera en castellano -> texto, con Cartesia."""
    from servicio.flujo import entender_castellano
    try:
        return entender_castellano(await audio.read(), audio.filename or "turno.webm")
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


def _voz_para_chaski(texto: str, idioma: str) -> bytes:
    """La síntesis que el intérprete llama MIENTRAS el crítico revisa.

    Hacerla ahí quita ~1 s por turno: el audio se genera en paralelo con la
    revisión en vez de después. Si el crítico bloquea, el audio se descarta y
    nunca suena — generar no es decir.
    """
    from servicio.flujo import decir_en_voz, voz_castellano

    if idioma == "quy":
        audio, _ = decir_en_voz(texto, voz=os.environ.get("CHASKI_VOZ_QUY", "mama_freddy"))
        return audio
    try:
        return voz_castellano(texto)
    except Exception as e:
        # Respaldo: robotico, pero nunca mudo. Que Chaski se quede callado en
        # una posta es peor que sonar mal.
        print(f"Cartesia no respondio ({type(e).__name__}); voz de respaldo", flush=True)
        audio, _ = decir_en_voz(texto, voz="base")
        return audio


def _dependencias(motor: str):
    """El cableado del intérprete con el traductor elegido.

    `servicio.turno` arma las dependencias con motor «claude» fijo. Pasarlas
    desde aquí es el hueco que su propia firma deja para esto, y evita tocar
    su archivo.
    """
    import anthropic

    from chaski import orquestador
    return orquestador.dependencias(anthropic.Anthropic(),
                                    motor="nllb" if motor == "nllb" else "claude")


def _detectar_idioma(audio: bytes, nombre: str) -> dict:
    """El /idioma de la instancia (mms-lid-512, ~49 ms): {codigo: 'spa'|'quy', confianza}."""
    import httpx

    from servicio.flujo import INSTANCIA, _a_wav
    with httpx.Client(timeout=30) as cli:
        r = cli.post(f"{INSTANCIA}/idioma",
                     files={"audio": ("turno.wav", _a_wav(audio, nombre), "audio/wav")})
    r.raise_for_status()
    return r.json()


def _oidos_auto() -> dict:
    from servicio.flujo import entender_castellano, entender_chanka
    return {"detectar_idioma": _detectar_idioma, "oir_castellano": entender_castellano,
            "oir_quechua": entender_chanka}


# ----------------------------------------------------------------- opciones al bloquear

CODIGOS_NLLB = {"spa": "spa_Latn", "quy": "quy_Latn"}

AVISO_CONFIRMADA = (
    "Lo confirmó una persona. Chaski no pudo comprobar el dato por su cuenta: la lectura de vuelta "
    "está para revisarla antes de decir que sí."
)


def _mt_local(texto: str, desde: str, hacia: str) -> str:
    """NLLB-1.3B en la instancia, una dirección. Si no responde devuelve vacío: una opción de menos, nunca un error."""
    import httpx

    from servicio.flujo import INSTANCIA
    texto = (texto or "").strip()
    if not texto:
        return ""
    try:
        with httpx.Client(timeout=30) as cli:
            r = cli.post(f"{INSTANCIA}/traducir",
                         data={"texto": texto, "desde": CODIGOS_NLLB.get(desde, desde),
                               "hacia": CODIGOS_NLLB.get(hacia, hacia)})
        r.raise_for_status()
        d = r.json()
        return (d.get("traduccion") or d.get("texto") or "").strip()
    except Exception as e:  # noqa: BLE001
        print(f"opciones: NLLB no respondio ({type(e).__name__}: {e})", flush=True)
        return ""


def _texto_alternativa(a) -> str:
    """Las n-mejores vienen como texto o como [texto, puntaje] (lo que devuelve /entender)."""
    if isinstance(a, str):
        return a.strip()
    if isinstance(a, (list, tuple)) and a:
        return str(a[0]).strip()
    if isinstance(a, dict):
        return str(a.get("texto") or a.get("text") or "").strip()
    return ""


def _degenerada(texto: str) -> bool:
    """NLLB se traba y repite la misma palabra veinte veces. Una propuesta así no se ofrece."""
    palabras = [w for w in (texto or "").lower().split() if w]
    return len(palabras) >= 6 and len(set(palabras)) <= max(2, len(palabras) // 4)


SISTEMA_LECTURA = (
    "Eres el intérprete de una posta de salud de Pilpichaca (Huancavelica, Perú). Recibes la transcripción "
    "CRUDA de un reconocedor de voz, que se equivoca sobre todo en los préstamos del castellano dichos dentro "
    "de una frase en quechua chanka («para sitamulta» por «paracetamolta», «pastiya», «dotora», «presyun»). "
    "Tu trabajo es decir cuál es la lectura más plausible y traducirla. "
    "Responde SOLO un objeto JSON con estas claves: "
    "`lectura` (la frase arreglada, en el MISMO idioma en que se oyó), "
    "`traduccion` (esa lectura en el idioma pedido), "
    "`cambio` (qué palabra arreglaste, o \"\" si no arreglaste ninguna), "
    "`confianza` (\"alta\" | \"media\" | \"baja\"). "
    "Pon `confianza` en \"baja\" si la transcripción es ruido, sílabas sueltas, o si para leerla tendrías que "
    "inventar un número o un medicamento que no está. Nunca inventes una dosis ni una frecuencia."
)


def _lectura_de_chaski(crudo: str, origen: str, destino: str) -> dict | None:
    """La lectura que Chaski propone de una transcripción rota, con Claude. None si no hay ninguna creíble.

    Esto es lo que el NLLB local no puede hacer: NLLB traduce lo que le den, letra por letra, y de
    «upshashkani para sitamulta» saca una frase inventada. El intérprete sí sabe que ahí dentro hay un
    medicamento mal oído. Por eso la propuesta la hace Claude y NLLB queda de respaldo sin red.
    """
    import anthropic

    nombre = {"spa": "castellano", "quy": "quechua chanka"}
    try:
        cli = anthropic.Anthropic()
        r = cli.messages.create(
            model=os.environ.get("CHASKI_MODELO_CRITICO", "claude-sonnet-5"),
            # Sin pensar: con el presupuesto por defecto los 500 tokens se iban enteros en el bloque
            # `thinking` y la respuesta volvía con stop_reason `max_tokens` y sin JSON.
            max_tokens=600, thinking={"type": "disabled"}, system=SISTEMA_LECTURA,
            messages=[{"role": "user", "content":
                       f"Se oyó en {nombre.get(origen, origen)}: «{crudo}»\n"
                       f"Tradúcela al {nombre.get(destino, destino)}."}])
        texto = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        d = json.loads(texto[texto.index("{"):texto.rindex("}") + 1])
    except Exception as e:  # noqa: BLE001  sin propuesta se sigue pidiendo repetir, que es lo de antes
        print(f"opciones: lectura de Chaski falló ({type(e).__name__}: {e})", flush=True)
        return None
    if str(d.get("confianza", "")).lower() == "baja":
        return None
    if not str(d.get("traduccion", "")).strip():
        return None
    return d


def _con_opciones(r, alternativas=None):
    """Cuando Chaski bloquea, agrega `opciones`: repetir, o decir lo que él mismo propuso.

    El caso que lo pide: una sola palabra en castellano dentro de una frase en chanka —un medicamento,
    «presión», «control»— hace dudar al crítico y la consulta se traba en «¿me lo repite?». Con esto la
    pantalla ya trae qué habría dicho Chaski y su lectura de vuelta, y la persona elige: repetir, o
    decirlo igual. Confirmar NO verifica nada; lo dice una persona, y el aviso de `/confirmar` lo deja escrito.

    No cambia ningún campo existente. `opciones` es un campo nuevo: una app que no lo lea sigue igual.
    """
    if not isinstance(r, dict) or r.get("opciones"):
        return r
    accion = r.get("accion")
    # `no_entendi` llega con estado "dicho" (Chaski SÍ dijo su frase de disculpa) y es el caso que más
    # traba la consulta, así que no se filtra por estado. Para `repreguntar` sí: una repregunta normal
    # —«¿cada cuánto?»— es una pregunta de verdad que espera respuesta, no una frase que confirmar.
    if accion == "repreguntar" and r.get("estado") not in ("bloqueado", "dicho_con_aviso"):
        return r
    if accion not in ("repreguntar", "no_entendi"):
        return r

    # Chaski le responde a quien acaba de hablar, así que `para` dice de qué idioma venía lo que se oyó.
    origen = "spa" if r.get("para") == "personal" else "quy"
    destino = "quy" if origen == "spa" else "spa"
    # En `no_entendi`, `texto_pulido` es la disculpa de Chaski, no lo que dijo la persona: solo sirve el original.
    base = ((r.get("texto_original") or "") if accion == "no_entendi"
            else (r.get("texto_pulido") or r.get("texto_original") or "")).strip()

    opciones = [{"id": "repetir", "etiqueta": "Que lo repita", "texto": None, "idioma": None,
                 "glosa": None, "para": r.get("para"), "verificado": False}]

    vistos = set()
    para_quien = "paciente" if destino == "quy" else "personal"
    # Solo se propone hacia el personal (decisión de Freddy, dom 08:40, antes del jurado).
    # Lo encontró probando en vivo: «brazo izquierdo» se bloqueó por `partes_cuerpo` y la propuesta
    # decía «Lloqe makikipi…» —maki es mano, no brazo—, pero la `glosa` que acompañaba era la frase
    # ORIGINAL de la enfermera, no una retraducción a ciegas. Es decir: ella leía lo que ella misma
    # había dicho, confirmaba, y el paciente escuchaba «mano». La lectura de vuelta solo sirve si la
    # hace alguien que no vio el original, y la de `_lectura_de_chaski` no lo es.
    # Hacia el personal no pasa: la propuesta va en castellano y la enfermera la juzga directo.
    # Para devolverla del lado del paciente hace falta la retraducción a ciegas del crítico.
    if para_quien == "paciente":
        return r
    if base:
        lectura = _lectura_de_chaski(base, origen, destino)
        if lectura:
            propuesta = str(lectura["traduccion"]).strip()
            vistos.add(propuesta.lower())
            opciones.append({"id": "propuesta", "etiqueta": "Quise decir esto",
                             "texto": propuesta, "idioma": destino,
                             "glosa": str(lectura.get("lectura") or base).strip(),
                             "origen": base, "cambio": str(lectura.get("cambio") or ""),
                             "confianza": lectura.get("confianza"), "para": para_quien,
                             "verificado": False,
                             "motor": os.environ.get("CHASKI_MODELO_CRITICO", "claude-sonnet-5")})
        else:  # sin red o sin lectura creíble: NLLB, y solo si no se traba repitiendo
            propuesta = _mt_local(base, origen, destino)
            glosa = _mt_local(propuesta, destino, origen) if propuesta else ""
            if propuesta and not _degenerada(propuesta) and not _degenerada(glosa):
                vistos.add(propuesta.lower())
                opciones.append({"id": "propuesta", "etiqueta": "Quise decir esto",
                                 "texto": propuesta, "idioma": destino, "glosa": glosa,
                                 "origen": base, "para": para_quien,
                                 "verificado": False, "motor": "nllb-1.3B"})

    # Del lado del paciente las n-mejores del reconocedor son el resto de lecturas posibles de lo mismo.
    for i, a in enumerate(alternativas or []):
        texto = _texto_alternativa(a)
        if not texto or texto.lower() == base.lower():
            continue
        traducida = _mt_local(texto, origen, destino)
        if not traducida or traducida.lower() in vistos:
            continue
        vistos.add(traducida.lower())
        if _degenerada(traducida):
            continue
        opciones.append({"id": f"alterna_{i}", "etiqueta": "O quizá dijo esto",
                         "texto": traducida, "idioma": destino, "glosa": texto, "origen": texto,
                         "para": para_quien, "verificado": False, "motor": "nllb-1.3B"})
        if len(opciones) >= 4:
            break

    if len(opciones) == 1:  # solo quedó «repetir»: no hay nada que ofrecer, se deja como estaba
        return r
    r["opciones"] = opciones
    return r


def _con_opciones_sse(eventos, alternativas=None):
    """Lo mismo sobre la ruta en vivo: solo toca el evento `resultado`, el resto pasa tal cual."""
    for bloque in eventos:
        if isinstance(bloque, str) and bloque.startswith("event: resultado"):
            cabecera, _, resto = bloque.partition("\n")
            datos = resto.strip()
            if datos.startswith("data: "):
                try:
                    r = _con_opciones(json.loads(datos[len("data: "):]), alternativas)
                    bloque = f"{cabecera}\ndata: {json.dumps(r, ensure_ascii=False)}\n\n"
                except Exception as e:  # noqa: BLE001  un evento intacto vale más que un error
                    print(f"opciones sse: {type(e).__name__}: {e}", flush=True)
        yield bloque


@aplicacion.post("/confirmar")
def confirmar(texto: str = Form(...), idioma: str = Form("quy"), para: str = Form("paciente"),
              contexto: str = Form(""), dicho: str = Form(""), lectura: str = Form("")):
    """Dice una de las `opciones` que devolvió un turno bloqueado, tal cual, porque una persona la confirmó.

    `texto` es lo que se va a decir y `idioma` en cuál ('quy' | 'spa'); `dicho` es lo que se había oído y
    `lectura` cómo lo leyó Chaski al arreglarlo (el campo `glosa` de la opción), para que el historial se
    quede con la frase buena y la consulta siga. No pasa por el crítico a propósito: ya pasó y
    bloqueó. Quien responde por esta frase es quien tocó el botón, y eso va escrito en `aviso`.
    """
    from chaski.interprete import Contexto

    texto = (texto or "").strip()
    if not texto:
        return JSONResponse({"error": "falta el texto a decir"}, status_code=400)
    if idioma not in ("quy", "spa"):
        return JSONResponse({"error": f"idioma desconocido: {idioma}"}, status_code=400)

    t0 = time.perf_counter()
    try:
        ctx = Contexto.model_validate(json.loads(contexto)) if contexto.strip() else Contexto()
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": f"contexto mal formado: {type(e).__name__}: {e}"}, status_code=400)

    audio_b64 = None
    try:
        wav = _voz_para_chaski(texto, idioma)
        audio_b64 = base64.b64encode(wav).decode() if wav else None
    except Exception as e:  # noqa: BLE001  sin voz se muestra el texto igual
        print(f"confirmar: sin voz ({type(e).__name__}: {e})", flush=True)

    quien = "personal" if para == "paciente" else "paciente"
    dicho = (lectura.strip() or dicho.strip())  # la lectura arreglada vale más en el historial que la rota
    # El turno que bloqueó ya guardó lo que se oyó: sin esto la frase quedaba dos veces en el historial.
    ya = ctx.historial[-2:] if ctx.historial else []
    if dicho and not any(h.rol == quien and h.texto.strip() == dicho for h in ya):
        ctx.agregar(quien, dicho)
    ctx.agregar("chaski", texto)
    ctx.repreguntas_seguidas.clear()  # se resolvió: la consulta sigue, no encadena otra repregunta

    return {"estado": "dicho_con_aviso", "accion": "traducir", "motivo": "confirmada por una persona",
            "dato_faltante": None, "frase_banco_id": None, "para": para, "idioma_salida": idioma,
            "texto_original": dicho, "texto_pulido": dicho, "texto_salida": texto,
            "audio_wav_b64": audio_b64, "audio": None, "aviso": AVISO_CONFIRMADA,
            "confirmada": True, "sembrada": False, "modelos": {"principal": None, "critico": None},
            "paso_fallido": None, "ms": {"total": round((time.perf_counter() - t0) * 1000, 1)},
            "contexto": ctx.model_dump()}


@aplicacion.post("/turno")
async def turno_auto(audio: UploadFile = File(...), contexto: str = Form("")):
    """Manos libres: audio de cualquiera de los dos, Chaski decide quién habló y qué hacer.

    Un solo llamado. El detector dice el idioma, eso dice quién habló, y de ahí
    sigue el intérprete de siempre. Si el detector duda o se cae, alterna con el
    último que habló: en una consulta se habla por turnos, así que adivinar por
    alternancia acierta más que adivinar por idioma dudoso.
    """
    from chaski import servicio as interprete
    try:
        return _con_opciones(
            interprete.turno_auto(await audio.read(), audio.filename or "turno.wav",
                                  contexto, dependencias=_dependencias("claude"),
                                  voz_fn=_voz_para_chaski, **_oidos_auto()))
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/turno/vivo")
async def turno_auto_vivo(audio: UploadFile = File(...), contexto: str = Form("")):
    """Lo mismo en vivo: `oido` (~1-2 s), `decision`, `resultado` (o `error`)."""
    from fastapi.responses import StreamingResponse

    from chaski import servicio as interprete
    # Se lee aquí: el generador corre después, fuera del async.
    datos = await audio.read()
    return StreamingResponse(
        _con_opciones_sse(
            interprete.turno_auto_eventos(datos, audio.filename or "turno.wav", contexto,
                                          dependencias=_dependencias("claude"),
                                          voz_fn=_voz_para_chaski, **_oidos_auto())),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@aplicacion.post("/turno/paciente")
async def turno_paciente(audio: UploadFile = File(...), contexto: str = Form(""),
                         lengua: str = Form(""), motor: str = Form("claude")):
    """El paciente habla chanka. Lo oye nuestro reconocedor, lo interpreta el de Freddy.

    Las dos mitades: `/entender` de la instancia pone el texto y las N mejores
    alternativas; `chaski.servicio.turno` decide qué hacer con eso —traducir,
    repreguntar, responder, callarse— y pasa sus barreras antes de decir nada.
    """
    from chaski import servicio as interprete

    from servicio.flujo import entender_chanka
    try:
        oido = entender_chanka(await audio.read(), audio.filename or "turno.wav")
        r = interprete.turno(oido.get("texto", ""), "quy", "paciente", contexto,
                             json.dumps(oido.get("alternativas", []), ensure_ascii=False),
                             oido.get("confianza"),
                             dependencias=_dependencias(motor),
                             voz_fn=_voz_para_chaski)
        return _con_opciones(r, oido.get("alternativas"))
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/turno/enfermera")
def turno_enfermera(texto: str = Form(...), contexto: str = Form(""),
                    n_mejores: str = Form(""), confianza: str = Form(""),
                    traduccion_sembrada: str = Form(""), motor: str = Form("claude")):
    """La enfermera habla castellano. Mismo intérprete, mismas barreras.

    `motor` elige quién traduce. Por defecto **Claude** (D43): sobre los mismos
    conjuntos no daña ningún término fijo —NLLB dañaba 3 de 92— y lo que dice el
    paciente se lee mucho mejor de vuelta (qu→es 50.1 contra 24.7). El turno
    entero queda en ~8 s, que es espera aceptable cuando la consulta dura una
    hora.

    `motor=nllb` sigue disponible: es el modo sin conexión, y 483 ms contra
    5042. Lo que no cambia en ningún caso son las barreras ni el crítico.
    """
    from chaski import servicio as interprete
    try:
        return _con_opciones(
            interprete.turno(texto, "spa", "personal", contexto, n_mejores,
                             confianza, traduccion_sembrada,
                             dependencias=_dependencias(motor),
                             voz_fn=_voz_para_chaski))
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/turno/enfermera/vivo")
def turno_enfermera_vivo(texto: str = Form(...), contexto: str = Form(""),
                         n_mejores: str = Form(""), confianza: str = Form(""),
                         traduccion_sembrada: str = Form("")):
    """El mismo turno, en vivo: `decision` a los ~3 s, `resultado` al final.

    Sirve para que la app enseñe el castellano pulido mientras traduce y el
    crítico revisa. Lo que se DICE es solo `resultado`: `decision` es para
    mirar, no para hablar.
    """
    from fastapi.responses import StreamingResponse

    from chaski import servicio as interprete
    return StreamingResponse(
        _con_opciones_sse(
            interprete.turno_eventos(texto, "spa", "personal", contexto, n_mejores,
                                     confianza, traduccion_sembrada)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@aplicacion.get("/banco")
def banco(tag: str = ""):
    """Las frases verificadas. `revisado` dice cuáles puede decir la app."""
    from chaski import servicio as interprete
    try:
        return interprete.banco_por_tag(tag or None)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)



@aplicacion.post("/idioma")
async def idioma(audio: UploadFile = File(...)):
    """Solo detección de idioma, sin Claude: la app decide de qué lado va el turno.

    Reenvía al servicio de voz, que ya tiene `mms-lid-512` cargado. Son 49 ms de
    mediana, así que la app puede preguntarlo en cada turno en vez de alternar
    los lados a mano.
    """
    import httpx

    from servicio.flujo import INSTANCIA
    try:
        with httpx.Client(timeout=30) as cli:
            r = cli.post(f"{INSTANCIA}/idioma",
                         files={"audio": (audio.filename or "turno.wav",
                                          await audio.read(), "audio/wav")})
            return r.json()
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/resumen")
def resumen(turnos: str = Form(...), rol: str = Form("personal")):
    """F11: el resumen de la consulta, según quién lo lee (D27).

    `turnos` llega como JSON: [{lado, castellano, quechua, estado}], con estado en
    dicho · dicho_con_aviso · bloqueado · entendido · con_dudas. La regla que
    importa vive en `chaski.resumen`: lo que la auditoría bloqueó no puede salir
    como indicación, porque nunca se le dijo al paciente.
    """
    import anthropic

    from chaski.resumen import Turno, resumir, texto_para_decir
    try:
        r = resumir(anthropic.Anthropic(), [Turno(**t) for t in json.loads(turnos)], rol)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return {**r.model_dump(), "texto_para_decir": texto_para_decir(r)}


@aplicacion.post("/receta")
async def receta(imagen: UploadFile = File(...), contexto: str = Form(""),
                 dicho: str = Form("")):
    """Foto de una caja o receta → la pregunta de confirmación a la enfermera.

    Nada leído de una foto llega al paciente sin que la enfermera lo confirme:
    Chaski lee, pregunta «¿se lo digo?» y deja la indicación en
    `contexto.receta_pendiente`. El turno siguiente decide.
    """
    from chaski import servicio as interprete

    try:
        lectura = como_json(leer(await imagen.read(), dicho or None))
        return interprete.receta(lectura, contexto, voz_fn=_voz_para_chaski)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/medicamento")
async def medicamento(imagen: UploadFile = File(...), dicho: str = Form(""),
                      con_audio: bool = Form(True)):
    """Foto de una caja o receta -> qué es, para qué sirve, y Chaski diciéndolo en chanka.

    Es `/ver` + `/turno/enfermera` en una sola llamada, para que la app no tenga
    que encadenar tres peticiones desde el teléfono. Lo que se traduce y se dice
    es el «para qué sirve» más la indicación cuando la posología está; ambos
    pasan por la auditoría igual que cualquier otro texto.

    Si la posología no estaba escrita, `faltan` dice qué pedirle a la enfermera
    y no se dice ninguna dosis. Nunca se deduce una.
    """
    import base64

    from servicio.flujo import turno_de_la_enfermera

    try:
        lectura = como_json(leer(await imagen.read(), dicho_por_la_enfermera=dicho or None))
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)

    # Lo que se traduce y se dice es la receta corta: las mismas frases que el
    # paciente se lleva. Si no hay dosis escrita no hay receta, y entonces se
    # dice solo para qué sirve — nunca una dosis deducida.
    receta = lectura.get("receta_corta") or {}
    # Se dice la dosis, que es lo que la auditoria sabe revisar. El resto de la
    # receta se muestra: para que sirve y las advertencias de la caja no son
    # indicaciones, y pasarlas por la guarda de dosis solo produce bloqueos.
    if receta.get("dosis"):
        para_decir = " ".join(receta["dosis"])
    else:
        para_decir = (lectura.get("para_que_sirve") or "").strip()

    salida = {"lectura": lectura, "castellano": para_decir,
              "receta_corta": receta.get("lineas"),
              "se_dice_en_voz": receta.get("dosis"),
              "solo_se_muestra": receta.get("contexto") or [],
              "faltan": receta.get("faltan") or [],
              "por_que_sin_receta": receta.get("por_que")}
    if not para_decir:
        salida["error"] = "no se pudo leer nada seguro de la imagen"
        return salida

    try:
        turno = turno_de_la_enfermera(para_decir, modo_ensayo=True, rapido=True,
                                      con_audio=con_audio)
    except Exception as e:
        salida["error"] = f"{type(e).__name__}: {e}"
        return salida

    salida.update({
        "quechua": turno.get("quechua"),
        "retraduccion": turno.get("retraduccion"),
        "aprobado_por_auditoria": turno.get("aprobado_por_auditoria"),
        "motivo": turno.get("motivo"),
        "aviso": turno.get("aviso"),
        "se_dice": turno.get("se_dice"),
        "audio_wav_b64": turno.get("audio_wav_b64"),
        "ms": turno.get("total_ms"),
    })
    return salida


@aplicacion.get("/emergencia")
def emergencia(voz: str = "p24"):
    """Las frases de emergencia con la URL de su audio ya generado.

    Lo que le falta al banco de Freddy es el campo `audio`. Aquí va resuelto:
    las 24 frases están sintetizadas en las cinco voces y servidas como
    archivos, así que la app toca y suena, sin esperar a ningún modelo.
    """
    carpeta = AQUI.parent / "reports" / "emergencia"
    lista = carpeta / "frases.json"
    if not lista.exists():
        return JSONResponse({"error": "todavía no se generaron"}, status_code=404)
    frases = json.loads(lista.read_text(encoding="utf-8"))
    disponibles = sorted(d.name for d in carpeta.iterdir() if d.is_dir())
    elegida = voz if voz in disponibles else "base"
    for f in frases:
        f["audio"] = f"/emergencia/audio/{elegida}/{f['id']}.mp3"
    return {"voz": elegida, "voces": disponibles, "frases": frases}


@aplicacion.get("/emergencia/audio/{voz}/{nombre}")
def emergencia_audio(voz: str, nombre: str):
    ruta = (AQUI.parent / "reports" / "emergencia" / voz / nombre).resolve()
    raiz = (AQUI.parent / "reports" / "emergencia").resolve()
    # Que el nombre pedido no se salga de la carpeta.
    if raiz not in ruta.parents or not ruta.exists():
        return JSONResponse({"error": "no existe"}, status_code=404)
    return FileResponse(ruta, media_type="audio/mpeg")


@aplicacion.get("/voces")
def voces():
    """Las voces de Chaski que se pueden pedir. Reenvía al servicio de voz."""
    import httpx

    from servicio.flujo import INSTANCIA
    try:
        with httpx.Client(timeout=20) as cli:
            return cli.get(f"{INSTANCIA}/voces").json()
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.get("/corregir")
def pagina_corregir():
    return FileResponse(AQUI / "static" / "corregir.html")


@aplicacion.get("/corpus/personas")
def corpus_personas():
    from servicio.corpus import personas
    return {"personas": personas()}


@aplicacion.get("/corpus/clips")
def corpus_clips(persona: str):
    from servicio.corpus import clips
    return {"clips": clips(persona)}


@aplicacion.get("/corpus/audio")
def corpus_audio(ruta: str):
    p = Path(ruta)
    return FileResponse(p) if p.exists() else JSONResponse({"error": "no existe"}, 404)


@aplicacion.post("/corpus/subir")
async def corpus_subir(audio: UploadFile = File(...), persona: str = Form(...),
                       bloque: str = Form("A"), esperadas: int = Form(0)):
    """Nota de voz larga -> clips numerados listos para corregir."""
    from servicio.corpus import recibir_nota
    try:
        return recibir_nota(persona, bloque, await audio.read(), audio.filename or "nota.ogg",
                            esperadas=esperadas)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/transcribir")
def corpus_transcribir(ruta: str = Form(...)):
    from servicio.corpus import transcribir
    try:
        return transcribir(ruta)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/codigo")
def corpus_codigo(ruta: str = Form(...)):
    """Detecta el identificador (C1, M5...) oyendo el principio del clip."""
    from servicio.corpus import detectar_codigo
    try:
        return detectar_codigo(ruta)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/recodificar")
def corpus_recodificar(persona: str = Form(...), bloque_actual: str = Form(...),
                       numero_actual: int = Form(...), bloque_nuevo: str = Form(...),
                       numero_nuevo: int = Form(...)):
    from servicio.corpus import recodificar
    try:
        return recodificar(persona, numero_actual, bloque_actual, bloque_nuevo, numero_nuevo)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/importar")
def corpus_importar(origen: str = Form(...), persona: str = Form("")):
    """Trae al corpus el export del formulario (archivo o URL)."""
    from voz.importar_formulario import importar
    try:
        return importar(origen, persona)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/verificar")
def corpus_verificar(ruta: str = Form(...), escrito: str = Form("")):
    from servicio.corpus import verificar
    try:
        return verificar(ruta, escrito)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/ajustar")
def corpus_ajustar(persona: str = Form(...), bloque: str = Form(...), numero: int = Form(...),
                   inicio: float = Form(None), fin: float = Form(None)):
    from servicio.corpus import ajustar
    try:
        return ajustar(persona, bloque, numero, inicio, fin)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/partir")
def corpus_partir(persona: str = Form(...), bloque: str = Form(...), numero: int = Form(...),
                  en_segundo: float = Form(...)):
    from servicio.corpus import partir
    try:
        return partir(persona, bloque, numero, en_segundo)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/unir")
def corpus_unir(persona: str = Form(...), bloque: str = Form(...), numero: int = Form(...)):
    from servicio.corpus import unir
    try:
        return unir(persona, bloque, numero)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/guardar")
def corpus_guardar(persona: str = Form(...), numero: int = Form(...),
                   transcripcion: str = Form(""), consentimiento: bool = Form(True),
                   descartar: bool = Form(False)):
    from servicio.corpus import guardar
    try:
        return guardar(persona, numero, transcripcion, consentimiento, descartar)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/corpus/exportar")
def corpus_exportar(persona: str = Form("")):
    from servicio.corpus import exportar
    return exportar(persona or None)


@aplicacion.post("/voz")
def ruta_voz(texto: str = Form(...), voz: str = Form("")):
    """Solo la voz, para pedirla DESPUÉS de mostrar el texto."""
    from servicio.flujo import decir_en_voz
    try:
        audio, ms = decir_en_voz(texto, voz or os.environ.get("CHASKI_VOZ_QUY", "mama_freddy"))
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return Response(content=audio, media_type="audio/wav", headers={"X-Ms": str(ms)})


@aplicacion.post("/mt")
def mt(texto: str = Form(...), desde: str = Form("spa_Latn"),
       hacia: str = Form("quy_Latn")):
    """Traducción local con NLLB-1.3B, sin Claude y sin salir a internet.

    Medido sobre las 62 frases que tradujeron las familias el 24-oct, que
    ningún modelo publicado ha visto:

    | motor | chrF++ | una petición |
    |---|---|---|
    | claude-sonnet-5 | 44.55 | 1496 ms |
    | **nllb-1.3B** | **34.72** | **565 ms** |
    | nllb-600M | 28.58 | 346 ms |

    Claude traduce mejor; NLLB responde antes y no depende de la red. Esta ruta
    es la rápida; `/traducir` sigue siendo la de Claude con auditoría.

    Funciona en las dos direcciones: `desde`/`hacia` son códigos de NLLB
    (`spa_Latn`, `quy_Latn`).
    """
    import httpx

    from servicio.flujo import INSTANCIA
    try:
        with httpx.Client(timeout=120) as cli:
            return cli.post(f"{INSTANCIA}/traducir",
                            data={"texto": texto, "desde": desde, "hacia": hacia}).json()
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/traducir")
def traducir(texto: str = Form(...)):
    """Castellano -> chanka, con la auditoria de retraduccion de Freddy.

    No traduce Haiku: traduce `chaski.auditoria`, que usa Opus 5 con glosario,
    retraduce A CIEGAS y compara los datos criticos con codigo. Si algo cambio,
    `enviar` viene en false y NO se dice en voz alta.
    """
    if not HAY_TRADUCTOR:
        return JSONResponse({"error": f"falta el modulo de Freddy: {_FALLO_TRADUCTOR}"},
                            status_code=503)
    t0 = time.perf_counter()
    try:
        r = auditar(anthropic.Anthropic(), texto)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return {"quechua": r.quechua, "retraduccion": r.retraduccion, "enviar": r.enviar,
            "motivo": r.motivo, "terminos_inseguros": r.terminos_inseguros,
            "diferencias": [d.model_dump() for d in r.diferencias],
            "segundos": round(time.perf_counter() - t0, 2)}


@aplicacion.post("/ver")
async def ver(imagen: UploadFile = File(...), dicho: str = Form(""),
              modelo: str = Form("")):
    datos = await imagen.read()
    try:
        lectura = leer(datos, dicho_por_la_enfermera=dicho or None, modelo=modelo or MODELO)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)
    return como_json(lectura)
