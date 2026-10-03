# mp4_creation

Pipeline para convertir material educativo (presentación + transcripción de clase)
en un video MP4 listo para YouTube, con locución sintética sincronizada con las
diapositivas.

## Retomar el proyecto

**En una nueva sesión, leer primero [CONTINUIDAD_PROYECTO.md](CONTINUIDAD_PROYECTO.md).**
Contiene objetivos, decisiones, estado comprobado, archivos relevantes y próximos pasos.
Los comandos operativos están en [INSTRUCCIONES_TERMINAL.md](INSTRUCCIONES_TERMINAL.md).

Estado documentado al **3 de octubre de 2026**: generación de materiales y archivo
por API de Drive implementados; subida automática a YouTube pendiente. El paso 09
vacía los contenedores después de archivar y verificar, salvo `--conservar-local`.
No se ha ejecutado ese vaciado sobre el material actual.

## Cómo funciona

Diez scripts numerados (00–09) que se corren en orden. Cada uno es independiente,
reejecutable. El guion y los audios existentes se conservan salvo que se use
`--forzar`; el paso 03 vuelve a escribir los textos y el control de calidad se
actualiza en cada ejecución.

```
00_validar_insumos.py   ¿están los archivos, ffmpeg y la credencial?
01_preparar_slides.py   PNG → slide_01.png, slide_02.png… + hoja de contacto
02_escribir_guion.py    transcripción + slides → guion_maestro.md   ← API de OpenAI
        ▼ PARADA: revisión humana del guion
03_dividir_guion.py     guion_maestro.md → un .txt por segmento
04_crear_audios.py      un .txt → un .mp3            ← edge-tts
05_montar_video.py      PNG + audio → video_final.mp4  ← ffmpeg
06_control_calidad.py   reporte, capturas y avisos
07_preparar_youtube.py  guion → título y descripción; primera slide → miniatura
08_crear_cuestionario.py guion + lecturas → cuestionario y respuestas ← API de OpenAI
09_archivar_drive.py    archivo por lección en Drive → verificación → vaciado local
```

`correr_pipeline_guion.py` ejecuta los pasos 00–02 y termina para revisar el
guion. Una vez aprobado, `correr_pipeline_video.py` ejecuta los pasos 03–08.
El paso 09 se ejecuta por separado o con `--archivar-drive` al terminar el segundo pipeline.
`limpiar_proyecto.py` borra `02_archivosIntermedios/` y `03_output/` (los
artefactos regenerables) para empezar de cero, sin tocar el material original.

## Comandos para ejecutar los dos pipelines

La guía completa, con comandos para editar los archivos y resolver errores, está
en [INSTRUCCIONES_TERMINAL.md](INSTRUCCIONES_TERMINAL.md).

El espacio de trabajo es **`01_content`** y se reutiliza para todas las lecciones.
`--proyecto` indica esa carpeta de trabajo, no el número de lección ni del pipeline.

### 1. Entrar a la carpeta del proyecto

Abrí Terminal o la terminal integrada de VS Code y ejecutá:

```bash
cd "/Users/diegoabal/Library/CloudStorage/OneDrive-Personal/Documents/03 - Desarrollo/Cursos/Datascience/02 - Diplomatura (UP)/04 - PROYECTOS/09 - mp4_creation"
```

Los comandos usan `/opt/miniconda3/bin/python3`, el Python con las dependencias
verificadas en esta Mac. Así no dependen de qué `python` o `python3` seleccione
la terminal. En otra computadora, reemplazá esa ruta por la de su entorno Python.

### 2. Preparar el guion: pasos 00 a 02

```bash
/opt/miniconda3/bin/python3 correr_pipeline_guion.py --proyecto 01_content
```

Valida los insumos, prepara las imágenes y genera el guion si todavía no existe.
Termina después del paso 02 para que puedas revisarlo.

### 3. Abrir, editar y guardar el guion

```bash
code "01_content/02_archivosIntermedios/guion/guion_maestro.md"
```

Revisá el contenido y guardá con `Cmd+S`. Conservá los encabezados de diapositiva,
los encabezados de segmento si existen y las marcas `Narración:`.

### 4. Generar el video: pasos 03 a 08

Para la primera generación, cuando todavía no hay audios:

```bash
/opt/miniconda3/bin/python3 correr_pipeline_video.py --proyecto 01_content
```

**Si editaste el guion o cambiaste la voz o el léxico y ya existen audios**, usá:

```bash
/opt/miniconda3/bin/python3 correr_pipeline_video.py --proyecto 01_content --forzar
```

