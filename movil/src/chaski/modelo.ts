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
  /** app/chaski/banco.json: false hasta que la enfermera la revisa. Una frase sin revisar NUNCA se dice. */
  revisado?: boolean;
  split?: string;
};

// ---- Contrato final de /turno/* (app/chaski/orquestador.py, clase `Resultado`) ----------------------

export type Estado = 'dicho' | 'dicho_con_aviso' | 'bloqueado';

export type Resultado = {
  estado: Estado;
  accion: Accion | null;
  motivo: string;
  dato_faltante?: string | null;
  frase_banco_id?: string | null;
  para: 'personal' | 'paciente';
  idioma_salida: 'spa' | 'quy';
  texto_pulido?: string;
  /** Lo que se oyó, en el idioma de origen. */
  texto_original?: string;
  /** Ensayo: la traducción la sembró la app, no la hizo el traductor. */
  sembrada?: boolean;
  /** Lo que se dice, en idioma_salida. Vacío si bloqueado. */
  texto_salida?: string;
  /** Audio verificado del banco, cuando accion == usar_frase_banco. */
  audio?: string | null;
  aviso?: string | null;
  motor?: string | null;
  respaldo?: boolean;
  modelos?: { principal?: string | null; critico?: string | null };
  paso_fallido?: string | null;
  ms?: Record<string, number>;
  /** El estado de la consulta: la app lo guarda y lo devuelve en el siguiente turno. */
  contexto?: { historial?: { rol: string; texto: string }[]; modo?: string; repreguntas_seguidas?: string[] };
};

/** ¿La respuesta trae el contrato nuevo? Hasta que el servicio cambie, conviven las dos formas. */
export function esResultado(r: unknown): r is Resultado {
  return !!r && typeof r === 'object' && typeof (r as Resultado).estado === 'string'
    && ['dicho', 'dicho_con_aviso', 'bloqueado'].includes((r as Resultado).estado);
}

/**
 * «Revisado por el crítico»: solo cuando se TRADUJO (o no viene acción), corrió el crítico y no quedó bloqueado.
 * Repreguntar y responder son respuestas de Chaski al personal: pasan las barreras de código, no el crítico.
 */
export function revisadoPorCritico(r: unknown): boolean {
  return esResultado(r) && (r.accion == null || r.accion === 'traducir')
    && !!r.modelos?.critico && r.estado !== 'bloqueado';
}

/** ¿Este turno fue un ensayo con traducción sembrada? Lo dice el servicio, no solo la app. */
export function esEnsayo(r: unknown): boolean {
  return esResultado(r) && r.sembrada === true;
}

/** La negación de una frase en castellano, para mostrar qué prohibición se perdió: «no con té». */
export function negacionEn(texto: string): string | null {
  const m = texto.match(/\b(no|nunca|ni)\s+([^,.;:!?]{1,24})/i);
  return m ? `${m[1].toLowerCase()} ${m[2].trim()}` : null;
}

/**
 * Por qué Chaski no lo dijo, en palabras simples, desde `paso_fallido` + `motivo` del orquestador y las
 * barreras (app/chaski/guardas.py). Lo específico gana a lo general; nunca se muestra jerga técnica.
 */
/** Quita el nombre de la capa del motivo («B5 ida y vuelta: …», «C agregados: …») y deja el detalle. */
export function detalleDelMotivo(motivo: string | null | undefined): string {
  return (motivo ?? '').replace(/^\s*(?:[A-Z]\d*[\w\s/]*?|cr[ií]tico|guardas|barreras?)\s*:\s*/i, '').trim();
}

