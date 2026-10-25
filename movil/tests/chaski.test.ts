// node --test tests/   (Node 22+ con tipos nativos)
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { base64ABytes, bocaAbierta, envolvente } from '../src/chaski/wav.ts';
import {
  AVISO_LENTO_MS, esEnsayo, esReintentable, esResultado, explicarBloqueo, negacionEn, pacienteDesdeResultado, pasoPorTiempo, revisadoPorCritico,
  fraseRevisada, frasesConTag, leerInterprete, type FraseBanco, type Resultado,
  fueCastellano, ladoDetectado, nombreDelCampo, siguienteLado, veredictoEnfermera,
  type RespuestaEnfermera, type RespuestaPaciente,
} from '../src/chaski/modelo.ts';
import bancoReal from '../../app/chaski/banco.json' with { type: 'json' };
import { comprobarRepeticion, faltantes, indicacionDesdeHechos, numerosEn, type HechosReceta } from '../src/chaski/receta.ts';

function wav(muestras: number[], frecuencia = 16000): Uint8Array {
  const datos = muestras.length * 2;
  const b = new Uint8Array(44 + datos);
  const v = new DataView(b.buffer);
  const s = (o: number, t: string) => [...t].forEach((c, i) => (b[o + i] = c.charCodeAt(0)));
  s(0, 'RIFF'); v.setUint32(4, 36 + datos, true); s(8, 'WAVE');
  s(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, frecuencia, true); v.setUint32(28, frecuencia * 2, true); v.setUint16(32, 2, true);
  v.setUint16(34, 16, true); s(36, 'data'); v.setUint32(40, datos, true);
  muestras.forEach((m, i) => v.setInt16(44 + i * 2, m, true));
  return b;
}

test('base64 ida y vuelta', () => {
  const original = new Uint8Array([0, 1, 2, 250, 251, 252, 253]);
  const b64 = Buffer.from(original).toString('base64');
  assert.deepEqual([...base64ABytes(b64)], [...original]);
});

test('envolvente: silencio, voz, silencio', () => {
  const silencio = Array(800).fill(0);           // 50 ms a 16 kHz
  const voz = Array.from({ length: 800 }, (_, i) => (i % 2 ? 12000 : -12000));
  const env = envolvente(wav([...silencio, ...voz, ...silencio]))!;
  assert.equal(env.niveles.length, 3);
  assert.equal(env.niveles[1], 1);
  assert.equal(env.niveles[0], 0);
  assert.ok(Math.abs(env.segundos - 0.15) < 1e-9);
  assert.equal(bocaAbierta(env, 0.01), false);
  assert.equal(bocaAbierta(env, 0.07), true);
  assert.equal(bocaAbierta(env, 0.12), false);
});

test('envolvente: lo que no es WAV devuelve null y la boca alterna sola', () => {
  assert.equal(envolvente(new Uint8Array(100)), null);
  assert.equal(typeof bocaAbierta(null, 0.3), 'boolean');
});

const base: RespuestaEnfermera = {
  quechua: 'Q', retraduccion: 'R', aprobado_por_auditoria: true, motivo: null,
  terminos_inseguros: [], diferencias: [], se_dice: true, aviso: null, total_ms: 5000,
};

test('aprobado → dicho, todas las casillas en verde', () => {
  const v = veredictoEnfermera('Tome', base);
  assert.equal(v.tipo, 'dicho');
  if (v.tipo === 'dicho') assert.ok(v.casillas.every((c) => c.ok));
});

test('solo términos dudosos en modo ensayo → ámbar, nunca rojo', () => {
  const v = veredictoEnfermera('Venga a la posta', {
    ...base, aprobado_por_auditoria: false, terminos_inseguros: ['posta'], se_dice: true,
  });
  assert.equal(v.tipo, 'dicho_con_aviso');
  if (v.tipo === 'dicho_con_aviso') assert.deepEqual(v.terminos, ['posta']);
});

