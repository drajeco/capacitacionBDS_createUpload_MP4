# Guía de terminal: ejecutar y editar los pipelines

Los comandos están preparados para esta Mac y el proyecto existente `01_content`.
Ejecutá cada bloque cuando corresponda; entre ambos pipelines hay una revisión
manual del guion. Esta guía no ejecuta nada por sí sola.

Para retomar una sesión, leer primero [CONTINUIDAD_PROYECTO.md](CONTINUIDAD_PROYECTO.md).
Estado al 3 de octubre de 2026: Astra configurado para el guion; Drive conectado;
subida privada a YouTube implementada; OAuth conectado al canal Capacitacion BDS. No se vació el contenido real en las últimas modificaciones.

## Entrar al proyecto

```bash
cd "/Users/diegoabal/Library/CloudStorage/OneDrive-Personal/Documents/03 - Desarrollo/Cursos/Datascience/02 - Diplomatura (UP)/04 - PROYECTOS/09 - mp4_creation"
```

En todos los comandos usamos `/opt/miniconda3/bin/python3` para elegir el entorno correcto.
`--proyecto 01_content` selecciona el espacio de trabajo reutilizable para todas
las lecciones. No hace falta crear otra carpeta ni otro YAML.

## Flujo habitual

### A. Preparar un guion: pasos 00, 01 y 02

```bash
/opt/miniconda3/bin/python3 correr_pipeline_guion.py --proyecto 01_content
```

Si ya existe un guion, lo conserva. Para generar una nueva versión con las
instrucciones actuales, reemplazando las ediciones manuales:

```bash
/opt/miniconda3/bin/python3 correr_pipeline_guion.py --proyecto 01_content --forzar
```

### B. Revisar las imágenes y editar el guion

```bash
open "01_content/03_output/qc/hoja_de_contacto.png"
code "01_content/02_archivosIntermedios/guion/guion_maestro.md"
```

Guardá con `Cmd+S` antes de continuar. Mantené los encabezados `## Diapositiva`,
`### Segmento` cuando existan y las marcas `Narración:`. No hace falta volver al
pipeline A después de editar manualmente el guion.

### C. Generar el video: pasos 03, 04, 05, 06, 07 y 08

Primera generación o reintento para completar audios faltantes:

```bash
/opt/miniconda3/bin/python3 correr_pipeline_video.py --proyecto 01_content
```

Después de editar el guion, la voz o el léxico, cuando ya existen audios:

```bash
/opt/miniconda3/bin/python3 correr_pipeline_video.py --proyecto 01_content --forzar
```

Sin `--forzar`, los audios existentes se reutilizan aunque haya cambiado el texto.
Con `--forzar`, se regeneran todos los audios y segmentos del proyecto.

### D. Revisar el resultado

```bash
open "01_content/03_output/video_final.mp4"
code "01_content/03_output/qc/reporte.md"
open "01_content/03_output/qc/capturas"
```

Escuchá el inicio, un tramo central y el cierre; comprobá pronunciación,
correspondencia con las imágenes y que no se corten las frases.

## Abrir y editar los pipelines desde la terminal

Abrir el proyecto completo en VS Code:

```bash
code .
```

Abrir los dos scripts que encadenan las etapas:

```bash
code correr_pipeline_guion.py correr_pipeline_video.py
code 09_archivar_drive.py
```

Guardá con `Cmd+S` y volvé a ejecutar el comando del pipeline correspondiente.
La lista `PASOS` dentro de cada script define sus etapas. Para cambiar el texto,
la voz o el estilo normalmente basta con editar los archivos siguientes.

### Editar el contenido narrado

```bash
code "01_content/02_archivosIntermedios/guion/guion_maestro.md"
```

### Modelo actual y título automático

El guion usa `gpt-6-astra` con esfuerzo `high`. Los pasos de YouTube y cuestionario
siguen usando `gpt-5.4`. La próxima generación del paso 02 utilizará Astra; no se
regeneró el guion existente por cambiar el YAML. El acceso API a Astra está pendiente
de comprobar con una generación real.

No editar el YAML para cambiar de tema: cargar nuevas fuentes en los mismos
contenedores una vez archivada y retirada la lección anterior. El título se genera
con el guion. Para corregirlo, editar su primera línea `# Guion de locución — …`
antes del pipeline de video. El número se pide al archivar, no al generar el guion.

