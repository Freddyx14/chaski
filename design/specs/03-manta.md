# Rimay · la manta andina (D28)

> Sábado 24 de octubre, 09:40 PT. Pedido de Freddy: la identidad visual sale de las mantas de la sierra
> (lliclla), con sus franjas de tinte y sus cadenas tejidas. Referencia favorita: tela blanca con franjas de
> colores y bandas de rombos. **Reemplaza la regla de D24 de «una sola franja textil fina como único adorno».**

## La regla que ordena todo

La manta es la **capa de identidad**, nunca el contenido. La enfermera mira el teléfono uno o dos segundos:
lo que dice el estado (auditado, aviso, bloqueado) tiene que seguir leyéndose sin ruido.

| Dónde va | Variante | Alto |
|---|---|---|
| Onboarding, arriba de todo, con Chaski sentado encima | `gala` (franjas + trenza + rombos + ganchos en S + escalón) | ~200 pt en el paso 1 |
| Banda bajo el encabezado de la consulta y del resumen | `faja` (franjas + una cadena de rombos) | ~24 pt |
| Base de la tarjeta de Chaski: Chaski se sienta en su lliclla | `lliclla` | ~22 pt a 240 pt de tarjeta, escala con la tarjeta |

## Reglas (también en `design/tokens.json`)

1. La manta solo vive en bandas decorativas. Nunca dentro de una tarjeta de contenido ni detrás de texto.
2. Los colores de estado (ok, warn, block) no cambian y nunca salen de la paleta de la manta.
3. Una banda de manta nunca toca un elemento de estado: al menos 12 pt de fondo liso entre los dos, para que
   el rojo o el rosado del tejido no se lean como «bloqueado». Por eso la `lliclla` de Chaski no lleva rojo.
4. El teal sigue siendo el único color de acción. El turquesa de la manta es adorno, no botón.
5. Los motivos se tejen sobre una grilla de puntos (mapas de bits en `movil/src/rimay/manta.tsx`), como en el
   telar. Nada de curvas ni degradados.

## Paleta (`tokens.json` → `manta`)

Tintes puros tomados a ojo de la referencia: magenta, rosado, naranja, amarillo, verde, lima, turquesa, cobalto,
morado, rojo, blanco y el hilo oscuro de las trenzas.
