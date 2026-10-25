// Modo emergencia (C11, D35): frases verificadas del banco, toca y suena. Cero espera de modelos.
// La respuesta del paciente vuelve por el turno normal («Escuchar la respuesta»).
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Animated, { FadeInDown, useReducedMotion } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { audioDeFrase, banco } from '@/chaski/api';
import { fraseRevisada, type FraseBanco } from '@/chaski/modelo';
import { MarcaChakana } from '@/chaski/motivos';
import { usePerfil } from '@/chaski/perfil';
import { textos } from '@/chaski/textos';
import { C, ESCALA } from '@/chaski/tokens';
import { Aviso, Boton, Icono } from '@/chaski/ui';

export default function Emergencia() {
  const perfil = usePerfil();
  const t = textos(perfil?.idioma ?? 'castellano');
  const sinMovimiento = useReducedMotion();
  const [frases, setFrases] = useState<FraseBanco[] | null>(null);
  const [origen, setOrigen] = useState<'servicio' | 'local'>('local');
  const [sonando, setSonando] = useState<string | null>(null);
  const [fallo, setFallo] = useState<string | null>(null);
  // La frase tocada, en grande: sin audio grabado todavía, la enfermera la lee o se la muestra al paciente.
  const [grande, setGrande] = useState<FraseBanco | null>(null);
  const listos = useRef(new Map<string, Promise<{ uri: string; headers?: Record<string, string> }>>());
  const reproductor = useAudioPlayer(null);
  const estado = useAudioPlayerStatus(reproductor);

  useEffect(() => {
    banco('emergencia').then(({ frases, origen }) => {
      setFrases(frases);
      setOrigen(origen);
      // Se preparan todos los audios al abrir la pantalla: al tocar, suena sin esperar.
      for (const f of frases) {
        if (fraseRevisada(f)) {
          const p = audioDeFrase(f);
          p.catch(() => {});
          listos.current.set(f.id, p);
        }
      }
    });
  }, []);

  useEffect(() => {
    if (estado.didJustFinish) setSonando(null);
  }, [estado.didJustFinish]);

  async function tocar(f: FraseBanco) {
    setFallo(null);
    if (!fraseRevisada(f)) {
      setFallo(f.id);
      return;
    }
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setGrande(f);
    try {
      const fuente = await (listos.current.get(f.id) ?? audioDeFrase(f));
      reproductor.replace(fuente);
      reproductor.seekTo(0);
      reproductor.play();
      setSonando(f.id);
    } catch {
      setFallo(f.id);
    }
  }


  return (
    <SafeAreaView style={e.pantalla} edges={['bottom']}>
      <View style={e.encabezado}>
        <View style={e.titulo}>
          <MarcaChakana tam={22} />
          <Text style={e.tituloTexto}>{t.emergencia}</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={e.grilla}>
        {(frases ?? []).map((f, i) => {
          const activa = sonando === f.id;
          const lista = fraseRevisada(f);
          return (
            <Animated.View
              key={f.id}
              entering={sinMovimiento ? undefined : FadeInDown.delay(i * 40).springify().damping(18)}
              style={e.celda}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={f.es}
                accessibilityState={{ disabled: !lista }}
                // Seguridad (§6.4): sin revisar o sin quechua, el botón no suena. Se ve, pero está deshabilitado.
                disabled={!lista}
                onPress={() => tocar(f)}
                style={({ pressed }) => [
                  e.boton,
                  activa && { borderColor: C.action, borderWidth: 3, backgroundColor: C.actionTint },
                  pressed && { backgroundColor: C.actionTint },
                  !lista && { opacity: 0.55, backgroundColor: C.ground, borderStyle: 'dashed' },
                ]}>
                <View style={e.filaIcono}>
                  <View style={[e.icono, { backgroundColor: !lista ? C.castellanoTag : activa ? C.action : C.actionTint }]}>
                    <Icono
                      nombre={!lista ? 'speaker.slash.fill' : activa ? 'speaker.wave.3.fill' : 'speaker.wave.2.fill'}
                      color={!lista ? C.inkTertiary : activa ? C.surface : C.action}
                      tam={20}
                    />
                  </View>
                  {lista && f.revisado && (
                    <View style={e.revisado}>
                      <Icono nombre="checkmark.seal.fill" color={C.ok} tam={12} />
                      <Text style={e.revisadoTexto}>{t.revisadaEnfermera}</Text>
                    </View>
                  )}
                </View>
                <Text style={e.es}>{f.es}</Text>
                {lista ? (
                  <Text style={e.quy}>{f.quy}</Text>
                ) : (
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                    <Icono nombre="lock.fill" color={C.inkTertiary} tam={12} />
                    <Text style={e.pendiente}>{t.pendienteRevision}</Text>
                  </View>
                )}
              </Pressable>
              {fallo === f.id && (
                <View style={{ marginTop: 6 }}>
                  <Aviso tipo="warn" texto={lista ? t.sinConexion : t.faltaRevisarAviso} />
                </View>
              )}
            </Animated.View>
          );
        })}
      </ScrollView>

      {grande && (
        <Pressable style={e.velo} onPress={() => setGrande(null)} accessibilityRole="button" accessibilityLabel={t.cerrar}>
          <Animated.View entering={sinMovimiento ? undefined : FadeInDown.springify().damping(18)} style={e.tarjetaGrande}>
            <Text style={e.grandeEtiqueta}>{t.muestreleEsto}</Text>
            <Text style={e.grandeQuy}>{grande.quy}</Text>
            <Text style={e.grandeEs}>{grande.es}</Text>
            {sonando === grande.id ? (
              <View style={e.grandeFila}>
                <Icono nombre="speaker.wave.3.fill" color={C.action} tam={18} />
                <Text style={e.grandeNota}>{t.chaskiLoDice}</Text>
              </View>
            ) : fallo === grande.id ? (
              <Text style={e.grandeNota}>{t.sinVozLeaUsted}</Text>
            ) : null}
            <Boton tipo="secundario" texto={t.cerrar} onPress={() => setGrande(null)} />
          </Animated.View>
        </Pressable>
      )}

      <View style={e.pie}>
        <Boton
          icono="mic.fill"
          texto={t.escucharRespuesta}
          onPress={() => router.replace({ pathname: '/', params: { lado: 'quechua' } })}
        />
        <Boton tipo="texto" texto={t.volverConsulta} onPress={() => router.back()} />
      </View>
    </SafeAreaView>
  );
}

