// Modo conversación (como el modo voz de ChatGPT): se prende una vez y Chaski vuelve a escuchar solo después de
// cada turno. Esta función decide CUÁNDO, a partir de lo que muestra la pantalla. Pura, para probarla.

export type Pantalla = {
  f: string;
  /** El audio del turno ya terminó de prepararse (solo «dicho»). */
  vozLista?: boolean;
  /** Ensayo de la barrera: la tarjeta roja se queda para que el jurado la lea. */
  ensayo?: boolean;
  /** Error del micrófono (grabación vacía o muda), no de la red. */
  deGrabacion?: boolean;
};

/** Espera tras callar el audio: deja pasar la cola del parlante para que Chaski no se oiga a sí mismo. */
export const COLA_MS = 700;
/** La tarjeta roja se lee antes de volver a escuchar. */
export const LECTURA_BLOQUEO_MS = 4000;

/**
 * Milisegundos hasta volver a escuchar, o null si no toca (piensa, habla, graba, o espera un toque).
 * Mientras suena cualquier audio el micrófono queda cerrado.
 */
export function esperaParaEscuchar(p: Pantalla, sonando: boolean): number | null {
  if (sonando) return null;
  switch (p.f) {
    case 'listo':
      return 300;
    case 'dicho':
      return p.vozLista && !p.ensayo ? COLA_MS : null;
    case 'pregunta':
    case 'respuesta':
    case 'noentendi':
    case 'frase':
    case 'paciente':
      return COLA_MS;
    case 'bloqueado':
      return p.ensayo ? null : LECTURA_BLOQUEO_MS;
    case 'error':
      // Sin red o sin servicio se queda en la pantalla de error, con sus botones: escuchar en bucle no lo arregla.
      return p.deGrabacion ? 300 : null;
    default:
      return null;
  }
}