test('dato crítico cambiado → bloqueado, con lo que dijo y lo que decía', () => {
  const v = veredictoEnfermera('Una pastilla cada 8 horas', {
    ...base, aprobado_por_auditoria: false, se_dice: false,
    diferencias: [{ campo: 'paracetamol.cada_horas', original: '8.0', retraducido: 'None' }],
  });
  assert.equal(v.tipo, 'bloqueado');
  if (v.tipo === 'bloqueado') {
    assert.deepEqual(v.diferencias, [{ nombre: 'Horario', dijo: '8', decia: '(no lo dice)' }]);
    assert.deepEqual(v.casillasOk, ['Medicamento', 'Dosis', 'Días']);
  }
});

test('nombres de campos', () => {
  assert.equal(nombreDelCampo('medicamento'), 'Medicamento');
  assert.equal(nombreDelCampo('sulfato ferroso.cantidad'), 'Dosis');
  assert.equal(nombreDelCampo('x.dias'), 'Días');
  assert.equal(nombreDelCampo('proxima_cita_en_dias'), 'Próxima cita');
  assert.equal(nombreDelCampo('ir_ya_si (cantidad de señales)'), 'Señales de alarma');
});

test('turnos alternan', () => {
  assert.equal(siguienteLado('castellano'), 'quechua');
  assert.equal(siguienteLado('quechua'), 'castellano');
});

test('solo se reencamina a castellano con confianza alta', () => {
  const p: RespuestaPaciente = {
    idioma: { codigo: 'spa', confianza: 0.95 }, chanka_oido: '', castellano: '', literal: '',
    dudas: [], seguro: true, total_ms: 0,
  };
  assert.equal(fueCastellano(p), true);
  assert.equal(fueCastellano({ ...p, idioma: { codigo: 'spa', confianza: 0.6 } }), false);
  assert.equal(fueCastellano({ ...p, idioma: { codigo: 'quy', confianza: 0.99 } }), false);
  assert.equal(fueCastellano({ ...p, idioma: null }), false);
});

import { escalonado, escalonadoAdentro, escalonesDeChaski, trazo } from '../src/chaski/geometria.ts';

test('escalonado: cuatro esquinas de escalones, contorno cerrado y simétrico', () => {
  const p = escalonado(100, 2, 10);
  // Cada esquina aporta 1 + 2·pasos puntos.
  assert.equal(p.length, 4 * (1 + 2 * 2));
  // Empieza en el borde superior, donde arranca el corte de la esquina derecha.
  assert.deepEqual(p[0], [80, 0]);
  // La esquina superior derecha baja en escalones hasta el borde derecho.
  assert.deepEqual(p.slice(0, 5), [[80, 0], [80, 10], [90, 10], [90, 20], [100, 20]]);
  // Nunca se sale del cuadrado.
  assert.ok(p.every(([x, y]) => x >= 0 && x <= 100 && y >= 0 && y <= 100));
});

test('escalonado: la chakana (corte hondo) y la crucecita (un paso) salen de la misma figura', () => {
  assert.equal(escalonado(90, 3, 10).length, 28);
  assert.deepEqual(escalonado(10, 1, 3).slice(0, 3), [[7, 0], [7, 3], [10, 3]]);
  assert.throws(() => escalonado(10, 2, 3), /demasiado hondo/);
});

test('escalonadoAdentro: los escalones quedan paralelos al contorno de afuera', () => {
  const fuera = escalonado(100, 2, 10);
  const dentro = escalonadoAdentro(100, 2, 10, 5);
  // Cada punto se mueve en diagonal hacia adentro: |dx| = |dy| = margen en las esquinas de los escalones.
  assert.deepEqual(dentro[0], [75, 5]);
  assert.deepEqual(dentro[4], [95, 25]);
  assert.equal(dentro.length, fuera.length);
});

test('trazo y escalones de Chaski', () => {
  assert.equal(trazo([[0, 0], [1.234, 2]]), 'M0 0L1.23 2Z');
  assert.deepEqual(escalonesDeChaski(240), { pasos: 5, paso: 7 });
  assert.deepEqual(escalonesDeChaski(96), { pasos: 4, paso: 3 });
});

