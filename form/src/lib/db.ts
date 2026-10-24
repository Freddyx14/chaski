import { neon } from "@neondatabase/serverless";

let _sql: ReturnType<typeof neon> | null = null;
let _schemaReady: Promise<void> | null = null;

export function sql() {
  if (!_sql) {
    const url = process.env.DATABASE_URL;
    if (!url) throw new Error("DATABASE_URL is not set");
    _sql = neon(url);
  }
  return _sql;
}

/** Creates the tables on first use. Idempotent, runs once per server instance. */
export function ensureSchema(): Promise<void> {
  if (!_schemaReady) {
    const q = sql();
    _schemaReady = (async () => {
      await q`CREATE TABLE IF NOT EXISTS participantes (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        n serial UNIQUE,
        codigo text UNIQUE,
        nombre_opcional text,
        sexo_opcional text,
        edad_rango_opcional text,
        lugar_opcional text,
        sabe_escribir_quechua boolean NOT NULL DEFAULT true,
        consentimiento boolean NOT NULL,
        creado timestamptz NOT NULL DEFAULT now()
      )`;
      await q`CREATE TABLE IF NOT EXISTS respuestas (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        participante_id uuid NOT NULL REFERENCES participantes(id) ON DELETE CASCADE,
        numero_global int NOT NULL,
        bloque text NOT NULL,
        numero_bloque int NOT NULL,
        castellano text NOT NULL,
        quechua_texto text,
        audio_url text,
        audio_segundos real,
        mime text,
        creado timestamptz NOT NULL DEFAULT now(),
        actualizado timestamptz NOT NULL DEFAULT now(),
        UNIQUE (participante_id, numero_global)
      )`;
    })().catch((e) => {
      _schemaReady = null;
      throw e;
    });
  }
  return _schemaReady;
}

export const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function tokenOk(token: string | null | undefined): boolean {
  const expected = process.env.EXPORT_TOKEN;
  return !!expected && !!token && token === expected;
}
