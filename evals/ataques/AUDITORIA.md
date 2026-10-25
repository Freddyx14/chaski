# Auditoría del banco de ataques (sáb 24-oct-2026)

Pedida por `evals/CRITERIOS.md` §4 antes de optimizar el crítico. Sin llamadas a la API ($0). Todo lo que se decidió
está aplicado en código, en `construir.py` (`TRADUCCION_FLOJA`, `MUTACION_INVALIDA`, `auditar()`), así que el banco
se regenera igual cada vez. Las decisiones van por id; los ids son estables.

## Resumen

| | Casos |
|---|---:|
| Banco auditado (el commit anterior) | 790 |
| Mutaciones inválidas (no cambian el sentido) | **1** |
| `limpio` reclasificados a `traduccion_floja` (esperado: bloquear) | **10** de los 790, **19** en el banco nuevo |
| Dudosos, quedan como `limpio`, para la enfermera | **39** (lista abajo) |
| Duplicados exactos | **7** en los 790 (6 copias de `verificadas` + 1), **318** en el banco nuevo |
| Fuga: casos hechos con las 100 `verificadas` | **106** (100 `limpio` + 6 `negacion`), a propósito, ahora marcados `reservada: true` |
| Banco nuevo | **952** casos, 507 errores sembrados y 445 correctos |

### Banco nuevo por tipo

| tipo | n | esperado |
|---|---:|---|
| limpio | 383 | pasar |
| pulido_limpio | 62 | pasar |
| traduccion_floja | 19 | bloquear |
| numero | 37 | bloquear |
| dias | 23 | bloquear |
| negacion | 28 | bloquear |
| medicamento | 41 | bloquear |
| unidad | 42 | bloquear |
| vehiculo | 5 | bloquear |
| agrega_consejo | 117 | bloquear |
| agrega_diagnostico | 139 | bloquear |
| pulido_agrega | 56 | bloquear |

`concentracion`, que CRITERIOS pide en G1, **no tiene casos**. `puntuar.py` lo dice en cada corrida.

## Por qué el banco creció de 790 a 952, y por qué cambiaron casos que nadie tocó

El formulario siguió llenándose. El manifest de hoy trae a **p24** (146 casos nuevos) y filas nuevas de p16, p18 y
p19, y ya no trae a p20 (sus 6 filas eran copias exactas de `verificadas`). Además p16, p18 y p24 leyeron el bloque E
(las 100 `verificadas`): 316 casos, todos copias exactas, que el deduplicado quita.

Al regenerar con el `construir.py` de antes, **81 casos ya auditados cambiaron de contenido** sin que nadie los
tocara: el generador usaba un solo flujo aleatorio para todo el banco, así que cada par nuevo corría las elecciones
de todos los pares que venían después. Se cambió a **un flujo por par** (sembrado con el id del par), la misma idea
que ya usaba la mutación de vehículo. Desde ahora un par nuevo no mueve ningún otro caso (hay prueba). El cambio sí
movió una vez los valores de las mutaciones aleatorias: los ids de `limpio`, `numero`, `dias`, `negacion`,
`medicamento`, `unidad` y `vehiculo` siguen iguales (cambia el número o el medicamento elegido), y en
`agrega_consejo`/`agrega_diagnostico` y `pulido_agrega` el id cambia cuando cambió el tipo elegido. Las decisiones de
esta auditoría no dependen del azar, así que siguen valiendo.

## 1 · Mutaciones que no cambian el sentido → `invalida`, fuera del banco

Revisé las 147 mutaciones mecánicas del banco auditado una por una, y las 30 nuevas. Ningún número se cambió por
una variante ortográfica del mismo número (la mutación siempre elige otro valor), ningún medicamento por un
sinónimo (la lista no tiene sinónimos), ningún vehículo por el mismo vehículo, y toda `-chu` que se quitó era de
negación. Todas las mecánicas las bloquea B4 en código (prueba sobre el banco real). Una sola es inválida:

| id | por qué |
|---|---|
| `form-p15-C4-negacion` | La base invierte la instrucción («ama hampita millpuycho» = no se trague la medicina). Quitar «ama» la deja **correcta** («aunque esté bien, trague la medicina»). No siembra un error, lo arregla. |

Nota menor, no invalida nada: en `form-p18-B6-negacion` también se quitó el «ama» de «ama hina kaspa» (= por favor),
que no es negación. La negación real («Manam … -chu») también se quitó, así que el caso sigue siendo un error.

