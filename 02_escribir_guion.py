#!/usr/bin/env python3
"""Paso 02 - Convierte la transcripción oral en un guion de locución por diapositiva.

Único paso que usa la API de OpenAI. Le manda las diapositivas como imágenes
—ver qué hay en pantalla es lo que alinea la narración con cada slide— junto
con la transcripción y las fichas de lectura, y pide una respuesta estructurada
que después se renderiza a Markdown.

El guion resultante SIEMPRE requiere revisión humana antes de continuar.

    python 02_escribir_guion.py --proyecto 01_content
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from comun import config, consola, guion as guion_mod, modelo, rutas


class SegmentoGuion(BaseModel):
    slide: int = Field(description="Número de diapositiva, empezando en 1")
    sufijo: str = Field(
        description=(
            "Letra del segmento dentro de la diapositiva: 'a', 'b', 'c'... "
            "Cadena vacía si la diapositiva tiene un solo segmento. "
            "Si una diapositiva tiene varios, TODOS llevan letra."
        )
    )
    titulo: str = Field(description="Título breve de la diapositiva, sin numerarla")
    narracion: str = Field(description="Texto exacto que va a leer la voz, sin encabezados ni marcas")


class Guion(BaseModel):
    segmentos: list[SegmentoGuion]


def imagen_a_data_url(ruta: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(ruta.read_bytes()).decode("ascii")


def construir_instrucciones(proy) -> str:
    cfg = proy.guion_cfg
    transicion = (
        "- Muchas diapositivas consecutivas comparten el mismo título porque "
        "desarrollan una misma sección en varias pantallas. Agrupalas mentalmente "
        "por título antes de escribir. La frase de transición va SOLO en el primer "
        "segmento de la PRIMERA diapositiva de cada sección nueva (cuando el "
        "título cambia respecto de la diapositiva anterior), nunca en las "
        "diapositivas siguientes que repiten el mismo título: esas continúan la "
        "narración como si fuera el mismo tramo, sin anunciarse de nuevo.\n"
        "- Esa frase de transición tiene que anunciar explícitamente el cambio de "
        "tema con una construcción del tipo 'ahora nos concentraremos en...', "
        "'pasemos a...', 'veamos ahora...', 'comenzaremos observando...'. No cites "
        "el título de la diapositiva tal cual aparece en pantalla: escribí una "
        "oración propia que anuncie de qué se trata la sección que empieza. Por "
        "ejemplo, al pasar de una sección sobre el origen del dinero a una sobre "
        "cómo intermedian los bancos, algo como 'ahora nos concentraremos en cómo "
        "intermedian los bancos'; al abrir la primera sección de contenido, algo "
        "como 'comenzaremos observando cómo se crea el dinero'.\n"
        if cfg.get("transicion_titulo", True)
        else ""
    )
    return (
        "Sos un guionista de material educativo audiovisual. Transformás la "
        "transcripción de una exposición oral en el guion de locución de un video "
        "autónomo, que se va a leer con voz sintética sobre las diapositivas que "
        "te muestro.\n\n"
        "JERARQUÍA DE LAS FUENTES (léela con atención, es la parte más importante):\n"
        "- La transcripción de la exposición oral es el material FUNDAMENTAL. El guion "
        "se basa en ella: sus conceptos, su razonamiento, sus ejemplos, su forma de "
        "explicar y su orden. El objetivo es que el video suene a esa exposición, "
        "limpia y prolija, con una voz propia y natural, no a la lectura de un libro.\n"
        "- Las fichas de lectura y el material bibliográfico son COMPLEMENTARIOS. Recurrí "
        "a ellos solo para llenar un vacío que la exposición deja abierto, precisar una "
        "definición o corregir una imprecisión, nunca para reemplazar el desarrollo, el "
        "tono ni los ejemplos de la exposición oral.\n"
        "- Si una diapositiva plantea un tema, dato o subtema que la exposición NO "
        "desarrolla, no lo dejes afuera del guion: completalo con las fichas de lectura "
        "o el material bibliográfico para que la narración cubra todo lo que la "
        "diapositiva muestra en pantalla. La prioridad de la exposición rige sobre el "
        "contenido que sí trata; no autoriza a dejar huecos temáticos frente a lo que "
        "pide la diapositiva.\n"
        "- Si un tramo de la exposición ya cubre bien un concepto, escribilo a partir de "
        "ESE tramo. No lo reemplaces por la versión del material de apoyo aunque esté "
        "mejor redactada: se notaría el cambio de voz y dejaría de sonar propio.\n"
        "- Evitá que el guion se lea como un resumen de manual: nada de definiciones "
        "generales enumeradas si la exposición ya las explica con un ejemplo concreto.\n\n"
        "REGLAS EDITORIALES (obligatorias):\n"
        f"{cfg['reglas']}\n"
        "ESTRUCTURA DE LA SALIDA:\n"
        f"- Tenés que cubrir exactamente las diapositivas 1 a {cfg['_cantidad_slides']}, "
        "en orden y sin saltear ninguna.\n"
        "- Cada diapositiva puede dividirse en varios segmentos de narración para que "
        "la imagen no quede fija demasiado tiempo. Usá hasta "
        f"{cfg['max_segmentos_por_slide']} segmentos por diapositiva, de unas "
        f"{cfg['palabras_por_segmento']} palabras cada uno.\n"
        "- Si una diapositiva tiene un solo segmento, su 'sufijo' es cadena vacía. "
        "Si tiene varios, van 'a', 'b', 'c'... y NINGUNO queda con sufijo vacío.\n"
        "- Un segmento es una unidad conceptual cerrada: no cortes una idea al medio.\n"
        "- La diapositiva 1 es la portada y es un caso especial: su narración "
        "tiene que presentar el video entero, no describir la imagen. Anunciá el "
        "curso o tema general y los ejes que se van a tratar (los que aparecen "
        "listados en la portada, dichos con tus propias palabras, no leídos "
        "literalmente), y cerrá anticipando por dónde se empieza. Por ejemplo, "
        "con un tono como: 'Este es un curso de introducción a la gestión "
        "bancaria y nos concentraremos hoy en la intermediación bancaria. "
        "Vamos a abordar los temas de dinero, intermediación, riesgos y "
        "servicios financieros. Empecemos por...'.\n"
        f"{transicion}"
        f"- Duración objetivo del video completo: unos {cfg['duracion_objetivo_min']} "
        "minutos leídos en voz alta (~150 palabras por minuto).\n"
        "- El campo 'narracion' contiene solo el texto a leer: sin títulos, sin viñetas, "
        "sin acotaciones entre paréntesis, sin marcas de formato.\n"
        "- Escribí en el español rioplatense del material original.\n"
    )


def main() -> int:
    args = config.parser(__doc__).parse_args()
    proy = config.cargar(args.proyecto)
    consola.titulo("Paso 02", f"Escribir guion · {proy.nombre}")

    destino = proy.salida("guion")
    if destino.is_file() and not args.forzar:
        consola.aviso(f"Ya existe {destino.name}. Usar --forzar para regenerarlo desde cero.")
        consola.info("  [dim]Regenerar descarta cualquier edición manual que le hayas hecho.[/]")
        consola.siguiente(f"python 03_dividir_guion.py --proyecto {args.proyecto}")
        return 0

    clave = config.clave_openai()
    if not clave:
        consola.abortar(
            "Falta OPENAI_API_KEY.\n"
            "  Opción 1:  export OPENAI_API_KEY=sk-...\n"
            f"  Opción 2:  crear un archivo .env en {config.RAIZ} con la línea "
            "OPENAI_API_KEY=sk-..."
        )

    # --- insumos ---
    imagenes = rutas.descubrir_slides(proy.salida("slides"))
    if not imagenes:
        consola.abortar(
            f"No hay diapositivas normalizadas en {proy.salida('slides')}.\n"
            f"  Correr antes: python 01_preparar_slides.py --proyecto {args.proyecto}"
        )

    transcripcion = rutas.primer_archivo(proy.insumo("transcripcion"))
    if not transcripcion:
        consola.abortar(f"Falta la transcripción en {proy.insumo('transcripcion')}")

    fichas = rutas.todos_los_archivos(proy.insumo("fichas"))
    consola.ok(f"{len(imagenes)} diapositivas · transcripción de "
               f"{len(transcripcion.read_text(encoding='utf-8').split()):,} palabras · "
               f"{len(fichas)} ficha(s)")

    # --- armado del pedido ---
    cfg = dict(proy.guion_cfg)
    cfg["_cantidad_slides"] = len(imagenes)
    proy.datos["guion"] = cfg

    contenido: list[dict] = [{
        "type": "input_text",
        "text": (
            f"Título del video: {proy.titulo}\n\n"
            f"A continuación, las {len(imagenes)} diapositivas en orden. "
            "La narración de cada una tiene que corresponder con lo que se ve en ella."
        ),
    }]
    for numero, imagen in enumerate(imagenes, start=1):
        contenido.append({"type": "input_text", "text": f"--- Diapositiva {numero} ---"})
        contenido.append({"type": "input_image", "image_url": imagen_a_data_url(imagen)})

    contenido.append({
        "type": "input_text",
        "text": (
            "--- MATERIAL FUNDAMENTAL: TRANSCRIPCIÓN DE LA EXPOSICIÓN ORIGINAL ---\n"
            "Esta es la base del guion. Es habla espontánea: contiene muletillas, "
            "repeticiones e interpelaciones al público presente, que hay que limpiar. "
            "Pero los conceptos, el razonamiento, los ejemplos y el orden en que se "
            "explican las cosas vienen de acá. Priorizala por sobre cualquier otra fuente.\n\n"
            + transcripcion.read_text(encoding="utf-8")
        ),
    })
    for ficha in fichas:
        contenido.append({
            "type": "input_text",
            "text": (
                f"--- MATERIAL COMPLEMENTARIO (usar con moderación): {ficha.stem} ---\n"
                "Esto NO es la base del guion. Recurrí a este texto solo si la "
                "transcripción deja un vacío de contenido que conviene llenar, o si hace "
                "falta precisar una definición o un término. Si la transcripción ya explica "
                "el concepto, ignorá este material y quedate con la versión de la "
                "exposición.\n\n"
                + ficha.read_text(encoding="utf-8")
            ),
        })

    # --- llamada ---
    from openai import OpenAI

    cliente = OpenAI(api_key=clave)
    consola.info(f"Consultando [bold]{cfg['modelo']}[/] (esfuerzo {cfg['esfuerzo']})… "
                 "puede tardar varios minutos.")

    try:
        respuesta = cliente.responses.parse(
            model=cfg["modelo"],
            instructions=construir_instrucciones(proy),
            input=[{"role": "user", "content": contenido}],
            text_format=Guion,
            reasoning={"effort": cfg["esfuerzo"]},
            max_output_tokens=cfg["max_output_tokens"],
            prompt_cache_key=f"mp4_creation:{proy.nombre}",
        )
    except Exception as exc:
        consola.abortar(f"La llamada a OpenAI falló: {exc}")

    if respuesta.status == "incomplete":
        motivo = getattr(respuesta.incomplete_details, "reason", "desconocido")
        consola.abortar(
            f"La respuesta quedó incompleta ({motivo}). "
            "Subí 'guion.max_output_tokens' en proyecto.yaml y volvé a intentar."
        )

    resultado = respuesta.output_parsed
    if resultado is None or not resultado.segmentos:
        consola.abortar("El modelo no devolvió segmentos. Reintentar.")

    # --- validación contra las diapositivas reales ---
    segmentos = sorted(
        modelo.Segmento(
            slide=s.slide,
            sufijo=(s.sufijo or "").strip().lower(),
            titulo=s.titulo.strip(),
            narracion=s.narracion.strip(),
        )
        for s in resultado.segmentos
    )

    numeros = {s.slide for s in segmentos}
    esperados = set(range(1, len(imagenes) + 1))
    if faltan := sorted(esperados - numeros):
        consola.aviso(f"el guion no cubre las diapositivas {faltan}; se van a quedar sin narración")
    if sobran := sorted(numeros - esperados):
        consola.abortar(f"el guion menciona diapositivas inexistentes: {sobran}")

    destino.parent.mkdir(parents=True, exist_ok=True)
    rutas.escribir_atomico(destino, guion_mod.renderizar(segmentos, proy.titulo or proy.nombre))

    palabras = sum(len(s.narracion.split()) for s in segmentos)
    consola.ok(f"{len(segmentos)} segmentos · {palabras:,} palabras · "
               f"~{palabras / 150:.0f} min de locución estimados")
    consola.ok(f"Guion: {destino}")

    if uso := respuesta.usage:
        consola.info(
            f"  [dim]tokens: {uso.input_tokens:,} entrada "
            f"(+{getattr(uso.input_tokens_details, 'cached_tokens', 0):,} en caché) · "
            f"{uso.output_tokens:,} salida[/]"
        )

    consola.info(
        "\n[bold yellow]PARADA — revisión humana obligatoria.[/]\n"
        f"  Abrí {destino.name} y verificá:\n"
        "    · que se entienda sin haber asistido a ninguna clase;\n"
        "    · que no mencione reuniones, clases ni contenido previo o posterior;\n"
        "    · que el texto de cada diapositiva se corresponda con lo que muestra.\n"
        "  Editalo con confianza: el paso 03 lee este archivo, no la respuesta del modelo."
    )
    consola.siguiente(f"python 03_dividir_guion.py --proyecto {args.proyecto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