import { hebrasEncendidas, nivelDesdeDb, palabrasDichas } from '../src/chaski/movimiento.ts';
import { nivelEn } from '../src/chaski/wav.ts';

test('movimiento: con más voz se encienden más hebras, de adentro hacia afuera', () => {
  assert.equal(hebrasEncendidas(0), 0);
  assert.equal(hebrasEncendidas(0.2), 1);
  assert.equal(hebrasEncendidas(0.5), 2);
  assert.equal(hebrasEncendidas(0.9), 3);
  assert.equal(nivelDesdeDb(undefined), 0);
  assert.equal(nivelDesdeDb(-160), 0);
  assert.equal(nivelDesdeDb(0), 1);
});

test('movimiento: las palabras se revelan con el avance del audio, sin pasarse', () => {
  assert.equal(palabrasDichas(6, 0), 0);
  assert.equal(palabrasDichas(6, 0.5), 3);
  assert.equal(palabrasDichas(6, 1.4), 6);
  assert.equal(palabrasDichas(0, 0.5), 0);
});

test('nivelEn lee la envolvente en el instante del audio', () => {
  const env = { niveles: [0, 1, 0.5], ventanaMs: 50, segundos: 0.15 };
  assert.equal(nivelEn(env, 0.06), 1);
  assert.equal(nivelEn(env, 0.9), 0);
  assert.equal(nivelEn(null, 0.1), 0);
});

test('el detector de idioma decide el lado solo con confianza alta', () => {
  assert.equal(ladoDetectado({ codigo: 'quy', confianza: 1 }, 'castellano'), 'quechua');
  assert.equal(ladoDetectado({ codigo: 'spa', confianza: 0.95 }, 'quechua'), 'castellano');
  assert.equal(ladoDetectado({ codigo: 'spa', confianza: 0.5 }, 'quechua'), 'quechua');
  assert.equal(ladoDetectado(null, 'quechua'), 'quechua');
  assert.equal(ladoDetectado({ codigo: 'eng', confianza: 1 }, 'castellano'), 'castellano');
});

// ---- intérprete agente (D32) -------------------------------------------------------------

const FRASE: FraseBanco = { id: 'dolor-donde', es: '¿Dónde le duele?', quy: 'Maypitaq nanasunki?', audio: null, tags: ['emergencia'] };
const PENDIENTE: FraseBanco = { id: 'p', es: '¿Desde cuándo?', quy: '[revisar con la enfermera]', audio: null, tags: ['emergencia'] };

test('sin accion la app traduce como siempre', () => {
  assert.deepEqual(leerInterprete({}), { tipo: 'traducir' });
  assert.deepEqual(leerInterprete({ accion: 'traducir' }), { tipo: 'traducir' });
});

test('repreguntar trae pregunta, motivo y dato faltante; acepta la decision anidada', () => {
  const v = leerInterprete({ decision: { accion: 'repreguntar', para: 'paciente', texto_pulido: '¿Desde cuándo le duele?',
    motivo: 'No dijo desde cuándo', dato_faltante: 'desde cuándo' }, quechua: 'Hayk\'aqmantataq?' } as any);
  assert.equal(v.tipo, 'pregunta');
  if (v.tipo === 'pregunta') {
    assert.equal(v.dato, 'desde cuándo');
    assert.equal(v.quechua, "Hayk'aqmantataq?");
    assert.equal(v.para, 'paciente');
  }
});

test('falla cerrada: responder sin texto, accion rara o frase ausente terminan en no_entendi', () => {
  assert.equal(leerInterprete({ accion: 'responder', texto_pulido: '' }).tipo, 'no_entendi');
  assert.equal(leerInterprete({ accion: 'inventada' as any }).tipo, 'no_entendi');
  assert.equal(leerInterprete({ accion: 'usar_frase_banco', frase_banco_id: 'nada' }, [FRASE]).tipo, 'no_entendi');
  assert.equal(leerInterprete({ accion: 'usar_frase_banco', frase_banco_id: 'p' }, [PENDIENTE]).tipo, 'no_entendi');
});

