# -*- coding: utf-8 -*-
"""Mide cuanto cuesta ajustar mms-tts-quy, la voz de Chaski.

El numero del ajuste de omniASR no sirve aqui y por eso existe este archivo:
omniASR es un codificador con CTC, y VITS es un generador con un discriminador
adversarial encima. Son dos costos por paso distintos.

Que mide, y que no:

  generador      real. Carga los pesos de facebook/mms-tts-quy y cronometra
                 adelante + atras sobre ellos.
  discriminador  aproximado. VITS entrena con el discriminador multi-periodo y
                 multi-escala de HiFi-GAN, que no viene en transformers. Se
                 arma aqui con la arquitectura estandar; los tamanos son los del
                 paper, asi que el costo deberia quedar cerca, pero es una
                 reconstruccion, no el discriminador exacto de Meta.

El total por paso es la suma: en VITS cada paso entrena las dos redes.

Uso:
  python voz/bench_tts.py --clips 175 --epocas 200
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.nn.utils import weight_norm

TARJETA = "facebook/mms-tts-quy"


class Periodo(nn.Module):
    """Una rama del discriminador multi-periodo: mira la onda cada `p` muestras."""

    def __init__(self, p: int):
        super().__init__()
        self.p = p
        self.convs = nn.ModuleList([
            weight_norm(nn.Conv2d(1, 32, (5, 1), (3, 1), padding=(2, 0))),
            weight_norm(nn.Conv2d(32, 128, (5, 1), (3, 1), padding=(2, 0))),
            weight_norm(nn.Conv2d(128, 512, (5, 1), (3, 1), padding=(2, 0))),
            weight_norm(nn.Conv2d(512, 1024, (5, 1), (3, 1), padding=(2, 0))),
            weight_norm(nn.Conv2d(1024, 1024, (5, 1), 1, padding=(2, 0))),
        ])
        self.post = weight_norm(nn.Conv2d(1024, 1, (3, 1), 1, padding=(1, 0)))

    def forward(self, x):
        b, c, t = x.shape
        if t % self.p:
            x = nn.functional.pad(x, (0, self.p - (t % self.p)), "reflect")
            t = x.shape[-1]
        x = x.view(b, c, t // self.p, self.p)
        for conv in self.convs:
            x = nn.functional.leaky_relu(conv(x), 0.1)
        return self.post(x)


class Escala(nn.Module):
    """Una rama del discriminador multi-escala: mira la onda completa."""

    def __init__(self):
        super().__init__()
        self.convs = nn.ModuleList([
            weight_norm(nn.Conv1d(1, 128, 15, 1, padding=7)),
            weight_norm(nn.Conv1d(128, 128, 41, 2, groups=4, padding=20)),
            weight_norm(nn.Conv1d(128, 256, 41, 2, groups=16, padding=20)),
            weight_norm(nn.Conv1d(256, 512, 41, 4, groups=16, padding=20)),
            weight_norm(nn.Conv1d(512, 1024, 41, 4, groups=16, padding=20)),
            weight_norm(nn.Conv1d(1024, 1024, 5, 1, padding=2)),
        ])
        self.post = weight_norm(nn.Conv1d(1024, 1, 3, 1, padding=1))

    def forward(self, x):
        for conv in self.convs:
            x = nn.functional.leaky_relu(conv(x), 0.1)
        return self.post(x)


class Discriminador(nn.Module):
    """El de HiFi-GAN, que es el que usa VITS: periodos 2,3,5,7,11 mas una escala."""

    def __init__(self):
        super().__init__()
        self.ramas = nn.ModuleList([Periodo(p) for p in (2, 3, 5, 7, 11)] + [Escala()])

    def forward(self, x):
        return [rama(x) for rama in self.ramas]


def medir(clips: int, epocas: int, batch: int, segundos: float, pasos: int,
          dispositivo: str) -> dict:
    from transformers import VitsModel, AutoTokenizer

    d = torch.device(dispositivo)
    generador = VitsModel.from_pretrained(TARJETA).to(d).train()
    tokenizador = AutoTokenizer.from_pretrained(TARJETA)
    discriminador = Discriminador().to(d).train()

    opt_g = torch.optim.AdamW(generador.parameters(), lr=2e-4)
    opt_d = torch.optim.AdamW(discriminador.parameters(), lr=2e-4)

    # Una frase del cuadernillo, del largo real que vamos a grabar.
    texto = "Sapa pusaq horapi huk pastillata upyanki"
    lote = tokenizador([texto] * batch, return_tensors="pt", padding=True).to(d)
    muestras = int(16000 * segundos)
    objetivo = torch.randn(batch, 1, muestras, device=d)

    tiempos_g, tiempos_d = [], []
    for paso in range(pasos + 2):          # dos pasos de calentamiento
        if d.type == "cuda":
            torch.cuda.synchronize()

        t0 = time.perf_counter()
        salida = generador(**lote).waveform
        if salida.dim() == 2:
            salida = salida.unsqueeze(1)
        n = min(salida.shape[-1], muestras)
        perdida_g = nn.functional.l1_loss(salida[..., :n], objetivo[..., :n])
        for falso in discriminador(salida[..., :n]):
            perdida_g = perdida_g + falso.pow(2).mean() * 0.01
        opt_g.zero_grad(set_to_none=True)
        perdida_g.backward()
        opt_g.step()
        if d.type == "cuda":
            torch.cuda.synchronize()
        t1 = time.perf_counter()

        perdida_d = sum(
            (real - 1).pow(2).mean() + falso.pow(2).mean()
            for real, falso in zip(discriminador(objetivo[..., :n]),
                                   discriminador(salida[..., :n].detach())))
        opt_d.zero_grad(set_to_none=True)
        perdida_d.backward()
        opt_d.step()
        if d.type == "cuda":
            torch.cuda.synchronize()
        t2 = time.perf_counter()

        if paso >= 2:
            tiempos_g.append(t1 - t0)
            tiempos_d.append(t2 - t1)

    g = sum(tiempos_g) / len(tiempos_g)
    disc = sum(tiempos_d) / len(tiempos_d)
    por_paso = g + disc
    pasos_totales = max(1, (clips // batch)) * epocas

    return {
        "maquina": f"{platform.machine()} {platform.system()}",
        "dispositivo": dispositivo,
        "gpu": torch.cuda.get_device_name(0) if dispositivo == "cuda" else None,
        "modelo": TARJETA,
        "parametros_generador_millones": round(
            sum(p.numel() for p in generador.parameters()) / 1e6, 1),
        "parametros_discriminador_millones": round(
            sum(p.numel() for p in discriminador.parameters()) / 1e6, 1),
        "batch": batch, "segundos_audio": segundos, "clips": clips, "epocas": epocas,
        "segundos_generador": round(g, 4),
        "segundos_discriminador": round(disc, 4),
        "segundos_por_paso": round(por_paso, 4),
        "pasos": pasos_totales,
        "minutos_estimados": round(pasos_totales * por_paso / 60, 1),
        "memoria_gb": (round(torch.cuda.max_memory_allocated() / 1e9, 2)
                       if dispositivo == "cuda" else None),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--clips", type=int, default=175, help="una sola voz: la del cuadernillo")
    p.add_argument("--epocas", type=int, default=200)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--segundos-audio", type=float, default=4.0)
    p.add_argument("--pasos", type=int, default=6)
    p.add_argument("--dispositivo", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--salida", default="reports/bench_tts.json")
    args = p.parse_args()

    r = medir(args.clips, args.epocas, args.batch, args.segundos_audio,
              args.pasos, args.dispositivo)
    print(f"{r['modelo']} en {r['dispositivo']}"
          + (f" ({r['gpu']})" if r["gpu"] else ""))
    print(f"  generador      {r['parametros_generador_millones']} M · "
          f"{r['segundos_generador']} s por paso")
    print(f"  discriminador  {r['parametros_discriminador_millones']} M · "
          f"{r['segundos_discriminador']} s por paso")
    print(f"  juntos         {r['segundos_por_paso']} s por paso de {r['batch']} clips")
    print(f"\n{r['clips']} clips x {r['epocas']} epocas = {r['pasos']} pasos "
          f"-> {r['minutos_estimados']} min ({round(r['minutos_estimados'] / 60, 1)} h)")
    if r["memoria_gb"]:
        print(f"memoria: {r['memoria_gb']} GB")

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    historial = json.loads(salida.read_text()) if salida.exists() else []
    historial.append(r)
    salida.write_text(json.dumps(historial, ensure_ascii=False, indent=1))
    print(f"guardado en {salida}")


if __name__ == "__main__":
    main()
