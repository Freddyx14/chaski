import pytest


@pytest.fixture(autouse=True)
def _memoria_aislada(tmp_path, monkeypatch):
    """No test writes Chaski's real automatic memory: each one gets its own file."""
    monkeypatch.setenv("CHASKI_MEMORIA_RUTA", str(tmp_path / "memoria_auto.jsonl"))


@pytest.fixture(autouse=True)
def _memoria_sin_hilos(monkeypatch):
    """Background memory writes run inline in tests, so no test depends on thread timing (a 50 ms sleep was flaky
    under load). Same contract as production: an error in the write never reaches the turn."""
    from chaski import orquestador

    def en_linea(fn, *args):
        try:
            fn(*args)
        except Exception:  # noqa: BLE001
            pass

    monkeypatch.setattr(orquestador, "_en_fondo", en_linea)