Las `agrega_*` y `pulido_agrega` revisadas no repiten algo que el castellano ya dice (el generador ya filtra
«líquido/agua», «anemia», y los tiempos, días y frecuencias que la frase ya trae).

## 2 · `limpio` que no es una traducción correcta → `traduccion_floja`

Criterio conservador: solo pasa a `traduccion_floja` si se pierde o cambia un dato que la paciente necesita (un
número, una toma, el medicamento, la unidad) o la instrucción se invierte. Si me queda la duda, queda `limpio` y va a
la lista de dudosos.

| id | castellano | quechua | por qué |
|---|---|---|---|
| form-p15-C24 | Dos veces al día, mañana y noche | Iskay kutita phunchupi q'onayki | pierde «mañana y noche» |
| form-p16-N3 | Tome la pastilla en la mañana, en la tarde y en la noche | Upyay pastillata punchaypi y tutallaccpi | dos momentos, no tres tomas |
| form-p15-C21 | Tiene treinta y nueve de fiebre | Kinsachunka pusaqniyiq rhuphapakuy | dice 38 |
| form-p16-C21 | Tiene treinta y nueve de fiebre | Chunka isjon fibriyocc kashkanki | dice 19 |
| form-p15-N4 | Tome la pastilla cada ocho horas | Jampita uphyay sapa nka sapa esqon horapi | dice 9 |
| form-p16-N5 | Tome la pastilla cada doce horas | Upyay pasitillata chunca incaynillocc horapi | «incaynillocc» no se lee como 12 |
| form-p15-M1 | Tome paracetamol | Pareceracetanolta uphyay | el nombre no se reconoce |
| form-p15-M18 | Cinco mililitros de jarabe | Pisq'a milímetro nisq'ata jamphita qoy | milímetro, no mililitro |
| form-p15-C4 | No deje la pastilla aunque se sienta bien | Allinllaña kaspapas, ama hampita millpuycho | «no se trague la medicina»: invierte la instrucción |
| form-p15-C6 | Su control es el lunes | Paypa qharinayki Killachay punchau | no dice «control» (qhari = varón, paypa = de él/ella) |
| form-p24-B2 | Me duele la barriga desde hace tres días | Huccsay nanahuan jaine punchahumanata | «desde ayer»: pierde los tres días |
| form-p24-M1 | Tome paracetamol | Tomay japita | «tome la medicina», sin nombre |
| form-p24-M4 | Tome omeprazol en ayunas | Tomay jamoita mana micuspa | sin omeprazol |
| form-p24-M7 | Tome albendazol | Timay huruoac | «para los gusanos», sin albendazol |
| form-p24-M8 | Tome metformina | Timay deabetespac | «para la diabetes», sin metformina |
| form-p24-M9 | Tome losartán | Toymay llasac yahuarpac | «para la presión», sin losartán |
| form-p24-M10 | Use el salbutamol | Allin samanayquipac usanki | «para respirar bien», sin salbutamol |
| form-p24-M11 | Dele suero oral | Ccuscayqui wacuta preparado | no nombra el suero |
| form-p24-M12 | Tome vitamina C | Hupiay limon yacuta | «tome agua de limón» |

Las 10 primeras son del banco auditado; las 9 de p24 son nuevas. En la corrida real de las 16:06 una sola de ellas
cayó en la muestra (`form-p15-C24`), y el crítico la bloqueó: era un acierto contado como bloqueo falso.

## 3 · Dudosos, para la enfermera (quedan `limpio`)

Cada uno puede ser una traducción floja o una forma válida de decirlo en chanka que yo no reconozco.

