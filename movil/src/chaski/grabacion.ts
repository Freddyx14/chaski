import { IOSOutputFormat, type RecordingOptions } from 'expo-audio';

// WAV 16 kHz mono 16 bits: lo que piden el detector de idioma y el reconocimiento (CONTRATO.md §1).
export const GRABACION: RecordingOptions = {
  extension: '.wav',
  sampleRate: 16000,
  numberOfChannels: 1,
  bitRate: 256000,
  isMeteringEnabled: true,
  ios: {
    outputFormat: IOSOutputFormat.LINEARPCM,
    audioQuality: 96,
    linearPCMBitDepth: 16,
    linearPCMIsBigEndian: false,
    linearPCMIsFloat: false,
  },
  android: { outputFormat: 'default', audioEncoder: 'default' },
  web: {},
};
