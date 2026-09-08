# mp4_creation

Pipeline para convertir material educativo (presentación + transcripción de clase)
en un video MP4 listo para YouTube, con locución sintética sincronizada con las
diapositivas.

## Cómo funciona

Siete scripts numerados que se corren en orden. Cada uno es independiente,
reejecutable, y salta lo que ya está hecho salvo que se le pase `--forzar`.

```
00_validar_insumos.py   ¿están los archivos, ffmpeg y la credencial?
01_preparar_slides.py   PNG → slide_01.png, slide_02.png… + hoja de contacto
02_escribir_guion.py    transcripción + slides → guion_maestro.md   ← API de OpenAI
        ▼ PARADA: revisión humana del guion
03_dividir_guion.py     guion_maestro.md → un .txt por segmento
04_crear_audios.py      un .txt → un .mp3            ← edge-tts
05_montar_video.py      PNG + audio → video_final.mp4  ← ffmpeg
06_control_calidad.py   reporte, capturas y avisos
```

`correr_pipeline.py` los encadena y se detiene solo en la parada del guion.

## Instalación (una vez)

```bash
brew install ffmpeg
pip install -r requirements.txt
echo 'OPENAI_API_KEY=sk-...' > .env    # con tu clave real
```

## Uso

```bash
python 00_validar_insumos.py --proyecto 01_content
python 01_preparar_slides.py --proyecto 01_content
# revisar 01_content/03_output/qc/hoja_de_contacto.png

python 02_escribir_guion.py --proyecto 01_content
# LEER Y EDITAR 01_content/02_archivosIntermedios/guion/guion_maestro.md

python 03_dividir_guion.py --proyecto 01_content
python 04_crear_audios.py --proyecto 01_content --segmentos 1 2
# ESCUCHAR esos dos audios antes de generar el resto

python 04_crear_audios.py --proyecto 01_content
python 05_montar_video.py --proyecto 01_content
python 06_control_calidad.py --proyecto 01_content
```

O todo de una:

```bash
python correr_pipeline.py --proyecto 01_content            # se detiene tras el guion
python correr_pipeline.py --proyecto 01_content --desde 03 # continuar tras aprobarlo
```

## Un video nuevo

1. Crear una carpeta hermana de `01_content` (por ejemplo `02_content`) con:

   ```
   02_content/
     proyecto.yaml                    ← copiar el de 01_content y ajustar
     01_materialOriginal/
       slides/                        ← los PNG exportados de la presentación
       exposicion/                    ← la transcripción (.md o .txt)
       fichas_lectura/                ← material de apoyo (opcional)
   ```

2. Correr el pipeline con `--proyecto 02_content`.

Las carpetas de salida se crean solas.

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

**Pronunciación.** El guion se escribe en castellano normal (`LCR`, `cash flow`)
y la corrección fonética vive en `config/lexico.yaml`, que se aplica recién al
sintetizar. Así el guion sigue siendo legible y la corrección sirve para todos
los videos.

**Transición de apertura.** Cada diapositiva puede abrir con dos mecanismos
independientes y combinables, aplicados solo a su primer segmento (nunca a los
`b`, `c`... que comparten imagen con el anterior):

- `guion.transicion_titulo` — el modelo redacta una frase de transición propia
  antes de entrar en el contenido (no el título leído literal). Es una
  instrucción de prompt: vive en `02_escribir_guion.py`.
- `audio.pausa_inicial_seg` — silencio real antepuesto al audio, vía el filtro
  `adelay` de ffmpeg (`comun/ffmpeg.py::anteponer_silencio`). No se puede lograr
  pidiéndoselo al modelo de texto ni depender de que el proveedor de voz
  soporte SSML, así que se inserta después de sintetizar — mismo punto donde se
  aplica el léxico de pronunciación.

## Configuración

`config/lexico.yaml` es compartido. `proyecto.yaml` es de cada video; lo que no
esté ahí toma el valor por defecto de `comun/config.py`. Lo que más se toca:

| Clave | Para qué |
| --- | --- |
| `guion.modelo` | Modelo de OpenAI (por defecto `gpt-5.4`) |
| `guion.reglas` | Reglas editoriales que recibe el modelo |
| `guion.duracion_objetivo_min` | Largo buscado del video |
| `guion.max_segmentos_por_slide` | Cuánto puede subdividirse una diapositiva |
| `guion.transicion_titulo` | El primer segmento de cada diapositiva abre con una frase de transición |
| `audio.proveedor` | `edge` (gratis) · `openai` · `existente` |
| `audio.voz` | `es-AR-TomasNeural`, `es-AR-ElenaNeural`, `es-UY-MateoNeural`… |
| `audio.pausa_inicial_seg` | Silencio antepuesto al primer segmento de cada diapositiva (`0` lo apaga) |
| `video.movimiento` | `ninguno` o `kenburns` (deriva lenta en segmentos largos) |

## Tests

```bash
python -m pytest tests/ -q
```

Cubren lo que más fácil se rompe en silencio: el orden de las diapositivas y los
caracteres invisibles en sus nombres, el parseo del guion editado a mano, y los
reemplazos del léxico.

## Qué queda manual

Exportar la presentación a PNG. El pipeline los toma de
`01_materialOriginal/slides/` con cualquier nombre, siempre que terminen en un
número.
