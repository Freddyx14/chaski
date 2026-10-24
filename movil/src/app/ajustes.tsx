// Dirección del servicio (el túnel HTTPS cambia cada vez que se levanta). Se entra con un toque largo en «Chaski».
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { salud } from '@/chaski/api';
import { guardarServidor, leerServidor } from '@/chaski/config';
import { guardarPerfil } from '@/chaski/perfil';
import { MarcaChaski } from '@/chaski/motivos';
import { C, ESCALA } from '@/chaski/tokens';
import { Aviso, Boton } from '@/chaski/ui';

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
        <MarcaChaski texto="Servicio" tam={ESCALA.h1} />
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
        <Boton tipo="secundario" texto="Cambiar idioma, nombre o rol" onPress={async () => { await guardarPerfil(null); router.replace('/bienvenida'); }} />
        <Boton tipo="texto" texto="Cerrar" onPress={() => router.back()} />
      </View>
    </SafeAreaView>
  );
}

const e = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: C.ground },
  secundario: { fontSize: ESCALA.chico, color: C.inkSecondary, lineHeight: 20 },
  campo: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 14, padding: 14, fontSize: ESCALA.chico, color: C.ink },
});
