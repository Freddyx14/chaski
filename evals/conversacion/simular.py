"""Voice-mode simulation: whole consultations against the LIVE service, nobody tells Chaski who is speaking.

    cd /Users/freddy/projects/1-projects-active/loopmind/clients/chaski
    ELEVENLABS_API_KEY="$(secretctl get ELEVENLABS_API_KEY)" python3 evals/conversacion/simular.py

Staff lines: Spanish synthesized with ElevenLabs (Peruvian voices, cached in data/conversacion/, gitignored).
Patient lines: real Quechua audio from speaker p16, whom the recognizer never heard (data/formulario/).
Each turn does what the hands-free app does: /idioma decides who spoke (no hint), then the staff route (/escuchar +
/turno/enfermera) or the patient route (/turno/paciente), carrying `contexto`. If the single auto route exists
(POST /turno), it is used instead and its own `quien_hablo` is scored.
Scored per turn: who-spoke right, expected action (traducir / repreguntar / no_entendi), output to the right person in
the right language, numbers of the reference intact, seconds. Writes resultados/simulacion-<fecha>.json.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
URL = json.loads((RAIZ / "ricardo-artifacts/servicio/url.json").read_text())["url"].rstrip("/")
CACHE = RAIZ / "data/conversacion"
VOZ = {"enfermera": "34EkeMY6ezBFj41NQj1f", "medico": "TTfJ6x7olNX5yvlMWLyu"}  # Nelly, Jorge (peruanos)
P16 = RAIZ / "data/formulario/p16"
NUM = {"una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
       "nueve": 9, "diez": 10, "doce": 12, "quince": 15}

# (who, text or p16 clip, expected action(s), reference for numbers)
CONSULTAS = {
    "dolor_de_cabeza": [
        ("enfermera", "Buenos días, señora. ¿Qué le pasa?", {"traducir"}),
        ("paciente", "064", {"traducir"}, "Me duele la cabeza desde ayer"),
        ("enfermera", "¿Está tomando algún medicamento?", {"traducir"}),
        ("paciente", "066", {"traducir"}, "Estoy tomando paracetamol"),
        ("enfermera", "Tome la pastilla.", {"repreguntar"}),
        ("enfermera", "Tome una pastilla de paracetamol cada ocho horas, por tres días.", {"traducir"}),
        ("paciente", "069", {"traducir", "responder"}, "No entendí, ¿me lo puede repetir?"),
        ("enfermera", "Vuelva en una semana.", {"traducir"}),
        ("paciente", "075", {"traducir"}, "Gracias, señorita"),
    ],
    "nino_con_fiebre": [
        ("medico", "Buenas tardes. Cuénteme, ¿qué le trae por aquí?", {"traducir"}),
        ("paciente", "067", {"traducir"}, "Mi hijo tiene fiebre desde anoche"),
        ("medico", "¿El niño es alérgico a algún medicamento?", {"traducir"}),
        ("paciente", "072", {"traducir"}, "No soy alérgico a ningún remedio"),
        ("medico", "Dele paracetamol en jarabe, cinco mililitros cada seis horas, por tres días.", {"traducir"}),
        ("paciente", "071", {"traducir"}, "¿Cuándo es mi próximo control?"),
        ("medico", "Vuelva en tres días, o antes si la fiebre no baja.", {"traducir"}),
    ],
    "barriga": [
        ("enfermera", "Pase, siéntese. ¿Dónde le duele?", {"traducir", "usar_frase_banco"}),
        ("paciente", "065", {"traducir"}, "Me duele la barriga desde hace tres días"),
        ("enfermera", "¿Le dio diarrea?", {"traducir"}),
        ("paciente", "068", {"traducir"}, "Mi hija tiene diarrea desde hace dos días"),
        ("enfermera", "Tómela con agua, no con té.", {"traducir", "repreguntar"}),
        ("paciente", "074", {"traducir"}, "Ya me siento mejor"),
    ],
}


def numeros(t: str) -> set[int]:
    t = (t or "").lower()
    return {int(x) for x in re.findall(r"\d+", t)} | {v for k, v in NUM.items() if re.search(rf"\b{k}\b", t) and v > 1}


def voz_es(texto: str, quien: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{quien}-{abs(hash(texto)) % 10**10}.mp3"
    if not f.exists():
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOZ[quien]}?output_format=mp3_44100_128",
            data=json.dumps({"text": texto, "model_id": "eleven_multilingual_v2"}).encode(),
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
        f.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    w = f.with_suffix(".wav")
    if not w.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(f), "-ar", "16000", "-ac", "1", str(w)], check=True)
    return w


def wav_p16(clip: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    w = CACHE / f"p16-{clip}.wav"
    if not w.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(P16 / f"{clip}.webm"), "-ar", "16000", "-ac", "1",
                        str(w)], check=True)
    return w


def post(ruta: str, archivo: Path | None = None, campos: dict | None = None, timeout=180) -> dict:
    cmd = ["curl", "-s", "-m", str(timeout), "-H", "ngrok-skip-browser-warning: 1", "-X", "POST", f"{URL}{ruta}"]
    if archivo:
        cmd += ["-F", f"audio=@{archivo};type=audio/wav"]
    for k, v in (campos or {}).items():
        cmd += ["-F", f"{k}={v}"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"error": f"respuesta no JSON: {out[:120]}"}


def hay_ruta_auto() -> bool:
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "20", "-H",
                        "ngrok-skip-browser-warning: 1", "-X", "POST", f"{URL}/turno"], capture_output=True, text=True)
    return r.stdout.strip() not in ("404", "405", "000")


def un_turno(archivo: Path, contexto: str, auto: bool) -> tuple[dict, str, float]:
    t0 = time.perf_counter()
    if auto:
        r = post("/turno", archivo, {"contexto": contexto})
        return r, r.get("quien_hablo", "?"), round(time.perf_counter() - t0, 1)
    det = post("/idioma", archivo)
    lado = "personal" if str(det.get("codigo", "")).startswith("spa") else "paciente"
    if lado == "personal":
        oido = post("/escuchar", archivo)
        r = post("/turno/enfermera", None, {"texto": oido.get("texto", ""), "contexto": contexto})
    else:
        r = post("/turno/paciente", archivo, {"contexto": contexto})
    return r, lado, round(time.perf_counter() - t0, 1)


def main():
    auto = hay_ruta_auto()
    salida = {"ruta": "/turno (auto)" if auto else "/idioma + rutas por lado", "consultas": {}}
    for nombre, turnos in CONSULTAS.items():
        contexto, filas = "", []
        for t in turnos:
            quien, contenido, esperado = t[0], t[1], t[2]
            rol_real = "paciente" if quien == "paciente" else "personal"
            ref = t[3] if len(t) > 3 else contenido
            archivo = wav_p16(contenido) if quien == "paciente" else voz_es(contenido, quien)
            r, lado, s = un_turno(archivo, contexto, auto)
            if isinstance(r.get("contexto"), dict):
                contexto = json.dumps(r["contexto"], ensure_ascii=False)
            accion, para, idioma = r.get("accion"), r.get("para"), r.get("idioma_salida")
            destino_ok = None
            if accion == "traducir" and r.get("estado", "").startswith("dicho"):
                destino_ok = (para, idioma) == (("personal", "spa") if rol_real == "paciente" else ("paciente", "quy"))
            faltan = None
            if r.get("estado", "").startswith("dicho") and accion == "traducir" and rol_real == "paciente":
                faltan = sorted(numeros(ref) - numeros(r.get("texto_salida", "")))
            fila = {"quien": quien, "dicho": ref, "lado_detectado": lado, "quien_ok": lado == rol_real,
                    "estado": r.get("estado") or ("error" if r.get("error") else "?"), "accion": accion,
                    "accion_ok": accion in esperado, "para": para, "idioma_salida": idioma, "destino_ok": destino_ok,
                    "salida": r.get("texto_salida"), "oido": r.get("texto_original"), "motivo": r.get("motivo"),
                    "numeros_faltan": faltan, "s": s, "error": r.get("error")}
            filas.append(fila)
            print(nombre, "|", quien, "|", "✓" if fila["quien_ok"] else "✗ lado", "|", accion,
                  "✓" if fila["accion_ok"] else "✗", "|", s, "s |", (fila["salida"] or fila["motivo"] or fila["error"] or "")[:90],
                  flush=True)
        salida["consultas"][nombre] = filas
    todas = [f for fs in salida["consultas"].values() for f in fs]
    ok = lambda k: f"{sum(1 for f in todas if f[k])}/{len(todas)}"
    dest = [f for f in todas if f["destino_ok"] is not None]
    s = sorted(f["s"] for f in todas)
    salida["resumen"] = {"turnos": len(todas), "quien_hablo_bien": ok("quien_ok"), "accion_esperada": ok("accion_ok"),
                         "a_quien_y_en_que_idioma": f"{sum(f['destino_ok'] for f in dest)}/{len(dest)}",
                         "numeros_perdidos": sum(1 for f in todas if f["numeros_faltan"]),
                         "estados": {e: sum(1 for f in todas if f["estado"] == e) for e in {f["estado"] for f in todas}},
                         "s_p50": s[len(s) // 2], "s_p95": s[int(.95 * (len(s) - 1))],
                         "consulta_total_s": {k: round(sum(f["s"] for f in v), 1) for k, v in salida["consultas"].items()}}
    print(json.dumps(salida["resumen"], ensure_ascii=False, indent=1))
    d = Path(__file__).with_name("resultados"); d.mkdir(exist_ok=True)
    (d / f"simulacion-{datetime.now():%Y%m%d-%H%M}.json").write_text(json.dumps(
        {**salida, "consultas": {k: [{x: y for x, y in f.items() if x != "oido"} for f in v]
                                 for k, v in salida["consultas"].items()}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
