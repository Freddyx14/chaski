# -*- coding: utf-8 -*-
"""Convierte una nota de voz larga en clips cortos con texto, listos para VITS.

El ajuste de voz quiere enunciados cortos: VITS alinea texto con audio dentro de
cada clip, y un audio de un minuto con varias frases no se alinea con nada. Las
grabaciones del formulario ya venian cortadas de origen; una nota de WhatsApp no.

Tres pasos:

  1. Partir por silencios con ffmpeg. Se corta donde la persona respira, no cada
     N segundos, asi ningun corte cae en mitad de una palabra.
  2. Transcribir cada trozo con nuestro reconocedor ajustado. Sale un BORRADOR.
  3. Escribir el audiofolder y un jsonl para revisar.

Lo tercero importa: el texto sale del modelo, no de la persona. Para entrenar la
voz, un texto equivocado le enseña a pronunciar mal. Con pocos minutos conviene
revisarlo en /corregir antes de entrenar; con `--sin-revisar` se entrena igual y
queda dicho que el texto es automatico.

Uso:
  python voz/preparar_voz_larga.py "reports/voz mama de freddy" --persona mama_freddy
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

MINIMO = 1.0
MAXIMO = 15.0


def duracion(ruta: Path) -> float:
    s = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(ruta)], capture_output=True, text=True)
    try:
        return float(s.stdout.strip())
    except ValueError:
        return 0.0


def cortes(ruta: Path, total: float, ruido_db: int, silencio_min: float) -> list:
    import re
    salida = subprocess.run(
        ["ffmpeg", "-i", str(ruta), "-af",
         f"silencedetect=noise={ruido_db}dB:d={silencio_min}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    inicios = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", salida)]
    finales = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", salida)]
    trozos, cursor = [], 0.0
    for i, inicio in enumerate(inicios):
        if inicio - cursor >= MINIMO:
            trozos.append((cursor, inicio))
        cursor = finales[i] if i < len(finales) else total
    if total - cursor >= MINIMO:
        trozos.append((cursor, total))
    # Los trozos largos se parten a la mitad hasta que entren; mejor dos pedazos
    # que descartar diez segundos de voz.
    salida_final = []
    for inicio, fin in trozos:
        pila = [(inicio, fin)]
        while pila:
            a, b = pila.pop()
            if b - a <= MAXIMO:
                salida_final.append((a, b))
            else:
                medio = (a + b) / 2
                pila.extend([(a, medio), (medio, b)])
    return sorted(t for t in salida_final if MINIMO <= t[1] - t[0] <= MAXIMO)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("carpeta", help="carpeta con las notas de voz largas")
    p.add_argument("--persona", required=True)
    p.add_argument("--ruido-db", type=int, default=-32)
    p.add_argument("--silencio-min", type=float, default=0.45)
    p.add_argument("--transcribir", action="store_true",
                   help="pide el borrador al reconocedor ajustado")
    p.add_argument("--salida", default="")
    args = p.parse_args()

    origen = Path(args.carpeta)
    destino = Path(args.salida or f"datos/crudo/{args.persona}")
    (destino / "trozos").mkdir(parents=True, exist_ok=True)

    piezas = []
    for nota in sorted(origen.iterdir()):
        if nota.suffix.lower() not in (".ogg", ".m4a", ".mp3", ".wav", ".opus"):
            continue
        total = duracion(nota)
        trozos = cortes(nota, total, args.ruido_db, args.silencio_min)
        print(f"  {nota.name}  {total:.0f}s -> {len(trozos)} trozos")
        for i, (inicio, fin) in enumerate(trozos, 1):
            salida = destino / "trozos" / f"{args.persona}_{len(piezas)+1:03d}.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(inicio),
                            "-t", str(fin - inicio), "-i", str(nota),
                            "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
                            str(salida)], check=True)
            piezas.append({"audio": str(salida), "segundos": round(fin - inicio, 2),
                           "origen": nota.name, "texto": ""})

    if args.transcribir and piezas:
        import torch
        from transformers import AutoProcessor, Wav2Vec2ForCTC
        import soundfile as sf

        base = "facebook/mms-1b-all"
        proc = AutoProcessor.from_pretrained(base, target_lang="quy")
        modelo = Wav2Vec2ForCTC.from_pretrained(base, target_lang="quy",
                                                ignore_mismatched_sizes=True)
        adaptador = Path("modelos/asr-chanka/adaptador_mejor.pt")
        if adaptador.exists():
            modelo.load_state_dict(torch.load(adaptador, map_location="cpu"), strict=False)
        d = "cuda" if torch.cuda.is_available() else "cpu"
        modelo = modelo.to(d).eval()
        for pieza in piezas:
            onda, fr = sf.read(pieza["audio"], dtype="float32")
            x = proc(onda, sampling_rate=fr, return_tensors="pt").input_values.to(d)
            with torch.no_grad():
                pieza["texto"] = proc.batch_decode(torch.argmax(modelo(x).logits, -1))[0]
        print("  texto: borrador del reconocedor, SIN revisar")

    total_s = sum(p_["segundos"] for p_ in piezas)
    with (destino / "trozos.jsonl").open("w", encoding="utf-8") as f:
        for pieza in piezas:
            f.write(json.dumps(pieza, ensure_ascii=False) + "\n")
    print(f"\n{len(piezas)} trozos · {total_s/60:.1f} min -> {destino}/trozos.jsonl")


if __name__ == "__main__":
    main()
