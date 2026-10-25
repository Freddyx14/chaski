// Lector mínimo de Server-Sent Events, puro para probarlo con node. Recibe el texto acumulado y devuelve
// los eventos completos más lo que todavía no terminó de llegar.

export type EventoSSE = { evento: string; datos: string };

export function leerEventosSSE(buffer: string): { eventos: EventoSSE[]; resto: string } {
  const texto = buffer.replace(/\r\n/g, '\n');
  const bloques = texto.split('\n\n');
  const resto = bloques.pop() ?? '';
  const eventos: EventoSSE[] = [];
  for (const b of bloques) {
    let evento = 'message';
    const datos: string[] = [];
    for (const linea of b.split('\n')) {
      if (linea.startsWith(':')) continue; // comentario o latido
      if (linea.startsWith('event:')) evento = linea.slice(6).trim();
      else if (linea.startsWith('data:')) datos.push(linea.slice(5).replace(/^ /, ''));
    }
    if (datos.length) eventos.push({ evento, datos: datos.join('\n') });
  }
  return { eventos, resto };
}
