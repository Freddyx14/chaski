// Textos de la interfaz en los dos idiomas (D27): la app habla el idioma que eligió quien la usa.
//
// ⚠️ EL QUECHUA DE ESTE ARCHIVO ES UN BORRADOR DE CLAUDE, SIN REVISAR. Lo revisa la mamá de Freddy
// (hablante de chanka, enfermera en Pilpichaca) antes de mostrarlo en el pitch. Cada línea revisada se
// marca con `// ✓` al final.
import type { Idioma, Perfil, Rol } from './perfil';

const es = {
  elegirIdioma: '¿Qué idioma habla?',
  suNombre: '¿Cómo se llama?',
  nombreEjemplo: 'Su nombre',
  quienEs: '¿Quién es usted?',
  personal: 'Personal de salud',
  personalDetalle: 'Enfermera, técnico, obstetra, médico',
  paciente: 'Paciente',
  pacienteDetalle: 'Vengo a atenderme a la posta',
  seguir: 'Seguir',
  empezar: 'Empezar',
  hola: (n: string) => `Hola, ${n}`,
  listo: 'Listo para interpretar',
  explicaYo: (otro: string) => `Hable en castellano. Rimay se lo dirá en quechua a ${otro} y le avisará si algo no se entendió.`,
  explicaYoQuechua: (otro: string) => `Hable en quechua. Rimay le dirá a ${otro} lo que usted quiso decir.`,
  explicaOtro: (otro: string, idioma: string) => `Ahora habla ${otro}, en ${idioma}. Rimay le dirá a usted lo que quiso decir.`,
  tocarHablar: 'Toque para hablar',
  tocarTerminar: 'Toque para terminar',
  habla: (quien: string, idioma: string) => `Habla ${quien} · ${idioma}`,
  usted: 'usted',
  elPaciente: 'el paciente',
  elPersonal: 'el personal de salud',
  castellano: 'castellano',
  quechua: 'quechua',
  escuchando: 'Escuchando…',
  hableNormal: 'Hable con normalidad. Toque el botón cuando termine.',
  pasosCastellano: ['Le escuché', 'Traduciendo al quechua', 'Revisando dosis, horas y días'],
  pasosQuechua: ['Detectando el idioma', 'Escuchando en quechua', 'Entendiendo lo que quiso decir'],
  preparandoVoz: 'Preparando la voz…',
  hablandoAhora: 'Rimay está hablando…',
  yaLoDijo: 'Rimay ya lo dijo en voz alta.',
  auditado: 'Auditado antes de hablar',
  dichoConAviso: (t: string) => `Dicho con aviso: revise ${t}`,
  dichoConAvisoSolo: 'Dicho con aviso: confírmelo',
  repetirAudio: 'Repetir audio',
  seguirConsulta: 'Seguir',
  noLoDije: 'No lo dije: algo cambió al traducir',
  reviseParte: 'Revise esta parte antes de que Rimay la diga.',
  ustedDijo: 'USTED DIJO',
  traduccionDecia: 'LA TRADUCCIÓN DECÍA',
  sinTraduccionSegura: 'PALABRAS SIN TRADUCCIÓN SEGURA',
  loDemasBien: 'LO DEMÁS ESTÁ BIEN',
  decirloOtraForma: 'Decirlo de otra forma',
  loExplicoYo: 'Lo explico yo',
  loQueDijo: 'LO QUE DIJO',
  loQueQuisoDecir: 'LO QUE QUISO DECIR',
  noSeOyo: '(no se oyó con claridad)',
  noLoEntendi: 'No lo entendí. Pídale que lo repita.',
  entendidoSeguro: 'Rimay lo entendió con seguridad',
  seguridadMedia: 'Seguridad media · confírmelo',
  noEntendi: 'No entendí',
  idiomaDetectado: 'Idioma detectado automáticamente',
  responder: 'Responder',
  pedirQueRepita: 'Pedir que repita',
  sinServidor: 'Falta conectar Rimay con el servicio.',
  noEscuche: 'No le escuché bien. Hable un poco más cerca.',
  sinConexion: 'No pude conectarme. Vuelva a intentarlo.',
  conectar: 'Conectar el servicio',
  reintentar: 'Reintentar',
  volver: 'Volver',
  receta: 'Receta',
  consulta: 'Consulta',
  resumen: 'Resumen',
};

export type Textos = typeof es;

// BORRADOR SIN REVISAR (ver arriba). Chanka, ortografía de tres vocales.
const quechua: Textos = {
  ...es,
  elegirIdioma: '¿Ima simitam rimanki?',
  suNombre: '¿Imataq sutiyki?',
  nombreEjemplo: 'Sutiyki',
  quienEs: '¿Pitaq kanki?',
  personal: 'Hampiq',
  personalDetalle: 'Enfermera, técnico, obstetra, médico',
  paciente: 'Hampichikuq',
  pacienteDetalle: 'Postaman hampichikuq hamuni',
  seguir: 'Qatiy',
  empezar: 'Qallariy',
  hola: (n: string) => `Allillanchu, ${n}`,
  listo: 'Yanapanaypaqmi kachkani',
  explicaYoQuechua: () => 'Runasimipi rimay. Rimaymi hampiqman willanqa.',
  explicaOtro: () => 'Kunanqa hampiqmi rimanqa. Rimaymi runasimipi willasunki.',
  tocarHablar: 'Llapiy rimanaykipaq',
  tocarTerminar: 'Llapiy tukunaykipaq',
  habla: (quien: string, idioma: string) => `${quien} rimachkan · ${idioma}`,
  usted: 'qam',
  elPersonal: 'hampiq',
  elPaciente: 'hampichikuq',
  castellano: 'castellano',
  quechua: 'runasimi',
  escuchando: 'Uyarichkani…',
  hableNormal: 'Rimay. Tukuspaqa llapiy.',
  preparandoVoz: 'Rimanaypaq wakichikuchkani…',
  hablandoAhora: 'Rimaymi rimachkan…',
  yaLoDijo: 'Rimayqa rimarqanñam.',
  repetirAudio: 'Yapamanta uyariy',
  seguirConsulta: 'Qatiy',
  responder: 'Kutichiy',
  pedirQueRepita: 'Yapamanta nichun',
  volver: 'Kutiy',
  reintentar: 'Yapamanta',
  sinConexion: 'Manam atinichu. Yapamanta ruray.',
  noEscuche: 'Manam allintachu uyarirqani. Asuykamuspa rimay.',
  receta: 'Receta',
  consulta: 'Consulta',
};

export function textos(idioma: Idioma): Textos {
  return idioma === 'quechua' ? quechua : es;
}

/** El idioma que habla la otra persona de la consulta. */
export function idiomaDelOtro(p: Perfil): Idioma {
  return p.idioma === 'castellano' ? 'quechua' : 'castellano';
}

/** Cómo se nombra a quien habla, visto desde el usuario de este teléfono. */
export function quienHabla(p: Perfil, idiomaDelTurno: Idioma, t: Textos): string {
  if (idiomaDelTurno === p.idioma) return t.usted;
  return otraPersona(p.rol, t);
}

export function otraPersona(rol: Rol, t: Textos): string {
  return rol === 'personal' ? t.elPaciente : t.elPersonal;
}
