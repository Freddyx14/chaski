# -*- coding: utf-8 -*-
"""Compara traductores sobre frases que ninguno pudo haber visto.

El problema de medir con `rosettia-chanka-data`: los modelos chanka publicados
se entrenaron con eso. `Thermostatic/rosettia-chanka-4b` lo lleva en el nombre.
Medirlos ahi les regala el examen.

Asi que se mide con las 62 frases que las familias tradujeron el 24-oct. Son de
hoy y no estan publicadas: nadie las vio.

Y con VARIAS referencias por frase, una por persona. Cuando cinco hablantes
traducen distinto y las cinco estan bien, exigir una sola respuesta mide
dialecto, no calidad.

Uso:
  python voz/comparar_traductores.py --modelos facebook/nllb-200-distilled-1.3B …
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

FAMILIAS = Path("datos/frases/evaluacion_familias.json")
ROSETTIA = Path("datos/frases/frases.json")


def cargar(cual: str):
    """Los dos conjuntos, y la diferencia entre ellos es el dato.

    `familias` son 62 frases traducidas hoy por las familias, con varias
    referencias. Nadie las ha visto.

    `rosettia` son las 100 verificadas de `rosettia-chanka-data`, que es
    justamente el corpus con el que se entrenaron los modelos chanka
    publicados. Un modelo que puntue mucho mejor aqui que alla no es mejor
    traductor: es que ya habia visto estas.
    """
    if cual == "familias":
        d = json.loads(FAMILIAS.read_text(encoding="utf-8"))
        fuentes = [p["castellano"] for p in d["pares"]]
        ancho = max(len(p["referencias"]) for p in d["pares"])
        columnas = [[(p["referencias"][i] if i < len(p["referencias"])
                      else p["referencias"][0]) for p in d["pares"]] for i in range(ancho)]
        return fuentes, columnas, d["pares"]

    d = json.loads(ROSETTIA.read_text(encoding="utf-8"))["verificadas"][:100]
    fuentes = [f["castellano"] for f in d]
    return fuentes, [[f["chanka"] for f in d]], [{"referencias": [f["chanka"]]} for f in d]


def con_nllb(tarjeta, fuentes):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(tarjeta, src_lang="spa_Latn")
    m = AutoModelForSeq2SeqLM.from_pretrained(tarjeta, torch_dtype=torch.float16).cuda().eval()
    forzado = tok.convert_tokens_to_ids("quy_Latn")
    salida = []
    for i in range(0, len(fuentes), 8):
        x = tok(fuentes[i:i + 8], return_tensors="pt", padding=True,
                truncation=True, max_length=128).to("cuda")
        with torch.no_grad():
            y = m.generate(**x, forced_bos_token_id=forzado, max_new_tokens=96, num_beams=4)
        salida.extend(tok.batch_decode(y, skip_special_tokens=True))
    del m
    torch.cuda.empty_cache()
    return salida


# El prompt exacto de la tarjeta de rosettia-chanka. Un modelo instruido
# responde distinto segun como se le pida, asi que se usa el suyo y no uno
# inventado: medir con otro prompt seria medir nuestro prompt, no el modelo.
SISTEMA_CHANKA = "Eres un traductor profesional español-quechua chanka."
PETICION_CHANKA = (
    "Traduce del español al quechua chanka. Usa una traducción directa, "
    "natural y fiel. Conserva nombres, números y entidades; evita copiar "
    "el español salvo cuando sea necesario.\n\nEspañol: {texto}")


def con_llm(tarjeta, fuentes, base=""):
    """Un LLM instruido, con o sin LoRA encima."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    origen = base or tarjeta
    tok = AutoTokenizer.from_pretrained(origen)
    m = AutoModelForCausalLM.from_pretrained(origen, dtype=torch.bfloat16,
                                             device_map="auto")
    if base:
        from peft import PeftModel
        m = PeftModel.from_pretrained(m, tarjeta)
    m.eval()
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    salida = []
    for texto in fuentes:
        mensajes = [{"role": "system", "content": SISTEMA_CHANKA},
                    {"role": "user", "content": PETICION_CHANKA.format(texto=texto)}]
        try:
            prompt = tok.apply_chat_template(mensajes, tokenize=False,
                                             add_generation_prompt=True,
                                             enable_thinking=False)
        except TypeError:
            prompt = tok.apply_chat_template(mensajes, tokenize=False,
                                             add_generation_prompt=True)
        x = tok(prompt, return_tensors="pt").to(m.device)
        with torch.no_grad():
            y = m.generate(**x, max_new_tokens=96, do_sample=False,
                           pad_token_id=tok.pad_token_id)
        texto_salida = tok.decode(y[0, x["input_ids"].shape[-1]:],
                                  skip_special_tokens=True).strip()
        salida.append(texto_salida.split("\n")[0].strip())
    del m
    torch.cuda.empty_cache()
    return salida


