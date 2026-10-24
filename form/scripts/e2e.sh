#!/usr/bin/env bash
# End-to-end check against a deployed form: creates a throwaway participant, saves one
# answer with text + audio, proves both landed (export row + audio bytes match), re-saves
# without audio to prove the old audio is kept, then deletes the participant.
#
#   BASE=https://rimay-datos.vercel.app EXPORT_TOKEN=... ./scripts/e2e.sh
#
# Exits non-zero on the first failed check. Never prints the token.
set -euo pipefail

BASE="${BASE:-https://rimay-datos.vercel.app}"
: "${EXPORT_TOKEN:?set EXPORT_TOKEN (vercel env pull)}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
pass() { printf '  ok  %s\n' "$1"; }
fail() { printf '  FAIL %s\n' "$1"; exit 1; }

# 1 s of 440 Hz tone, 16 kHz mono 16-bit WAV, stdlib only.
python3 - "$TMP/tono.wav" <<'PY'
import math, struct, sys, wave
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    w.writeframes(b"".join(struct.pack("<h", int(8000*math.sin(2*math.pi*440*i/16000))) for i in range(16000)))
PY

echo "1. participant without consent is refused"
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/participantes" \
  -H 'content-type: application/json' -d '{"consentimiento":false}')
[ "$code" = 400 ] && pass "400 without consent" || fail "expected 400, got $code"

echo "2. create participant"
curl -sf -X POST "$BASE/api/participantes" -H 'content-type: application/json' \
  -d '{"consentimiento":true,"sabe_escribir_quechua":true,"nombre":"PRUEBA-E2E"}' > "$TMP/p.json" \
  || fail "create participant"
PID=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["id"])' "$TMP/p.json")
COD=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["codigo"])' "$TMP/p.json")
pass "participant $COD"
cleanup() { curl -s -o /dev/null -X DELETE "$BASE/api/participantes/$PID?token=$EXPORT_TOKEN"; rm -rf "$TMP"; }
trap cleanup EXIT

echo "3. save text + audio for phrase 1"
TEXTO="prueba e2e ñañez $(date +%s)"
curl -sf -X POST "$BASE/api/respuestas" -F participante_id="$PID" -F numero_global=1 \
  -F quechua_texto="$TEXTO" -F audio_segundos=1 -F "audio=@$TMP/tono.wav;type=audio/wav" > "$TMP/r.json" \
  || fail "save answer"
AURL=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["audio_url"] or "")' "$TMP/r.json")
[ -n "$AURL" ] && pass "audio stored" || fail "no audio_url returned"

echo "3b. resume by code returns the same participant with its saved answer"
curl -sf "$BASE/api/retomar?codigo=$COD" > "$TMP/ret.json" || fail "resume by code"
python3 - "$TMP/ret.json" "$PID" <<'PY' || fail "resume payload"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["id"] == sys.argv[2], d["id"]
assert [r["numero_global"] for r in d["respuestas"]] == [1], d["respuestas"]
PY
code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/retomar?codigo=p999999")
[ "$code" = 404 ] && pass "resume works, unknown code is 404" || fail "unknown code gave $code"

echo "4. audio bytes round-trip"
curl -sf "$AURL" -o "$TMP/back.wav" || fail "download audio"
cmp -s "$TMP/tono.wav" "$TMP/back.wav" && pass "downloaded audio == uploaded" || fail "audio differs"

echo "5. export has the row with the text"
curl -sf "$BASE/api/export?token=$EXPORT_TOKEN" > "$TMP/x.jsonl" || fail "export"
python3 - "$TMP/x.jsonl" "$COD" "$TEXTO" "$AURL" <<'PY' || fail "export row"
import json, sys
path, cod, texto, aurl = sys.argv[1:]
rows = [json.loads(l) for l in open(path) if l.strip()]
mine = [r for r in rows if r["persona"] == cod and r["numero_global"] == 1]
assert len(mine) == 1, f"expected 1 row, got {len(mine)}"
r = mine[0]
# Block E phrases carry their own Quechua; phrase 1 is a written one, so the text must be ours.
assert r["transcripcion"] == texto, r["transcripcion"]
assert r["audio"] == aurl and r["consentimiento"] is True
PY
pass "export row matches text + audio"

echo "6. re-save text only keeps the old audio"
curl -sf -X POST "$BASE/api/respuestas" -F participante_id="$PID" -F numero_global=1 \
  -F quechua_texto="$TEXTO editado" > "$TMP/r2.json" || fail "re-save"
python3 - "$TMP/r2.json" "$AURL" "$TEXTO editado" <<'PY' || fail "re-save kept audio"
import json, sys
r = json.load(open(sys.argv[1]))
assert r["audio_url"] == sys.argv[2], r
assert r["quechua_texto"] == sys.argv[3], r
PY
pass "text updated, audio kept"

echo "7. delete participant removes the rows"
curl -sf -X DELETE "$BASE/api/participantes/$PID?token=$EXPORT_TOKEN" > /dev/null || fail "delete"
curl -sf "$BASE/api/export?token=$EXPORT_TOKEN" | grep -q "\"persona\":\"$COD\"" && fail "rows survived delete" || pass "rows gone"
trap 'rm -rf "$TMP"' EXIT

echo "ALL PASSED"
