// La consulta: una sola pantalla que cambia de estado (tablero de Pencil + design/specs/02-pulido-ui.md).
import {
  setAudioModeAsync, useAudioPlayer, useAudioPlayerStatus, useAudioRecorder,
  useAudioRecorderState, requestRecordingPermissionsAsync,
} from 'expo-audio';
import { File, Paths } from 'expo-file-system';
import * as Haptics from 'expo-haptics';
import * as Speech from 'expo-speech';
import { Redirect, router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { audioDeFrase, escuchar, FalloServicio, idioma, salud, SinServidor, turnoEnfermera, turnoPaciente, voz } from '@/chaski/api';
import { Chaski, usarChaskiLibre, type EstadoChaski } from '@/chaski/chaski';
import { agregarTurno, inicioDeConsulta } from '@/chaski/consulta';
import {
  AVISO_LENTO_MS, AVISO_MUY_LENTO_MS, esEnsayo, esResultado, explicarBloqueo, fueCastellano, ladoDetectado, leerInterprete, pacienteDesdeResultado,
  pasoPorTiempo, siguienteLado, veredictoEnfermera,
  type Interprete, type Lado, type RespuestaPaciente, type Veredicto,
} from '@/chaski/modelo';
import { usePerfil, type Perfil } from '@/chaski/perfil';
import { idiomaDelOtro, quienHabla, textos, type Textos } from '@/chaski/textos';
import { C, ESCALA } from '@/chaski/tokens';
import { AnilloInti } from '@/chaski/inti';
import { BotonEscalonado, Cruz, MarcaChaski, Zigzag } from '@/chaski/motivos';
import { nivelDesdeDb } from '@/chaski/movimiento';
import { Aviso, Boton, Etiqueta, Icono, Tarjeta } from '@/chaski/ui';
import { base64ABytes, bocaAbierta, envolvente, nivelEn, revisarGrabacion, type Envolvente } from '@/chaski/wav';
import Animated, {
  FadeInDown, useAnimatedStyle, useReducedMotion, useSharedValue, withSequence, withTiming, ZoomIn,
} from 'react-native-reanimated';

import { GRABACION } from '@/chaski/grabacion';
import { esperaParaEscuchar } from '@/chaski/conversacion';
import { nuevoVad, pasoVad } from '@/chaski/vad';
import { FRASE_NEGATIVA_DEMO, useEnsayo } from '@/chaski/ensayo';


type Fase =
  | { f: 'listo' }
  | { f: 'grabando' }
  | { f: 'pensando'; lado: Lado; paso: number; oido?: string; desde?: number; pulido?: string }
  | { f: 'dicho'; v: Extract<Veredicto, { tipo: 'dicho' | 'dicho_con_aviso' }>; vozLista: boolean; ensayo?: boolean }
  | { f: 'bloqueado'; v: Extract<Veredicto, { tipo: 'bloqueado' }>; ensayo?: 'servicio' | 'sin_conexion' }
  | { f: 'paciente'; r: RespuestaPaciente }
  | { f: 'error'; mensaje: string; sinServidor: boolean; detalle?: string; prueba?: 'probando' | 'responde' | 'no_responde' }
  // Intérprete agente (D32): las acciones que no son «traducir».
  | { f: 'pregunta'; d: Extract<Interprete, { tipo: 'pregunta' }>; lado: Lado }
  | { f: 'respuesta'; d: Extract<Interprete, { tipo: 'respuesta' }> }
  | { f: 'noentendi'; d: Extract<Interprete, { tipo: 'no_entendi' }>; lado: Lado }
  | { f: 'frase'; d: Extract<Interprete, { tipo: 'frase' }> };

// Modo demo: chaski:///?demo=<estado>&idioma=quechua&rol=paciente muestra un estado con datos de ejemplo,
// sin servicio. Sirve para revisar pantallas y como respaldo de la demo si falla el wifi.
const DEMO_CASTELLANO = 'Tome una pastilla dos veces al día, en la mañana y en la noche, durante siete días.';
const DEMO: Record<string, Fase> = {
  listo: { f: 'listo' },
  grabando: { f: 'grabando' },
  pensando: { f: 'pensando', lado: 'castellano', paso: 2, oido: DEMO_CASTELLANO },
  dicho: {
    f: 'dicho', vozLista: true,
    v: veredictoEnfermera(DEMO_CASTELLANO, {
      quechua: '[Indicación en quechua chanka]', retraduccion: '', aprobado_por_auditoria: true, motivo: null,
      terminos_inseguros: [], diferencias: [], se_dice: true, aviso: null, total_ms: 0,
    }) as Extract<Veredicto, { tipo: 'dicho' }>,
  },
  aviso: {
    f: 'dicho', vozLista: true,
    v: veredictoEnfermera('Si hay sangrado, venga a la posta.', {
      quechua: '[Indicación en quechua chanka]', retraduccion: '', aprobado_por_auditoria: false, motivo: null,
      terminos_inseguros: ['posta'], diferencias: [], se_dice: true, aviso: null, total_ms: 0,
    }) as Extract<Veredicto, { tipo: 'dicho_con_aviso' }>,
  },
  // Contrato final (Resultado): bloqueo en palabras simples, ámbar con su aviso, insignia del crítico.
  negativa: {
    f: 'bloqueado', ensayo: 'servicio',
    v: veredictoEnfermera(FRASE_NEGATIVA_DEMO.es, {
      estado: 'bloqueado', accion: 'traducir', motivo: 'cambió un dato crítico: prohibiciones', para: 'paciente',
      idioma_salida: 'quy', paso_fallido: 'guardas', modelos: { principal: 'claude-opus-5', critico: null },
    }) as Extract<Veredicto, { tipo: 'bloqueado' }>,
  },
  critico: {
    f: 'dicho', vozLista: true,
    v: veredictoEnfermera(DEMO_CASTELLANO, {
      estado: 'dicho', accion: 'traducir', motivo: '', para: 'paciente', idioma_salida: 'quy',
      texto_salida: '[Indicación en quechua chanka]', modelos: { principal: 'claude-opus-5', critico: 'claude-haiku-4-5' },
    }) as Extract<Veredicto, { tipo: 'dicho' }>,
  },
  aviso2: {
    f: 'dicho', vozLista: true,
    v: veredictoEnfermera('Si hay sangrado, venga a la posta.', {
      estado: 'dicho_con_aviso', accion: 'traducir', motivo: '', para: 'paciente', idioma_salida: 'quy',
      texto_salida: '[Indicación en quechua chanka]', aviso: '«posta» se dijo como préstamo del castellano',
      modelos: { principal: 'claude-opus-5', critico: 'claude-haiku-4-5' },
    }) as Extract<Veredicto, { tipo: 'dicho_con_aviso' }>,
  },
  lento: { f: 'pensando', lado: 'castellano', paso: 2, oido: DEMO_CASTELLANO, desde: -7000 },
  bloqueado: {
    f: 'bloqueado',
    v: veredictoEnfermera('Tome una pastilla cada 8 horas, nunca dos juntas.', {
      quechua: '', retraduccion: '', aprobado_por_auditoria: false, motivo: null, terminos_inseguros: [],
      diferencias: [{ campo: 'paracetamol.cantidad', original: '1.0', retraducido: '2.0' }],
      se_dice: false, aviso: null, total_ms: 0,
    }) as Extract<Veredicto, { tipo: 'bloqueado' }>,
  },
  paciente: {
    f: 'paciente',
    r: {
      idioma: { codigo: 'quy', confianza: 0.97 }, chanka_oido: '[Respuesta del paciente en quechua]',
      castellano: '¿Y si me olvido la pastilla de la noche?', literal: '', dudas: [], seguro: false, total_ms: 0,
    },
  },
  error: { f: 'error', mensaje: 'Sin conexión', sinServidor: false, detalle: '/turno/enfermera · 502' },
  pregunta: {
    f: 'pregunta', lado: 'quechua',
    d: leerInterprete({ accion: 'repreguntar', para: 'paciente', texto_pulido: '¿Desde cuándo le duele la barriga?',
      motivo: 'Dijo que le duele, pero no desde cuándo', dato_faltante: 'desde cuándo' },
    ) as Extract<Interprete, { tipo: 'pregunta' }>,
  },
  respuesta: {
    f: 'respuesta',
    d: leerInterprete({ accion: 'responder', texto_pulido: 'Dijo «wiksa», que es barriga. No mencionó fiebre.',
      motivo: 'La enfermera le preguntó a Chaski, no al paciente' }) as Extract<Interprete, { tipo: 'respuesta' }>,
  },
  no_entendi: {
    f: 'noentendi', lado: 'quechua',
    d: leerInterprete({ accion: 'no_entendi', motivo: 'Se oyó un número con poca seguridad' }) as Extract<Interprete, { tipo: 'no_entendi' }>,
  },
  frase: {
    f: 'frase',
    d: { tipo: 'frase', frase: { id: 'emerg-donde-duele', es: '¿Dónde le duele?', quy: '[quechua revisado del banco]', audio: 'demo', tags: ['emergencia'] } },
  },
};

class GrabacionInvalida extends Error {}

export default function Pantalla() {
  const perfil = usePerfil();
  const q = useLocalSearchParams<{ demo?: string; idioma?: string; rol?: string; lado?: string; marco?: string }>();
  // D40: Chaski sin fondo es lo normal; `&marco=1` muestra el marco anterior para comparar.
  usarChaskiLibre(q.marco !== '1');
  if (q.demo && DEMO[q.demo]) {
    const demo: Perfil = {
      idioma: q.idioma === 'quechua' ? 'quechua' : 'castellano',
      rol: q.rol === 'paciente' ? 'paciente' : 'personal',
      nombre: 'Rosa',
    };
    return <Consulta key={q.demo + (q.idioma ?? '') + (q.rol ?? '')} perfil={demo} inicial={DEMO[q.demo]} />;
  }
  if (perfil === undefined) return <View style={e.pantalla} />;
  if (perfil === null) return <Redirect href="/bienvenida" />;
  // Desde el modo emergencia se vuelve con el turno del paciente listo para escuchar su respuesta.
  const ladoInicial = q.lado === 'quechua' || q.lado === 'castellano' ? q.lado : undefined;
  return <Consulta key={ladoInicial ?? 'consulta'} perfil={perfil} ladoInicial={ladoInicial} />;
}

function Consulta({ perfil, inicial, ladoInicial }: { perfil: Perfil; inicial?: Fase; ladoInicial?: Lado }) {
  const t = textos(perfil.idioma);
  const [fase, setFase] = useState<Fase>(inicial ?? { f: 'listo' });
  const [lado, setLado] = useState<Lado>(ladoInicial ?? perfil.idioma);
  const [env, setEnv] = useState<Envolvente | null>(null);
  const ultimoAudio = useRef<string | null>(null);
  const ensayo = useEnsayo();

  // Modo conversación (como el modo voz de ChatGPT): un toque y Chaski escucha, piensa, habla y vuelve a escuchar
  // solo. El micrófono solo se abre en «grabando»; mientras piensa o suena audio queda cerrado.
  const [conversa, setConversaEstado] = useState(false);
  const conversaRef = useRef(false);
  const setConversa = (v: boolean) => { conversaRef.current = v; setConversaEstado(v); };
  const [ocupado, setOcupadoEstado] = useState(false);
  const ocupadoRef = useRef(false);
  const setOcupado = (v: boolean) => { ocupadoRef.current = v; setOcupadoEstado(v); };
  const [hablandoSistema, setHablandoSistemaEstado] = useState(false);
  const hablandoSistemaRef = useRef(false);
  const setHablandoSistema = (v: boolean) => { hablandoSistemaRef.current = v; setHablandoSistemaEstado(v); };
  const vadRef = useRef(nuevoVad(0));

  const grabadora = useAudioRecorder(GRABACION);
  const estadoGrabadora = useAudioRecorderState(grabadora, 80);
  const reproductor = useAudioPlayer(null, { updateInterval: 50 });
  const estadoReproductor = useAudioPlayerStatus(reproductor);

  useEffect(() => {
    (async () => {
      await requestRecordingPermissionsAsync();
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
    })();
  }, []);

  // En modo demo no hay micrófono ni audio: un reloj falso mueve el nivel y la voz para que se vea el movimiento.
  const esDemo = !!inicial;
  const reloj = useRelojDemo(esDemo && (fase.f === 'grabando' || fase.f === 'dicho'));
  const hablandoDemo = esDemo && fase.f === 'dicho';
  const hablando = estadoReproductor.playing || hablandoDemo;
  const nivelVoz = esDemo && fase.f === 'grabando'
    ? 0.45 + 0.45 * Math.sin(reloj * 5) * Math.sin(reloj * 1.3)
    : nivelDesdeDb(estadoGrabadora.metering);
  const pulso = !hablando ? undefined
    : hablandoDemo ? Math.abs(Math.sin(reloj * 9)) * (0.55 + 0.45 * Math.sin(reloj * 2))
      : nivelEn(env, estadoReproductor.currentTime);
  const progresoVoz = hablandoDemo ? (reloj % 4) / 4
    : estadoReproductor.duration > 0 ? estadoReproductor.currentTime / estadoReproductor.duration : 0;
  const boca = hablando && (hablandoDemo ? (pulso ?? 0) > 0.25 : bocaAbierta(env, estadoReproductor.currentTime));

  // ---- grabar -----------------------------------------------------------------------------
  async function empezar(auto = false) {
    reproductor.pause();
    if (!auto) await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    await grabadora.prepareToRecordAsync();
    grabadora.record();
    vadRef.current = nuevoVad(Date.now());
    setFase({ f: 'grabando' });
  }

  /** El toque en el micrófono desde «listo»: prende el modo conversación. */
  function conversar() {
    setConversa(true);
    empezar();
  }

  /** Apaga el modo conversación: corta lo que suene, descarta lo que se esté grabando y deja los botones de siempre. */
  async function pausar() {
    setConversa(false);
    reproductor.pause();
    Speech.stop();
    setHablandoSistema(false);
    if (fase.f === 'grabando') {
      try { await grabadora.stop(); } catch {}
      setFase({ f: 'listo' });
    }
  }

  /** Tocar mientras Chaski habla: lo corta y, en conversación, vuelve a escuchar. */
  function cortar() {
    reproductor.pause();
    Speech.stop();
    setHablandoSistema(false);
  }

  // Al salir de la pantalla (receta, emergencia, resumen) la conversación se pausa: nadie graba en segundo plano.
  useFocusEffect(useCallback(() => () => { if (conversaRef.current) pausar(); }, []));

  // La detección de voz: cada lectura del nivel avanza el detector; al callarse quien habla, se manda el turno.
  useEffect(() => {
    if (!conversa || esDemo || fase.f !== 'grabando' || ocupadoRef.current) return;
    const [s, ev] = pasoVad(vadRef.current, estadoGrabadora.metering, Date.now());
    vadRef.current = s;
    if (ev === 'fin') terminar();
    else if (ev === 'reiniciar') {
      // Nadie habló en un buen rato: grabación nueva (archivo chico) y piso de ruido recalibrado.
      (async () => { try { await grabadora.stop(); } catch {} if (conversaRef.current) empezar(true); })();
    }
  }, [estadoGrabadora.metering, estadoGrabadora.durationMillis]);

  // Vuelve a escuchar solo cuando terminó el turno y calló el audio, con un respiro para no oírse a sí mismo.
  const sonando = hablando || hablandoSistema;
  useEffect(() => {
    if (!conversa || esDemo || ocupado) return;
    const ms = esperaParaEscuchar({
      f: fase.f,
      vozLista: fase.f === 'dicho' ? fase.vozLista : undefined,
      ensayo: (fase.f === 'dicho' || fase.f === 'bloqueado') && !!fase.ensayo,
      deGrabacion: fase.f === 'error' && (fase.detalle ?? '').startsWith('grabación'),
    }, sonando);
    if (ms === null) return;
    const id = setTimeout(() => {
      if (!conversaRef.current || ocupadoRef.current || reproductor.playing || hablandoSistemaRef.current) return;
      if (fase.f === 'bloqueado') setLado('castellano'); // tras un bloqueo, el personal lo dice de otra forma
      empezar(true);
    }, ms);
    return () => clearTimeout(id);
  }, [conversa, ocupado, fase, sonando]);

  async function terminar() {
    setOcupado(true);
    try {
      await procesarGrabacion();
    } finally {
      setOcupado(false);
    }
  }

  async function procesarGrabacion() {
    await grabadora.stop();
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const uri = grabadora.uri;
    if (!uri) return fallar(new GrabacionInvalida('sin archivo'));
    try {
      const revision = revisarGrabacion(await new File(uri).bytes());
      // En conversación, un ruido que no era voz no merece una pantalla de error: se vuelve a escuchar.
      if (!revision.ok && conversaRef.current) return empezar(true);
      if (!revision.ok) return fallar(new GrabacionInvalida(revision.motivo));
    } catch (e) {
      return fallar(new GrabacionInvalida(`no se pudo leer (${String((e as Error)?.message ?? e).slice(0, 40)})`));
    }
    ultimoAudio.current = uri;
    // D11: el detector decide quién habló; si falla o duda, manda la alternancia.
    let quien = lado;
    try {
      quien = ladoDetectado(await idioma(uri), lado);
    } catch {}
    if (quien !== lado) setLado(quien);
    if (quien === 'castellano') return turnoDeLaEnfermera(uri);
    return turnoDelPaciente(uri);
  }

  // ---- turnos -----------------------------------------------------------------------------
  async function turnoDeLaEnfermera(uri: string) {
    try {
      const desde = Date.now();
      setFase({ f: 'pensando', lado: 'castellano', paso: 0, desde });
      const { texto } = await escuchar(uri);
      if (!texto.trim()) throw new Error('No le escuché bien');
      setFase({ f: 'pensando', lado: 'castellano', paso: 1, oido: texto, desde });
      await decirTexto(texto);
    } catch (e) {
      fallar(e);
    }
  }

  /**
   * El turno del personal con un texto ya oído. `sembrada` es solo para el ensayo de la negativa: reemplaza la
   * traducción para mostrar que la barrera la atrapa, y la pantalla lo dice en claro.
   */
  async function decirTexto(texto: string, sembrada?: string) {
    const r = await turnoEnfermera(texto, perfil.rol, {
      traduccionSembrada: sembrada,
      // A los ~3 s llega la decisión del intérprete: se muestra cómo lo va a decir, mientras traduce y revisa.
      // Solo se muestra; lo único que se dice en voz alta es el resultado auditado.
      alDecidir: (d) => setFase((p) => (p.f === 'pensando'
        ? { ...p, paso: Math.max(p.paso, 2), pulido: d.texto_pulido?.trim() || undefined } : p)),
    });
    // El letrero de ensayo sale si la app lo pidió o si el servicio dice que la traducción fue sembrada.
    const ensayoReal = !!sembrada || esEnsayo(r);
    const ia = leerInterprete(r);
    if (ia.tipo !== 'traducir' && !ensayoReal) return interpretar(ia, 'castellano', texto, r.quechua);
    const v = veredictoEnfermera(texto, r);
    agregarTurno({ lado: 'castellano', castellano: texto, quechua: r.quechua ?? r.texto_salida ?? '', estado: v.tipo });
    if (v.tipo === 'bloqueado') {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      setFase({ f: 'bloqueado', v, ensayo: ensayoReal ? 'servicio' : undefined });
      return;
    }
    setFase({ f: 'dicho', v, vozLista: false, ensayo: ensayoReal });
    if (ensayoReal) return; // un ensayo nunca se le dice al paciente
    setLado(siguienteLado('castellano'));
    await decir(v.quechua);
    setFase((p) => (p.f === 'dicho' ? { ...p, vozLista: true } : p));
  }

  /** Ensayo de la negativa (D37): manda la frase fija al servicio REAL con la traducción errada sembrada. */
  async function ensayarNegativa() {
    const desde = Date.now();
    setFase({ f: 'pensando', lado: 'castellano', paso: 1, oido: FRASE_NEGATIVA_DEMO.es, desde });
    try {
      await decirTexto(FRASE_NEGATIVA_DEMO.es, FRASE_NEGATIVA_DEMO.quySembrado);
    } catch {
      // Sin servicio: el mismo resultado de ejemplo, con un letrero que dice que es de ejemplo.
      setFase({
        f: 'bloqueado', ensayo: 'sin_conexion',
        v: { tipo: 'bloqueado', castellano: FRASE_NEGATIVA_DEMO.es, diferencias: [], terminos: [], casillasOk: [],
          razon: explicarBloqueo('guardas', 'cambió un dato crítico: prohibiciones', FRASE_NEGATIVA_DEMO.es) },
      });
    }
  }

  async function turnoDelPaciente(uri: string) {
    try {
      setFase({ f: 'pensando', lado: 'quechua', paso: 0, desde: Date.now() });
      const crudo = await turnoPaciente(uri, perfil.rol);
      // Contrato final: bloqueado no se le muestra al personal como si fuera lo que dijo el paciente.
      if (esResultado(crudo) && crudo.estado === 'bloqueado') {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        setFase({ f: 'bloqueado', v: veredictoEnfermera('', crudo) as Extract<Veredicto, { tipo: 'bloqueado' }> });
        setLado('quechua');
        return;
      }
      const r = esResultado(crudo) ? pacienteDesdeResultado(crudo) : crudo;
      if (fueCastellano(r)) {
        // Detección automática (D11): el turno se habló en castellano aunque tocaba quechua.
        setLado('castellano');
        return turnoDeLaEnfermera(uri);
      }
      const ia = leerInterprete(r);
      if (ia.tipo !== 'traducir') return interpretar(ia, 'quechua', r.castellano, r.chanka_oido);
      agregarTurno({
        lado: 'quechua', castellano: r.castellano, quechua: r.chanka_oido,
        estado: r.seguro ? 'entendido' : 'con_dudas',
      });
      setFase({ f: 'paciente', r });
      setLado('castellano');
      // En conversación Chaski le DICE al personal lo que entendió (con la voz del servicio si vino).
      if (conversaRef.current && r.castellano) {
        const b64 = esResultado(crudo) && crudo.idioma_salida === 'spa' ? crudo.audio_wav_b64 : null;
        if (b64) { try { return await reproducirB64(b64); } catch {} }
        decirEnCastellano(r.castellano);
      }
    } catch (e) {
      fallar(e);
    }
  }

  /** Las acciones del intérprete que no son traducir (D32). El código decide qué se dice y a quién. */
  async function interpretar(ia: Interprete, hablo: Lado, castellano: string, quechua: string) {
    if (ia.tipo === 'traducir') return;
    if (ia.tipo === 'no_entendi') {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
      setLado(hablo);
      setFase({ f: 'noentendi', d: ia, lado: hablo });
      // La voz del servicio primero (la misma del resto); /voz solo si no vino audio o falló.
      if (ia.audioB64) { try { return await reproducirB64(ia.audioB64); } catch {} }
      if (ia.quechua) { try { await decir(ia.quechua); } catch {} }
      return;
    }
    if (ia.tipo === 'pregunta') {
      // Repregunta: vuelve al MISMO hablante, una sola vez (C4 lo impone el servicio).
      agregarTurno({ lado: hablo, castellano: ia.texto || castellano, quechua: ia.quechua ?? quechua, estado: 'dicho' });
      setLado(hablo);
      setFase({ f: 'pregunta', d: ia, lado: hablo });
      // La voz del servicio; si no vino o no se pudo reproducir, el respaldo de abajo.
      if (ia.audioB64) { try { return await reproducirB64(ia.audioB64); } catch {} }
      if (ia.para === 'paciente' && ia.quechua) return decir(ia.quechua);
      return decirEnCastellano(ia.texto);
    }
    if (ia.tipo === 'respuesta') {
      // Chaski le responde al personal: no se traduce al otro lado.
      setLado('castellano');
      setFase({ f: 'respuesta', d: ia });
      if (ia.audioB64) return reproducirB64(ia.audioB64);
      return decirEnCastellano(ia.texto);
    }
    // Frase verificada del banco: suena el audio revisado, sin generar nada.
    agregarTurno({ lado: hablo, castellano: ia.frase.es, quechua: ia.frase.quy, estado: 'dicho' });
    setLado('quechua');
    setFase({ f: 'frase', d: ia });
    try {
      reproductor.replace(await audioDeFrase(ia.frase));
      reproductor.play();
    } catch {}
  }

  async function reproducirB64(b64: string) {
    const bytes = base64ABytes(b64);
    const archivo = new File(Paths.cache, `chaski-${Date.now()}.wav`);
    archivo.create();
    await archivo.write(bytes);
    setEnv(envolvente(bytes));
    reproductor.replace({ uri: archivo.uri });
    reproductor.play();
  }

  function decirEnCastellano(texto: string) {
    // Sin audio del servicio (Cartesia), la voz del sistema en castellano. Se sigue cuándo suena para no
    // abrir el micrófono encima (modo conversación).
    if (!texto) return;
    setHablandoSistema(true);
    const fin = () => setHablandoSistema(false);
    Speech.speak(texto, { language: 'es-US', rate: 0.95, onDone: fin, onStopped: fin, onError: fin });
  }

  async function decir(quechua: string) {
    const { uri, bytes } = await voz(quechua);
    setEnv(envolvente(bytes));
    reproductor.replace({ uri });
    reproductor.play();
  }

  function repetirAudio() {
    reproductor.seekTo(0);
    reproductor.play();
  }

  function fallar(e: unknown) {
    if (e instanceof GrabacionInvalida) {
      // No es la red: el teléfono no grabó voz. Se dice así, con el motivo en la línea gris.
      setFase({ f: 'error', sinServidor: false, mensaje: t.sinGrabacion, detalle: `grabación · ${e.message}` });
      return;
    }
    const sinServidor = e instanceof SinServidor;
    setFase({
      f: 'error',
      sinServidor,
      mensaje: sinServidor
        ? t.sinServidor
        : String((e as Error)?.message ?? '').includes('escuché')
          ? t.noEscuche
          : t.sinConexion,
      // La única línea técnica, en gris: ruta y estado, para distinguir un reinicio del servicio de la red del teléfono.
      detalle: e instanceof FalloServicio ? t.detalleError(e.ruta, e.tipo) : undefined,
    });
  }

  async function probarConexion() {
    setFase((p) => (p.f === 'error' ? { ...p, prueba: 'probando' } : p));
    let ok = false;
    try {
      await salud();
      ok = true;
    } catch {}
    setFase((p) => (p.f === 'error' ? { ...p, prueba: ok ? 'responde' : 'no_responde' } : p));
  }

  async function reintentar() {
    const uri = ultimoAudio.current;
    if (!uri) return setFase({ f: 'listo' });
    setOcupado(true);
    try {
      await (lado === 'castellano' ? turnoDeLaEnfermera(uri) : turnoDelPaciente(uri));
    } finally {
      setOcupado(false);
    }
  }

  // ---- qué se ve ----------------------------------------------------------------------------
  const estadoChaski: EstadoChaski =
    fase.f === 'grabando' ? 'escuchando'
      : fase.f === 'pensando' ? 'pensando'
        : fase.f === 'bloqueado' || fase.f === 'error' || fase.f === 'noentendi' ? 'no_entendi'
        : fase.f === 'pregunta' || fase.f === 'respuesta' || fase.f === 'frase' ? (hablando ? 'hablando' : 'reposo')
          : fase.f === 'dicho' ? 'hablando'
            : fase.f === 'paciente' ? 'escuchando'
              : 'reposo';
  const protagonista = fase.f === 'listo' || fase.f === 'dicho' || fase.f === 'bloqueado' || fase.f === 'error' || fase.f === 'pensando'
    || fase.f === 'pregunta' || fase.f === 'respuesta' || fase.f === 'noentendi' || fase.f === 'frase';

  return (
    <SafeAreaView style={e.pantalla} edges={['top', 'bottom']}>
      <Encabezado t={t} />
      <ScrollView contentContainerStyle={e.cuerpo} bounces={false}>
        {protagonista ? (
          <View style={e.centro}>
            <Chaski estado={estadoChaski} tam={fase.f === 'listo' ? 240 : fase.f === 'dicho' ? 200 : 150} boca={boca} pulso={fase.f === 'dicho' || fase.f === 'pregunta' || fase.f === 'respuesta' || fase.f === 'frase' ? pulso : undefined} />
          </View>
        ) : (
          <View style={e.filaChica}>
            <Chaski estado={estadoChaski} tam={112} />
            <View style={{ gap: 6, flex: 1 }}>
              <Etiqueta idioma={fase.f === 'paciente' ? 'quechua' : lado} />
              <Text style={e.secundario}>
                {fase.f === 'grabando' ? t.escuchando : ''}
              </Text>
            </View>
          </View>
        )}

        {fase.f === 'listo' && (
          <View style={e.centroTexto}>
            <Text style={e.titulo}>{t.listo}</Text>
          </View>
        )}

        {fase.f === 'grabando' && <Medidor nivel={nivelVoz} tinte={lado} t={t} />}

        {fase.f === 'pensando' && <Pensando fase={fase} t={t} />}
        {fase.f === 'bloqueado' && fase.ensayo && <LetreroEnsayo sinConexion={fase.ensayo === 'sin_conexion'} t={t} />}
        {fase.f === 'dicho' && fase.ensayo && <LetreroEnsayo noBloqueo t={t} />}

        {fase.f === 'dicho' && <Dicho v={fase.v} vozLista={fase.vozLista || hablandoDemo} hablando={hablando} progreso={progresoVoz} t={t} />}

        {fase.f === 'bloqueado' && <Bloqueado v={fase.v} t={t} />}

        {fase.f === 'paciente' && <Paciente r={fase.r} t={t} />}

        {fase.f === 'pregunta' && <TarjetaPregunta d={fase.d} t={t} />}
        {fase.f === 'respuesta' && <TarjetaRespuesta d={fase.d} t={t} />}
        {fase.f === 'noentendi' && <TarjetaNoEntendi d={fase.d} t={t} />}
        {fase.f === 'frase' && <TarjetaFrase d={fase.d} t={t} />}

        {fase.f === 'error' && (
          <View style={e.centroTexto}>
            <Text style={e.titulo}>{fase.mensaje}</Text>
            {fase.detalle ? <Text style={e.detalleError}>{fase.detalle}</Text> : null}
            {fase.prueba === 'responde' && <Aviso tipo="ok" texto={t.servicioResponde} />}
            {fase.prueba === 'no_responde' && <Aviso tipo="warn" texto={t.servicioNoResponde} />}
          </View>
        )}
      </ScrollView>

      <View style={e.pie}>
        {fase.f === 'dicho' && (
          <View style={e.filaBotones}>
            <Boton tipo="secundario" icono="speaker.wave.2.fill" texto={t.repetirAudio} onPress={repetirAudio} deshabilitado={!fase.vozLista} flex />
            <Boton icono="mic.fill" texto={t.seguirConsulta} onPress={() => setFase({ f: 'listo' })} flex />
          </View>
        )}
        {fase.f === 'bloqueado' && (
          <View style={{ gap: 8 }}>
            <Boton alto={56} texto={t.decirloOtraForma} icono="mic.fill" onPress={() => { setLado('castellano'); empezar(); }} />
            <Boton tipo="texto" texto={t.loExplicoYo} onPress={() => { setLado('castellano'); setFase({ f: 'listo' }); }} />
          </View>
        )}
        {fase.f === 'paciente' && (
          <View style={e.filaBotones}>
            <Boton icono="mic.fill" texto={t.responder} onPress={() => { setLado('castellano'); empezar(); }} flex />
            <Boton tipo="secundario" texto={t.pedirQueRepita} onPress={() => { setLado('quechua'); setFase({ f: 'listo' }); }} flex />
          </View>
        )}
        {(fase.f === 'pregunta' || fase.f === 'frase') && (
          <View style={e.filaBotones}>
            <Boton tipo="secundario" icono="speaker.wave.2.fill" texto={t.repetirAudio} onPress={repetirAudio} flex />
            <Boton icono="mic.fill" texto={t.responder} onPress={() => { setLado(fase.f === 'pregunta' ? fase.lado : 'quechua'); empezar(); }} flex />
          </View>
        )}
        {fase.f === 'respuesta' && (
          <View style={e.filaBotones}>
            <Boton tipo="secundario" icono="speaker.wave.2.fill" texto={t.repetirAudio} onPress={() => decirEnCastellano(fase.d.texto)} flex />
            <Boton icono="mic.fill" texto={t.seguirConsulta} onPress={() => setFase({ f: 'listo' })} flex />
          </View>
        )}
        {fase.f === 'noentendi' && (
          <View style={{ gap: 8 }}>
            <Boton alto={56} icono="mic.fill" texto={t.repetir} onPress={() => { setLado(fase.lado); empezar(); }} />
            <Boton tipo="texto" texto={t.volver} onPress={() => setFase({ f: 'listo' })} />
          </View>
        )}
        {fase.f === 'error' && (
          <View style={{ gap: 8 }}>
            {fase.sinServidor
              ? <Boton texto={t.conectar} icono="link" onPress={() => router.push('/ajustes')} />
              : <Boton texto={t.reintentar} icono="arrow.clockwise" onPress={reintentar} />}
            {!fase.sinServidor && (
              <Boton tipo="secundario" icono="antenna.radiowaves.left.and.right" texto={fase.prueba === 'probando' ? '…' : t.probarConexion}
                onPress={probarConexion} deshabilitado={fase.prueba === 'probando'} />
            )}
            <Boton tipo="texto" texto={t.volver} onPress={() => setFase({ f: 'listo' })} />
          </View>
        )}
        {fase.f === 'pensando' && (
          <View style={{ alignItems: 'center' }}>
            {/* Mientras piensa, el brillo gira por la constelación en el mismo lugar donde estaba el micrófono. */}
            <AnilloInti modo="piensa" tinte={fase.lado} centro={72}>
              <View style={[e.micro, { width: 72, height: 72, borderRadius: 36, backgroundColor: C.actionTint }]}>
                <Icono nombre="ellipsis" color={C.action} tam={28} />
              </View>
            </AnilloInti>
          </View>
        )}
        {fase.f === 'listo' && ensayo && (
          <Pressable accessibilityRole="button" onPress={ensayarNegativa} style={e.chipEnsayo}>
            <Icono nombre="theatermasks.fill" color={C.ink} tam={14} />
            <Text style={e.chipEnsayoTexto}>{t.ensayoChip}</Text>
          </Pressable>
        )}
        {(fase.f === 'listo' || fase.f === 'grabando') && (
          <Microfono
            nivel={nivelVoz}
            grabando={fase.f === 'grabando'}
            lado={lado}
            perfil={perfil}
            t={t}
            onPress={fase.f === 'grabando' ? terminar : empezar}
            onCambiarLado={() => fase.f === 'listo' && setLado(siguienteLado(lado))}
            onReceta={() => router.push('/receta')}
            onResumen={() => router.push('/resumen')}
          />
        )}
      </View>
    </SafeAreaView>
  );
}

// ---- piezas -------------------------------------------------------------------------------

/** «Chaski pregunta»: la repregunta al mismo hablante, con el porqué y el dato que falta. */
function TarjetaPregunta({ d, t }: { d: Extract<Interprete, { tipo: 'pregunta' }>; t: Textos }) {
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)} style={{ gap: 12, marginTop: 12 }}>
      <View style={{ alignItems: 'center' }}><Etiqueta idioma={d.para === 'paciente' ? 'quechua' : 'castellano'} /></View>
      <Tarjeta estilo={{ gap: 8 }}>
        <View style={e.fila}>
          <Icono nombre="questionmark.bubble.fill" color={C.action} tam={20} />
          <Text style={e.rotuloAccion}>{t.chaskiPregunta}</Text>
        </View>
        {d.para === 'paciente' && d.quechua ? <Text style={e.quechua}>{d.quechua}</Text> : null}
        {d.texto ? <Text style={d.para === 'paciente' && d.quechua ? e.secundario : e.significado}>{d.texto}</Text> : null}
      </Tarjeta>
      {(d.motivo || d.dato) && (
        <Tarjeta estilo={{ gap: 8 }}>
          {d.motivo ? <Text style={e.secundario} numberOfLines={2}>{d.motivo}</Text> : null}
          {d.dato ? (
            <View style={e.chipDato}>
              <Icono nombre="exclamationmark.circle" color={C.warn} tam={14} />
              <Text style={e.chipDatoTexto}>{t.falta}: {d.dato}</Text>
            </View>
          ) : null}
        </Tarjeta>
      )}
    </Animated.View>
  );
}

