// Textos de la interfaz en los dos idiomas (D27): la app habla el idioma que eligió quien la usa.
//
// ⚠️ EL QUECHUA DE ESTE ARCHIVO ES UN BORRADOR DE CLAUDE, SIN REVISAR. Lo revisa la mamá de Freddy
// (hablante de chanka, enfermera en Pilpichaca) antes de mostrarlo en el pitch. Cada línea revisada se
// marca con `// ✓` al final. Ojo: «rimay» aquí es el VERBO (hablar), no el nombre de la app (D30).
import type { Idioma, Perfil, Rol } from './perfil';

/** «a el paciente» → «al paciente»: la contracción del castellano. */
const a = (quien: string) => (quien.startsWith('el ') ? `al ${quien.slice(3)}` : `a ${quien}`);

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
  explicaYo: (otro: string) => `Hable en castellano. Chaski se lo dirá en quechua ${a(otro)} y le avisará si algo no se entendió.`,
  explicaYoQuechua: (otro: string) => `Hable en quechua. Chaski le dirá ${a(otro)} lo que usted quiso decir.`,
  explicaOtro: (otro: string, idioma: string) => `Ahora habla ${otro}, en ${idioma}. Chaski le dirá a usted lo que quiso decir.`,
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
  pasosCastellano: ['Entendiendo lo que dijo', 'Traduciendo al quechua', 'Revisando que nada cambió'],
  pasosQuechua: ['Entendiendo en quechua', 'Pasándolo al castellano', 'Revisando que nada cambió'],
  puedeTardar: 'Esto puede tardar unos segundos.',
  preparandoVoz: 'Preparando la voz…',
  hablandoAhora: 'Chaski está hablando…',
  yaLoDijo: 'Chaski ya lo dijo en voz alta.',
  auditado: 'Auditado antes de hablar',
  dichoConAviso: (t: string) => `Dicho con aviso: revise ${t}`,
  dichoConAvisoSolo: 'Dicho con aviso: confírmelo',
  repetirAudio: 'Repetir audio',
  seguirConsulta: 'Seguir',
  noLoDije: 'No lo dije: algo cambió al traducir',
  reviseParte: 'Revise esta parte antes de que Chaski la diga.',
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
  entendidoSeguro: 'Chaski lo entendió con seguridad',
  seguridadMedia: 'Seguridad media · confírmelo',
  noEntendi: 'No entendí',
  idiomaDetectado: 'Idioma detectado automáticamente',
  responder: 'Responder',
  pedirQueRepita: 'Pedir que repita',
  sinServidor: 'Falta conectar Chaski con el servicio.',
  noEscuche: 'No le escuché bien. Hable un poco más cerca.',
  sinConexion: 'No pude conectarme. Vuelva a intentarlo.',
  sinGrabacion: 'No se grabó su voz. Revise que Chaski tenga permiso para usar el micrófono y vuelva a hablar.',
  conectar: 'Conectar el servicio',
  reintentar: 'Reintentar',
  volver: 'Volver',
  receta: 'Receta',
  // Contrato final (Resultado)
  chaskiNoLoDijo: (razon: string) => `Chaski no lo dijo: ${razon}`,
  revisadoCritico: 'Revisado por el crítico',
  ensayoChip: 'Ensayo · frase con prohibición',
  ensayoLetrero: 'Ensayo: simulamos que el traductor se equivocó, para mostrar que la barrera lo atrapa.',
  ensayoSinConexion: 'Ensayo sin conexión: este resultado es de ejemplo, no lo revisó el servicio.',
  ensayoNoBloqueo: 'Ensayo: el servicio todavía no acepta la traducción sembrada, así que tradujo normal. No se dijo.',
  // Errores de conexión
  detalleError: (ruta: string, tipo: string) => `${ruta} · ${tipo}`,
  probarConexion: 'Probar conexión',
  servicioResponde: 'El servicio responde. Vuelva a intentarlo.',
  servicioNoResponde: 'El servicio no responde. Puede estar reiniciándose.',
  // Intérprete agente (D32)
  chaskiPregunta: 'Chaski pregunta',
  chaskiPreguntaAl: (quien: string) => `Chaski le pregunta ${quien}`,
  chaskiResponde: 'Chaski le responde',
  porQue: 'POR QUÉ',
  falta: 'Falta',
  noLeEntendi: 'No le entendí',
  noLeEntendiExplica: 'Chaski no dijo nada para no adivinar. Pida que lo repita.',
  repetir: 'Repetir',
  fraseVerificada: 'Frase verificada',
  fraseVerificadaExplica: 'Traducción y audio revisados: suena sin esperar.',
  // Modo emergencia (C11)
  emergencia: 'Emergencia',
  emergenciaExplica: 'Toque una frase: Chaski la dice en quechua al instante.',
  faltaRevisar: 'Falta revisar el quechua con la enfermera',
  pendienteRevision: 'Pendiente de revisión: todavía no se dice',
  revisadaEnfermera: 'Revisada',
  modoEnsayo: 'Modo ensayo (para el jurado)',
  modoEnsayoExplica: 'Muestra un atajo que manda una frase con prohibición y siembra una traducción errada, para ver cómo la barrera la frena. En una consulta real, apagado.',
  faltaRevisarAviso: 'Esta frase todavía no tiene quechua revisado. Chaski no la dice.',
  bancoLocal: (n: number) => `${n} frases esperan la revisión de la enfermera.`,
  escucharRespuesta: 'Escuchar la respuesta del paciente',
  volverConsulta: 'Volver a la consulta',
  // Receta y «¿me lo repite?» (F9, F6)
  confirmeDatos: 'Confirme los datos',
  confirmeDatosExplica: 'Chaski solo dice lo que usted confirma aquí. Lo que no leyó, no lo adivina.',
  cuantoPorToma: 'Cuánto por toma',
  cadaCuantasHoras: 'Cada cuántas horas',
  porCuantosDias: 'Por cuántos días',
  faltaParaDecir: (f: string) => `Falta: ${f}`,
  decirAlPaciente: 'Decírselo al paciente',
  meLoRepite: '¿Me lo repite?',
  meLoRepiteExplica: 'Pida al paciente que repita la indicación con sus palabras.',
  loQueEntendio: 'Lo que entendió',
  entendidos: (n: number, total: number) => `${n} de ${total} entendidos`,
  noLoMenciono: 'No lo mencionó',
  explicarLoQueFalto: 'Explicar lo que faltó',
  // Glosario (D36)
  palabrasNuevas: 'Palabras nuevas en quechua',
  palabrasNuevasExplica: 'Las que se usaron en esta consulta, para ir aprendiendo.',
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
  explicaYoQuechua: () => 'Runasimipi rimay. Chaskim hampiqman willanqa.',
  explicaOtro: () => 'Kunanqa hampiqmi rimanqa. Chaskim runasimipi willasunki.',
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
  hablandoAhora: 'Chaskim rimachkan…',
  yaLoDijo: 'Chaskiqa rimarqanñam.',
  repetirAudio: 'Yapamanta uyariy',
  seguirConsulta: 'Qatiy',
  responder: 'Kutichiy',
  pedirQueRepita: 'Yapamanta nichun',
  volver: 'Kutiy',
  reintentar: 'Yapamanta',
  sinConexion: 'Manam atinichu. Yapamanta ruray.',
  noEscuche: 'Manam allintachu uyarirqani. Asuykamuspa rimay.',
  receta: 'Receta',
  // BORRADOR: intérprete agente
  chaskiPregunta: 'Chaskim tapukun',
  noLeEntendi: 'Manam entiendinichu',
  repetir: 'Yapamanta',
  meLoRepite: '¿Yapamanta niwankimanchu?',
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
