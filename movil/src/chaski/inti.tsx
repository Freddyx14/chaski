// El micrófono inti (D31): anillos concéntricos alrededor del botón, como un medallón de sol andino,
// con rayos escalonados cortos detrás. Solo la paleta del producto, la misma del marco de Chaski.
//
// Está vivo, siempre con señales reales:
//  - reposo:  los anillos respiran despacio, uno detrás del otro.
//  - escucha: una onda sale del centro hacia afuera con el volumen del micrófono (el anillo de adentro primero).
//  - piensa:  los rayos giran despacio y una luz recorre el anillo de afuera.
//  - habla:   los anillos laten con la envolvente de la voz (`pulso`).
// El tinte dice de quién es el turno: castellano en la paleta normal, quechua en canela.
// Con «Reducir movimiento» queda quieto; los anillos solo cambian de brillo con la voz.
import { useEffect, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, {
  cancelAnimation, Easing, Extrapolation, interpolate, useAnimatedStyle, useReducedMotion, useSharedValue,
  withRepeat, withTiming, type SharedValue,
} from 'react-native-reanimated';
import Svg, { Path } from 'react-native-svg';

import { trazo, type Punto } from './geometria';
import { UMBRALES } from './movimiento';
import { C, M } from './tokens';

export type ModoInti = 'reposo' | 'escucha' | 'piensa' | 'habla';

// Ritmo de la referencia: anillos gruesos y finos alternados, con un aire de fondo entre cada uno.
const GROSORES = [5, 9, 5, 9]; // de adentro hacia afuera
const AIRE = 3;
const PALETA = { castellano: [M.cobalto, M.amarillo, M.turquesa, M.magenta], quechua: [M.naranja, M.amarillo, C.quechua, M.naranja] };
const RAYOS = 8;

export function AnilloInti({ children, centro = 96, modo = 'reposo', nivel = 0, pulso, tinte = 'castellano' }: {
  children: ReactNode; centro?: number; modo?: ModoInti; nivel?: number; pulso?: number; tinte?: 'castellano' | 'quechua';
}) {
  const quieto = useReducedMotion();
  const escala = centro / 96;
  const grosores = GROSORES.map((g) => Math.max(2, Math.round(g * escala)));
  const aire = Math.max(2, Math.round(AIRE * escala));
  const colores = PALETA[tinte];

  // Radio interior de cada anillo.
  const radios: number[] = [];
  let r = centro / 2 + aire;
  for (const g of grosores) { radios.push(r); r += g + aire; }
  const exterior = r - aire;
  const largoRayo = Math.round(16 * escala);
  const caja = 2 * (exterior + largoRayo + 4);

  const senal = useSharedValue(0); // volumen del micrófono o de la voz, 0..1
  const fase = useSharedValue(0); // respiración / onda / giro
  const activa = modo === 'escucha' || modo === 'habla';

  useEffect(() => {
    senal.value = withTiming(modo === 'escucha' ? nivel : modo === 'habla' ? (pulso ?? 0) : 0, { duration: 90 });
  }, [modo, nivel, pulso, senal]);

  useEffect(() => {
    cancelAnimation(fase);
    fase.value = 0;
    if (quieto) return;
    if (modo === 'reposo') fase.value = withRepeat(withTiming(1, { duration: 4000, easing: Easing.linear }), -1, false);
    if (modo === 'escucha' || modo === 'habla') fase.value = withRepeat(withTiming(1, { duration: 900, easing: Easing.linear }), -1, false);
    if (modo === 'piensa') fase.value = withRepeat(withTiming(1, { duration: 6000, easing: Easing.linear }), -1, false);
  }, [modo, quieto, fase]);

  const giro = useAnimatedStyle(() => ({
    transform: [{ rotate: `${modo === 'piensa' && !quieto ? fase.value * 360 : 0}deg` }],
  }));

  return (
    <View style={{ width: caja, height: caja, alignItems: 'center', justifyContent: 'center' }}>
      {/* Rayos escalonados detrás del anillo de afuera: cortos y pocos. */}
      <Animated.View style={[StyleSheet.absoluteFill, giro]}>
        <Svg width={caja} height={caja}>
          {Array.from({ length: RAYOS }).map((_, i) => (
            <Path key={i} d={rayo(caja / 2, exterior - 2, largoRayo + 2, (360 / RAYOS) * i, 7 * escala)} fill={colores[i % 2 ? 1 : 3]} />
          ))}
        </Svg>
      </Animated.View>
      {/* El fondo del medallón tapa la base de los rayos. */}
      <View style={[estilos.disco, { width: exterior * 2, height: exterior * 2, borderRadius: exterior }]} />
      {radios.map((rad, i) => (
        <Anillo key={i} i={i} radio={rad} grosor={grosores[i]} color={colores[i]} senal={senal} fase={fase}
          modo={modo} activa={activa} quieto={quieto} />
      ))}
      {modo === 'piensa' && !quieto && <Luz radio={radios[3] + grosores[3] / 2} fase={fase} />}
      {children}
    </View>
  );
}

function Anillo({ i, radio, grosor, color, senal, fase, modo, activa, quieto }: {
  i: number; radio: number; grosor: number; color: string; senal: SharedValue<number>; fase: SharedValue<number>;
  modo: ModoInti; activa: boolean; quieto: boolean;
}) {
  const lado = 2 * (radio + grosor);
  const estilo = useAnimatedStyle(() => {
    // Brillo: con voz, los anillos se encienden de adentro hacia afuera (umbral del anillo i).
    const umbral = i === 0 ? 0.05 : UMBRALES[Math.min(2, i - 1)];
    const brillo = activa ? interpolate(senal.value, [umbral - 0.08, umbral], [0.3, 1], Extrapolation.CLAMP) : 1;
    let escala = 1;
    if (!quieto) {
      if (modo === 'reposo') {
        // Respiración escalonada: cada anillo un cuarto de ciclo detrás del anterior.
        escala = 1 + 0.025 * Math.max(0, Math.sin((fase.value - i * 0.12) * 2 * Math.PI));
      } else if (activa) {
        // Onda que sale del centro: el frente pasa por el anillo i cuando la fase llega a i/4.
        const frente = fase.value * 4.6 - i;
        const golpe = Math.max(0, 1 - Math.abs(frente - 0.5) * 1.6);
        escala = 1 + senal.value * (0.03 + 0.07 * golpe);
      }
    }
    return { opacity: brillo, transform: [{ scale: escala }] };
  });
  return (
    <Animated.View
      pointerEvents="none"
      style={[{ position: 'absolute', width: lado, height: lado, borderRadius: lado / 2, borderWidth: grosor, borderColor: color }, estilo]}
    />
  );
}

/** Una luz que recorre el anillo de afuera mientras Chaski piensa. */
function Luz({ radio, fase }: { radio: number; fase: SharedValue<number> }) {
  const estilo = useAnimatedStyle(() => {
    const a = fase.value * 2 * Math.PI * 3 - Math.PI / 2; // tres vueltas por cada giro de los rayos
    return { transform: [{ translateX: Math.cos(a) * radio }, { translateY: Math.sin(a) * radio }] };
  });
  return <Animated.View pointerEvents="none" style={[estilos.luz, estilo]} />;
}

/** Un rayo escalonado: dos peldaños que se angostan hacia afuera, girado `grados` desde arriba. */
function rayo(c: number, desde: number, largo: number, grados: number, ancho: number): string {
  const mitad = largo / 2;
  const pts: Punto[] = [
    [-ancho, 0], [ancho, 0], [ancho, -mitad], [ancho / 2, -mitad], [ancho / 2, -largo],
    [-ancho / 2, -largo], [-ancho / 2, -mitad], [-ancho, -mitad],
  ].map(([x, y]) => [x, y - desde] as Punto);
  const a = (grados * Math.PI) / 180;
  return trazo(pts.map(([x, y]) => [c + x * Math.cos(a) - y * Math.sin(a), c + x * Math.sin(a) + y * Math.cos(a)]));
}

const estilos = StyleSheet.create({
  disco: { position: 'absolute', backgroundColor: C.ground },
  luz: { position: 'absolute', width: 10, height: 10, borderRadius: 5, backgroundColor: C.surface, borderWidth: 2, borderColor: M.amarillo },
});
