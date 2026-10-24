// La consulta en curso: los turnos, para el historial. Vive en memoria y se borra al terminar.
// No se guarda nada del paciente en el teléfono (SOT §8).
import { useSyncExternalStore } from 'react';

import type { Turno } from './modelo';

let turnos: Turno[] = [];
let inicio = Date.now();
const oyentes = new Set<() => void>();
const avisar = () => oyentes.forEach((o) => o());

export function agregarTurno(t: Omit<Turno, 'id' | 'hora'>) {
  turnos = [...turnos, { ...t, id: turnos.length + 1, hora: new Date() }];
  avisar();
}

export function nuevaConsulta() {
  turnos = [];
  inicio = Date.now();
  avisar();
}

export function inicioDeConsulta() {
  return inicio;
}

export function useTurnos(): Turno[] {
  return useSyncExternalStore(
    (o) => (oyentes.add(o), () => oyentes.delete(o)),
    () => turnos,
  );
}
