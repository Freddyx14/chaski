"""Mide `facebook/mms-lid-512` sobre el set minimo: acierto y latencia.

Corre EN la instancia. El set tiene tres clases y solo dos tienen respuesta
correcta: `spa` y `quy`. Los `mix` (castellano con quechua adentro) se reportan
aparte porque NO tienen respuesta unica, y contarlos como error o como acierto
seria mentir en las dos direcciones.
"""
import json
import time
from pathlib import Path

import soundfile as sf
import torch
from transformers import AutoFeatureExtractor, Wav2Vec2ForSequenceClassification

BASE = Path("/opt/dlami/nvme/chaski")
MUESTRAS = BASE / "datos/prueba_minima"
TARJETA = "facebook/mms-lid-512"
INTERESAN = ("spa", "quy")


def main() -> None:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    t0 = time.perf_counter()
    extractor = AutoFeatureExtractor.from_pretrained(TARJETA)
    modelo = Wav2Vec2ForSequenceClassification.from_pretrained(TARJETA).to(dev).eval()
    carga = round(time.perf_counter() - t0, 2)
    print("modelo cargado en", carga, "s en", dev, flush=True)

    etiquetas = modelo.config.id2label
    indices = {c: [i for i, n in etiquetas.items() if n == c] for c in INTERESAN}
    print("indices:", {k: v for k, v in indices.items()}, flush=True)

    fichas = json.loads((MUESTRAS / "fichas.json").read_text(encoding="utf-8"))
    filas = []
    for f in fichas:
        audio, fm = sf.read(str(MUESTRAS / f["archivo"]))
        entrada = extractor(audio, sampling_rate=fm, return_tensors="pt").to(dev)
        if dev == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.no_grad():
            logits = modelo(**entrada).logits[0]
        if dev == "cuda":
            torch.cuda.synchronize()
        ms = round((time.perf_counter() - t0) * 1000, 1)

        libre = etiquetas[int(logits.argmax())]
        # restringido a las dos lenguas del producto
        puntajes = {c: float(max(logits[i] for i in indices[c])) for c in INTERESAN if indices[c]}
        total = torch.logsumexp(torch.tensor(list(puntajes.values())), dim=0)
        probabilidades = {c: round(float(torch.exp(torch.tensor(v) - total)), 3)
                          for c, v in puntajes.items()}
        restringido = max(probabilidades, key=probabilidades.get)

        filas.append({"archivo": f["archivo"], "esperado": f["idioma"], "libre_512": libre,
                      "restringido": restringido, "probabilidades": probabilidades,
                      "ms": ms, "segundos_audio": f["segundos"]})
        print(f"{f['archivo']:<16} esperado={f['idioma']:<4} libre={libre:<10} "
              f"restringido={restringido:<4} p={probabilidades} {ms} ms", flush=True)

    puros = [r for r in filas if r["esperado"] in INTERESAN]
    aciertos = sum(r["restringido"] == r["esperado"] for r in puros)
    mezclas = [r for r in filas if r["esperado"] == "mix"]
    resumen = {
        "modelo": TARJETA, "dispositivo": dev, "cargar_s": carga,
        "acierto_puros": f"{aciertos}/{len(puros)}",
        "latencia_mediana_ms": sorted(r["ms"] for r in filas)[len(filas) // 2],
        "latencia_max_ms": max(r["ms"] for r in filas),
        "mix": [{"archivo": r["archivo"], "restringido": r["restringido"],
                 "probabilidades": r["probabilidades"]} for r in mezclas],
        "detalle": filas,
    }
    (BASE / "lid.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    print("\nacierto en casos puros:", resumen["acierto_puros"])
    print("latencia mediana:", resumen["latencia_mediana_ms"], "ms | maxima:",
          resumen["latencia_max_ms"], "ms")
    print("mezclas (sin respuesta correcta unica):",
          [(r["archivo"], r["restringido"]) for r in mezclas])


if __name__ == "__main__":
    main()
