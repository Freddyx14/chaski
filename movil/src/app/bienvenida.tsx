// Onboarding de D27: (1) idioma, (2) nombre, (3) ¿personal de salud o paciente?
// El paso 1 va en los dos idiomas porque todavía no sabemos cuál lee.
import { router } from 'expo-router';
import { useAudioPlayer } from 'expo-audio';
import { useEffect, useState } from 'react';
import { KeyboardAvoidingView, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { audioDeFrase } from '@/chaski/api';
import { Chaski } from '@/chaski/chaski';
import bancoReal from '../../../app/chaski/banco.json';
import { guardarPerfil, type Idioma, type Rol } from '@/chaski/perfil';
import { textos } from '@/chaski/textos';
import { C, ESCALA, M } from '@/chaski/tokens';
import { ColumnaDeCruces, FilaDeCruces, ProgresoCruces } from '@/chaski/motivos';
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
      <KeyboardAvoidingView behavior="padding" style={{ flex: 1 }}>
        <View style={e.cuerpo}>
          <View style={{ alignSelf: 'center', marginTop: 8 }}>
            <Chaski estado="presentarse" tam={paso === 1 ? 230 : 160} />
          </View>
          <Text style={e.marca}>Chaski</Text>
          <ProgresoCruces total={3} actual={paso} />

          {paso === 1 && <Saludo />}

          {paso === 1 && (
            <>
              <Text style={e.pregunta}>¿Qué idioma habla?</Text>
              <Text style={[e.pregunta, { color: C.quechua, marginTop: -6 }]}>¿Ima simitam rimanki?</Text>
              <View style={{ marginTop: 14 }}><FilaDeCruces /></View>
              <Opcion cruces={M.cobalto} titulo="Castellano" onPress={() => { setIdioma('castellano'); setPaso(2); }} />
              <Opcion cruces={C.quechua} titulo="Runasimi" detalle="Quechua chanka" quechua onPress={() => { setIdioma('quechua'); setPaso(2); }} />
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

// El saludo de Chaski (principio «llegar rápido al ajá»): lo primero que oye quien abre la app es a Chaski
// hablando quechua. Es una frase revisada por la enfermera de Pilpichaca (banco, `revisado: true`); su nota
// aclara que dice «no se preocupe, aquí estamos». Si el audio no llega, el texto basta.
const SALUDO = (bancoReal as { id: string; quy: string; revisado?: boolean; audio?: string; tags?: string[]; es: string }[])
  .find((f) => f.id === 'emg-tranquilo' && f.revisado);

function Saludo() {
  const reproductor = useAudioPlayer(null);
  const [listo, setListo] = useState(false);
  async function sonar() {
    if (!SALUDO) return;
    try {
      reproductor.replace(await audioDeFrase(SALUDO as never));
      reproductor.seekTo(0);
      reproductor.play();
      setListo(true);
    } catch {}
  }
  useEffect(() => { sonar(); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  if (!SALUDO) return null;
  return (
    <View style={e.saludo}>
      <Text style={e.saludoEtiqueta}>CHASKI TE SALUDA</Text>
      <Text style={e.saludoQuy}>{SALUDO.quy}</Text>
      <Text style={e.saludoEs}>No se preocupe, aquí estamos.</Text>
      {listo && (
        <Pressable onPress={sonar} style={e.saludoBoton} accessibilityRole="button">
          <Icono nombre="speaker.wave.2.fill" color={C.action} tam={14} />
          <Text style={e.saludoBotonTexto}>Escuchar de nuevo</Text>
        </Pressable>
      )}
    </View>
  );
}

function Opcion({ titulo, detalle, quechua, icono, cruces, onPress }: {
  titulo: string; detalle?: string; quechua?: boolean; icono?: 'cross.case.fill' | 'person.fill'; cruces?: string; onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [e.opcion, pressed && { backgroundColor: C.actionTint, borderColor: C.action }]}>
      {icono ? <Icono nombre={icono} color={C.action} tam={24} /> : null}
      {cruces ? <ColumnaDeCruces color={cruces} /> : null}
      <View style={{ flex: 1 }}>
        <Text style={[e.opcionTitulo, quechua && { color: C.quechua }]}>{titulo}</Text>
        {detalle ? <Text style={e.opcionDetalle}>{detalle}</Text> : null}
      </View>
      <Icono nombre="chevron.right" color={C.inkTertiary} tam={16} />
    </Pressable>
  );
}

const e = StyleSheet.create({
  saludo: { alignSelf: 'center', alignItems: 'center', gap: 2, marginTop: -4, marginBottom: 6 },
  saludoEtiqueta: { fontSize: 11, fontWeight: '700', color: C.inkTertiary, letterSpacing: 0.6 },
  saludoQuy: { fontSize: ESCALA.cuerpo, fontWeight: '700', color: C.quechua, textAlign: 'center' },
  saludoEs: { fontSize: ESCALA.mini, color: C.inkSecondary, textAlign: 'center' },
  saludoBoton: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4, paddingHorizontal: 10, paddingVertical: 4 },
  saludoBotonTexto: { fontSize: ESCALA.mini, fontWeight: '600', color: C.action },
  pantalla: { flex: 1, backgroundColor: C.ground },
  cuerpo: { flex: 1, padding: 16, gap: 12 },
  marca: { fontSize: ESCALA.display, fontWeight: '700', color: C.ink, textAlign: 'center' },
  pregunta: { fontSize: ESCALA.h1, fontWeight: '700', color: C.ink, textAlign: 'center' },
  opcion: { flexDirection: 'row', alignItems: 'center', gap: 14, minHeight: 72, paddingHorizontal: 18, backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20 },
  opcionTitulo: { fontSize: ESCALA.h2, fontWeight: '700', color: C.ink },
  opcionDetalle: { fontSize: ESCALA.mini, color: C.inkSecondary, marginTop: 2 },
  campo: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 16, padding: 16, fontSize: ESCALA.h2, color: C.ink, textAlign: 'center' },
});
