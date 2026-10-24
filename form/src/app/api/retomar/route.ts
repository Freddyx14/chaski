import { NextRequest, NextResponse } from "next/server";
import { ensureSchema, sql } from "@/lib/db";

// Resume by the short code (p4) a participant sees on every phrase, so progress survives
// a lost link, a cleared browser or a new phone.
export async function GET(request: NextRequest) {
  const codigo = (request.nextUrl.searchParams.get("codigo") ?? "").trim().toLowerCase();
  if (!/^p\d{1,6}$/.test(codigo)) return NextResponse.json({ error: "not found" }, { status: 404 });
  await ensureSchema();
  const q = sql();
  const p = (await q`SELECT id, codigo, sabe_escribir_quechua FROM participantes WHERE codigo = ${codigo}`) as {
    id: string; codigo: string; sabe_escribir_quechua: boolean;
  }[];
  if (!p.length) return NextResponse.json({ error: "not found" }, { status: 404 });
  const respuestas = await q`
    SELECT numero_global, quechua_texto, audio_url, audio_segundos
    FROM respuestas WHERE participante_id = ${p[0].id}`;
  return NextResponse.json({ ...p[0], respuestas });
}
