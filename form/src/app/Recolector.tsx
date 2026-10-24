"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FRASES, PARTES, TOTAL_OBLIGATORIAS, type Bloque } from "@/lib/frases";

type Participante = { id: string; codigo: string; sabe_escribir_quechua: boolean };
type Guardada = { numero_global: number; quechua_texto: string | null; audio_url: string | null; audio_segundos: number | null };
type Pantalla = "cargando" | "bienvenida" | "frase" | "partes" | "gracias";

const LS_PARTICIPANTE = "rimay.participante";
const LS_INDICE = "rimay.indice";
const LS_BORRADOR = "rimay.borrador";
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
    // The browser must not restore an old scroll position: every screen starts at the top.
    if ("scrollRestoration" in history) history.scrollRestoration = "manual";
    const id = lsGet(LS_PARTICIPANTE);
    if (!id) { setPantalla("bienvenida"); return; }
    fetch(`/api/participantes/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        retomar(d, lsGet(LS_INDICE));
      })
      .catch((status) => {
        if (status === 404) lsDel(LS_PARTICIPANTE);
        setPantalla("bienvenida");
      });
  }, []);

  useEffect(() => { if (part) lsSet(LS_INDICE, String(indice)); }, [indice, part]);

  // Progress lives on the server and this browser remembers who they are, so opening the
  // link again lands exactly where they left off. Nothing to remember, no code to type.
  function retomar(d: Participante & { respuestas: Guardada[] }, indiceLocal: string | null) {
    const mapa = new Map(d.respuestas.map((g) => [g.numero_global, g]));
    setPart({ id: d.id, codigo: d.codigo, sabe_escribir_quechua: d.sabe_escribir_quechua });
    setGuardadas(mapa);
    const local = Number(indiceLocal);
    const pendiente = FRASES.findIndex((f) => f.bloque !== "E" && !mapa.has(f.global));
    const i = indiceLocal !== null && Number.isFinite(local) && local >= 0 && local < FRASES.length
      ? local
      : pendiente === -1 ? ULTIMA_OBLIGATORIA : pendiente;
    setIndice(i);
    setPantalla(pendiente === -1 && indiceLocal === null ? "gracias" : "frase");
  }

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
        <p className="muted">Todo lo que grabó quedó guardado. Si vuelve a abrir este enlace, sigue donde se quedó.</p>
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
      onGuardada={(g, avanzar = true) => {
        setGuardadas((m) => new Map(m).set(g.numero_global, g));
        if (avanzar) siguiente();
      }}
      onSaltar={siguiente}
      onAnterior={() => indice > 0 && irA(indice - 1)}
      onPartes={() => setPantalla("partes")}
    />
  );
}

function Bienvenida({ onListo }: { onListo: (p: Participante) => void }) {
  const [consent, setConsent] = useState(false);
  const [nombre, setNombre] = useState("");
  const [sexo, setSexo] = useState("");
  const [edad, setEdad] = useState("");
  const [lugar, setLugar] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  async function empezar() {
    setError("");
    if (!consent) { setError("Marque la casilla para aceptar."); return; }
    setEnviando(true);
    let r: Response;
    try {
      r = await fetch("/api/participantes", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ consentimiento: true, nombre, sexo, edad, lugar }),
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
  const hechasTotal = FRASES.filter((x) => x.bloque !== "E" && guardadas.has(x.global)).length;
  const total = f.bloque === "E" ? FRASES.filter((x) => x.bloque === "E").length : TOTAL_OBLIGATORIAS;
  const hechas = f.bloque === "E" ? FRASES.filter((x) => x.bloque === "E" && guardadas.has(x.global)).length : hechasTotal;
  return (
    <div className="prog">
      <div className="prog-label small">
        <span>Parte {parte.parte} · {parte.titulo}</span><span>{hechas}/{total}</span>
      </div>
      <div className="bar thin"><div style={{ width: `${(100 * hechas) / total}%` }} /></div>
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
  onGuardada: (g: Guardada, avanzar?: boolean) => void; onSaltar: () => void; onAnterior: () => void; onPartes: () => void;
}) {
  const f = FRASES[indice];
  const esExtra = f.bloque === ("E" as Bloque);
  const claveBorrador = `${LS_BORRADOR}.${part.id}.${f.global}`;
  // What they typed survives closing the browser before saving.
  const [texto, setTexto] = useState(
    esExtra ? "" : lsGet(claveBorrador) ?? guardada?.quechua_texto ?? "",
  );
  const rec = useGrabadora();
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (esExtra) return;
    if (texto && texto !== (guardada?.quechua_texto ?? "")) lsSet(claveBorrador, texto);
    else lsDel(claveBorrador);
  }, [texto, esExtra, claveBorrador, guardada]);

  useEffect(() => { window.scrollTo(0, 0); }, []);

  const tieneAudioPrevio = !!guardada?.audio_url && !rec.blob;
  const textoNuevo = !esExtra && texto.trim() !== (guardada?.quechua_texto ?? "").trim() && !!texto.trim();
  const hayPendiente = !!rec.blob || textoNuevo;
  const puedeGuardar = !enviando && rec.estado !== "grabando" &&
    (esExtra ? !!rec.blob || tieneAudioPrevio : !!texto.trim() || !!rec.blob || tieneAudioPrevio);

  async function enviar(): Promise<Guardada | null> {
    setError("");
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
      let r: Response;
      try {
        r = await fetch("/api/respuestas", { method: "POST", body: fd });
      } catch {
        setError("No se pudo guardar. Revise su internet e intente de nuevo.");
        return null;
      }
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        setError(d.error && r.status < 500 ? d.error : "No se pudo guardar por un problema nuestro. Intente de nuevo.");
        return null;
      }
      const g = (await r.json()) as Guardada;
      lsDel(claveBorrador);
      return g;
    } finally {
      setEnviando(false);
    }
  }

  async function guardar() {
    if (esExtra && !rec.blob && !tieneAudioPrevio) { setError("Grabe la frase antes de guardar."); return; }
    if (!esExtra && !texto.trim() && !rec.blob && !tieneAudioPrevio) { setError("Escriba la frase o grábela."); return; }
    const g = await enviar();
    if (g) onGuardada(g);
  }

  // Leaving a phrase never throws away what they did: anything unsaved is saved first.
  async function salir(ir: () => void) {
    if (rec.estado === "grabando") rec.detener();
    if (hayPendiente) {
      const g = await enviar();
      if (!g) return;
      onGuardada(g, false);
    }
    ir();
  }

  return (
    <main className="wrap frase-pantalla">
      <header className="cabecera">
        <div className="top">
          <button className="link" onClick={() => salir(onPartes)} disabled={enviando}>☰ Partes</button>
          <span className="muted small">Se guarda solo</span>
        </div>
        <Progreso indice={indice} guardadas={guardadas} />
      </header>

      <div className="frase">
        <p className="es"><span className="num">{f.global}.</span> {f.castellano}</p>
        {esExtra && <p className="qu-given">{f.chanka}</p>}
        {guardada && <p className="ok">✓ Guardada. Puede cambiarla.</p>}
      </div>

      {esExtra ? (
        <p className="paso">Grábese leyendo en voz alta el texto en quechua</p>
      ) : (
        <>
          <label className="field">
            <span>1 · Escríbalo en quechua</span>
            <textarea
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              rows={2}
              autoCapitalize="sentences"
              autoCorrect="off"
              spellCheck={false}
              enterKeyHint="done"
              placeholder="Si no sabe escribirla, solo grábela"
            />
          </label>
          <p className="paso">
            2 · {texto.trim()
              ? "Grábese leyendo exactamente lo que escribió"
              : "Grábese diciendo la frase en quechua"}
          </p>
        </>
      )}

      <Grabadora rec={rec} audioPrevio={tieneAudioPrevio ? guardada!.audio_url! : null} />

      <div className="acciones">
        {error && <p className="error">{error}</p>}
        <div className="barra">
          <button className="btn chico" onClick={() => salir(onAnterior)} disabled={indice === 0 || enviando} aria-label="Frase anterior">←</button>
          <button className="btn primary" disabled={!puedeGuardar} onClick={guardar}>
            {enviando ? "Guardando…" : "Guardar y seguir"}
          </button>
          <button className="btn chico" onClick={() => salir(onSaltar)} disabled={enviando}>Saltar</button>
        </div>
      </div>
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

