# Ruta `GET /banco` para el servidor

La app de iOS lee exactamente `{id, es, quy, audio, tags}`. Esta ruta devuelve eso y nada más.

```python
from fastapi import FastAPI, Query

from chaski import banco as banco_frases

app = FastAPI()


@app.on_event("startup")
def _precargar_banco() -> None:
    # Carga el modelo de embeddings una vez (≈0,5 s con el modelo ya bajado; la primera vez baja ~220 MB).
    banco_frases.precargar()


@app.get("/banco")
def get_banco(tag: str | None = Query(default=None), con_quechua: bool = True) -> list[dict]:
    """Frases del banco. `?tag=emergencia` para el modo emergencia.

    Por defecto solo devuelve las que tienen quechua: un botón sin quechua no puede sonar.
    `?con_quechua=false` trae también las `falta_quechua` (para la pantalla de revisión de la enfermera).
    """
    b = banco_frases.banco()
    items = b.por_tag(tag, solo_con_quechua=con_quechua) if tag else [
        it for it in b.items if it["quy"] or not con_quechua]
    return [banco_frases.para_app(it) for it in items]
```

Notas:

- **Nada del banco está revisado todavía** (`revisado: false` en todo). El quechua del manual del CMP es
  Collao convertido a Chanka por regla; lo tiene que revisar la mamá de Freddy o la enfermera antes de que B7
  lo trate como verificado.
- **Audio**: hoy ninguna frase tiene audio de la familia. Las 6 del bloque E del formulario son justo frases de
  las 100 `verificadas` y la regla de fuga las saca. Si `audio` es `null`, la app usa la voz de Chaski.
- Para el intérprete: `banco_frases.candidatos(texto_es, k=20)` devuelve `[{id, es}]` listo para el prompt.
- Regenerar el banco: `cd app && uv run python ../evals/banco/construir.py`.
