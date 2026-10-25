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

echo "-- 1/6 creando carpetas"
ssh_ "mkdir -p $DESTINO/servicio $DESTINO/voz $DESTINO/chaski $DESTINO/rimay $DESTINO/datos $DESTINO/memoria /opt/dlami/nvme/chaski/design/chaski"

# /opt/dlami/nvme es efimero: se borra al parar la instancia. El etiquetador
# escribe ahi las grabaciones nuevas, asi que bajarlas ANTES de copiar nada es
# lo primero que hace el despliegue. Si no, el rsync de ida las pisa con la
# copia vieja de la laptop y se pierde lo grabado.
# `--update` en las dos direcciones: rsync solo pisa un archivo si el de origen
# es MAS NUEVO. Hace falta porque los manifiestos los escriben los dos lados
# —aqui al importar del formulario, alla al corregir en /corregir— y sin esa
# bandera la bajada revivia la copia vieja de la instancia encima de lo recien
# importado. Paso exactamente eso: 80 clips de p24 volvieron a ser 36.
echo "-- 2/6 trayendo de vuelta lo que se grabo en la instancia"
if ssh_ "test -d $DESTINO/datos/crudo" 2>/dev/null; then
  rsync -az --update -e "ssh -i $LLAVE -o BatchMode=yes" \
    "$MAQUINA:$DESTINO/datos/crudo/" "$RAIZ/datos/crudo/"
  rsync -az --update -e "ssh -i $LLAVE -o BatchMode=yes" \
    "$MAQUINA:$DESTINO/datos/corpus/" "$RAIZ/datos/corpus/" 2>/dev/null || true
  echo "   $(find "$RAIZ/datos/crudo" -name '*.wav' | wc -l | tr -d ' ') wav en la laptop"
else
  echo "   todavia no hay nada grabado alla"
fi

echo "-- 3/6 copiando código y datos"
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
# Sin --delete y con --update, por lo mismo que la bajada.
rsync -az --update -e "ssh -i $LLAVE -o BatchMode=yes" "$RAIZ/datos/" "$MAQUINA:$DESTINO/datos/"
# Los audios del modo emergencia los sirve el orquestador, asi que viajan con el.
rsync -az --update -e "ssh -i $LLAVE -o BatchMode=yes" \
  "$RAIZ/reports/emergencia/" "$MAQUINA:$DESTINO/reports/emergencia/" 2>/dev/null || true
# El avatar de Chaski. `app.py` lo busca en ../design/chaski relativo a su cwd,
# así que del lado de la instancia cuelga de /opt/dlami/nvme/chaski/design.
# Copia de solo lectura del diseño de Freddy: no se edita aquí.
rsync -az -e "ssh -i $LLAVE -o BatchMode=yes" \
  "$RAIZ/../design/chaski/" "$MAQUINA:/opt/dlami/nvme/chaski/design/chaski/"

echo "-- 4/6 claves (nunca pasan por git)"
# Se manda por stdin, no como archivo en el comando, para que no quede en el
# historial de shell de ninguna de las dos máquinas.
ssh_ "cat > $DESTINO/.env && chmod 600 $DESTINO/.env" < "$RAIZ/.env"

echo "-- 5/6 venv del orquestador"
ssh_ "set -e
  cd $DESTINO
  test -d venv || python3 -m venv venv
  ./venv/bin/pip install --quiet --upgrade pip
  ./venv/bin/pip install --quiet fastapi uvicorn anthropic httpx python-multipart pydantic"

echo "-- 6/6 arrancando en :8080"
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
  # D43: traduce Claude Sonnet 5 con esfuerzo medio. Esta variable va VACIA a
  # proposito; `motor=nllb` en la ruta sigue funcionando para el modo sin
  # conexion, y no depende de ella.
  export CHASKI_NLLB_URL=
  export CHASKI_MODELO_PRINCIPAL=claude-opus-5
  export CHASKI_MODELO_CRITICO=claude-sonnet-5
  export CHASKI_PENSAR_TRADUCIR=medium
  export CHASKI_TRADUCIR_ANTICIPADO=1
  # D44, memoria automatica. Vive FUERA de la carpeta chaski, que es lo que
  # este script sincroniza: si quedara adentro, cada despliegue la borraria.
  mkdir -p $DESTINO/memoria
  # La voz de Chaski: quechua con la de la mama de Freddy (SOT F5), castellano
  # con Cartesia. p24 queda como respaldo si la primera falla en vivo.
  export CHASKI_VOZ_QUY=mama_freddy
  export CHASKI_VOZ_ES=3597a26f-80ef-4bd5-8101-9699bc764917
  export CHASKI_MEMORIA_AUTO=1
  export CHASKI_MEMORIA_RUTA=$DESTINO/memoria/memoria_auto.jsonl
  export PYTHONPATH=$DESTINO
  setsid nohup ./venv/bin/uvicorn servicio.app:aplicacion --host 127.0.0.1 --port 8080 \
    > $DESTINO/orquestador.log 2>&1 < /dev/null &
  sleep 6
  curl -s -o /dev/null -w 'salud local en la instancia: %{http_code}\n' http://127.0.0.1:8080/salud"
