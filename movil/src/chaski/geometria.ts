// Geometría de los motivos de D29 (opción L = D + I). Pura, para probarla con node.
//
// Una sola figura hace todo: un cuadrado con las cuatro esquinas cortadas en escalones.
//  - Pocos escalones chicos  → la silueta escalonada de Chaski (D).
//  - Corte hondo, 2-3 pasos  → la chakana, la cruz andina escalonada (I).
//  - Un solo paso grande     → la crucecita de los rombos de progreso y la constelación.

export type Punto = [number, number];

/**
 * Contorno de un cuadrado de lado `lado` que empieza en (x0, y0), con cada esquina cortada por
 * `pasos` escalones de `paso` puntos. Sentido horario, empezando arriba a la izquierda del borde superior.
 */
export function escalonado(lado: number, pasos: number, paso: number, x0 = 0, y0 = 0): Punto[] {
  const corte = pasos * paso;
  if (corte * 2 > lado) throw new Error(`corte ${corte} demasiado hondo para un lado de ${lado}`);
  // La esquina superior derecha, en coordenadas locales del cuadrado.
  const esquina: Punto[] = [[lado - corte, 0]];
  for (let k = 1; k <= pasos; k++) {
    esquina.push([lado - corte + (k - 1) * paso, k * paso]);
    esquina.push([lado - corte + k * paso, k * paso]);
  }
  // Las otras tres esquinas son la misma girada 90° en sentido horario: (x, y) → (lado − y, x).
  const girar = ([x, y]: Punto): Punto => [lado - y, x];
  const contorno: Punto[] = [];
  let actual = esquina;
  for (let i = 0; i < 4; i++) {
    contorno.push(...actual);
    actual = actual.map(girar);
  }
  return contorno.map(([x, y]) => [x + x0, y + y0]);
}

/** El mismo contorno metido `margen` puntos hacia adentro. Los escalones quedan paralelos. */
export function escalonadoAdentro(lado: number, pasos: number, paso: number, margen: number): Punto[] {
  return escalonado(lado - 2 * margen, pasos, paso, margen, margen);
}

/** Puntos → atributo `d` de un <Path> de SVG, cerrado. */
export function trazo(puntos: Punto[]): string {
  const r = (n: number) => Math.round(n * 100) / 100;
  return 'M' + puntos.map(([x, y]) => `${r(x)} ${r(y)}`).join('L') + 'Z';
}

/** La figura escalonada de Chaski a un tamaño dado: cuántos escalones y de cuánto, legibles en chico y en grande. */
export function escalonesDeChaski(lado: number): { pasos: number; paso: number } {
  // Como en la maqueta L: cinco escalones que comen ~15 % del lado en cada esquina.
  const paso = Math.max(3, Math.round(lado * 0.03));
  return { pasos: lado >= 150 ? 5 : 4, paso };
}