test('usar_frase_banco busca la frase por id en el banco', () => {
  const v = leerInterprete({ accion: 'usar_frase_banco', frase_banco_id: 'dolor-donde' }, [FRASE]);
  assert.equal(v.tipo, 'frase');
});

test('una frase con marcador pendiente nunca se dice; con audio sí', () => {
  assert.equal(fraseRevisada(PENDIENTE), false);
  assert.equal(fraseRevisada(FRASE), true);
  assert.equal(fraseRevisada({ ...PENDIENTE, audio: 'https://x/a.wav' }), true);
  assert.deepEqual(frasesConTag([FRASE, { ...FRASE, id: 'x', tags: ['dolor'] }], 'emergencia').map((f) => f.id), ['dolor-donde']);
});

// ---- receta y «¿me lo repite?» ------------------------------------------------------------

const PARACETAMOL: HechosReceta = { medicamento: 'paracetamol', concentracion: '500 mg', cantidad: 1, unidad: 'pastilla', cada_horas: 8, dias: 3 };

test('la indicación sale de una plantilla con los números confirmados', () => {
  assert.equal(indicacionDesdeHechos(PARACETAMOL), 'Tome una pastilla de paracetamol de 500 mg cada ocho horas, durante tres días.');
  assert.equal(indicacionDesdeHechos({ ...PARACETAMOL, cantidad: 2, cada_horas: 24, dias: 1, concentracion: null }),
    'Tome dos pastillas de paracetamol una vez al día, durante un día.');
});

test('sin un dato no se puede decir', () => {
  assert.deepEqual(faltantes({ ...PARACETAMOL, cada_horas: null, dias: null }), ['Cada cuántas horas', 'Por cuántos días']);
  assert.deepEqual(faltantes(PARACETAMOL), []);
});

test('números en cifras y en palabras', () => {
  assert.deepEqual(numerosEn('cada 8 horas por tres días').sort((a, b) => a - b), [3, 8]);
  assert.ok(numerosEn('una vez al día').includes(24));
});

test('«¿me lo repite?» marca lo que falta', () => {
  const r = comprobarRepeticion(PARACETAMOL, 'Tomo una pastilla cada ocho horas');
  assert.deepEqual(r.map((c) => c.ok), [true, true, true, false]);
  assert.equal(r[3].nombre, 'Por cuántos días');
  assert.ok(comprobarRepeticion(PARACETAMOL, 'el paracetamol, uno cada 8 horas, tres días').every((c) => c.ok));
});

// ---- contrato final (Resultado) ------------------------------------------------------------

const BASE_R: Resultado = {
  estado: 'dicho', accion: 'traducir', motivo: '', para: 'paciente', idioma_salida: 'quy',
  texto_pulido: 'Tome con agua', texto_salida: 'Yakuwan upyay', modelos: { principal: 'opus', critico: 'haiku' },
  contexto: { historial: [{ rol: 'personal', texto: 'Tome con agua' }], modo: 'consulta' },
};

test('reconoce el contrato nuevo y convive con el viejo', () => {
  assert.equal(esResultado(BASE_R), true);
  assert.equal(esResultado({ quechua: 'q', se_dice: true }), false);
  assert.equal(esResultado({ estado: 'otro' }), false);
});

test('dicho con el contrato nuevo: quechua de texto_salida e insignia del crítico', () => {
  const v = veredictoEnfermera('Tome con agua', BASE_R);
  assert.equal(v.tipo, 'dicho');
  if (v.tipo === 'dicho') { assert.equal(v.quechua, 'Yakuwan upyay'); assert.equal(v.critico, true); }
  assert.equal(revisadoPorCritico({ ...BASE_R, modelos: { principal: 'opus', critico: null } }), false);
  assert.equal(revisadoPorCritico({ ...BASE_R, estado: 'bloqueado' }), false);
});

