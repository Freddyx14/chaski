# -*- coding: utf-8 -*-
"""Los iconos que van dentro de las cajas de los diagramas.

Dos clases de icono, y la diferencia importa:

  - Chaski sale del arte real del repo (`design/chaski/reposo.png`), reducido a
    64 px. Es nuestro, así que se usa tal cual.
  - Los demás son glifos dibujados aquí: un chip para la GPU, una onda para
    Cartesia, un destello para Claude. No son los logos de las marcas; son
    señas para que la caja se reconozca de un vistazo sin copiar un logo ajeno.
    La excepción es EC2, que es un cuadrado naranja con un chip: la figura es
    geométrica y es la que usa el propio draw.io en su librería de AWS.

Todo viaja como data URI, así que el `.svg` y el `.drawio` quedan autocontenidos:
no hay archivos sueltos que se pierdan al mover el diagrama de carpeta.
"""
from __future__ import annotations

import base64
from pathlib import Path

ARTE_CHASKI = Path(__file__).resolve().parents[3] / "design" / "chaski" / "reposo.png"

_GLIFOS = {
    "ec2": """<rect x="1" y="1" width="22" height="22" rx="3" fill="#D05C17"/>
      <rect x="6.5" y="6.5" width="11" height="11" rx="1.5" fill="#FFFFFF"/>
      <g stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round">
      <path d="M9 1.5v4M12 1.5v4M15 1.5v4M9 18.5v4M12 18.5v4M15 18.5v4"/>
      <path d="M1.5 9h4M1.5 12h4M1.5 15h4M18.5 9h4M18.5 12h4M18.5 15h4"/></g>""",

    "gpu": """<rect x="2" y="4" width="20" height="16" rx="2" fill="#1F6FD0"/>
      <rect x="6" y="8" width="12" height="8" rx="1" fill="#FFFFFF"/>
      <g stroke="#1F6FD0" stroke-width="1.4" stroke-linecap="round">
      <path d="M9 10h6M9 12.5h6"/></g>
      <g stroke="#1F6FD0" stroke-width="1.6" stroke-linecap="round">
      <path d="M7 1.5v2.5M12 1.5v2.5M17 1.5v2.5M7 20v2.5M12 20v2.5M17 20v2.5"/></g>""",

    "claude": """<circle cx="12" cy="12" r="11" fill="#D97757"/>
      <g stroke="#FFFFFF" stroke-width="2.1" stroke-linecap="round">
      <path d="M12 4.5v15M4.5 12h15M6.7 6.7l10.6 10.6M17.3 6.7L6.7 17.3"/></g>""",

    "cartesia": """<circle cx="12" cy="12" r="11" fill="#1B9476"/>
      <g stroke="#FFFFFF" stroke-width="2" stroke-linecap="round">
      <path d="M5.5 12v0M8.5 8.5v7M11.5 5.5v13M14.5 8v8M17.5 10.5v3"/></g>""",

    "ngrok": """<path d="M12 1.5l9.5 4v7c0 5.5-4 9.2-9.5 10.5C6.5 21.7 2.5 18 2.5 12.5v-7z"
      fill="#5A5A52"/><g stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" fill="none">
      <path d="M7.5 12h9M13 8.5l3.5 3.5L13 15.5"/></g>""",

    "navegador": """<rect x="1.5" y="3.5" width="21" height="17" rx="2" fill="#FFFFFF"
      stroke="#5A5A52" stroke-width="1.8"/><path d="M1.5 8.5h21" stroke="#5A5A52" stroke-width="1.8"/>
      <circle cx="5" cy="6" r="1" fill="#5A5A52"/><circle cx="8" cy="6" r="1" fill="#5A5A52"/>""",

    "formulario": """<rect x="4" y="2.5" width="16" height="19" rx="2" fill="#FFFFFF"
      stroke="#1B9476" stroke-width="1.8"/><rect x="8.5" y="1" width="7" height="3.5" rx="1.2"
      fill="#1B9476"/><g stroke="#1B9476" stroke-width="1.7" stroke-linecap="round">
      <path d="M8 10h8M8 13.5h8M8 17h5"/></g>""",

    "etiqueta": """<path d="M2.5 11.5V3.5a1 1 0 011-1h8l10 10-9 9z" fill="#FFFFFF"
      stroke="#1F6FD0" stroke-width="1.8" stroke-linejoin="round"/>
      <circle cx="7" cy="7" r="1.9" fill="#1F6FD0"/>""",

    "disco": """<ellipse cx="12" cy="5.5" rx="9" ry="3.2" fill="#FFFFFF" stroke="#5A5A52"
      stroke-width="1.8"/><path d="M3 5.5v13c0 1.8 4 3.2 9 3.2s9-1.4 9-3.2v-13" fill="none"
      stroke="#5A5A52" stroke-width="1.8"/><path d="M3 12c0 1.8 4 3.2 9 3.2s9-1.4 9-3.2"
      fill="none" stroke="#5A5A52" stroke-width="1.4"/>""",

    "micro": """<rect x="8.5" y="1.5" width="7" height="12" rx="3.5" fill="#5A5A52"/>
      <path d="M5 11.5a7 7 0 0014 0" fill="none" stroke="#5A5A52" stroke-width="2"
      stroke-linecap="round"/><path d="M12 18.5v4" stroke="#5A5A52" stroke-width="2"
      stroke-linecap="round"/>""",

    "parlante": """<path d="M4 9h4l5-4.5v15L8 15H4z" fill="#5A5A52"/>
      <g stroke="#5A5A52" stroke-width="1.8" stroke-linecap="round" fill="none">
      <path d="M16 8.5a5 5 0 010 7M18.5 6a8.5 8.5 0 010 12"/></g>""",

    "guarda": """<path d="M12 1.5l9 3.8v6.4c0 5.3-3.8 9-9 10.8-5.2-1.8-9-5.5-9-10.8V5.3z"
      fill="#8A4FBD"/><path d="M7.5 12.2l3 3 6-6.4" fill="none" stroke="#FFFFFF"
      stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>""",

    "servidor": """<rect x="2.5" y="3" width="19" height="7" rx="1.5" fill="#FFFFFF"
      stroke="#8A4FBD" stroke-width="1.8"/><rect x="2.5" y="14" width="19" height="7" rx="1.5"
      fill="#FFFFFF" stroke="#8A4FBD" stroke-width="1.8"/>
      <circle cx="6" cy="6.5" r="1.3" fill="#8A4FBD"/><circle cx="6" cy="17.5" r="1.3" fill="#8A4FBD"/>
      <g stroke="#8A4FBD" stroke-width="1.5" stroke-linecap="round">
      <path d="M10 6.5h8M10 17.5h8"/></g>""",

    "cuaderno": """<path d="M4 2.5h13a2 2 0 012 2v17H6a2 2 0 01-2-2z" fill="#FFFFFF"
      stroke="#8C8C7A" stroke-width="1.8" stroke-linejoin="round"/>
      <path d="M8 2.5v19" stroke="#8C8C7A" stroke-width="1.5"/>
      <g stroke="#8C8C7A" stroke-width="1.5" stroke-linecap="round">
      <path d="M11 8h5M11 11.5h5M11 15h3"/></g>""",

    "medir": """<rect x="2" y="2" width="20" height="20" rx="2" fill="#FFFFFF"
      stroke="#5A5A52" stroke-width="1.8"/><g fill="#5A5A52">
      <rect x="6" y="13" width="3" height="6" rx="0.6"/><rect x="10.5" y="9" width="3" height="10" rx="0.6"/>
      <rect x="15" y="5.5" width="3" height="13.5" rx="0.6"/></g>""",
}


