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
from rimay import auditoria as A
from rimay.hechos import comparar

MODELO_TRADUCCION = "claude-sonnet-5"   # la unica que necesita calidad
MODELO_MECANICO = "claude-haiku-4-5"    # extraer hechos y retraducir


def _parse(cliente, sistema: str, contenido: str, formato, modelo: str,
           cachear: bool = False):
    """Igual que `rimay.auditoria._parse`, pero el modelo es un argumento.

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
    enviar, motivo = A.decidir(diferencias, traduccion.terminos_inseguros,
                               retraduccion.castellano)

    return {"quechua": traduccion.quechua, "retraduccion": retraduccion.castellano,
            "enviar": enviar, "motivo": motivo,
            "terminos_inseguros": traduccion.terminos_inseguros,
            "diferencias": [d.model_dump() for d in diferencias],
            "modelos": {"traduccion": modelo_traduccion, "mecanico": modelo_mecanico},
            "tiempos": tiempos,
            "total_ms": round(sum(tiempos.values()), 1)}
