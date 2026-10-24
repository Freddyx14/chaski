#!/usr/bin/env python3
"""Download everything the families saved in the form: text + audio, one folder per person.

    EXPORT_TOKEN=... python3 form/scripts/bajar-datos.py            # -> data/formulario/
    EXPORT_TOKEN=... python3 form/scripts/bajar-datos.py --out DIR

Writes <out>/<persona>/<numero_global>.<ext> and <out>/manifest.jsonl (Ricardo's export rows plus
`audio_local`). Re-running skips audio already downloaded. `data/` is gitignored on purpose:
these are family voices, they never go into the repo. Never prints the token.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

BASE = os.environ.get("BASE", "https://rimay-datos.vercel.app")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/formulario")
    args = ap.parse_args()
    token = os.environ.get("EXPORT_TOKEN")
    if not token:
        print("set EXPORT_TOKEN (Vercel env of the rimay-datos project)", file=sys.stderr)
        return 2

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f"{BASE}/api/export?token={token}") as r:
        rows = [json.loads(line) for line in r.read().decode().splitlines() if line.strip()]

    bajados = 0
    for row in rows:
        row["audio_local"] = None
        if not row.get("audio"):
            continue
        ext = row["audio"].rsplit(".", 1)[-1].split("?")[0]
        destino = out / row["persona"] / f"{row['numero_global']:03d}.{ext}"
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not destino.exists():
            urllib.request.urlretrieve(row["audio"], destino)
            bajados += 1
        row["audio_local"] = str(destino.relative_to(out))

    with open(out / "manifest.jsonl", "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    personas = sorted({r["persona"] for r in rows})
    print(f"{len(rows)} filas · {len(personas)} personas ({', '.join(personas)}) · {bajados} audios nuevos -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