def _uri(mime: str, datos: bytes) -> dict:
    """Guarda el base64 crudo: cada formato lo escribe a su manera.

    draw.io espera `data:image/png,<base64>` (sin `;base64`), el SVG estándar
    espera `data:image/png;base64,<base64>`. Mismo contenido, prefijo distinto.
    """
    b64 = base64.b64encode(datos).decode("ascii")
    return {"mime": mime, "b64": b64,
            "svg": f"data:{mime};base64,{b64}",
            "drawio": f"data:{mime},{b64}"}


def _chaski() -> dict | None:
    if not ARTE_CHASKI.exists():
        return None
    from io import BytesIO
    from PIL import Image
    im = Image.open(ARTE_CHASKI).convert("RGB").resize((64, 64), Image.LANCZOS)
    bio = BytesIO()
    im.save(bio, format="PNG", optimize=True)
    return _uri("image/png", bio.getvalue())


def cargar() -> dict:
    iconos = {}
    for nombre, cuerpo in _GLIFOS.items():
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
               f'width="24" height="24">{cuerpo}</svg>')
        iconos[nombre] = _uri("image/svg+xml", svg.encode("utf-8"))
    chaski = _chaski()
    if chaski:
        iconos["chaski"] = chaski
    return iconos


if __name__ == "__main__":
    for n, v in cargar().items():
        print(f"{n:<12} {v['mime']:<16} {len(v['b64']):>6} bytes en base64")
