"""Trae al corpus lo que la familia mandó por el formulario.

El formulario (Next.js + Neon + Vercel Blob, carpeta `form/`) exporta un JSONL
con una línea por frase: el castellano que vio, el quechua que ESCRIBIÓ y el
audio leyéndolo. Eso ya viene emparejado, así que aquí no hay que partir nada
por silencios ni adivinar números: solo bajar el audio, normalizarlo y armar el
manifiesto.

Formato esperado (ver CONTRATO.md §7):

  {"persona": "p1", "numero": 3,
   "castellano": "Tómela con agua, no con té",
   "quechua_escrito": "Yakuwan upyay, mana tewan",
   "audio_url": "https://...blob.../p1-003.webm",
   "segundos": 4.2, "consentimiento": true}

Uso:
  PYTHONPATH=. uv run --with httpx python voz/importar_formulario.py export.jsonl
  PYTHONPATH=. uv run --with httpx python voz/importar_formulario.py https://.../export.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import httpx

from voz.contrato import Grabacion, escribir_manifiesto
from voz.ingesta import convertir

RAIZ = Path("datos/crudo")
# El formulario desplegado usa `audio`, `transcripcion` y `numero_global`; el
# contrato original decia `audio_url`, `quechua_escrito` y `numero`. Se aceptan
# las dos formas: el importador es liberal con lo que recibe.
ALIAS = {
    "audio": ("audio_url", "audio", "url", "blob_url"),
    "texto": ("quechua_escrito", "transcripcion", "quechua", "quechua_texto"),
    "numero": ("numero_global", "numero", "n"),
    "bloque": ("parte", "bloque"),
    "castellano": ("castellano", "frase_castellano"),
    "segundos": ("segundos", "audio_segundos", "duracion"),
}


def campo(fila: dict, cual: str):
    for nombre in ALIAS[cual]:
        valor = fila.get(nombre)
        if valor not in (None, ""):
            return valor
    return None


def leer_lineas(origen: str) -> list[dict]:
    if origen.startswith(("http://", "https://")):
        texto = httpx.get(origen, timeout=120, follow_redirects=True).text
    else:
        texto = Path(origen).read_text(encoding="utf-8")
    filas = []
    for n, linea in enumerate(texto.splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        try:
            filas.append(json.loads(linea))
        except json.JSONDecodeError as e:
            print(f"  línea {n} no es JSON, se salta: {e}", file=sys.stderr)
    return filas


def bajar(url: str, cliente: httpx.Client) -> bytes:
    r = cliente.get(url, timeout=120, follow_redirects=True)
    r.raise_for_status()
    return r.content


def parte_de(numero: int) -> str:
    from servicio.corpus import parte_de as calcular
    return calcular(numero) or "C"


def importar(origen: str, solo: str = "") -> dict:
    filas = leer_lineas(origen)
    por_persona: dict[str, list[Grabacion]] = {}
    saltadas, sin_consentimiento, bajadas, rotas = 0, 0, 0, 0

    with httpx.Client() as cliente:
        for fila in filas:
            url = campo(fila, "audio")
            numero_crudo = campo(fila, "numero")
            if not fila.get("persona") or numero_crudo is None or not url:
                saltadas += 1
                continue
            persona = str(fila["persona"]).strip()
            if solo and persona != solo:
                continue
            if not fila.get("consentimiento", False):
                sin_consentimiento += 1
                continue

            numero = int(numero_crudo)
            bloque = campo(fila, "bloque") or parte_de(numero)
            carpeta = RAIZ / persona
            carpeta.mkdir(parents=True, exist_ok=True)
            destino = carpeta / f"{persona}_{bloque}_{numero:03d}.wav"

            try:
                datos = bajar(url, cliente)
            except Exception as e:
                print(f"  {persona} #{numero}: no se pudo bajar el audio ({str(e)[:60]})",
                      file=sys.stderr)
                saltadas += 1
                continue
            crudo = tempfile.NamedTemporaryFile(
                suffix=Path(str(url).split("?")[0]).suffix or ".webm", delete=False)
            crudo.write(datos)
            crudo.close()
            try:
                segundos = convertir(crudo.name, destino)
            except Exception as e:
                # Una grabacion que se corto a la mitad deja un webm que ffmpeg
                # no puede leer. Antes eso tiraba la importacion entera y se
                # perdian las cuatrocientas buenas por una mala.
                print(f"  {persona} #{numero}: el audio no se pudo convertir "
                      f"({str(e)[:50]}); se salta", file=sys.stderr)
                destino.unlink(missing_ok=True)
                rotas += 1
                continue
            finally:
                Path(crudo.name).unlink(missing_ok=True)
            bajadas += 1

            por_persona.setdefault(persona, []).append(Grabacion(
                persona=persona, bloque=bloque, numero=numero, audio=str(destino),
                # Lo que la persona ESCRIBIO es la verdad de referencia que ella
                # misma declaro. El etiquetador sirve para comprobar que el audio
                # dice eso, no para inventarlo de cero.
                transcripcion=str(campo(fila, "texto") or "").strip(),
                castellano=str(campo(fila, "castellano") or "").strip(),
                segundos=round(float(campo(fila, "segundos") or segundos), 2),
                consentimiento=True))

    for persona, grabaciones in por_persona.items():
        grabaciones.sort(key=lambda g: g.numero)
        escribir_manifiesto(RAIZ / persona / "manifiesto.jsonl", grabaciones,
                            cabecera="del formulario: el texto lo escribio la propia persona")

    return {"personas": {p: len(g) for p, g in por_persona.items()},
            "audios": bajadas, "saltadas": saltadas, "rotas": rotas,
            "sin_consentimiento": sin_consentimiento,
            "con_texto": sum(1 for g in sum(por_persona.values(), []) if g.transcripcion)}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("origen", help="archivo .jsonl o URL del export")
    p.add_argument("--persona", default="", help="importar solo a esta persona")
    args = p.parse_args()
    r = importar(args.origen, args.persona)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if r["sin_consentimiento"]:
        print(f"\n{r['sin_consentimiento']} filas sin consentimiento: NO entran al corpus.")
    print("Ahora: abre /corregir, revisa que el audio diga lo que la persona escribió, "
          "y exporta el corpus.")


if __name__ == "__main__":
    main()
