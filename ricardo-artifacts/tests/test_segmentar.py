import subprocess
from pathlib import Path

import pytest

from voz.segmentar import mejor_particion, trozos_de_voz
from voz.ingesta import duracion

MUESTRAS = Path("datos/prueba_minima")


def grabacion_larga(tmp_path, clips, silencio=1.0):
    """Pega varios clips con silencios en medio, como una grabacion seguida."""
    lista = tmp_path / "lista.txt"
    quieto = tmp_path / "silencio.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"anullsrc=r=16000:cl=mono", "-t", str(silencio), str(quieto)], check=True)
    partes = []
    for c in clips:
        partes += [f"file '{c.resolve()}'", f"file '{quieto.resolve()}'"]
    lista.write_text("\n".join(partes), encoding="utf-8")
    destino = tmp_path / "larga.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lista), "-ac", "1", "-ar", "16000", str(destino)], check=True)
    return destino


@pytest.mark.skipif(not MUESTRAS.exists(), reason="falta datos/prueba_minima")
def test_encuentra_tantos_trozos_como_frases(tmp_path):
    clips = sorted(MUESTRAS.glob("spa_*.wav"))
    assert len(clips) == 5
    larga = grabacion_larga(tmp_path, clips)
    trozos, diag = mejor_particion(larga, duracion(larga), len(clips))
    assert len(trozos) == len(clips)
    assert diag["exacto"] is True


@pytest.mark.skipif(not MUESTRAS.exists(), reason="falta datos/prueba_minima")
def test_los_trozos_van_en_orden_y_no_se_pisan(tmp_path):
    clips = sorted(MUESTRAS.glob("spa_*.wav"))[:3]
    larga = grabacion_larga(tmp_path, clips)
    trozos, _ = mejor_particion(larga, duracion(larga), 3)
    for a, b in zip(trozos, trozos[1:]):
        assert a.fin <= b.inicio


@pytest.mark.skipif(not MUESTRAS.exists(), reason="falta datos/prueba_minima")
def test_descarta_los_trozos_demasiado_cortos(tmp_path):
    clips = sorted(MUESTRAS.glob("spa_*.wav"))[:2]
    larga = grabacion_larga(tmp_path, clips, silencio=0.8)
    trozos = trozos_de_voz(larga, duracion(larga), -30, 0.45)
    assert all(t.largo >= 0.5 for t in trozos)
