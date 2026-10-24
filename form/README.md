# Rimay · recolector de frases en quechua chanka

Mobile-first web form that collects Quechua Chanka data from volunteers (relatives in Peru).
For each phrase the person reads the Spanish, types it in Quechua, records themselves reading
what they typed, and saves. That yields:

- Spanish → Quechua written pairs (translation fine-tuning)
- audio + exact transcript (ASR / TTS fine-tuning)

Production: https://rimay-datos.vercel.app (Vercel project `rimay-datos`, Freddy's personal account).

## How it works

- `src/frases/frases.json` is a **copy** of `../ricardo-artifacts/datos/frases/frases.json`, committed so
  the deploy doesn't depend on the parent folder. After Ricardo changes the source, run
  `./scripts/sync-frases.sh`, commit and redeploy.
- Parts: 1 C "Lo que dice la enfermera", 2 M "Medicinas", 3 N "Números y días",
  4 B "Lo que dice el paciente", 5 E "Extra (opcional)" (Quechua given, audio only).
  People see the global number (1..175, from `numeracion`).
- Participant id lives in `localStorage` (`rimay.participante`), so they can close and continue.
- Audio: `MediaRecorder` in the browser (webm/opus on Chrome/Android, mp4/aac on iOS Safari),
  sent to `POST /api/respuestas`, stored in Vercel Blob (`rimay/<codigo>/<nnn>-<random>.<ext>`),
  URL saved in Postgres. Recordings are capped at 90 s (function body limit is 4.5 MB).
- Text and metadata: Neon Postgres. Tables are created on first request (`src/lib/db.ts`).
  `respuestas` is unique on `(participante_id, numero_global)`; re-saving overwrites, and a
  re-save without a new recording keeps the previous audio.

## Run locally

```sh
cd form
npm install
vercel env pull .env.local     # gets the env vars below (never commit it)
lsof -nP -iTCP:3000 -sTCP:LISTEN  # pick a free port
npm run dev -- -p 3000
```

Recording needs HTTPS or `localhost`; to test on a phone use the deployed URL.

## Env vars (set in Vercel, names only)

| Name | What |
|---|---|
| `DATABASE_URL` | Neon Postgres connection string |
| `BLOB_READ_WRITE_TOKEN` | Vercel Blob store `rimay-audios` (public access, random suffixes) |
| `EXPORT_TOKEN` | Shared secret for `/admin` and `/api/export` |

## Export for Ricardo

```sh
curl "https://rimay-datos.vercel.app/api/export?token=$EXPORT_TOKEN" > respuestas.jsonl
```

One line per response, participants without consent excluded:

```json
{"persona":"p1","bloque":"C","numero":1,"numero_global":1,"audio":"https://…","transcripcion":"…","castellano":"…","segundos":3.4,"consentimiento":true}
```

## Admin

`https://rimay-datos.vercel.app/admin?token=<EXPORT_TOKEN>` lists participants with counts; click a
code to see and play their responses.

Delete a participant (rows + audio files), e.g. test data:

```sh
curl -X DELETE "https://rimay-datos.vercel.app/api/participantes/<uuid>?token=$EXPORT_TOKEN"
```

## Deploy

```sh
cd form && vercel deploy --prod
```
