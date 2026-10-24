"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FRASES, PARTES, TOTAL_OBLIGATORIAS, type Bloque } from "@/lib/frases";

type Participante = { id: string; codigo: string; sabe_escribir_quechua: boolean };
type Guardada = { numero_global: number; quechua_texto: string | null; audio_url: string | null; audio_segundos: number | null };
type Pantalla = "cargando" | "bienvenida" | "frase" | "partes" | "gracias";

const LS_PARTICIPANTE = "rimay.participante";
const LS_INDICE = "rimay.indice";
const MAX_SEGUNDOS = 90;
const ULTIMA_OBLIGATORIA = FRASES.findLastIndex((f) => f.bloque !== "E");

function lsGet(k: string): string | null {
  try { return localStorage.getItem(k); } catch { return null; }
}
function lsSet(k: string, v: string) {
  try { localStorage.setItem(k, v); } catch { /* private mode: progress is still in the server */ }
}
function lsDel(k: string) {
  try { localStorage.removeItem(k); } catch { /* ignore */ }
}

function elegirMime(): string {
  if (typeof MediaRecorder === "undefined") return "";
  for (const m of ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/aac", "audio/ogg;codecs=opus"]) {
    try { if (MediaRecorder.isTypeSupported(m)) return m; } catch { /* ignore */ }
  }
  return "";
}

