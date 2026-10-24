// Cliente del servicio de Ricardo (ricardo-artifacts/servicio/app.py). Contrato: CONTRATO.md.
import { File, Paths } from 'expo-file-system';

import { leerServidor } from './config';
import type { Rol } from './perfil';
import type { RespuestaEnfermera, RespuestaEscuchar, RespuestaPaciente } from './modelo';

export class SinServidor extends Error {}

async function pedir<T>(ruta: string, cuerpo: FormData, segundos = 90): Promise<T> {
  const base = await leerServidor();
  if (!base) throw new SinServidor('Falta la dirección del servicio');
  const corte = new AbortController();
  const reloj = setTimeout(() => corte.abort(), segundos * 1000);
  try {
    const r = await fetch(`${base}${ruta}`, { method: 'POST', body: cuerpo, signal: corte.signal });
    const d = await r.json();
    if (!r.ok || d?.error) throw new Error(d?.error ?? `HTTP ${r.status}`);
    return d as T;
  } finally {
    clearTimeout(reloj);
  }
}

function conAudio(uri: string, nombre = 'turno.wav'): FormData {
  const f = new FormData();
  // React Native sube archivos locales así: { uri, name, type }.
  f.append('audio', { uri, name: nombre, type: 'audio/wav' } as unknown as Blob);
  return f;
}

/** Voz de la enfermera → texto (Cartesia ink-whisper). */
export function escuchar(uri: string) {
  return pedir<RespuestaEscuchar>('/escuchar', conAudio(uri));
}

/** Castellano → auditoría → quechua. Sin audio: la voz se pide aparte para mostrar el texto antes. */
export function turnoEnfermera(texto: string, rol: Rol) {
  const f = new FormData();
  f.append('texto', texto);
  // D27: el rol elige el prompt del agente y el resumen. El servicio lo ignora hasta que lo use.
  f.append('rol', rol);
  f.append('modo_ensayo', 'true');
  f.append('rapido', 'true');
  f.append('con_audio', 'false');
  return pedir<RespuestaEnfermera>('/turno/enfermera', f, 120);
}

/** Audio del paciente → idioma, lo que se oyó en chanka y lo que quiso decir. */
export function turnoPaciente(uri: string, rol: Rol) {
  const f = conAudio(uri);
  f.append('rol', rol);
  return pedir<RespuestaPaciente>('/turno/paciente', f, 120);
}

/** Texto en quechua → WAV (mms-tts-quy). Devuelve el archivo local y sus bytes, para la boca de Chaski. */
export async function voz(quechua: string): Promise<{ uri: string; bytes: Uint8Array }> {
  const base = await leerServidor();
  if (!base) throw new SinServidor('Falta la dirección del servicio');
  const f = new FormData();
  f.append('texto', quechua);
  const r = await fetch(`${base}/voz`, { method: 'POST', body: f });
  if (!r.ok) throw new Error(`voz HTTP ${r.status}`);
  const bytes = new Uint8Array(await r.arrayBuffer());
  const archivo = new File(Paths.cache, `voz-${Date.now()}.wav`);
  archivo.create();
  await archivo.write(bytes);
  return { uri: archivo.uri, bytes };
}

export async function salud(): Promise<Record<string, unknown>> {
  const base = await leerServidor();
  if (!base) throw new SinServidor('Falta la dirección del servicio');
  const r = await fetch(`${base}/salud`);
  return r.json();
}

export type Lectura = {
  seguro: boolean;
  medicamento: string | null;
  concentracion: string | null;
  presentacion: string | null;
  para_que_sirve: string;
  advertencias: string[];
  no_leido: string[];
  coincide_con_lo_dicho: boolean | null;
  segundos: number;
};

/** Foto de la caja o la receta → Claude visión (F9). `dicho` es lo último que dijo la enfermera. */
export function ver(uri: string, dicho: string) {
  const f = new FormData();
  f.append('imagen', { uri, name: 'receta.jpg', type: 'image/jpeg' } as unknown as Blob);
  if (dicho) f.append('dicho', dicho);
  return pedir<Lectura>('/ver', f, 60);
}

export type Resumen = {
  rol: Rol;
  resumen: string;
  indicaciones: string[];
  senales_de_alarma: string[];
  proxima_cita: string | null;
  dudas: string[];
  no_se_dijo: string[];
  texto_para_decir: string;
};

/** F11: el resumen de la consulta, según quién lo lee (D27). Lo bloqueado nunca entra como indicación. */
export function resumen(turnos: { lado: string; castellano: string; quechua: string; estado: string }[], rol: Rol) {
  const f = new FormData();
  f.append('turnos', JSON.stringify(turnos));
  f.append('rol', rol);
  return pedir<Resumen>('/resumen', f, 90);
}
