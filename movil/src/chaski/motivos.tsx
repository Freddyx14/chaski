// Los motivos de D29 (opción L = D + I) hechos componentes: la chakana, la crucecita escalonada,
// la fila de cruces, el zigzag tejido y el anillo del micrófono. Todo sale de `escalonado()`.
import { useEffect, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import Animated, {
  cancelAnimation, Easing, Extrapolation, interpolate, useAnimatedProps, useAnimatedStyle, useReducedMotion,
  useSharedValue, withRepeat, withSequence, withTiming, type SharedValue,
} from 'react-native-reanimated';
import Svg, { Path, Rect } from 'react-native-svg';

import { escalonado, escalonadoAdentro, trazo } from './geometria';
import { brilloDeEstrella, UMBRALES } from './movimiento';
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

export type ModoAnillo = 'reposo' | 'escucha' | 'piensa';

const AnimatedPath = Animated.createAnimatedComponent(Path);

/**
 * El anillo del micrófono: tres chakanas anidadas y la constelación alrededor. Está vivo:
 *  - reposo:  respira despacio (~4 s) para invitar a tocar.
 *  - escucha: las hebras se encienden de adentro hacia afuera con el volumen real y las estrellas se abren.
 *  - piensa:  un brillo gira por la constelación, estrella por estrella.
 * El tinte dice de quién es el turno: teal-amarillo-magenta para castellano, canela para quechua.
 * Con «Reducir movimiento» no respira ni gira; las hebras solo cambian de brillo.
 */
export function AnilloChakana({ children, lado = 148, modo = 'reposo', nivel = 0, tinte = 'castellano' }: {
  children: ReactNode; lado?: number; modo?: ModoAnillo; nivel?: number; tinte?: 'castellano' | 'quechua';
}) {
  const quieto = useReducedMotion();
  const g = 4; // grosor de cada hebra
  const s = 4; // aire entre hebras
  const pasos = 2;
  const paso = lado * 0.105;
  // De afuera hacia adentro.
  const hebras = tinte === 'quechua' ? [C.quechua, M.naranja, M.amarillo] : [M.turquesa, M.amarillo, M.magenta];
  const caja = lado + 64; // la constelación vive fuera de la chakana
  const o = (caja - lado) / 2;

  const nivelSV = useSharedValue(0);
  const respiro = useSharedValue(1);
  const giro = useSharedValue(0);
  const escucha = modo === 'escucha';

  useEffect(() => {
    nivelSV.value = withTiming(escucha ? nivel : 0, { duration: 90 });
  }, [nivel, escucha, nivelSV]);

  useEffect(() => {
    cancelAnimation(respiro);
    respiro.value = 1;
    if (modo === 'reposo' && !quieto) {
      respiro.value = withRepeat(withSequence(
        withTiming(1.035, { duration: 2000, easing: Easing.inOut(Easing.sin) }),
        withTiming(1, { duration: 2000, easing: Easing.inOut(Easing.sin) }),
      ), -1);
    }
    cancelAnimation(giro);
    giro.value = 0;
    if (modo === 'piensa' && !quieto) {
      giro.value = withRepeat(withTiming(8, { duration: 2400, easing: Easing.linear }), -1, false);
    }
  }, [modo, quieto, respiro, giro]);

  const estiloRespiro = useAnimatedStyle(() => ({ transform: [{ scale: respiro.value }] }));

  return (
    <View style={{ width: caja, height: caja, alignItems: 'center', justifyContent: 'center' }}>
      <Animated.View style={[StyleSheet.absoluteFill, estiloRespiro]}>
        <Svg width={caja} height={caja}>
          {hebras.map((color, i) => (
            <Hebra
              key={i}
              d={trazo(escalonadoAdentro(lado, pasos, paso, i * (g + s) + g / 2).map(([x, y]) => [x + o, y + o]))}
              color={color}
              grosor={g}
              // La hebra de adentro se enciende primero: umbral de la capa (2 - i).
              umbral={UMBRALES[2 - i]}
              nivel={nivelSV}
              escucha={escucha}
            />
          ))}
        </Svg>
      </Animated.View>
      {Array.from({ length: 8 }).map((_, i) => (
        <Estrella key={i} i={i} caja={caja} radio={lado / 2 + 22} color={hebras[i % 3]}
          nivel={nivelSV} giro={giro} piensa={modo === 'piensa'} quieto={quieto} />
      ))}
      {children}
    </View>
  );
}

function Hebra({ d, color, grosor, umbral, nivel, escucha }: {
  d: string; color: string; grosor: number; umbral: number; nivel: SharedValue<number>; escucha: boolean;
}) {
  const props = useAnimatedProps(() => ({
    strokeOpacity: escucha ? interpolate(nivel.value, [umbral - 0.08, umbral], [0.25, 1], Extrapolation.CLAMP) : 1,
  }));
  return <AnimatedPath d={d} fill="none" stroke={color} strokeWidth={grosor} animatedProps={props} />;
}

function Estrella({ i, caja, radio, color, nivel, giro, piensa, quieto }: {
  i: number; caja: number; radio: number; color: string; nivel: SharedValue<number>; giro: SharedValue<number>;
  piensa: boolean; quieto: boolean;
}) {
  const a = (Math.PI / 4) * i - Math.PI / 2;
  const r = i % 2 ? radio * 0.92 : radio * 1.06;
  const estilo = useAnimatedStyle(() => {
    const abre = quieto ? 0 : nivel.value * 7;
    return {
      opacity: piensa && !quieto ? brilloDeEstrella(i, 8, giro.value) : 1,
      transform: [{ translateX: Math.cos(a) * abre }, { translateY: Math.sin(a) * abre }],
    };
  });
  return (
    <Animated.View style={[{ position: 'absolute', left: caja / 2 + Math.cos(a) * r - 5, top: caja / 2 + Math.sin(a) * r - 5 }, estilo]}>
      <Cruz tam={10} color={color} />
    </Animated.View>
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
