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
    from servicio.flujo import decir_en_voz
    audio, _ = decir_en_voz(texto, voz="p24" if idioma == "quy" else "base")
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
        return interprete.turno(oido.get("texto", ""), "quy", "paciente", contexto,
                                json.dumps(oido.get("alternativas", []), ensure_ascii=False),
                                oido.get("confianza"),
                                dependencias=_dependencias(motor),
                                voz_fn=_voz_para_chaski)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@aplicacion.post("/turno/enfermera")
def turno_enfermera(texto: str = Form(...), contexto: str = Form(""),
                    n_mejores: str = Form(""), confianza: str = Form(""),
                    traduccion_sembrada: str = Form(""), motor: str = Form("claude")):
    """La enfermera habla castellano. Mismo intérprete, mismas barreras.

    `motor` elige quién traduce. Por defecto **Claude** (D40): sobre los mismos
    conjuntos no daña ningún término fijo —NLLB dañaba 3 de 92— y lo que dice el
    paciente se lee mucho mejor de vuelta (qu→es 50.1 contra 24.7). El turno
    entero queda en ~8 s, que es espera aceptable cuando la consulta dura una
    hora.

    `motor=nllb` sigue disponible: es el modo sin conexión, y 483 ms contra
    5042. Lo que no cambia en ningún caso son las barreras ni el crítico.
    """
    from chaski import servicio as interprete
    try:
        return interprete.turno(texto, "spa", "personal", contexto, n_mejores,
                                confianza, traduccion_sembrada,
                                dependencias=_dependencias(motor),
                                voz_fn=_voz_para_chaski)
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
        interprete.turno_eventos(texto, "spa", "personal", contexto, n_mejores,
                                 confianza, traduccion_sembrada),
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

    partes = [lectura.get("para_que_sirve") or ""]
    if lectura.get("indicacion"):
        partes.append(lectura["indicacion"])
    para_decir = " ".join(p for p in partes if p).strip()

    salida = {"lectura": lectura, "castellano": para_decir}
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
def ruta_voz(texto: str = Form(...), voz: str = Form("p24")):
    """Solo la voz, para pedirla DESPUÉS de mostrar el texto."""
    from servicio.flujo import decir_en_voz
    try:
        audio, ms = decir_en_voz(texto, voz)
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