/** Chaski le responde al personal directamente: no se traduce al paciente. */
function TarjetaRespuesta({ d, t }: { d: Extract<Interprete, { tipo: 'respuesta' }>; t: Textos }) {
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)} style={{ gap: 12, marginTop: 12 }}>
      <View style={{ alignItems: 'center' }}><Etiqueta idioma="castellano" /></View>
      <Tarjeta estilo={{ gap: 8 }}>
        <View style={e.fila}>
          <Icono nombre="bubble.left.fill" color={C.action} tam={20} />
          <Text style={e.rotuloAccion}>{t.chaskiResponde}</Text>
        </View>
        <Text style={e.significado}>{d.texto}</Text>
      </Tarjeta>
    </Animated.View>
  );
}

function TarjetaNoEntendi({ d, t }: { d: Extract<Interprete, { tipo: 'no_entendi' }>; t: Textos }) {
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)} style={{ gap: 10, marginTop: 12, alignItems: 'center' }}>
      <Text style={e.titulo}>{t.noLeEntendi}</Text>
      {d.quechua ? <Text style={[e.quechua, { textAlign: 'center' }]}>{d.quechua}</Text> : null}
      {d.motivo ? <Aviso tipo="warn" texto={d.motivo} /> : null}
    </Animated.View>
  );
}

