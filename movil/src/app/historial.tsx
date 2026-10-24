// La conversación de la consulta, para volver atrás sin repetir el turno (ajuste 8 de D26).
import { router } from 'expo-router';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { nuevaConsulta, useTurnos } from '@/rimay/consulta';
import type { Turno } from '@/rimay/modelo';
import { C, ESCALA } from '@/rimay/tokens';
import { Aviso, Boton, Etiqueta, Tarjeta } from '@/rimay/ui';

const AVISO: Record<Turno['estado'], { tipo: 'ok' | 'warn' | 'block'; texto: string }> = {
  dicho: { tipo: 'ok', texto: 'Auditado y dicho' },
  dicho_con_aviso: { tipo: 'warn', texto: 'Dicho con aviso' },
  bloqueado: { tipo: 'block', texto: 'No se dijo' },
  entendido: { tipo: 'ok', texto: 'Entendido' },
  con_dudas: { tipo: 'warn', texto: 'Con dudas' },
};

export default function Historial() {
  const turnos = useTurnos();
  return (
    <SafeAreaView style={e.pantalla} edges={['top', 'bottom']}>
      <View style={e.encabezado}>
        <Text style={e.titulo}>La conversación</Text>
        <Boton tipo="texto" texto="Cerrar" onPress={() => router.back()} />
      </View>
      <FlatList
        data={[...turnos].reverse()}
        keyExtractor={(t) => String(t.id)}
        contentContainerStyle={{ padding: 16, gap: 12 }}
        ListEmptyComponent={<Text style={e.vacio}>Todavía no hay turnos en esta consulta.</Text>}
        renderItem={({ item: t }) => (
          <Tarjeta estilo={{ gap: 8 }}>
            <View style={e.fila}>
              <Text style={e.quien}>{t.lado === 'enfermera' ? 'Enfermera' : 'Paciente'}</Text>
              <Text style={e.hora}>{t.hora.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })}</Text>
            </View>
            {t.lado === 'enfermera' ? (
              <>
                <Text style={e.texto}>{t.castellano}</Text>
                {t.estado !== 'bloqueado' && <Etiqueta idioma="quechua" />}
                {t.estado !== 'bloqueado' && <Text style={e.secundario}>{t.quechua}</Text>}
              </>
            ) : (
              <>
                <Etiqueta idioma="quechua" />
                <Text style={e.secundario}>{t.quechua}</Text>
                <Text style={e.texto}>{t.castellano}</Text>
              </>
            )}
            <Aviso {...AVISO[t.estado]} />
          </Tarjeta>
        )}
      />
      <View style={{ padding: 16 }}>
        <Boton tipo="secundario" texto="Terminar consulta" onPress={() => { nuevaConsulta(); router.back(); }} />
      </View>
    </SafeAreaView>
  );
}

const e = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: C.ground },
  encabezado: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingTop: 12 },
  titulo: { fontSize: ESCALA.h1, fontWeight: '700', color: C.ink },
  fila: { flexDirection: 'row', justifyContent: 'space-between' },
  quien: { fontSize: ESCALA.mini, fontWeight: '600', color: C.inkTertiary, letterSpacing: 0.6 },
  hora: { fontSize: ESCALA.mini, color: C.inkTertiary, fontVariant: ['tabular-nums'] },
  texto: { fontSize: ESCALA.cuerpo, color: C.ink, lineHeight: 23 },
  secundario: { fontSize: ESCALA.chico, color: C.inkSecondary, lineHeight: 20 },
  vacio: { fontSize: ESCALA.chico, color: C.inkSecondary, textAlign: 'center', marginTop: 40 },
});
