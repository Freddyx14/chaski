# -*- coding: utf-8 -*-
"""Genera el A/B/C de cada voz: base de Meta, ajustada, y la grabacion real.

Es la prueba del pitch (§11 de plan/pitch.md): la misma frase tres veces para
que el jurado oiga la diferencia. Una carpeta por voz, los tres archivos con el
mismo nombre de frase, asi se comparan sin buscar.

  A  base.mp3       la voz de Meta tal cual
  B  ajustada.mp3   el mismo modelo entrenado con esa persona
  C  real.mp3       la persona

Si B no se distingue de C, ese es el momento tecnico del pitch. Y si no, se dice
tambien: la regla de la casa es no afirmar lo que no se oye.

Uso:
  python voz/generar_abc.py --voces p24 p16 mama_freddy papa_ricardo
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

FRASES = [
    ("dosis", "Sapa pusaq horapi huk pastillata upyay"),
    ("control", "Controlniykiqa lunesmi kanqa"),
    ("alarma", "Wawacha mana kuyukuptinqa, kaymanmi hamuykunki"),
    ("saludo", "Allinllanchu mamay, imaynallam kachkanki"),
]


def a_mp3(wav: Path, mp3: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                    "-b:a", "96k", str(mp3)], check=True)


def real_de(persona: str) -> Path | None:
    """Una grabacion de verdad de esa persona, para la C."""
    for patron in (f"datos/crudo/{persona}/*.wav", f"datos/crudo/{persona}/trozos/*.wav"):
        encontrados = sorted(Path().glob(patron))
        if encontrados:
            # El mas largo: se oye mejor la voz que en un «si» de medio segundo.
            return max(encontrados, key=lambda p: p.stat().st_size)
    return None


def main() -> None:
    import torch
    from transformers import AutoTokenizer, VitsModel

    p = argparse.ArgumentParser()
    p.add_argument("--voces", nargs="+", default=["p24"])
    p.add_argument("--modelos", default="modelos")
    p.add_argument("--salida", default="reports/voces")
    args = p.parse_args()

    import soundfile as sf

    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    raiz = Path(args.salida)

    # La A es la misma para todos: el modelo de fabrica.
    base_tok = AutoTokenizer.from_pretrained("facebook/mms-tts-quy")
    base = VitsModel.from_pretrained("facebook/mms-tts-quy").to(dispositivo).eval()

    resumen = {}
    for persona in args.voces:
        ruta = Path(args.modelos) / f"tts-{persona}"
        if not ruta.exists():
            print(f"  {persona}: todavia no hay modelo en {ruta}")
            continue
        destino = raiz / persona
        destino.mkdir(parents=True, exist_ok=True)

        tok = AutoTokenizer.from_pretrained(str(ruta))
        voz = VitsModel.from_pretrained(str(ruta)).to(dispositivo).eval()

        for nombre, texto in FRASES:
            for etiqueta, modelo, tokenizador in (("A_base", base, base_tok),
                                                  ("B_ajustada", voz, tok)):
                with torch.no_grad():
                    onda = modelo(**tokenizador(texto, return_tensors="pt")
                                  .to(dispositivo)).waveform[0].cpu().numpy()
                wav = destino / f"{nombre}_{etiqueta}.wav"
                sf.write(wav, onda, modelo.config.sampling_rate)
                a_mp3(wav, wav.with_suffix(".mp3"))
                wav.unlink()

        real = real_de(persona)
        if real:
            a_mp3(real, destino / "C_real.mp3")
        (destino / "frases.json").write_text(
            json.dumps({"persona": persona, "modelo": str(ruta),
                        "real": str(real) if real else None,
                        "frases": dict(FRASES)}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        resumen[persona] = len(list(destino.glob("*.mp3")))
        print(f"  {persona}: {resumen[persona]} mp3 en {destino}")

    print(f"\n{sum(resumen.values())} archivos en {raiz}/")


if __name__ == "__main__":
    main()
