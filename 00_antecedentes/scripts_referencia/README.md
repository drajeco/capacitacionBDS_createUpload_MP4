# Scripts de referencia de la primera prueba

Estos scripts son copias de los utilizados en la prueba realizada en `/Users/diegoabal/Desktop/0102`. Se conservan como antecedente funcional; no constituyen todavía la versión reutilizable del proyecto.

## Contenido

- `montar_video.swift`: monta un MP4 a partir de `png_finales/` y audios `.m4a` en `audio_por_slide/`.
- `montar_video_audio_alt.swift`: variante usada para montar el MP4 con los audios `.wav` de `audio_por_slide_alt/`.
- `extraer_frames.swift`: extrae capturas del primer MP4 para control visual.
- `extraer_frames_audio_alt.swift`: extrae capturas del MP4 generado con los WAV alternativos.

## Advertencias antes de ejecutarlos

Los scripts tienen rutas absolutas a la carpeta original `/Users/diegoabal/Desktop/0102`, nombres específicos de archivos y resolución de 960 x 540. También reemplazan los archivos de salida definidos en el propio script.

Por lo tanto, deben tomarse como base de lectura. La versión de desarrollo deberá reemplazar esas rutas por un archivo de configuración por proyecto, validar la correspondencia entre `slide_XX.png` y `slide_XX.wav`, y producir el video con `ffmpeg` o un montador equivalente más portable.
