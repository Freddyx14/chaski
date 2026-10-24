import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { C } from '@/rimay/tokens';

export default function Layout() {
  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: C.ground } }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="historial" options={{ presentation: 'modal' }} />
        <Stack.Screen name="receta" options={{ presentation: 'modal' }} />
        <Stack.Screen name="ajustes" options={{ presentation: 'modal' }} />
      </Stack>
    </>
  );
}
