# Chaski · UI final: opción L = D + I (D29)

> Sábado 24 de octubre de 2026, 11:05 PT. Aprobada por Freddy sobre la maqueta `design/manta-opciones/opcion-L.png`
> («FUCKING LIKE IT, LET'S GO WITH THAT AND BUILD IT»). Reemplaza las bandas de franjas de D28 (`03-manta.md`).
> Construida en `movil/` y revisada en el simulador con los enlaces demo.

## La idea

Los motivos andinos no decoran la pantalla: **son** los componentes. Una sola figura geométrica, un cuadrado con
las esquinas cortadas en escalones (`movil/src/chaski/geometria.ts → escalonado()`), da todo el vocabulario:

| Con… | sale… | dónde |
|---|---|---|
| 5 escalones chicos (~3 % del lado) | la silueta escalonada de D | la foto de Chaski |
| la misma silueta metida hacia adentro, tres veces | las hebras de I: cobalto (afuera), amarillo, magenta (adentro) | el marco de Chaski |
| 2 escalones hondos | la chakana | el anillo del micrófono, la marca del encabezado |
| 1 escalón muy hondo | la crucecita | progreso, constelación, filas y columnas, medidor de voz, etiqueta |

## Componentes (`movil/src/chaski/motivos.tsx`, `chaski.tsx`, `ui.tsx`)

| Componente | Qué es |
|---|---|
| `Chaski` | Foto o loop recortado en la silueta escalonada, con las tres hebras. `pulso` (0..1) las enciende con la voz |
| `MarcaChaski` / `MarcaChakana` | Chakana cobalto con el centro abierto antes de «Chaski» (o del título de la pantalla) |
| `ProgresoCruces` | Progreso del onboarding: actual magenta con borde de hilo, las demás huecas |
| `FilaDeCruces` | Fila multicolor (magenta, amarillo, turquesa, cobalto) sobre las opciones de idioma |
| `ColumnaDeCruces` | Tres crucecitas a la izquierda de cada fila de idioma: cobalto castellano, canela runasimi |
| `Etiqueta` | Etiqueta de idioma con dos escalones en cada punta y una crucecita adentro |
| `Zigzag` | Divisor de puntos en zigzag dentro de la tarjeta de quechua |
| `AnilloChakana` | Tres chakanas anidadas alrededor del micrófono y una constelación de 8 crucecitas |
| `BotonEscalonado` | Receta y Resumen con contorno escalonado |
| Chips de auditoría | Cada verificación en su chip blanco. **Ningún motivo toca la fila de auditoría** |

Reglas que no cambian: teal es el único color de acción; rojo solo significa «no lo dije»; avisos siempre con ícono.

## Movimiento

Pedido de Freddy: que la persona se **sienta escuchada y hablada**. Todo el movimiento sale de **señales reales**:
el volumen del micrófono, la envolvente de la voz y el avance del audio. Las reglas están en `movimiento.ts`
(puras, probadas). Se anima con `react-native-reanimated`. Con **Reducir movimiento** del sistema
(`useReducedMotion`) nada respira, nada gira y nada tiembla: las hebras solo cambian de brillo.

| Estado | Qué se mueve | Señal |
|---|---|---|
| **Listo** | El anillo respira muy despacio (escala 1 → 1.035, ciclo de 4 s) para invitar a tocar | — |
| **Escuchando** | Las hebras del anillo se encienden de adentro hacia afuera con el volumen (umbrales 0.12 / 0.4 / 0.7) y las crucecitas de la constelación se abren unos puntos. El medidor es una fila de crucecitas que crecen con la voz | `metering` del grabador (dB → 0..1) |
| **Escuchando al paciente** | Lo mismo, con el anillo y el medidor en canela, naranja y amarillo: se ve de quién es el turno | lado = quechua |
| **Pensando** | Un brillo gira por la constelación, estrella por estrella (2.4 s por vuelta). Cada paso cumplido entra con un resorte chico | pasos del turno |
| **Chaski habla** | El marco de Chaski late con la voz: en las partes fuertes se encienden magenta → amarillo → cobalto. El quechua se lee entero; lo ya dicho pasa a tinta plena, palabra por palabra | envolvente del WAV y `currentTime / duration` |
| **Transiciones** | Las tarjetas suben con un resorte corto. Los chips de la auditoría entran uno por uno (110 ms entre chip y chip): se ve revisado | — |
| **Bloqueado** | Un solo temblor suave de la comparación al aparecer. Nunca rojo que parpadea | — |

**Modo demo:** sin micrófono ni audio, un reloj falso mueve el nivel (`?demo=grabando`) y la voz (`?demo=dicho`),
así el movimiento se puede mostrar y revisar en el simulador o en el jurado sin servicio.