El segundo comando vuelve a dividir el guion, regenera los audios, monta el video
y actualiza el control de calidad, el texto de YouTube y ambos cuestionarios.
También reemplaza las ediciones manuales de esos textos de salida. Es el que corresponde para aplicar tus cambios
al guion actual. No hace falta volver a ejecutar el pipeline del guion.

### 5. Abrir el resultado y el reporte

```bash
open "01_content/03_output/video_final.mp4"
code "01_content/03_output/qc/reporte.md"
open "01_content/03_output/qc/capturas"
```

### Opciones de ejecución

| Necesidad | Comando desde la carpeta del proyecto |
| --- | --- |
| Preparar el guion, conservando el existente | `/opt/miniconda3/bin/python3 correr_pipeline_guion.py --proyecto 01_content` |
| Regenerar el guion con el prompt actual (reemplaza las ediciones manuales) | `/opt/miniconda3/bin/python3 correr_pipeline_guion.py --proyecto 01_content --forzar` |
| Generar video o reintentar usando los audios existentes | `/opt/miniconda3/bin/python3 correr_pipeline_video.py --proyecto 01_content` |
| Incorporar cambios del guion, voz o léxico al video | `/opt/miniconda3/bin/python3 correr_pipeline_video.py --proyecto 01_content --forzar` |
| Empezar de cero: borrar intermedios y salida, y ejecutar 00–02 | `/opt/miniconda3/bin/python3 correr_pipeline_guion.py --proyecto 01_content --limpiar` |

`--limpiar` está disponible solo en el pipeline del guion y **borra sin otra
confirmación el guion editado, textos, audios, segmentos y video final**. Usalo
solo para empezar de cero. Para limpiar con confirmación, ejecutá por separado:

```bash
/opt/miniconda3/bin/python3 limpiar_proyecto.py --proyecto 01_content
```

Ambos pipelines se detienen si falla una etapa. No aceptan `--desde`, `--hasta`
ni `--sin-parada`; para correr una etapa suelta, consultá la guía de terminal.

## Instalación (una vez)

```bash
brew install ffmpeg
/opt/miniconda3/bin/python3 -m pip install -r requirements.txt
```

Los pasos 02, 07 y 08 necesitan `OPENAI_API_KEY` en el entorno o en `.env` en la raíz del
proyecto. Para crear o editar ese archivo:

```bash
code .env
```

Agregá `OPENAI_API_KEY=tu_clave_real` y guardá. El proveedor de voz `edge`
configurado actualmente no necesita esa clave, pero sí conexión a Internet.

## Una lección nueva

Usar siempre `01_content`. Después de archivar y vaciar la lección anterior,
colocar las nuevas diapositivas, exposición y lecturas en las mismas subcarpetas
de `01_materialOriginal`. Ejecutar el pipeline de guion, revisar el guion y su
título, y ejecutar el pipeline de video. Finalmente, archivar con el paso 09:
solo preguntará el número de lección. Los comandos completos están en la sección
«Archivo por API de Google Drive y reutilización de 01_content».

## Conceptos

**Segmento.** La unidad del pipeline no es la diapositiva sino el segmento de
narración. Una diapositiva puede tener varios (`slide_03_a`, `slide_03_b`) para
que una imagen no quede fija cuatro o cinco minutos. Todos los segmentos de una
diapositiva comparten su PNG.

```
slide_03_a.txt  ─┐
                 ├─→ slide_03.png
slide_03_b.txt  ─┘
```

**El guion es la fuente de verdad.** El paso 02 lo genera, pero el que se usa es
el archivo en disco: editalo todo lo que haga falta antes del paso 03.

**Estilo de locución.** El paso 02 carga siempre `config/estilo_guion.md`, que
recoge el estilo del guion revisado: explicación oral natural, ejemplos concretos,
párrafos breves y desarrollo paso a paso. Incluye ejemplos de voz y pautas para
síntesis de voz. Este archivo se conserva aunque se limpien los intermedios y
se aplica también a proyectos nuevos; no depende de que exista un guion anterior.
Las reglas compartidas de redacción viven en `guion.reglas`; no se cambian según el tema.

La exposición es la fuente principal. Las fichas y los archivos de
`insumos.bibliografia` se envían como apoyo secundario. La bibliografía admite
`.md`, `.txt` y PDF con texto extraíble (requiere `pypdf`); un PDF sin texto exige
OCR o una versión de texto antes de generar el guion. Por defecto se busca en
`01_materialOriginal/material_bibliográfico/`; la ruta puede ajustarse en YAML.

