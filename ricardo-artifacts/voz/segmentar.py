"""Corta una grabacion larga en un clip por frase.

La familia no va a mandar 125 archivos: va a mandar un audio seguido, o una
videollamada grabada. Esto lo parte por los silencios con ffmpeg, sin librerias
extra, y lo empareja en orden con el cuadernillo de frases.

Regla: si el numero de trozos no coincide con el numero de frases, NO se empareja
a ciegas. Se prueban varios umbrales; si ninguno cuadra, se escribe un archivo de
revision y se dice cuantos salieron. Un emparejamiento corrido arruina todo el
conjunto de entrenamiento y no se nota hasta que el modelo sale mal.

Uso:
  PYTHONPATH=. uv run python voz/segmentar.py grabacion.m4a --persona p1 --frases 125
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from voz.contrato import Grabacion, escribir_manifiesto
from voz.ingesta import convertir, duracion

UMBRALES = [(-30, 0.45), (-35, 0.40), (-25, 0.50), (-40, 0.35), (-30, 0.30)]
MINIMO_CLIP = 0.5      # segundos; menos que esto es un carraspeo
MAXIMO_CLIP = 20.0


@dataclass
class Trozo:
    inicio: float
    fin: float

    @property
    def largo(self) -> float:
        return self.fin - self.inicio


def detectar_silencios(audio: Path, ruido_db: int, minimo_s: float) -> list[tuple[float, float]]:
    salida = subprocess.run(
        ["ffmpeg", "-i", str(audio), "-af",
         f"silencedetect=noise={ruido_db}dB:d={minimo_s}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    inicios = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", salida)]
    finales = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", salida)]
    return list(zip(inicios, finales + [None] * (len(inicios) - len(finales))))


def trozos_de_voz(audio: Path, total: float, ruido_db: int, minimo_s: float) -> list[Trozo]:
    silencios = detectar_silencios(audio, ruido_db, minimo_s)
    trozos, cursor = [], 0.0
    for inicio, fin in silencios:
        if inicio - cursor >= MINIMO_CLIP:
            trozos.append(Trozo(cursor, inicio))
        cursor = fin if fin is not None else total
    if total - cursor >= MINIMO_CLIP:
        trozos.append(Trozo(cursor, total))
    return [t for t in trozos if MINIMO_CLIP <= t.largo <= MAXIMO_CLIP]


def mejor_particion(audio: Path, total: float, esperadas: int) -> tuple[list[Trozo], dict]:
    """Prueba varios umbrales y se queda con el que mas se acerque al numero de frases."""
    intentos = []
    for ruido, minimo in UMBRALES:
        trozos = trozos_de_voz(audio, total, ruido, minimo)
        intentos.append({"ruido_db": ruido, "silencio_s": minimo, "trozos": len(trozos),
                         "diferencia": abs(len(trozos) - esperadas)})
        if len(trozos) == esperadas:
            return trozos, {"umbral": intentos[-1], "intentos": intentos, "exacto": True}
    mejor = min(intentos, key=lambda x: x["diferencia"])
    trozos = trozos_de_voz(audio, total, mejor["ruido_db"], mejor["silencio_s"])
    return trozos, {"umbral": mejor, "intentos": intentos, "exacto": False}


def recortar(origen: Path, destino: Path, inicio: float, largo: float) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{inicio:.3f}",
                    "-t", f"{largo:.3f}", "-i", str(origen), "-ac", "1", "-ar", "16000",
                    "-sample_fmt", "s16", str(destino)], check=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("grabacion")
    p.add_argument("--persona", required=True, help="identificador corto y anonimo: p1, p2")
    p.add_argument("--bloque", default="A", choices=["A", "B"])
    p.add_argument("--frases", type=int, help="cuantas frases trae el cuadernillo")
    p.add_argument("--lista", default="datos/frases/frases.json")
    p.add_argument("--salida", default="datos/crudo")
    args = p.parse_args()

    origen = Path(args.grabacion)
    salida = Path(args.salida) / args.persona
    salida.mkdir(parents=True, exist_ok=True)

    normalizado = salida / "completo.wav"
    total = convertir(origen, normalizado)

    textos: list[str] = []
    lista = Path(args.lista)
    if lista.exists():
        datos = json.loads(lista.read_text(encoding="utf-8"))
        textos = [f["castellano"] for f in datos["verificadas"]] + datos["clinicas_sin_traducir"]
    esperadas = args.frases or len(textos) or 0

    trozos, diagnostico = mejor_particion(normalizado, total, esperadas or 1)

    grabaciones = []
    for i, t in enumerate(trozos, 1):
        destino = salida / f"{args.persona}_{args.bloque}_{i:03d}.wav"
        recortar(normalizado, destino, t.inicio, t.largo)
        grabaciones.append(Grabacion(
            persona=args.persona, bloque=args.bloque, numero=i, audio=str(destino),
            transcripcion="", castellano=textos[i - 1] if i <= len(textos) else "",
            segundos=round(t.largo, 2), consentimiento=False))

    escribir_manifiesto(salida / "manifiesto.jsonl", grabaciones,
                        cabecera=("SIN REVISAR: falta transcripcion en chanka y marcar "
                                  "consentimiento=true"))
    (salida / "diagnostico.json").write_text(
        json.dumps({"total_segundos": total, "esperadas": esperadas,
                    "obtenidas": len(trozos), **diagnostico}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print(f"audio: {total:.1f} s -> {len(trozos)} trozos "
          f"(umbral {diagnostico['umbral']['ruido_db']} dB, "
          f"{diagnostico['umbral']['silencio_s']} s de silencio)")
    if esperadas and len(trozos) != esperadas:
        print(f"OJO: se esperaban {esperadas} frases y salieron {len(trozos)}. "
              "NO se empareja a ciegas: revisa diagnostico.json y el manifiesto antes de usarlo.")
    else:
        print("coincide con el cuadernillo; el emparejamiento es fiable")
    print(f"manifiesto en {salida / 'manifiesto.jsonl'}")


if __name__ == "__main__":
    main()
