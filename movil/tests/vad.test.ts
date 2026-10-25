// node --test tests/   (Node 22+ con tipos nativos)
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { nuevoVad, pasoVad, VAD, type EventoVad } from '../src/chaski/vad.ts';

/** Corre el detector sobre una serie [ms, dB] cada 80 ms (el intervalo de la grabadora) y junta los eventos. */
function correr(tramos: [number, number][]): { t: number; ev: EventoVad }[] {
  let s = nuevoVad(0);
  const eventos: { t: number; ev: EventoVad }[] = [];
  let t = 0;
  for (const [dur, db] of tramos) {
    for (const fin = t + dur; t < fin; t += 80) {
      const [n, ev] = pasoVad(s, db, t);
      s = n;
      if (ev) eventos.push({ t, ev });
    }
  }
  return eventos;
}

test('sala callada, alguien habla 2 s y se calla: un inicio y un fin', () => {
  const ev = correr([[600, -50], [2000, -25], [1200, -50]]);
  assert.deepEqual(ev.map((e) => e.ev), ['inicio', 'fin']);
  assert.ok(ev[1].t >= 2600 + VAD.finMs - 80, 'no corta antes del silencio sostenido');
});

test('una tos corta no abre el turno', () => {
  assert.deepEqual(correr([[600, -50], [120, -20], [3000, -50]]), []);
});

test('una pausa breve entre palabras no cierra el turno', () => {
  const ev = correr([[600, -50], [1000, -25], [400, -50], [1000, -25], [1200, -50]]);
  assert.deepEqual(ev.map((e) => e.ev), ['inicio', 'fin']);
});

test('el silencio digital del simulador no vuelve todo «voz»: el piso tiene un mínimo', () => {
  const ev = correr([[600, -160], [500, -70], [1500, -25], [1200, -160]]);
  assert.deepEqual(ev.map((e) => e.ev), ['inicio', 'fin']);
});

test('en una sala ruidosa calibra el piso alto y solo la voz por encima abre el turno', () => {
  assert.deepEqual(correr([[600, -35], [2000, -33]]), []);
  assert.deepEqual(correr([[600, -35], [1000, -15], [1200, -35]]).map((e) => e.ev), ['inicio', 'fin']);
});

test('si nadie para de hablar, el tope cierra el turno', () => {
  const ev = correr([[600, -50], [VAD.maxTurnoMs + 1000, -20]]);
  assert.equal(ev.at(-1)?.ev, 'fin');
});

test('sin nadie que hable, pide reiniciar la grabación', () => {
  const ev = correr([[VAD.reinicioMs + 200, -50]]);
  assert.equal(ev[0]?.ev, 'reiniciar');
});

test('un nivel indefinido no rompe ni dispara nada', () => {
  const [s, ev] = pasoVad(nuevoVad(0), undefined, 100);
  assert.equal(ev, null);
  assert.equal(s.muestras.length, 0);
});

import { COLA_MS, esperaParaEscuchar, LECTURA_BLOQUEO_MS } from '../src/chaski/conversacion.ts';

test('mientras suena audio, nunca se abre el micrófono', () => {
  for (const f of ['listo', 'dicho', 'pregunta', 'noentendi', 'paciente', 'bloqueado']) {
    assert.equal(esperaParaEscuchar({ f, vozLista: true }, true), null, f);
  }
});

test('mientras piensa o graba no se vuelve a escuchar', () => {
  assert.equal(esperaParaEscuchar({ f: 'pensando' }, false), null);
  assert.equal(esperaParaEscuchar({ f: 'grabando' }, false), null);
});

test('después de decirlo, o de una repregunta, vuelve a escuchar tras la cola del parlante', () => {
  assert.equal(esperaParaEscuchar({ f: 'dicho', vozLista: false }, false), null);
  assert.equal(esperaParaEscuchar({ f: 'dicho', vozLista: true }, false), COLA_MS);
  assert.equal(esperaParaEscuchar({ f: 'pregunta' }, false), COLA_MS);
  assert.equal(esperaParaEscuchar({ f: 'noentendi' }, false), COLA_MS);
  assert.equal(esperaParaEscuchar({ f: 'paciente' }, false), COLA_MS);
});

test('el bloqueo se deja leer; el ensayo de la barrera se queda quieto', () => {
  assert.equal(esperaParaEscuchar({ f: 'bloqueado' }, false), LECTURA_BLOQUEO_MS);
  assert.equal(esperaParaEscuchar({ f: 'bloqueado', ensayo: true }, false), null);
  assert.equal(esperaParaEscuchar({ f: 'dicho', vozLista: true, ensayo: true }, false), null);
});

test('un error de red espera un toque; una grabación muda solo vuelve a escuchar', () => {
  assert.equal(esperaParaEscuchar({ f: 'error' }, false), null);
  assert.equal(esperaParaEscuchar({ f: 'error', deGrabacion: true }, false), 300);
});
