// La consulta: una sola pantalla que cambia de estado (tablero de Pencil + design/specs/02-pulido-ui.md).
import {
  IOSOutputFormat, setAudioModeAsync, useAudioPlayer, useAudioPlayerStatus, useAudioRecorder,
  useAudioRecorderState, requestRecordingPermissionsAsync, type RecordingOptions,
} from 'expo-audio';
import * as Haptics from 'expo-haptics';
import { Redirect, router, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { escuchar, SinServidor, turnoEnfermera, turnoPaciente, voz } from '@/chaski/api';
import { Chaski, type EstadoChaski } from '@/chaski/chaski';
import { agregarTurno, inicioDeConsulta } from '@/chaski/consulta';
import {
  fueCastellano, siguienteLado, veredictoEnfermera, type Lado, type RespuestaPaciente, type Veredicto,
} from '@/chaski/modelo';
import { usePerfil, type Perfil } from '@/chaski/perfil';
import { idiomaDelOtro, otraPersona, quienHabla, textos, type Textos } from '@/chaski/textos';
import { C, ESCALA } from '@/chaski/tokens';
import { AnilloChakana, BotonEscalonado, Cruz, MarcaChaski, Zigzag } from '@/chaski/motivos';
import { nivelDesdeDb, palabrasDichas } from '@/chaski/movimiento';
import { Aviso, Boton, Etiqueta, Icono, Tarjeta } from '@/chaski/ui';
import { bocaAbierta, envolvente, nivelEn, type Envolvente } from '@/chaski/wav';
import Animated, {
  FadeInDown, useAnimatedStyle, useReducedMotion, useSharedValue, withSequence, withTiming, ZoomIn,
} from 'react-native-reanimated';

// WAV 16 kHz mono 16 bits: lo que piden el detector de idioma y el reconocimiento (CONTRATO.md §1).
const GRABACION: RecordingOptions = {
  extension: '.wav',
  sampleRate: 16000,
  numberOfChannels: 1,
  bitRate: 256000,
  isMeteringEnabled: true,
  ios: {
    outputFormat: IOSOutputFormat.LINEARPCM,
    audioQuality: 96,
    linearPCMBitDepth: 16,
    linearPCMIsBigEndian: false,
    linearPCMIsFloat: false,
  },
  android: { outputFormat: 'default', audioEncoder: 'default' },
  web: {},
};


type Fase =
  | { f: 'listo' }
  | { f: 'grabando' }
  | { f: 'pensando'; lado: Lado; paso: number; oido?: string }
  | { f: 'dicho'; v: Extract<Veredicto, { tipo: 'dicho' | 'dicho_con_aviso' }>; vozLista: boolean }
  | { f: 'bloqueado'; v: Extract<Veredicto, { tipo: 'bloqueado' }> }
  | { f: 'paciente'; r: RespuestaPaciente }
  | { f: 'error'; mensaje: string; sinServidor: boolean };

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
  error: { f: 'error', mensaje: 'No pude conectarme. Vuelva a intentarlo.', sinServidor: false },
};

export default function Pantalla() {
  const perfil = usePerfil();
  const q = useLocalSearchParams<{ demo?: string; idioma?: string; rol?: string }>();
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
  return <Consulta perfil={perfil} />;
}

