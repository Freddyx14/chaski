"""One interpreter turn end to end (plan/arquitectura-interprete.md §2 and §2b).

    decide ─► usar_frase_banco: the verified bank item, nothing generated
          └► translate the polished text ─► guards ─► critic ─► dicho | dicho_con_aviso | bloqueado

Two model roles and no more (§7a): the MAIN interpreter (`decidir`) and the CRITIC (`auditar_fn`), which checks the
final output invented no data and says nothing it shouldn't. The translator is an engine (NLLB or Claude), not an
agent. Every step is an injected callable, so the service wires the real ones (`dependencias`) and tests wire fakes:

    traducir_fn(texto, de, a)    -> TextoTraducido | str        chaski.traducir.traducir
    guardas_fn(EntradaRevision)  -> Veredicto                   `guardas` below: B1, B2/B3 in code, B4 (chaski.guardas)
    auditar_fn(EntradaRevision)  -> Veredicto                   `auditor(client)`: chaski.critico.revisar, the SAME
                                                                function evals/ataques/correr.py --modo chaski measures
    banco_fn(frase_id)           -> {"id","es","quy","audio"}   `frase_servible`: reviewed bank items only
    candidatos_fn(texto_es)      -> [{"id","es"}]               `candidatos_servibles`: bank candidates for `decidir`

Models come from the environment so they can be switched without code: CHASKI_MODELO_PRINCIPAL (default
claude-opus-5) and CHASKI_MODELO_CRITICO (default claude-sonnet-5, the critic measured at 160/160 caught).

Fail closed: any exception, in any step, gives `bloqueado` with «no pude verificar esto». A blocked turn is never
said to the patient; the staff sees why.
"""
from __future__ import annotations

import base64
import os
import re
import time
import unicodedata
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Literal

import anthropic
from pydantic import BaseModel, Field

from chaski import critico, memoria, guardas as g
from chaski.interprete import NO_ENTENDI, Accion, Contexto, Decision, Idioma, Rol, TurnoEntrada, decidir
from chaski.traducir import Motor, TextoTraducido, traducir

Estado = Literal["dicho", "dicho_con_aviso", "bloqueado"]
NO_PUDE = "No pude verificar esto"

ENV_MODELO_PRINCIPAL = "CHASKI_MODELO_PRINCIPAL"
ENV_MODELO_CRITICO = "CHASKI_MODELO_CRITICO"
MODELO_PRINCIPAL = "claude-opus-5"
MODELO_CRITICO = "claude-sonnet-5"
UMBRAL_OIDO = 0.6  # B1: below this ASR confidence, a critical token (number, medicine, body part) blocks


def modelo_principal_env() -> str:
    return os.environ.get(ENV_MODELO_PRINCIPAL, "").strip() or MODELO_PRINCIPAL


def modelo_critico_env() -> str:
    return os.environ.get(ENV_MODELO_CRITICO, "").strip() or MODELO_CRITICO


class Veredicto(BaseModel):
    """What the guard layer or the critic says about a message, as the turn consumes it."""
    ok: bool
    motivo: str = ""
    aviso: str | None = Field(default=None, description="Passes, but the staff should see this (amber)")
    usar_literal: bool = Field(default=False, description="B2: the polish changed a fact; retry with the literal transcript")


class EntradaRevision(BaseModel):
    """Everything a guard or the critic needs to judge one outgoing message."""
    accion: Accion
    original: str = Field(description="The transcript as heard")
    fuente: str = Field(description="Everything Chaski may draw facts from: transcript (+ history for responder)")
    pulido: str = Field(description="What Chaski is about to say, before translation")
    traduccion: str = Field(description="What will actually be said (== pulido when no translation was needed)")
    de: Idioma
    a: Idioma
    confianza: float | None = None
    n_mejores: list[str] = Field(default_factory=list)


EntradaGuardas = EntradaRevision  # same payload; the name the guards module may import


