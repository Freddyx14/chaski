// Colores SOLO desde design/tokens.json (D24). Nunca un color escrito a mano en la app.
import tokens from '../../../design/tokens.json';

export const C = tokens.color;
export const ESCALA = { display: 34, h1: 24, h2: 20, cuerpo: 17, chico: 15, mini: 13 } as const;
