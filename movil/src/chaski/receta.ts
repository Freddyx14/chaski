// La receta (F9, §5) y «¿me lo repite?» (F6, B8). Puro: se prueba con node.
// La indicación se arma DESDE los hechos con una plantilla, nunca la escribe un modelo: así el número
// que se dice es el que la enfermera confirmó.

export type HechosReceta = {
  medicamento: string;
  concentracion: string | null;
  cantidad: number | null;
  unidad: string;
  cada_horas: number | null;
  dias: number | null;
};

const PLURAL: Record<string, string> = {
  pastilla: 'pastillas', tableta: 'tabletas', cápsula: 'cápsulas', cucharada: 'cucharadas',
  cucharadita: 'cucharaditas', gota: 'gotas', sobre: 'sobres', ml: 'ml',
};

const UNO = ['', 'una', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez',
  'once', 'doce', 'trece', 'catorce', 'quince'];

function enLetras(n: number, femenino = true): string {
  if (Number.isInteger(n) && n > 0 && n < UNO.length) return n === 1 && !femenino ? 'un' : UNO[n];
  if (n === 0.5) return 'media';
  return String(n);
}

/** Lo que falta para poder decir la indicación completa. Sin esto, no se dice (falla cerrada). */
export function faltantes(h: HechosReceta): string[] {
  const f: string[] = [];
  if (!h.medicamento.trim()) f.push('Medicamento');
  if (!h.cantidad) f.push('Cuánto por toma');
  if (!h.cada_horas) f.push('Cada cuántas horas');
  if (!h.dias) f.push('Por cuántos días');
  return f;
}

/** «Tome una pastilla de paracetamol de 500 mg cada ocho horas, durante tres días.» */
export function indicacionDesdeHechos(h: HechosReceta): string {
  const unidad = (h.cantidad ?? 0) > 1 ? (PLURAL[h.unidad] ?? `${h.unidad}s`) : h.unidad;
  const med = [h.medicamento.trim(), h.concentracion ? `de ${h.concentracion.trim()}` : ''].filter(Boolean).join(' ');
  const cada = h.cada_horas === 24 ? 'una vez al día' : `cada ${enLetras(h.cada_horas ?? 0, false)} horas`;
  const dias = h.dias === 1 ? 'durante un día' : `durante ${enLetras(h.dias ?? 0, false)} días`;
  return `Tome ${enLetras(h.cantidad ?? 0)} ${unidad} de ${med} ${cada}, ${dias}.`;
}

const PALABRAS_NUM: Record<string, number> = {
  un: 1, una: 1, uno: 1, media: 0.5, medio: 0.5, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7,
  ocho: 8, nueve: 9, diez: 10, once: 11, doce: 12, trece: 13, catorce: 14, quince: 15, veinte: 20,
  treinta: 30,
};

function normal(t: string): string {
  return t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
}

/** Los números que aparecen en un texto, en cifras o en palabras. */
export function numerosEn(texto: string): number[] {
  const t = normal(texto);
  const salida: number[] = [];
  for (const m of t.matchAll(/\d+(?:[.,]\d+)?/g)) salida.push(Number(m[0].replace(',', '.')));
  for (const p of t.split(/[^a-z]+/)) if (p in PALABRAS_NUM) salida.push(PALABRAS_NUM[p]);
  if (/\b(una vez al dia|diario|cada dia|todos los dias)\b/.test(t)) salida.push(24);
  if (/\buna semana\b/.test(t)) salida.push(7);
  return salida;
}

export type Comprobacion = { nombre: string; ok: boolean };

/**
 * «¿Me lo repite?»: qué partes de la indicación aparecen en lo que el paciente dijo (ya pasado al
 * castellano). Es código, no un modelo: un dato que el paciente no dijo cuenta como no entendido.
 */
export function comprobarRepeticion(h: HechosReceta, dichoPorElPaciente: string): Comprobacion[] {
  const t = normal(dichoPorElPaciente);
  const nums = numerosEn(dichoPorElPaciente);
  const raiz = normal(h.medicamento).split(/\s+/)[0] ?? '';
  const nombraMedicina = raiz.length > 2 && t.includes(raiz.slice(0, Math.max(4, raiz.length - 2)));
  const nombraPastilla = /(pastilla|tableta|capsula|remedio|medicina|jarabe|gota|cucharad)/.test(t);
  return [
    { nombre: 'Qué medicina tomar', ok: nombraMedicina || nombraPastilla },
    { nombre: 'Cuánto por toma', ok: h.cantidad != null && nums.includes(h.cantidad) },
    { nombre: 'Cada cuántas horas', ok: h.cada_horas != null && nums.includes(h.cada_horas) },
    { nombre: 'Por cuántos días', ok: h.dias != null && nums.includes(h.dias) },
  ];
}