/** Frase verificada del banco (C9): traducción y audio revisados. */
function TarjetaFrase({ d, t }: { d: Extract<Interprete, { tipo: 'frase' }>; t: Textos }) {
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)} style={{ gap: 12, marginTop: 12 }}>
      <View style={{ alignItems: 'center' }}><Etiqueta idioma="quechua" /></View>
      <Tarjeta estilo={{ gap: 8 }}>
        <Text style={e.quechua}>{d.frase.quy}</Text>
        <Zigzag />
        <Text style={e.secundario}>{d.frase.es}</Text>
      </Tarjeta>
      <View style={[e.auditoria, { backgroundColor: C.okTint }]}>
        <View style={e.fila}>
          <Icono nombre="checkmark.seal.fill" color={C.ok} tam={18} />
          <Text style={[e.auditoriaTitulo, { color: C.ok }]}>{t.fraseVerificada}</Text>
        </View>
      </View>
    </Animated.View>
  );
}

function Encabezado({ t }: { t: Textos }) {
  const [ahora, setAhora] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const s = Math.max(0, Math.floor((ahora - inicioDeConsulta()) / 1000));
  const reloj = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  return (
    <View style={e.encabezado}>
      <Pressable onLongPress={() => router.push('/ajustes')} style={e.marca} accessibilityHint="Mantenga presionado para ajustes">
        <MarcaChaski />
        <Text style={e.reloj}>{t.consulta} · {reloj}</Text>
      </Pressable>
      <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t.emergencia}
          onPress={() => router.push('/emergencia')}
          style={({ pressed }) => [e.emergencia, pressed && { opacity: 0.8 }]}>
          <Icono nombre="bolt.heart.fill" color={C.surface} tam={16} />
          <Text style={e.emergenciaTexto}>{t.emergencia}</Text>
        </Pressable>
        <Pressable accessibilityLabel="Ver la conversación" onPress={() => router.push('/historial')} style={e.botonRedondo}>
          <Icono nombre="doc.text" color={C.inkSecondary} tam={18} />
        </Pressable>
      </View>
    </View>
  );
}

