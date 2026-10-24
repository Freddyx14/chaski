import { NextRequest, NextResponse } from "next/server";
import { ensureSchema, sql, tokenOk } from "@/lib/db";

type Row = {
  codigo: string; bloque: string; numero_bloque: number; numero_global: number;
  audio_url: string | null; quechua_texto: string | null; castellano: string;
  audio_segundos: number | null; consentimiento: boolean;
};

// JSONL, one line per response, in Ricardo's contract. Participants without consent are excluded.
export async function GET(request: NextRequest) {
  if (!tokenOk(request.nextUrl.searchParams.get("token"))) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  await ensureSchema();
  const rows = (await sql()`
    SELECT p.codigo, r.bloque, r.numero_bloque, r.numero_global, r.audio_url, r.quechua_texto,
           r.castellano, r.audio_segundos, p.consentimiento
    FROM respuestas r JOIN participantes p ON p.id = r.participante_id
    WHERE p.consentimiento = true
    ORDER BY p.n, r.numero_global`) as Row[];
  const body = rows
    .map((r) =>
      JSON.stringify({
        persona: r.codigo,
        bloque: r.bloque,
        numero: r.numero_bloque,
        numero_global: r.numero_global,
        audio: r.audio_url,
        transcripcion: r.quechua_texto,
        castellano: r.castellano,
        segundos: r.audio_segundos,
        consentimiento: r.consentimiento,
      }),
    )
    .join("\n");
  return new NextResponse(body ? body + "\n" : "", {
    headers: {
      "content-type": "application/x-ndjson; charset=utf-8",
      "content-disposition": 'inline; filename="rimay-respuestas.jsonl"',
      "cache-control": "no-store",
    },
  });
}
