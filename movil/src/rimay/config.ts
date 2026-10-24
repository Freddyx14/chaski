// La dirección del servicio cambia cada vez que se levanta el túnel, así que se guarda en el teléfono
// y se cambia desde Ajustes, sin recompilar.
import { File, Paths } from 'expo-file-system';

const ARCHIVO = () => new File(Paths.document, 'rimay-config.json');
const POR_DEFECTO = process.env.EXPO_PUBLIC_RIMAY_API ?? '';

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