### Editar configuración, estilo y pronunciación

```bash
code "01_content/proyecto.yaml"
code "config/estilo_guion.md" "02_escribir_guion.py"
code "config/lexico.yaml"
```

| Archivo | Qué cambia | Cómo aplicar el cambio |
| --- | --- | --- |
| `guion_maestro.md` | Texto de la narración actual | Pipeline de video con `--forzar` |
| `proyecto.yaml`, sección `audio` | Voz, proveedor, velocidad y pausas | Pipeline de video con `--forzar` |
| `config/lexico.yaml` | Pronunciación de términos y siglas | Pipeline de video con `--forzar` |
| `config/estilo_guion.md`, `02_escribir_guion.py` o `guion.reglas` en YAML | Instrucciones para futuras generaciones | Pipeline de guion con `--forzar`, revisar y luego pipeline de video con `--forzar` |
| `proyecto.yaml`, sección `video` | Resolución y montaje | Ejecutar `05_montar_video.py --forzar` y después `06_control_calidad.py`, con Python y `--proyecto` como abajo |

Si `code` no está disponible, podés editar dentro de la terminal con `nano`:

```bash
nano correr_pipeline_guion.py
nano correr_pipeline_video.py
nano "01_content/02_archivosIntermedios/guion/guion_maestro.md"
```

En `nano`: `Ctrl+O`, Enter para guardar; `Ctrl+X` para salir.

## Ejecutar etapas individuales

Cada línea ejecuta únicamente esa etapa. No es necesario repetir las anteriores
si sus resultados ya están listos.

```bash
/opt/miniconda3/bin/python3 00_validar_insumos.py --proyecto 01_content
/opt/miniconda3/bin/python3 01_preparar_slides.py --proyecto 01_content
/opt/miniconda3/bin/python3 02_escribir_guion.py --proyecto 01_content
```

Revisar y guardar el guion antes de pasar a las siguientes:

```bash
/opt/miniconda3/bin/python3 03_dividir_guion.py --proyecto 01_content
/opt/miniconda3/bin/python3 04_crear_audios.py --proyecto 01_content --segmentos 1 2 --forzar
```

Escuchar las muestras:

```bash
open "01_content/02_archivosIntermedios/audio_files/slide_01.mp3"
open "01_content/02_archivosIntermedios/audio_files/slide_02.mp3"
```

Estos nombres corresponden al guion actual, con un segmento por diapositiva.
Si hay varios, los nombres incluyen sufijos como `slide_01_a.mp3`.

Generar todos los audios actualizados y montar:

```bash
/opt/miniconda3/bin/python3 04_crear_audios.py --proyecto 01_content --forzar
/opt/miniconda3/bin/python3 05_montar_video.py --proyecto 01_content --forzar
/opt/miniconda3/bin/python3 06_control_calidad.py --proyecto 01_content
```

## Empezar de cero

Este comando **borra sin otra confirmación el guion editado y todos los
intermedios y salidas**, y después corre los pasos 00–02:

```bash
/opt/miniconda3/bin/python3 correr_pipeline_guion.py --proyecto 01_content --limpiar
```

Solo limpiar, mostrando los archivos y pidiendo confirmación:

```bash
/opt/miniconda3/bin/python3 limpiar_proyecto.py --proyecto 01_content
```

El material original y `proyecto.yaml` se conservan. Para incorporar cambios
al guion actual, usá el pipeline de video con `--forzar`, sin limpiar.

## Ayuda y errores frecuentes

Consultar las opciones aceptadas:

```bash
/opt/miniconda3/bin/python3 correr_pipeline_guion.py --help
/opt/miniconda3/bin/python3 correr_pipeline_video.py --help
/opt/miniconda3/bin/python3 09_archivar_drive.py --help
```

- **No existe la carpeta de proyecto:** usá `--proyecto 01_content` para este
  contenido, siempre desde la raíz del repositorio. No crear una carpeta por lección.
- **Command not found / no se encuentra el script:** ejecutá primero el `cd`
  de esta guía y anteponé la ruta de Python al nombre del script.
- **No module named…:** instalá las dependencias en el mismo Python:

```bash
/opt/miniconda3/bin/python3 -m pip install -r requirements.txt
```

