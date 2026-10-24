// node --test tests/   (Node 22+ con tipos nativos)
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { base64ABytes, bocaAbierta, envolvente } from '../src/rimay/wav.ts';
import {
  fueCastellano, nombreDelCampo, siguienteLado, veredictoEnfermera,
  type RespuestaEnfermera, type RespuestaPaciente,
} from '../src/rimay/modelo.ts';

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

import { tramos } from '../src/rimay/tejido.ts';

test('tejido: une puntos contiguos y salta el fondo', () => {
  assert.deepEqual(tramos('.11.2', 1), [
    { desde: 1, largo: 2, valor: '1' },
    { desde: 4, largo: 1, valor: '2' },
  ]);
  // Al repetir, el último punto de una copia y el primero de la siguiente se unen.
  assert.deepEqual(tramos('1..1', 2), [
    { desde: 0, largo: 1, valor: '1' },
    { desde: 3, largo: 2, valor: '1' },
    { desde: 7, largo: 1, valor: '1' },
  ]);
});
