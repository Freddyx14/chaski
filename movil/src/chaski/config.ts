// La dirección del servicio cambia cada vez que se levanta el túnel, así que se guarda en el teléfono
// y se cambia desde Ajustes, sin recompilar.
import { File, Paths } from 'expo-file-system';

import publicada from '../../../ricardo-artifacts/servicio/url.json';

const ARCHIVO = () => new File(Paths.document, 'rimay-config.json');

// Por defecto, la dirección que Ricardo publica en git (servicio/url.json). Ajustes la puede pisar.
const POR_DEFECTO = process.env.EXPO_PUBLIC_RIMAY_API ?? publicada.url ?? '';

let actual: string | null = null;

export async function leerServidor(): Promise<string> {
  if (actual !== null) return actual;
  try {
    const f = ARCHIVO();
    if (f.exists) {
      const d = JSON.parse(await f.text());
      actual = typeof d.servidor === 'string' ? d.servidor : POR_DEFECTO;
      return actual ?? POR_DEFECTO;
    }
  } catch {}
  actual = POR_DEFECTO;
  return POR_DEFECTO;
}

export async function guardarServidor(url: string): Promise<void> {
  const limpio = url.trim().replace(/\/+$/, '');
  actual = limpio;
  const f = ARCHIVO();
  if (!f.exists) f.create();
  await f.write(JSON.stringify({ servidor: limpio }));
}
