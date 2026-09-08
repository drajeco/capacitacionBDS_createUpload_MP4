# Proyecto: creación semiautomática de videos educativos a partir de presentaciones

## Propósito

Este proyecto busca transformar una presentación y la transcripción de una explicación original en un video educativo autónomo, con locución generada por voz sintética y diapositivas sincronizadas con esa locución.

El resultado esperado es un archivo MP4 listo para distribuir. El proceso debe poder repetirse periódicamente desde Visual Studio Code, reduciendo el trabajo manual y conservando puntos de revisión humana donde realmente aportan valor: la calidad del guion, la presentación visual y la voz.

La primera experiencia se realizó sobre un material de introducción a la gestión bancaria: balance bancario, depósitos, fondeo y liquidez.

## Idea central

La presentación aporta la estructura visual. La transcripción aporta el contenido real de la explicación. Ninguno de los dos insumos debe utilizarse mecánicamente:

- la transcripción se transforma en un guion de locución claro y didáctico;
- la presentación se revisa y se adapta para que funcione sin la presencia del docente;
- cada diapositiva se asocia con un fragmento de guion y un archivo de audio;
- el video final muestra cada diapositiva exactamente durante la duración de su audio.

El principio más importante es que el producto final debe ser independiente: una persona que no asistió a la clase debe poder entenderlo sin referencias a una reunión, clase, lección o contenido anterior/posterior.

## Antecedentes: experiencia inicial

La prueba se desarrolló en la carpeta local:

```text
/Users/diegoabal/Desktop/0102
```

Los insumos iniciales fueron:

```text
Capacitacion_bancaria_Reunion_1.pptx    Presentación original
Capacitacion_bancaria_Reunion_1.key     Presentación editada en Keynote
01_02.md                                Transcripción de la explicación original
```

### Decisiones editoriales tomadas

El guion se reescribió conservando los conceptos, el razonamiento y los ejemplos reales de la exposición, pero eliminando elementos propios de una situación presencial:

- muletillas, repeticiones e interrupciones;
- referencias a "primera reunión";
- referencias a la clase, a lo ya visto o a una próxima lección;
- frases que dependieran de que el público hubiera participado antes;
- instrucciones internas de exposición.

También se agregó una portada con el título `Introducción a la gestión bancaria` y se quitó una diapositiva final que ya no correspondía al video. La presentación editada terminó con 20 diapositivas: portada y 19 diapositivas de contenido.

### Entregables generados

```text
guion_locucion_sincronizado.md                         Guion maestro, ordenado por diapositiva
locucion_por_slide/slide_01.txt ... slide_20.txt      Texto de locución individual por diapositiva
png_finales/                                           20 PNG exportados desde la presentación editada
audio_por_slide/                                       Primer juego de audios sintéticos de macOS
audio_por_slide_alt/                                   Segundo juego de 20 audios WAV, con voz mejorada
capacitacion_bancaria_balance_depositos_liquidez.mp4   Primer video MP4
capacitacion_bancaria_balance_depositos_liquidez_audio_alt.mp4
                                                       Video final montado con los WAV alternativos
```

El segundo video duró aproximadamente 22 minutos y fue verificado visualmente en distintos momentos de la línea de tiempo para confirmar que las diapositivas avanzaran correctamente y que terminara en la diapositiva de síntesis.

## Flujo de trabajo objetivo

```text
Presentación + transcripción
            |
            v
Revisión y adaptación de la presentación
            |
            v
Guion maestro autónomo por diapositiva
            |
            v
Textos individuales de locución
            |
            +------------------+
            |                  |
            v                  v
Exportación de slides       Generación de voz
como PNG                    por diapositiva
            |                  |
            +--------+---------+
                     v
           Montaje y codificación MP4
                     |
                     v
           Control de calidad y entrega
```

## Qué automatizar y qué revisar manualmente

La automatización no debería sustituir el criterio editorial. El objetivo es estandarizar lo repetible y dejar explícitos los puntos de aprobación.

