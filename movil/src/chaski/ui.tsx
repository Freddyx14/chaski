// Piezas de interfaz compartidas, todas con los tokens de D24.
import { SymbolView, type SymbolViewProps } from 'expo-symbols';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';

import { C, ESCALA } from './tokens';

export function Icono({ nombre, color, tam = 20 }: { nombre: SymbolViewProps['name']; color: string; tam?: number }) {
  return <SymbolView name={nombre} tintColor={color} size={tam} resizeMode="scaleAspectFit" style={{ width: tam, height: tam }} />;
}

export function Etiqueta({ idioma }: { idioma: 'castellano' | 'quechua' }) {
  const q = idioma === 'quechua';
  return (
    <View style={[estilos.etiqueta, { backgroundColor: q ? C.quechua : C.castellanoTag }]}>
      <Text style={[estilos.etiquetaTexto, { color: q ? C.surface : C.ink }]}>
        {q ? 'Quechua chanka' : 'Castellano'}
      </Text>
    </View>
  );
}

export function Tarjeta({ children, estilo }: { children: ReactNode; estilo?: StyleProp<ViewStyle> }) {
  return <View style={[estilos.tarjeta, estilo]}>{children}</View>;
}

type BotonProps = {
  texto: string;
  onPress: () => void;
  tipo?: 'primario' | 'secundario' | 'texto';
  icono?: SymbolViewProps['name'];
  alto?: number;
  flex?: boolean;
  deshabilitado?: boolean;
};

export function Boton({ texto, onPress, tipo = 'primario', icono, alto = 52, flex, deshabilitado }: BotonProps) {
  const primario = tipo === 'primario';
  const color = primario ? C.surface : tipo === 'texto' ? C.inkSecondary : C.action;
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={deshabilitado}
      style={({ pressed }) => [
        estilos.boton,
        { height: alto, borderRadius: alto / 2, opacity: deshabilitado ? 0.5 : 1 },
        flex && { flex: 1 },
        primario && { backgroundColor: pressed ? C.actionPressed : C.action },
        tipo === 'secundario' && { backgroundColor: pressed ? C.actionTint : C.surface, borderWidth: 1, borderColor: C.border },
      ]}>
      {icono ? <Icono nombre={icono} color={color} tam={18} /> : null}
      <Text style={[estilos.botonTexto, { color, fontSize: tipo === 'texto' ? ESCALA.chico : ESCALA.cuerpo }]}>{texto}</Text>
    </Pressable>
  );
}

/** Aviso con ícono: nunca solo color (regla de tokens.json). */
export function Aviso({ tipo, texto }: { tipo: 'ok' | 'warn' | 'block'; texto: string }) {
  const fg = tipo === 'ok' ? C.ok : tipo === 'warn' ? C.warn : C.block;
  const bg = tipo === 'ok' ? C.okTint : tipo === 'warn' ? C.warnTint : C.blockTint;
  const icono = tipo === 'ok' ? 'checkmark.circle.fill' : tipo === 'warn' ? 'exclamationmark.triangle.fill' : 'xmark.octagon.fill';
  return (
    <View style={[estilos.aviso, { backgroundColor: bg }]}>
      <Icono nombre={icono} color={fg} tam={16} />
      <Text style={[estilos.avisoTexto, { color: fg }]}>{texto}</Text>
    </View>
  );
}

export const estilos = StyleSheet.create({
  etiqueta: { height: 28, borderRadius: 14, paddingHorizontal: 12, justifyContent: 'center', alignSelf: 'flex-start' },
  etiquetaTexto: { fontSize: ESCALA.mini, fontWeight: '600' },
  tarjeta: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 20, padding: 16 },
  boton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 20 },
  botonTexto: { fontWeight: '600' },
  aviso: { flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 14, paddingVertical: 8, paddingHorizontal: 12, alignSelf: 'flex-start' },
  avisoTexto: { fontSize: ESCALA.mini, fontWeight: '600', flexShrink: 1 },
});