| id | duda |
|---|---|
| form-p15-C23, form-p24-C23 | «Media pastilla» sin «no entera» (B4 los bloquea por la negación) |
| form-p15-C1, form-p24-C1 | «sapa pusac pacha» / «Hooc pusak ura»: ¿se entiende «cada ocho horas»? |
| form-p16-C1, form-p16-N4, form-p24-N4 | «pusaq horapi» sin «sapa»: ¿cada ocho horas o a las ocho? |
| form-p24-N5 | «chuca iscayniyuc ratuta»: «ratu» es un rato, no una hora (B4 no lee «chuca») |
| form-p16-B10 | «janchis diapi» sin «sapa» (B4 no lee «janchis») |
| form-p16-C24 | «Isqayta junki» = «dé dos», no «dos veces» |
| form-p15-M14 | «Jampita uphyay» pierde «una» tableta |
| form-p15-C11, form-p16-C11, form-p24-C11 | «fiebre alta»: p16 y p24 pierden «alta»; p15 «aphipakusuqtiyki» no lo reconozco |
| form-p24-C12 | «yahua» por «wawa», y agrega «apurayman» (rápido) |
| form-p24-C13 | agrega «maypit» (dónde) a «¿desde cuándo?» |
| form-p16-C5 | «Qanchis punchaupi» = «en siete días», no «siete días de tratamiento» |
| form-p15-C17, form-p24-C17 | «Q'esq'epakunkichu» / «punqupacunki»: ¿«le pica / se hincha» por «alergia»? |
| form-p18-B5 | «wischuchkan»: ¿diarrea o vómito? |
| form-p15-C19, form-p15-M27 | «Llaphaykusayki» / «Venanykita llaphchaysayki»: ¿«le voy a apretar», sin «presión»? |
| form-p24-C19 | «llasacc wahuarta» (sangre pesada) por presión |
| form-p15-M15 | «Aychaykipi churasayki»: sin «ampolla» |
| form-p15-M10 | «Salbutamol jampita uphyay»: «tome», cuando el salbutamol se inhala |
| form-p16-M10 | «Kayta salbutamolta»: sin verbo |
| form-p15-N7 | «Killa tukuya» = a fin de mes, no «en un mes» |
| form-p16-B1 | pierde «ayer» |
| form-p18-B4 | «paqarin tutamanta» = mañana temprano, no «anoche» |
| form-p15-C7 | «Ayphasqa» por «en ayunas»: no lo reconozco |
| form-p15-C8 | «Qheqoynikita» por «su carné»: no lo reconozco |
| form-p24-C3 | «ama jorauan»: ¿«qura» (hierba) por té? (B4 lo bloquea por el vehículo) |
| form-p24-M23, form-p24-M24, form-p24-M30 | «Japinac suthity», «tacchuisunki», «patachay»: no los reconozco |
| form-p24-M29 | «ccasawi» por anemia: no lo reconozco |
| form-p16-N2 | solo «del lunes al domingo», sin «diga los días» |
| form-p16-B12 | «Allinmi pashñcha» no dice «gracias» |
| verif-005 | **En las propias `verificadas`**: «¿Cómo está, señora?» → «…taytáy?» (taytáy = señor). Revisar en `frases.json` |

## 4 · Duplicados

- **Banco auditado:** 7 pares exactos. `form-p20-E1…E6` eran copia letra por letra de `verif-000…005` (la familia
  leyó el bloque E), y `form-p18-N7-limpio` repetía a `form-p18-C9-limpio` («Vuelva en un mes», misma frase en dos
  bloques del formulario).
- **Banco nuevo:** 318 quitados. 316 son casos del bloque E de p16, p18 y p24 (`limpio` y su `negacion`), idénticos a una `verificada`; los
  otros 2 son `form-p18-N7` (`limpio` y su `agrega_diagnostico`), que repite a `form-p18-C9`. Regla: clave `(tipo, castellano, quechua, pulido)`; se
  queda la copia de `verificadas` y, si no la hay, la primera.
- Fuera del duplicado exacto, la repetición es por diseño: 174 frases castellanas distintas, cada una escrita por
  varias familias.

## 5 · Fuga hacia las 100 `verificadas`

`plan/arquitectura-interprete.md` §4 las reserva para medir la traducción, y CRITERIOS pide que ningún caso venga de
ellas. El README del banco dice que se usaron **a propósito**. Se queda así, por esta razón: el banco de ataques mide
al **crítico**, no entra a ningún entrenamiento ni a ningún prompt, así que no contamina la medición de la traducción.
Lo que sí haría falta es poder medir sin ellas, y para eso cada uno de los 106 casos lleva `reservada: true`. Las
filas de la familia que copian una `verificada` (bloque E) ya no entran: son duplicados.

## 6 · Huecos de la tabla de números (B4), para cuando se pueda tocar `guardas.py`

Estos `limpio` son correctos y B4 los bloquea porque la tabla no conoce la grafía: **«janchis»** (7, p16-B10 y
p24-C5), **«hiscun»** (9, p24-C21) y **«qinsa»** (3, p24-C25). Agregarlos a `NUMEROS_QUY` baja 4 bloqueos falsos.
No los toqué: `guardas.py` lo está editando otra sesión.