class Resultado(BaseModel):
    """What `/turno/*` returns to the app."""
    estado: Estado
    accion: Accion | None
    motivo: str
    dato_faltante: str | None = None
    frase_banco_id: str | None = None
    para: Rol
    idioma_salida: Idioma
    texto_original: str = Field(default="", description="What was heard (the transcript) for this turn")
    texto_pulido: str = ""
    texto_salida: str = Field(default="", description="What is said, in idioma_salida. Empty when bloqueado")
    audio: str | None = Field(default=None, description="Verified bank audio URL, when accion == usar_frase_banco")
    audio_wav_b64: str | None = Field(default=None, description="Generated voice of texto_salida (when the service "
                                                                 "passes voz_fn); only set when every check passed")
    anticipada: bool = Field(default=False, description="The translation started during the decision and passed")
    aviso: str | None = None
    motor: Motor | None = Field(default=None, description="Translation engine actually used")
    respaldo: bool = False
    sembrada: bool = Field(default=False, description="Rehearsal: the translation was seeded by the app, not produced "
                                                       "by the translator. A block here is the demo, not a real error")
    modelos: dict[str, str | None] = Field(default_factory=dict, description="{principal, critico} that ran this turn")
    paso_fallido: str | None = None
    ms: dict[str, float] = Field(default_factory=dict, description="Per step: decidir, traducir, guardas, critico, total")
    contexto: Contexto


TraducirFn = Callable[[str, Idioma, Idioma], "TextoTraducido | str"]
RevisarFn = Callable[[EntradaRevision], Veredicto]
BancoFn = Callable[[str], "dict | None"]
CandidatosFn = Callable[[str], list]
VozFn = Callable[[str, Idioma], bytes]  # text, language -> wav bytes

_hilos = ThreadPoolExecutor(max_workers=8, thread_name_prefix="chaski")


def _en_fondo(fn, *args) -> None:
    """Fire and forget: the memory never adds time to a turn, and an error in it never reaches one."""
    def correr():
        try:
            fn(*args)
        except Exception:  # noqa: BLE001
            pass
    _hilos.submit(correr)


# ── A block asks before it gives up (Freddy, 25-oct 02:23) ──────────────────────────────────────────────────────
# When a check stops a translation, Chaski first asks the speaker to say it again, naming the data that failed, once.
# Nothing doubtful reaches the listener: the question goes back to whoever spoke. A second block in a row, a rehearsal
# (the barrier demo) or a failure that is not a check (network, model) still ends in the plain block.

CONFIRMAR = "confirmar"
_CAMPOS = [  # (substring of the guard/critic reason, field id, how it is said to the staff)
    ("dosis", "dosis", "la dosis"), ("cada_horas", "frecuencia", "cada cuánto se toma"),
    ("frecuencia", "frecuencia", "cada cuánto se toma"), ("dias", "duracion", "por cuántos días"),
    ("duracion", "duracion", "por cuántos días"), ("negaci", "otro", "si es un «no»"),
    ("vehiculo", "otro", "con qué se toma"), ("unidad", "dosis", "la unidad"),
    ("medicamento", "medicamento", "el medicamento"), ("concentracion", "dosis", "la concentración"),
    ("momento", "otro", "cuándo se toma"), ("ayunas", "otro", "si es en ayunas"),
    ("embarazo", "embarazo", "lo del embarazo"), ("alergia", "alergia", "la alergia"),
    ("partes_cuerpo", "parte_del_cuerpo", "la parte del cuerpo"), ("consejo", "otro", "un consejo que no se dijo"),
    ("diagn", "otro", "un diagnóstico que no se dijo"),
    ("número", "dosis", "un número"), ("numero", "dosis", "un número"),  # B4 says «número N…» (audit L1)
    ("con agua", "otro", "con qué se toma"),
]


def _campo(motivo: str) -> tuple[str, str]:
    m = (motivo or "").lower()
    for clave, campo, llano in _CAMPOS:
        if clave in m:
            return campo, llano
    return "otro", "un dato"


def repreguntar_al_bloquear_env() -> bool:
    return os.environ.get("CHASKI_REPREGUNTAR_AL_BLOQUEAR", "1").strip() not in ("0", "no", "false", "")