test('ámbar trae su aviso; rojo solo para bloqueado', () => {
  const v = veredictoEnfermera('x', { ...BASE_R, estado: 'dicho_con_aviso', aviso: 'posta como préstamo' });
  assert.equal(v.tipo, 'dicho_con_aviso');
  if (v.tipo === 'dicho_con_aviso') assert.equal(v.aviso, 'posta como préstamo');
});

test('bloqueado gana a cualquier acción y se explica en palabras simples', () => {
  const r: Resultado = { ...BASE_R, estado: 'bloqueado', accion: 'repreguntar', texto_salida: '',
    motivo: 'cambió un dato crítico: paracetamol.cada_horas', paso_fallido: 'guardas' };
  assert.equal(leerInterprete(r).tipo, 'traducir');
  const v = veredictoEnfermera('Tome paracetamol cada 8 horas', r);
  assert.equal(v.tipo, 'bloqueado');
  if (v.tipo === 'bloqueado') assert.equal(v.razon, 'no coincidió la frecuencia');
});

test('la negativa del ensayo: «se perdió la prohibición (no con té)»', () => {
  assert.equal(explicarBloqueo('guardas', 'cambió un dato crítico: prohibiciones', 'Tómela con agua, no con té'),
    'se perdió la prohibición (no con té)');
  assert.equal(explicarBloqueo('B4', 'el castellano tiene una negación y el quechua no (ama / mana / -chu)'),
    'se perdió la prohibición');
  assert.equal(negacionEn('Nunca dos juntas.'), 'nunca dos juntas');
});

test('nombres de pasos y campos a castellano llano', () => {
  assert.equal(explicarBloqueo(null, 'cambió un dato crítico: medicamento, medicamento'), 'no coincidió el medicamento');
  assert.equal(explicarBloqueo(null, 'x.cantidad'), 'no coincidió la dosis');
  assert.equal(explicarBloqueo(null, 'x.dias'), 'no coincidieron los días');
  assert.equal(explicarBloqueo(null, 'unidad «cucharada» en el quechua'), 'no coincidió la unidad (pastilla, cucharada…)');
  assert.equal(explicarBloqueo(null, 'el pulido agregó un dato: después de comer'), 'iba a agregar algo que nadie dijo');
  assert.equal(explicarBloqueo(null, 'cambió a quién se le habla: paciente → personal'), 'cambió a quién se le habla');
  assert.equal(explicarBloqueo('decidir', 'No pude verificar esto: TimeoutError'), 'no pude verificarlo');
  assert.equal(explicarBloqueo('critico', 'el crítico lo frenó'), 'el revisor encontró un problema');
  assert.equal(explicarBloqueo(null, ''), 'algo cambió al traducir');
});

test('el turno del paciente con el contrato nuevo', () => {
  const r = pacienteDesdeResultado({ ...BASE_R, idioma_salida: 'spa', texto_salida: 'Me duele la barriga', para: 'personal',
    contexto: { historial: [{ rol: 'paciente', texto: 'wiksay nanan' }] }, estado: 'dicho_con_aviso', aviso: 'no dijo desde cuándo' });
  assert.equal(r.castellano, 'Me duele la barriga');
  assert.equal(r.chanka_oido, 'wiksay nanan');
  assert.equal(r.seguro, false);
  assert.deepEqual(r.dudas, ['no dijo desde cuándo']);
});

test('repreguntar con el contrato nuevo usa texto_salida como quechua', () => {
  const v = leerInterprete({ ...BASE_R, accion: 'repreguntar', texto_salida: 'Hayk\'aqmantataq?', texto_pulido: '¿Desde cuándo?', dato_faltante: 'desde cuándo' });
  assert.equal(v.tipo, 'pregunta');
  if (v.tipo === 'pregunta') assert.equal(v.quechua, "Hayk'aqmantataq?");
});

test('los pasos del «Pensando» avanzan con el tiempo y avisa si tarda', () => {
  assert.deepEqual([0, 1900, 2100, 5500, 30000].map(pasoPorTiempo), [0, 0, 1, 2, 2]);
  assert.equal(AVISO_LENTO_MS, 8000);
});