export default function Recolector() {
  const [pantalla, setPantalla] = useState<Pantalla>("cargando");
  const [part, setPart] = useState<Participante | null>(null);
  const [guardadas, setGuardadas] = useState<Map<number, Guardada>>(new Map());
  const [indice, setIndice] = useState(0);

  // Resume where they left off.
  useEffect(() => {
    const id = lsGet(LS_PARTICIPANTE);
    if (!id) { setPantalla("bienvenida"); return; }
    fetch(`/api/participantes/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        setPart({ id: d.id, codigo: d.codigo, sabe_escribir_quechua: d.sabe_escribir_quechua });
        setGuardadas(new Map((d.respuestas as Guardada[]).map((g) => [g.numero_global, g])));
        const i = Number(lsGet(LS_INDICE) ?? 0);
        setIndice(Number.isFinite(i) && i >= 0 && i < FRASES.length ? i : 0);
        setPantalla("frase");
      })
      .catch((status) => {
        if (status === 404) lsDel(LS_PARTICIPANTE);
        setPantalla("bienvenida");
      });
  }, []);

  useEffect(() => { if (part) lsSet(LS_INDICE, String(indice)); }, [indice, part]);

  const irA = useCallback((i: number) => {
    setIndice(i);
    setPantalla("frase");
    window.scrollTo({ top: 0 });
  }, []);

  const siguiente = useCallback(() => {
    if (indice === ULTIMA_OBLIGATORIA || indice >= FRASES.length - 1) {
      setIndice(Math.min(indice + 1, FRASES.length - 1));
      setPantalla("gracias");
      window.scrollTo({ top: 0 });
      return;
    }
    irA(indice + 1);
  }, [indice, irA]);

  if (pantalla === "cargando") return <main className="wrap"><p className="muted">Cargando…</p></main>;
  if (pantalla === "bienvenida" || !part) {
    return (
      <Bienvenida
        onListo={(p) => {
          lsSet(LS_PARTICIPANTE, p.id);
          setPart(p);
          setGuardadas(new Map());
          irA(0);
        }}
      />
    );
  }
  if (pantalla === "partes") {
    return <Partes guardadas={guardadas} onElegir={irA} onVolver={() => setPantalla("frase")} />;
  }
  if (pantalla === "gracias") {
    const hechas = [...guardadas.keys()].filter((g) => FRASES.find((f) => f.global === g)?.bloque !== "E").length;
    const terminoExtra = indice >= FRASES.length - 1 && FRASES[indice].bloque === "E";
    const primeraExtra = FRASES.findIndex((f) => f.bloque === "E");
    return (
      <main className="wrap">
        <h1 className="big">¡Gracias!</h1>
        <p>Usted guardó {hechas} de {TOTAL_OBLIGATORIAS} frases. Su ayuda enseña a Rimay a hablar quechua chanka.</p>
        <p className="muted">Su código es <b>{part.codigo}</b>.</p>
        {!terminoExtra && (
          <button className="btn primary" onClick={() => irA(primeraExtra)}>
            Seguir con la parte extra (opcional)
          </button>
        )}
        <button className="btn" onClick={() => setPantalla("partes")}>Ver las partes</button>
      </main>
    );
  }

  return (
    <FraseView
      key={FRASES[indice].global}
      part={part}
      indice={indice}
      guardada={guardadas.get(FRASES[indice].global)}
      guardadas={guardadas}
      onGuardada={(g) => {
        setGuardadas((m) => new Map(m).set(g.numero_global, g));
        siguiente();
      }}
      onSaltar={siguiente}
      onAnterior={() => indice > 0 && irA(indice - 1)}
      onPartes={() => setPantalla("partes")}
    />
  );
}

function Bienvenida({ onListo }: { onListo: (p: Participante) => void }) {
  const [consent, setConsent] = useState(false);
  const [sabe, setSabe] = useState<boolean | null>(null);
  const [nombre, setNombre] = useState("");
  const [sexo, setSexo] = useState("");
  const [edad, setEdad] = useState("");
  const [lugar, setLugar] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  async function empezar() {
    setError("");
    if (!consent) { setError("Marque la casilla para aceptar."); return; }
    if (sabe === null) { setError("Díganos si escribe en quechua."); return; }
    setEnviando(true);
    let r: Response;
    try {
      r = await fetch("/api/participantes", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ consentimiento: true, sabe_escribir_quechua: sabe, nombre, sexo, edad, lugar }),
      });
    } catch {
      // fetch only throws when the request never reached the server.
      setError("No se pudo guardar. Revise su internet e intente de nuevo.");
      setEnviando(false);
      return;
    }
    if (!r.ok) {
      setError("No se pudo guardar por un problema nuestro, no de su internet. Intente en unos minutos.");
      setEnviando(false);
      return;
    }
    onListo(await r.json());
  }

  return (
    <main className="wrap">
      <h1 className="big">Rimay</h1>
      <p className="lead">
        Rimay es una aplicación que ayuda al personal de la posta a hablar con los pacientes en quechua.
        Lo que usted escriba y grabe le enseña a traducir, entender y hablar quechua chanka.
      </p>
      <p>Le mostraremos frases en castellano. Escríbalas en quechua y luego léalas en voz alta para grabarlas. Puede cerrar y volver cuando quiera.</p>

      <fieldset className="card">
        <legend>¿Usted escribe en quechua?</legend>
        <div className="row">
          <button type="button" className={`btn choice ${sabe === true ? "on" : ""}`} onClick={() => setSabe(true)}>Sí</button>
          <button type="button" className={`btn choice ${sabe === false ? "on" : ""}`} onClick={() => setSabe(false)}>No, solo hablo</button>
        </div>
      </fieldset>

      <details className="card">
        <summary>Datos opcionales (puede dejarlos en blanco)</summary>
        <label>Nombre<input value={nombre} onChange={(e) => setNombre(e.target.value)} autoComplete="off" /></label>
        <label>Sexo
          <select value={sexo} onChange={(e) => setSexo(e.target.value)}>
            <option value="">—</option><option>Mujer</option><option>Hombre</option><option>Prefiero no decir</option>
          </select>
        </label>
        <label>Edad
          <select value={edad} onChange={(e) => setEdad(e.target.value)}>
            <option value="">—</option><option>Menos de 18</option><option>18 a 29</option><option>30 a 44</option>
            <option>45 a 59</option><option>60 o más</option>
          </select>
        </label>
        <label>¿De dónde es? (pueblo, provincia)<input value={lugar} onChange={(e) => setLugar(e.target.value)} autoComplete="off" /></label>
      </details>

      <label className="consent card">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        <span>
          Acepto que mi voz y lo que escriba se usen para entrenar la aplicación Rimay y para mostrarla en
          Cal Hacks, un concurso de tecnología en Estados Unidos.
        </span>
      </label>

      {error && <p className="error">{error}</p>}
      <button className="btn primary" disabled={enviando} onClick={empezar}>
        {enviando ? "Un momento…" : "Empezar"}
      </button>
    </main>
  );
}

function Progreso({ indice, guardadas }: { indice: number; guardadas: Map<number, Guardada> }) {
  const f = FRASES[indice];
  const parte = PARTES.find((p) => p.bloque === f.bloque)!;
  const deParte = FRASES.filter((x) => x.bloque === f.bloque);
  const hechasParte = deParte.filter((x) => guardadas.has(x.global)).length;
  const hechasTotal = FRASES.filter((x) => x.bloque !== "E" && guardadas.has(x.global)).length;
  return (
    <div className="prog">
      <div className="prog-label">
        <span>Parte {parte.parte} · {parte.titulo}</span>
        <span>{hechasParte}/{deParte.length}</span>
      </div>
      <div className="bar"><div style={{ width: `${(100 * hechasParte) / deParte.length}%` }} /></div>
      <div className="prog-label small">
        <span>Total</span><span>{hechasTotal}/{TOTAL_OBLIGATORIAS}</span>
      </div>
      <div className="bar thin"><div style={{ width: `${(100 * hechasTotal) / TOTAL_OBLIGATORIAS}%` }} /></div>
    </div>
  );
}

function Partes({ guardadas, onElegir, onVolver }: {
  guardadas: Map<number, Guardada>; onElegir: (i: number) => void; onVolver: () => void;
}) {
  return (
    <main className="wrap">
      <h1>Partes</h1>
      {PARTES.map((p) => {
        const fs = FRASES.filter((f) => f.bloque === p.bloque);
        const hechas = fs.filter((f) => guardadas.has(f.global)).length;
        const primeraPendiente = fs.find((f) => !guardadas.has(f.global)) ?? fs[0];
        return (
          <button key={p.bloque} className="btn parte" onClick={() => onElegir(FRASES.indexOf(primeraPendiente))}>
            <span>Parte {p.parte} · {p.titulo}</span>
            <span className="muted">{hechas}/{fs.length}</span>
          </button>
        );
      })}
      <button className="btn" onClick={onVolver}>Volver</button>
    </main>
  );
}

function FraseView({ part, indice, guardada, guardadas, onGuardada, onSaltar, onAnterior, onPartes }: {
  part: Participante; indice: number; guardada?: Guardada; guardadas: Map<number, Guardada>;
  onGuardada: (g: Guardada) => void; onSaltar: () => void; onAnterior: () => void; onPartes: () => void;
}) {
  const f = FRASES[indice];
  const esExtra = f.bloque === ("E" as Bloque);
  const [texto, setTexto] = useState(guardada?.quechua_texto && !esExtra ? guardada.quechua_texto : "");
  const rec = useGrabadora();
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  const tieneAudioPrevio = !!guardada?.audio_url && !rec.blob;
  const puedeGuardar = !enviando && rec.estado !== "grabando" &&
    (esExtra ? !!rec.blob || tieneAudioPrevio : !!texto.trim() || !!rec.blob || tieneAudioPrevio);

  async function guardar() {
    setError("");
    if (esExtra && !rec.blob && !tieneAudioPrevio) { setError("Grabe la frase antes de guardar."); return; }
    if (!esExtra && !texto.trim() && !rec.blob && !tieneAudioPrevio) { setError("Escriba la frase o grábela."); return; }
    setEnviando(true);
    try {
      const fd = new FormData();
      fd.set("participante_id", part.id);
      fd.set("numero_global", String(f.global));
      fd.set("quechua_texto", esExtra ? "" : texto);
      if (rec.blob) {
        const ext = rec.blob.type.includes("mp4") ? "m4a" : rec.blob.type.includes("ogg") ? "ogg" : "webm";
        fd.set("audio", rec.blob, `audio.${ext}`);
        fd.set("audio_segundos", String(rec.segundos));
      }
      const r = await fetch("/api/respuestas", { method: "POST", body: fd });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d.error || "No se pudo guardar.");
      }
      onGuardada(await r.json());
    } catch (e) {
      setError(e instanceof Error && e.message ? `${e.message} Revise su internet e intente de nuevo.` : "No se pudo guardar.");
      setEnviando(false);
    }
  }

  return (
    <main className="wrap">
      <div className="top">
        <button className="link" onClick={onPartes}>☰ Partes</button>
        <span className="muted">Código {part.codigo}</span>
      </div>
      <Progreso indice={indice} guardadas={guardadas} />

      <div className="frase card">
        <div className="num">{f.global}</div>
        <p className="es">{f.castellano}</p>
        {esExtra && <p className="qu-given">{f.chanka}</p>}
        {guardada && <p className="ok">✓ Ya guardada. Puede cambiarla.</p>}
      </div>

      {esExtra ? (
        <p className="regla">Lea en voz alta el texto en quechua de arriba y grábelo.</p>
      ) : (
        <>
          <label className="field">
            <span>Escríbalo en quechua{part.sabe_escribir_quechua ? "" : " (si puede)"}</span>
            <textarea
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              rows={3}
              autoCapitalize="sentences"
              autoCorrect="off"
              spellCheck={false}
              placeholder={part.sabe_escribir_quechua ? "" : "Si no escribe quechua, solo grabe la frase"}
            />
          </label>
          <p className="regla">
            {texto.trim()
              ? "Ahora lea en voz alta exactamente lo que escribió."
              : "Diga la frase en quechua y grábela."}
          </p>
        </>
      )}

      <Grabadora rec={rec} audioPrevio={tieneAudioPrevio ? guardada!.audio_url! : null} />

      {error && <p className="error">{error}</p>}
      <button className="btn primary" disabled={!puedeGuardar} onClick={guardar}>
        {enviando ? "Guardando…" : "Guardar y seguir"}
      </button>
      <div className="row">
        <button className="btn" onClick={onAnterior} disabled={indice === 0 || enviando}>← Anterior</button>
        <button className="btn" onClick={onSaltar} disabled={enviando}>Saltar →</button>
      </div>
      {!esExtra && <p className="muted small center">Si no sabe una frase, toque «Saltar».</p>}
    </main>
  );
}

type Rec = ReturnType<typeof useGrabadora>;

function useGrabadora() {
  const [estado, setEstado] = useState<"listo" | "grabando" | "grabado">("listo");
  const [blob, setBlob] = useState<Blob | null>(null);
  const [segundos, setSegundos] = useState(0);
  const [error, setError] = useState("");
  const mrRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const inicioRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const url = useMemo(() => (blob ? URL.createObjectURL(blob) : null), [blob]);

  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  useEffect(() => () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (mrRef.current?.state === "recording") mrRef.current.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
  }, []);

  const detener = useCallback(() => {
    if (mrRef.current?.state === "recording") mrRef.current.stop();
  }, []);

  const iniciar = useCallback(async () => {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("Este teléfono no permite grabar desde el navegador. Pruebe con Chrome o Safari actualizado.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 },
      });
      streamRef.current = stream;
      const mime = elegirMime();
      const mr = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      const partes: Blob[] = [];
      mr.ondataavailable = (e) => { if (e.data && e.data.size > 0) partes.push(e.data); };
      mr.onstop = () => {
        if (timerRef.current) clearInterval(timerRef.current);
        const dur = (Date.now() - inicioRef.current) / 1000;
        const type = (mr.mimeType || mime || "audio/webm").split(";")[0];
        const b = new Blob(partes, { type });
        stream.getTracks().forEach((t) => t.stop()); // release the mic between phrases
        if (b.size === 0) { setError("No se grabó nada. Intente de nuevo."); setEstado("listo"); return; }
        setBlob(b);
        setSegundos(Math.round(dur * 10) / 10);
        setEstado("grabado");
      };
      mrRef.current = mr;
      inicioRef.current = Date.now();
      setSegundos(0);
      mr.start(250);
      setEstado("grabando");
      timerRef.current = setInterval(() => {
        const s = (Date.now() - inicioRef.current) / 1000;
        setSegundos(Math.floor(s));
        if (s >= MAX_SEGUNDOS) mr.stop();
      }, 250);
    } catch {
      setError("No pudimos usar el micrófono. Toque «Permitir» cuando el teléfono lo pregunte.");
      setEstado("listo");
    }
  }, []);

  const reiniciar = useCallback(() => { setBlob(null); setSegundos(0); setEstado("listo"); }, []);

  return { estado, blob, url, segundos, error, iniciar, detener, reiniciar };
}

function Grabadora({ rec, audioPrevio }: { rec: Rec; audioPrevio: string | null }) {
  return (
    <div className="grab card">
      {rec.estado === "grabando" ? (
        <button className="rec on" onClick={rec.detener} aria-label="Parar grabación">
          <span className="dot" /> Parar ({rec.segundos}s)
        </button>
      ) : rec.estado === "grabado" && rec.url ? (
        <>
          <p className="ok">Escuche su grabación</p>
          <audio controls src={rec.url} />
          <button className="btn" onClick={() => { rec.reiniciar(); rec.iniciar(); }}>Grabar de nuevo</button>
        </>
      ) : (
        <>
          {audioPrevio && (
            <>
              <p className="ok">Grabación guardada</p>
              <audio controls src={audioPrevio} preload="none" />
            </>
          )}
          <button className="rec" onClick={rec.iniciar} aria-label="Empezar a grabar">
            <span className="dot" /> {audioPrevio ? "Grabar de nuevo" : "Tocar para grabar"}
          </button>
        </>
      )}
      {rec.error && <p className="error">{rec.error}</p>}
    </div>
  );
}