def _pregunta_de_confirmacion(turno, ya_pidio_repetir: bool, motivo: str, paso: str, sembrada: bool):
    """(para, idioma, texto) of the question back, or None to keep the plain block."""
    if (sembrada or not repreguntar_al_bloquear_env() or paso not in ("guardas", "critico") or ya_pidio_repetir):
        return None
    if turno.rol == "personal":
        return ("personal", "spa", f"No quiero decir un dato equivocado: {_campo(motivo)[1]}. ¿Me lo repite, por favor?")
    return ("paciente", "quy", NO_ENTENDI["quy"])


def anticipar_env() -> bool:
    """CHASKI_TRADUCIR_ANTICIPADO: start translating the transcript while the interpreter decides (1/0)."""
    return os.environ.get("CHASKI_TRADUCIR_ANTICIPADO", "1").strip() not in ("0", "no", "false", "")


def _de_guardas(v: g.Veredicto, **extra) -> Veredicto:
    return Veredicto(ok=v.ok, motivo=f"{v.capa}: {v.motivo}" if not v.ok else v.capa, **extra)


# ── Guards (pure code, chaski.guardas) ────────────────────────────────────────────────────────────────────────

def guardas(e: EntradaRevision) -> Veredicto:
    """B1, B2/B3 in code and B4 on one outgoing message. No model call. The first layer that blocks wins.

    B1   only when the recogniser gave a confidence: it applies to every word of the transcript (no per-word scores).
    B2/B3 on a Spanish `traducir`: a block asks the turn to retry with the literal transcript (§2b). On Chaski's own
         words (repreguntar/responder) it checks nothing new was brought in versus the source; the negation rule is
         skipped there because a question or an answer legitimately drops the source's «no».
    B4   on whatever crosses languages: Spanish→Quechua checks the polish against the translation; Quechua→Spanish
         checks the translation against what the patient was heard saying.
    """
    if e.confianza is not None and e.original.strip():
        v = g.oido_confiable([{"texto": w, "confianza": e.confianza} for w in e.original.split()], UMBRAL_OIDO)
        if not v.ok:
            return _de_guardas(v)

    if e.accion == "traducir" and e.de == "spa":
        v = g.pulido_sin_terminos_nuevos(e.original, e.pulido)
        if not v.ok:
            return _de_guardas(v, usar_literal=True)
    elif e.accion in ("repreguntar", "responder"):
        v = g.pulido_sin_terminos_nuevos(e.fuente, e.pulido)
        problemas = [p for p in v.detalle if "negación" not in p] if not v.ok else []
        if problemas or (not v.ok and not v.detalle):
            return Veredicto(ok=False, motivo=f"{v.capa}: {problemas[0] if problemas else v.motivo}")

    if e.de == "spa" and e.a == "quy":
        v = g.terminos_fijos(e.pulido, e.traduccion)
    elif e.de == "quy" and e.a == "spa":
        v = g.terminos_fijos(e.traduccion, e.original)
    else:
        v = g.pasa("B4")
    return _de_guardas(v) if not v.ok else Veredicto(ok=True, motivo="barreras de código")


# ── The critic: chaski.critico.revisar, the measured path ─────────────────────────────────────────────────────

def que_auditar(e: EntradaRevision) -> dict | None:
    """The arguments of `critico.revisar` for this message, or None when nothing crosses into Quechua or back.

    Spanish → Quechua: the polish is what is meant; the translation is checked against it, and on `traducir` the polish
    is checked against the transcript. Quechua → Spanish: the translation is what will be read; it is checked against
    a blind back-translation of what the patient was heard saying.
    """
    if e.de == "spa" and e.a == "quy":
        return {"texto_es": e.pulido, "quechua": e.traduccion,
                "transcripcion": e.original if e.accion == "traducir" else None}
    if e.de == "quy" and e.a == "spa":
        return {"texto_es": e.traduccion, "quechua": e.original}
    return None


