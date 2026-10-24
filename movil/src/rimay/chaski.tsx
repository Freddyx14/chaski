// Chaski, la vicuña intérprete (D22). Siempre en su tarjeta con degradado (regla de tokens.json).
// Los estados con video usan los loops de avatar/loops; «hablando» alterna dos cuadros con la boca.
import { Image } from 'expo-image';
import { useVideoPlayer, VideoView } from 'expo-video';
import { StyleSheet, View } from 'react-native';

import { C } from './tokens';

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

export function Chaski({ estado, tam, boca = false }: { estado: EstadoChaski; tam: number; boca?: boolean }) {
  const radio = tam >= 200 ? 28 : 20;
  const loop = LOOPS[estado];
  return (
    <View style={[estilos.tarjeta, { width: tam, height: tam, borderRadius: radio }]}>
      {/* El cuadro fijo queda debajo: si el video tarda en arrancar, no se ve un hueco. */}
      <Image
        source={estado === 'hablando' ? (boca ? CUADROS.hablando : CUADROS.reposo) : CUADROS[estado]}
        style={StyleSheet.absoluteFill}
        contentFit="cover"
        transition={0}
      />
      {loop ? <Loop key={estado} fuente={loop} /> : null}
    </View>
  );
}

function Loop({ fuente }: { fuente: number }) {
  const player = useVideoPlayer(fuente, (p) => {
    p.loop = true;
    p.muted = true;
    p.play();
  });
  return (
    <VideoView
      player={player}
      style={StyleSheet.absoluteFill}
      contentFit="cover"
      nativeControls={false}
      allowsPictureInPicture={false}
    />
  );
}

const estilos = StyleSheet.create({
  tarjeta: {
    overflow: 'hidden',
    // El degradado de la tarjeta es el mismo fondo de las imágenes; con la imagen a sangre
    // solo se ve este color mientras carga.
    backgroundColor: C.chaskiCardBottom,
  },
});