function Microfono({ grabando, nivel, lado, perfil, t, onPress, onCambiarLado, onReceta, onResumen }: {
  grabando: boolean; nivel: number; lado: Lado; perfil: Perfil; t: Textos; onPress: () => void; onCambiarLado: () => void; onReceta: () => void; onResumen: () => void;
}) {
  return (
    <View style={{ alignItems: 'center', gap: 12 }}>
      <View style={e.filaMicro}>
        <View style={e.lateral}>
          {!grabando && (
            <BotonEscalonado onPress={onReceta} etiqueta="Leer receta">
              <Icono nombre="camera" color={C.inkSecondary} tam={22} />
            </BotonEscalonado>
          )}
          {!grabando && <Text style={e.lateralTexto}>{t.receta}</Text>}
        </View>
        <AnilloInti modo={grabando ? 'escucha' : 'reposo'} nivel={nivel} tinte={lado}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={grabando ? 'Terminar y traducir' : 'Empezar a hablar'}
          onPress={onPress}
          style={({ pressed }) => [
            e.micro,
            { backgroundColor: grabando || pressed ? C.actionPressed : C.action },
            grabando && { borderWidth: 6, borderColor: C.actionTint },
          ]}>
          <Icono nombre={grabando ? 'stop.fill' : 'mic.fill'} color={C.surface} tam={36} />
        </Pressable>
        </AnilloInti>
        <View style={e.lateral}>
          {!grabando && (
            <BotonEscalonado onPress={onResumen} etiqueta="Terminar y ver el resumen">
              <Icono nombre="checklist" color={C.inkSecondary} tam={22} />
            </BotonEscalonado>
          )}
          {!grabando && <Text style={e.lateralTexto}>{t.resumen}</Text>}
        </View>
      </View>
      <Text style={e.microTexto}>{grabando ? t.tocarTerminar : t.tocarHablar}</Text>
      <Pressable onPress={onCambiarLado} disabled={grabando} style={e.lado} accessibilityHint="Toque para cambiar quién habla">
        <Icono nombre="arrow.left.arrow.right" color={C.inkSecondary} tam={14} />
        <Text style={e.ladoTexto}>
          {primeraMayuscula(t.habla(quienHabla(perfil, lado, t), lado === 'castellano' ? t.castellano : t.quechua))}
        </Text>
      </Pressable>
    </View>
  );
}

