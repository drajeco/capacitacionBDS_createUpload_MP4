# Continuidad del proyecto mp4_creation

Actualizado: **4 de octubre de 2026**. Este es el archivo de entrada para una
nueva sesión. Describe decisiones y estado comprobado, no autoriza por sí mismo
subidas, borrados ni regeneraciones. Leer luego `README.md`,
`INSTRUCCIONES_TERMINAL.md` y el código pertinente; si el estado del disco cambió,
verificarlo antes de actuar y actualizar este documento.

## Objetivo y forma de trabajo acordada

Convertir material educativo en lecciones listas para YouTube: diapositivas,
desgrabación, fichas de lectura y bibliografía → guion natural → voz sintética,
video, publicación y cuestionarios. Archivar ordenadamente las lecciones en
Google Drive mediante API y reutilizar las mismas carpetas locales.

- Un solo espacio de trabajo: `01_content`. No crear `02_content` ni un YAML
  por lección. `01_content/proyecto.yaml` es la configuración compartida.
- Solo cambia el contenido. El tema, título y miniatura no requieren reglas
  específicas ni cambios de configuración por lección.
- Dos pipelines separados: 00–02 para preparar guion; 03–08 para producir video
  y entregables. Entre ambos hay revisión humana obligatoria del guion.
- El número de lección se pide al archivar en el paso 09, o se recibe con
  `--leccion N`. El nombre deriva del encabezado del guion maestro.
- Drive por API, sin Drive para escritorio.
- Se prioriza calidad del guion sobre ahorro. El usuario pidió cambiar el
  modelo del guion a GPT-6 Astra; no pidió cambiar todos los modelos del proyecto.
- La petición anterior fue modificar el borrado del paso 09, **sin vaciar todavía
  los archivos reales**. No se ejecutó el vaciado en estas sesiones.

## Flujo implementado

| Paso | Función |
| --- | --- |
| 00 | Validar insumos y herramientas |
| 01 | Normalizar imágenes y generar hoja de contacto |
| 02 | Generar título y guion estructurado mediante OpenAI |
| Pausa | Revisar y editar el guion maestro |
| 03 | Dividir el guion en textos por segmento |
| 04 | Generar audios, aplicar léxico y pausas |
| 05 | Montar MP4 con ffmpeg |
| 06 | Control de calidad, capturas y reporte |
| 07 | Generar título y descripción para YouTube y copiar la primera diapositiva como miniatura |
| 08 | Generar cuestionario limpio y resuelto |
| 09 | Archivar en Drive, verificar y vaciar contenedores salvo `--conservar-local` |

`correr_pipeline_guion.py`: 00–02. `correr_pipeline_video.py`: 03–08;
`--archivar-drive` agrega el 09. Ambos se detienen ante errores.
El antiguo `correr_pipeline.py` fue eliminado y reemplazado por estos dos scripts.

La subida privada a YouTube está implementada en `10_subir_youtube.py`, con
`--subir-youtube` en el pipeline. Se ejecuta ANTES del 09. El paso 07 solo prepara
archivos. Ver actualización del 4 de octubre al final para el estado real de conexión.

## Calidad y generación de texto

La desgrabación de la exposición es la fuente principal. Diapositivas y guion
se acompañan; lecturas y bibliografía complementan de forma secundaria. Cada
slide abre con una introducción natural que alude a su título, incluso si se
repite. El texto se prepara para ser leído por una IA: español rioplatense
neutro, registro profesional, frases claras, transiciones variadas y desarrollo
oral del razonamiento. Evitar muletillas, tono de libro leído y datos inventados.

`config/estilo_guion.md` conserva el estilo del guion maestro editado por el
usuario; es una referencia permanente, no depende de archivos intermedios.
`config/lexico.yaml` corrige pronunciación al generar audio, sin deformar el guion.
`comun/materiales.py` comparte lectura de textos y PDF; PDF sin texto requiere OCR.

El paso 02 ahora devuelve `titulo_leccion` junto con los segmentos y escribe:

```markdown
# Guion de locución — Título de la lección
```

`Proyecto.titulo` lee ese encabezado; no toma el título de YAML. El usuario puede
corregirlo durante la revisión. El título editorial de YouTube se genera aparte.
El paso 02 infiere el tema de las fuentes, sin reutilizar el de un guion anterior.

