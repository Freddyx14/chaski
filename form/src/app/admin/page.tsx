import { ensureSchema, sql, tokenOk, UUID_RE } from "@/lib/db";
import { FRASES, TOTAL_OBLIGATORIAS } from "@/lib/frases";

export const dynamic = "force-dynamic";
export const metadata = { title: "Chaski · admin", robots: { index: false } };

type P = {
  id: string; codigo: string; nombre_opcional: string | null; sexo_opcional: string | null;
  edad_rango_opcional: string | null; lugar_opcional: string | null; sabe_escribir_quechua: boolean;
  consentimiento: boolean; creado: string; total: number; con_audio: number; con_texto: number; segundos: number | null;
};
type R = { numero_global: number; castellano: string; quechua_texto: string | null; audio_url: string | null; audio_segundos: number | null };

export default async function Admin({ searchParams }: { searchParams: Promise<{ token?: string; p?: string }> }) {
  const { token, p } = await searchParams;
  if (!tokenOk(token)) return <main className="admin"><p>No autorizado.</p></main>;
  await ensureSchema();
  const q = sql();
  const ps = (await q`
    SELECT p.*, count(r.id)::int AS total,
           count(r.audio_url)::int AS con_audio,
           count(r.quechua_texto)::int AS con_texto,
           round(sum(r.audio_segundos)::numeric, 1)::float AS segundos
    FROM participantes p LEFT JOIN respuestas r ON r.participante_id = p.id
    GROUP BY p.id ORDER BY p.n DESC`) as P[];
  const sel = p && UUID_RE.test(p) ? ps.find((x) => x.id === p) : undefined;
  const rs = sel
    ? ((await q`SELECT numero_global, castellano, quechua_texto, audio_url, audio_segundos
                FROM respuestas WHERE participante_id = ${sel.id} ORDER BY numero_global`) as R[])
    : [];
  const t = encodeURIComponent(token!);
  const totalAudios = ps.reduce((a, x) => a + x.con_audio, 0);
  const totalSeg = ps.reduce((a, x) => a + (x.segundos ?? 0), 0);

  return (
    <main className="admin">
      <h1>Chaski · datos</h1>
      <p>
        {ps.length} participantes · {totalAudios} audios · {(totalSeg / 60).toFixed(1)} min ·{" "}
        <a href={`/api/export?token=${t}`}>Exportar JSONL</a>
      </p>
      <table>
        <thead>
          <tr><th>Código</th><th>Nombre</th><th>Datos</th><th>Escribe</th><th>Consent.</th><th>Resp.</th><th>Audio</th><th>Texto</th><th>Min</th></tr>
        </thead>
        <tbody>
          {ps.map((x) => (
            <tr key={x.id} className={sel?.id === x.id ? "sel" : ""}>
              <td><a href={`/admin?token=${t}&p=${x.id}`}>{x.codigo}</a></td>
              <td>{x.nombre_opcional ?? "—"}</td>
              <td>{[x.sexo_opcional, x.edad_rango_opcional, x.lugar_opcional].filter(Boolean).join(" · ") || "—"}</td>
              <td>{x.sabe_escribir_quechua ? "sí" : "no"}</td>
              <td>{x.consentimiento ? "sí" : "NO"}</td>
              <td>{x.total}/{TOTAL_OBLIGATORIAS}</td>
              <td>{x.con_audio}</td>
              <td>{x.con_texto}</td>
              <td>{((x.segundos ?? 0) / 60).toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {sel && (
        <section>
          <h2>{sel.codigo} · {rs.length} respuestas de {FRASES.length}</h2>
          <ul className="resp">
            {rs.map((r) => (
              <li key={r.numero_global}>
                <div><b>{r.numero_global}.</b> {r.castellano}</div>
                <div className="qu">{r.quechua_texto ?? <i>(sin texto)</i>}</div>
                {r.audio_url ? (
                  <audio controls preload="none" src={r.audio_url} />
                ) : (
                  <i>(sin audio)</i>
                )}
                {r.audio_segundos ? <span> {r.audio_segundos}s</span> : null}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
