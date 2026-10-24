// Onboarding de D27: (1) idioma, (2) nombre, (3) ¿personal de salud o paciente?
// El paso 1 va en los dos idiomas porque todavía no sabemos cuál lee.
import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Chaski } from '@/chaski/chaski';
import { guardarPerfil, type Idioma, type Rol } from '@/chaski/perfil';
import { textos } from '@/chaski/textos';
import { C, ESCALA } from '@/chaski/tokens';
import { Manta } from '@/chaski/manta';
import { Boton, Icono } from '@/chaski/ui';

export default function Bienvenida() {
  const [paso, setPaso] = useState<1 | 2 | 3>(1);
  const [idioma, setIdioma] = useState<Idioma | null>(null);
  const [nombre, setNombre] = useState('');
  const t = textos(idioma ?? 'castellano');

  async function terminar(rol: Rol) {
    await guardarPerfil({ idioma: idioma!, nombre: nombre.trim(), rol });
    router.replace('/');
  }

  return (
    <SafeAreaView style={e.pantalla} edges={['top', 'bottom']}>
      {/* La manta de gala abre la pantalla; Chaski se sienta encima. */}
      <View style={e.heroe}>
        <Manta variante="gala" escala={paso === 1 ? 2.1 : 1.4} />
      </View>
      <KeyboardAvoidingView behavior="padding" style={{ flex: 1 }}>
        <View style={e.cuerpo}>
          <View style={[e.chaskiSobreManta, { marginTop: paso === 1 ? -120 : -90 }]}>
            <Chaski estado="presentarse" tam={paso === 1 ? 210 : 150} />
          </View>
          <Text style={e.marca}>Chaski</Text>
          <View style={e.puntos}>
            {[1, 2, 3].map((n) => <View key={n} style={[e.punto, n <= paso && { backgroundColor: C.action }]} />)}
          </View>

          {paso === 1 && (
            <>
              <Text style={e.pregunta}>¿Qué idioma habla?</Text>
              <Text style={[e.pregunta, { color: C.quechua }]}>¿Ima simitam rimanki?</Text>
              <Opcion titulo="Castellano" onPress={() => { setIdioma('castellano'); setPaso(2); }} />
              <Opcion titulo="Runasimi" detalle="Quechua chanka" quechua onPress={() => { setIdioma('quechua'); setPaso(2); }} />
            </>
          )}

          {paso === 2 && (
            <>
              <Text style={e.pregunta}>{t.suNombre}</Text>
              <TextInput
                value={nombre}
                onChangeText={setNombre}
                placeholder={t.nombreEjemplo}
                placeholderTextColor={C.inkTertiary}
                autoFocus
                autoCapitalize="words"
                returnKeyType="next"
                onSubmitEditing={() => nombre.trim() && setPaso(3)}
                style={e.campo}
              />
              <Boton texto={t.seguir} onPress={() => setPaso(3)} deshabilitado={!nombre.trim()} />
              <Boton tipo="texto" texto={t.volver} onPress={() => setPaso(1)} />
            </>
          )}

          {paso === 3 && (
            <>
              <Text style={e.pregunta}>{t.hola(nombre.trim())}. {t.quienEs}</Text>
              <Opcion icono="cross.case.fill" titulo={t.personal} detalle={t.personalDetalle} onPress={() => terminar('personal')} />
              <Opcion icono="person.fill" titulo={t.paciente} detalle={t.pacienteDetalle} onPress={() => terminar('paciente')} />
              <Boton tipo="texto" texto={t.volver} onPress={() => setPaso(2)} />
            </>
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Opcion({ titulo, detalle, quechua, icono, onPress }: {
  titulo: string; detalle?: string; quechua?: boolean; icono?: 'cross.case.fill' | 'person.fill'; onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [e.opcion, pressed && { backgroundColor: C.actionTint, borderColor: C.action }]}>
      {icono ? <Icono nombre={icono} color={C.action} tam={24} /> : null}
      <View style={{ flex: 1 }}>
        <Text style={[e.opcionTitulo, quechua && { color: C.quechua }]}>{titulo}</Text>
        {detalle ? <Text style={e.opcionDetalle}>{detalle}</Text> : null}
      </View>
      <Icono nombre="chevron.right" color={C.inkTertiary} tam={16} />
    </Pressable>
  );
}

const e = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: C.ground },
  cuerpo: { flex: 1, padding: 16, gap: 12 },
  heroe: { overflow: 'hidden' },
  chaskiSobreManta: { alignSelf: 'center', padding: 6, borderRadius: 34, backgroundColor: C.ground },
  marca: { fontSize: ESCALA.display, fontWeight: '700', color: C.ink, textAlign: 'center' },
  puntos: { flexDirection: 'row', gap: 6, justifyContent: 'center', marginBottom: 8 },
  punto: { width: 8, height: 8, borderRadius: 4, backgroundColor: C.border },
  pregunta: { fontSize: ESCALA.h1, fontWeight: '700', color: C.ink, textAlign: 'center' },
  opcion: { flexDirection: 'row', alignItems: 'center', gap: 14, minHeight: 72, paddingHorizontal: 18, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20 },
  opcionTitulo: { fontSize: ESCALA.h2, fontWeight: '700', color: C.ink },
  opcionDetalle: { fontSize: ESCALA.mini, color: C.inkSecondary, marginTop: 2 },
  campo: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, padding: 16, fontSize: ESCALA.h2, color: C.ink, textAlign: 'center' },
});