const e = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: C.ground },
  encabezado: { paddingHorizontal: 16, paddingTop: 20, paddingBottom: 8, gap: 6 },
  titulo: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  tituloTexto: { fontSize: ESCALA.h1, fontWeight: '700', color: C.ink },
  secundario: { fontSize: ESCALA.chico, color: C.inkSecondary, lineHeight: 20 },
  grilla: { padding: 16, paddingTop: 8, flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 12 },
  celda: { width: '48.5%' },
  boton: {
    minHeight: 150, borderRadius: 20, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border,
    padding: 14, gap: 8,
  },
  filaIcono: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  revisado: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: C.okTint, borderRadius: 10, paddingHorizontal: 8, paddingVertical: 3 },
  revisadoTexto: { fontSize: 11, fontWeight: '700', color: C.ok },
  icono: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  es: { fontSize: ESCALA.h2, fontWeight: '700', color: C.ink, lineHeight: 25 },
  quy: { fontSize: ESCALA.chico, fontWeight: '600', color: C.quechua },
  pendiente: { fontSize: ESCALA.mini, color: C.inkTertiary },
  pie: { paddingHorizontal: 16, paddingBottom: 8, gap: 8 },
  velo: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(24,34,31,0.45)', justifyContent: 'center', padding: 16 },
  tarjetaGrande: { backgroundColor: C.surface, borderRadius: 28, padding: 24, gap: 14, borderWidth: 1, borderColor: C.border },
  grandeEtiqueta: { fontSize: ESCALA.mini, fontWeight: '700', color: C.inkTertiary, letterSpacing: 0.6 },
  grandeQuy: { fontSize: 34, fontWeight: '800', color: C.quechua, lineHeight: 42 },
  grandeEs: { fontSize: ESCALA.cuerpo, color: C.inkSecondary },
  grandeFila: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  grandeNota: { fontSize: ESCALA.chico, color: C.inkSecondary },
  nota: { fontSize: ESCALA.mini, color: C.inkTertiary, textAlign: 'center' },
});
