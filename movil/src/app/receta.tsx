// F9: foto de la caja o la receta → Claude la lee y la cruza con lo que dijo la enfermera.
// Si no lo lee con seguridad, no adivina: lo dice y lista lo que no pudo leer.
import * as ImagePicker from 'expo-image-picker';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ver, type Lectura } from '@/chaski/api';
import { Chaski } from '@/chaski/chaski';
import { useTurnos } from '@/chaski/consulta';
import { C, ESCALA } from '@/chaski/tokens';
import { Aviso, Boton, Tarjeta } from '@/chaski/ui';

export default function Receta() {
  const turnos = useTurnos();
  const dicho = [...turnos].reverse().find((t) => t.lado === 'castellano')?.castellano ?? '';
  const [foto, setFoto] = useState<string | null>(null);
  const [lectura, setLectura] = useState<Lectura | null>(null);
  const [leyendo, setLeyendo] = useState(false);
  const [error, setError] = useState(false);

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
    setLectura(null);
    setError(false);
    setLeyendo(true);
    try {
      setLectura(await ver(uri, dicho));
    } catch {
      setError(true);
    } finally {
      setLeyendo(false);
    }
  }

  return (
    <SafeAreaView style={e.pantalla} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 14 }}>
        <View style={e.fila}>
          <Chaski estado={leyendo ? 'pensando' : lectura && !lectura.seguro ? 'no_entendi' : 'reposo'} tam={96} />
          <View style={{ flex: 1, gap: 4 }}>
            <Text style={e.titulo}>Leer la receta o la caja</Text>
            <Text style={e.secundario}>Chaski la lee y la compara con lo que usted dijo.</Text>
          </View>
        </View>

        {dicho ? (
          <Tarjeta>
            <Text style={e.rotulo}>LO ÚLTIMO QUE USTED DIJO</Text>
            <Text style={e.cuerpo}>{dicho}</Text>
          </Tarjeta>
        ) : null}

        {foto && <Image source={{ uri: foto }} style={e.foto} contentFit="cover" />}

        {leyendo && <Aviso tipo="warn" texto="Leyendo la foto…" />}
        {error && <Aviso tipo="block" texto="No pude conectarme. Vuelva a intentarlo." />}

        {lectura && (
          <Tarjeta estilo={{ gap: 8 }}>
            {lectura.seguro ? (
              <>
                <Text style={e.rotulo}>MEDICAMENTO</Text>
                <Text style={e.grande}>
                  {[lectura.medicamento, lectura.concentracion].filter(Boolean).join(' ')}
                </Text>
                {lectura.presentacion ? <Text style={e.secundario}>{lectura.presentacion}</Text> : null}
                <Text style={[e.rotulo, { marginTop: 8 }]}>PARA QUÉ SIRVE</Text>
                <Text style={e.cuerpo}>{lectura.para_que_sirve}</Text>
                {lectura.coincide_con_lo_dicho === true && <Aviso tipo="ok" texto="Coincide con lo que usted dijo" />}
                {lectura.coincide_con_lo_dicho === false && (
                  <Aviso tipo="block" texto="No coincide con lo que usted dijo. Revise antes de seguir." />
                )}
                {lectura.advertencias.map((a, i) => <Aviso key={i} tipo="warn" texto={a} />)}
              </>
            ) : (
              <>
                <Text style={[e.grande, { color: C.warn }]}>No lo leo con seguridad</Text>
                <Text style={e.secundario}>Prefiero no adivinar. Lo que no pude leer:</Text>
                {lectura.no_leido.map((n, i) => <Text key={i} style={e.cuerpo}>· {n}</Text>)}
              </>
            )}
          </Tarjeta>
        )}
      </ScrollView>
      <View style={{ padding: 16, gap: 8 }}>
        <View style={{ flexDirection: 'row', gap: 12 }}>
          <Boton icono="camera.fill" texto="Tomar foto" onPress={() => tomar(true)} flex deshabilitado={leyendo} />
          <Boton tipo="secundario" icono="photo" texto="Galería" onPress={() => tomar(false)} flex deshabilitado={leyendo} />
        </View>
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
  grande: { fontSize: ESCALA.h1, fontWeight: '700', color: C.ink },
  foto: { width: '100%', aspectRatio: 4 / 3, borderRadius: 20, borderWidth: 1, borderColor: C.border },
});
