// Lo que devuelve el servicio de Ricardo (ricardo-artifacts/servicio) y cómo lo lee la pantalla.
// Puro a propósito: se prueba con node sin simulador.

export type Diferencia = { campo: string; original: string; retraducido: string };

export type RespuestaEnfermera = {
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

export type RespuestaPaciente = {
  idioma: { codigo: string; confianza: number } | null;
  chanka_oido: string;
  castellano: string;
  literal: string;
  dudas: string[];
  seguro: boolean;
  total_ms: number;
};

export type RespuestaEscuchar = { texto: string; ms: number };

/** Nombre que la enfermera entiende para cada campo que compara la auditoría (app/rimay/hechos.py). */
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

export type Turno = {
  id: number;
  lado: Lado;
  hora: Date;
  castellano: string;
  quechua: string;
  estado: 'dicho' | 'dicho_con_aviso' | 'bloqueado' | 'entendido' | 'con_dudas';
};
