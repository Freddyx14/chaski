import { NextRequest, NextResponse } from "next/server";
import { del } from "@vercel/blob";
import { ensureSchema, sql, tokenOk, UUID_RE } from "@/lib/db";

export async function GET(_request: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  if (!UUID_RE.test(id)) return NextResponse.json({ error: "not found" }, { status: 404 });
  await ensureSchema();
  const q = sql();
  const p = (await q`SELECT id, codigo, sabe_escribir_quechua FROM participantes WHERE id = ${id}`) as {
    id: string; codigo: string; sabe_escribir_quechua: boolean;
  }[];
  if (!p.length) return NextResponse.json({ error: "not found" }, { status: 404 });
  const respuestas = await q`
    SELECT numero_global, quechua_texto, audio_url, audio_segundos
    FROM respuestas WHERE participante_id = ${id}`;
  return NextResponse.json({ ...p[0], respuestas });
}

// Admin only: removes a participant, their responses and their audio files (used to clean test data).
export async function DELETE(request: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  if (!tokenOk(request.nextUrl.searchParams.get("token"))) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const { id } = await ctx.params;
  if (!UUID_RE.test(id)) return NextResponse.json({ error: "not found" }, { status: 404 });
  await ensureSchema();
  const q = sql();
  const audios = (await q`SELECT audio_url FROM respuestas WHERE participante_id = ${id} AND audio_url IS NOT NULL`) as {
    audio_url: string;
  }[];
  if (audios.length) await del(audios.map((a) => a.audio_url));
  const gone = await q`DELETE FROM participantes WHERE id = ${id} RETURNING codigo`;
  return NextResponse.json({ deleted: gone, audios_borrados: audios.length });
}
