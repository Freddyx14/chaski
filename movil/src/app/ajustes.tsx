// Dirección del servicio (el túnel HTTPS cambia cada vez que se levanta). Se entra con un toque largo en «Rimay».
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { salud } from '@/rimay/api';
import { guardarServidor, leerServidor } from '@/rimay/config';
import { C, ESCALA } from '@/rimay/tokens';
import { Aviso, Boton } from '@/rimay/ui';

export default function Ajustes() {
  const [url, setUrl] = useState('');
  const [estado, setEstado] = useState<{ tipo: 'ok' | 'warn' | 'block'; texto: string } | null>(null);

  useEffect(() => { leerServidor().then(setUrl); }, []);

  async function probar() {
    await guardarServidor(url);
    setEstado({ tipo: 'warn', texto: 'Probando…' });
    try {
      const s = await salud();
      const faltan = ['clave_anthropic', 'clave_cartesia', 'traductor_de_freddy'].filter((k) => !s[k]);
      setEstado(faltan.length
        ? { tipo: 'warn', texto: `Conectado, pero falta: ${faltan.join(', ')}` }
        : { tipo: 'ok', texto: 'Conectado. Todo listo.' });
    } catch {
      setEstado({ tipo: 'block', texto: 'No respondió. Revise la dirección y que el túnel esté abierto.' });
    }
  }

  return (
    <SafeAreaView style={e.pantalla}>
      <View style={{ padding: 16, gap: 14 }}>
        <Text style={e.titulo}>Servicio</Text>
        <Text style={e.secundario}>La dirección HTTPS del túnel que expone el servicio (termina en trycloudflare.com).</Text>
        <TextInput
          value={url}
          onChangeText={setUrl}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          placeholder="https://…trycloudflare.com"
          placeholderTextColor={C.inkTertiary}
          style={e.campo}
        />
        <Boton texto="Guardar y probar" onPress={probar} />
        {estado && <Aviso {...estado} />}
        <Boton tipo="texto" texto="Cerrar" onPress={() => router.back()} />
      </View>
    </SafeAreaView>
  );
}

const e = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: C.ground },
  titulo: { fontSize: ESCALA.h1, fontWeight: '700', color: C.ink },
  secundario: { fontSize: ESCALA.chico, color: C.inkSecondary, lineHeight: 20 },
  campo: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 14, padding: 14, fontSize: ESCALA.chico, color: C.ink },
});
