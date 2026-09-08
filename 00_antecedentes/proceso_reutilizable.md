# Proceso reutilizable para generar videos de capacitación

Este documento describe una rutina semi automática para transformar una presentación y una transcripción de clase en un video narrado.

La idea es repetir siempre el mismo flujo:

1. presentación + transcripción;
2. guion limpio por diapositiva;
3. locución separada por slide;
4. audios generados automáticamente;
5. exportación de diapositivas a PNG;
6. montaje final en MP4;
7. revisión y ajustes.

## Estructura recomendada de carpetas

Para cada nuevo contenido, crear una carpeta de trabajo con esta estructura:

```text
nombre_del_video/
  00_insumos/
    presentacion.key o presentacion.pptx
    transcripcion.md

  01_guion/
    guion_locucion_sincronizado.md
    locucion_por_slide/
      slide_01.txt
      slide_02.txt
      ...

  02_slides/
    png_finales/
      slide_01.png
      slide_02.png
      ...

  03_audio/
    audio_por_slide/
      slide_01.mp3 o slide_01.m4a
      slide_02.mp3 o slide_02.m4a
      ...

  04_video/
    video_final.mp4

  _work/
    archivos temporales, hojas de contacto, scripts y pruebas
```

La clave es que los nombres coincidan:

```text
slide_01.txt  ->  slide_01.png  ->  slide_01.mp3
slide_02.txt  ->  slide_02.png  ->  slide_02.mp3
...
```

Si hay 20 diapositivas, tiene que haber:

- 20 textos de locución;
- 20 imágenes PNG;
- 20 audios.

## Etapa 1 - Preparar insumos

Archivos necesarios:

- una presentación en Keynote o PowerPoint;
- una transcripción de la clase o explicación original;
- opcionalmente, comentarios sobre tono, público, duración deseada y estilo de voz.

Conviene definir desde el inicio:

- título del video;
- público destinatario;
- si el material debe funcionar como pieza independiente;
- duración aproximada deseada;
- si se deben evitar referencias a clases, reuniones o lecciones anteriores/posteriores.

## Etapa 2 - Revisar la presentación

Objetivo: que la presentación pueda funcionar como soporte visual del video.

Checklist:

- quitar referencias como "Reunión 1", "próxima reunión", "clase anterior", etc.;
- agregar portada si falta;
- eliminar slides que solo servían para la clase presencial;
- confirmar que la secuencia visual coincide con el guion;
- revisar que no queden pies de página o títulos que contradigan el enfoque autónomo del video.

Resultado esperado:

```text
presentacion_editada.key
```

## Etapa 3 - Crear el guion maestro

Objetivo: transformar la transcripción en una narración clara, continua y apta para voz sintética.

El guion maestro debe tener, por cada diapositiva:

```text
## Diapositiva N - Título

Duración estimada: MM:SS

Sincronización:
Indicación breve de cómo usar la diapositiva.

Narración:
Texto limpio que se va a convertir en voz.
```

Criterios de redacción:

- no copiar literalmente la transcripción;
- mantener los conceptos reales y los ejemplos útiles;
- eliminar muletillas, interrupciones y repeticiones;
- evitar frases que dependan de una clase previa;
- escribir para una persona que ve el video sin contexto anterior;
- usar frases relativamente cortas, buenas para locución;
- dejar pausas naturales después de preguntas retóricas o ideas importantes.
- las palabras en inglés, escribirlas como suenan en inglés, de forma que el locutor al leerlo, suene como si estuviera en inglés.
- las siglas también hay que redactarlas de forma que al leerlas se pronuncien como siglas.  Por ejemplo FNR debiera redactarse EFE-ENE-ERRE, de forma que el locutor lo narre correctamente.

Resultado esperado:

```text
guion_locucion_sincronizado.md
```

## Etapa 4 - Separar locución por slide

Objetivo: generar un archivo de texto por diapositiva.

Cada archivo debe contener solo:

- título del slide;
- texto de locución.

No debe contener:

- "Narración:";
- "Duración estimada:";
- instrucciones de sincronización;
- comentarios internos.