def con_claude(fuentes):
    import os
    from concurrent.futures import ThreadPoolExecutor

    import anthropic
    cli = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sistema = [{"type": "text",
                "text": "Traduces del castellano al quechua chanka de Ayacucho. "
                        "Respondes solo con la traducción, una línea.",
                "cache_control": {"type": "ephemeral"}}]

    def uno(t):
        r = cli.messages.create(model="claude-sonnet-5", max_tokens=400, system=sistema,
                                thinking={"type": "disabled"},
                                messages=[{"role": "user", "content": t}])
        return [b for b in r.content if b.type == "text"][-1].text.strip()

    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(uno, fuentes))


def main() -> None:
    import sacrebleu

    p = argparse.ArgumentParser()
    p.add_argument("--modelos", nargs="+", required=True,
                   help="tarjeta, o tarjeta@base si es un LoRA, o 'claude'")
    p.add_argument("--salida", default="reports/traductores.json")
    p.add_argument("--conjuntos", nargs="+", default=["familias", "rosettia"])
    args = p.parse_args()

    chrf = sacrebleu.CHRF(word_order=2)
    todo = {}
    for cual in args.conjuntos:
        fuentes, referencias, pares = cargar(cual)
        refs = sum(len(x["referencias"]) for x in pares) / len(pares)
        print(f"\n=== {cual}: {len(fuentes)} frases · {refs:.1f} referencias ===")
        todo[cual] = correr(args.modelos, fuentes, referencias, chrf, sacrebleu)

    if len(todo) > 1 and all(todo.values()):
        print(f"\n{'modelo':<30}{'familias':>10}{'rosettia':>10}{'diferencia':>12}")
        for nombre in todo[args.conjuntos[0]]:
            a = todo[args.conjuntos[0]].get(nombre, {}).get("chrf2")
            b = todo[args.conjuntos[1]].get(nombre, {}).get("chrf2")
            if a is None or b is None:
                continue
            print(f"{nombre:<30}{a:>10.2f}{b:>10.2f}{b-a:>+12.2f}")
        print("\nUna diferencia grande a favor de rosettia delata que el modelo")
        print("vio ese corpus al entrenarse. Las familias son de hoy: nadie las vio.")

    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(json.dumps(todo, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
    print(f"\nguardado en {args.salida}")


def correr(modelos, fuentes, referencias, chrf, sacrebleu):
    resultados, salidas = {}, {}
    for entrada in modelos:
        nombre = entrada.split("@")[0].split("/")[-1]
        t0 = time.perf_counter()
        try:
            if entrada == "claude":
                hip = con_claude(fuentes)
            elif "nllb" in entrada.lower():
                hip = con_nllb(entrada, fuentes)
            else:
                tarjeta, _, base = entrada.partition("@")
                hip = con_llm(tarjeta, fuentes, base)
        except Exception as e:
            print(f"  {nombre:<34}falló: {type(e).__name__}: {str(e)[:60]}")
            continue
        seg = time.perf_counter() - t0
        salidas[nombre] = hip
        resultados[nombre] = {
            "chrf2": round(chrf.corpus_score(hip, referencias).score, 2),
            "bleu": round(sacrebleu.BLEU().corpus_score(hip, referencias).score, 2),
            "ms_por_frase": round(seg / len(fuentes) * 1000)}
        r = resultados[nombre]
        print(f"  {nombre:<34}chrF++ {r['chrf2']:>6}  BLEU {r['bleu']:>6}  "
              f"{r['ms_por_frase']:>6} ms")
    return resultados


if __name__ == "__main__":
    main()