/** El medidor mientras alguien habla: una fila de crucecitas que crecen con la voz, del color del turno. */
function Medidor({ nivel, tinte, t }: { nivel: number; tinte: Lado; t: Textos }) {
  const [historia, setHistoria] = useState<number[]>(Array(18).fill(0));
  useEffect(() => setHistoria((h) => [...h.slice(1), nivel]), [nivel]);
  const color = tinte === 'quechua' ? C.quechua : C.action;
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)}>
      <Tarjeta estilo={{ marginTop: 16, alignItems: 'center' }}>
        <View style={e.barras}>
          {historia.map((v, i) => (
            <View key={i} style={{ width: 16, alignItems: 'center' }}>
              <Cruz tam={Math.round(5 + v * 11)} color={color} />
            </View>
          ))}
        </View>
      </Tarjeta>
    </Animated.View>
  );
}

/** El ensayo de la negativa siempre se dice en claro: nunca se presenta como un error real del traductor. */
function LetreroEnsayo({ sinConexion, noBloqueo, t }: { sinConexion?: boolean; noBloqueo?: boolean; t: Textos }) {
  return (
    <View style={e.ensayo}>
      <Icono nombre="theatermasks.fill" color={C.ink} tam={16} />
      <Text style={e.ensayoTexto}>
        {noBloqueo ? t.ensayoNoBloqueo : sinConexion ? t.ensayoSinConexion : t.ensayoLetrero}
      </Text>
    </View>
  );
}