| Etapa | Automatización | Revisión humana |
| --- | --- | --- |
| Validación de carpetas y nombres | Total | No necesaria salvo errores |
| Lectura de presentación y transcripción | Parcial | Confirmar que los insumos son los correctos |
| Guion por diapositiva | Parcial, con IA | Obligatoria: contenido, tono y alcance |
| Separación en archivos `slide_XX.txt` | Total | Revisar cantidad y orden |
| Exportación de PNG | Total o semiautomática | Revisar hoja de contacto |
| Generación de audio | Total | Escuchar muestra y pronunciaciones |
| Montaje del MP4 | Total | Verificar inicio, tramos y final |
| Informe final | Total | Validar antes de distribuir |

## Reglas editoriales para el guion

Estas reglas deben quedar parametrizadas en el proyecto y aplicarse a todos los nuevos videos, salvo que se indique lo contrario:

1. Escribir como material independiente y autocontenido.
2. Preservar los conceptos, ejemplos y orden lógico de la explicación original.
3. No utilizar literalmente una transcripción oral.
4. Eliminar muletillas, redundancias y frases incompletas.
5. No mencionar reuniones, clases, lecciones ni contenidos anteriores o futuros.
6. No prometer que un tema se verá más adelante, salvo que el video forme parte explícitamente de una serie y se solicite incluirlo.
7. Usar oraciones naturales, de extensión moderada y adecuadas para voz sintética.
8. Explicar siglas la primera vez que aparecen, y prever su pronunciación en el motor de voz.
9. Mantener una unidad conceptual por diapositiva siempre que sea posible.
10. Evitar instrucciones visuales dentro de la locución, como "miren aquí", salvo que sean indispensables y claras.

## Estructura de proyecto propuesta

Se recomienda crear un repositorio independiente, por ejemplo `mp4_creation`, y abrir esa carpeta desde Visual Studio Code.

```text
mp4_creation/
  README.md
  pyproject.toml
  .env.example
  config/
    proyecto.example.yaml
    voces.example.yaml
  src/
    mp4_creation/
      __init__.py
      config.py
      validar.py
      guion.py
      dividir_guion.py
      exportar_slides.py
      generar_audio.py
      montar_video.py
      control_calidad.py
      utilidades.py
  scripts/
    crear_proyecto.py
    ejecutar_pipeline.py
  tests/
  proyectos/
    ejemplo_gestion_bancaria/
      00_insumos/
        presentacion.key
        transcripcion.md
      01_presentacion/
        presentacion_editada.key
      02_guion/
        guion_maestro.md
        locucion_por_slide/
          slide_01.txt
      03_slides/
        png/
          slide_01.png
      04_audio/
        wav/
          slide_01.wav
      05_video/
        video_final.mp4
      06_control_calidad/
        reporte.md
        hoja_de_contacto.png
      trabajo/
```

La carpeta `trabajo/` contiene archivos temporales y puede regenerarse. Las carpetas numeradas son los artefactos que interesa conservar y versionar.

## Convención de nombres

La correspondencia entre texto, imagen y audio debe ser determinista:

```text
slide_01.txt -> slide_01.png -> slide_01.wav
slide_02.txt -> slide_02.png -> slide_02.wav
```

No se debe depender del orden en que el sistema operativo enumera archivos. Los scripts deben ordenar por número de diapositiva y validar que las tres colecciones tengan exactamente los mismos identificadores.

## Archivo de configuración por proyecto

Cada video debería incluir un archivo `config/proyecto.yaml` o `proyecto.yaml`. Ejemplo:

