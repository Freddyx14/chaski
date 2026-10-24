"""El contrato entre las sesiones. Ver CONTRATO.md.

Mientras el reconocimiento de voz real no exista, `entender` devuelve una
transcripcion fija: la sesion B y Freddy programan contra esto desde el minuto
cero en vez de esperar al modelo.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

BLOQUES = ("A", "B")
FRECUENCIA_HZ = 16000


@dataclass(frozen=True)
class Grabacion:
    """Una linea del manifiesto."""
    persona: str
    bloque: str
    numero: int
    audio: str
    transcripcion: str = ""
    castellano: str = ""
    segundos: float = 0.0
    consentimiento: bool = False

    def __post_init__(self) -> None:
        if self.bloque not in BLOQUES:
            raise ValueError(f"bloque invalido: {self.bloque!r}; se espera A o B")
        if self.numero < 0:
            raise ValueError("numero no puede ser negativo")

    @property
    def nombre(self) -> str:
        return f"{self.persona}_{self.bloque}_{self.numero:03d}"

    def a_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def de_json(cls, linea: str) -> "Grabacion":
        return cls(**json.loads(linea))


def leer_manifiesto(ruta: str | Path) -> list[Grabacion]:
    lineas = Path(ruta).read_text(encoding="utf-8").splitlines()
    return [Grabacion.de_json(l) for l in lineas if l.strip() and not l.startswith("#")]


def escribir_manifiesto(ruta: str | Path, grabaciones: list[Grabacion],
                        cabecera: str = "") -> None:
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    cuerpo = "\n".join(g.a_json() for g in grabaciones)
    texto = (f"# {cabecera}\n" if cabecera else "") + cuerpo + "\n"
    destino.write_text(texto, encoding="utf-8")


@dataclass(frozen=True)
class Transcripcion:
    texto: str
    confianza: float
    segundos: float
    modelo: str


TEXTO_FALSO = "sangre kaptinqa posta man hamuy"


def entender(audio: str | Path) -> Transcripcion:
    """Audio -> texto en chanka.

    Version falsa. La sesion A la reemplaza cuando el modelo este listo, sin
    cambiar la firma. Quien la llame NO debe mirar el campo `modelo` para
    decidir logica de producto; sirve solo para los reportes.
    """
    return Transcripcion(texto=TEXTO_FALSO, confianza=0.0, segundos=0.0, modelo="falso")