- **Falta ffmpeg/ffprobe:** instalalos con `brew install ffmpeg`.
- **Falta el guion o las diapositivas normalizadas:** prepará los insumos con el
  pipeline del guion y revisá su resultado antes del pipeline de video.
- **Se sigue escuchando el texto anterior:** guardá el guion y ejecutá el
  pipeline de video con `--forzar`.
- **Falla la síntesis de voz:** revisá el error y la conexión. Si no cambiaste
  el texto, podés reintentar sin `--forzar` para completar los audios faltantes.

Si el error persiste, conservá el mensaje completo, incluida la etapa que falló.

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

## Subida privada a YouTube por API

`10_subir_youtube.py` usa `client_secret_yt.json` (OAuth de escritorio) y guarda
su token separado en `.youtube/token.json`, excluido de Git. Solicita permisos
para subir y consultar el canal. Habilitar YouTube Data API v3 en Google Cloud;
si el consentimiento está en pruebas, agregar la cuenta como usuario de prueba.

Conectar y consultar el canal, sin subir ni borrar:

```bash
/opt/miniconda3/bin/python3 10_subir_youtube.py --comprobar
```

Preparar la miniatura y simular sin conectar:

```bash
/opt/miniconda3/bin/python3 07_preparar_youtube.py --proyecto 01_content
/opt/miniconda3/bin/python3 10_subir_youtube.py --proyecto 01_content --simular
```

Subir el video existente en **privado**, reemplazando `ID_DEL_CANAL` por el ID
obtenido con `--comprobar`:

```bash
/opt/miniconda3/bin/python3 10_subir_youtube.py --proyecto 01_content --canal-id ID_DEL_CANAL
```

La subida usa `video_final.mp4`, `youtube.txt` y `miniatura.png`. Declara categoría
Educación y contenido no dirigido a niños, adecuado al material actual de formación
bancaria para adultos. Si cambia la audiencia prevista, revisar esa declaración.
No hace público el video ni cambia posteriormente su visibilidad.

El registro `historial_youtube/CANAL_SHA256.json` guarda el ID fuera del área que
se vacía; `03_output/youtube_subida.json` copia el resultado verificado para Drive.
Repetir el comando reutiliza ese video y completa la miniatura o verificación
pendientes; no actualiza el título o descripción de una carga ya existente.
No borrar el historial: evita duplicados. Los `.lock` solo coordinan procesos locales.

Si el proceso se interrumpe sin registrar el ID, bloquea una nueva inserción.
Revisar YouTube Studio. Si se identifica el video exacto, recuperar explícitamente:

```bash
/opt/miniconda3/bin/python3 10_subir_youtube.py --proyecto 01_content --canal-id ID_DEL_CANAL --recuperar-id ID_DEL_VIDEO
```

La recuperación verifica el canal, pero requiere identificar manualmente que es
el mismo video. Si no existe, revisar el caso antes de retirar el registro pendiente;
no reintentar a ciegas. La carga por bloques reintenta durante la ejecución, no
reanuda automáticamente una sesión de bytes después de cerrar el proceso.

El script espera hasta dos minutos al procesamiento. Si demora más, conserva
el ID, devuelve error y se puede repetir sin duplicar. Un fallo de miniatura
(por ejemplo, canal sin habilitación) también conserva el ID y detiene el flujo.

### Integrar con el pipeline y Drive

Aunque el archivo se llame 10, se ejecuta **antes del 09** cuando se activan ambas
opciones. El orden es 03–08 → 10 YouTube → 09 Drive → limpieza. Si YouTube falla,
no se ejecuta Drive. El 09 independiente sigue funcionando como archivo de Drive,
sin exigir una carga a YouTube.

```bash
/opt/miniconda3/bin/python3 correr_pipeline_video.py --proyecto 01_content --subir-youtube --canal-id ID_DEL_CANAL --archivar-drive --leccion 1 --conservar-local
```

Este ejemplo conserva los archivos locales. Omitir `--conservar-local` solo cuando
se quiera vaciar los contenedores después de verificar el archivo en Drive.
No se debe ejecutar un 09 con limpieza antes de la subida a YouTube.

Google restringe a privado las subidas de proyectos API no auditados creados después
del 28/07/2020. Levantar esa restricción exige auditoría y no solo consentimiento
OAuth. [Documentación oficial](https://developers.google.com/youtube/v3/docs/videos/insert).