def auditor(client: anthropic.Anthropic, modelo: str | None = None) -> RevisarFn:
    """The critic role over `critico.revisar`. Its `.modelo` is recorded in `Resultado.modelos`."""
    modelo = modelo or modelo_critico_env()

    def revisar(e: EntradaRevision) -> Veredicto:
        args = que_auditar(e)
        if args is None:
            return Veredicto(ok=True, motivo="sin traducción: solo las barreras de código")
        texto_es = args.pop("texto_es")
        return _de_guardas(critico.revisar(client, texto_es, modelo=modelo, **args).veredicto)

    revisar.modelo = modelo
    return revisar


# ── The bank ──────────────────────────────────────────────────────────────────────────────────────────────────

def servible(item: dict | None) -> bool:
    """A bank phrase may be spoken only if a native speaker reviewed it and it has Quechua."""
    return bool(item) and item.get("revisado") is True and bool(str(item.get("quy") or "").strip())


def frase_servible(frase_id: str) -> dict | None:
    """`banco_fn`: the reviewed item by id, else None (the turn then translates what was said)."""
    from chaski import banco

    item = banco.banco().por_id(frase_id)
    return item if servible(item) else None


def candidatos_servibles(texto_es: str) -> list[dict]:
    """`candidatos_fn`: bank candidates for `decidir`, only the ones `frase_servible` would serve.

    Offering an unreviewed phrase can only end in the fallback, so it is not offered. With no reviewed phrase at all
    the embedding model is never loaded.
    """
    from chaski import banco

    b = banco.banco()
    if not any(servible(it) for it in b.items):
        return []
    return [c for c in b.candidatos(texto_es) if servible(b.por_id(c["id"]))]


def ejemplos_env() -> bool:
    """CHASKI_EJEMPLOS: give the translator the nurse's reviewed phrases as examples (1/0). Moat step 1."""
    return os.environ.get("CHASKI_EJEMPLOS", "1").strip() not in ("0", "no", "false", "")


def ejemplos_para(texto: str, idioma: Idioma) -> list[dict] | None:
    """Reviewed examples for this text, or None. Retrieval failing never breaks a turn: it just translates without."""
    if not ejemplos_env() or not texto.strip():
        return None
    try:
        from chaski import banco as b
        return b.ejemplos_revisados(texto, idioma) or None
    except Exception:  # noqa: BLE001
        return None


def dependencias(client: anthropic.Anthropic, motor: Motor = "claude", modelo_principal: str | None = None,
                 modelo_critico: str | None = None) -> dict:
    """The real wiring: `interpretar(turno, contexto, **dependencias(client))`."""
    return {
        "client": client,
        "traducir_fn": lambda texto, de, a: traducir(texto, de, a, motor=motor, client=client,
                                                     ejemplos=ejemplos_para(texto, de)),
        "guardas_fn": guardas,
        "auditar_fn": auditor(client, modelo_critico),
        "banco_fn": frase_servible,
        "candidatos_fn": candidatos_servibles,
        "modelo": modelo_principal or modelo_principal_env(),
    }


# ── A prescription read from a photo waits for the staff's spoken «sí» (servicio.receta) ──────────────────────
# Deterministic, Spanish only, no model call: the WHOLE utterance must be affirmation words. «sí, pero son dos»,
# «no», «mmm» or anything else is not a yes; the pending prescription is then dropped and the turn runs as usual.

_AFIRMACION_PALABRAS = {"si", "ya", "ok", "okay", "correcto", "exacto", "claro", "dale", "digale", "digaselo",
                        "diselo", "dile", "adelante", "nomas"}
_RELLENO = {"eh", "ah", "mm", "mmm", "pues", "este"}


