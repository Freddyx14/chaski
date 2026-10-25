# -*- coding: utf-8 -*-
"""El flujo COMPLETO de un turno: la voz (Ricardo) + el intérprete agente, las barreras y el crítico.

Reusa el Lienzo de `generar.py` para que salga con el mismo estilo y en los dos formatos (.svg y .drawio).
Se corre desde la raíz de ricardo-artifacts:

    uv run --with pillow python reports/drawio/flujo_completo.py

Cada número sale de un archivo de resultados (ver `evals/HISTORIA.md` y `README.md` en la raíz del repo).
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("generar", Path(__file__).with_name("generar.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)  # regenera los 3 diagramas de Ricardo tal cual (es determinista)

Lienzo, CAJA, TXT = G.Lienzo, G.CAJA, G.TXT
GRIS, AZUL, VERDE, ROJO, MORADO = "#8C8C7A", "#1F6FD0", "#1B9476", "#C8372F", "#8A4FBD"
BANDA = TXT.format(s=13, c="#16160F", f=1)
NOTA = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#C4C2B6;align=left;"
        "verticalAlign=top;spacingLeft=12;spacingTop=8;fontSize=11;fontColor=#4E4D45;")

f = Lienzo("Flujo completo")
f.caja("Chaski · un turno completo: oír, entender, revisar y recién ahí hablar",
       TXT.format(s=19, c="#16160F", f=1), 40, 20, 1200, 28)
f.caja("Azul: Meta en nuestra GPU, ajustado con las voces de la familia · Verde: Cartesia · Rojo: Claude · "
       "Morado: barreras en código (el modelo propone, el código decide) · Medido el 24-oct-2026",
       TXT.format(s=12, c="#4E4D45", f=0), 40, 50, 1500, 20)

# ── 1 · Oír ─────────────────────────────────────────────────────────────────────────────
f.caja("1 · Oír y entender", BANDA, 40, 86, 300, 20)
mic = f.caja("Micrófono\n\niPhone · 16 kHz mono\nEnfermera o paciente",
             CAJA.format(b=GRIS), 40, 190, 170, 76, icono="micro")
lid = f.caja("mms-lid-512\n\n¿quechua o castellano?\n49 ms · 6/6 aciertos",
             CAJA.format(b=AZUL), 245, 180, 200, 90, icono="gpu")
f.flecha(mic, lid)
stt_es = f.caja("Cartesia ink-whisper\n\nOye castellano\n3,5 s de audio en 480 ms",
                CAJA.format(b=VERDE), 490, 110, 230, 84, icono="cartesia")
stt_qu = f.caja("MMS-1b + nuestro adaptador\n\nOye quechua chanka\nError 54 % → 41 % con las voces\nde la familia (hablante nunca oído)",
                CAJA.format(b=AZUL) + "strokeWidth=3;", 490, 250, 250, 110, icono="gpu")
f.flecha(lid, stt_es, "castellano", f"strokeColor={VERDE};fontColor={VERDE};")
f.flecha(lid, stt_qu, "quechua", f"strokeColor={AZUL};fontColor={AZUL};")
b1 = f.caja("B1 · ¿Se oyó bien?\n\nNúmero, medicamento o parte\ndel cuerpo con baja confianza\n→ «¿me lo repite?», nunca adivina",
            CAJA.format(b=MORADO), 770, 175, 230, 110, icono="guarda")
f.flecha(stt_es, b1); f.flecha(stt_qu, b1)
banco = f.caja("Banco de frases verificadas · RAG\n\n216 frases · 24 de emergencia revisadas\npor la enfermera · embeddings + léxico\nacierta a la primera 88 % (palabras: 70 %)",
               CAJA.format(b=MORADO), 1030, 320, 290, 110, icono="disco")
interp = f.caja("INTÉRPRETE · Claude Opus 5\n\nUna llamada decide una de 5 acciones:\ntraducir · repreguntar una vez ·\nresponder al que preguntó · no entendí ·\nusar frase verificada\nPule los dos lados (estilo Wispr Flow)\n98–100 % acción correcta · 0 datos inventados",
                CAJA.format(b=ROJO) + "strokeWidth=3;", 1340, 140, 290, 170, icono="claude")
f.flecha(b1, interp)
f.flecha(banco, interp, "candidatas")
verif = f.caja("Frase verificada\n\nAudio revisado por la enfermera\nVa directo al parlante,\nsin generar ni esperar",
               CAJA.format(b=MORADO), 1670, 110, 200, 100, icono="guarda")
f.flecha(interp, verif, "usar frase", f"strokeColor={MORADO};fontColor={MORADO};")

# ── 2 · Revisar antes de hablar (de derecha a izquierda) ─────────────────────────────────
f.caja("2 · Revisar antes de hablar (ante la duda, Chaski no habla)", BANDA, 40, 455, 600, 20)
b23 = f.caja("B2 · B3 · El pulido\n\nNo cambia ni agrega datos\nSi cambió algo, se usa\nlo dicho tal cual",
             CAJA.format(b=MORADO), 1620, 495, 230, 110, icono="guarda")
f.flecha(interp, b23, "traducir", f"strokeColor={ROJO};fontColor={ROJO};")
trad = f.caja("Traductor\n\nClaude Sonnet 5: chrF++ 42,3\nInterruptor a NLLB-200 ajustado\n(25,8 → 31,7): gana el que mide mejor",
              CAJA.format(b=ROJO), 1340, 495, 240, 110, icono="claude")
f.flecha(b23, trad)
b4 = f.caja("B4 · Términos fijos\n\nNúmeros en chanka (pusaq = 8)\nmedicamento · unidad · negación\n«con agua» exige unu / yaku",
            CAJA.format(b=MORADO), 1060, 495, 240, 110, icono="guarda")
f.flecha(trad, b4)
crit = f.caja("CRÍTICO · Claude Sonnet 5\n\nRetraduce a ciegas (no ve el original)\nExtrae los hechos de los dos lados\nMarca consejos o diagnósticos inventados\n2,6 s · antes 9 s",
              CAJA.format(b=ROJO) + "strokeWidth=3;", 740, 490, 280, 130, icono="claude")
f.flecha(b4, crit)
b56 = f.caja("B5 · B6 · El código compara\n\nDosis · frecuencia · días · unidad\nnegación · con qué se toma\nconcentración · alergia · embarazo\nCualquier error → falla cerrada",
             CAJA.format(b=MORADO) + "strokeWidth=3;", 430, 490, 270, 130, icono="guarda")
f.flecha(crit, b56)
bloq = f.caja("BLOQUEO\n\nChaski no lo dice y le explica\nal personal qué dato falló:\n«no coincidió la frecuencia»",
              CAJA.format(b=ROJO) + "dashed=1;", 70, 500, 300, 100, icono="guarda")
f.flecha(b56, bloq, "no coincide", f"strokeColor={ROJO};fontColor={ROJO};")

# ── 3 · Hablar ──────────────────────────────────────────────────────────────────────────
f.caja("3 · Hablar", BANDA, 40, 700, 300, 20)
voz_es = f.caja("Cartesia Sonic 3.6\n\nHabla castellano\na la enfermera",
                CAJA.format(b=VERDE), 300, 740, 220, 84, icono="cartesia")
voz_qu = f.caja("mms-tts-quy ajustado\n\nHabla quechua al paciente\nCon la voz de una enfermera\nde la comunidad, con su permiso",
                CAJA.format(b=AZUL) + "strokeWidth=3;", 560, 740, 250, 100, icono="gpu")
f.flecha(b56, voz_es, "pasa", f"strokeColor={VERDE};fontColor={VERDE};")
f.flecha(b56, voz_qu, "pasa", f"strokeColor={AZUL};fontColor={AZUL};")
par = f.caja("Parlante y pantalla\n\nTexto primero, audio después\nRojo solo si Chaski no lo dijo",
             CAJA.format(b=GRIS), 440, 880, 240, 76, icono="parlante")
f.flecha(voz_es, par); f.flecha(voz_qu, par)

res = f.caja("Al cerrar la consulta · Claude\n\nNota clínica para el personal\nIndicaciones para llevar al paciente\nPalabras quechua nuevas de esa consulta",
             CAJA.format(b=ROJO), 1150, 740, 260, 110, icono="claude")
rec = f.caja("Receta · Claude visión\n\nFoto de la caja o la receta\n→ dosis, frecuencia, días\n→ las mismas barreras → «¿me lo repite?»",
             CAJA.format(b=ROJO), 1450, 740, 280, 110, icono="claude")

f.caja("Lo medido\n\n"
       "Banco de 952 errores sembrados (dosis cambiada, negación invertida, medicamento, unidad, «con agua» perdido, consejo inventado): "
       "Chaski atrapó 183 de 184 y el 100 % de los críticos, y cada bloqueo dice qué dato falló.\n"
       "Preguntarle a Claude «¿está bien traducido?» también atrapa, pero no dice por qué y retiene 1 de cada 4 frases correctas.\n"
       "Turno completo: 6,5 s típico · crítico 2,6 s · $0,008 por turno. Solo dos roles de Claude (intérprete y crítico): ningún agente de más.",
       NOTA, 40, 990, 1830, 110)

f.guardar("reports/drawio/arquitectura-flujo-completo.drawio", 1900, 1130)
G.revisar([("flujo completo", f, (1900, 1130))])
