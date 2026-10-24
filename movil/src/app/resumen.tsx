// F11: el cierre de la consulta. El personal ve la nota para la historia clínica y lo que falta revisar;
// el paciente ve lo que tiene que hacer en casa y lo puede escuchar en quechua, siempre por la auditoría.
import { useAudioPlayer } from 'expo-audio';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { resumen as pedirResumen, turnoEnfermera, voz, type Resumen } from '@/chaski/api';
import { Chaski } from '@/chaski/chaski';
import { nuevaConsulta, useTurnos } from '@/chaski/consulta';
import { usePerfil } from '@/chaski/perfil';
import { C, ESCALA } from '@/chaski/tokens';
import { Manta } from '@/chaski/manta';
import { Aviso, Boton, Tarjeta } from '@/chaski/ui';

const EJEMPLO: Resumen = {
  rol: 'personal',
  resumen: 'Paciente con fiebre de dos días. Se indicó paracetamol y control en tres días.',
  indicaciones: ['Una pastilla de paracetamol cada 8 horas, durante 3 días'],
  senales_de_alarma: ['la fiebre no baja en dos días'],
  proxima_cita: 'en 3 días',
  dudas: ['qué hacer si olvida la dosis de la noche'],
  no_se_dijo: ['Tome dos juntas si le duele mucho.'],
  texto_para_decir: '',
};

export default function PantallaResumen() {
  const turnos = useTurnos();
  const perfil = usePerfil();
  const q = useLocalSearchParams<{ demo?: string; rol?: string }>();
  const rol = q.rol === 'paciente' ? 'paciente' : q.rol === 'personal' ? 'personal' : perfil?.rol ?? 'personal';
  const [r, setR] = useState<Resumen | null>(q.demo ? { ...EJEMPLO, rol } : null);
  const [error, setError] = useState(false);
  const [voz_, setVoz] = useState<'nada' | 'preparando' | 'lista' | 'no_segura'>('nada');
  const reproductor = useAudioPlayer(null);

  useEffect(() => {
    if (q.demo) return;
    pedirResumen(turnos.map(({ lado, castellano, quechua, estado }) => ({ lado, castellano, quechua, estado })), rol)
      .then(setR)
      .catch(() => setError(true));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function escuchar() {
    if (!r?.texto_para_decir) return;
    setVoz('preparando');
    try {
      // El resumen pasa por la misma auditoría que cualquier turno antes de decirse en quechua.
      const t = await turnoEnfermera(r.texto_para_decir, rol);
      if (!t.se_dice) return setVoz('no_segura');
      const { uri } = await voz(t.quechua);
      reproductor.replace({ uri });
      reproductor.play();
      setVoz('lista');
    } catch {
      setVoz('nada');
      setError(true);
    }
  }

  function terminar() {
    nuevaConsulta();
    router.dismissTo('/');
  }

  const paraPaciente = rol === 'paciente';
  return (
    <SafeAreaView style={e.pantalla} edges={['top', 'bottom']}>
      <Manta variante="faja" escala={1.3} />
      <ScrollView contentContainerStyle={{ padding: 16, gap: 12 }}>
        <View style={e.fila}>
          <Chaski estado={r ? 'presentarse' : error ? 'no_entendi' : 'pensando'} tam={96} />
          <View style={{ flex: 1, gap: 4 }}>
            <Text style={e.titulo}>{paraPaciente ? 'Lo que tiene que hacer en casa' : 'Resumen de la consulta'}</Text>
            <Text style={e.secundario}>
              {r ? (paraPaciente ? 'Solo lo que le dijeron en la consulta.' : 'Para la historia clínica.')
                : error ? 'No pude preparar el resumen.' : 'Preparando el resumen…'}
            </Text>
          </View>
        </View>

        {r && (
          <>
            {!paraPaciente && (
              <Tarjeta>
                <Text style={e.rotulo}>NOTA</Text>
                <Text style={e.cuerpo}>{r.resumen}</Text>
              </Tarjeta>
            )}
            <Tarjeta estilo={{ gap: 10 }}>
              <Text style={e.rotulo}>INDICACIONES</Text>
              {r.indicaciones.length ? r.indicaciones.map((i, n) => (
                <View key={n} style={e.item}>
                  <Text style={e.numero}>{n + 1}</Text>
                  <Text style={[e.cuerpo, { flex: 1 }]}>{i}</Text>
                </View>
              )) : <Text style={e.secundario}>No hubo indicaciones.</Text>}
              {r.proxima_cita ? <Text style={e.cuerpo}>Próximo control: {r.proxima_cita}</Text> : null}
            </Tarjeta>
            {r.senales_de_alarma.length > 0 && (
              <Tarjeta estilo={{ gap: 8 }}>
                <Text style={e.rotulo}>VENGA DE INMEDIATO SI</Text>
                {r.senales_de_alarma.map((s, n) => <Aviso key={n} tipo="warn" texto={s} />)}
              </Tarjeta>
            )}
            {!paraPaciente && r.no_se_dijo.length > 0 && (
              <Tarjeta estilo={{ gap: 8 }}>
                <Text style={[e.rotulo, { color: C.block }]}>CHASKI NO LO DIJO AL PACIENTE</Text>
                {r.no_se_dijo.map((s, n) => <Aviso key={n} tipo="block" texto={s} />)}
              </Tarjeta>
            )}
            {!paraPaciente && r.dudas.length > 0 && (
              <Tarjeta estilo={{ gap: 8 }}>
                <Text style={e.rotulo}>POR CONFIRMAR</Text>
                {r.dudas.map((s, n) => <Aviso key={n} tipo="warn" texto={s} />)}
              </Tarjeta>
            )}
            {voz_ === 'no_segura' && <Aviso tipo="warn" texto="La auditoría no aprobó decirlo en quechua. Pídale al personal que lo repita." />}
          </>
        )}
      </ScrollView>
      <View style={{ padding: 16, gap: 8 }}>
        {r && r.texto_para_decir ? (
          <Boton
            icono="speaker.wave.2.fill"
            texto={voz_ === 'preparando' ? 'Preparando…' : 'Escuchar en quechua'}
            onPress={escuchar}
            deshabilitado={voz_ === 'preparando'}
          />
        ) : null}
        <Boton tipo="secundario" texto="Terminar consulta" onPress={terminar} />
        <Boton tipo="texto" texto="Volver a la consulta" onPress={() => router.back()} />
      </View>
    </SafeAreaView>
  );
}

const e = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: C.ground },
  fila: { flexDirection: 'row', gap: 14, alignItems: 'center' },
  titulo: { fontSize: ESCALA.h2, fontWeight: '700', color: C.ink },
  secundario: { fontSize: ESCALA.chico, color: C.inkSecondary, lineHeight: 20 },
  rotulo: { fontSize: ESCALA.mini, fontWeight: '600', color: C.inkTertiary, letterSpacing: 0.6 },
  cuerpo: { fontSize: ESCALA.cuerpo, color: C.ink, lineHeight: 23 },
  item: { flexDirection: 'row', gap: 10, alignItems: 'flex-start' },
  numero: { width: 26, height: 26, borderRadius: 13, backgroundColor: C.actionTint, color: C.action, textAlign: 'center', lineHeight: 26, fontWeight: '700', overflow: 'hidden' },
});