function Consulta({ perfil, inicial }: { perfil: Perfil; inicial?: Fase }) {
  const t = textos(perfil.idioma);
  const [fase, setFase] = useState<Fase>(inicial ?? { f: 'listo' });
  const [lado, setLado] = useState<Lado>(perfil.idioma);
  const [env, setEnv] = useState<Envolvente | null>(null);
  const ultimoAudio = useRef<string | null>(null);

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
  async function empezar() {
    reproductor.pause();
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    await grabadora.prepareToRecordAsync();
    grabadora.record();
    setFase({ f: 'grabando' });
  }

  async function terminar() {
    await grabadora.stop();
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const uri = grabadora.uri;
    if (!uri) return fallar(new Error('sin audio'));
    ultimoAudio.current = uri;
    if (lado === 'castellano') return turnoDeLaEnfermera(uri);
    return turnoDelPaciente(uri);
  }

  // ---- turnos -----------------------------------------------------------------------------
  async function turnoDeLaEnfermera(uri: string) {
    try {
      setFase({ f: 'pensando', lado: 'castellano', paso: 0 });
      const { texto } = await escuchar(uri);
      if (!texto.trim()) throw new Error('No le escuché bien');
      setFase({ f: 'pensando', lado: 'castellano', paso: 1, oido: texto });
      const avance = setTimeout(() => setFase((p) => (p.f === 'pensando' ? { ...p, paso: 2 } : p)), 1800);
      const r = await turnoEnfermera(texto, perfil.rol);
      clearTimeout(avance);
      const v = veredictoEnfermera(texto, r);
      agregarTurno({ lado: 'castellano', castellano: texto, quechua: r.quechua, estado: v.tipo });
      if (v.tipo === 'bloqueado') {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        setFase({ f: 'bloqueado', v });
        return;
      }
      setFase({ f: 'dicho', v, vozLista: false });
      setLado(siguienteLado('castellano'));
      await decir(v.quechua);
      setFase((p) => (p.f === 'dicho' ? { ...p, vozLista: true } : p));
    } catch (e) {
      fallar(e);
    }
  }

  async function turnoDelPaciente(uri: string) {
    try {
      setFase({ f: 'pensando', lado: 'quechua', paso: 0 });
      const avance = setTimeout(() => setFase((p) => (p.f === 'pensando' ? { ...p, paso: 1 } : p)), 700);
      const avance2 = setTimeout(() => setFase((p) => (p.f === 'pensando' ? { ...p, paso: 2 } : p)), 2600);
      const r = await turnoPaciente(uri, perfil.rol);
      clearTimeout(avance);
      clearTimeout(avance2);
      if (fueCastellano(r)) {
        // Detección automática (D11): el turno se habló en castellano aunque tocaba quechua.
        setLado('castellano');
        return turnoDeLaEnfermera(uri);
      }
      agregarTurno({
        lado: 'quechua', castellano: r.castellano, quechua: r.chanka_oido,
        estado: r.seguro ? 'entendido' : 'con_dudas',
      });
      setFase({ f: 'paciente', r });
      setLado('castellano');
    } catch (e) {
      fallar(e);
    }
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
    const sinServidor = e instanceof SinServidor;
    setFase({
      f: 'error',
      sinServidor,
      mensaje: sinServidor
        ? t.sinServidor
        : String((e as Error)?.message ?? '').includes('escuché')
          ? t.noEscuche
          : t.sinConexion,
    });
  }

  function reintentar() {
    const uri = ultimoAudio.current;
    if (!uri) return setFase({ f: 'listo' });
    return lado === 'castellano' ? turnoDeLaEnfermera(uri) : turnoDelPaciente(uri);
  }

  // ---- qué se ve ----------------------------------------------------------------------------
  const estadoChaski: EstadoChaski =
    fase.f === 'grabando' ? 'escuchando'
      : fase.f === 'pensando' ? 'pensando'
        : fase.f === 'bloqueado' || fase.f === 'error' ? 'no_entendi'
          : fase.f === 'dicho' ? 'hablando'
            : fase.f === 'paciente' ? 'escuchando'
              : 'reposo';
  const protagonista = fase.f === 'listo' || fase.f === 'dicho' || fase.f === 'bloqueado' || fase.f === 'error' || fase.f === 'pensando';

  return (
    <SafeAreaView style={e.pantalla} edges={['top', 'bottom']}>
      <Encabezado t={t} />
      <ScrollView contentContainerStyle={e.cuerpo} bounces={false}>
        {protagonista ? (
          <View style={e.centro}>
            <Chaski estado={estadoChaski} tam={fase.f === 'listo' ? 240 : fase.f === 'bloqueado' || fase.f === 'pensando' ? 150 : 200} boca={boca} pulso={fase.f === 'dicho' ? pulso : undefined} />
          </View>
        ) : (
          <View style={e.filaChica}>
            <Chaski estado={estadoChaski} tam={112} />
            <View style={{ gap: 6, flex: 1 }}>
              <Etiqueta idioma={fase.f === 'paciente' ? 'quechua' : lado} />
              <Text style={e.secundario}>
                {fase.f === 'grabando' ? t.escuchando : fase.f === 'paciente' ? t.idiomaDetectado : ''}
              </Text>
            </View>
          </View>
        )}

        {fase.f === 'listo' && (
          <View style={e.centroTexto}>
            <Text style={e.titulo}>{t.listo}</Text>
            <Text style={e.explicacion}>{explicacion(perfil, lado, t)}</Text>
          </View>
        )}

        {fase.f === 'grabando' && <Medidor nivel={nivelVoz} tinte={lado} t={t} />}

        {fase.f === 'pensando' && <Pensando fase={fase} t={t} />}

        {fase.f === 'dicho' && <Dicho v={fase.v} vozLista={fase.vozLista || hablandoDemo} hablando={hablando} progreso={progresoVoz} t={t} />}

        {fase.f === 'bloqueado' && <Bloqueado v={fase.v} t={t} />}

        {fase.f === 'paciente' && <Paciente r={fase.r} t={t} />}

        {fase.f === 'error' && (
          <View style={e.centroTexto}>
            <Text style={e.titulo}>{fase.mensaje}</Text>
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
        {fase.f === 'error' && (
          <View style={{ gap: 8 }}>
            {fase.sinServidor
              ? <Boton texto={t.conectar} icono="link" onPress={() => router.push('/ajustes')} />
              : <Boton texto={t.reintentar} icono="arrow.clockwise" onPress={reintentar} />}
            <Boton tipo="texto" texto={t.volver} onPress={() => setFase({ f: 'listo' })} />
          </View>
        )}
        {fase.f === 'pensando' && (
          <View style={{ alignItems: 'center' }}>
            {/* Mientras piensa, el brillo gira por la constelación en el mismo lugar donde estaba el micrófono. */}
            <AnilloChakana modo="piensa" tinte={fase.lado} lado={116}>
              <View style={[e.micro, { width: 72, height: 72, borderRadius: 36, backgroundColor: C.actionTint }]}>
                <Icono nombre="ellipsis" color={C.action} tam={28} />
              </View>
            </AnilloChakana>
          </View>
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

function explicacion(p: Perfil, lado: Lado, t: Textos): string {
  const otro = otraPersona(p.rol, t);
  if (lado !== p.idioma) return t.explicaOtro(otro, lado === 'castellano' ? t.castellano : t.quechua);
  return p.idioma === 'castellano' ? t.explicaYo(otro) : t.explicaYoQuechua(otro);
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
      <Pressable accessibilityLabel="Ver la conversación" onPress={() => router.push('/historial')} style={e.botonRedondo}>
        <Icono nombre="doc.text" color={C.inkSecondary} tam={18} />
      </Pressable>
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
        <AnilloChakana modo={grabando ? 'escucha' : 'reposo'} nivel={nivel} tinte={lado}>
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
        </AnilloChakana>
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
        <Text style={e.secundario}>{t.hableNormal}</Text>
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

function Pensando({ fase, t }: { fase: Extract<Fase, { f: 'pensando' }>; t: Textos }) {
  const pasos = fase.lado === 'castellano' ? t.pasosCastellano : t.pasosQuechua;
  return (
    <View style={{ gap: 12, marginTop: 16 }}>
      {fase.oido ? (
        <Tarjeta>
          <Etiqueta idioma="castellano" />
          <Text style={[e.cuerpoTexto, { marginTop: 8 }]}>{fase.oido}</Text>
        </Tarjeta>
      ) : null}
      <Tarjeta estilo={{ gap: 10 }}>
        {pasos.map((p, i) => {
          const hecho = i < fase.paso;
          const ahora = i === fase.paso;
          return (
            <View key={p} style={e.paso}>
              {/* Cada paso cumplido entra con un resorte chico: se siente que avanzó. */}
              <Animated.View key={hecho ? 'hecho' : 'falta'} entering={hecho ? ZoomIn.springify().damping(12) : undefined}>
                <Icono
                  nombre={hecho ? 'checkmark.circle.fill' : ahora ? 'ellipsis.circle' : 'circle'}
                  color={hecho ? C.ok : ahora ? C.action : C.border}
                  tam={20}
                />
              </Animated.View>
              <Text style={[e.pasoTexto, { color: hecho || ahora ? C.ink : C.inkTertiary }]}>{p}</Text>
            </View>
          );
        })}
      </Tarjeta>
    </View>
  );
}

function Casillas({ casillas }: { casillas: { nombre: string; ok: boolean }[] }) {
  return (
    <View style={e.casillas}>
      {casillas.map((c, i) => (
        // Los chips entran uno por uno: la auditoría se ve revisada, punto por punto.
        <Animated.View key={c.nombre} entering={ZoomIn.delay(180 + i * 110).springify().damping(14)} style={e.casilla}>
          <Icono nombre="checkmark" color={C.ok} tam={11} />
          <Text style={e.casillaTexto}>{c.nombre}</Text>
        </Animated.View>
      ))}
    </View>
  );
}

function Dicho({ v, vozLista, hablando, progreso, t }: {
  v: Extract<Veredicto, { tipo: 'dicho' | 'dicho_con_aviso' }>; vozLista: boolean; hablando: boolean; progreso: number; t: Textos;
}) {
  // El texto se lee siempre entero; lo que la voz ya dijo pasa a tinta plena, palabra por palabra.
  const palabras = v.quechua.split(/\s+/).filter(Boolean);
  const dichas = hablando ? palabrasDichas(palabras.length, progreso) : vozLista ? palabras.length : 0;
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)} style={{ gap: 12, marginTop: 12 }}>
      <View style={{ alignItems: 'center' }}><Etiqueta idioma="quechua" /></View>
      <Tarjeta>
        <Text style={e.quechua}>
          {palabras.map((p, i) => (
            <Text key={i} style={{ color: i < dichas ? C.ink : C.inkTertiary }}>{p}{i < palabras.length - 1 ? ' ' : ''}</Text>
          ))}
        </Text>
        <Zigzag />
        <Text style={e.secundario}>{v.castellano}</Text>
        <Text style={[e.mini, { marginTop: 8 }]}>
          {!vozLista ? t.preparandoVoz : hablando ? t.hablandoAhora : t.yaLoDijo}
        </Text>
      </Tarjeta>
      <View style={[e.auditoria, { backgroundColor: C.okTint }]}>
        <View style={e.paso}>
          <Icono nombre="checkmark.shield.fill" color={C.ok} tam={18} />
          <Text style={[e.auditoriaTitulo, { color: C.ok }]}>{t.auditado}</Text>
        </View>
        <Casillas casillas={v.casillas} />
      </View>
      {v.tipo === 'dicho_con_aviso' && (
        <Aviso
          tipo="warn"
          texto={v.terminos.length ? t.dichoConAviso(v.terminos.join(', ')) : t.dichoConAvisoSolo}
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
      <Text style={[e.titulo, { color: C.block, textAlign: 'center' }]}>{t.noLoDije}</Text>
      <Text style={[e.explicacion, { alignSelf: 'center' }]}>{t.reviseParte}</Text>
      <Tarjeta>
        <Etiqueta idioma="castellano" />
        <Text style={[e.cuerpoTexto, { marginTop: 8 }]}>{v.castellano}</Text>
      </Tarjeta>
      {v.diferencias.length > 0 ? (
        v.diferencias.map((d, i) => (
          <Animated.View key={i} style={[e.comparacion, temblor]}>
            <Text style={[e.rotulo, { color: C.block }]}>{d.nombre.toUpperCase()}</Text>
            <View style={e.dosColumnas}>
              <View style={{ flex: 1 }}>
                <Text style={e.rotulo}>{t.ustedDijo}</Text>
                <Text style={e.valor}>{d.dijo}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={e.rotulo}>{t.traduccionDecia}</Text>
                <Text style={[e.valor, { color: C.block }]}>{d.decia}</Text>
              </View>
            </View>
          </Animated.View>
        ))
      ) : (
        <View style={e.comparacion}>
          <Text style={e.rotulo}>{t.sinTraduccionSegura}</Text>
          <Text style={e.valor}>{v.terminos.join(', ')}</Text>
        </View>
      )}
      {v.casillasOk.length > 0 && (
        <Tarjeta>
          <Text style={e.rotulo}>{t.loDemasBien}</Text>
          <Casillas casillas={v.casillasOk.map((nombre) => ({ nombre, ok: true }))} />
        </Tarjeta>
      )}
    </Animated.View>
  );
}

function Paciente({ r, t }: { r: RespuestaPaciente; t: Textos }) {
  return (
    <Animated.View entering={FadeInDown.springify().damping(18)}>
    <Tarjeta estilo={{ marginTop: 16, gap: 6 }}>
      <Text style={e.rotulo}>{t.loQueDijo}</Text>
      <Text style={[e.cuerpoTexto, { color: C.inkSecondary }]}>{r.chanka_oido || t.noSeOyo}</Text>
      <Text style={[e.rotulo, { marginTop: 16 }]}>{t.loQueQuisoDecir}</Text>
      <Text style={e.significado}>{r.castellano || t.noLoEntendi}</Text>
      <View style={{ marginTop: 12, gap: 8 }}>
        {r.seguro
          ? <Aviso tipo="ok" texto={t.entendidoSeguro} />
          : <Aviso tipo="warn" texto={t.seguridadMedia} />}
        {r.dudas.length > 0 && <Text style={e.mini}>{t.noEntendi}: {r.dudas.join(' · ')}</Text>}
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
  valor: { fontSize: ESCALA.h2, fontWeight: '700', color: C.ink, marginTop: 2 },
  comparacion: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderLeftWidth: 4, borderLeftColor: C.block, borderRadius: 16, padding: 16 },
  dosColumnas: { flexDirection: 'row', gap: 16, marginTop: 8 },
  auditoria: { borderRadius: 16, padding: 14, gap: 8 },
  auditoriaTitulo: { fontSize: ESCALA.chico, fontWeight: '600' },
  casillas: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  // Cada verificación en su propio chip blanco (D29): ningún motivo toca la fila de auditoría.
  casilla: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: C.surface, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4 },
  casillaTexto: { fontSize: ESCALA.mini, fontWeight: '500', color: C.ok },
  paso: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  pasoTexto: { fontSize: ESCALA.cuerpo, fontWeight: '500' },
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