export function explicarBloqueo(paso: string | null | undefined, motivo: string | null | undefined, original = ''): string {
  const det = detalleDelMotivo(motivo);
  const m = (motivo ?? '').toLowerCase();
  const p = (paso ?? '').toLowerCase();
  // Primero los motivos que traen el dato exacto: se muestra QUÉ falló, no una categoría (pitch: «cada
  // bloqueo dice qué dato falló»).
  const conDato: [RegExp, string][] = [
    [/consejo que no estaba:\s*(.+)/i, 'agregaba algo que no se dijo: $1'],
    [/diagn[oó]stico que no estaba:\s*(.+)/i, 'agregaba un diagnóstico: $1'],
    [/el pulido agreg[oó] un dato:\s*(.+)/i, 'agregaba un dato: $1'],
    [/el pulido cambi[oó] un dato:\s*(.+)/i, 'cambió un dato: $1'],
    [/cambi[oó] a qui[eé]n se le habla:\s*(.+)/i, 'cambió a quién se le habla: $1'],
  ];
  for (const [re, plantilla] of conDato) {
    const x = det.match(re);
    if (x) return corto(plantilla.replace('$1', x[1].trim()));
  }
  if (/prohibici|negaci|ama \/ mana|quitó una negación/.test(m)) {
    const neg = negacionEn(original);
    return neg ? `se perdió la prohibición (${neg})` : 'se perdió la prohibición';
  }
  if (/cada_horas|frecuencia|horario|cada cu[aá]ntas horas/.test(m)) return 'no coincidió la frecuencia';
  if (/cantidad|dosis/.test(m)) return 'no coincidió la dosis';
  if (/\bdias\b|d[ií]as|duraci/.test(m)) return 'no coincidieron los días';
  if (/proxima_cita|cita|control/.test(m)) return 'no coincidió la fecha del control';
  if (/medicamento|nombra «/.test(m)) return 'no coincidió el medicamento';
  if (/unidad/.test(m)) return 'no coincidió la unidad (pastilla, cucharada…)';
  if (/parte del cuerpo|cuerpo/.test(m)) return 'cambió la parte del cuerpo';
  if (/alergi/.test(m)) return 'cambió lo de la alergia';
  if (/embaraz/.test(m)) return 'cambió lo del embarazo';
  if (/\bvía\b|\bvia\b/.test(m)) return 'cambió cómo se toma';
  if (/a quién se le habla/.test(m)) return 'cambió a quién se le habla';
  if (/no se oyó nada/.test(m)) return 'no se oyó nada';
  if (/no se oyó bien/.test(m)) return 'no se oyó bien un dato importante';
  if (/agreg|nada nuevo|que no se dijo|no estaba/.test(m)) return 'iba a agregar algo que nadie dijo';
  if (/número|numero/.test(m)) return 'cambió un número';
  if (/no pude verificar|error|timeout|mal formada/.test(m)) return 'no pude verificarlo';
  if (/sublingu|under the tongue|route/.test(m)) return 'cambió cómo se toma';
  // Sin categoría conocida: el motivo real, aunque sea crudo, antes que un genérico que no dice nada.
  if (det) return corto(det);
  if (p.includes('critico')) return 'el revisor encontró un problema';
  if (p.includes('guardas') || /^b\d/.test(p)) return 'una barrera de seguridad lo frenó';
  if (p.includes('traducir')) return 'la traducción no se pudo revisar';
  if (p.includes('decidir')) return 'no pude entender el turno';
  return 'algo cambió al traducir';
}

function corto(t: string, max = 90): string {
  const limpio = t.replace(/\s+/g, ' ').trim();
  return limpio.length > max ? limpio.slice(0, max - 1).trimEnd() + '…' : limpio;
}

/** ¿Vale la pena reintentar? Red caída o sin respuesta (null), o el servicio reiniciándose (502/503/504). */
export function esReintentable(status: number | null): boolean {
  return status === null || status === 502 || status === 503 || status === 504;
}

/** Los pasos del «Pensando», por tiempo transcurrido (la respuesta no llega por partes). */
// Turno con el intérprete nuevo, medido de punta a punta el 24-oct 21:56 (evals/HISTORIA.md §2b):
// p50 ~17 s, peor 26 s (oír 1,1 · decidir 2,9 · traducir 9,0 · crítico 3,1 · voz 1,0).
export const UMBRALES_PASOS_MS = [0, 4000, 13000] as const;
export const AVISO_LENTO_MS = 12000;
/** Después de esto se dice que la revisión sigue, para que nadie crea que se colgó. */
export const AVISO_MUY_LENTO_MS = 22000;

