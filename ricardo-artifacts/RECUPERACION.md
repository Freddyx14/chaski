# Si algo se rompe

> Sábado 24 de octubre de 2026, ~03:00 PT. Escrito justo después de mergear a `main`.

## El punto de rescate

Antes del merge, `main` estaba en `adb4e2c`. Está etiquetado y subido:

```bash
git fetch --tags
git log --oneline antes-merge-ricardo -1     # ver qué había antes
```

**Volver atrás sin romperle nada a Freddy** (deshace el merge dejando un commit nuevo, no reescribe
historia, así que él no tiene que hacer nada raro):

```bash
git checkout main && git pull
git revert -m 1 <sha-del-merge>
git push origin main
```

Si hiciera falta el martillo —y solo si Freddy está de acuerdo, porque le reescribe la historia:

```bash
git reset --hard antes-merge-ricardo && git push --force-with-lease origin main
```

## Qué se verificó antes de mergear

| | |
|---|---|
| Archivos que tocan los dos | ninguno |
| `git merge-tree` | exit 0, 0 conflictos |
| Pruebas de Freddy (`app/tests`) después del merge | **20 pasan** |
| Pruebas mías (`ricardo-artifacts/tests`) | **26 pasan** |
| Archivos `.env` versionados | 0 |

Todo lo mío vive en `ricardo-artifacts/`. **No modifiqué ni un archivo de `app/`.**

## Lo único que los conecta, y cómo falla

`servicio/app.py` y `servicio/auditoria_rapida.py` **importan** el módulo de Freddy:

```python
from rimay.auditoria import auditar, SISTEMA_TRADUCIR, extraer_hechos, traducir, retraducir
from rimay.hechos import comparar
```

Si él renombra alguna de esas funciones, **falla mi lado, no el suyo**, con un `ImportError` claro al
arrancar mi servicio. Su app sigue igual. El arreglo es cambiar el nombre en dos archivos míos.

`servicio/app.py` ya lo contempla: si no encuentra el módulo, levanta igual con
`traductor_de_freddy: false` en `/salud` y solo se cae la ruta `/traducir`.

## Si el servicio local no arranca

| Síntoma | Causa casi segura | Arreglo |
|---|---|---|
| `ModuleNotFoundError: rimay` | falta `../app` en `PYTHONPATH` | `PYTHONPATH=.:../app` |
| `/salud` dice `clave_anthropic: false` | no cargaste el `.env` | `set -a; source .env; set +a` |
| Todo responde 500 al llamar a la voz | el túnel se cayó | reabrir el túnel SSH |
| `/turno/paciente` tarda 20 s la primera vez | el modelo se está cargando en la GPU | normal, la segunda baja a 2 s |

## Si la instancia se perdió

El respaldo vive en el disco raíz, que sobrevive al apagado: `~/chaski-respaldo`, 18 GB.

```bash
ssh -i ~/.ssh/id_rsa_aws ubuntu@<IP-NUEVA> 'bash ~/restaurar.sh'     # ~2 min
```

**Si la instancia se terminó en vez de detenerse**, el disco raíz se borró con ella y el respaldo también.
Entonces hay que reconstruir desde cero, que son 12 a 15 minutos:

```bash
scp -i ~/.ssh/id_rsa_aws ricardo-artifacts/voz/instancia_setup.sh ubuntu@<IP>:~
ssh -i ~/.ssh/id_rsa_aws ubuntu@<IP> 'bash ~/instancia_setup.sh'
scp -i ~/.ssh/id_rsa_aws ricardo-artifacts/servicio/instancia.py ubuntu@<IP>:/opt/dlami/nvme/chaski/
```

Ese script lleva dentro las cuatro trampas que costaron tiempo anoche: torch 2.8.0 exacto para
`fairseq2n`, numpy 1.26.4 contra pyarrow, la caché de fairseq2 enlazada al NVMe, y `lang` como lista.

## Si el demo se cae en vivo

En orden, de menos a más pérdida:

1. **La GPU no responde** → la página sigue funcionando con las versiones falsas del contrato:
   `entender`, `hablar` e `idioma` devuelven datos fijos. El flujo se ve, sin modelos.
2. **Claude no responde** → la visión y la traducción caen; el reconocimiento de voz sigue vivo.
3. **Cartesia sin créditos** → el dictado deja de funcionar. Se escribe a mano en el cuadro de texto.
4. **Nada funciona** → quedan los audios ya generados en `datos/muestras_quy/` y las capturas de los
   reportes. El video de respaldo de Devpost es obligatorio por eso.

## Las claves

Están en `ricardo-artifacts/.env`, que git ignora. **Rótalas cuando termine el hackathon**: se pegaron
en un chat. En el repo solo hay `.env.example` con valores de mentira.
