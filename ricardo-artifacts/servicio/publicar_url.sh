#!/usr/bin/env bash
# Levanta el tunel publico y deja la URL en el repo, para que Freddy no tenga
# que preguntarla. Si la URL cambia, se commitea y se empuja sola.
#
#   bash servicio/publicar_url.sh            # relanza y publica
#   bash servicio/publicar_url.sh --revisar  # solo mira si sigue viva
set -uo pipefail
cd "$(dirname "$0")/.."              # ricardo-artifacts
ARCHIVO=servicio/url.json
DOC=servicio/PARA-FREDDY.md
LOG=/tmp/ngrok.log
# ngrok da una URL FIJA por cuenta: sobrevive reinicios. cloudflared daba una
# distinta cada vez. El authtoken ya esta en ~/.../ngrok.yml.

url_actual() { [ -f "$ARCHIVO" ] && python3 -c "import json,sys;print(json.load(open('$ARCHIVO'))['url'])" 2>/dev/null; }

if [ "${1:-}" = "--revisar" ]; then
  URL=$(url_actual)
  if [ -z "$URL" ]; then echo "no hay URL publicada"; exit 1; fi
  if curl -s --max-time 15 "$URL/salud" > /dev/null; then
    echo "viva: $URL"; exit 0
  fi
  echo "CAIDA: $URL — relanza sin --revisar"; exit 1
fi

# el tunel SSH a la GPU tiene que estar antes que nada
if ! curl -s --max-time 10 http://127.0.0.1:8010/salud > /dev/null; then
  echo "AVISO: la GPU no responde en 8010. Abre el tunel SSH primero:"
  echo "  ssh -i ~/.ssh/id_rsa_aws -N -L 8010:localhost:8000 ubuntu@<ip>"
fi
if ! curl -s --max-time 10 http://127.0.0.1:8000/salud > /dev/null; then
  echo "ERROR: el servicio local no responde en 8000. Arrancalo primero."; exit 1
fi

ANTERIOR=$(url_actual)
pkill -f "ngrok http" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 2
nohup ngrok http 8000 --log="$LOG" > /dev/null 2>&1 &

# ngrok publica sus tuneles en una API local; es mas fiable que leer el log.
URL=""
for _ in $(seq 1 20); do
  sleep 2
  URL=$(curl -s --max-time 5 http://127.0.0.1:4040/api/tunnels 2>/dev/null \
        | python3 -c "import json,sys;t=json.load(sys.stdin).get('tunnels');print(t[0]['public_url'] if t else '')" 2>/dev/null)
  [ -n "$URL" ] && break
done
if [ -z "$URL" ]; then echo "ERROR: ngrok no dio URL. Mira $LOG"; exit 1; fi

# cloudflared tarda unos segundos en propagar el nombre
VIVA=0
for _ in $(seq 1 20); do
  if [ "$(curl -s --max-time 20 -o /dev/null -w "%{http_code}" "$URL/salud")" = "200" ]; then
    VIVA=1; break
  fi
  sleep 6
done
if [ "$VIVA" != "1" ]; then
  echo "ERROR: la URL no respondio en 2 minutos: $URL"; exit 1
fi

CUANDO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '{\n "url": "%s",\n "publicada": "%s",\n "nota": "ngrok, fija por cuenta: no cambia entre reinicios"\n}\n' \
  "$URL" "$CUANDO" > "$ARCHIVO"
python3 - "$URL" "$DOC" <<'PY'
import re, sys
url, doc = sys.argv[1], sys.argv[2]
texto = open(doc, encoding="utf-8").read()
texto = re.sub(r"https://[a-z0-9-]+\.trycloudflare\.com", url, texto)
open(doc, "w", encoding="utf-8").write(texto)
PY

if [ "$ANTERIOR" = "$URL" ]; then
  echo "misma URL: $URL"; exit 0
fi

cd ..
git add ricardo-artifacts/"$ARCHIVO" ricardo-artifacts/"$DOC"
git commit -q -m "chore: new public URL for the voice models

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>" 2>/dev/null
git fetch -q origin && git merge -q --no-edit origin/main 2>/dev/null
git push -q origin main 2>/dev/null && echo "publicada y empujada: $URL" || echo "publicada local (el push fallo): $URL"
[ -n "$ANTERIOR" ] && echo "la anterior era: $ANTERIOR"
