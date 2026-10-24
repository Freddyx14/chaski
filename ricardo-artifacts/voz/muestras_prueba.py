"""Arma un set minimo de audios para probar el ciclo sin esperar a las familias.

Tres clases de audio, porque el interprete tiene que distinguir las tres:
  quy  - chanka real, de las muestras de `facebook/mms-tts-quy` que ya estan en el repo
  spa  - castellano, generado con la voz del sistema de macOS (`say`), sin descargar nada
  mix  - castellano con palabras en quechua, que es como se habla en la posta

Uso:  uv run python voz/muestras_prueba.py            # escribe datos/prueba_minima/
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from voz.ingesta import convertir

# Pares castellano / chanka de muestras/mms-tts-quy/tts_quy.py
FRASES_POSTA = [
    ("¿Está bien, señora?", "¿Allinllanchu, mamáy?"),
    ("¿Cómo está, señor?", "¿Imaynallam kachkanki, taytáy?"),
    ("¿Habla quechua, doctor?", "¿Runasimita rimankichu, doctor?"),
    ("Estoy esperando a mi hija, jefe", "Wawata suyarichkani, jefelláy"),
    ("Señora, estoy bien", "Mamáy, allillanmi"),
]

# Lo que de verdad se dice en una consulta, con el dato critico adentro
FRASES_CLINICAS = [
    "Tome una pastilla cada ocho horas, después de comer",
    "Su próximo control es el lunes, venga en ayunas",
    "Si hay sangrado, venga a la posta de inmediato",
    "El bebé tiene fiebre de treinta y nueve grados",
    "No deje de tomar la pastilla aunque se sienta bien",
]

# Mezcla: castellano con palabras de quechua, normal en la posta
FRASES_MEZCLA = [
    "Mamáy, tome una pastilla cada ocho horas",
    "Taytáy, su control es el lunes",
    "Allinllanchu, ¿tiene dolor aquí?",
]

VOZ_ES = "Paulina"   # si no existe, se usa la primera voz es_ disponible


def voz_disponible() -> str:
    salida = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    nombres = [l.split()[0] for l in salida.splitlines() if " es_" in l]
    return VOZ_ES if VOZ_ES in nombres else (nombres[0] if nombres else "")


def decir(texto: str, destino: Path, voz: str) -> float:
    crudo = destino.with_suffix(".aiff")
    subprocess.run(["say", "-v", voz, "-o", str(crudo), texto], check=True)
    segundos = convertir(crudo, destino)
    crudo.unlink(missing_ok=True)
    return segundos


def main() -> None:
    if not shutil.which("say"):
        raise SystemExit("este script usa `say`, que es de macOS")
    voz = voz_disponible()
    if not voz:
        raise SystemExit("no hay voces en castellano instaladas en el sistema")

    raiz = Path("datos/prueba_minima")
    raiz.mkdir(parents=True, exist_ok=True)
    fichas = []

    for i, texto in enumerate(FRASES_CLINICAS, 1):
        destino = raiz / f"spa_{i:02d}.wav"
        fichas.append({"archivo": destino.name, "idioma": "spa", "texto": texto,
                       "segundos": decir(texto, destino, voz)})

    for i, texto in enumerate(FRASES_MEZCLA, 1):
        destino = raiz / f"mix_{i:02d}.wav"
        fichas.append({"archivo": destino.name, "idioma": "mix", "texto": texto,
                       "segundos": decir(texto, destino, voz)})

    chanka = Path("../muestras/mms-tts-quy/todas.wav")
    if chanka.exists():
        destino = raiz / "quy_todas.wav"
        segundos = convertir(chanka, destino)
        fichas.append({"archivo": destino.name, "idioma": "quy",
                       "texto": " · ".join(q for _, q in FRASES_POSTA), "segundos": segundos})
    else:
        print(f"aviso: falta {chanka}; el lado chanka queda sin audio")

    (raiz / "fichas.json").write_text(json.dumps(fichas, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    print(f"voz del sistema: {voz}")
    for f in fichas:
        print(f"  {f['archivo']:<16} {f['idioma']:<4} {f['segundos']:>5.1f}s  {f['texto'][:52]}")
    print(f"\n{len(fichas)} audios en {raiz}")
    print("Sirven para: probar idioma() con las tres clases, medir la espera por turno,")
    print("y tener un castellano de referencia antes de que lleguen las voces de las familias.")


if __name__ == "__main__":
    main()
