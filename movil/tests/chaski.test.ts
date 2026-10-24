// node --test tests/   (Node 22+ con tipos nativos)
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { base64ABytes, bocaAbierta, envolvente } from '../src/chaski/wav.ts';
import {
  fueCastellano, nombreDelCampo, siguienteLado, veredictoEnfermera,
  type RespuestaEnfermera, type RespuestaPaciente,
} from '../src/chaski/modelo.ts';

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
