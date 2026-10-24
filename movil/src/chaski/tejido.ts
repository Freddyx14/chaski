// Puro, para probarlo con node: convierte una fila de un motivo tejido en rectángulos.

/** Une los puntos contiguos de una fila del mapa en un solo rectángulo: menos nodos, mismo tejido. */
export function tramos(fila: string, repeticiones: number): { desde: number; largo: number; valor: string }[] {
  const linea = fila.repeat(repeticiones);
  const salida: { desde: number; largo: number; valor: string }[] = [];
  let i = 0;
  while (i < linea.length) {
    const v = linea[i];
    let j = i;
    while (j < linea.length && linea[j] === v) j++;
    if (v !== '.') salida.push({ desde: i, largo: j - i, valor: v });
    i = j;
  }
  return salida;
}