export function pasoPorTiempo(ms: number): number {
  let paso = 0;
  UMBRALES_PASOS_MS.forEach((u, i) => { if (ms >= u) paso = i; });
  return paso;
}

/**
 * Los campos de la `Decision` que traen /turno/enfermera y /turno/paciente cuando el intérprete está
 * integrado. Todos opcionales: sin `accion` la app hace exactamente lo de antes (traducir).
 * El servicio puede mandarlos sueltos o dentro de `decision`.
 */
export type CamposDecision = {
  accion?: Accion | null;
  // Campos del contrato final (Resultado) que pueden venir en cualquiera de las dos formas.
  estado?: Estado;
  texto_salida?: string;
  audio?: string | null;
  modelos?: Resultado['modelos'];
  paso_fallido?: string | null;
  ms?: Record<string, number>;
  contexto?: Resultado['contexto'];
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
  | { tipo: 'dicho'; quechua: string; castellano: string; casillas: { nombre: string; ok: boolean }[];
      critico?: boolean }
  | { tipo: 'dicho_con_aviso'; quechua: string; castellano: string; terminos: string[];
      casillas: { nombre: string; ok: boolean }[]; aviso?: string | null; critico?: boolean }
  | { tipo: 'bloqueado'; castellano: string; diferencias: { nombre: string; dijo: string; decia: string }[];
      terminos: string[]; casillasOk: string[]; razon?: string; oido?: string };

/**
 * Qué pantalla toca después del turno de la enfermera.
 * Rojo solo si NO se dijo (regla de design/tokens.json). Si se dijo con dudas de términos, ámbar.
 */
export function veredictoEnfermera(castellano: string, r: RespuestaEnfermera | Resultado): Veredicto {
  if (esResultado(r)) return veredictoResultado(castellano, r);
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
  | { tipo: 'no_entendi'; motivo: string; quechua?: string | null }
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
  // Bloqueado gana a cualquier acción: lo bloqueado nunca se dice (lo muestra el veredicto).
  if (esResultado(r) && r.estado === 'bloqueado') return { tipo: 'traducir' };
  if (!d.accion || d.accion === 'traducir') return { tipo: 'traducir' };
  if (!ACCIONES.includes(d.accion)) return { tipo: 'no_entendi', motivo: 'Respuesta del intérprete no reconocida' };
  const motivo = (d.motivo ?? '').trim();
  const nuevo = esResultado(r) ? r : null;
  // Con el contrato nuevo lo que se dice es texto_salida; texto_pulido puede ser la frase original pulida.
  const salidaSpa = nuevo && nuevo.idioma_salida === 'spa' ? (nuevo.texto_salida ?? '').trim() : '';
  const texto = salidaSpa || (d.texto_pulido ?? '').trim();
  const quechua = r.quechua || (nuevo && nuevo.idioma_salida === 'quy' ? nuevo.texto_salida || null : null);
  switch (d.accion) {
    case 'repreguntar':
      if (!texto && !quechua) return { tipo: 'no_entendi', motivo: motivo || 'Faltó la pregunta' };
      return {
        // Repregunta que nace de una barrera: el motivo es técnico; basta la pregunta y el dato que falta.
        tipo: 'pregunta', para: d.para ?? 'paciente', texto, quechua: quechua || null,
        motivo: nuevo?.paso_fallido ? '' : motivo,
        dato: d.dato_faltante ?? null, audioB64: d.audio_wav_b64 ?? null,
      };
    case 'responder':
      if (!texto) return { tipo: 'no_entendi', motivo: motivo || 'Faltó la respuesta' };
      return { tipo: 'respuesta', texto, motivo, audioB64: d.audio_wav_b64 ?? null };
    case 'usar_frase_banco': {
      const frase = d.frase_banco ?? banco.find((f) => f.id === d.frase_banco_id)
        ?? (nuevo && (nuevo.audio || nuevo.texto_salida)
          ? { id: nuevo.frase_banco_id ?? 'banco', es: nuevo.texto_pulido ?? '', quy: nuevo.texto_salida ?? '',
              audio: nuevo.audio ?? null, tags: [] }
          : undefined);
      if (!frase || !fraseRevisada(frase)) return { tipo: 'no_entendi', motivo: 'La frase verificada no está disponible' };
      return { tipo: 'frase', frase };
    }
    default:
      // Si el servicio trae la disculpa en quechua (barrera en el turno del paciente), se le dice al paciente.
      return { tipo: 'no_entendi', motivo: nuevo?.paso_fallido ? '' : (motivo || 'No se entendió con seguridad'),
        quechua: quechua || null };
  }
}

/** Una frase del banco solo se dice si su quechua ya existe (no es un marcador pendiente de revisión). */
export function fraseRevisada(f: FraseBanco): boolean {
  // Seguridad (checklist §6.4): sin revisar o sin quechua, NUNCA se reproduce.
  if (f.revisado === false || (f.tags ?? []).includes('falta_quechua')) return false;
  const q = (f.quy ?? '').trim();
  return !!f.audio || (q.length > 0 && !q.startsWith('['));
}

/** Las frases de una etiqueta, en el orden del banco. */
export function frasesConTag(banco: FraseBanco[], tag: string): FraseBanco[] {
  return banco.filter((f) => (f.tags ?? []).includes(tag));
}

/** El contrato nuevo: el estado lo decide el orquestador (código), la app solo lo muestra. */
export function veredictoResultado(castellano: string, r: Resultado): Veredicto {
  const casillas = CASILLAS.map((nombre) => ({ nombre, ok: true }));
  if (r.estado === 'bloqueado') {
    return {
      tipo: 'bloqueado', castellano, diferencias: [], terminos: [], casillasOk: [],
      razon: explicarBloqueo(r.paso_fallido, r.motivo, castellano),
      oido: (r.texto_original ?? '').trim() || undefined,
    };
  }
  const quechua = r.idioma_salida === 'quy' ? (r.texto_salida ?? '') : '';
  const critico = revisadoPorCritico(r);
  if (r.estado === 'dicho_con_aviso') {
    return { tipo: 'dicho_con_aviso', quechua, castellano, terminos: [], casillas, aviso: r.aviso ?? null, critico };
  }
  return { tipo: 'dicho', quechua, castellano, casillas, critico };
}

/**
 * Turno del paciente con el contrato nuevo → lo que la pantalla ya sabe mostrar. Lo que oyó en quechua
 * sale del último renglón del paciente en `contexto`, porque `Resultado` no lo trae aparte.
 */
export function pacienteDesdeResultado(r: Resultado): RespuestaPaciente {
  const oido = r.texto_original
    || ([...(r.contexto?.historial ?? [])].reverse().find((h) => h.rol === 'paciente')?.texto ?? '');
  return {
    accion: r.accion, para: r.para, idioma_salida: r.idioma_salida, texto_pulido: r.texto_pulido,
    motivo: r.motivo, dato_faltante: r.dato_faltante, frase_banco_id: r.frase_banco_id,
    estado: r.estado, texto_salida: r.texto_salida, audio: r.audio, modelos: r.modelos,
    paso_fallido: r.paso_fallido, ms: r.ms, contexto: r.contexto,
    idioma: null,
    chanka_oido: oido,
    castellano: r.idioma_salida === 'spa' ? (r.texto_salida ?? '') : (r.texto_pulido ?? ''),
    literal: '',
    dudas: r.aviso ? [r.aviso] : [],
    seguro: r.estado === 'dicho',
    total_ms: r.ms?.total ?? 0,
  };
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