Resultado esperado:

```text
locucion_por_slide/
  slide_01.txt
  slide_02.txt
  ...
```

## Etapa 5 - Generar la voz

Objetivo: convertir cada `slide_XX.txt` en un archivo de audio.

Recomendación: generar un audio por slide, no un único audio largo. Esto facilita:

- sincronizar la duración de cada diapositiva;
- reemplazar una parte sin rehacer todo;
- detectar errores slide por slide;
- ajustar ritmo con más precisión.

Resultado esperado:

```text
audio_por_slide/
  slide_01.mp3
  slide_02.mp3
  ...
```

Checklist:

- todos los audios deben estar numerados igual que los textos;
- escuchar al menos los primeros dos audios antes de generar todo;
- revisar pronunciación de siglas: EMO, LCR, FNE;
- revisar pronunciación de términos bancarios: fondeo, encaje, tasa pasiva, liquidez;
- verificar que no lea el título si no se desea.

## Etapa 6 - Exportar slides a PNG

Objetivo: convertir la presentación editada en imágenes finales.

Resultado esperado:

```text
png_finales/
  slide_01.png
  slide_02.png
  ...
```

Checklist:

- cantidad de PNG = cantidad de textos = cantidad de audios;
- la portada está incluida;
- no hay slides eliminados;
- no quedan referencias a reuniones o clases;
- revisar una hoja de contacto para detectar errores visuales.

## Etapa 7 - Montar el video

Objetivo: combinar cada PNG con su audio correspondiente.

Regla de montaje:

```text
slide_01.png dura lo mismo que slide_01.mp3
slide_02.png dura lo mismo que slide_02.mp3
...
```

Salida recomendada:

```text
video_final.mp4
```

Parámetros prácticos:

- formato: MP4;
- video: H.264;
- audio: AAC;
- resolución: usar la resolución exportada por la presentación, o 1920x1080 si se exporta en alta;
- sin transiciones al principio: primero validar contenido y sincronización.

## Etapa 8 - Control de calidad

Antes de darlo por terminado:

- reproducir el video completo o al menos por bloques;
- revisar el inicio, mitad y final;
- confirmar que las diapositivas avanzan;
- verificar que no haya slides congelados;
- revisar que el audio no corte al final de cada slide;
- escuchar pronunciación de siglas y conceptos técnicos;
- verificar que el archivo final abra correctamente;
- guardar una versión fechada.

Ejemplo de nombres:

```text
video_final_v1.mp4
video_final_v2_voz_mejorada.mp4
video_final_aprobado.mp4
```

## Roles: qué hace Codex y qué conviene revisar manualmente

Codex puede hacer:

- revisar presentación y transcripción;
- proponer y editar guion;
- separar locución por slide;
- revisar cantidad de archivos;
- generar hojas de contacto;
- montar video;
- verificar duración, resolución y pistas de audio/video;
- dejar scripts y estructura de carpetas.

Conviene revisar manualmente:

- tono final del guion;
- si los ejemplos son institucionalmente correctos;
- pronunciación y naturalidad de la voz;
- estética de la presentación;
- si el video final resulta demasiado largo o demasiado rápido.

## Rutina resumida para repetir

```text
1. Crear carpeta del video.
2. Guardar presentación y transcripción en 00_insumos.
3. Revisar y editar presentación.
4. Construir guion maestro por diapositiva.
5. Separar locución por slide.
6. Generar audios por slide.
7. Exportar presentación a PNG.
8. Verificar que textos, PNG y audios tengan la misma cantidad.
9. Montar MP4.
10. Revisar, ajustar y generar versión final.
```

## Próxima mejora recomendada

Convertir este proceso en un pequeño kit reutilizable con:

```text
crear_proyecto.py
separar_locucion.py
validar_archivos.py
montar_video.swift
README_PROCESO.md
config.json
```

Así, para cada nuevo video solo habría que:

1. crear una carpeta nueva;
2. poner presentación y transcripción;
3. editar el guion;
4. ejecutar los scripts en orden.