function Pensando({ fase, t }: { fase: Extract<Fase, { f: 'pensando' }>; t: Textos }) {
  const pasos = fase.lado === 'castellano' ? t.pasosCastellano : t.pasosQuechua;
  // Pasos reales por tiempo transcurrido (Opus + crítico ≈ 5–6 s, p95 ~11 s): nunca silencio.
  const [ahora, setAhora] = useState(Date.now());
  useEffect(() => {
    const i = setInterval(() => setAhora(Date.now()), 250);
    return () => clearInterval(i);
  }, []);
  const transcurrido = fase.desde ? ahora - fase.desde : 0;
  const paso = fase.desde ? Math.max(fase.paso, pasoPorTiempo(transcurrido)) : fase.paso;
  const lento = transcurrido >= AVISO_LENTO_MS;
  const muyLento = transcurrido >= AVISO_MUY_LENTO_MS;
  return (
    <View style={{ gap: 12, marginTop: 16 }}>
      {fase.oido ? (
        <Tarjeta>
          <Etiqueta idioma="castellano" />
          <Text style={[e.cuerpoTexto, { marginTop: 8 }]}>{fase.oido}</Text>
          {fase.pulido && fase.pulido !== fase.oido ? (
            <Animated.View entering={FadeInDown.springify().damping(18)} style={{ marginTop: 10, gap: 4 }}>
              <Text style={e.secundario}>{t.chaskiLoDira} {fase.pulido}</Text>
            </Animated.View>
          ) : null}
        </Tarjeta>
      ) : null}
      {/* Una sola línea que cambia: para quien casi no usa tecnología, una lista de pasos es ruido (D41). */}
      <View style={e.pensandoLinea}>
        <Animated.View key={paso} entering={ZoomIn.springify().damping(14)}>
          <Icono nombre="ellipsis.circle" color={C.action} tam={22} />
        </Animated.View>
        <Text style={e.pensandoTexto}>{muyLento ? t.sigueRevisando : lento ? t.puedeTardar : pasos[paso]}</Text>
      </View>
    </View>
  );
}

