// Cliente del servicio de Ricardo (ricardo-artifacts/servicio/app.py). Contrato: CONTRATO.md.
import { File, Paths } from 'expo-file-system';

import { leerServidor } from './config';
import { contextoActual, guardarContexto } from './consulta';
import type { Rol } from './perfil';
import bancoReal from '../../../app/chaski/banco.json';
import bancoDemo from './banco-demo.json';
import { esReintentable, frasesConTag, type FraseBanco, type RespuestaEnfermera, type RespuestaEscuchar, type RespuestaPaciente } from './modelo';

export class SinServidor extends Error {}

// El servicio va por ngrok gratuito, que a veces responde con una página de aviso en vez de la API.
// Esta cabecera la salta; con otros túneles se ignora.
const CABECERAS = { 'ngrok-skip-browser-warning': '1' };

/**
 * Un fallo de red o del servicio, con la ruta y el tipo para la línea gris de la pantalla de error
 * («/ver · 502», «/turno/enfermera · sin respuesta en 90 s»): así se distingue un reinicio del servicio de un
 * problema de red del teléfono.
 */
export class FalloServicio extends Error {
  constructor(readonly ruta: string, readonly tipo: string, readonly reintentable: boolean) {
    super(`${ruta} · ${tipo}`);
  }
}

const ESPERA_REINTENTO_MS = 2000;

async function pedirUnaVez<T>(base: string, ruta: string, cuerpo: FormData, segundos: number): Promise<T> {
  const corte = new AbortController();
  const reloj = setTimeout(() => corte.abort(), segundos * 1000);
  let r: Response;
  try {
    r = await fetch(`${base}${ruta}`, { method: 'POST', body: cuerpo, signal: corte.signal, headers: CABECERAS });
  } catch (e) {
    const agotado = (e as Error)?.name === 'AbortError';
    // Un turno que se agotó NO se reintenta: repetirlo duplicaría la espera. Solo los cortes rápidos.
    throw new FalloServicio(ruta, agotado ? `sin respuesta en ${segundos} s` : 'sin conexión', !agotado);
  } finally {
    clearTimeout(reloj);
  }
  let d: any = null;
  try {
    d = await r.json();
  } catch {
    throw new FalloServicio(ruta, String(r.status), esReintentable(r.status) || !r.ok);
  }
  if (!r.ok) throw new FalloServicio(ruta, String(r.status), esReintentable(r.status));
  if (d?.error) throw new Error(d.error);
  return d as T;
}

