# Medios de la enfermera · dónde está cada archivo y para qué (sáb 24-oct, 21:25 PT)

> Los archivos viven **solo en la Mac de Freddy**, en `data/mama/` (está en `.gitignore`: son su voz y su cara; no se
> suben al repo). Este índice sí está en git para que cualquiera sepa qué hay y dónde va. Ella dio permiso para usarlos
> y para mostrar su nombre: **Lic. Norma Choque Guerreros**, enfermera de la zona sanitaria de Pilpichaca.
>
> Etiquetas del nombre de archivo: **`PITCH-`** va en la presentación de 3 min · **`VIDEO-NN`** va en el video de Devpost,
> en ese orden · **`RESPALDO`** si el principal falla · `extra/` material sin uso asignado.

## Video (horizontal 1024×576, con subtítulos en inglés `.en.srt` al lado) · `data/mama/video/clips/`

| Archivo | Dura | Qué dice (castellano) | Va en |
|---|---|---|---|
| **`PITCH-B1_problema-profesionales-costa_16s.mp4`** | 16 s | «Muchas veces vienen aquí a trabajar profesionales de la costa, y ellos no entienden el quechua» | **Pitch, apertura (0:00–0:16)** |
| `VIDEO-01_presentacion-nombre_16s.mp4` | 16 s | «Soy la licenciada Norma Choque Guerreros, enfermera de Huancavelica, Perú. Trabajo en la zona sanitaria de Pilpichaca. Hablo quechua, runa simi» | Video Devpost, 1.º |
| `VIDEO-02_problema-yo-traduzco_21s.mp4` | 21 s | «Cuando vienen los profesionales de la costa no hablan quechua. Cuando no entienden, yo lo soluciono, yo traduzco» | Video, 2.º |
| *(VIDEO-03: la negativa de Chaski, grabación de pantalla de la app)* | — | — | Video, 3.º |
| `VIDEO-04_atiende-ninos-emergencias_16s.mp4` | 16 s | «Atiendo a los niños, las enfermedades, las emergencias, porque esta población habla quechua» | Video, 4.º (antes de la consulta y el modo emergencia) |
| `VIDEO-05_medicamentos-junto-a-receta_16s.mp4` | 16 s | «…cómo lo deben tomar o administrar, qué deben tomar; eso lo ayudo traduciendo» | Video, 5.º, junto a la función **receta** |
| *(VIDEO-06: A/B/C de voz, de Ricardo: `ricardo-artifacts/reports/voces/mama_freddy/`)* | — | Voz de Meta → voz de Chaski → ella (`C_real.mp3`) | Video, 6.º; y pitch B5 si pasa la prueba a ciegas |
| `VIDEO-07_confianza-pacientes_31s.mp4` | 31 s | «Los pacientes me dicen: ayúdame, interprétame. La enfermera sabe quechua, vamos a consultarle. Me alegro cuando me dan su confianza» | Video, 7.º (momento emocional) |
| `VIDEO-08_saludo-eeuu-cierre_14s.mp4` | 14 s | «Me alegra hablar quechua. Mando un saludo desde Huancavelica, Perú, al pueblo de Estados Unidos. Muchas gracias» | Video, cierre |
| `RESPALDO_problema-otra-toma_16s.mp4` | 16 s | Otra toma del problema | Si el de PITCH no sirve |

Originales: `data/mama/video/originales/` (3 videos de ~3 min). Traducción completa por ventanas: `data/mama/video/traduccion-videos.md`; subtítulos de todos los clips: `data/mama/video/clips/subtitulos.md`.

## Audio · `data/mama/audio/clips/`

| Archivo | Dura | Qué dice | Va en |
|---|---|---|---|
| `RESPALDO-PITCH-B1_problema-profesionales_14s.mp3` | 14 s | «A veces los profesionales no entienden el quechua; entonces yo ayudo, hago la traducción» | Pitch, si el video falla en la sala |
| `VIDEO-07b_recibe-paciente-como-en-casa_29s.mp3` | 29 s | Recibiendo a una paciente (Kati): «aquí, conmigo, va a estar bien… dígame con confianza… siéntese aquí, como en su casa» | Video, bajo el 07 o en su lugar |
| `extra/` | — | Saludos y presentaciones de los primeros audios | Sin uso asignado |

Originales: `data/mama/audio/originales/`. Transcripción MMS y traducciones: `data/mama/audio/*.md|txt`.

## Prueba a ciegas de la voz · `data/mama/prueba-ciegas-para-mama/`

8 audios («Frase N (tema) - voz X/Y.mp3») enviados a la enfermera. La clave está aparte en
`data/mama/prueba-ciegas-CLAVE-NO-ENVIAR.json` (no se le muestra). Su respuesta decide qué voz usa el modo emergencia.

## Cómo se transcribieron
MMS de Meta (`facebook/mms-1b-all`, adaptador `quy`), localmente en la Mac, en ventanas de 5 s; traducido con Claude
Opus; los subtítulos en inglés también con Claude, sin inventar lo que no se entiende. Script: `~/.cache/transcribe/mms_ventanas.py`.