test('banco real: sin revisar o falta_quechua NUNCA se reproduce', () => {
  const real: FraseBanco = { id: 'emg-dolor-donde', es: '¿Dónde le duele?', quy: '', audio: null,
    tags: ['emergencia', 'falta_quechua'], revisado: false };
  assert.equal(fraseRevisada(real), false);
  assert.equal(fraseRevisada({ ...real, quy: 'Maypitaq nanasunki?', tags: ['emergencia'], revisado: false }), false);
  assert.equal(fraseRevisada({ ...real, quy: 'Maypitaq nanasunki?', tags: ['emergencia', 'falta_quechua'], revisado: true }), false);
  assert.equal(fraseRevisada({ ...real, quy: 'Maypitaq nanasunki?', tags: ['emergencia'], revisado: true }), true);
});

test('banco real: en emergencia solo se dice lo que la enfermera revisó', () => {
  const emerg = frasesConTag(bancoReal as FraseBanco[], 'emergencia');
  assert.ok(emerg.length >= 20);
  for (const f of emerg.filter(fraseRevisada)) {
    assert.equal(f.revisado, true, `${f.id} se diría sin revisión`);
    assert.ok(!(f.tags ?? []).some((x) => x === 'falta_quechua' || x === 'por_confirmar'), `${f.id} está por confirmar`);
    assert.ok(f.quy && !f.quy.trim().startsWith('['), `${f.id} no tiene quechua`);
  }
});

test('reintento automático solo para red caída o servicio reiniciándose', () => {
  assert.deepEqual([null, 502, 503, 504].map(esReintentable), [true, true, true, true]);
  assert.deepEqual([400, 404, 500, 422].map(esReintentable), [false, false, false, false]);
});

test('la insignia del crítico no sale en repreguntar ni responder', () => {
  assert.equal(revisadoPorCritico({ ...BASE_R, accion: 'repreguntar' }), false);
  assert.equal(revisadoPorCritico({ ...BASE_R, accion: 'responder' }), false);
  assert.equal(revisadoPorCritico({ ...BASE_R, accion: 'traducir' }), true);
  assert.equal(revisadoPorCritico({ ...BASE_R, accion: null }), true);
});

test('el paciente usa texto_original y cae al historial si falta', () => {
  const con = pacienteDesdeResultado({ ...BASE_R, idioma_salida: 'spa', texto_original: 'wiksay nanan',
    contexto: { historial: [{ rol: 'paciente', texto: 'otra cosa' }] } });
  assert.equal(con.chanka_oido, 'wiksay nanan');
  const sin = pacienteDesdeResultado({ ...BASE_R, idioma_salida: 'spa', contexto: { historial: [{ rol: 'paciente', texto: 'otra cosa' }] } });
  assert.equal(sin.chanka_oido, 'otra cosa');
});

test('sembrada del servicio marca el ensayo', () => {
  assert.equal(esEnsayo({ ...BASE_R, sembrada: true }), true);
  assert.equal(esEnsayo(BASE_R), false);
});

test('una grabación vacía, corta o en silencio no se manda al servicio', async () => {
  const { revisarGrabacion } = await import('../src/chaski/wav.ts');
  assert.equal(revisarGrabacion(new Uint8Array(0)).ok, false);
  assert.equal(revisarGrabacion(wav([])).ok, false);                       // solo cabecera
  assert.equal(revisarGrabacion(wav(Array(1600).fill(1000))).ok, false);   // 0.1 s
  assert.equal(revisarGrabacion(wav(Array(16000).fill(0))).ok, false);     // 1 s de silencio digital
  const voz = Array.from({ length: 16000 }, (_, i) => (i % 2 ? 9000 : -9000));
  const r = revisarGrabacion(wav(voz));
  assert.equal(r.ok, true);
  const m4a = new Uint8Array(200); m4a.set([0, 0, 0, 0x20, 0x66, 0x74, 0x79, 0x70], 0); // «ftyp»
  assert.equal(revisarGrabacion(m4a).ok, false);
});
