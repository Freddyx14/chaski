// F9 + F6 (§5, D35): foto de la receta o la caja → Claude la lee → la enfermera confirma los datos →
// la indicación se arma con una plantilla desde esos datos → se traduce, se audita y se dice →
// «¿me lo repite?»: el paciente la repite y el código marca qué entendió y qué no.
// Nada se adivina: lo que la foto no dice, lo confirma la enfermera; sin todos los datos, no se dice.
import {
  setAudioModeAsync, useAudioPlayer, useAudioRecorder, requestRecordingPermissionsAsync,
} from 'expo-audio';
import * as Haptics from 'expo-haptics';
import * as ImagePicker from 'expo-image-picker';
import { Image } from 'expo-image';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import Animated, { FadeInDown, useReducedMotion } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { turnoEnfermera, turnoPaciente, ver, voz, type Lectura } from '@/chaski/api';
import { Chaski } from '@/chaski/chaski';
import { agregarTurno, useTurnos } from '@/chaski/consulta';
import { GRABACION } from '@/chaski/grabacion';
import { leerInterprete, veredictoEnfermera, type Veredicto } from '@/chaski/modelo';
import { MarcaChaski } from '@/chaski/motivos';
import { usePerfil } from '@/chaski/perfil';
import {
  comprobarRepeticion, faltantes, indicacionDesdeHechos, type Comprobacion, type HechosReceta,
} from '@/chaski/receta';
import { textos } from '@/chaski/textos';
import { C, ESCALA } from '@/chaski/tokens';
import { Aviso, Boton, Etiqueta, Icono, Tarjeta } from '@/chaski/ui';

type Paso =
  | { p: 'foto' }
  | { p: 'leyendo' }
  | { p: 'datos' }
  | { p: 'diciendo' }
  | { p: 'dicho'; v: Extract<Veredicto, { tipo: 'dicho' | 'dicho_con_aviso' }> }
  | { p: 'bloqueado'; v: Extract<Veredicto, { tipo: 'bloqueado' }> }
  | { p: 'repite' }
  | { p: 'juzgando' }
  | { p: 'resultado'; checks: Comprobacion[]; dijo: string };

const UNIDADES = ['pastilla', 'cápsula', 'cucharada', 'gotas', 'sobre'];
const CANTIDADES = [0.5, 1, 2, 3];
const HORAS = [4, 6, 8, 12, 24];
const DIAS = [1, 3, 5, 7, 10, 14];

const VACIOS: HechosReceta = { medicamento: '', concentracion: null, cantidad: null, unidad: 'pastilla', cada_horas: null, dias: null };

// Demo: /receta?demo=datos|dicho|resultado, sin servicio.
const DEMO_HECHOS: HechosReceta = { medicamento: 'paracetamol', concentracion: '500 mg', cantidad: 1, unidad: 'pastilla', cada_horas: 8, dias: 3 };
const DEMO_LECTURA: Lectura = {
  seguro: true, medicamento: 'Paracetamol', concentracion: '500 mg', presentacion: 'Caja de 20 tabletas',
  para_que_sirve: 'Baja la fiebre y calma el dolor.', advertencias: [], no_leido: ['cada cuántas horas', 'por cuántos días'],
  coincide_con_lo_dicho: null, segundos: 2.3,
};

export default function Pantalla() {
  // Cada enlace de demo arranca la pantalla de cero.
  const q = useLocalSearchParams<{ demo?: string }>();
  return <Receta key={q.demo ?? 'receta'} />;
}

