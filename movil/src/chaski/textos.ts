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
  personalDetalle: '',
  paciente: 'Paciente',
  pacienteDetalle: '',
  seguir: 'Seguir',
  empezar: 'Empezar',
  hola: (n: string) => `Hola, ${n}`,
  listo: 'Toque y hable',
  explicaYo: (otro: string) => `Hable en castellano. Chaski se lo dirá en quechua ${a(otro)} y le avisará si algo no se entendió.`,
  explicaYoQuechua: (otro: string) => `Hable en quechua. Chaski le dirá ${a(otro)} lo que usted quiso decir.`,
  explicaOtro: (otro: string, idioma: string) => `Ahora habla ${otro}, en ${idioma}. Chaski le dirá a usted lo que quiso decir.`,
  tocarHablar: 'Hablar',
  tocarTerminar: 'Terminar',
  // Modo conversación: 1–2 palabras por estado (D42).
  tocarPausar: 'Pausar',
  hablandoAlPaciente: 'Hablando al paciente',
  hablandoAlPersonal: 'Hablando al personal',
  habla: (quien: string, idioma: string) => `${quien} · ${idioma}`,
  usted: 'usted',
  elPaciente: 'el paciente',
  elPersonal: 'el personal de salud',
  castellano: 'castellano',
  quechua: 'quechua',
  escuchando: 'Le escucho…',
  hableNormal: 'Hable con normalidad. Toque el botón cuando termine.',
  pasosCastellano: ['Escuchando…', 'Traduciendo…', 'Revisando…'],
  pasosQuechua: ['Escuchando…', 'Traduciendo…', 'Revisando…'],
  puedeTardar: 'Un momento…',
  sigueRevisando: 'Sigo revisando…',
  preparandoVoz: 'Preparando la voz…',
  hablandoAhora: 'Chaski está hablando…',
  yaLoDijo: 'Chaski ya lo dijo en voz alta.',
  auditado: 'Revisado',
  dichoConAviso: (t: string) => `Revise: ${t}`,
  dichoConAvisoSolo: 'Confírmelo',
  repetirAudio: 'Repetir',
  seguirConsulta: 'Seguir',
  noLoDije: 'No lo dije',
  reviseParte: 'Antes de hablar, Chaski revisa cada dato. Esta vez encontró un cambio y prefirió callar antes que decir algo equivocado. Dígalo de otra forma o explíquelo usted.',
  loFrenoATiempo: 'Chaski lo frenó a tiempo',
  ustedDijo: 'USTED DIJO',
  traduccionDecia: 'LA TRADUCCIÓN DECÍA',
  sinTraduccionSegura: 'PALABRAS SIN TRADUCCIÓN SEGURA',
  loDemasBien: 'LO DEMÁS ESTÁ BIEN',
  decirloOtraForma: 'Dígalo de otra forma',
  loExplicoYo: 'Lo explico yo',
  loQueDijo: 'LO QUE DIJO',
  loQueQuisoDecir: 'LO QUE QUISO DECIR',
  noSeOyo: '(no se oyó con claridad)',
  noLoEntendi: 'No entendí',
  entendidoSeguro: 'Entendido',
  seguridadMedia: 'Confírmelo',
  noEntendi: 'No entendí',
  idiomaDetectado: 'Idioma detectado automáticamente',
  responder: 'Responder',
  pedirQueRepita: 'Repetir',
  sinServidor: 'Sin conexión',
  noEscuche: 'No le escuché',
  sinConexion: 'Sin conexión',
  chaskiLoDira: 'Chaski dirá:',
  muestreleEsto: 'Muéstreselo',
  chaskiLoDice: 'Chaski lo dice',
  sinVozLeaUsted: 'Léalo usted',
  cerrar: 'Cerrar',
  sinGrabacion: 'No se grabó su voz',
  conectar: 'Conectar',
  reintentar: 'Reintentar',
  volver: 'Volver',
  receta: 'Receta',
  // Contrato final (Resultado)
  chaskiNoLoDijo: (razon: string) => `Chaski no lo dijo: ${razon}`,
  revisadoCritico: 'Revisado',
  ensayoChip: 'Ensayo · frase con prohibición',
  ensayoLetrero: 'Ensayo: error simulado',
  ensayoSinConexion: 'Ensayo: ejemplo sin conexión',
  ensayoNoBloqueo: 'Ensayo: no se pudo simular',
  // Errores de conexión
  detalleError: (ruta: string, tipo: string) => `${ruta} · ${tipo}`,
  probarConexion: 'Probar',
  servicioResponde: 'Servicio activo',
  servicioNoResponde: 'Servicio caído',
  // Intérprete agente (D32)
  chaskiPregunta: 'Chaski pregunta',
  chaskiPreguntaAl: (quien: string) => `Chaski le pregunta ${quien}`,
  chaskiResponde: 'Chaski le responde',
  porQue: 'POR QUÉ',
  falta: 'Falta',
  noLeEntendi: 'No le entendí',
  noLeEntendiExplica: '',
  repetir: 'Repetir',
  fraseVerificada: 'Frase verificada',
  fraseVerificadaExplica: '',
  // Modo emergencia (C11)
  emergencia: 'Emergencia',
  emergenciaExplica: '',
  faltaRevisar: 'Falta revisar el quechua con la enfermera',
  pendienteRevision: 'Pendiente',
  revisadaEnfermera: 'Revisada',
  modoEnsayo: 'Modo ensayo (para el jurado)',
  modoEnsayoExplica: 'Solo para el jurado.',
  faltaRevisarAviso: 'Pendiente',
  bancoLocal: (n: number) => `${n} pendientes`,
  escucharRespuesta: 'Escuchar respuesta',
  volverConsulta: 'Volver',
  // Receta y «¿me lo repite?» (F9, F6)
  confirmeDatos: 'Confirme los datos',
  confirmeDatosExplica: '',
  cuantoPorToma: 'Cuánto por toma',
  cadaCuantasHoras: 'Cada cuántas horas',
  porCuantosDias: 'Por cuántos días',
  faltaParaDecir: (f: string) => `Falta: ${f}`,
  decirAlPaciente: 'Decirle',
  meLoRepite: '¿Me lo repite?',
  meLoRepiteExplica: '',
  loQueEntendio: 'Lo que entendió',
  entendidos: (n: number, total: number) => `${n} de ${total} entendidos`,
  noLoMenciono: 'No lo mencionó',
  explicarLoQueFalto: 'Explicar de nuevo',
  // Glosario (D36)
  palabrasNuevas: 'Palabras nuevas',
  palabrasNuevasExplica: '',
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
  // Sin traducir a propósito: no se inventa quechua. En castellano hasta que la mamá de Freddy lo escriba.
  tocarPausar: 'Pausar',
  hablandoAlPaciente: 'Hablando al paciente',
  hablandoAlPersonal: 'Hablando al personal',
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
