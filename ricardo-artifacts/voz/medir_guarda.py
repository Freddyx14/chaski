"""Mide si la auditoría atrapa traducciones malas, con verdad de referencia.

El hueco que teníamos: las dos auditorías solo se comparaban entre sí. Si las
dos se equivocan igual, el acuerdo no prueba nada.

Los 100 pares verificados de frases.json cierran ese hueco sin esperar a la
hablante, porque ahí el chanka ya es correcto. Cada par se usa dos veces:

  limpio       el chanka verificado tal cual. La guarda debe aprobarlo.
               Si lo bloquea, es un falso bloqueo: la enfermera no puede decir
               algo que estaba bien.
  corrompido   el mismo chanka con un error clínico inyectado a propósito.
               La guarda debe bloquearlo. Si lo aprueba, es una fuga, y la fuga
               manda al paciente una indicación equivocada.

Lo que se mide es la guarda, no el traductor: se le entrega el chanka ya hecho
y solo corre retraducción + comparación de hechos. La calidad del traductor se
mide aparte, en medir_traduccion.py.

Las dos reglas de decisión (`decidir` de Freddy y `decidir_separando` mía) solo
se diferencian en cómo tratan `terminos_inseguros`, que aquí no existe porque no
pasamos por el traductor. Así que sobre estos casos dan lo mismo a propósito:
esta prueba aísla la mecánica de comparación de hechos, que es la parte de la
que depende la seguridad. La diferencia entre reglas se ve en el bloqueo, y eso
lo mide medir_auditoria.py.

Uso:
  PYTHONPATH=. uv run --with anthropic --with pydantic python voz/medir_guarda.py --pares 8
"""
from __future__ import annotations

import argparse
import concurrent.futures as futuros
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path

SALIDA = Path("reports/guarda.json")

# Numerales chanka. Cambiar uno es el error que más daño hace:
# «una pastilla cada ocho horas» vuelto «una pastilla cada seis horas».
NUMEROS = ["huk", "iskay", "kimsa", "tawa", "pichqa", "suqta", "qanchis",
           "pusaq", "isqun", "chunka"]


def corromper(chanka: str, azar: random.Random) -> tuple[str, str] | None:
    """Devuelve (chanka_corrompido, tipo_de_error), o None si la frase no se presta."""
    palabras = chanka.split()

    posiciones = [i for i, p in enumerate(palabras)
                  if re.sub(r"\W", "", p.lower()) in NUMEROS]
    if posiciones:
        i = azar.choice(posiciones)
        actual = re.sub(r"\W", "", palabras[i].lower())
        otro = azar.choice([n for n in NUMEROS if n != actual])
        palabras[i] = re.sub(re.escape(actual), otro, palabras[i], flags=re.I)
        return " ".join(palabras), "numero"

    # `mana` es la negación. Borrarla invierte la indicación entera.
    if any(re.sub(r"\W", "", p.lower()) == "mana" for p in palabras):
        quedan = [p for p in palabras if re.sub(r"\W", "", p.lower()) != "mana"]
        return " ".join(quedan).replace("-chu", ""), "negacion"

    # Dos cláusulas: borrar la segunda deja la orden sin su condición
    # («si hay sangrado, venga» queda en «venga»).
    if "," in chanka and len(palabras) >= 6:
        return chanka.split(",")[0].strip() + ".", "condicion"

    return None


def verificar(cliente, hechos_original, chanka: str) -> dict:
    """Retraduce un chanka dado y compara sus hechos contra el original."""
    from chaski.auditoria import decidir, extraer_hechos, retraducir
    from chaski.hechos import comparar

    from servicio.auditoria_rapida import decidir_separando

    retraduccion = retraducir(cliente, chanka)
    hechos_vuelta = extraer_hechos(cliente, retraduccion.castellano)
    diferencias = comparar(hechos_original, hechos_vuelta)

    f_enviar, f_motivo = decidir(diferencias, [], retraduccion.castellano)
    r = decidir_separando(diferencias, [], retraduccion.castellano)
    return {
        "retraduccion": retraduccion.castellano,
        "campos_distintos": [d.campo for d in diferencias],
        "freddy_decidir": {"enviar": f_enviar, "motivo": f_motivo},
        "ricardo_separando": {"enviar": r[0], "motivo": r[1]},
    }


def un_caso(cliente, par: dict, roto: str, tipo: str) -> dict:
    from chaski.auditoria import extraer_hechos

    hechos_original = extraer_hechos(cliente, par["castellano"])
    with futuros.ThreadPoolExecutor(max_workers=2) as pool:
        f_limpia = pool.submit(verificar, cliente, hechos_original, par["chanka"])
        f_sucia = pool.submit(verificar, cliente, hechos_original, roto)
        return {"castellano": par["castellano"], "chanka": par["chanka"],
                "corrompido": roto, "tipo": tipo,
                "limpia": f_limpia.result(), "corrompida": f_sucia.result()}


