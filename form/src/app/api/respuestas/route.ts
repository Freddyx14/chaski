import { NextResponse } from "next/server";
import { put } from "@vercel/blob";
import { ensureSchema, sql, UUID_RE } from "@/lib/db";
import { FRASE_POR_GLOBAL } from "@/lib/frases";

const MAX_AUDIO_BYTES = 4 * 1024 * 1024; // Vercel function bodies cap at 4.5 MB

function extFor(mime: string): string {
  if (mime.includes("mp4") || mime.includes("m4a") || mime.includes("aac")) return "m4a";
  if (mime.includes("ogg")) return "ogg";
  if (mime.includes("wav")) return "wav";
  if (mime.includes("mpeg")) return "mp3";
  return "webm";
}

export async function POST(request: Request) {
  const form = await request.formData().catch(() => null);
  if (!form) return NextResponse.json({ error: "bad form" }, { status: 400 });

  const participanteId = String(form.get("participante_id") ?? "");
  const numeroGlobal = Number(form.get("numero_global"));
  const frase = FRASE_POR_GLOBAL.get(numeroGlobal);
  if (!UUID_RE.test(participanteId) || !frase) {
    return NextResponse.json({ error: "bad participante or frase" }, { status: 400 });
  }

  // Block E: the Quechua is given, so it is the transcript regardless of what the client sends.
  const textoRaw = frase.chanka ?? String(form.get("quechua_texto") ?? "");
  const texto = textoRaw.trim() ? textoRaw.trim().slice(0, 2000) : null;
  const audio = form.get("audio");
  const hasAudio = audio instanceof File && audio.size > 0;
  const segundosRaw = Number(form.get("audio_segundos"));
  const segundos = Number.isFinite(segundosRaw) && segundosRaw > 0 ? Math.round(segundosRaw * 10) / 10 : null;

  if (!texto && !hasAudio) {
    return NextResponse.json({ error: "Escriba la frase o grábela." }, { status: 400 });
  }
  if (hasAudio && audio.size > MAX_AUDIO_BYTES) {
    return NextResponse.json({ error: "La grabación es muy larga." }, { status: 413 });
  }

  await ensureSchema();
  const q = sql();
  const p = (await q`SELECT codigo FROM participantes WHERE id = ${participanteId}`) as { codigo: string }[];
  if (!p.length) return NextResponse.json({ error: "participante not found" }, { status: 404 });

  let audioUrl: string | null = null;
  let mime: string | null = null;
  if (hasAudio) {
    mime = (audio.type || "audio/webm").split(";")[0];
    const blob = await put(
      `rimay/${p[0].codigo}/${String(numeroGlobal).padStart(3, "0")}.${extFor(mime)}`,
      audio,
      { access: "public", addRandomSuffix: true, contentType: mime },
    );
    audioUrl = blob.url;
  }

  // Re-saving overwrites. Without a new recording, the previous audio is kept.
  const rows = await q`
    INSERT INTO respuestas (participante_id, numero_global, bloque, numero_bloque, castellano,
                            quechua_texto, audio_url, audio_segundos, mime)
    VALUES (${participanteId}, ${numeroGlobal}, ${frase.bloque}, ${frase.numero}, ${frase.castellano},
            ${texto}, ${audioUrl}, ${hasAudio ? segundos : null}, ${mime})
    ON CONFLICT (participante_id, numero_global) DO UPDATE SET
      quechua_texto = EXCLUDED.quechua_texto,
      audio_url = COALESCE(EXCLUDED.audio_url, respuestas.audio_url),
      audio_segundos = CASE WHEN EXCLUDED.audio_url IS NULL THEN respuestas.audio_segundos ELSE EXCLUDED.audio_segundos END,
      mime = COALESCE(EXCLUDED.mime, respuestas.mime),
      actualizado = now()
    RETURNING numero_global, quechua_texto, audio_url, audio_segundos`;
  return NextResponse.json((rows as Record<string, unknown>[])[0]);
}