**Pronunciación.** El guion se escribe en castellano normal (`LCR`, `cash flow`)
y la corrección fonética vive en `config/lexico.yaml`, que se aplica recién al
sintetizar. Así el guion sigue siendo legible y la corrección sirve para todos
los videos.

**Transición de apertura.** Cada diapositiva puede abrir con dos mecanismos
independientes y combinables, aplicados solo a su primer segmento (nunca a los
`b`, `c`... que comparten imagen con el anterior):

- `guion.transicion_titulo` — el modelo redacta una frase de transición propia
  que menciona el título o su sentido dentro de la explicación. También se
  aplica cuando se repite el título: la apertura enlaza con el contenido nuevo,
  sin anunciar otra sección. Es una instrucción de `02_escribir_guion.py`.
- `audio.pausa_inicial_seg` — silencio real antepuesto al audio, vía el filtro
  `adelay` de ffmpeg (`comun/ffmpeg.py::anteponer_silencio`). No se puede lograr
  pidiéndoselo al modelo de texto ni depender de que el proveedor de voz
  soporte SSML, así que se inserta después de sintetizar — mismo punto donde se
  aplica el léxico de pronunciación.

## Configuración

`config/lexico.yaml` y `01_content/proyecto.yaml` se reutilizan en todas las lecciones.
Cambiar el contenido no exige editar el YAML. Sus parámetros controlan la producción;
lo que no esté ahí toma el valor por defecto de `comun/config.py`.

| Clave | Para qué |
| --- | --- |
| `guion.modelo` | Configurado en `gpt-6-astra`, con esfuerzo `high` |
| `guion.reglas` | Reglas editoriales que recibe el modelo |
| `guion.duracion_objetivo_min` | Largo buscado del video |
| `guion.max_segmentos_por_slide` | Cuánto puede subdividirse una diapositiva |
| `guion.transicion_titulo` | El primer segmento de cada diapositiva abre con una frase de transición |
| `audio.proveedor` | `edge` (gratis) · `openai` · `existente` |
| `audio.voz` | `es-UY-ValentinaNeural`, `es-AR-ElenaNeural`, `es-UY-MateoNeural`… |
| `audio.pausa_inicial_seg` | Silencio antepuesto al primer segmento de cada diapositiva (`0` lo apaga) |
| `video.movimiento` | `ninguno` o `kenburns` (deriva lenta en segmentos largos) |

El guion está configurado con `gpt-6-astra`/`high`, máximo de salida de 32.000 tokens,
duración objetivo de 22 minutos y hasta 5 segmentos por diapositiva. YouTube usa
`gpt-5.4`/`medium` y el cuestionario `gpt-5.4`/`high`. El cambio a Astra se validó
al cargar el YAML, pero todavía no se probó una generación real con ese modelo.
El valor de respaldo en `comun/config.py` sigue siendo `gpt-5.4`; prevalece el YAML.
Una revisión editorial automática en una segunda llamada fue propuesta, no implementada.

## Tests

```bash
/opt/miniconda3/bin/python3 -m pytest tests/ -q
```

Cubren lo que más fácil se rompe en silencio: el orden de las diapositivas y los
caracteres invisibles en sus nombres, el parseo del guion editado a mano, y los
reemplazos del léxico.

## Qué queda manual

Preparar las fuentes, exportar la presentación a PNG y revisar el guion antes
de producir el video. Revisar también los entregables antes de distribuirlos.
La publicación en YouTube aún es manual. El pipeline toma las imágenes de
`01_materialOriginal/slides/` con cualquier nombre, siempre que terminen en un
número.

## Título y descripción para YouTube

El paso 07 del pipeline de video usa la API de OpenAI y el
guion maestro revisado para generar `01_content/03_output/youtube.txt`. El archivo
incluye un título y una descripción listos para revisar y copiar. No publica el video.
El paso también copia la primera diapositiva normalizada a `03_output/miniatura.png`,
incluso si `youtube.txt` ya existe. Es una portada basada en el slide, sin diseño
adicional por IA. Requiere haber ejecutado el paso 01.
Requiere `OPENAI_API_KEY`, conexión a Internet y consume tokens de la API.

Para generar solo este texto, sin rehacer los audios ni el video:

```bash
/opt/miniconda3/bin/python3 07_preparar_youtube.py --proyecto 01_content
code "01_content/03_output/youtube.txt"
```

