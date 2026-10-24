"""La misma auditoría de Freddy, pero sin tiempos muertos.

Reusa SUS prompts y SUS modelos de datos: aquí solo cambia la orquestación.

Lo que costaba 30 s eran cuatro llamadas a Opus 5 en fila. Dos cosas lo bajan:

1. **Paralelo.** Sacar los hechos del original y traducir NO dependen una de la
   otra: salen juntas. La cadena real es  max(hechos, traducir) + retraducir +
   hechos_de_la_retraduccion, o sea tres pasos en vez de cuatro.
2. **Cada llamada con el modelo que le corresponde.** Traducir a chanka es la
   unica que pide calidad. Sacar hechos de un texto y retraducir son mecanicas:
   las hace Haiku en una fraccion del tiempo.

La comparación y la decisión ya eran código puro y no cuestan nada.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import anthropic
from chaski import auditoria as A
from chaski.hechos import comparar

MODELO_TRADUCCION = "claude-sonnet-5"   # la unica que necesita calidad
MODELO_MECANICO = "claude-haiku-4-5"    # extraer hechos y retraducir
MODELO_ARBITRO = "claude-opus-5"        # solo cuando el primer intento bloquea


def _parse(cliente, sistema: str, contenido: str, formato, modelo: str,
           cachear: bool = False):
    """Igual que `chaski.auditoria._parse`, pero el modelo es un argumento.

    `cachear` marca el sistema como prefijo estable: el glosario viaja ahí y no
    se vuelve a procesar en cada llamada.
    """
    bloques = [{"type": "text", "text": sistema}]
    if cachear:
        bloques[0]["cache_control"] = {"type": "ephemeral"}
    r = cliente.messages.parse(model=modelo, max_tokens=4000, system=bloques,
                               messages=[{"role": "user", "content": contenido}],
                               output_format=formato)
    if r.stop_reason == "refusal" or r.parsed_output is None:
        raise A.SinRespuesta(f"stop_reason={r.stop_reason}")
    return r.parsed_output


def auditar_rapido(texto_es: str, glosario: list[dict] | None = None,
                   modelo_traduccion: str = MODELO_TRADUCCION,
                   modelo_mecanico: str = MODELO_MECANICO) -> dict:
    glosario = A.cargar_glosario() if glosario is None else glosario
    cliente = anthropic.Anthropic()
    tiempos = {}

    # El glosario va en el SISTEMA, no en el mensaje: así es prefijo estable y
    # se cachea entre llamadas en vez de reenviarse y reprocesarse cada vez.
    sistema_traducir = A.SISTEMA_TRADUCIR
    if glosario:
        lineas = "\n".join(f"- {g['castellano']} → {g['quechua']}" for g in glosario)
        sistema_traducir = (f"{A.SISTEMA_TRADUCIR}\n\nGlosario revisado por una hablante "
                            f"nativa:\n{lineas}")
    contenido_traduccion = texto_es

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuro_hechos = pool.submit(_parse, cliente, A.SISTEMA_EXTRAER, texto_es,
                                    A.Hechos, modelo_mecanico)
        futuro_traduccion = pool.submit(_parse, cliente, sistema_traducir,
                                        contenido_traduccion, A.Traduccion,
                                        modelo_traduccion, True)
        hechos_original = futuro_hechos.result()
        traduccion = futuro_traduccion.result()
    tiempos["paralelo_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    retraduccion = _parse(cliente, A.SISTEMA_RETRADUCIR, traduccion.quechua,
                          A.Retraduccion, modelo_mecanico)
    tiempos["retraducir_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    hechos_retraducido = _parse(cliente, A.SISTEMA_EXTRAER, retraduccion.castellano,
                                A.Hechos, modelo_mecanico)
    tiempos["hechos_retraduccion_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    diferencias = comparar(hechos_original, hechos_retraducido)
    enviar, motivo, aviso = decidir_separando(diferencias, traduccion.terminos_inseguros,
                                              retraduccion.castellano, texto_es)

    return {"quechua": traduccion.quechua, "retraduccion": retraduccion.castellano,
            "enviar": enviar, "motivo": motivo, "aviso": aviso,
            "terminos_inseguros": traduccion.terminos_inseguros,
            "diferencias": [d.model_dump() for d in diferencias],
            "modelos": {"traduccion": modelo_traduccion, "mecanico": modelo_mecanico},
            "tiempos": tiempos,
            "total_ms": round(sum(tiempos.values()), 1)}


# NOTA (24-oct): aqui habia una normalizacion de sinonimos propia. Sobra:
# Freddy la puso en `chaski.hechos` el mismo dia, y la suya es mejor porque
# ademas empareja por orden cuando el nombre es generico («tome una pastilla»
# no dice cual). Se usa `comparar` tal cual.


DIAS = ("lunes", "martes", "miércoles", "miercoles", "jueves", "viernes",
        "sábado", "sabado", "domingo")


def artefacto_de_dia(diferencia, texto_es: str, retraduccion: str) -> bool:
    """¿La diferencia es del extractor, no de la traducción?

    Caso medido el 24-oct:

        original     : Su control es el lunes
        chanka       : Controlniykiqa lunesmi kanqa.
        retraducción : Tu control será el lunes.
        DIFF proxima_cita_en_dias: None -> 3

    La traducción es correcta y dice exactamente el mismo día. Lo que cambió es
    que el extractor convirtió «lunes» en un número de días en la vuelta y no en
    la ida. Nadie puede sacar un número de días de un nombre de día sin saber la
    fecha de hoy, así que ese número es ruido, no un dato distinto.

    La regla es estrecha a propósito: solo `proxima_cita_en_dias`, y solo cuando
    los dos textos nombran el mismo día de la semana. Si el quechua perdiera el
    día, los dos textos ya no coincidirían y volvería a bloquear.
    """
    if diferencia.campo != "proxima_cita_en_dias":
        return False
    a, b = texto_es.lower(), retraduccion.lower()
    return any(d in a and d in b for d in DIAS)


def decidir_separando(diferencias, terminos_inseguros, retraduccion, texto_es=""):
    """Separa lo que bloquea de lo que solo avisa.

    La medicion del 24-oct mostro dos cosas:

    1. La regla original bloquea 8 de cada 9 frases, casi siempre por
       «terminos sin traduccion segura». Palabras como «posta», «tableta» o
       «en ayunas» salen en cada frase de una posta: si cada una bloquea, el
       sistema se calla siempre y la enfermera deja de hacerle caso.
    2. Ese motivo NO es reproducible. La misma frase, tres corridas seguidas,
       dio True, True, False. Es una opinion del modelo, y varia.

    La comparacion de datos criticos —dosis, horas, fechas— la hace CODIGO sobre
    la retraduccion, es estable y es la que puede hacer dano. Esa bloquea.
    Los terminos inseguros pasan a aviso: se muestran, no callan al sistema.
    """
    reales = [d for d in diferencias if not artefacto_de_dia(d, texto_es, retraduccion)]
    if reales:
        return False, f"cambió un dato crítico: {', '.join(d.campo for d in reales)}", None
    if A.MARCA_NO_ENTIENDO in retraduccion:
        return False, "la retraducción no entiende una parte del quechua", None
    if terminos_inseguros:
        return True, "los datos críticos coinciden", (
            "términos sin traducción segura: " + ", ".join(terminos_inseguros) +
            " — se dice igual, pero la enfermera debería revisarlos")
    return True, "los datos críticos coinciden", None


def auditar_con_arbitro(texto_es: str, glosario: list[dict] | None = None) -> dict:
    """Rapido por defecto, caro solo cuando hace falta.

    Primer intento con los modelos ligeros. Si bloquea por un dato critico, se
    repite con Opus traduciendo antes de callar al sistema: bloquear es la
    decision cara de equivocar, y es la que menos veces ocurre, asi que pagar
    el modelo grande solo ahi sale casi gratis en promedio.
    """
    primero = auditar_rapido(texto_es, glosario)
    if primero["enviar"]:
        primero["arbitro"] = None
        return primero

    segundo = auditar_rapido(texto_es, glosario, modelo_traduccion=MODELO_ARBITRO)
    segundo["arbitro"] = {"primer_intento": primero["motivo"],
                          "confirmado": not segundo["enviar"],
                          "ms_primer_intento": primero["total_ms"]}
    segundo["total_ms"] = round(primero["total_ms"] + segundo["total_ms"], 1)
    return segundo
