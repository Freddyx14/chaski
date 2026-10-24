import data from "@/frases/frases.json";

export type Bloque = "C" | "M" | "N" | "B" | "E";

export type Frase = {
  global: number;
  bloque: Bloque;
  numero: number;
  castellano: string;
  chanka?: string; // only block E: the Quechua is given, they only read it aloud
};

export const PARTES: { bloque: Bloque; parte: number; titulo: string; opcional?: boolean }[] = [
  { bloque: "C", parte: 1, titulo: "Lo que dice la enfermera" },
  { bloque: "M", parte: 2, titulo: "Medicinas" },
  { bloque: "N", parte: 3, titulo: "Números y días" },
  { bloque: "B", parte: 4, titulo: "Lo que dice el paciente" },
  { bloque: "E", parte: 5, titulo: "Extra (opcional)", opcional: true },
];

type Raw = {
  clinicas_sin_traducir: string[];
  medicamentos_y_prestamos: string[];
  numeros_y_tiempos: string[];
  respuestas_libres: string[];
  verificadas: { castellano: string; chanka: string }[];
  numeracion: Record<string, [string, number]>;
};

const raw = data as unknown as Raw;

function lookup(bloque: Bloque, numero: number): { castellano: string; chanka?: string } {
  const i = numero - 1;
  switch (bloque) {
    case "C": return { castellano: raw.clinicas_sin_traducir[i] };
    case "M": return { castellano: raw.medicamentos_y_prestamos[i] };
    case "N": return { castellano: raw.numeros_y_tiempos[i] };
    case "B": return { castellano: raw.respuestas_libres[i] };
    case "E": return { castellano: raw.verificadas[i].castellano, chanka: raw.verificadas[i].chanka };
  }
}

export const FRASES: Frase[] = Object.entries(raw.numeracion)
  .map(([g, [b, n]]) => {
    const bloque = b as Bloque;
    const f = lookup(bloque, n);
    if (!f || !f.castellano) throw new Error(`frases.json: no phrase for ${g} -> ${b}${n}`);
    return { global: Number(g), bloque, numero: n, ...f };
  })
  .sort((a, b) => a.global - b.global);

export const FRASE_POR_GLOBAL = new Map(FRASES.map((f) => [f.global, f]));
export const TOTAL_OBLIGATORIAS = FRASES.filter((f) => f.bloque !== "E").length;