function Dicho({ v, vozLista, hablando, progreso, t }: {
  v: Extract<Veredicto, { tipo: 'dicho' | 'dicho_con_aviso' }>; vozLista: boolean; hablando: boolean; progreso: number; t: Textos;
}) {
  // El texto se lee siempre entero; lo que la voz ya dijo pasa a tinta plena, palabra por palabra.
  const palabras = v.quechua.split(/\s+/).filter(Boolean);
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)} style={{ gap: 12, marginTop: 12 }}>
      <View style={{ alignItems: 'center' }}><Etiqueta idioma="quechua" /></View>
      <Tarjeta>
        <Text style={e.quechua}>
          {/* Texto entero y fijo: revelarlo palabra por palabra parpadeaba (Freddy, 25-oct 01:46). */}
          {palabras.map((p, i) => (
            <Text key={i} style={{ color: C.ink }}>{p}{i < palabras.length - 1 ? ' ' : ''}</Text>
          ))}
        </Text>
        <Zigzag />
        <Text style={e.secundario}>{v.castellano}</Text>
      </Tarjeta>
      {/* La auditoría (y el crítico) en una sola línea verde: la seguridad se ve sin leer (D41). */}
      <Animated.View entering={ZoomIn.delay(250).springify().damping(14)} style={e.revisado}>
        <Icono nombre={v.critico ? 'checkmark.seal.fill' : 'checkmark.shield.fill'} color={C.ok} tam={20} />
        <Text style={e.revisadoTexto}>{t.auditado}</Text>
      </Animated.View>
      {v.tipo === 'dicho_con_aviso' && (
        <Aviso
          tipo="warn"
          texto={v.aviso ? v.aviso : v.terminos.length ? t.dichoConAviso(v.terminos.join(', ')) : t.dichoConAvisoSolo}
        />
      )}
    </Animated.View>
  );
}

function Bloqueado({ v, t }: { v: Extract<Veredicto, { tipo: 'bloqueado' }>; t: Textos }) {
  // Un solo temblor suave de la comparación al aparecer: avisa sin alarmar. Nunca rojo que parpadea.
  const quieto = useReducedMotion();
  const x = useSharedValue(0);
  useEffect(() => {
    if (quieto) return;
    x.value = withSequence(
      withTiming(-6, { duration: 70 }), withTiming(6, { duration: 70 }),
      withTiming(-3, { duration: 70 }), withTiming(0, { duration: 70 }),
    );
  }, [quieto, x]);
  const temblor = useAnimatedStyle(() => ({ transform: [{ translateX: x.value }] }));
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)} style={{ gap: 12, marginTop: 12 }}>
      {/* El bloqueo es la función estrella haciendo su trabajo, no un error: se dice como protección. */}
      <View style={e.protegio}>
        <Icono nombre="checkmark.shield.fill" color={C.action} tam={16} />
        <Text style={e.protegioTexto}>{t.loFrenoATiempo}</Text>
      </View>
      <Text style={[e.titulo, { color: C.block, textAlign: 'center' }]}>{t.noLoDije}</Text>
      <Animated.Text style={[e.razon, temblor]}>{razonCorta(v)}</Animated.Text>
      {/* Lo que Chaski oyó, en gris: separa un error del reconocedor de uno del traductor. */}
      {v.oido ? <Text style={e.oido}>Oí: «{v.oido}»</Text> : null}
    </Animated.View>
  );
}

