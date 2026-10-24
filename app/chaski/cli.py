"""Try the audit from the terminal:

    uv run python -m chaski.cli "Tome una pastilla de sulfato ferroso cada día después del almuerzo, durante un mes."
"""
import sys

import anthropic

from chaski.auditoria import auditar


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit('uso: python -m chaski.cli "indicación en castellano"')
    resultado = auditar(anthropic.Anthropic(), " ".join(sys.argv[1:]))
    print(f"\nORIGINAL     {resultado.original}")
    print(f"QUECHUA      {resultado.quechua}")
    print(f"RETRADUCIDO  {resultado.retraduccion}")
    for d in resultado.diferencias:
        print(f"  ✗ {d.campo}: {d.original} → {d.retraducido}")
    if resultado.terminos_inseguros:
        print(f"  ? inseguros: {', '.join(resultado.terminos_inseguros)}")
    print(f"\n{'✅ ENVIAR' if resultado.enviar else '⛔ NO ENVIAR'} — {resultado.motivo}\n")


if __name__ == "__main__":
    main()
