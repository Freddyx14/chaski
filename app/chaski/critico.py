"""The critic: a separate, fast model that checks a Quechua output before Chaski speaks it.

The translator and the critic are different roles. The critic never writes what the patient
hears; it only extracts, and plain code decides (chaski.hechos.comparar, chaski.guardas). It runs
on Sonnet by default (CHASKI_MODELO_CRITICO): Anthropic's workshop suggested Haiku for speed, but on the shared
attack sample Sonnet caught 160/160 with 7.5 % false blocks vs Haiku's 96 % / 18 %. The model is a parameter.

Calls per output, all with the critic model:
  1. facts of the Spanish original                       (extraer_hechos)
  2. blind back-translation of the Quechua               (retraducir_ciego; never sees the original)
  3. facts of the back-translation                       (extraer_hechos)
  4. what the back-translation says that the original
     does not: advice, diagnosis, addressee              (detectar_agregados)

Then code: B5 `comparar` + `auditoria.decidir`, B4 `terminos_fijos`, and `sin_agregados`.
Reuses the system prompts of chaski.auditoria so the two paths cannot drift apart.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import anthropic
from pydantic import BaseModel

from chaski import auditoria
from chaski.auditoria import Retraduccion, SinRespuesta
from chaski.guardas import (Agregados, Veredicto, bloqueo, fail_closed, pasa, pulido_conserva_hechos,
                            pulido_sin_terminos_nuevos, sin_agregados, terminos_fijos)
from chaski.hechos import Hechos, comparar

# One default for the product and the evals (they once disagreed and a run measured Haiku by accident, 24-oct).
# Sonnet won on the shared sample: 160/160 caught, 7.5 % false blocks, vs Haiku 96 % / 18 %.
MODELO_CRITICO = os.environ.get("CHASKI_MODELO_CRITICO", "claude-sonnet-5")

SISTEMA_AGREGADOS = (
    "Comparas dos textos en castellano de una posta de salud del Perú: el ORIGINAL que dijo el personal y la "
    "VERSIÓN que va a escuchar el paciente. Tu único trabajo es listar lo que la VERSIÓN dice y el ORIGINAL no: "
    "consejos o advertencias nuevos, y diagnósticos o enfermedades nuevos. Decir lo mismo con otras palabras no "
    "cuenta. Además indica a quién se dirige cada texto. No juzgues si la versión es buena; solo lista."
)


class ResultadoCritico(BaseModel):
    veredicto: Veredicto
    modelo: str
    llamadas: int
    hechos_original: Hechos | None = None
    retraduccion: str | None = None
    hechos_retraducido: Hechos | None = None
    agregados: Agregados | None = None
    pulido: ResultadoCritico | None = None  # set by `revisar` when it also checked the polish


def _parse(client, modelo: str, sistema: str, contenido: str, formato: type[BaseModel]):
    respuesta = client.messages.parse(
        model=modelo,
        max_tokens=4000,
        system=sistema,
        messages=[{"role": "user", "content": contenido}],
        output_format=formato,
    )
    if respuesta.stop_reason == "refusal" or respuesta.parsed_output is None:
        raise SinRespuesta(f"stop_reason={respuesta.stop_reason}")
    return respuesta.parsed_output


def extraer_hechos(client: anthropic.Anthropic, texto_es: str, modelo: str = MODELO_CRITICO) -> Hechos:
    return _parse(client, modelo, auditoria.SISTEMA_EXTRAER, texto_es, Hechos)


def retraducir_ciego(client: anthropic.Anthropic, quechua: str, modelo: str = MODELO_CRITICO) -> Retraduccion:
    return _parse(client, modelo, auditoria.SISTEMA_RETRADUCIR, quechua, Retraduccion)


def detectar_agregados(client: anthropic.Anthropic, original_es: str, version_es: str,
                       modelo: str = MODELO_CRITICO) -> Agregados:
    contenido = f"ORIGINAL:\n{original_es}\n\nVERSIÓN:\n{version_es}"
    return _parse(client, modelo, SISTEMA_AGREGADOS, contenido, Agregados)


def criticar(client: anthropic.Anthropic, texto_es: str, quechua: str, modelo: str = MODELO_CRITICO) -> ResultadoCritico:
    """Run the critic on one Spanish → Quechua output. Fails closed: any error is a block."""
    r = ResultadoCritico(veredicto=bloqueo("crítico", "no pude verificar"), modelo=modelo, llamadas=0)
    try:
        r.hechos_original = extraer_hechos(client, texto_es, modelo)
        r.llamadas += 1
        retr = retraducir_ciego(client, quechua, modelo)
        r.llamadas += 1
        r.retraduccion = retr.castellano
        r.hechos_retraducido = extraer_hechos(client, retr.castellano, modelo)
        r.llamadas += 1
        r.agregados = detectar_agregados(client, texto_es, retr.castellano, modelo)
        r.llamadas += 1
    except Exception as e:  # noqa: BLE001 — fail closed
        r.veredicto = bloqueo("crítico", "no pude verificar", [f"{type(e).__name__}: {e}"])
        return r
    r.veredicto = decidir_critico(texto_es, quechua, r.hechos_original, r.retraduccion,
                                  r.hechos_retraducido, r.agregados)
    return r


@fail_closed
def decidir_critico(texto_es: str, quechua: str, hechos_original: Hechos, retraduccion: str,
                    hechos_retraducido: Hechos, agregados: Agregados) -> Veredicto:
    """Pure code over what the critic extracted. The first layer that blocks gives the reason."""
    enviar, motivo = auditoria.decidir(comparar(hechos_original, hechos_retraducido), [], retraduccion)
    if not enviar:
        return bloqueo("B5 ida y vuelta", motivo)
    for v in (terminos_fijos(texto_es, quechua, hechos_original), sin_agregados(agregados)):
        if not v.ok:
            return v
    return pasa("crítico")


def criticar_pulido(client: anthropic.Anthropic, transcripcion: str, pulido: str,
                    modelo: str = MODELO_CRITICO) -> ResultadoCritico:
    """B2/B3 on the polish of one turn: facts of both sides, what the polish added, then code."""
    r = ResultadoCritico(veredicto=bloqueo("crítico", "no pude verificar"), modelo=modelo, llamadas=0)
    try:
        r.hechos_original = extraer_hechos(client, transcripcion, modelo)
        r.llamadas += 1
        r.hechos_retraducido = extraer_hechos(client, pulido, modelo)
        r.llamadas += 1
        r.agregados = detectar_agregados(client, transcripcion, pulido, modelo)
        r.llamadas += 1
    except Exception as e:  # noqa: BLE001 — fail closed
        r.veredicto = bloqueo("crítico", "no pude verificar", [f"{type(e).__name__}: {e}"])
        return r
    r.veredicto = decidir_pulido(transcripcion, pulido, r.hechos_original, r.hechos_retraducido, r.agregados)
    return r


@fail_closed
def decidir_pulido(transcripcion: str, pulido: str, hechos_transcripcion: Hechos, hechos_pulido: Hechos,
                   agregados: Agregados) -> Veredicto:
    for v in (pulido_sin_terminos_nuevos(transcripcion, pulido),
              pulido_conserva_hechos(hechos_transcripcion, hechos_pulido),
              sin_agregados(agregados)):
        if not v.ok:
            return v
    return pasa("crítico pulido")


def revisar(client: anthropic.Anthropic, texto_es: str, *, quechua: str | None = None,
            transcripcion: str | None = None, modelo: str = MODELO_CRITICO) -> ResultadoCritico:
    """THE critic path. `evals/ataques/correr.py --modo chaski` and the orchestrator both call this, so what was
    measured is literally what runs in the product.

      quechua        → `criticar(texto_es, quechua)`: blind back-translation, facts, B4/B5, added content (C)
      transcripcion  → `criticar_pulido(transcripcion, texto_es)`: B2/B3 on the polish (skipped when identical)

    When both apply they run in parallel and the polish verdict is reported first (it is upstream). With neither,
    there is nothing a model can check: it passes and the code guards are all that ran.
    """
    con_pulido = transcripcion is not None and transcripcion.strip() != texto_es.strip()
    if not con_pulido and quechua is None:
        return ResultadoCritico(veredicto=pasa("crítico: nada que retraducir"), modelo=modelo, llamadas=0)
    if not con_pulido:
        return criticar(client, texto_es, quechua, modelo)
    if quechua is None:
        return criticar_pulido(client, transcripcion, texto_es, modelo)
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_pulido = pool.submit(criticar_pulido, client, transcripcion, texto_es, modelo)
        f_traduccion = pool.submit(criticar, client, texto_es, quechua, modelo)
        r_pulido, r_traduccion = f_pulido.result(), f_traduccion.result()
    r = r_traduccion.model_copy(update={"llamadas": r_pulido.llamadas + r_traduccion.llamadas, "pulido": r_pulido})
    if not r_pulido.veredicto.ok:
        r.veredicto = r_pulido.veredicto
    return r


# Calls each path makes, for the cost estimate in evals/ataques/correr.py.
LLAMADAS_TRADUCCION = 4
LLAMADAS_PULIDO = 3
