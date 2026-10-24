#!/usr/bin/env bash
# Deja la instancia lista para omniASR. Reconstruye TODO: /opt/dlami/nvme es
# efimero y se borra cada vez que la instancia se apaga.
#
#   scp -i ~/.ssh/id_rsa_aws voz/instancia_setup.sh ubuntu@<ip>:~
#   ssh -i ~/.ssh/id_rsa_aws ubuntu@<ip> 'bash ~/instancia_setup.sh'
#
# Lo aprendido a la mala, en orden:
#   1. El disco raiz se llena: todo va al NVMe de 229 GB.
#   2. fairseq2n 0.6 exige torch==2.8.0 EXACTO. Con 2.6 revienta torchaudio.
#   3. fairseq2 pide numpy~=1.23; `datasets` arrastra pyarrow que pide numpy>=2.
#      Gana fairseq2: pyarrow queda en 16.1.0 y no se instala `datasets`.
#   4. fairseq2 NO respeta HF_HOME para sus pesos: usa ~/.cache/fairseq2.
#      Sin el enlace al NVMe, la descarga llena el disco raiz y falla.
set -uo pipefail
BASE=/opt/dlami/nvme/chaski
sudo mkdir -p "$BASE"/{hf,pip,datos,modelos,cache,tmp}
sudo chown -R ubuntu:ubuntu "$BASE"
mkdir -p ~/.cache && ln -sfn "$BASE/cache" ~/.cache/fairseq2

export PIP_CACHE_DIR=$BASE/pip HF_HOME=$BASE/hf TMPDIR=$BASE/tmp XDG_CACHE_HOME=$BASE/cache
python3 -m venv "$BASE/venv"
source "$BASE/venv/bin/activate"
pip install -q --upgrade pip
pip install -q numpy==1.26.4 "torch==2.8.0" "torchaudio==2.8.0" \
    --index-url https://download.pytorch.org/whl/cu128
pip install -q omnilingual-asr
pip install -q "pyarrow==16.1.0" "scipy==1.13.1" soundfile jiwer huggingface_hub

python - <<'PY'
import torch
from omnilingual_asr.models.wav2vec2_llama.lang_ids import supported_langs
print("torch", torch.__version__, "| cuda", torch.cuda.is_available(),
      "|", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "sin gpu")
print("quy_Latn soportado:", "quy_Latn" in list(supported_langs))
PY
echo "listo. Para correr:  source $BASE/venv/bin/activate && export HF_HOME=$BASE/hf XDG_CACHE_HOME=$BASE/cache"
