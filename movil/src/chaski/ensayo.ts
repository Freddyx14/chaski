// Ensayo de la negativa (D37, checklist §6.6): una frase fija que la barrera bloquea siempre.
// HONESTIDAD: el ensayo SIEMBRA la traducción errada en vez de la del traductor, para mostrar que la barrera la
// atrapa. La pantalla lo dice en claro («Ensayo: simulamos que el traductor se equivocó»); nunca se presenta
// como un error real del traductor. Bloqueó 16/16 en corridas reales, motivo «cambió un dato crítico: prohibiciones».
import { File, Paths } from 'expo-file-system';
import { useSyncExternalStore } from 'react';

export const FRASE_NEGATIVA_DEMO = {
  es: 'Tómela con agua, no con té',
  /** Correcto (familia p18). */
  quy: 'Yakuwan upyay, ama tewan upyaychu.',
  /** Con el error sembrado: sin «ama … -chu», dice «tómela con té». */
  quySembrado: 'Yakuwan upyay, tewan upyay.',
} as const;

// El modo ensayo se prende en Ajustes y queda guardado en el teléfono. Apagado por defecto: en una consulta real
// no existe el atajo.
const ARCHIVO = () => new File(Paths.document, 'chaski-ensayo.json');
let activo = false;
let leido = false;
const oyentes = new Set<() => void>();

async function leer() {
  if (leido) return;
  leido = true;
  try {
    const f = ARCHIVO();
    if (f.exists) activo = !!JSON.parse(await f.text()).activo;
  } catch {}
  oyentes.forEach((o) => o());
}

export async function fijarEnsayo(valor: boolean) {
  activo = valor;
  const f = ARCHIVO();
  if (!f.exists) f.create();
  await f.write(JSON.stringify({ activo: valor }));
  oyentes.forEach((o) => o());
}

export function useEnsayo(): boolean {
  leer();
  return useSyncExternalStore((o) => (oyentes.add(o), () => oyentes.delete(o)), () => activo);
}
