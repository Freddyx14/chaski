// Chaski, la vicuña intérprete (D22), en su marco de D29: la silueta escalonada de D dentro de las tres
// hebras de I (cobalto, amarillo, magenta) que siguen los escalones. Los estados con video usan los loops
// de avatar/loops; «hablando» alterna dos cuadros con la boca.
import { Image } from 'expo-image';
import { useVideoPlayer, VideoView } from 'expo-video';
import { StyleSheet, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { escalonadoAdentro, escalonesDeChaski, trazo } from './geometria';
import { hebrasEncendidas } from './movimiento';
import { C, M } from './tokens';

export type EstadoChaski = 'reposo' | 'presentarse' | 'escuchando' | 'pensando' | 'hablando' | 'no_entendi';

const CUADROS = {
  reposo: require('../../../avatar/estados/reposo.png'),
  hablando: require('../../../avatar/estados/hablando.png'),
  escuchando: require('../../../avatar/estados/escuchando.png'),
  pensando: require('../../../avatar/estados/pensando.png'),
  no_entendi: require('../../../avatar/estados/no_entendi.png'),
  presentarse: require('../../../avatar/estados/presentarse.png'),
};

const LOOPS: Partial<Record<EstadoChaski, number>> = {
  presentarse: require('../../../avatar/loops/presentarse.mp4'),
  escuchando: require('../../../avatar/loops/escuchando.mp4'),
  pensando: require('../../../avatar/loops/pensando.mp4'),
  no_entendi: require('../../../avatar/loops/no_entendi.mp4'),
};

// Chaski «libre» (prueba del 24-oct): sin fondo, recortado con BiRefNet; video HEVC con alfa donde ya existe.
const LIBRE_CUADROS = {
  reposo: require('../../../avatar/estados-alfa/reposo.png'),
  hablando: require('../../../avatar/estados-alfa/hablando.png'),
  escuchando: require('../../../avatar/estados-alfa/escuchando.png'),
  pensando: require('../../../avatar/estados-alfa/pensando.png'),
  no_entendi: require('../../../avatar/estados-alfa/no_entendi.png'),
  presentarse: require('../../../avatar/estados-alfa/presentarse.png'),
};
const LIBRE_LOOPS: Partial<Record<EstadoChaski, number>> = {
  escuchando: require('../../../avatar/loops/escuchando-alfa.mov'),
};

/** D40: Chaski va sin marco ni fondo, sobre el fondo de la app. El marco anterior queda con `&marco=1`. */
let libre = true;
export function usarChaskiLibre(si: boolean) {
  libre = si;
}

const HEBRAS = [M.cobalto, M.amarillo, M.magenta]; // de afuera hacia adentro

/**
 * `fondo` es el color de lo que hay detrás: tapa las esquinas de la foto fuera de los escalones.
 * `pulso` (0..1) es el volumen de la voz en este instante (la envolvente del WAV): mientras Chaski habla,
 * las hebras se encienden de adentro hacia afuera, magenta → amarillo → cobalto, en las partes fuertes.
 */
export function Chaski({ estado, tam, boca = false, fondo = C.ground, pulso }: {
  estado: EstadoChaski; tam: number; boca?: boolean; fondo?: string; pulso?: number;
}) {
  if (libre) return <ChaskiLibre estado={estado} tam={tam} boca={boca} pulso={pulso} />;
  const encendidas = pulso === undefined ? 3 : hebrasEncendidas(pulso, [0.15, 0.45, 0.75]);
  const loop = LOOPS[estado];
  const g = Math.max(2, Math.round(tam * 0.022)); // grosor de cada hebra
  const s = Math.max(1.5, Math.round(tam * 0.018 * 2) / 2); // aire entre hebras
  const foto = 3 * g + 2 * s; // donde empieza la foto
  const { pasos, paso } = escalonesDeChaski(tam);
  const silueta = trazo(escalonadoAdentro(tam, pasos, paso, foto));
  const lienzo = `M0 0H${tam}V${tam}H0Z`;
  return (
    <View style={{ width: tam, height: tam }}>
      <View style={[estilos.foto, { left: foto, top: foto, right: foto, bottom: foto }]}>
        {/* El cuadro fijo queda debajo: si el video tarda en arrancar, no se ve un hueco. */}
        <Image
          source={estado === 'hablando' ? (boca ? CUADROS.hablando : CUADROS.reposo) : CUADROS[estado]}
          style={StyleSheet.absoluteFill}
          contentFit="cover"
          transition={0}
        />
        {loop ? <Loop key={estado} fuente={loop} /> : null}
      </View>
      <Svg width={tam} height={tam} style={StyleSheet.absoluteFill} pointerEvents="none">
        <Path d={lienzo + silueta} fill={fondo} fillRule="evenodd" />
        {HEBRAS.map((color, i) => (
          <Path
            key={color}
            d={trazo(escalonadoAdentro(tam, pasos, paso, i * (g + s) + g / 2))}
            fill="none"
            stroke={color}
            strokeWidth={g}
            // i = 0 es la de afuera; se enciende la última.
            strokeOpacity={2 - i < encendidas ? 1 : 0.35}
          />
        ))}
      </Svg>
    </View>
  );
}

function ChaskiLibre({ estado, tam, boca, pulso }: { estado: EstadoChaski; tam: number; boca: boolean; pulso?: number }) {
  const loop = LIBRE_LOOPS[estado];
  const cuadro = estado === 'hablando' ? (boca ? LIBRE_CUADROS.hablando : LIBRE_CUADROS.reposo) : LIBRE_CUADROS[estado];
  // Al hablar, Chaski crece apenas con la voz: el mismo pulso que encendía las hebras del marco.
  // Las imágenes traen mucho aire alrededor: se agranda para que Chaski llene el mismo espacio que el marco.
  const escala = 1.3 + (pulso ?? 0) * 0.05;
  return (
    <View style={{ width: tam, height: tam, alignItems: 'center', justifyContent: 'flex-end', overflow: 'visible' }}>
      {/* Sombra en el piso: el recorte se lleva la del video, y sin ella Chaski flota. */}
      <View style={[estilos.sombra, { width: tam * 0.5, height: tam * 0.07, borderRadius: tam, bottom: tam * 0.04 }]} />
      <View style={[StyleSheet.absoluteFill, { transform: [{ translateY: -tam * 0.06 }, { scale: escala }] }]}>
        {/* Con video transparente, la imagen fija NO va debajo: se vería a través (Chaski doble). */}
        {loop ? (
          <Loop key={estado} fuente={loop} ajuste="contain" />
        ) : (
          <Image source={cuadro} style={StyleSheet.absoluteFill} contentFit="contain" transition={0} />
        )}
      </View>
    </View>
  );
}

function Loop({ fuente, ajuste = 'cover' }: { fuente: number; ajuste?: 'cover' | 'contain' }) {
  const player = useVideoPlayer(fuente, (p) => {
    p.loop = true;
    p.muted = true;
    p.play();
  });
  return (
    <VideoView
      player={player}
      style={[StyleSheet.absoluteFill, { backgroundColor: 'transparent' }]}
      contentFit={ajuste}
      nativeControls={false}
      allowsPictureInPicture={false}
    />
  );
}

const estilos = StyleSheet.create({
  // El fondo de la foto es el mismo de las imágenes: mientras carga no se ve un hueco blanco.
  foto: { position: 'absolute', overflow: 'hidden', backgroundColor: C.chaskiCardBottom },
  sombra: { position: 'absolute', backgroundColor: C.ink, opacity: 0.08 },
});
