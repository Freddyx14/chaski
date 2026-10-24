"""Audios de WhatsApp -> conjuntos listos para entrenar y medir.

Tres reglas que no se negocian (plan/recoleccion-de-voz.md):
  1. Sin consentimiento, el audio no entra a ningun conjunto.
  2. El conjunto de prueba es UNA PERSONA COMPLETA que no aparece en el
     entrenamiento. Si se parte por frase, el modelo aprende la voz y el numero
     del pitch deja de significar nada.
  3. Quien no es hablante nativo no entra ni al entrenamiento ni a la prueba.
     Sus grabaciones sirven para probar la tuberia, no para enseñarle al modelo
     como suena el chanka ni para decir que tan bien lo entiende.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from voz.contrato import FRECUENCIA_HZ, Grabacion, escribir_manifiesto

FRACCION_VALIDACION = 0.12
MINIMO_PARA_VALIDACION = 10  # con menos clips, la validacion se comeria el entrenamiento

# `origen` del contrato. Quien marca "aprendiz" esta leyendo el cuadernillo sin
# ser hablante: su pronunciacion es una imitacion, no el acento de la posta.
APRENDIZ = "aprendiz"


def es_nativo(g: Grabacion) -> bool:
    return g.origen != APRENDIZ


def utilizables(grabaciones: list[Grabacion], incluir_aprendices: bool = False) -> list[Grabacion]:
    """Lo que puede entrar a un conjunto.

    `incluir_aprendices` existe para probar la tuberia de punta a punta antes de
    que lleguen las grabaciones de las familias, no para entrenar. Por defecto
    va en falso: una grabacion de alguien que imita el chanka le ensena al modelo
    una pronunciacion que ningun paciente tiene, y medida como prueba da un WER
    que no representa a nadie.
    """
    listos = [g for g in grabaciones if g.consentimiento and g.transcripcion.strip()]
    return listos if incluir_aprendices else [g for g in listos if es_nativo(g)]


def resumen_por_persona(grabaciones: list[Grabacion]) -> dict:
    salida: dict[str, dict] = {}
    for g in grabaciones:
        fila = salida.setdefault(g.persona, {"clips": 0, "segundos": 0.0, "bloque_A": 0,
                                             "bloque_B": 0, "sin_transcripcion": 0})
        fila["clips"] += 1
        fila["segundos"] += g.segundos
        fila[f"bloque_{g.bloque}"] += 1
        if not g.transcripcion.strip():
            fila["sin_transcripcion"] += 1
    for fila in salida.values():
        fila["minutos"] = round(fila["segundos"] / 60, 2)
    return salida


def elegir_persona_prueba(grabaciones: list[Grabacion]) -> str:
    """Quien tenga mas respuestas espontaneas (bloque B), que es lo que se parece
    al uso real; a igualdad, quien tenga menos clips, para no regalar datos de
    entrenamiento."""
    resumen = resumen_por_persona(grabaciones)
    return sorted(resumen.items(), key=lambda kv: (-kv[1]["bloque_B"], kv[1]["clips"]))[0][0]


def partir_por_hablante(grabaciones: list[Grabacion], persona_prueba: str | None = None) -> dict:
    datos = utilizables(grabaciones)
    personas = sorted({g.persona for g in datos})
    if len(personas) < 2:
        aprendices = sorted({g.persona for g in grabaciones if not es_nativo(g)})
        pista = (f" (se dejaron fuera {len(aprendices)} aprendices: {aprendices})"
                 if aprendices else "")
        raise ValueError(
            "hacen falta al menos dos personas para una particion honesta; "
            f"hay {len(personas)}{pista}")

    prueba_id = persona_prueba or elegir_persona_prueba(datos)
    if prueba_id not in personas:
        raise ValueError(f"{prueba_id!r} no aparece en los datos: {personas}")

    prueba = [g for g in datos if g.persona == prueba_id]
    resto = sorted((g for g in datos if g.persona != prueba_id),
                   key=lambda g: (g.persona, g.bloque, g.numero))
    if len(resto) >= MINIMO_PARA_VALIDACION:
        corte = max(1, int(len(resto) * FRACCION_VALIDACION))
        # la validacion toma una de cada N, no el final: asi cubre a todas las personas
        paso = max(1, len(resto) // corte)
        indices = set(range(0, len(resto), paso))
        indices = set(sorted(indices)[:corte])
    else:
        indices = set()
    validacion = [g for i, g in enumerate(resto) if i in indices]
    entrenamiento = [g for i, g in enumerate(resto) if i not in indices]
    # Solo listas de grabaciones: quien llama itera .values() sin sorpresas.
    return {"entrenamiento": entrenamiento, "validacion": validacion, "prueba": prueba}


def convertir(origen: str | Path, destino: str | Path) -> float:
    """A WAV mono 16 kHz 16 bits. Devuelve la duracion en segundos."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not shutil.which("ffmpeg"):
        raise RuntimeError("falta ffmpeg: brew install ffmpeg")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(origen),
         "-ac", "1", "-ar", str(FRECUENCIA_HZ), "-sample_fmt", "s16", str(destino)],
        check=True)
    return duracion(destino)


def duracion(audio: str | Path) -> float:
    salida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
        capture_output=True, text=True, check=True)
    return round(float(salida.stdout.strip()), 2)


def escribir_particion(partes: dict, raiz: str | Path = "datos") -> dict:
    raiz = Path(raiz)
    persona_prueba = partes["prueba"][0].persona if partes["prueba"] else "?"
    conteos = {}
    for conjunto in ("entrenamiento", "validacion", "prueba"):
        cabecera = (f"prueba: unica persona {persona_prueba}, "
                    "jamas vista en entrenamiento") if conjunto == "prueba" else ""
        escribir_manifiesto(raiz / conjunto / "manifiesto.jsonl", partes[conjunto], cabecera)
        conteos[conjunto] = len(partes[conjunto])
    resumen = {"conteos": conteos, "persona_prueba": persona_prueba,
               "por_persona": resumen_por_persona(
                   partes["entrenamiento"] + partes["validacion"] + partes["prueba"])}
    (raiz / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    return resumen