/** Una sola línea con el motivo del bloqueo, en palabras simples. */
function razonCorta(v: Extract<Veredicto, { tipo: 'bloqueado' }>): string {
  if (v.razon) return primeraMayuscula(v.razon);
  const d = v.diferencias[0];
  if (d) return `Cambió: ${d.nombre.toLowerCase()}`;
  if (v.terminos.length) return `Palabra dudosa: ${v.terminos.join(', ')}`;
  return 'Algo cambió al traducir';
}

function Paciente({ r, t }: { r: RespuestaPaciente; t: Textos }) {
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)}>
    <Tarjeta estilo={{ marginTop: 16, gap: 8 }}>
      <Text style={e.significado}>{r.castellano || t.noLoEntendi}</Text>
      <Text style={[e.secundario, { color: C.quechua }]} numberOfLines={1}>{r.chanka_oido || t.noSeOyo}</Text>
      <View style={{ marginTop: 6 }}>
        {r.seguro
          ? <Aviso tipo="ok" texto={t.entendidoSeguro} />
          : <Aviso tipo="warn" texto={t.seguridadMedia} />}
      </View>
    </Tarjeta>
    </Animated.View>
  );
}

/** Segundos desde que se activó, cada 50 ms. Solo para el modo demo, que no tiene micrófono ni audio. */
function useRelojDemo(activo: boolean): number {
  const [t, setT] = useState(0);
  useEffect(() => {
    if (!activo) return;
    const inicio = Date.now();
    const id = setInterval(() => setT((Date.now() - inicio) / 1000), 50);
    return () => clearInterval(id);
  }, [activo]);
  return t;
}

function primeraMayuscula(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const e = StyleSheet.create({
  detalleError: { fontSize: ESCALA.mini, color: C.inkTertiary, fontVariant: ['tabular-nums'] },
  ensayo: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: C.castellanoTag, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 8, marginTop: 12 },
  ensayoTexto: { fontSize: ESCALA.mini, fontWeight: '600', color: C.ink, flexShrink: 1 },
  chipEnsayo: { flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'center', backgroundColor: C.castellanoTag, borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6, marginBottom: 8 },
  chipEnsayoTexto: { fontSize: ESCALA.mini, fontWeight: '700', color: C.ink },
  fila: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  rotuloAccion: { fontSize: ESCALA.chico, fontWeight: '700', color: C.action },
  chipDato: { flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-start', backgroundColor: C.warnTint, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 5 },
  chipDatoTexto: { fontSize: ESCALA.mini, fontWeight: '600', color: C.warn },
  emergencia: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 36, paddingHorizontal: 12, borderRadius: 18, backgroundColor: C.ink },
  emergenciaTexto: { fontSize: ESCALA.mini, fontWeight: '700', color: C.surface },
  pantalla: { flex: 1, backgroundColor: C.ground },
  encabezado: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 10 },
  marca: { gap: 2 },
  // Alineado bajo «Chaski», pasando la chakana.
  reloj: { fontSize: ESCALA.mini, color: C.inkSecondary, fontVariant: ['tabular-nums'], paddingLeft: 27 },
  botonRedondo: { width: 40, height: 40, borderRadius: 20, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, alignItems: 'center', justifyContent: 'center' },
  cuerpo: { paddingHorizontal: 16, paddingTop: 16, paddingBottom: 24 },
  centro: { alignItems: 'center' },
  centroTexto: { alignItems: 'center', gap: 8, marginTop: 20 },
  filaChica: { flexDirection: 'row', gap: 14, alignItems: 'center' },
  titulo: { fontSize: ESCALA.h1, fontWeight: '700', color: C.ink, textAlign: 'center' },
  explicacion: { fontSize: ESCALA.chico, color: C.inkSecondary, textAlign: 'center', maxWidth: 300, lineHeight: 20 },
  secundario: { fontSize: ESCALA.chico, color: C.inkSecondary, lineHeight: 20 },
  mini: { fontSize: ESCALA.mini, color: C.inkTertiary },
  cuerpoTexto: { fontSize: ESCALA.h2, color: C.ink, lineHeight: 26 },
  quechua: { fontSize: ESCALA.h1, fontWeight: '600', color: C.ink, lineHeight: 31 },
  significado: { fontSize: ESCALA.h1, fontWeight: '700', color: C.ink, lineHeight: 31 },
  rotulo: { fontSize: ESCALA.mini, fontWeight: '600', color: C.inkTertiary, letterSpacing: 0.6 },
  pensandoLinea: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, paddingVertical: 14 },
  pensandoTexto: { fontSize: ESCALA.h2, fontWeight: '600', color: C.ink },
  revisado: { flexDirection: 'row', alignItems: 'center', gap: 8, alignSelf: 'center', backgroundColor: C.okTint, borderRadius: 18, paddingHorizontal: 16, paddingVertical: 8 },
  revisadoTexto: { fontSize: ESCALA.cuerpo, fontWeight: '700', color: C.ok },
  razon: { fontSize: ESCALA.cuerpo, color: C.inkSecondary, textAlign: 'center' },
  oido: { fontSize: ESCALA.mini, color: C.inkTertiary, textAlign: 'center', paddingHorizontal: 16 },
  protegio: { flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'center', backgroundColor: C.actionTint, borderRadius: 14, paddingHorizontal: 12, paddingVertical: 6 },
  protegioTexto: { fontSize: ESCALA.mini, fontWeight: '700', color: C.action },
  auditoria: { borderRadius: 16, padding: 14, gap: 8 },
  auditoriaTitulo: { fontSize: ESCALA.chico, fontWeight: '600' },
  // Cada verificación en su propio chip blanco (D29): ningún motivo toca la fila de auditoría.
  paso: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  barras: { flexDirection: 'row', alignItems: 'center', height: 40, marginTop: 12 },
  pie: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8 },
  filaBotones: { flexDirection: 'row', gap: 12 },
  filaMicro: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', alignSelf: 'stretch' },
  micro: { width: 96, height: 96, borderRadius: 48, alignItems: 'center', justifyContent: 'center' },
  microTexto: { fontSize: ESCALA.chico, fontWeight: '600', color: C.action },
  lateral: { width: 72, alignItems: 'center', gap: 4 },
  lateralTexto: { fontSize: ESCALA.mini, color: C.inkSecondary },
  lado: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingVertical: 8, paddingHorizontal: 14, borderRadius: 16, backgroundColor: C.castellanoTag },
  ladoTexto: { fontSize: ESCALA.mini, fontWeight: '600', color: C.inkSecondary },
});