Si ya existe, se conserva. Para reemplazarlo después de modificar el guion:

```bash
/opt/miniconda3/bin/python3 07_preparar_youtube.py --proyecto 01_content --forzar
```

Podés editar `youtube.modelo`, `youtube.esfuerzo`, `youtube.max_output_tokens`
y las reglas editoriales comunes en `proyecto.yaml` si querés modificar el
comportamiento general. No hace falta hacerlo al cambiar de tema. El prompt
está en `07_preparar_youtube.py`.
El archivo de salida se configura en `salidas.youtube`. `--limpiar` también lo borra.
Si falla el paso 07, el MP4 ya generado se conserva; corregí el error y reintentá
solo este paso. La descripción se basa en el guion: revisá que el video publicado
corresponda a esa misma versión.

## Cuestionario y respuestas

El paso 08 cierra el pipeline de video y usa la API de OpenAI con el guion
final, las fichas y la bibliografía. Necesita `OPENAI_API_KEY`, Internet y
consume tokens. Requiere al menos una lectura: no omite esa fuente si falta.

Produce dos archivos en `03_output`:

- `cuestionario.txt`: instrucciones, diez preguntas con cuatro opciones y hoja de respuestas.
- `cuestionario_resuelto.txt`: las mismas preguntas, respuesta correcta, explicación,
  análisis de cada alternativa y fragmentos de las fuentes que fundamentan la solución.

La dificultad crece: 1–4 comprenden el video; 5–8 aplican y relacionan ideas del
video y lecturas; 9–10 integran mecanismos y aportes de las lecturas que no bastan
con el video solo. Hay una única opción correcta. Las instrucciones permiten
consultar ambos materiales. Revisá la calidad pedagógica antes de distribuirlo;
la validación automática controla estructura y citas, no garantiza la dificultad.

Generarlo sin rehacer el video:

```bash
/opt/miniconda3/bin/python3 08_crear_cuestionario.py --proyecto 01_content
code "01_content/03_output/cuestionario.txt"
code "01_content/03_output/cuestionario_resuelto.txt"
```

Para regenerar las dos versiones después de editar el guion o las lecturas:

```bash
/opt/miniconda3/bin/python3 08_crear_cuestionario.py --proyecto 01_content --forzar
```

Ambas versiones se generan a partir de una única respuesta de IA. Si ya existen,
se conservan; si existe solo una, se pide `--forzar` para evitar mezclar versiones.
`--limpiar` las borra. Las opciones del modelo están en `cuestionario` en
`proyecto.yaml`; el prompt está en `08_crear_cuestionario.py`. Si falla esta etapa,
se puede reintentar por separado y los resultados anteriores se conservan.

## Archivo por API de Google Drive y reutilización de 01_content

`01_content` es un espacio de trabajo reutilizable para una lección a la vez.
No hace falta crear otra carpeta ni editar el YAML para cambiar de tema.
Las reglas de redacción y producción son comunes; solo cambian los materiales.
El paso 02 infiere el título de la lección de las diapositivas y la exposición,
y lo guarda en la primera línea del guion maestro:

```markdown
# Guion de locución — Título de la lección
```

Si querés corregirlo, editá ese encabezado durante la revisión del guion, antes
de ejecutar el pipeline de video. Los cuestionarios, la publicación y el archivo
usan ese título como referencia. YouTube genera además su propio título editorial.
El paso 07 copia la primera diapositiva normalizada como `03_output/miniatura.png`;
no usa la antigua miniatura de la raíz ni requiere reglas según el tema.

El paso 09 pide **solo el número de lección** si no se proporciona en los
argumentos. En Drive crea `Lección 01 - Título/version_…`, dentro del destino
configurado. El mismo contenido reutiliza su versión; material diferente crea
una nueva. No modifica ni elimina versiones anteriores. La carga anterior,
hecha con la organización por proyecto, permanece en su ubicación original.

**Al terminar una carga y verificar todos los archivos y el inventario remoto,
el paso 09 borra los archivos de estos tres contenedores:**

- `01_content/01_materialOriginal`
- `01_content/02_archivosIntermedios`
- `01_content/03_output`

Conserva las carpetas y subcarpetas vacías, el YAML, los scripts y las credenciales.
Los archivos externos a esos contenedores no se borran. La miniatura de cada
lección se genera dentro de output y se archiva y limpia junto con los demás resultados.
El respaldo incluye también los archivos auxiliares y formatos que antes se
omitían, en `08_Respaldo_completo`, aunque `incluir_intermedios` esté desactivado.
Los enlaces simbólicos y las credenciales dentro de los contenedores bloquean
la operación: deben retirarse antes. Las credenciales de la raíz no se suben.

