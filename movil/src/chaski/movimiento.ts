// Reglas del movimiento de D29, puras para probarlas con node. La animación vive en los componentes;
// aquí solo se decide QUÉ se enciende y CUÁNTO, a partir de datos reales (volumen, avance del audio).

/** Umbrales de las tres hebras, de adentro hacia afuera: con más voz se encienden más hebras. */
export const UMBRALES = [0.12, 0.4, 0.7] as const;

/** Cuántas hebras se encienden con este nivel (0..1). 0 = silencio, 3 = voz fuerte. */
export function hebrasEncendidas(nivel: number, umbrales: readonly number[] = UMBRALES): number {
  return umbrales.filter((u) => nivel >= u).length;
}

/** Nivel 0..1 desde el metering del grabador (dB, −160..0). −55 dB es silencio de sala, −5 dB voz cerca. */
export function nivelDesdeDb(db: number | undefined): number {
  if (db === undefined || !Number.isFinite(db)) return 0;
  return Math.max(0, Math.min(1, (db + 55) / 50));
}

/** Cuántas palabras ya dijo la voz, repartiendo el audio en partes iguales por palabra. */
export function palabrasDichas(total: number, progreso: number): number {
  if (total <= 0) return 0;
  return Math.max(0, Math.min(total, Math.ceil(total * Math.max(0, Math.min(1, progreso)))));
}

/** Brillo de la estrella `i` de `n` cuando el brillo gira en `giro` (0..n): llena cerca, tenue lejos. */
export function brilloDeEstrella(i: number, n: number, giro: number): number {
  'worklet';
  const d = Math.abs(((giro - i) % n + n) % n);
  const cerca = Math.min(d, n - d);
  return cerca < 1 ? 1 - 0.7 * cerca : 0.3;
}
