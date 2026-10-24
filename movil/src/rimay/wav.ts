// Audio puro, sin dependencias de React Native, para poder probarlo con node.

const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
const B64_INDEX: Record<string, number> = Object.fromEntries([...B64].map((c, i) => [c, i]));

/** base64 -> bytes. Propio, para no depender de que el motor traiga `atob`. */
export function base64ABytes(b64: string): Uint8Array {
  const limpio = b64.replace(/[^A-Za-z0-9+/]/g, '');
  const largo = Math.floor((limpio.length * 3) / 4);
  const salida = new Uint8Array(largo);
  let o = 0;
  for (let i = 0; i < limpio.length; i += 4) {
    const a = B64_INDEX[limpio[i]] ?? 0;
    const b = B64_INDEX[limpio[i + 1]] ?? 0;
    const c = B64_INDEX[limpio[i + 2]] ?? 0;
    const d = B64_INDEX[limpio[i + 3]] ?? 0;
    const n = (a << 18) | (b << 12) | (c << 6) | d;
    if (o < largo) salida[o++] = (n >> 16) & 0xff;
    if (o < largo && i + 2 < limpio.length) salida[o++] = (n >> 8) & 0xff;
    if (o < largo && i + 3 < limpio.length) salida[o++] = n & 0xff;
  }
  return salida;
}

export type Envolvente = {
  /** Un valor 0..1 por ventana, normalizado al pico del audio. */
  niveles: number[];
  ventanaMs: number;
  segundos: number;
};

/**
 * Lee un WAV PCM de 16 bits y devuelve el volumen por ventana. Es lo que mueve la boca de Chaski:
 * abierta donde hay voz, cerrada en los silencios. Si el archivo no es un WAV que entendemos,
 * devuelve null y la app alterna a ritmo fijo.
 */
export function envolvente(bytes: Uint8Array, ventanaMs = 50): Envolvente | null {
  if (bytes.length < 44) return null;
  const vista = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const texto = (o: number) => String.fromCharCode(bytes[o], bytes[o + 1], bytes[o + 2], bytes[o + 3]);
  if (texto(0) !== 'RIFF' || texto(8) !== 'WAVE') return null;

  let canales = 1, frecuencia = 16000, bits = 16;
  let datos = -1, largoDatos = 0;
  let o = 12;
  while (o + 8 <= bytes.length) {
    const id = texto(o);
    const tam = vista.getUint32(o + 4, true);
    if (id === 'fmt ') {
      canales = vista.getUint16(o + 10, true);
      frecuencia = vista.getUint32(o + 12, true);
      bits = vista.getUint16(o + 22, true);
    } else if (id === 'data') {
      datos = o + 8;
      largoDatos = Math.min(tam, bytes.length - datos);
      break;
    }
    o += 8 + tam + (tam % 2);
  }
  if (datos < 0 || bits !== 16 || canales < 1) return null;

  const muestras = Math.floor(largoDatos / 2 / canales);
  const porVentana = Math.max(1, Math.round((frecuencia * ventanaMs) / 1000));
  const niveles: number[] = [];
  for (let inicio = 0; inicio < muestras; inicio += porVentana) {
    const fin = Math.min(muestras, inicio + porVentana);
    let suma = 0;
    for (let m = inicio; m < fin; m++) {
      const v = vista.getInt16(datos + m * 2 * canales, true) / 32768;
      suma += v * v;
    }
    niveles.push(Math.sqrt(suma / (fin - inicio)));
  }
  const pico = Math.max(...niveles, 1e-9);
  return {
    niveles: niveles.map((n) => n / pico),
    ventanaMs,
    segundos: muestras / frecuencia,
  };
}

/** ¿La boca va abierta en este instante? Umbral relativo al pico. */
export function bocaAbierta(env: Envolvente | null, segundo: number, umbral = 0.22): boolean {
  if (!env) return Math.floor(segundo * 6) % 2 === 0;
  const i = Math.floor((segundo * 1000) / env.ventanaMs);
  return (env.niveles[i] ?? 0) >= umbral;
}
