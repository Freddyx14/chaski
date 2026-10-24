#!/bin/bash
# Lleva el orquestador a la instancia y lo deja corriendo en el puerto 8080.
#
# Reparto de puertos dentro de la instancia:
#   8000  servicio de voz (omniASR, mms-lid, mms-tts). Ya corre. No se toca.
#   8080  orquestador (este). Habla con el de voz por 127.0.0.1, sin red.
#
# El venv es APARTE del de los modelos a propósito: ese tiene torch==2.8.0 y
# numpy~=1.23 clavados por fairseq2, y basta un `pip install` encima para
# romperlo. Ya pasó una vez.
#
# El script no toca ngrok. Primero se prueba por túnel SSH, con el servicio
# local todavía sirviendo a Freddy; el cambio de ngrok es un paso aparte.
set -euo pipefail

MAQUINA="${CHASKI_MAQUINA:-ubuntu@44.220.107.99}"
LLAVE="${CHASKI_LLAVE:-$HOME/.ssh/id_rsa_aws}"
DESTINO=/opt/dlami/nvme/chaski/orquestador
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
ssh_() { ssh -i "$LLAVE" -o ConnectTimeout=15 -o BatchMode=yes "$MAQUINA" "$@"; }

echo "-- 1/5 creando carpetas"
ssh_ "mkdir -p $DESTINO/servicio $DESTINO/voz $DESTINO/chaski $DESTINO/rimay $DESTINO/datos /opt/dlami/nvme/chaski/design/chaski"

echo "-- 2/5 copiando código y datos"
rsync -az --delete -e "ssh -i $LLAVE -o BatchMode=yes" \
  --exclude '__pycache__' --exclude '*.pyc' --exclude 'url.json' \
  "$RAIZ/servicio/" "$MAQUINA:$DESTINO/servicio/"
rsync -az --delete -e "ssh -i $LLAVE -o BatchMode=yes" \
  --exclude '__pycache__' --exclude '*.pyc' \
  "$RAIZ/voz/" "$MAQUINA:$DESTINO/voz/"
rsync -az --delete -e "ssh -i $LLAVE -o BatchMode=yes" \
  --exclude '__pycache__' --exclude '*.pyc' \
  "$RAIZ/../app/chaski/" "$MAQUINA:$DESTINO/chaski/"
rsync -az --delete -e "ssh -i $LLAVE -o BatchMode=yes" \
  --exclude '__pycache__' --exclude '*.pyc' \
  "$RAIZ/../app/rimay/" "$MAQUINA:$DESTINO/rimay/"
rsync -az -e "ssh -i $LLAVE -o BatchMode=yes" "$RAIZ/datos/" "$MAQUINA:$DESTINO/datos/"
# El avatar de Chaski. `app.py` lo busca en ../design/chaski relativo a su cwd,
# así que del lado de la instancia cuelga de /opt/dlami/nvme/chaski/design.
# Copia de solo lectura del diseño de Freddy: no se edita aquí.
rsync -az -e "ssh -i $LLAVE -o BatchMode=yes" \
  "$RAIZ/../design/chaski/" "$MAQUINA:/opt/dlami/nvme/chaski/design/chaski/"

echo "-- 3/5 claves (nunca pasan por git)"
# Se manda por stdin, no como archivo en el comando, para que no quede en el
# historial de shell de ninguna de las dos máquinas.
ssh_ "cat > $DESTINO/.env && chmod 600 $DESTINO/.env" < "$RAIZ/.env"

echo "-- 4/5 venv del orquestador"
ssh_ "set -e
  cd $DESTINO
  test -d venv || python3 -m venv venv
  ./venv/bin/pip install --quiet --upgrade pip
  ./venv/bin/pip install --quiet fastapi uvicorn anthropic httpx python-multipart pydantic"

echo "-- 5/5 arrancando en :8080"
ssh_ "set -e
  cd $DESTINO
  # Matar por puerto, no por patrón: `pkill -f 'uvicorn servicio.app'` también
  # casa con la propia línea de comando de este SSH y se suicida el script.
  sudo fuser -k 8080/tcp 2>/dev/null || true
  sleep 1
  # setsid: si no, el servicio muere cuando se cierra esta sesión SSH.
  # CHASKI_VOZ apunta al servicio de voz dentro de la misma máquina.
  set -a; . ./.env; set +a
  export CHASKI_VOZ=http://127.0.0.1:8000
  export PYTHONPATH=$DESTINO
  setsid nohup ./venv/bin/uvicorn servicio.app:aplicacion --host 127.0.0.1 --port 8080 \
    > $DESTINO/orquestador.log 2>&1 < /dev/null &
  sleep 6
  curl -s -o /dev/null -w 'salud local en la instancia: %{http_code}\n' http://127.0.0.1:8080/salud"
