import pytest


@pytest.fixture(autouse=True)
def _memoria_aislada(tmp_path, monkeypatch):
    """No test writes Chaski's real automatic memory: each one gets its own file."""
    monkeypatch.setenv("CHASKI_MEMORIA_RUTA", str(tmp_path / "memoria_auto.jsonl"))
