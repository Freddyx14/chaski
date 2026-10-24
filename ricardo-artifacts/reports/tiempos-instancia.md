# Tiempos medidos en la instancia — omniASR sobre quechua chanka

> Sábado 24 de octubre de 2026, ~01:30 PT. Instancia `mistiai-parque-arauco-tests`
> (`i-0d4df93dbf7907bfc`, `g5.xlarge`, `44.220.107.99`). Reproducible con
> `voz/instancia_setup.sh` y `voz/omni_humo.py`.

## La máquina

| | |
|---|---|
| GPU | **NVIDIA A10G, 23,028 MiB** — no los 40 GB que dice el SOT D7 |
| RAM | 15 GB · 4 vCPU |
| Disco raíz | 145 GB, estaba al **97%**. Se liberaron 28 GB de caché vieja de Hugging Face |
| Disco de trabajo | **229 GB en `/opt/dlami/nvme`**, NVMe efímero del g5 |
| Driver | 595.91.07 · CUDA disponible |

**`/opt/dlami/nvme` se borra cada vez que la instancia se apaga.** Por eso el entorno vive en
`voz/instancia_setup.sh`, dentro del repo, y no solo en la máquina.

## El modelo corre

`omniASR_LLM_300M`, lengua `quy_Latn`, que está entre las **1,672** que soporta Omnilingual.

| Medición | Valor |
|---|---|
| Cargar el modelo | **20.17 s** (una sola vez, al arrancar el servicio) |
| Transcribir 15.84 s de audio, primera pasada | **2.85 s** |
| Transcribir lo mismo, segunda pasada | **1.71 s** |
| Factor de tiempo real | **0.11** — nueve veces más rápido que escuchar el audio |
| Pico de memoria GPU | **3.41 GB** de 23 disponibles |

Con 3.41 GB de pico, en esta GPU entra incluso el modelo de 7B. Y 1.71 s por turno es una espera
aceptable para una consulta cara a cara, antes de sumar Claude y la voz de salida.

## Primer número de calidad, con su advertencia

Audio: las cinco frases de `muestras/mms-tts-quy/todas.wav`.

```
referencia  Allinllanchu mamáy · Imaynallam kachkanki taytáy · Runasimita rimankichu doctor ·
            Wawata suyarichkani jefelláy · Mamáy allillanmi
omniASR     allinllanchu mamaña imaynallam kachkanki taytáy runasimita rimankichu luctor
            wawata suyarichkani que fillay nunamáy allillanmi
```

| | |
|---|---|
| **WER** | **38.5%** |
| **CER** | **10.7%** |

**Este número no es la línea base del pitch y no debe presentarse como tal.** El audio es voz
sintética de MMS-TTS, no una persona. La línea base de verdad sale de voz humana: el corpus público
`josemercado/quechua-chanka-asr` primero, y después las grabaciones de las familias.

Lo que sí dice este número, y es mucho: **el modelo entiende chanka de verdad.** Acertó la estructura
entera de las cinco frases. Dónde falla es exactamente donde esperábamos: en los **préstamos del
castellano** — `doctor` → `luctor`, `jefelláy` → `que fillay` — y en los vocativos de respeto,
`mamáy` → `mamaña`.

Eso apunta directo a dónde conviene gastar el ajuste fino: nombres de medicamentos, títulos y números,
que son préstamos y son justo lo que no se puede equivocar en una posta.

## Lo que costó llegar aquí, para que no se repita

| Problema | Solución |
|---|---|
| `fairseq2n 0.6` exige `torch==2.8.0` exacto | Instalar 2.8.0 + `torchaudio` 2.8.0 desde el índice cu128 |
| `fairseq2` pide `numpy~=1.23`; `datasets` arrastra `pyarrow` que pide `numpy>=2` | No instalar `datasets`. `pyarrow==16.1.0`, `numpy==1.26.4` |
| El modelo se descargó al disco raíz y lo llenó | `fairseq2` **no respeta `HF_HOME`**: usa `~/.cache/fairseq2`. Se enlaza al NVMe |
| `pipe.transcribe(..., lang="quy_Latn")` falla | `lang` es una **lista**, una entrada por audio |

## Cuánto tarda el ajuste fino en la A10G (medido, 24-oct)

El mismo `voz/bench_finetune.py` que corrí en la laptop, corrido en la instancia. No es una
extrapolación por factores: es el costo por paso de esa GPU, con lotes del tamaño real.

Configuración: `ctc-300m` (el proxy medible de omniASR: misma familia wav2vec2 con CTC),
**700 clips** —175 frases × 4 personas—, 5 s por clip, batch 8.

| Épocas | Pasos | Tiempo |
|---|---|---|
| 3 | 264 | **1.4 min** |
| 10 | 880 | **4.5 min** |
| 30 | 2 640 | **14.0 min** |
| 60 | 5 280 | **27.8 min** |

Con el **encoder congelado**, 30 épocas bajan de 14.0 a **4.5 min**: 0.328 → 0.102 s por paso.

Memoria: **6.76 GB de 23**. Sobra para subir el batch si hiciera falta.

Batch, medido aparte a 3 épocas: 4 → 1.7 min, 8 → 1.4 min, 16 → 1.2 min. Ganancia marginal; con 700
clips el lote grande deja muy pocos pasos por época, así que batch 8 es el punto razonable.

**Conclusión: el entrenamiento no es el cuello de botella.** Una corrida completa son minutos, no
horas. Lo caro es grabar, y después la cantidad de configuraciones que probemos: el presupuesto real
es «cuántos experimentos × 14 min», no «cuánto tarda uno».

Lo que este número NO cubre: el ajuste de `mms-tts-quy`. Es VITS, con discriminador adversarial, y su
costo por paso no se parece al de un CTC. Hay que medirlo aparte en vez de extrapolar de aquí.
