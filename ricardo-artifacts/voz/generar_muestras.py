"""Genera audios de prueba en chanka con texto de referencia conocido.

Usa los pares verificados del cuadernillo (`makitty/quechua-chanka-unified-v2`,
CC-BY-4.0) y los dice con `mms-tts-quy` a traves del servicio de la instancia.
Como sabemos EXACTAMENTE que texto se dijo, cada audio trae su verdad de
referencia y sirve para medir el reconocimiento sin esperar a las familias.

Limite de 45 s por audio: un turno de consulta no dura mas, y clips cortos
abaratan el ajuste fino con CTC.

Uso:  PYTHONPATH=. uv run --with httpx python voz/generar_muestras.py --cuantos 5
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import httpx

INSTANCIA = "http://127.0.0.1:8010"
DESTINO = Path("datos/muestras_quy")
SILENCIO_S = 0.55
LIMITE_S = 45.0


def duracion(ruta: Path) -> float:
    salida = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=nk=1:nw=1", str(ruta)],
                            capture_output=True, text=True, check=True)
    return round(float(salida.stdout.strip()), 2)


def decir(cliente: httpx.Client, texto: str, destino: Path) -> float:
    r = cliente.post(f"{INSTANCIA}/hablar", data={"texto": texto})
    r.raise_for_status()
    destino.write_bytes(r.content)
    return duracion(destino)


def pegar(partes: list[Path], silencio: Path, destino: Path) -> float:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lista:
        for p in partes:
            lista.write(f"file '{p.resolve()}'\nfile '{silencio.resolve()}'\n")
        ruta_lista = lista.name
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", ruta_lista, "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
                    str(destino)], check=True)
    Path(ruta_lista).unlink(missing_ok=True)
    return duracion(destino)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cuantos", type=int, default=5)
    p.add_argument("--limite", type=float, default=LIMITE_S)
    args = p.parse_args()

    frases = json.loads(Path("datos/frases/frases.json").read_text(encoding="utf-8"))["verificadas"]
    DESTINO.mkdir(parents=True, exist_ok=True)
    temporal = DESTINO / "_piezas"
    temporal.mkdir(exist_ok=True)

    silencio = temporal / "silencio.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=16000:cl=mono", "-t", str(SILENCIO_S), str(silencio)], check=True)

    fichas, usadas = [], 0
    with httpx.Client(timeout=300) as cliente:
        for n in range(1, args.cuantos + 1):
            partes, textos, acumulado = [], [], 0.0
            while usadas < len(frases):
                f = frases[usadas]
                pieza = temporal / f"p{usadas:03d}.wav"
                try:
                    largo = decir(cliente, f["chanka"], pieza)
                except Exception as e:
                    print("falla al decir:", str(e)[:80]); usadas += 1; continue
                if acumulado + largo + SILENCIO_S > args.limite and partes:
                    break
                partes.append(pieza); textos.append(f)
                acumulado += largo + SILENCIO_S
                usadas += 1
            if not partes:
                break
            destino = DESTINO / f"quy_{n:02d}.wav"
            real = pegar(partes, silencio, destino)
            fichas.append({"archivo": destino.name, "segundos": real, "frases": len(textos),
                           "chanka": " ".join(t["chanka"] for t in textos),
                           "castellano": " ".join(t["castellano"] for t in textos),
                           "partes": [{"chanka": t["chanka"], "castellano": t["castellano"]}
                                      for t in textos]})
            print(f"{destino.name}  {real:>5.1f}s  {len(textos)} frases")

    (DESTINO / "fichas.json").write_text(json.dumps(fichas, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    for pieza in temporal.glob("*.wav"):
        pieza.unlink()
    temporal.rmdir()
    total = sum(f["segundos"] for f in fichas)
    print(f"\n{len(fichas)} audios · {total:.0f} s en total · referencia en {DESTINO}/fichas.json")


if __name__ == "__main__":
    main()