Si falla la carga o la verificación, no empieza la limpieza. Si cambió el conjunto
o contenido de los archivos locales durante la carga, tampoco empieza.
Una interrupción durante el borrado puede dejar algunos archivos locales;
el respaldo completo ya estará en Drive. No editar los contenedores mientras
se ejecuta este paso.

El inventario con los enlaces queda fuera del área que se vacía, en
`historial_drive/leccion_NN_VERSION.json`, además de guardarse en Drive.

### Comandos (desde la raíz del repositorio)

Simular sin conectar ni borrar:

```bash
/opt/miniconda3/bin/python3 09_archivar_drive.py --proyecto 01_content --simular
```

Archivar: preguntará solo el número de lección, y **vaciará los contenedores al finalizar**:

```bash
/opt/miniconda3/bin/python3 09_archivar_drive.py --proyecto 01_content
```

Archivar sin borrar los archivos locales:

```bash
/opt/miniconda3/bin/python3 09_archivar_drive.py --proyecto 01_content --leccion 1 --conservar-local
```

Para la siguiente lección se vuelven a colocar sus fuentes en las mismas carpetas,
sin modificar la configuración y se ejecutan los dos pipelines:

```bash
/opt/miniconda3/bin/python3 correr_pipeline_guion.py --proyecto 01_content
# Revisar y editar el guion maestro antes de continuar.
/opt/miniconda3/bin/python3 correr_pipeline_video.py --proyecto 01_content
/opt/miniconda3/bin/python3 09_archivar_drive.py --proyecto 01_content --leccion 2
```

También se puede integrar el archivado y vaciado al pipeline de video:

```bash
/opt/miniconda3/bin/python3 correr_pipeline_video.py --proyecto 01_content --archivar-drive --leccion 2
```

### Conexión

El destino está en `drive.carpeta_id`. Para Mi unidad se utiliza un cliente OAuth
**Aplicación de escritorio** con Google Drive API habilitada. Su JSON se guarda
como `credentials.json` en la raíz. El token se guarda en `.drive/token.json`.
Ambos están excluidos de Git. El alcance OAuth permite administrar Drive; el
script limita sus escrituras a la carpeta configurada y conserva sus permisos.

```bash
/opt/miniconda3/bin/python3 -m pip install -r requirements.txt
/opt/miniconda3/bin/python3 09_archivar_drive.py --proyecto 01_content --comprobar
```

`--comprobar` verifica la conexión sin subir ni borrar. Tanto `--comprobar` como
`--simular` arman primero el inventario y requieren los entregables y la miniatura;
si falta esta última, ejecutar el paso 07. La autorización puede
requerir elegir la cuenta en el navegador. Las cuentas de servicio solo se
admiten para unidades compartidas.

## Subida automática a YouTube: pendiente

Todavía no hay un script ni un comando de subida a YouTube. El paso 07 solo
prepara archivos locales. La integración por YouTube Data API v3 se conversó,
pero no se implementó ni se autorizó un canal.

Plan para continuar:

1. Habilitar YouTube Data API v3 en Google Cloud y autorizar el canal por OAuth.
   El cliente OAuth de `credentials.json` se puede reutilizar; el permiso de
   Drive no autoriza YouTube. Guardar su token separado y excluirlo de Git.
2. Subir MP4, título, descripción y miniatura; guardar el ID y enlace fuera del
   área que se vacía y evitar repetir una carga que ya terminó.
3. Ejecutar el archivo en Drive incluyendo el enlace de YouTube.
4. Vaciar los contenedores solo cuando ambas operaciones hayan sido verificadas.

**El orden actual aún no incluye YouTube.** No agregar una subida después del
paso 09 sin cambiar el flujo: el video local ya podría haberse borrado.
Mientras se prepara la integración, `--conservar-local` permite archivar en Drive
conservando el video para publicarlo manualmente o probar la futura subida.

Google restringe a privado las subidas mediante proyectos API no auditados creados
después del 28 de julio de 2020. Levantar esa restricción requiere una auditoría
del proyecto API; no se resuelve solo con el consentimiento OAuth. Revisar la
[documentación de videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)
al implementar. La carga privada es el punto de partida propuesto; falta definir
el canal y la visibilidad deseada. Ver también la
[guía oficial de carga](https://developers.google.com/youtube/v3/guides/uploading_a_video).