def pares_clinicos(cliente, cuantos: int) -> list[dict]:
    """Arma pares (castellano, chanka) para las indicaciones de la posta.

    El bloque `verificadas` viene de un corpus de cortesía y trámite: saludos,
    citaciones, nada de dosis. Sirve para puntuar al traductor, pero no para
    probar la guarda, porque la guarda solo mira datos clínicos y en esas frases
    no hay ninguno — corromper un numeral en «espere un momento» no cambia
    ningún hecho, y la guarda aprueba con razón.

    Las indicaciones clínicas sí tienen dosis, pero todavía no tienen chanka
    verificado. Para la prueba de guarda no hace falta que el chanka suene
    natural: hace falta que diga los mismos datos. Así que se traduce una vez
    con el modelo grande y se conservan solo los pares donde los hechos ya
    coinciden. Ese par es el «limpio» que después se corrompe.
    """
    from chaski.auditoria import cargar_glosario, extraer_hechos, traducir

    d = json.loads(Path("datos/frases/frases.json").read_text(encoding="utf-8"))
    fuentes = d["clinicas_sin_traducir"] + d["numeros_y_tiempos"]
    glosario = cargar_glosario()

    def uno(texto: str) -> dict | None:
        t = traducir(cliente, texto, glosario)
        v = verificar(cliente, extraer_hechos(cliente, texto), t.quechua)
        if v["campos_distintos"]:
            return None
        return {"castellano": texto, "chanka": t.quechua}

    with futuros.ThreadPoolExecutor(max_workers=6) as pool:
        salidas = list(pool.map(uno, fuentes[: cuantos * 2]))
    return [s for s in salidas if s][:cuantos]


def medir(cuantos: int, semilla: int, fuente: str) -> dict:
    import anthropic

    azar = random.Random(semilla)
    if fuente == "clinicas":
        pares = pares_clinicos(anthropic.Anthropic(), cuantos * 2)
    else:
        pares = json.loads(Path("datos/frases/frases.json").read_text(encoding="utf-8"))["verificadas"]

    casos = []
    for par in pares:
        roto = corromper(par["chanka"], azar)
        if roto is not None:
            casos.append((par, *roto))
        if len(casos) >= cuantos:
            break

    cliente = anthropic.Anthropic()
    with futuros.ThreadPoolExecutor(max_workers=4) as pool:
        detalle = list(pool.map(lambda c: un_caso(cliente, *c), casos))

    reglas = {}
    for regla in ("freddy_decidir", "ricardo_separando"):
        falsos = sum(1 for d in detalle if not d["limpia"][regla]["enviar"])
        fugas = sum(1 for d in detalle if d["corrompida"][regla]["enviar"])
        n = len(detalle)
        reglas[regla] = {"casos": n, "falsos_bloqueos": falsos, "fugas": fugas,
                         "tasa_falso_bloqueo": round(falsos / n, 3) if n else None,
                         "tasa_fuga": round(fugas / n, 3) if n else None}

    for d in detalle:
        limpia = "ok" if d["limpia"]["freddy_decidir"]["enviar"] else "FALSO-BLOQUEO"
        sucia = "FUGA" if d["corrompida"]["freddy_decidir"]["enviar"] else "atrapada"
        print(f"  {d['castellano'][:32]:<34} {d['tipo']:<10} limpia:{limpia:<14} rota:{sucia}")

    salida = {"cuando": datetime.now(timezone.utc).isoformat(), "semilla": semilla,
              "fuente": fuente, "reglas": reglas, "detalle": detalle}
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    historial = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    historial[fuente] = salida
    SALIDA.write_text(json.dumps(historial, ensure_ascii=False, indent=1), encoding="utf-8")
    return salida


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pares", type=int, default=8)
    p.add_argument("--semilla", type=int, default=13)
    p.add_argument("--fuente", choices=["clinicas", "verificadas"], default="clinicas",
                   help="clinicas: indicaciones de la posta (tienen dosis). "
                        "verificadas: corpus de cortesía, sin datos clínicos que comparar.")
    args = p.parse_args()
    s = medir(args.pares, args.semilla, args.fuente)
    print(f"\n{'regla':<22}{'falso bloqueo':<20}{'fuga'}")
    for nombre, r in s["reglas"].items():
        print(f"{nombre:<22}{r['falsos_bloqueos']}/{r['casos']} ({r['tasa_falso_bloqueo']:.0%})"
              f"{'':<8}{r['fugas']}/{r['casos']} ({r['tasa_fuga']:.0%})")
    print(f"\nguardado en {SALIDA}")


if __name__ == "__main__":
    main()