Configuración efectiva en `01_content/proyecto.yaml`:

| Uso | Modelo / parámetros |
| --- | --- |
| Guion | `gpt-6-astra`, `high`, 32.000 tokens máximos de salida |
| Duración y división | Objetivo 22 minutos, hasta 5 segmentos por slide, 220 palabras por segmento |
| YouTube | `gpt-5.4`, `medium`, 6.000 tokens máximos |
| Cuestionario | `gpt-5.4`, `high`, 18.000 tokens máximos |
| Voz | Edge, `es-UY-ValentinaNeural`, velocidad `+0%`, pausa inicial 1 segundo |
| Video | 1920×1080, 30 fps, H.264/AAC, sin movimiento |

El valor de respaldo de guion en `comun/config.py` aún es `gpt-5.4`; el YAML
lo sobrescribe. El cambio a Astra solo se verificó cargando la configuración:
**no se ejecutó una generación real con Astra ni se confirmó acceso de la cuenta**.
Una segunda pasada automática de revisión editorial fue recomendada pero **no
implementada**. No describirla como parte del flujo actual.

## Cuestionario

Diez preguntas, cuatro opciones y una única respuesta correcta, en dificultad
creciente: 4 de comprensión del video; 4 de razonamiento con video y lecturas;
2 de integración profunda que requieren ambos. Dos archivos derivados de una
misma respuesta: `cuestionario.txt` y `cuestionario_resuelto.txt`.

La versión resuelta contiene explicaciones, análisis de distractores y evidencias.
Se valida estructura y citas literales con identificadores de fuentes. Se guarda
`cuestionario_borrador.json` y se reintenta una vez con correcciones si fallan
las evidencias. La dificultad y calidad pedagógica necesitan revisión humana.
En la lección 1 hubo además revisión editorial de distractores y distribución de
respuestas; el archivo `cuestionario_revisado.json` conserva ese resultado.

## Drive: estado y garantías del código

