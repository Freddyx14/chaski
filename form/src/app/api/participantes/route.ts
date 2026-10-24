import { NextResponse } from "next/server";
import { ensureSchema, sql } from "@/lib/db";

const clip = (v: unknown, max = 120) =>
  typeof v === "string" && v.trim() ? v.trim().slice(0, max) : null;

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || body.consentimiento !== true) {
    return NextResponse.json({ error: "Se necesita el consentimiento." }, { status: 400 });
  }
  await ensureSchema();
  const q = sql();
  const rows = (await q`
    INSERT INTO participantes (nombre_opcional, sexo_opcional, edad_rango_opcional, lugar_opcional,
                               sabe_escribir_quechua, consentimiento)
    VALUES (${clip(body.nombre)}, ${clip(body.sexo, 40)}, ${clip(body.edad, 40)}, ${clip(body.lugar)},
            ${body.sabe_escribir_quechua !== false}, true)
    RETURNING id, n`) as { id: string; n: number }[];
  const { id, n } = rows[0];
  const codigo = `p${n}`;
  await q`UPDATE participantes SET codigo = ${codigo} WHERE id = ${id}`;
  return NextResponse.json({ id, codigo, sabe_escribir_quechua: body.sabe_escribir_quechua !== false });
}
