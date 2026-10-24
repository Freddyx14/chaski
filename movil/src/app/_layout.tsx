import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';

import { cargarPerfil } from '@/chaski/perfil';

import { C } from '@/chaski/tokens';

export default function Layout() {
  useEffect(() => { cargarPerfil(); }, []);
  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: C.ground } }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="bienvenida" options={{ gestureEnabled: false }} />
        <Stack.Screen name="historial" options={{ presentation: 'modal' }} />
        <Stack.Screen name="receta" options={{ presentation: 'modal' }} />
        <Stack.Screen name="ajustes" options={{ presentation: 'modal' }} />
        <Stack.Screen name="resumen" />
      </Stack>
    </>
  );
}
