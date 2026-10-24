// Lo que devuelve el servicio de Ricardo (ricardo-artifacts/servicio) y cómo lo lee la pantalla.
// Puro a propósito: se prueba con node sin simulador.

export type Diferencia = { campo: string; original: string; retraducido: string };

/** Las cinco acciones del intérprete agente (D32, plan/arquitectura-interprete.md §2). */
export type Accion = 'traducir' | 'repreguntar' | 'responder' | 'no_entendi' | 'usar_frase_banco';

/** Una frase verificada del banco (§4): traducción y audio que sabemos que están bien. */
export type FraseBanco = {
  id: string;
  es: string;
  quy: string;
  audio?: string | null;
  tags: string[];
  fuente?: string;
};

/**
 * Los campos de la `Decision` que traen /turno/enfermera y /turno/paciente cuando el intérprete está
 * integrado. Todos opcionales: sin `accion` la app hace exactamente lo de antes (traducir).
 * El servicio puede mandarlos sueltos o dentro de `decision`.
 */
export type CamposDecision = {
  accion?: Accion;
  para?: 'personal' | 'paciente';
  idioma_salida?: 'spa' | 'quy';
  texto_pulido?: string;
  motivo?: string | null;
  frase_banco_id?: string | null;
  dato_faltante?: string | null;
  frase_banco?: FraseBanco | null;
  audio_wav_b64?: string | null;
  decision?: Omit<CamposDecision, 'decision'> | null;
};

export type RespuestaEnfermera = CamposDecision & {
  quechua: string;
  retraduccion: string;
  aprobado_por_auditoria: boolean;
  motivo: string | null;
  terminos_inseguros: string[];
  diferencias: Diferencia[];
  se_dice: boolean;
  aviso: string | null;
  total_ms: number;
};

export type RespuestaPaciente = CamposDecision & {
  idioma: { codigo: string; confianza: number } | null;
  chanka_oido: string;
  castellano: string;
  literal: string;
  dudas: string[];
  seguro: boolean;
  total_ms: number;
};

export type RespuestaEscuchar = { texto: string; ms: number };

/** Nombre que la enfermera entiende para cada campo que compara la auditoría (app/chaski/hechos.py). */
export function nombreDelCampo(campo: string): string {
  const c = campo.toLowerCase();
  // Primero los campos cuyo nombre contiene otra palabra clave («ir_ya_si (cantidad de señales)»).
  if (c.includes('ir_ya_si')) return 'Señales de alarma';
  if (c.includes('proxima_cita')) return 'Próxima cita';
  if (c.includes('cantidad')) return 'Dosis';
  if (c.includes('cada_horas')) return 'Horario';
  if (c.includes('dias')) return 'Días';
  if (c.includes('medicamento')) return 'Medicamento';
  return campo;
}

/** Las cuatro casillas que la fila «Auditado antes de hablar» muestra siempre. */
export const CASILLAS = ['Medicamento', 'Dosis', 'Horario', 'Días'] as const;

export type Veredicto =
  | { tipo: 'dicho'; quechua: string; castellano: string; casillas: { nombre: string; ok: boolean }[] }
  | { tipo: 'dicho_con_aviso'; quechua: string; castellano: string; terminos: string[];
      casillas: { nombre: string; ok: boolean }[] }
  | { tipo: 'bloqueado'; castellano: string; diferencias: { nombre: string; dijo: string; decia: string }[];
      terminos: string[]; casillasOk: string[] };

/**
 * Qué pantalla toca después del turno de la enfermera.
 * Rojo solo si NO se dijo (regla de design/tokens.json). Si se dijo con dudas de términos, ámbar.
 */
export function veredictoEnfermera(castellano: string, r: RespuestaEnfermera): Veredicto {
  const fallados = new Set(r.diferencias.map((d) => nombreDelCampo(d.campo)));
  const casillas = CASILLAS.map((nombre) => ({ nombre, ok: !fallados.has(nombre) }));
  if (!r.se_dice) {
    return {
      tipo: 'bloqueado',
      castellano,
      diferencias: r.diferencias.map((d) => ({
        nombre: nombreDelCampo(d.campo),
        dijo: legible(d.original),
        decia: legible(d.retraducido),
      })),
      terminos: r.terminos_inseguros ?? [],
      casillasOk: casillas.filter((c) => c.ok).map((c) => c.nombre),
    };
  }
  if (!r.aprobado_por_auditoria || (r.terminos_inseguros ?? []).length > 0) {
    return { tipo: 'dicho_con_aviso', quechua: r.quechua, castellano, terminos: r.terminos_inseguros ?? [], casillas };
  }
  return { tipo: 'dicho', quechua: r.quechua, castellano, casillas };
}

