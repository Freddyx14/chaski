// Los motivos de D29 (opción L = D + I) hechos componentes: la chakana, la crucecita escalonada,
// la fila de cruces y el zigzag tejido. Todo sale de `escalonado()`. El micrófono inti vive en inti.tsx (D31).
import { useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';

import { escalonado, escalonadoAdentro, trazo } from './geometria';
import { C, ESCALA, M } from './tokens';

/** La crucecita escalonada (un solo paso hondo). Rellena, o solo contorno si `hueca`. */
export function Cruz({ tam, color, borde, hueca }: { tam: number; color: string; borde?: string; hueca?: boolean }) {
  const g = borde || hueca ? Math.max(1, Math.round(tam / 9)) : 0;
  const l = tam - g;
  const d = trazo(escalonado(l, 1, l * 0.32, g / 2, g / 2));
  return (
    <Svg width={tam} height={tam}>
      <Path d={d} fill={hueca ? 'none' : color} stroke={hueca ? color : borde ?? 'none'} strokeWidth={g} />
    </Svg>
  );
}

/** La chakana pequeña del encabezado, cobalto con su centro abierto. */
export function MarcaChakana({ tam = 20 }: { tam?: number }) {
  const exterior = trazo(escalonado(tam, 2, tam / 6));
  const c = tam * 0.34;
  const centro = `M${(tam - c) / 2} ${(tam - c) / 2}h${c}v${c}h${-c}Z`;
  return (
    <Svg width={tam} height={tam}>
      <Path d={exterior + centro} fill={M.cobalto} fillRule="evenodd" />
    </Svg>
  );
}

/** «Chaski» con su chakana: la marca de cada pantalla. */
export function MarcaChaski({ texto = 'Chaski', tam = ESCALA.h2 }: { texto?: string; tam?: number }) {
  return (
    <View style={estilos.marca}>
      <MarcaChakana tam={Math.round(tam * 0.95)} />
      <Text style={[estilos.marcaTexto, { fontSize: tam }]}>{texto}</Text>
    </View>
  );
}

const MULTICOLOR = [M.magenta, M.amarillo, M.turquesa, M.cobalto];

/** Una fila de crucecitas de colores a lo ancho de la pantalla (menos los márgenes). */
export function FilaDeCruces({ tam = 11, separacion = 6, margen = 32, colores = MULTICOLOR }: {
  tam?: number; separacion?: number; margen?: number; colores?: string[];
}) {
  const { width } = useWindowDimensions();
  const n = Math.max(0, Math.floor((width - margen + separacion) / (tam + separacion)));
  return (
    <View style={[estilos.fila, { height: tam }]} accessibilityElementsHidden>
      {Array.from({ length: n }).map((_, i) => (
        <Cruz key={i} tam={tam} color={colores[i % colores.length]} />
      ))}
    </View>
  );
}

/** La columna de crucecitas a la izquierda de una fila de idioma. */
export function ColumnaDeCruces({ color, n = 3, tam = 8 }: { color: string; n?: number; tam?: number }) {
  return (
    <View style={{ gap: 3 }} accessibilityElementsHidden>
      {Array.from({ length: n }).map((_, i) => <Cruz key={i} tam={tam} color={color} />)}
    </View>
  );
}

/** El progreso del onboarding: la cruz actual en magenta con borde de hilo, las demás huecas. */
export function ProgresoCruces({ total, actual }: { total: number; actual: number }) {
  return (
    <View style={estilos.progreso} accessibilityLabel={`Paso ${actual} de ${total}`}>
      {Array.from({ length: total }).map((_, i) =>
        i + 1 <= actual
          ? <Cruz key={i} tam={18} color={M.magenta} borde={M.hilo} />
          : <Cruz key={i} tam={18} color={C.border} hueca />,
      )}
    </View>
  );
}

/** El divisor tejido de la tarjeta de quechua: un zigzag de puntos, suave. */
export function Zigzag({ color = C.border }: { color?: string }) {
  const [ancho, setAncho] = useState(0);
  const p = 3;
  const n = Math.floor(ancho / p);
  return (
    <View style={{ height: p * 2, marginVertical: 12 }} onLayout={(e) => setAncho(e.nativeEvent.layout.width)}>
      {n > 0 && (
        <Svg width={ancho} height={p * 2}>
          {Array.from({ length: n }).map((_, i) => (
            <Rect key={i} x={i * p} y={i % 2 ? 0 : p} width={p} height={p} fill={color} />
          ))}
        </Svg>
      )}
    </View>
  );
}

/** Botón lateral (Receta, Resumen) con la silueta escalonada de D. */
export function BotonEscalonado({ children, onPress, etiqueta }: { children: ReactNode; onPress: () => void; etiqueta: string }) {
  const lado = 56;
  const d = trazo(escalonadoAdentro(lado, 3, 4, 0.75));
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={etiqueta}
      style={({ pressed }) => [{ width: lado, height: lado, alignItems: 'center', justifyContent: 'center', opacity: pressed ? 0.7 : 1 }]}>
      <Svg width={lado} height={lado} style={StyleSheet.absoluteFill}>
        <Path d={d} fill={C.surface} stroke={C.border} strokeWidth={1.5} />
      </Svg>
      {children}
    </Pressable>
  );
}

const estilos = StyleSheet.create({
  marca: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  marcaTexto: { fontWeight: '700', color: C.ink },
  fila: { flexDirection: 'row', justifyContent: 'space-between', overflow: 'hidden' },
  progreso: { flexDirection: 'row', gap: 10, justifyContent: 'center' },
});
