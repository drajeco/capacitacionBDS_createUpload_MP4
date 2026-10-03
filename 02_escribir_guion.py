#!/usr/bin/env python3
"""Paso 02 - Convierte la transcripción oral en un guion de locución por diapositiva.

Usa la API de OpenAI. Le manda las diapositivas como imágenes
—ver qué hay en pantalla es lo que alinea la narración con cada slide— junto
con la transcripción, las fichas y la bibliografía, y pide una respuesta estructurada
que después se renderiza a Markdown.

El guion resultante SIEMPRE requiere revisión humana antes de continuar.

    python 02_escribir_guion.py --proyecto 01_content
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from comun.materiales import leer_material_complementario
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
    titulo_leccion: str = Field(min_length=1, max_length=150, description="Título breve de la lección, inferido de las diapositivas y la exposición; sin número de lección")
    segmentos: list[SegmentoGuion]


def imagen_a_data_url(ruta: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(ruta.read_bytes()).decode("ascii")


def construir_instrucciones(proy) -> str:
    cfg = proy.guion_cfg
    estilo = (config.RAIZ / "config" / "estilo_guion.md").read_text(encoding="utf-8")
    transicion = (
        "APERTURA DE CADA DIAPOSITIVA:\n"
        "- TODAS las diapositivas deben comenzar con una introducción natural que "
        "mencione directa o indirectamente su título o tema visible. Integrala a "
        "la explicación en una o dos frases; no leas un encabezado aislado.\n"
        "- Si varias diapositivas repiten título, cada una también necesita apertura: "
        "conectá con la anterior y nombrá la idea nueva que aparece en esta pantalla. "
        "No anuncies un cambio de sección cuando solo continúa el mismo tema.\n"
        "- Variá las entradas según su función: presentar un tema, continuar una "
        "explicación, proponer un ejemplo, introducir una consecuencia o resumir. "
        "No empieces todas con 'ahora veremos' ni agregues una frase de relleno.\n"
        "- Si una diapositiva tiene varios segmentos, la introducción va solo en "
        "el primero; los siguientes continúan la explicación sin volver a presentarla.\n"
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
        f"ESTILO DE LOCUCIÓN COMPARTIDO:\n{estilo}\n\n"
        "REGLAS EDITORIALES DEL PROYECTO:\n"
        f"{cfg['reglas']}\n"
        "ESTRUCTURA DE LA SALIDA:\n"
        f"- Tenés que cubrir exactamente las diapositivas 1 a {cfg['_cantidad_slides']}, "
        "en orden y sin saltear ninguna.\n"
        "- Cada diapositiva puede dividirse en segmentos para organizar unidades "
        "conceptuales y facilitar la síntesis. Todos comparten la misma imagen: "
        "dividir no implica un cambio visual. Usá hasta "
        f"{cfg['max_segmentos_por_slide']} segmentos por diapositiva, de unas "
        f"{cfg['palabras_por_segmento']} palabras como referencia por segmento. "
        "No es una cuota: ajustá la extensión a lo que necesita cada idea.\n"
        "- Si una diapositiva tiene un solo segmento, su 'sufijo' es cadena vacía. "
        "Si tiene varios, van 'a', 'b', 'c'... y NINGUNO queda con sufijo vacío.\n"
        "- Un segmento es una unidad conceptual cerrada: no cortes una idea al medio.\n"
        "- Las imágenes determinan el recorrido y qué se explica en cada pantalla. "
        "En secuencias acumulativas, concentrá la narración en lo que se agrega o "
        "cambia, sin volver a explicar todos los elementos anteriores. No describas "
        "iconos decorativos ni leas listas mecánicamente.\n"
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
        "minutos leídos en voz alta (~150 palabras por minuto). Distribuí ese "
        "tiempo según la complejidad: conservá ejemplos útiles y no comprimas "
        "todas las diapositivas a párrafos del mismo largo.\n"
        "- El campo 'narracion' contiene solo el texto a leer: sin encabezados, sin viñetas, "
        "sin acotaciones entre paréntesis, sin marcas de formato.\n"
        "- Escribí en el español rioplatense del material original.\n"
        "REVISIÓN ANTES DE ENTREGAR (no la incluyas en la narración):\n"
        "- Comprobá cobertura y correspondencia con cada imagen, apertura natural "
        "cuando esté activada y continuidad entre diapositivas.\n"
        "- Revisá ortografía, concordancia, puntuación y consistencia de ejemplos: "
        "no cambies bienes, actores, cantidades ni plazos a mitad de un razonamiento.\n"
        "- No inventes datos históricos, cifras, anécdotas ni atribuciones para "
        "imitar los ejemplos de estilo. Usá las fuentes suministradas; si no "
        "permiten sostener un detalle, omitilo o formulá solo lo que respaldan.\n"
        "- Releé como locución: eliminá frases trabadas, referencias ambiguas y "
        "repeticiones vacías, conservando las reformulaciones que ayudan a entender.\n"
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
    bibliografia = rutas.todos_los_archivos(
        proy.insumo("bibliografia"), extensiones=(".md", ".txt", ".pdf")
    )
    consola.ok(f"{len(imagenes)} diapositivas · transcripción de "
               f"{len(transcripcion.read_text(encoding='utf-8').split()):,} palabras · "
               f"{len(fichas)} ficha(s) · {len(bibliografia)} archivo(s) bibliográficos")

    # --- armado del pedido ---
    cfg = dict(proy.guion_cfg)
    cfg["_cantidad_slides"] = len(imagenes)
    proy.datos["guion"] = cfg

    contenido: list[dict] = [{
        "type": "input_text",
        "text": (
            "Inferí titulo_leccion del tema central de estas diapositivas y la exposición. "
            "No uses nombres de archivos ni títulos de ejecuciones anteriores.\n\n"
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
    for ficha in [*fichas, *bibliografia]:
        try:
            texto_apoyo = leer_material_complementario(ficha)
        except (OSError, ValueError, ImportError) as exc:
            consola.abortar(f"No se pudo leer el material complementario {ficha.name}: {exc}")
        contenido.append({
            "type": "input_text",
            "text": (
                f"--- MATERIAL COMPLEMENTARIO (usar con moderación): {ficha.stem} ---\n"
                "Esto NO es la base del guion. Recurrí a este texto solo si la "
                "transcripción deja un vacío de contenido que conviene llenar, o si hace "
                "falta precisar una definición o un término. Si la transcripción ya explica "
                "el concepto correctamente, conservá su desarrollo y sus ejemplos. "
                "Usá este apoyo para corregir imprecisiones sin cambiar esa voz.\n\n"
                + texto_apoyo
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

    titulo = resultado.titulo_leccion.strip()
    if not titulo or "\n" in titulo or "\r" in titulo:
        consola.abortar("El modelo no devolvió un título de lección válido.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    rutas.escribir_atomico(destino, guion_mod.renderizar(segmentos, titulo))

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
        "    · que no dependa de reuniones, clases ni contenido externo al video;\n"
        "    · que el texto de cada diapositiva se corresponda con lo que muestra.\n"
        "  Editalo con confianza: el paso 03 lee este archivo, no la respuesta del modelo."
    )
    consola.siguiente(f"python 03_dividir_guion.py --proyecto {args.proyecto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
