# Chaski · dirección de manta andina (pen.dev)

Son maquetas para elegir antes de tocar la app, con las mismas tres pantallas en cada opción:
idioma, Chaski habla y listo para hablar. Las referencias son las seis imágenes de Freddy.

**Elegida: L · D + I (sáb 24-oct).** Freddy descartó primero A, B y F, y después C, E, G, H, J
y K. Eligió D (formas geométricas) e I (chakana), y L es la mezcla de las dos. **El producto se
llama Chaski, igual que la vicuña.**

| Opción | Idea |
|---|---|
| **L · D + I** ★ final | Ver el detalle abajo |
| D · El motivo es la interfaz | Rombos y escalonados como componentes (referencia, todavía dice «Rimay») |
| I · Chakana | La cruz escalonada ordena el micrófono, el marco y el progreso (referencia, todavía dice «Rimay») |

Cómo queda L, elemento por elemento:
- **Chaski:** silueta escalonada de D, con el marco anidado cobalto, amarillo y magenta de I.
- **Encabezado:** chakana antes del nombre.
- **Progreso:** rombos de píxel.
- **Sobre los idiomas:** fila de pequeñas cruces escalonadas.
- **Filas de idioma:** columna de cruces a la izquierda, cobalto para castellano y canela para runasimi.
- **Etiqueta de quechua:** extremos escalonados con un rombo adentro.
- **Divisor:** zigzag de píxel.
- **Fila de auditoría:** la de D, sin motivos encima.
- **Micrófono:** anillo de chakana multicolor con una constelación de rombos alrededor.
- **Botones laterales:** octágonos escalonados.

Lo que no cambia:
- El fondo es crema.
- El teal es el único color de acción.
- El rojo solo significa «no lo dije».

Archivos:
- Tablero: `tablero.png`, en el orden L, D, I.
- Cada opción por separado: `opcion-<X>.png` y `.pen`.
- Las especificaciones están en `prompts/`. `gen.py` genera `opcion-<X>.txt`, y las correcciones de L están en `opcion-L-fix1.txt` y `opcion-L-fix2.txt`.

## Variaciones sobre L (sáb 24-oct, exploración de baja prioridad)

Freddy compartió nuevas referencias (dos grillas de «diseño andino», guardadas en `ref/andino-9.png`
y `ref/andino-10.png`). Su encargo: algo **simple y legible para todos**, donde los patrones son
identidad para que la gente se sienta representada, y un diseño que se sienta **vivo**. Cada
variación lleva las tres pantallas de L más un cuarto tablero, «Movimiento», con cuatro tiras de
fotogramas: escuchando, pensando, Chaski habla y habla el paciente (en canela).

| Variación | Idea | Movimiento |
|---|---|---|
| M · Rombo escalonado | Un solo rombo concéntrico marca a Chaski, el micrófono y el progreso | Onda concéntrica que se enciende anillo por anillo con el volumen |
| N · Greca y llamas | Una greca escalonada y una fila de llamas como hilo conductor, en naranja, teal y crema | La greca avanza como marquesina y las llamas caminan; hacia la enfermera cuando habla el paciente |
| O · Flor de ocho puntas | La flor-estrella es el sello y el micrófono, y dientes de sierra ordenan el resto | La flor se abre pétalo por pétalo, gira mientras piensa y respira con la voz |

- Tablero de variaciones: `tablero-variaciones.png`, en el orden L, M, N, O.
- Las especificaciones están en `prompts/`:
  - `opcion-<M|N|O>.txt` (la variación sobre L)
  - `opcion-<M|N|O>-mov.txt` (el tablero de movimiento)
- En O se quitó el rojo de los pétalos, porque el rojo solo significa «no lo dije».