export type Interprete =
  | { tipo: 'traducir' }
  | { tipo: 'pregunta'; para: 'personal' | 'paciente'; texto: string; quechua: string | null; motivo: string;
      dato: string | null; audioB64: string | null }
  | { tipo: 'respuesta'; texto: string; motivo: string; audioB64: string | null }
  | { tipo: 'no_entendi'; motivo: string }
  | { tipo: 'frase'; frase: FraseBanco };

const ACCIONES: Accion[] = ['traducir', 'repreguntar', 'responder', 'no_entendi', 'usar_frase_banco'];

/**
 * Qué hace la pantalla con la decisión del intérprete. Falla cerrada (§2b): una acción desconocida, una
 * frase del banco que no se encuentra o una repregunta sin texto terminan en «no le entendí», nunca en
 * algo dicho a medias.
 */
export function leerInterprete(
  r: CamposDecision & { quechua?: string; motivo?: string | null },
  banco: FraseBanco[] = [],
): Interprete {
  const d = { ...r, ...(r.decision ?? {}) };
  if (!d.accion || d.accion === 'traducir') return { tipo: 'traducir' };
  if (!ACCIONES.includes(d.accion)) return { tipo: 'no_entendi', motivo: 'Respuesta del intérprete no reconocida' };
  const motivo = (d.motivo ?? '').trim();
  const texto = (d.texto_pulido ?? '').trim();
  switch (d.accion) {
    case 'repreguntar':
      if (!texto && !r.quechua) return { tipo: 'no_entendi', motivo: motivo || 'Faltó la pregunta' };
      return {
        tipo: 'pregunta', para: d.para ?? 'paciente', texto, quechua: r.quechua || null, motivo,
        dato: d.dato_faltante ?? null, audioB64: d.audio_wav_b64 ?? null,
      };
    case 'responder':
      if (!texto) return { tipo: 'no_entendi', motivo: motivo || 'Faltó la respuesta' };
      return { tipo: 'respuesta', texto, motivo, audioB64: d.audio_wav_b64 ?? null };
    case 'usar_frase_banco': {
      const frase = d.frase_banco ?? banco.find((f) => f.id === d.frase_banco_id);
      if (!frase || !fraseRevisada(frase)) return { tipo: 'no_entendi', motivo: 'La frase verificada no está disponible' };
      return { tipo: 'frase', frase };
    }
    default:
      return { tipo: 'no_entendi', motivo: motivo || 'No se entendió con seguridad' };
  }
}

/** Una frase del banco solo se dice si su quechua ya existe (no es un marcador pendiente de revisión). */
export function fraseRevisada(f: FraseBanco): boolean {
  const q = (f.quy ?? '').trim();
  return !!f.audio || (q.length > 0 && !q.startsWith('['));
}

/** Las frases de una etiqueta, en el orden del banco. */
export function frasesConTag(banco: FraseBanco[], tag: string): FraseBanco[] {
  return banco.filter((f) => (f.tags ?? []).includes(tag));
}

function legible(v: string): string {
  if (v === 'None' || v === 'null' || v === '') return '(no lo dice)';
  if (v === '(falta)') return '(no aparece)';
  return v.replace(/\.0$/, '');
}

/** Cada turno se identifica por el idioma en que se habló (D27: el usuario puede ser de cualquiera de los dos lados). */
export type Lado = 'castellano' | 'quechua';

/** Después de un turno, habla el otro. Se puede cambiar a mano. */
export function siguienteLado(quienHablo: Lado): Lado {
  return quienHablo === 'castellano' ? 'quechua' : 'castellano';
}

/**
 * ¿El turno del paciente en realidad fue castellano? Lo dice el detector de idioma del servicio.
 * Solo se reencamina con confianza alta: la mezcla castellano-quechua es lo normal en la posta.
 */
export function fueCastellano(r: RespuestaPaciente, umbral = 0.8): boolean {
  return r.idioma?.codigo === 'spa' && (r.idioma.confianza ?? 0) >= umbral;
}

/**
 * El lado del turno según el detector de idioma (D11). Con confianza baja, o si el detector falló,
 * se queda el lado esperado por la alternancia: la mezcla castellano-quechua es normal en la posta.
 */
export function ladoDetectado(
  det: { codigo: string; confianza: number } | null, esperado: Lado, umbral = 0.8,
): Lado {
  if (!det || (det.confianza ?? 0) < umbral) return esperado;
  if (det.codigo === 'spa') return 'castellano';
  if (det.codigo === 'quy') return 'quechua';
  return esperado;
}

export type Turno = {
  id: number;
  lado: Lado;
  hora: Date;
  castellano: string;
  quechua: string;
  estado: 'dicho' | 'dicho_con_aviso' | 'bloqueado' | 'entendido' | 'con_dudas';
};