function Receta() {
  const perfil = usePerfil();
  const t = textos(perfil?.idioma ?? 'castellano');
  const rol = perfil?.rol ?? 'personal';
  const q = useLocalSearchParams<{ demo?: string }>();
  const sinMovimiento = useReducedMotion();
  const turnos = useTurnos();
  const dicho = [...turnos].reverse().find((x) => x.lado === 'castellano')?.castellano ?? '';

  const demo = q.demo;
  const [foto, setFoto] = useState<string | null>(null);
  const [lectura, setLectura] = useState<Lectura | null>(demo ? DEMO_LECTURA : null);
  const [hechos, setHechos] = useState<HechosReceta>(demo ? DEMO_HECHOS : VACIOS);
  const [paso, setPaso] = useState<Paso>(
    demo === 'dicho'
      ? { p: 'dicho', v: veredictoEnfermera(indicacionDesdeHechos(DEMO_HECHOS), {
          quechua: '[Indicación en quechua chanka]', retraduccion: '', aprobado_por_auditoria: true, motivo: null,
          terminos_inseguros: [], diferencias: [], se_dice: true, aviso: null, total_ms: 0 }) as Extract<Veredicto, { tipo: 'dicho' }> }
      : demo === 'resultado'
        ? { p: 'resultado', dijo: 'Tomo una pastilla cada ocho horas', checks: comprobarRepeticion(DEMO_HECHOS, 'Tomo una pastilla cada ocho horas') }
        : demo ? { p: 'datos' } : { p: 'foto' },
  );
  const [error, setError] = useState<string | null>(null);
  // Lo último que se dijo, para volver a explicarlo después de «¿me lo repite?».
  const [ultimo, setUltimo] = useState<Extract<Veredicto, { tipo: 'dicho' | 'dicho_con_aviso' }> | null>(
    paso.p === 'dicho' ? paso.v : null,
  );

  const grabadora = useAudioRecorder(GRABACION);
  const reproductor = useAudioPlayer(null);

  useEffect(() => {
    (async () => {
      await requestRecordingPermissionsAsync();
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
    })();
  }, []);

  async function tomar(camara: boolean) {
    const permiso = camara
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permiso.granted) return;
    const opciones: ImagePicker.ImagePickerOptions = { mediaTypes: ['images'], quality: 0.7 };
    const r = camara ? await ImagePicker.launchCameraAsync(opciones) : await ImagePicker.launchImageLibraryAsync(opciones);
    if (r.canceled) return;
    const uri = r.assets[0].uri;
    setFoto(uri);
    setError(null);
    setPaso({ p: 'leyendo' });
    try {
      const l = await ver(uri, dicho);
      setLectura(l);
      // Solo se prellena lo que la foto dijo con seguridad. Lo demás queda vacío para que la enfermera lo confirme.
      setHechos({
        medicamento: l.seguro && l.medicamento ? l.medicamento : '',
        concentracion: l.seguro ? l.concentracion : null,
        cantidad: l.cantidad ?? null,
        unidad: l.unidad ?? 'pastilla',
        cada_horas: l.cada_horas ?? null,
        dias: l.dias ?? null,
      });
      setPaso({ p: 'datos' });
    } catch {
      setError(t.sinConexion);
      setPaso({ p: 'foto' });
    }
  }

  async function decirAlPaciente() {
    if (faltantes(hechos).length) return;
    const texto = indicacionDesdeHechos(hechos);
    setError(null);
    setPaso({ p: 'diciendo' });
    try {
      const r = await turnoEnfermera(texto, rol);
      // Una indicación de receta solo se dice traducida y auditada; cualquier otra acción del intérprete la frena.
      const ia = leerInterprete(r);
      if (ia.tipo !== 'traducir') {
        setError('Chaski no la dijo: revise los datos y vuelva a intentarlo.');
        setPaso({ p: 'datos' });
        return;
      }
      const v = veredictoEnfermera(texto, r);
      agregarTurno({ lado: 'castellano', castellano: texto, quechua: r.quechua, estado: v.tipo });
      if (v.tipo === 'bloqueado') {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        setPaso({ p: 'bloqueado', v });
        return;
      }
      setPaso({ p: 'dicho', v });
      setUltimo(v);
      const { uri } = await voz(v.quechua);
      reproductor.replace({ uri });
      reproductor.play();
    } catch {
      setError(t.sinConexion);
      setPaso({ p: 'datos' });
    }
  }

  async function empezarRepite() {
    reproductor.pause();
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    await grabadora.prepareToRecordAsync();
    grabadora.record();
    setPaso({ p: 'repite' });
  }

  async function terminarRepite() {
    await grabadora.stop();
    const uri = grabadora.uri;
    if (!uri) return;
    setPaso({ p: 'juzgando' });
    try {
      const r = await turnoPaciente(uri, rol);
      agregarTurno({ lado: 'quechua', castellano: r.castellano, quechua: r.chanka_oido, estado: r.seguro ? 'entendido' : 'con_dudas' });
      setPaso({ p: 'resultado', checks: comprobarRepeticion(hechos, r.castellano), dijo: r.castellano });
    } catch {
      setError(t.sinConexion);
      setPaso(ultimo ? { p: 'dicho', v: ultimo } : { p: 'datos' });
    }
  }

  function repetirAudio() {
    reproductor.seekTo(0);
    reproductor.play();
  }

  const falta = faltantes(hechos);
  const estadoChaski = paso.p === 'leyendo' || paso.p === 'diciendo' || paso.p === 'juzgando' ? 'pensando'
    : paso.p === 'repite' ? 'escuchando'
      : paso.p === 'bloqueado' || (lectura && !lectura.seguro) ? 'no_entendi' : 'reposo';
  const entrar = sinMovimiento ? undefined : FadeInDown.springify().damping(18);

  return (
    <SafeAreaView style={e.pantalla} edges={['top', 'bottom']}>
      <View style={e.encabezado}>
        <MarcaChaski />
      </View>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 14 }} keyboardShouldPersistTaps="handled">
        <View style={e.fila}>
          <Chaski estado={estadoChaski} tam={96} />
          <View style={{ flex: 1, gap: 4 }}>
            <Text style={e.titulo}>
              {paso.p === 'resultado' || paso.p === 'repite' || paso.p === 'juzgando' ? t.meLoRepite : 'Leer la receta o la caja'}
            </Text>
            <Text style={e.secundario}>
              {paso.p === 'repite' || paso.p === 'juzgando' || paso.p === 'resultado' ? t.meLoRepiteExplica : 'Chaski la lee, usted confirma y Chaski se la explica al paciente.'}
            </Text>
          </View>
        </View>

        {foto && paso.p !== 'resultado' && <Image source={{ uri: foto }} style={e.foto} contentFit="cover" />}
        {paso.p === 'leyendo' && <Aviso tipo="warn" texto="Leyendo la foto…" />}
        {error && <Aviso tipo="warn" texto={error} />}

        {/* Lo que la foto dijo */}
        {lectura && (paso.p === 'datos' || paso.p === 'diciendo') && (
          <Animated.View entering={entrar}>
            <Tarjeta estilo={{ gap: 6 }}>
              {lectura.seguro ? (
                <>
                  <Text style={e.rotulo}>LO QUE DICE LA CAJA</Text>
                  <Text style={e.grande}>{[lectura.medicamento, lectura.concentracion].filter(Boolean).join(' ')}</Text>
                  {lectura.para_que_sirve ? <Text style={e.secundario}>{lectura.para_que_sirve}</Text> : null}
                  {lectura.coincide_con_lo_dicho === false && (
                    <Aviso tipo="warn" texto="No coincide con lo que usted dijo. Revise antes de seguir." />
                  )}
                  {lectura.advertencias.map((a, i) => <Aviso key={i} tipo="warn" texto={a} />)}
                </>
              ) : (
                <Text style={[e.grande, { color: C.warn }]}>No lo leo con seguridad</Text>
              )}
              {lectura.no_leido.length > 0 && (
                <Text style={e.mini}>No pude leer: {lectura.no_leido.join(' · ')}</Text>
              )}
            </Tarjeta>
          </Animated.View>
        )}

        {/* La enfermera confirma: nada se adivina */}
        {(paso.p === 'datos' || paso.p === 'diciendo') && (
          <Animated.View entering={entrar}>
            <Tarjeta estilo={{ gap: 14 }}>
              <View style={{ gap: 4 }}>
                <Text style={e.subtitulo}>{t.confirmeDatos}</Text>
                <Text style={e.mini}>{t.confirmeDatosExplica}</Text>
              </View>
              <View style={{ gap: 6 }}>
                <Text style={e.rotulo}>MEDICAMENTO</Text>
                <TextInput
                  value={hechos.medicamento}
                  onChangeText={(m) => setHechos({ ...hechos, medicamento: m })}
                  placeholder="Nombre del medicamento"
                  placeholderTextColor={C.inkTertiary}
                  style={e.campo}
                />
              </View>
              <Opciones titulo={t.cuantoPorToma.toUpperCase()} valores={CANTIDADES} actual={hechos.cantidad}
                etiqueta={(v) => (v === 0.5 ? '½' : String(v))} alElegir={(v) => setHechos({ ...hechos, cantidad: v })} />
              <Opciones titulo="DE" valores={UNIDADES} actual={hechos.unidad} etiqueta={(v) => v}
                alElegir={(v) => setHechos({ ...hechos, unidad: v })} />
              <Opciones titulo={t.cadaCuantasHoras.toUpperCase()} valores={HORAS} actual={hechos.cada_horas}
                etiqueta={(v) => (v === 24 ? '1 vez al día' : `${v} h`)} alElegir={(v) => setHechos({ ...hechos, cada_horas: v })} />
              <Opciones titulo={t.porCuantosDias.toUpperCase()} valores={DIAS} actual={hechos.dias}
                etiqueta={(v) => `${v} ${v === 1 ? 'día' : 'días'}`} alElegir={(v) => setHechos({ ...hechos, dias: v })} />
            </Tarjeta>
          </Animated.View>
        )}

        {(paso.p === 'datos' || paso.p === 'diciendo') && falta.length === 0 && (
          <Tarjeta>
            <Etiqueta idioma="castellano" />
            <Text style={[e.cuerpo, { marginTop: 8 }]}>{indicacionDesdeHechos(hechos)}</Text>
          </Tarjeta>
        )}

        {/* Dicho, auditado */}
        {paso.p === 'dicho' && (
          <Animated.View entering={entrar} style={{ gap: 12 }}>
            <View style={{ alignItems: 'center' }}><Etiqueta idioma="quechua" /></View>
            <Tarjeta estilo={{ gap: 8 }}>
              {paso.v.quechua ? <Text style={e.quechua}>{paso.v.quechua}</Text> : null}
              <Text style={e.secundario}>{paso.v.castellano}</Text>
            </Tarjeta>
            {paso.v.casillas.length > 0 && (
              <View style={[e.auditoria, { backgroundColor: C.okTint }]}>
                <View style={e.filaChica}>
                  <Icono nombre="checkmark.shield.fill" color={C.ok} tam={18} />
                  <Text style={[e.auditoriaTitulo, { color: C.ok }]}>{t.auditado}</Text>
                </View>
              </View>
            )}
            {paso.v.tipo === 'dicho_con_aviso' && <Aviso tipo="warn" texto={t.dichoConAvisoSolo} />}
          </Animated.View>
        )}

        {paso.p === 'bloqueado' && (
          <Animated.View entering={entrar} style={{ gap: 10 }}>
            <Text style={[e.grande, { color: C.block, textAlign: 'center' }]}>{t.noLoDije}</Text>
            {paso.v.diferencias.map((d, i) => (
              <Aviso key={i} tipo="block" texto={`${d.nombre}: usted ${d.dijo}, la traducción ${d.decia}`} />
            ))}
          </Animated.View>
        )}

        {paso.p === 'repite' && <Aviso tipo="ok" texto={t.escuchando} />}
        {paso.p === 'juzgando' && <Aviso tipo="warn" texto="Comparando con la indicación…" />}

        {/* «¿Me lo repite?»: la pantalla 6 del tablero */}
        {paso.p === 'resultado' && (
          <Animated.View entering={entrar} style={{ gap: 12 }}>
            <Text style={e.titulo}>{t.loQueEntendio}</Text>
            <Tarjeta estilo={{ paddingVertical: 4 }}>
              {paso.checks.map((c, i) => (
                <Animated.View
                  key={c.nombre}
                  entering={sinMovimiento ? undefined : FadeInDown.delay(i * 120).springify().damping(18)}
                  style={[e.check, i > 0 && { borderTopWidth: 1, borderTopColor: C.border }]}>
                  <View style={[e.circulo, { backgroundColor: c.ok ? C.okTint : C.blockTint }]}>
                    <Icono nombre={c.ok ? 'checkmark' : 'xmark'} color={c.ok ? C.ok : C.block} tam={14} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[e.cuerpo, !c.ok && { color: C.block }]}>{c.nombre}</Text>
                    {!c.ok && <Text style={e.noMenciono}>{t.noLoMenciono}</Text>}
                  </View>
                </Animated.View>
              ))}
            </Tarjeta>
            <Text style={e.subtitulo}>{t.entendidos(paso.checks.filter((c) => c.ok).length, paso.checks.length)}</Text>
            {paso.dijo ? <Text style={e.mini}>Dijo: «{paso.dijo}»</Text> : null}
          </Animated.View>
        )}
      </ScrollView>

      <View style={e.pie}>
        {(paso.p === 'foto' || paso.p === 'leyendo') && (
          <View style={{ flexDirection: 'row', gap: 12 }}>
            <Boton icono="camera.fill" texto="Tomar foto" onPress={() => tomar(true)} flex deshabilitado={paso.p === 'leyendo'} />
            <Boton tipo="secundario" icono="photo" texto="Galería" onPress={() => tomar(false)} flex deshabilitado={paso.p === 'leyendo'} />
          </View>
        )}
        {(paso.p === 'datos' || paso.p === 'diciendo') && (
          <>
            {falta.length > 0 && <Text style={e.falta}>{t.faltaParaDecir(falta.join(', '))}</Text>}
            <Boton icono="speaker.wave.2.fill" texto={paso.p === 'diciendo' ? 'Traduciendo y revisando…' : t.decirAlPaciente}
              onPress={decirAlPaciente} deshabilitado={falta.length > 0 || paso.p === 'diciendo'} />
          </>
        )}
        {paso.p === 'dicho' && (
          <View style={{ flexDirection: 'row', gap: 12 }}>
            <Boton tipo="secundario" icono="speaker.wave.2.fill" texto={t.repetirAudio} onPress={repetirAudio} flex />
            <Boton icono="mic.fill" texto={t.meLoRepite} onPress={empezarRepite} flex />
          </View>
        )}
        {paso.p === 'bloqueado' && <Boton texto={t.decirloOtraForma} onPress={() => setPaso({ p: 'datos' })} />}
        {paso.p === 'repite' && <Boton icono="stop.fill" texto={t.tocarTerminar} onPress={terminarRepite} />}
        {paso.p === 'resultado' && (
          <>
            {paso.checks.some((c) => !c.ok) && (
              <Boton icono="speaker.wave.2.fill" texto={t.explicarLoQueFalto} onPress={() => { repetirAudio(); setPaso(ultimo ? { p: 'dicho', v: ultimo } : { p: 'datos' }); }} />
            )}
            <Boton tipo="secundario" texto={t.volverConsulta} onPress={() => router.back()} />
          </>
        )}
        {paso.p !== 'resultado' && <Boton tipo="texto" texto={t.volverConsulta} onPress={() => router.back()} />}
      </View>
    </SafeAreaView>
  );
}

