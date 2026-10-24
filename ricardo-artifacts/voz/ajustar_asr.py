# -*- coding: utf-8 -*-
"""Ajusta el reconocimiento de chanka con las voces de las familias.

Por que adaptadores y no un ajuste completo: tenemos 25 minutos de audio. Con
eso no se entrena una cabeza CTC desde cero —no alcanza para aprender el mapeo
sonido-letra— pero si alcanza para acomodar un modelo que YA reconoce quechua.
`facebook/mms-1b-all` trae un adaptador por idioma, `quy` entre ellos. Se
congela el codificador y se entrenan solo el adaptador y la capa de salida: unos
pocos millones de parametros en vez de mil millones.

Dos efectos de eso, los dos buenos para nosotros: aprende sin sobreajustar media
hora de audio, y el codificador congelado no guarda gradientes, asi que entra en
la GPU sin apagar el servicio de voz que esta usando Freddy.

El texto se normaliza con `voz.ortografia` antes de entrenar. Si no, la misma
palabra escrita de cuatro maneras le pide al modelo que adivine quien escribio
la linea, y gasta capacidad en eso.

Uso:
  python voz/ajustar_asr.py --epocas 12 --batch 4
  python voz/ajustar_asr.py --pasos-maximos 50 --epocas 1   # prueba de humo
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from voz.ortografia import distancia, normalizar

BASE = "facebook/mms-1b-all"
IDIOMA = "quy"
SALIDA = Path("modelos/asr-chanka")


class Clips(Dataset):
    """Lee el jsonl del corte y entrega audio crudo y el texto ya normalizado."""

    def __init__(self, ruta: str, procesador, limite_segundos: float = 20.0):
        import soundfile as sf

        self.sf = sf
        self.procesador = procesador
        self.limite = limite_segundos
        self.filas = []
        permitidos = set(procesador.tokenizer.get_vocab())
        for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            d = json.loads(linea)
            texto = normalizar(d["texto"])
            # Fuera lo que el tokenizador no sabe representar: si una letra no
            # esta en su vocabulario, CTC no puede producirla y solo ensucia la
            # perdida.
            texto = "".join(c for c in texto if c in permitidos or c == " ").strip()
            if texto and Path(d["audio"]).exists():
                self.filas.append({"audio": d["audio"], "texto": texto,
                                   "persona": d.get("persona", "?")})

    def __len__(self):
        return len(self.filas)

    def __getitem__(self, i):
        fila = self.filas[i]
        onda, frecuencia = self.sf.read(fila["audio"], dtype="float32")
        if onda.ndim > 1:
            onda = onda.mean(axis=1)
        onda = onda[: int(self.limite * frecuencia)]
        entradas = self.procesador(onda, sampling_rate=frecuencia).input_values[0]
        etiquetas = self.procesador(text=fila["texto"]).input_ids
        return {"input_values": entradas, "labels": etiquetas, "texto": fila["texto"]}


@dataclass
class Juntar:
    """Arma el lote. Las etiquetas se rellenan con -100: CTC ignora esas posiciones."""

    procesador: object

    def __call__(self, ejemplos):
        audio = self.procesador.pad(
            [{"input_values": e["input_values"]} for e in ejemplos],
            padding=True, return_tensors="pt")
        texto = self.procesador.tokenizer.pad(
            [{"input_ids": e["labels"]} for e in ejemplos],
            padding=True, return_tensors="pt")
        etiquetas = texto["input_ids"].masked_fill(texto.attention_mask.ne(1), -100)
        audio["labels"] = etiquetas
        return audio


def cargar(reiniciar_adaptador: bool = False):
    from transformers import AutoProcessor, Wav2Vec2ForCTC

    procesador = AutoProcessor.from_pretrained(BASE, target_lang=IDIOMA)
    modelo = Wav2Vec2ForCTC.from_pretrained(
        BASE, target_lang=IDIOMA, ignore_mismatched_sizes=True,
        attention_dropout=0.0, hidden_dropout=0.0, feat_proj_dropout=0.0,
        layerdrop=0.0, ctc_loss_reduction="mean",
        pad_token_id=procesador.tokenizer.pad_token_id)

    if reiniciar_adaptador:
        # Solo para un idioma que el modelo no traiga. Para `quy` arranca de lo
        # que ya sabe, que es justamente la ventaja.
        modelo.init_adapter_layers()

    modelo.freeze_base_model()
    adaptador = modelo._get_adapters()
    for parametro in adaptador.values():
        parametro.requires_grad = True
    return modelo, procesador, adaptador


def wer(referencias, hipotesis) -> float:
    err = tot = 0
    for r, h in zip(referencias, hipotesis):
        a, b = normalizar(r).split(), normalizar(h).split()
        err += distancia(a, b)
        tot += len(a)
    return err / tot if tot else 0.0


@torch.no_grad()
def evaluar(modelo, procesador, cargador, dispositivo) -> tuple:
    modelo.eval()
    refs, hips, perdidas = [], [], []
    for lote in cargador:
        etiquetas = lote.pop("labels").to(dispositivo)
        lote = {k: v.to(dispositivo) for k, v in lote.items()}
        salida = modelo(**lote, labels=etiquetas)
        perdidas.append(float(salida.loss))
        ids = torch.argmax(salida.logits, dim=-1)
        hips.extend(procesador.batch_decode(ids))
        etiquetas[etiquetas == -100] = procesador.tokenizer.pad_token_id
        refs.extend(procesador.batch_decode(etiquetas, group_tokens=False))
    modelo.train()
    return wer(refs, hips), float(np.mean(perdidas)), list(zip(refs[:3], hips[:3]))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--entrenamiento", default="datos/corpus/entrenamiento.jsonl")
    p.add_argument("--validacion", default="datos/corpus/validacion.jsonl")
    p.add_argument("--epocas", type=int, default=12)
    p.add_argument("--batch", type=int, default=2)
    p.add_argument("--acumular", type=int, default=2,
                   help="lotes que se suman antes de actualizar; batch x acumular "
                        "es el lote efectivo. Sirve para no quedarse sin memoria "
                        "sin cambiar el tamano de lote que ve el optimizador")
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--cada", type=int, default=50, help="pasos entre checkpoints")
    p.add_argument("--pasos-maximos", type=int, default=0, help="0 = sin tope")
    p.add_argument("--reiniciar-adaptador", action="store_true")
    p.add_argument("--salida", default=str(SALIDA))
    args = p.parse_args()

    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    modelo, procesador, adaptador = cargar(args.reiniciar_adaptador)
    modelo.to(dispositivo).train()

    entrenables = sum(p_.numel() for p_ in modelo.parameters() if p_.requires_grad)
    totales = sum(p_.numel() for p_ in modelo.parameters())
    print(f"{BASE} · {IDIOMA}")
    print(f"  entrenables {entrenables/1e6:.1f} M de {totales/1e6:.0f} M "
          f"({entrenables/totales:.1%})")

    juntar = Juntar(procesador)
    tren = Clips(args.entrenamiento, procesador)
    val = Clips(args.validacion, procesador)
    print(f"  {len(tren)} clips de entrenamiento · {len(val)} de validacion")

    cargador = DataLoader(tren, batch_size=args.batch, shuffle=True, collate_fn=juntar)
    cargador_val = DataLoader(val, batch_size=args.batch, collate_fn=juntar)

    optimizador = torch.optim.AdamW(
        [p_ for p_ in modelo.parameters() if p_.requires_grad], lr=args.lr)
    pasos_totales = (len(cargador) // args.acumular) * args.epocas
    if args.pasos_maximos:
        pasos_totales = min(pasos_totales, args.pasos_maximos)
    plan = torch.optim.lr_scheduler.OneCycleLR(
        optimizador, max_lr=args.lr, total_steps=max(1, pasos_totales), pct_start=0.1)

    carpeta = Path(args.salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    historial, paso, micro, mejor = [], 0, 0, 1e9
    t0 = time.perf_counter()

    for epoca in range(args.epocas):
        for lote in cargador:
            etiquetas = lote.pop("labels").to(dispositivo)
            lote = {k: v.to(dispositivo) for k, v in lote.items()}
            perdida = modelo(**lote, labels=etiquetas).loss / args.acumular
            perdida.backward()
            micro += 1
            if micro % args.acumular:
                continue
            torch.nn.utils.clip_grad_norm_(
                [p_ for p_ in modelo.parameters() if p_.requires_grad], 1.0)
            optimizador.step()
            plan.step()
            optimizador.zero_grad(set_to_none=True)
            paso += 1

            if paso % args.cada == 0 or paso == pasos_totales:
                w, perdida_val, muestras = evaluar(modelo, procesador, cargador_val, dispositivo)
                minutos = (time.perf_counter() - t0) / 60
                print(f"  paso {paso:>4}/{pasos_totales}  perdida {perdida.item()*args.acumular:.3f}  "
                      f"val {perdida_val:.3f}  WER {w:.1%}  {minutos:.1f} min", flush=True)
                for r, h in muestras[:1]:
                    print(f"      ref {r[:54]}\n      oyo {h[:54]}", flush=True)
                historial.append({"paso": paso, "wer_validacion": round(w, 4),
                                  "perdida_validacion": round(perdida_val, 4),
                                  "minutos": round(minutos, 1)})
                # Se guarda SOLO el adaptador: son megabytes, no gigas, y es lo
                # unico que cambia.
                torch.save({k: v.cpu() for k, v in modelo._get_adapters().items()},
                           carpeta / f"adaptador_paso{paso}.pt")
                if w < mejor:
                    mejor = w
                    torch.save({k: v.cpu() for k, v in modelo._get_adapters().items()},
                               carpeta / "adaptador_mejor.pt")
                    (carpeta / "mejor.json").write_text(
                        json.dumps({"paso": paso, "wer_validacion": round(w, 4)}, indent=1))

            if args.pasos_maximos and paso >= args.pasos_maximos:
                break
        if args.pasos_maximos and paso >= args.pasos_maximos:
            break

    (carpeta / "historial.json").write_text(
        json.dumps(historial, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nmejor WER de validacion: {mejor:.1%}")
    print(f"adaptadores en {carpeta}/")


if __name__ == "__main__":
    main()