```yaml
proyecto:
  nombre: gestion_bancaria_balance_depositos_liquidez
  titulo: Introducción a la gestión bancaria
  idioma: es-AR

insumos:
  presentacion: 00_insumos/presentacion.key
  transcripcion: 00_insumos/transcripcion.md

salidas:
  guion: 02_guion/guion_maestro.md
  textos_locucion: 02_guion/locucion_por_slide
  slides_png: 03_slides/png
  audio: 04_audio/wav
  video: 05_video/video_final.mp4
  control_calidad: 06_control_calidad

guion:
  material_autonomo: true
  evitar_referencias:
    - clase
    - reunión
    - lección
    - contenido anterior
    - contenido siguiente

audio:
  proveedor: local
  formato: wav
  voz: por_definir
  velocidad: 1.0

video:
  ancho: 1920
  alto: 1080
  fps: 30
  codec_video: libx264
  codec_audio: aac
```

Las credenciales de proveedores externos, como ElevenLabs, nunca deben guardarse en este archivo ni subirse al repositorio. Deben ir en un archivo `.env` ignorado por Git.

## Pipeline propuesto

El pipeline puede implementarse en Python y ejecutarse mediante comandos simples desde la terminal integrada de Visual Studio Code.

```text
1. crear_proyecto
2. validar_insumos
3. preparar_guion
4. dividir_locucion
5. exportar_slides
6. generar_audio
7. validar_activos
8. montar_video
9. control_calidad
```

### 1. Crear proyecto

Recibe un nombre y crea la estructura de carpetas, un archivo de configuración y un checklist inicial.

```bash
python scripts/crear_proyecto.py gestion_bancaria
```

### 2. Validar insumos

Comprueba que exista una presentación y una transcripción. También identifica la cantidad de diapositivas una vez exportadas y verifica que no haya archivos con nombres ambiguos.

### 3. Preparar guion

Esta etapa puede ser asistida por IA, pero requiere revisión humana antes de continuar. El resultado debe ser un único Markdown con una sección por diapositiva.

Formato recomendado:

```markdown
## Diapositiva 01 - Título

Narración:

Texto que se utilizará en la voz.
```

Se pueden conservar campos opcionales como duración estimada e indicaciones de sincronización, pero el script de audio debe extraer solo el bloque `Narración`.

### 4. Dividir la locución

Lee el guion maestro, extrae la narración de cada diapositiva y crea `slide_XX.txt`. Debe fallar con un mensaje claro si falta una diapositiva, si hay números repetidos o si un bloque está vacío.

### 5. Exportar diapositivas

Se recomienda trabajar con la presentación ya revisada. En macOS, la exportación de Keynote puede realizarse mediante AppleScript o una automatización equivalente. Para PPTX, se puede utilizar LibreOffice en modo no interactivo o una herramienta de conversión validada.

El script debe convertir los archivos a un nombre predecible:

```text
slide_01.png
slide_02.png
...
```

Se debe generar además una hoja de contacto para revisar visualmente todas las diapositivas de una vez.

### 6. Generar audio

El sistema debe admitir proveedores intercambiables:

- `local`: voz local de macOS o un motor instalado en la computadora;
- `elevenlabs`: API de ElevenLabs;
- `archivo_existente`: usa WAV o MP3 ya producidos por otro script.

Cada proveedor recibe `slide_XX.txt` y genera, o valida, `slide_XX.wav` o `slide_XX.mp3`.

Antes de procesar todos los slides, el pipeline debe permitir una prueba limitada:

```bash
python scripts/ejecutar_pipeline.py --proyecto proyectos/gestion_bancaria --paso audio --slides 1 2
```

Esto permite escuchar la voz y corregir ritmo, pronunciaciones o estilo sin generar toda la serie.

### 7. Validar activos

Debe comprobarse lo siguiente antes de montar el video:

- misma cantidad de archivos `.txt`, `.png` y audio;
- misma numeración en las tres carpetas;
- audios reproducibles y con duración mayor a cero;
- imágenes con resolución consistente;
- ausencia de diapositivas no utilizadas o faltantes.

El pipeline debe detenerse si hay inconsistencias, en lugar de producir un video incompleto.

### 8. Montar el video

Por cada número de diapositiva:

1. obtener la duración real del audio;
2. mostrar el PNG durante esa duración;
3. colocar el audio correspondiente;
4. concatenar todos los segmentos en orden.