def _sin_acentos(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def es_afirmacion(texto: str) -> bool:
    """True only if the utterance is a plain yes («sí», «ya, dígale», «está bien», «ok», «así es»...)."""
    limpio = " ".join(re.sub(r"[^a-z\s]", " ", _sin_acentos(texto or "")).split())
    if not limpio:
        return False
    limpio = f" {limpio} ".replace(" por favor ", " ")  # filler, never a yes on its own
    for frase in ("esta bien", "asi es", "eso es"):
        limpio = limpio.replace(f" {frase} ", " si ")
    palabras = limpio.split()
    return (any(p in _AFIRMACION_PALABRAS for p in palabras)
            and all(p in _AFIRMACION_PALABRAS or p in _RELLENO for p in palabras))


def _receta_confirmada(texto: str) -> Decision:
    return Decision(accion="traducir", para="paciente", idioma_salida="quy", texto_pulido=texto,
                    motivo="receta leída de la foto, confirmada por el personal", frase_banco_id=None,
                    dato_faltante=None)


# ── The turn ──────────────────────────────────────────────────────────────────────────────────────────────────

def _como_veredicto(v) -> Veredicto:
    if isinstance(v, Veredicto):
        return v
    if isinstance(v, g.Veredicto):
        return _de_guardas(v)
    if isinstance(v, bool):
        return Veredicto(ok=v, motivo="" if v else "rechazado")
    if isinstance(v, dict):
        return Veredicto.model_validate(v)
    raise TypeError(f"veredicto inválido: {type(v).__name__}")


def _como_traduccion(t, de: Idioma, a: Idioma) -> TextoTraducido:
    if isinstance(t, TextoTraducido):
        return t
    if isinstance(t, str):
        return TextoTraducido(texto=t, de=de, a=a, motor="claude", motor_pedido="claude")
    raise TypeError(f"traducción inválida: {type(t).__name__}")


def _fuente(turno: TurnoEntrada, contexto: Contexto, d: Decision) -> str:
    if d.accion == "responder":
        return "\n".join([*(f"{h.rol}: {h.texto}" for h in contexto.historial), f"{turno.rol}: {turno.texto}"])
    return turno.texto


def interpretar(turno: TurnoEntrada | dict, contexto: Contexto | dict | None = None, *,
                client: anthropic.Anthropic, traducir_fn: TraducirFn, auditar_fn: RevisarFn,
                guardas_fn: RevisarFn = guardas, banco_fn: BancoFn | None = None,
                candidatos_fn: CandidatosFn | None = None, modelo: str | None = None,
                traduccion_forzada: str | None = None,
                al_decidir: Callable[[dict], None] | None = None, voz_fn: VozFn | None = None,
                anticipar: bool | None = None) -> Resultado:
    """Run one turn. Returns the result plus the updated `contexto` to send back next turn.

    `traduccion_forzada` is the rehearsal mode: the translation step returns that text instead of calling
    `traducir_fn`, the bank is skipped (so the seeded text is what gets checked), and guards and critic run as
    always. The result carries `sembrada=True`.

    `al_decidir` (optional) is called once, right after the decision and before translation, with
    {accion, para, idioma_salida, texto_pulido, ms_decidir}, so the app can show the polished Spanish ~3 s in instead
    of ~17 s. It is informational only: what is said is still the final Resultado, and an error in it never breaks the
    turn.

    Two latency paths, neither of which skips a check:
    - `anticipar` (default CHASKI_TRADUCIR_ANTICIPADO): the transcript is sent to the translator at the same time as
      the decision. If the decision is `traducir` in that direction, that translation goes through the same guards and
      critic as always (they compare against the polish and the transcript). If any check rejects it, the turn
      translates the polish as before, so the anticipated path can only save time, never lower the bar.
    - `voz_fn`: the voice is generated while the critic runs and attached only if the critic passes.
    """
    turno = TurnoEntrada.model_validate(turno)
    contexto = Contexto() if contexto is None else Contexto.model_validate(contexto)
    forzada: Decision | None = None
    if contexto.receta_pendiente and turno.rol == "personal":
        # One staff turn resolves the read prescription: a plain yes says it to the patient through every check;
        # anything else drops it and this turn runs as a normal staff turn (a correction is just a new order).
        pendiente, contexto.receta_pendiente = contexto.receta_pendiente.strip(), None
        if pendiente and es_afirmacion(turno.texto):
            turno = TurnoEntrada(texto=pendiente, idioma="spa", rol="personal")
            forzada = _receta_confirmada(pendiente)
            anticipar = False
    modelo = modelo or modelo_principal_env()
    sembrada = traduccion_forzada is not None
    ms: dict[str, float] = {}
    modelos = {"principal": modelo, "critico": getattr(auditar_fn, "modelo", None)}
    paso = "decidir"
    d: Decision | None = None
    avisos: list[str] = []
    t_total = time.perf_counter()
    ya_pidio_repetir = CONFIRMAR in contexto.repreguntas_seguidas  # read before decide() clears it
    anticipar = anticipar_env() if anticipar is None else anticipar
    a_anticipado: Idioma = "quy" if turno.idioma == "spa" else "spa"
    futura: Future | None = None
    if anticipar and not sembrada and turno.texto.strip():
        t_ant = time.perf_counter()

        def _anticipada():
            tt_ = _como_traduccion(traducir_fn(turno.texto.strip(), turno.idioma, a_anticipado), turno.idioma,
                                   a_anticipado)
            return tt_, round((time.perf_counter() - t_ant) * 1000, 1)

        futura = _hilos.submit(_anticipada)

    def medir(nombre: str, t0: float) -> None:
        ms[nombre] = round((time.perf_counter() - t0) * 1000, 1)

    def bloqueado(motivo: str, paso_fallido: str, chequeo: bool = True) -> Resultado:
        # A confirmed prescription that fails a check is not asked back (audit M8): the pending text is gone, so a
        # second «sí» would be translated on its own. The staff sees the plain block and says it themselves.
        pregunta = (_pregunta_de_confirmacion(turno, ya_pidio_repetir, motivo, paso_fallido, sembrada)
                    if chequeo and forzada is None else None)
        if pregunta is not None:
            contexto.agregar(turno.rol, turno.texto)
            contexto.agregar("chaski", pregunta[2])  # the question itself (audit M1: it stored the language code)
            contexto.repreguntas_seguidas.append(CONFIRMAR)
            ms["total"] = round((time.perf_counter() - t_total) * 1000, 1)
            para, idioma_salida, texto = pregunta
            audio_b64 = None
            if voz_fn:  # the same voice as every other turn, not the phone's system voice
                try:
                    t_voz = time.perf_counter()
                    wav = voz_fn(texto, idioma_salida)
                    ms["voz"] = round((time.perf_counter() - t_voz) * 1000, 1)
                    audio_b64 = base64.b64encode(wav).decode() if wav else None
                except Exception:  # noqa: BLE001  no voice is not a block: the text is still shown
                    audio_b64 = None
            return Resultado(audio_wav_b64=audio_b64, estado="dicho_con_aviso", accion="repreguntar" if para == "personal" else "no_entendi",
                             motivo=motivo, dato_faltante=_campo(motivo)[0], para=para, idioma_salida=idioma_salida,
                             texto_original=turno.texto, texto_pulido=d.texto_pulido if d else "", texto_salida=texto,
                             aviso=f"Chaski no lo dijo y pidió repetir: {motivo}", sembrada=sembrada, modelos=modelos,
                             paso_fallido=paso_fallido, ms=ms, contexto=contexto)
        contexto.agregar(turno.rol, turno.texto)
        ms["total"] = round((time.perf_counter() - t_total) * 1000, 1)
        return Resultado(estado="bloqueado", accion=d.accion if d else None, motivo=motivo,
                         dato_faltante=d.dato_faltante if d else None, frase_banco_id=d.frase_banco_id if d else None,
                         para="personal", idioma_salida="spa", texto_original=turno.texto,
                         texto_pulido=d.texto_pulido if d else "", aviso=f"{NO_PUDE}: {motivo}. Chaski no lo dijo.",
                         sembrada=sembrada, modelos=modelos, paso_fallido=paso_fallido, ms=ms, contexto=contexto)

    def listo(texto_salida: str, *, audio: str | None = None, tt: TextoTraducido | None = None,
              historial: str | None = None) -> Resultado:
        contexto.agregar(turno.rol, historial or turno.texto)
        if d.accion in ("repreguntar", "responder", "no_entendi"):
            contexto.agregar("chaski", d.texto_pulido)
        ms["total"] = round((time.perf_counter() - t_total) * 1000, 1)
        aviso = " · ".join(a for a in avisos if a) or None
        return Resultado(estado="dicho_con_aviso" if aviso else "dicho", accion=d.accion, motivo=d.motivo,
                         dato_faltante=d.dato_faltante, frase_banco_id=d.frase_banco_id, para=d.para,
                         idioma_salida=d.idioma_salida, texto_original=turno.texto, texto_pulido=d.texto_pulido,
                         texto_salida=texto_salida, audio=audio, aviso=aviso, motor=tt.motor if tt else None,
                         respaldo=tt.respaldo if tt else False, sembrada=sembrada, modelos=modelos, ms=ms,
                         contexto=contexto)

    try:
        turno_decidir = turno
        if (candidatos_fn and forzada is None and not sembrada and not turno.candidatas and turno.rol == "personal"
                and turno.idioma == "spa" and turno.texto.strip()):
            t0 = time.perf_counter()
            try:  # the bank failing must never break a turn: no candidates is a valid input
                turno_decidir = TurnoEntrada.model_validate(
                    {**turno.model_dump(), "candidatas": list(candidatos_fn(turno.texto) or [])})
            except Exception:  # noqa: BLE001
                turno_decidir = turno
            medir("banco_candidatos", t0)

        t0 = time.perf_counter()
        if forzada is not None:
            contexto.repreguntas_seguidas.clear()
            d = forzada
        else:
            d = decidir(client, turno_decidir, contexto, modelo=modelo)
        if sembrada and d.accion != "traducir":
            # Rehearsal shows the barrier on the seeded translation, whatever the interpreter would have done (audit
            # M6: a repregunta silently skipped the seed and the demo showed «dicho» instead of the block).
            otro: Idioma = "quy" if turno.idioma == "spa" else "spa"
            d = d.model_copy(update={"accion": "traducir", "para": "paciente" if turno.rol == "personal" else "personal",
                                     "idioma_salida": otro, "texto_pulido": turno.texto.strip(), "frase_banco_id": None,
                                     "dato_faltante": None, "motivo": "ensayo: se revisa la traducción sembrada"})
        medir("decidir", t0)
        if memoria.activa() and forzada is None and not sembrada and contexto.historial:
            ultimo = contexto.historial[-1]
            _en_fondo(memoria.senal_de_respuesta, ultimo.rol, ultimo.texto, turno.rol, d.accion)
        if al_decidir:
            try:
                al_decidir({"accion": d.accion, "para": d.para, "idioma_salida": d.idioma_salida,
                            "texto_pulido": d.texto_pulido, "ms_decidir": ms["decidir"]})
            except Exception:  # noqa: BLE001  the early preview must never break a turn
                pass
        if d.aviso:
            avisos.append(d.aviso)

        if d.accion == "no_entendi":  # fixed, verified sentence in the speaker's language: nothing to check
            return listo(d.texto_pulido)

        if d.accion == "usar_frase_banco":
            paso = "banco"
            item = banco_fn(d.frase_banco_id) if banco_fn and not sembrada else None
            if item and str(item.get("quy", "")).strip():
                return listo(item["quy"].strip(), audio=item.get("audio"))  # verified: no generation, no critic
            # The bank could not serve it: translate what the staff actually said, through every check.
            d = d.model_copy(update={"accion": "traducir", "frase_banco_id": None, "texto_pulido": turno.texto.strip(),
                                     "motivo": "frase del banco sin revisar o sin quechua; se traduce"})

        de: Idioma = turno.idioma if d.accion == "traducir" else "spa"  # Chaski's own words are in Spanish
        a: Idioma = d.idioma_salida

        def entrada(texto: str, tt: TextoTraducido) -> EntradaRevision:
            return EntradaRevision(accion=d.accion, original=turno.texto, fuente=_fuente(turno, contexto, d), pulido=texto,
                                   traduccion=tt.texto, de=de, a=a, confianza=turno.confianza, n_mejores=turno.n_mejores)

        def traducir_y_revisar(texto: str) -> tuple[TextoTraducido, Veredicto]:
            nonlocal paso
            paso = "traducir"
            t0 = time.perf_counter()
            if de == a:
                tt = TextoTraducido(texto=texto, de=de, a=a, motor="claude", motor_pedido="claude")
            elif sembrada:
                tt = TextoTraducido(texto=traduccion_forzada, de=de, a=a, motor="claude", motor_pedido="claude")
            else:
                tt = _como_traduccion(traducir_fn(texto, de, a), de, a)
            if not tt.texto.strip():
                raise ValueError("traducción vacía")
            medir("traducir", t0)
            paso = "guardas"
            t0 = time.perf_counter()
            v = _como_veredicto(guardas_fn(entrada(texto, tt)))
            medir("guardas", t0)
            return tt, v

        usada_anticipada = False
        tt = v = None
        if futura is not None and d.accion == "traducir" and de == turno.idioma and a == a_anticipado:
            try:
                tt, ms["traducir_anticipada"] = futura.result()
                if not tt.texto.strip():
                    raise ValueError("traducción anticipada vacía")
                paso = "guardas"
                t0 = time.perf_counter()
                v = _como_veredicto(guardas_fn(entrada(d.texto_pulido, tt)))
                medir("guardas", t0)
                usada_anticipada = v.ok
            except Exception:  # noqa: BLE001  the anticipated path failing only means: do it the normal way
                usada_anticipada = False
            if not usada_anticipada:
                tt = v = None
        if tt is None:
            tt, v = traducir_y_revisar(d.texto_pulido)
        if not v.ok and v.usar_literal and d.accion == "traducir" and d.texto_pulido != turno.texto.strip():
            # B2: the polish changed a fact. Drop it and say exactly what was heard.
            avisos.append(f"Se usó lo dicho tal cual: {v.motivo}")
            d = d.model_copy(update={"texto_pulido": turno.texto.strip()})
            tt, v = traducir_y_revisar(d.texto_pulido)
        if not v.ok:
            return bloqueado(v.motivo or "una barrera lo frenó", "guardas")
        if v.aviso:
            avisos.append(v.aviso)

        def criticar(tt_: TextoTraducido) -> tuple[Veredicto, Future | None]:
            nonlocal paso
            voz_f = None
            if voz_fn and tt_.texto.strip():
                t_voz = time.perf_counter()
                voz_f = _hilos.submit(lambda: (voz_fn(tt_.texto, a), round((time.perf_counter() - t_voz) * 1000, 1)))
            paso = "critico"
            t0 = time.perf_counter()
            vc_ = _como_veredicto(auditar_fn(entrada(d.texto_pulido, tt_)))
            medir("critico", t0)
            return vc_, voz_f

        vc, voz_f = criticar(tt)
        if not vc.ok and usada_anticipada:
            # The critic rejected the anticipated translation: give the normal path its chance before blocking.
            ms["critico_anticipada"] = ms["critico"]
            usada_anticipada = False
            tt2, v2 = traducir_y_revisar(d.texto_pulido)
            if v2.ok:
                tt = tt2
                vc, voz_f = criticar(tt)
        if not vc.ok:
            return bloqueado(vc.motivo or "el crítico lo frenó", "critico")
        audio_b64 = None
        if voz_f is not None:
            paso = "voz"
            try:
                wav, ms["voz"] = voz_f.result(timeout=60)
                audio_b64 = base64.b64encode(wav).decode() if wav else None
            except Exception:  # noqa: BLE001  no voice is not a block: the text is still shown
                avisos.append("sin audio generado")
        if vc.aviso:
            avisos.append(vc.aviso)

        historial = turno.texto
        if d.accion == "traducir" and turno.idioma == "quy":
            historial = f"{turno.texto} (en castellano: {tt.texto})"
        r = listo(tt.texto, tt=tt, historial=historial)
        if memoria.activa() and not sembrada and d.accion == "traducir":
            _en_fondo(memoria.guardar_turno, turno.rol, historial, turno.texto, d.texto_pulido, tt.texto, de, a)
        return r.model_copy(update={"audio_wav_b64": audio_b64, "anticipada": usada_anticipada})
    except Exception as e:  # fail closed: nothing reaches the patient
        return bloqueado(f"falló el paso «{paso}» ({type(e).__name__})", paso, chequeo=False)