/** Una fila de opciones grandes. Ninguna está elegida hasta que la enfermera la toca. */
function Opciones<T extends string | number>({ titulo, valores, actual, etiqueta, alElegir }: {
  titulo: string; valores: T[]; actual: T | null; etiqueta: (v: T) => string; alElegir: (v: T) => void;
}) {
  return (
    <View style={{ gap: 6 }}>
      <Text style={e.rotulo}>{titulo}</Text>
      <View style={e.opciones}>
        {valores.map((v) => {
          const activo = v === actual;
          return (
            <Pressable
              key={String(v)}
              accessibilityRole="button"
              accessibilityState={{ selected: activo }}
              onPress={() => alElegir(v)}
              style={[e.opcion, activo && { backgroundColor: C.action, borderColor: C.action }]}>
              <Text style={[e.opcionTexto, activo && { color: C.surface }]}>{etiqueta(v)}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const e = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: C.ground },
  encabezado: { paddingHorizontal: 16, paddingTop: 10 },
  fila: { flexDirection: 'row', gap: 14, alignItems: 'center' },
  filaChica: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  titulo: { fontSize: ESCALA.h2, fontWeight: '700', color: C.ink },
  subtitulo: { fontSize: ESCALA.cuerpo, fontWeight: '700', color: C.ink },
  secundario: { fontSize: ESCALA.chico, color: C.inkSecondary, lineHeight: 20 },
  mini: { fontSize: ESCALA.mini, color: C.inkTertiary, lineHeight: 18 },
  rotulo: { fontSize: ESCALA.mini, fontWeight: '600', color: C.inkTertiary, letterSpacing: 0.6 },
  cuerpo: { fontSize: ESCALA.cuerpo, color: C.ink, lineHeight: 23 },
  grande: { fontSize: ESCALA.h1, fontWeight: '700', color: C.ink },
  quechua: { fontSize: ESCALA.h1, fontWeight: '600', color: C.ink, lineHeight: 31 },
  foto: { width: '100%', aspectRatio: 16 / 9, borderRadius: 20, borderWidth: 1, borderColor: C.border },
  campo: { backgroundColor: C.ground, borderWidth: 1, borderColor: C.border, borderRadius: 14, padding: 12, fontSize: ESCALA.cuerpo, color: C.ink },
  opciones: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  opcion: { minHeight: 44, minWidth: 56, paddingHorizontal: 14, borderRadius: 22, borderWidth: 1, borderColor: C.border, backgroundColor: C.surface, alignItems: 'center', justifyContent: 'center' },
  opcionTexto: { fontSize: ESCALA.chico, fontWeight: '600', color: C.ink },
  auditoria: { borderRadius: 16, padding: 14 },
  auditoriaTitulo: { fontSize: ESCALA.chico, fontWeight: '600' },
  check: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 56, paddingVertical: 8 },
  circulo: { width: 28, height: 28, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  noMenciono: { fontSize: ESCALA.mini, fontWeight: '600', color: C.warn, marginTop: 2 },
  pie: { padding: 16, gap: 8 },
  falta: { fontSize: ESCALA.mini, color: C.warn, textAlign: 'center', fontWeight: '600' },
});
