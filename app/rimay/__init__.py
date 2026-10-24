"""Compatibility shim (D30): the package is now `chaski`. Kept so the running service, which still does
`from rimay.auditoria import ...`, keeps working until it is updated. Remove after the hackathon."""
import importlib
import sys

for _m in ("auditoria", "hechos", "resumen", "cli"):
    try:
        sys.modules[f"rimay.{_m}"] = importlib.import_module(f"chaski.{_m}")
    except Exception:  # cli may need extras; the shim must never break imports
        pass