Destino: [01_documentacion_final](https://drive.google.com/drive/folders/1KVQcdWeLU2OPUJ3QhK1KilLIOJj8eGLG).
ID: `1KVQcdWeLU2OPUJ3QhK1KilLIOJj8eGLG`.

Se reemplazaron credenciales de cuenta de servicio por OAuth de escritorio,
se autorizó la cuenta en navegador y se realizó una carga real exitosa de
**163 archivos, 167,1 MB**, correspondiente a la lección 1, Intermediación bancaria.

[Archivo real de esa carga](https://drive.google.com/drive/folders/14vF3pJfrPl3JZ7vGSodOIfMo1oMjc6-H).
Se hizo con la versión anterior del script, que organizaba por proyecto y no
vaciaba carpetas. Esa carga no se movió ni se renombró. No es el respaldo completo
del nuevo inventario ampliado: se añadieron después auxiliares y otros formatos.

Comportamiento del código actual, todavía no ejecutado de extremo a extremo en Drive:

- Carpeta `Lección NN - Título/version_HASH`; cambios de contenido crean otra versión.
  Cambiar el título también cambia la carpeta; no hay identidad estable solo por número.
- Reutiliza archivos remotos con el mismo MD5. No reemplaza archivos diferentes
  ni elimina versiones remotas. Los permisos se heredan del destino.
- Completa el inventario con todos los archivos regulares de los tres contenedores,
  incluidos auxiliares, JSON e imágenes intermedias, en `08_Respaldo_completo`.
  Rechaza enlaces simbólicos y ciertos nombres de credenciales dentro de ellos.
- Verifica MD5 y tamaños remotos, incluido el inventario. Compara otra vez todo
  el contenido local antes de empezar el borrado. No editar durante la operación.
- Si una carga o verificación falla, no empieza el vaciado. Una interrupción
  durante el borrado puede dejar limpieza parcial, con el respaldo ya verificado.
- Vacía archivos de `01_materialOriginal`, `02_archivosIntermedios` y `03_output`;
  conserva carpetas y subcarpetas, YAML y archivos externos. `--conservar-local`
  desactiva el vaciado.
- Guarda enlaces fuera de los contenedores: `historial_drive/leccion_NN_HASH.json`.
- `--simular` y `--comprobar` no suben ni borran, pero **requieren entregables y
  miniatura existentes**, porque primero arman el inventario.
- `--titulo-leccion` existe como excepción manual; normalmente se omite para
  usar el título del guion. Sin terminal interactiva se debe pasar `--leccion`.

Credenciales: `credentials.json` y `.drive/token.json` en la raíz, excluidos de Git.
No mostrar su contenido ni copiarlo a documentos o a Drive. `OPENAI_API_KEY`
está en entorno o `.env`. No confundir OAuth Drive con autorización de YouTube.

## Estado local al cerrar esta actualización documental

El material de la lección 1 sigue en `01_content`: guion editado, fuentes, audios,
video, publicación y cuestionarios. No se regeneraron ni borraron en esta tarea.

- Existe el inventario antiguo `01_content/03_output/drive_inventario.json`.
- Aún no existe `historial_drive/`: lo creará una carga con el script nuevo.
- Al cierre del 3 de octubre no existía `01_content/03_output/miniatura.png`. La antigua miniatura de
  Intermediación bancaria está en la raíz, pero el código actual ya no la usa.
- Para preparar la miniatura nueva basta ejecutar el paso 07: si ya existe
  `youtube.txt`, lo conserva y copia la primera diapositiva sin llamar al modelo.
  Esa ejecución no se hizo durante esta actualización documental.
- Cambiar Astra en YAML no cambia el guion ni los audios existentes. Para regenerar
  se necesita `--forzar`, lo cual reemplaza ediciones manuales.
- Última suite ejecutada en las modificaciones funcionales: **70 pruebas pasaron**.
  Incluye pruebas temporales de borrado y fallos de verificación; no sustituye
  una prueba de extremo a extremo de la nueva versión con Google Drive.
- Hay numerosas modificaciones y archivos no versionados de sesiones anteriores.
  Se conserva el trabajo del usuario; no hacer reset, limpieza Git ni commit masivo.

## Próximo trabajo conversado: YouTube por API

El usuario preguntó por la posibilidad de subir automáticamente y pidió documentar
antes de continuar. No se implementó ni se subió ningún video a YouTube.

Plan propuesto:

1. Habilitar YouTube Data API v3 en el proyecto Google Cloud y autorizar el canal
   con OAuth. Se puede reutilizar el cliente de escritorio, con token separado.
2. Definir canal y visibilidad. Se propuso empezar en privado; no hay elección
   final de canal ni configuración confirmada.
3. Subir video y metadata con reintentos; guardar ID y enlace fuera de los
   contenedores para evitar duplicados al reanudar. Considerar fallos después de
   crear el video y antes de guardar la respuesta.
4. Confirmar el estado de la subida y el procesamiento, archivar en Drive el
   enlace junto con el material y recién entonces vaciar el área de trabajo.
5. Ajustar el paso 09 o separar su limpieza para que no borre antes de YouTube.
   No alcanza con agregar un paso 10 después del 09 actual.

La API restringe a privado las subidas de proyectos no auditados creados después
del 28/07/2020. La auditoría del proyecto API es distinta del consentimiento OAuth.
Verificar condiciones vigentes al implementar:
[uploads](https://developers.google.com/youtube/v3/guides/uploading_a_video),
[videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert).

## Entorno y archivos para retomar

Raíz en esta Mac:

```text
/Users/diegoabal/Library/CloudStorage/OneDrive-Personal/Documents/03 - Desarrollo/Cursos/Datascience/02 - Diplomatura (UP)/04 - PROYECTOS/09 - mp4_creation
```

Python: `/opt/miniconda3/bin/python3`. ffmpeg/ffprobe y dependencias en
`requirements.txt`. El `python3` del sistema puede ser otro entorno.

Leer según la tarea:

- `01_content/proyecto.yaml`, `comun/config.py`: parámetros y rutas efectivas.
- `02_escribir_guion.py`, `config/estilo_guion.md`: título, fuentes y estilo.
- `07_preparar_youtube.py`, `08_crear_cuestionario.py`: entregables educativos.
- `09_archivar_drive.py`, `tests/test_drive.py`: archivo, verificaciones y limpieza.
- `correr_pipeline_guion.py`, `correr_pipeline_video.py`: orden y argumentos.
- `INSTRUCCIONES_TERMINAL.md`: comandos, edición, reintentos y efectos de `--forzar`.

Para iniciar una nueva sesión, pedir:

> Leé CONTINUIDAD_PROYECTO.md y revisá el estado actual del repositorio antes de
> continuar. El próximo trabajo conversado es integrar YouTube por API sin que
> el paso 09 elimine el material antes de completar ambas cargas.

Referencia histórica previa: sesión Claude Code del 14/09/2026:
https://claude.ai/code/session_01F93nGB8Ry8AxuWQi92ixRH
Este documento y el estado actual del código sustituyen ese enlace como punto
principal de continuidad.


## Actualización del 4 de octubre: integración YouTube

El usuario creó `client_secret_yt.json` y pidió continuar con la subida. Se verificó
sin mostrar secretos: es cliente OAuth de escritorio y está excluido de Git.
Se creó `comun/youtube_api.py`, que usa un token separado `.youtube/token.json`.
La autorización real venció con `WSGITimeoutError` sin recibir consentimiento.
Todavía no se verificó el canal ni se subió el video. Se pidió al usuario su canal
y está pendiente la respuesta. Repetir `10_subir_youtube.py --comprobar` para abrir
nuevamente el navegador; no confundir código probado con subida completa.

Implementado y probado con servicios simulados:

- `10_subir_youtube.py`: comprobación del canal, simulación, subida privada,
  miniatura y verificación del procesamiento, con registro persistente por canal
  y hash del MP4 en `historial_youtube/`.
- Una carga interrumpida con resultado incierto bloquea nuevas inserciones.
  `--recuperar-id` permite asociar el video previamente revisado en Studio.
- `--canal-id` obligatorio para subir: se compara con el canal autenticado.
- El pipeline acepta `--subir-youtube` y ejecuta 10 ANTES de 09; un fallo de YouTube
  impide el archivo y limpieza posterior. La prueba actual conserva el contenido.
- Se ejecutó 07 sin `--forzar`: creó `03_output/miniatura.png` a partir del primer
  slide y conservó `youtube.txt`, sin generación OpenAI. Simulación de subida OK:
  video de 66,7 MB, título «Intermediación bancaria: ahorro, crédito y gestión del riesgo».
- La API recibe categoría Educación, audiencia no infantil y visibilidad privada.
  No hay publicación pública ni programación de fecha implementadas.
- No se ejecutó el paso 09 ni se borraron archivos durante esta integración.

El commit previo es `83f1655` en `main`. El usuario pidió push, pero no había
remoto configurado; no se realizó. Las modificaciones de YouTube son posteriores
a ese commit. Los comandos actuales están en `INSTRUCCIONES_TERMINAL.md`.

Validación del 4 de octubre: **76 pruebas pasaron**. No se verificó aún si Google
Cloud tiene la API habilitada ni si el canal permite miniaturas personalizadas;
se podrá comprobar después del consentimiento OAuth.


### Reintento de autorización y primera subida real (4 de octubre)

Se amplió la espera OAuth de 180 a 600 segundos y el usuario completó la autorización.
Canal verificado: **Capacitacion BDS**, ID `UCSp1NB3m20yNM88paRKvKww`.
Se subió el MP4 de Intermediación bancaria, con título y descripción existentes,
en privado. YouTube aceptó también la miniatura.

Video: https://youtu.be/0ZE_S4UVh7c
ID: `0ZE_S4UVh7c`. El registro persistente está en `historial_youtube/`.
La primera espera de procesamiento venció; se reintentó la verificación con el
mismo ID, sin duplicar la subida. También venció la segunda espera: estado al
cierre `procesando`. La subida y miniatura están completas; falta verificar
procesamiento. Aún no se creó `03_output/youtube_subida.json`, que se escribe
cuando la verificación termina. Repetir el paso 10 con el canal indicado para
consultar el mismo video. Consultar el registro para el estado más reciente.
No se ejecutó el archivado en Drive ni se vació contenido local.


### Verificación final de YouTube (4 de octubre)

YouTube terminó de procesar el video `0ZE_S4UVh7c`. Estado final **verificado**,
visibilidad **private**, canal **Capacitacion BDS**. Se creó
`01_content/03_output/youtube_subida.json` con ID y enlace, y se actualizó el
registro en `historial_youtube/`. Esta comprobación reemplaza el estado pendiente
de las esperas anteriores. No se duplicó el video ni se ejecutó Drive o limpieza.
Enlace: https://youtu.be/0ZE_S4UVh7c
