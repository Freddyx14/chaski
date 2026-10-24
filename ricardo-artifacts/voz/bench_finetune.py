"""Mide cuanto tardaria el ajuste fino ANTES de prender la instancia de AWS.

No descarga pesos: arma el modelo desde la configuracion con pesos al azar, le
pasa lotes sinteticos del mismo tamano que los reales y cronometra pasos de
entrenamiento. Lo que mide es el costo por paso de ESTA maquina; el mismo script
corrido en la instancia da el numero de alla, sin adivinar factores.

Uso:
  uv run --with torch --with transformers python voz/bench_finetune.py
  uv run --with torch --with transformers python voz/bench_finetune.py \
      --modelo medium --clips 1200 --epocas 3 --batch 4 --congelar-encoder
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from dataclasses import dataclass, asdict

import torch
from transformers import WhisperConfig, WhisperForConditionalGeneration

# Dimensiones oficiales de Whisper. Se declaran aqui para no pedir nada por red.
CONFIGURACIONES = {
    "tiny":   dict(d_model=384,  encoder_layers=4,  decoder_layers=4,  encoder_attention_heads=6,  decoder_attention_heads=6),
    "base":   dict(d_model=512,  encoder_layers=6,  decoder_layers=6,  encoder_attention_heads=8,  decoder_attention_heads=8),
    "small":  dict(d_model=768,  encoder_layers=12, decoder_layers=12, encoder_attention_heads=12, decoder_attention_heads=12),
    "medium": dict(d_model=1024, encoder_layers=24, decoder_layers=24, encoder_attention_heads=16, decoder_attention_heads=16),
}
MELS = 80
MARCOS = 3000      # Whisper siempre procesa 30 s, aunque el clip dure 4
VOCABULARIO = 51865


@dataclass
class Resultado:
    maquina: str
    dispositivo: str
    modelo: str
    parametros_millones: float
    entrenables_millones: float
    batch: int
    segundos_por_paso: float
    clips: int
    epocas: int
    pasos: int
    minutos_estimados: float
    memoria_gb: float | None


def construir(tamano: str, congelar_encoder: bool):
    cfg = WhisperConfig(num_mel_bins=MELS, vocab_size=VOCABULARIO,
                        max_source_positions=MARCOS // 2, **CONFIGURACIONES[tamano])
    modelo = WhisperForConditionalGeneration(cfg)
    if congelar_encoder:
        for p in modelo.model.encoder.parameters():
            p.requires_grad = False
    return modelo


def dispositivo() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def medir(modelo, dev: str, batch: int, largo_etiquetas: int, pasos: int) -> float:
    modelo.to(dev).train()
    opt = torch.optim.AdamW([p for p in modelo.parameters() if p.requires_grad], lr=1e-5)
    rasgos = torch.randn(batch, MELS, MARCOS, device=dev)
    etiquetas = torch.randint(0, VOCABULARIO, (batch, largo_etiquetas), device=dev)

    def un_paso():
        opt.zero_grad(set_to_none=True)
        salida = modelo(input_features=rasgos, labels=etiquetas)
        salida.loss.backward()
        opt.step()

    for _ in range(2):           # calentamiento, no cuenta
        un_paso()
    if dev == "cuda":
        torch.cuda.synchronize()
    elif dev == "mps":
        torch.mps.synchronize()

    inicio = time.perf_counter()
    for _ in range(pasos):
        un_paso()
    if dev == "cuda":
        torch.cuda.synchronize()
    elif dev == "mps":
        torch.mps.synchronize()
    return (time.perf_counter() - inicio) / pasos


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--modelo", default="small", choices=list(CONFIGURACIONES))
    p.add_argument("--clips", type=int, default=1000, help="cuantos audios tendra el entrenamiento")
    p.add_argument("--epocas", type=int, default=3)
    p.add_argument("--batch", type=int, default=2)
    p.add_argument("--etiquetas", type=int, default=64, help="tokens por transcripcion")
    p.add_argument("--pasos", type=int, default=6, help="pasos cronometrados")
    p.add_argument("--congelar-encoder", action="store_true",
                   help="entrena solo el decodificador: mas barato y suele bastar con pocos datos")
    p.add_argument("--salida", default="reports/bench_finetune.json")
    args = p.parse_args()

    dev = dispositivo()
    modelo = construir(args.modelo, args.congelar_encoder)
    total = sum(x.numel() for x in modelo.parameters())
    entrenables = sum(x.numel() for x in modelo.parameters() if x.requires_grad)

    por_paso = medir(modelo, dev, args.batch, args.etiquetas, args.pasos)
    pasos = -(-args.clips // args.batch) * args.epocas
    memoria = (torch.cuda.max_memory_allocated() / 2**30) if dev == "cuda" else None

    r = Resultado(
        maquina=f"{platform.machine()} {platform.system()}",
        dispositivo=dev, modelo=args.modelo,
        parametros_millones=round(total / 1e6, 1),
        entrenables_millones=round(entrenables / 1e6, 1),
        batch=args.batch, segundos_por_paso=round(por_paso, 3),
        clips=args.clips, epocas=args.epocas, pasos=pasos,
        minutos_estimados=round(pasos * por_paso / 60, 1),
        memoria_gb=round(memoria, 2) if memoria else None)

    print(json.dumps(asdict(r), ensure_ascii=False, indent=1))
    print(f"\n{args.modelo} en {dev}: {r.segundos_por_paso} s por paso de {args.batch} clips")
    print(f"{args.clips} clips x {args.epocas} epocas = {pasos} pasos "
          f"-> {r.minutos_estimados} min ({round(r.minutos_estimados/60, 1)} h)")
    print("Whisper procesa 30 s por clip aunque el audio dure 4: el costo no baja "
          "por tener audios cortos.")

    import pathlib
    destino = pathlib.Path(args.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    historial = json.loads(destino.read_text()) if destino.exists() else []
    historial.append(asdict(r))
    destino.write_text(json.dumps(historial, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
