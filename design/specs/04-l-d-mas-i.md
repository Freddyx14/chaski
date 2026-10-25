# Chaski · UI final: opción L = D + I (D29) + micrófono inti (D31)

> **Diseño cerrado (D31, sáb 11:15).** Todo L queda igual salvo el micrófono: el anillo de chakana pasa a ser un
> **micrófono inti** de anillos concéntricos (`movil/src/chaski/inti.tsx`), ver la sección «Micrófono inti».

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
| 2 escalones hondos | la chakana | la marca del encabezado |
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
| `AnilloInti` (`inti.tsx`) | El micrófono inti: 4 anillos concéntricos y 8 rayos escalonados (D31) |
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
| **Listo** | Los anillos respiran muy despacio, uno detrás del otro (ciclo de 4 s), para invitar a tocar | — |
| **Escuchando** | Una onda sale del centro hacia afuera con el volumen: los anillos se encienden y se agrandan del de adentro al de afuera (umbrales 0.12 / 0.4 / 0.7). El medidor es una fila de crucecitas que crecen con la voz | `metering` del grabador (dB → 0..1) |
| **Escuchando al paciente** | Lo mismo, con los anillos y el medidor en canela, naranja y amarillo: se ve de quién es el turno | lado = quechua |
| **Pensando** | El inti chico gira sus rayos despacio (6 s por vuelta) y una luz recorre el anillo de afuera. Cada paso cumplido entra con un resorte chico | pasos del turno |
| **Chaski habla** | El marco de Chaski late con la voz: en las partes fuertes se encienden magenta → amarillo → cobalto. El quechua se lee entero; lo ya dicho pasa a tinta plena, palabra por palabra | envolvente del WAV y `currentTime / duration` |
| **Transiciones** | Las tarjetas suben con un resorte corto. Los chips de la auditoría entran uno por uno (110 ms entre chip y chip): se ve revisado | — |
| **Bloqueado** | Un solo temblor suave de la comparación al aparecer. Nunca rojo que parpadea | — |

**Modo demo:** sin micrófono ni audio, un reloj falso mueve el nivel (`?demo=grabando`) y la voz (`?demo=dicho`),
así el movimiento se puede mostrar y revisar en el simulador o en el jurado sin servicio.

## Micrófono inti (D31)

> **Ajuste del 24-oct, 18:18 (Freddy):** sin rayos, tres anillos (cobalto, amarillo, magenta; en quechua naranja, amarillo, canela), más finos y compactos. Lo que sigue sobre rayos y cuatro anillos queda como historia.

Referencia de Freddy: un inti andino, anillos sólidos concéntricos alrededor de un disco con rayos detrás.

| | |
|---|---|
| Centro | El botón teal del micrófono, 96 pt (72 pt en «pensando») |
| Anillos | 4, de adentro hacia afuera: cobalto 5 · amarillo 9 · turquesa 5 · magenta 9 pt, con 3 pt de fondo entre cada uno. En el turno del paciente: naranja, amarillo, canela, naranja |
| Rayos | 8 rayos escalonados cortos (dos peldaños) detrás del anillo de afuera, alternando amarillo y magenta (o los tonos canela) |
| Constelación | Fuera: con los anillos y los rayos, las crucecitas sueltas ensuciaban el medallón |
| Movimiento | Reposo: respiración escalonada. Escucha: onda del centro hacia afuera, escalada por el volumen. Piensa: giro de los rayos y una luz que recorre el anillo. `modo="habla"` + `pulso` laten con la envolvente de la voz (listo en el componente). Con «Reducir movimiento», quieto |

Mientras Chaski habla el micrófono no está en pantalla (la consulta muestra «Repetir audio» y «Seguir»), así que lo que late con la voz es el marco de Chaski.

## Chaski sin fondo: cómo se recortó (D40, rehecho el 25-oct)

- **Modelo:** BiRefNet HR-matting (`ZhengPeng7/BiRefNet_HR-matting`) a 2048 px, en una RTX 4090 de Runpod. Ganó contra BiRefNet general, BiRefNet-matting y las dos versiones de rembg en 96 cuadros difíciles: menos agujeros con color de Chaski (557 contra 816–905) y bordes de pelaje más finos.
- **Correcciones en código:** lo que tiene color claro de Chaski y está pegado al cuerpo se agrega al alfa (pezuñas y patas barridas), se borran manchitas sueltas cerca de los pies y se quita el gris del fondo de los bordes semitransparentes. **Sin mediana temporal:** borraba las partes que se mueven rápido (la pezuña de `no_entendi`).
- **QA por cuadro, en las dos direcciones:** «falta» (color claro de Chaski que el alfa quitó) y «sobra» (color de fondo, incluida la sombra del piso, que quedó opaco cerca del borde o en los huecos), más agujeros con color de Chaski y la coincidencia entre cuadros. Resultado: falta máx 26 px por cuadro (antes 550), sin agujeros malos, coincidencia ≥ 0,92. Lo que queda de «sobra» en `no_entendi` 187–198 es el barrido de la pata que ya trae el video original.
- **Video:** HEVC con alfa, color **premultiplicado** (con color debajo del alfa 0, iOS mostraba un recuadro claro).