/** POST con UN reintento automático a los ~2 s si falló la red o el servicio se estaba reiniciando. */
async function pedir<T>(ruta: string, cuerpo: FormData, segundos = 90): Promise<T> {
  const base = await leerServidor();
  if (!base) throw new SinServidor('Falta la dirección del servicio');
  try {
    return await pedirUnaVez<T>(base, ruta, cuerpo, segundos);
  } catch (e) {
    if (!(e instanceof FalloServicio) || !e.reintentable) throw e;
    await new Promise((ok) => setTimeout(ok, ESPERA_REINTENTO_MS));
    return pedirUnaVez<T>(base, ruta, cuerpo, segundos);
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

/** Solo el idioma del audio (D11), sin Claude: ~60-150 ms. Decide de qué lado va el turno. */
export function idioma(uri: string) {
  return pedir<{ codigo: string; confianza: number }>('/idioma', conAudio(uri), 8);
}

/** El modo de la consulta que el intérprete recibe en `contexto.modo` (D35). */
export type Modo = 'consulta' | 'emergencia' | 'receta';

/** `contexto` del turno anterior, como JSON en el form, con el modo puesto. Lo pide el orquestador. */
function conContexto(f: FormData, modo?: Modo) {
  const c = contextoActual();
  if (c || modo) f.append('contexto', JSON.stringify({ ...(c ?? {}), ...(modo ? { modo } : {}) }));
}

async function turno<T extends { contexto?: unknown }>(ruta: string, f: FormData): Promise<T> {
  const r = await pedir<T>(ruta, f, 120);
  guardarContexto(r.contexto);
  return r;
}

/**
 * Castellano → intérprete → traducción → barreras → crítico (contrato `Resultado`). Hasta que el servicio
 * cambie, devuelve la forma vieja (auditoría sola); `modelo.ts` entiende las dos.
 * `traduccionSembrada`: SOLO para el ensayo de la negativa (D37). Reemplaza la traducción para mostrar que la
 * barrera atrapa el error; la pantalla lo dice en claro y nunca se presenta como un error real del traductor.
 */
export function turnoEnfermera(texto: string, rol: Rol, opciones: { modo?: Modo; traduccionSembrada?: string } = {}) {
  const f = new FormData();
  f.append('texto', texto);
  // D27: el rol elige el prompt del agente y el resumen.
  f.append('rol', rol);
  f.append('modo_ensayo', 'true');
  f.append('rapido', 'true');
  f.append('con_audio', 'false');
  if (opciones.traduccionSembrada) f.append('traduccion_sembrada', opciones.traduccionSembrada);
  conContexto(f, opciones.modo);
  return turno<RespuestaEnfermera>('/turno/enfermera', f);
}

/** Audio del paciente → idioma, lo que se oyó en chanka y lo que quiso decir. */
export function turnoPaciente(uri: string, rol: Rol, opciones: { modo?: Modo } = {}) {
  const f = conAudio(uri);
  f.append('rol', rol);
  conContexto(f, opciones.modo);
  return turno<RespuestaPaciente>('/turno/paciente', f);
}

/** Texto en quechua → WAV (mms-tts-quy). Devuelve el archivo local y sus bytes, para la boca de Chaski. */
export async function voz(quechua: string): Promise<{ uri: string; bytes: Uint8Array }> {
  const base = await leerServidor();
  if (!base) throw new SinServidor('Falta la dirección del servicio');
  const f = new FormData();
  f.append('texto', quechua);
  const r = await fetch(`${base}/voz`, { method: 'POST', body: f, headers: CABECERAS });
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
  const corte = new AbortController();
  const reloj = setTimeout(() => corte.abort(), 8000);
  try {
    const r = await fetch(`${base}/salud`, { headers: CABECERAS, signal: corte.signal });
    if (!r.ok) throw new FalloServicio('/salud', String(r.status), true);
    return await r.json();
  } finally {
    clearTimeout(reloj);
  }
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
  // Si el servicio llega a leer la posología de una receta escrita, viene aquí; si no, la confirma la enfermera.
  cantidad?: number | null;
  unidad?: string | null;
  cada_horas?: number | null;
  dias?: number | null;
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
  /** D36: palabras quechua nuevas de esta consulta, para aprender. */
  glosario?: { quechua: string; castellano: string }[];
};

/** F11: el resumen de la consulta, según quién lo lee (D27). Lo bloqueado nunca entra como indicación. */
export function resumen(turnos: { lado: string; castellano: string; quechua: string; estado: string }[], rol: Rol) {
  const f = new FormData();
  f.append('turnos', JSON.stringify(turnos));
  f.append('rol', rol);
  return pedir<Resumen>('/resumen', f, 90);
}

/**
 * El banco de frases verificadas (D34, §4). Primero el servicio (`GET /banco?tag=`); si no responde, la
 * copia empaquetada de app/chaski/banco.json.
 */
export async function banco(tag: string): Promise<{ frases: FraseBanco[]; origen: 'servicio' | 'local' }> {
  try {
    const base = await leerServidor();
    if (base) {
      const corte = new AbortController();
      const reloj = setTimeout(() => corte.abort(), 4000);
      const r = await fetch(`${base}/banco?tag=${encodeURIComponent(tag)}`, { headers: CABECERAS, signal: corte.signal });
      clearTimeout(reloj);
      if (r.ok) {
        const d = await r.json();
        const frases: FraseBanco[] = Array.isArray(d) ? d : d.frases ?? [];
        if (frases.length) return { frases: frasesConTag(frases, tag), origen: 'servicio' };
      }
    }
  } catch {}
  // Copia empaquetada del banco real (app/chaski/banco.json, por watchFolders); el fixture es el último recurso.
  const local = Array.isArray(bancoReal) && bancoReal.length ? (bancoReal as FraseBanco[]) : (bancoDemo.frases as FraseBanco[]);
  return { frases: frasesConTag(local, tag), origen: 'local' };
}

/** Audio de una frase del banco: el verificado si existe; si no, la voz de Chaski con su quechua revisado. */
export async function audioDeFrase(f: FraseBanco): Promise<{ uri: string; headers?: Record<string, string> }> {
  if (f.audio) return { uri: f.audio, headers: CABECERAS };
  const { uri } = await voz(f.quy);
  return { uri };
}
