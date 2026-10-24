#!/bin/sh
# Copies the canonical phrase list into the app. Run after Ricardo updates frases.json.
set -e
cd "$(dirname "$0")/.."
cp ../ricardo-artifacts/datos/frases/frases.json src/frases/frases.json
echo "frases.json copied"
