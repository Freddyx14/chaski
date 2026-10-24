// La manta andina (D28): franjas de tinte y cadenas tejidas, como la lliclla de la referencia de Freddy.
// Es la capa de identidad, nunca contenido (reglas en design/tokens.json). Todo se teje sobre una grilla de
// puntos, igual que en el telar: por eso los motivos son mapas de bits y no curvas.
import { useState } from 'react';
import { View, type LayoutChangeEvent } from 'react-native';
import Svg, { Rect } from 'react-native-svg';

import { tramos } from './tejido';
import { M } from './tokens';

type Color = string;

/** Un motivo es un mapa de bits: '.' fondo, '1' color a, '2' color b. Se repite a lo ancho. */
const MOTIVOS = {
  // Cadena de rombos con el centro de otro color (la banda azul de la referencia 6).
  rombo: [
    '...1.....',
    '..121....',
    '.12221...',
    '1222221..',
    '.12221...',
    '..121....',
    '...1.....',
  ],
  // Gancho en S (las cadenas amarillas de las referencias 1 y 5).
  ese: [
    '.11..',
    '1....',
    '.11..',
    '...1.',
    '.11..',
  ],
  // Zigzag escalonado.
  escalon: [
    '1.......1',
    '11.....11',
    '.11...11.',
    '..11.11..',
    '...111...',
  ],
  // Cordón trenzado blanco y negro (las líneas finas de las referencias 4 y 5).
  trenza: [
    '11..',
    '.11.',
  ],
} as const;

type Motivo = keyof typeof MOTIVOS;

type Fila =
  | { tipo: 'franja'; alto: number; color: Color }
  | { tipo: 'motivo'; motivo: Motivo; alto: number; fondo: Color; a: Color; b?: Color };

const franja = (alto: number, color: Color): Fila => ({ tipo: 'franja', alto, color });
const motivo = (m: Motivo, alto: number, fondo: Color, a: Color, b?: Color): Fila => ({ tipo: 'motivo', motivo: m, alto, fondo, a, b });

/** Las composiciones. Fijas a propósito: la misma manta en cada build, como un tejido de verdad. */
const VARIANTES: Record<'faja' | 'lliclla' | 'gala', Fila[]> = {
  // Banda del encabezado, ~18 pt: pocas franjas y un rombo grande, para que se lea como tejido y no como ruido.
  faja: [
    franja(3, M.magenta),
    franja(2, M.amarillo),
    motivo('rombo', 9, M.cobalto, M.turquesa, M.blanco),
    franja(2, M.amarillo),
    franja(3, M.verde),
  ],
  // La base sobre la que se sienta Chaski, ~22 pt. Sin rojo: está cerca de los títulos de estado.
  lliclla: [
    franja(1.5, M.blanco),
    franja(2.5, M.naranja),
    franja(1.5, M.amarillo),
    motivo('rombo', 9, M.morado, M.rosado, M.amarillo),
    franja(1.5, M.amarillo),
    franja(2.5, M.turquesa),
    franja(3, M.verde),
  ],
  // El héroe del onboarding: la manta entera, ~110 pt.
  gala: [
    franja(5, M.naranja),
    franja(3, M.amarillo),
    franja(2, M.blanco),
    motivo('trenza', 3, M.hilo, M.blanco),
    franja(2, M.blanco),
    franja(6, M.magenta),
    franja(3, M.rosado),
    franja(2, M.blanco),
    motivo('rombo', 14, M.cobalto, M.turquesa, M.blanco),
    franja(2, M.blanco),
    franja(4, M.verde),
    franja(3, M.lima),
    franja(2, M.blanco),
    motivo('ese', 10, M.morado, M.amarillo),
    franja(2, M.blanco),
    franja(5, M.turquesa),
    franja(4, M.cobalto),
    franja(2, M.blanco),
    motivo('escalon', 10, M.rojo, M.amarillo),
    franja(2, M.blanco),
    franja(5, M.magenta),
    franja(3, M.naranja),
    franja(2, M.blanco),
    motivo('trenza', 3, M.hilo, M.blanco),
    franja(2, M.blanco),
    franja(4, M.morado),
    franja(6, M.verde),
  ],
};

export type VarianteManta = keyof typeof VARIANTES;

export function altoDeManta(v: VarianteManta, escala = 1): number {
  return VARIANTES[v].reduce((s, f) => s + f.alto, 0) * escala;
}

export function Manta({ variante, ancho, escala = 1 }: { variante: VarianteManta; ancho?: number; escala?: number }) {
  const [medido, setMedido] = useState(0);
  const w = ancho ?? medido;
  const filas = VARIANTES[variante];
  const alto = altoDeManta(variante, escala);

  const nodos: React.ReactElement[] = [];
  let y = 0;
  filas.forEach((f, n) => {
    const h = f.alto * escala;
    if (f.tipo === 'franja') {
      nodos.push(<Rect key={n} x={0} y={y} width={w} height={h} fill={f.color} />);
    } else {
      const mapa = MOTIVOS[f.motivo];
      const punto = h / mapa.length;
      const reps = Math.ceil(w / (mapa[0].length * punto)) + 1;
      nodos.push(<Rect key={`${n}f`} x={0} y={y} width={w} height={h} fill={f.fondo} />);
      mapa.forEach((fila, r) => {
        tramos(fila, reps).forEach((t, k) => {
          nodos.push(
            <Rect
              key={`${n}-${r}-${k}`}
              x={t.desde * punto}
              y={y + r * punto}
              width={t.largo * punto + 0.3}
              height={punto + 0.3}
              fill={t.valor === '2' ? f.b ?? f.a : f.a}
            />,
          );
        });
      });
    }
    y += h;
  });

  return (
    <View
      style={{ height: alto, width: ancho ?? '100%', overflow: 'hidden' }}
      onLayout={ancho ? undefined : (e: LayoutChangeEvent) => setMedido(e.nativeEvent.layout.width)}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants">
      {w > 0 ? (
        <Svg width={w} height={alto}>
          {nodos}
        </Svg>
      ) : null}
    </View>
  );
}
