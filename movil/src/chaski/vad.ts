// Detección de voz para el modo conversación: decide sola cuándo empieza y cuándo termina un turno, con el
// nivel (dB) que ya da la grabadora. Pura y sin reloj propio: recibe el tiempo, así se prueba sin micrófono.

export const VAD = {
  /** Primeros ms de cada escucha: miden el ruido de la sala. */
  calibrarMs: 500,
  /** Cuánto sobre el piso cuenta como voz. */
  sobrePisoDb: 12,
  /** Para terminar basta bajar a piso + esto (histéresis: no corta en cada sílaba suave). */
  silencioDb: 6,
  /** Voz sostenida para empezar el turno: una tos o un golpe no lo abren. */
  inicioMs: 200,
  /** Silencio sostenido para cerrar el turno. */
  finMs: 800,
  /** Tope de un turno, aunque la sala no se calle. */
  maxTurnoMs: 20000,
  /** Sin nadie que hable: se reinicia la grabación para no acumular un archivo enorme y se recalibra. */
  reinicioMs: 30000,
  /** Límites del piso: el simulador da -160 (silencio digital) y una sala ruidosa no debe volver sorda la escucha. */
  pisoMin: -60,
  pisoMax: -30,
};

export type EstadoVad = {
  t0: number;
  muestras: number[];
  piso: number | null;
  sobreDesde: number | null;
  bajoDesde: number | null;
  inicio: number | null;
  /** Ya dio «fin» o «reiniciar»: no vuelve a disparar hasta una escucha nueva. */
  cerrado: boolean;
};

export type EventoVad = 'inicio' | 'fin' | 'reiniciar' | null;

export function nuevoVad(t0: number): EstadoVad {
  return { t0, muestras: [], piso: null, sobreDesde: null, bajoDesde: null, inicio: null, cerrado: false };
}

function mediana(xs: number[]): number {
  const o = [...xs].sort((a, b) => a - b);
  return o[Math.floor(o.length / 2)];
}

/** Un paso del detector. Devuelve el estado nuevo y, si pasó algo, el evento. */
export function pasoVad(s: EstadoVad, db: number | undefined, t: number, c = VAD): [EstadoVad, EventoVad] {
  if (s.cerrado || db === undefined || !Number.isFinite(db)) return [s, null];
  if (s.piso === null) {
    const muestras = [...s.muestras, db];
    if (t - s.t0 < c.calibrarMs) return [{ ...s, muestras }, null];
    const piso = Math.min(c.pisoMax, Math.max(c.pisoMin, mediana(muestras)));
    return [{ ...s, muestras, piso }, null];
  }
  const umbral = s.piso + c.sobrePisoDb;
  if (s.inicio === null) {
    if (t - s.t0 >= c.reinicioMs) return [{ ...s, cerrado: true }, 'reiniciar'];
    if (db >= umbral) {
      const sobreDesde = s.sobreDesde ?? t;
      if (t - sobreDesde >= c.inicioMs) return [{ ...s, sobreDesde, inicio: sobreDesde, bajoDesde: null }, 'inicio'];
      return [{ ...s, sobreDesde }, null];
    }
    return [{ ...s, sobreDesde: null }, null];
  }
  if (t - s.inicio >= c.maxTurnoMs) return [{ ...s, cerrado: true }, 'fin'];
  if (db < s.piso + c.silencioDb) {
    const bajoDesde = s.bajoDesde ?? t;
    if (t - bajoDesde >= c.finMs) return [{ ...s, bajoDesde, cerrado: true }, 'fin'];
    return [{ ...s, bajoDesde }, null];
  }
  return [{ ...s, bajoDesde: null }, null];
}
