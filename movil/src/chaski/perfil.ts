// Quién usa este teléfono (D27): su idioma, su nombre y si es personal de salud o paciente.
// Se guarda solo en el teléfono.
import { File, Paths } from 'expo-file-system';
import { useSyncExternalStore } from 'react';

export type Idioma = 'castellano' | 'quechua';
export type Rol = 'personal' | 'paciente';
export type Perfil = { idioma: Idioma; nombre: string; rol: Rol };

const ARCHIVO = () => new File(Paths.document, 'chaski-perfil.json');

let perfil: Perfil | null | undefined; // undefined = todavía no se leyó
const oyentes = new Set<() => void>();

export async function cargarPerfil(): Promise<Perfil | null> {
  if (perfil !== undefined) return perfil;
  try {
    const f = ARCHIVO();
    perfil = f.exists ? (JSON.parse(await f.text()) as Perfil) : null;
  } catch {
    perfil = null;
  }
  oyentes.forEach((o) => o());
  return perfil;
}

export async function guardarPerfil(p: Perfil | null) {
  perfil = p;
  const f = ARCHIVO();
  if (p === null) {
    if (f.exists) f.delete();
  } else {
    if (!f.exists) f.create();
    await f.write(JSON.stringify(p));
  }
  oyentes.forEach((o) => o());
}

export function usePerfil(): Perfil | null | undefined {
  return useSyncExternalStore((o) => (oyentes.add(o), () => oyentes.delete(o)), () => perfil);
}