La salida será un MP4 H.264 con audio AAC, idealmente a 1920 x 1080 y 30 fps. La primera prueba produjo correctamente un MP4 de 960 x 540; el proyecto definitivo debería permitir configurar una resolución de producción más alta.

Una implementación recomendable usa `ffmpeg` desde Python. Es más portátil y simple de mantener que una solución ligada exclusivamente a macOS. El montador debe crear fotogramas durante toda la duración de cada slide; no debe depender de una única imagen con duración implícita, porque eso produjo inicialmente un video visualmente congelado en la portada.

### 9. Control de calidad

El script debe generar:

- duración total del video;
- tabla con duración por diapositiva;
- hoja de contacto de las imágenes;
- capturas de control tomadas en inicio, varios puntos intermedios y final;
- reporte Markdown de validación;
- un aviso si la duración de un audio es sospechosamente corta o larga.

La revisión final debe incluir escuchar al menos el inicio, un tramo central y el cierre, y confirmar que no haya pronunciaciones incorrectas de términos técnicos o siglas.

## Integración futura con ElevenLabs

ElevenLabs puede mejorar de forma importante la naturalidad de la voz. La integración debe ser opcional y aislada en un proveedor de audio, para que el resto del pipeline no cambie.

Variables sugeridas en `.env`:

```text
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

El proveedor debe:

1. leer el texto de cada `slide_XX.txt`;
2. enviar el texto y la configuración de voz a la API;
3. guardar la respuesta como `slide_XX.mp3` o `slide_XX.wav`;
4. conservar un registro de modelo, voz, fecha y parámetros usados;
5. permitir regenerar solo una diapositiva específica.

Conviene agregar un pequeño diccionario de pronunciación configurable, especialmente para siglas y vocabulario bancario: `LCR`, `FNE`, `EMO`, `fondeo`, `encaje`, `tasa pasiva` y términos que se detecten en cada curso.

## Tecnologías recomendadas

- Python 3.11 o superior para la lógica del pipeline.
- `ffmpeg` y `ffprobe` para duración de audio, montaje y verificación del MP4.
- `PyYAML` para archivos de configuración.
- `Pillow` para hojas de contacto y validación básica de imágenes.
- `pydub` o una interfaz directa con `ffprobe` para información de audio.
- AppleScript/Keynote para exportar desde Keynote en macOS, cuando corresponda.
- API de ElevenLabs como proveedor de voz opcional.
- `pytest` para validar numeración, correspondencias y funciones críticas.

## Criterios de aceptación

Un proyecto se considera terminado cuando:

1. El guion está aprobado y funciona como contenido autónomo.
2. La cantidad y numeración de textos, imágenes y audios coincide.
3. Las diapositivas exportadas corresponden a la presentación final, incluida la portada y excluyendo slides eliminados.
4. Todos los audios se escuchan correctamente y las siglas relevantes tienen buena pronunciación.
5. El MP4 tiene imagen y audio sincronizados por diapositiva.
6. El video no queda congelado en la portada ni muestra diapositivas incorrectas.
7. Se conserva un reporte reproducible de la ejecución.

## Próximo paso sugerido desde Visual Studio Code

1. Crear el repositorio `mp4_creation` en la carpeta de desarrollo definida.
2. Inicializar el entorno virtual de Python y las dependencias base.
3. Implementar primero el validador de estructura y el separador de guion.
4. Implementar el montador de video con `ffmpeg`, usando los 20 PNG y 20 WAV de esta experiencia como caso de prueba real.
5. Agregar el proveedor de voz local.
6. Integrar ElevenLabs una vez que la estructura y la prueba de voz estén aprobadas.
7. Incorporar exportación de diapositivas y generación de hoja de contacto.

El caso de gestión bancaria debe quedar como proyecto de demostración y prueba de regresión: cada mejora del pipeline puede comprobarse contra sus 20 textos, 20 imágenes, 20 audios y video esperado.
