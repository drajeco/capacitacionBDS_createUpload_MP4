"""Lectura compartida de fichas y bibliografía."""

from pathlib import Path


def leer_material_complementario(ruta: Path) -> str:
    """Lee texto o PDF con capa de texto; no omite bibliografía ilegible."""
    if ruta.suffix.lower() != ".pdf":
        texto = ruta.read_text(encoding="utf-8").strip()
    else:
        from pypdf import PdfReader
        from pypdf.errors import PyPdfError

        try:
            paginas = []
            for numero, pagina in enumerate(PdfReader(ruta).pages, start=1):
                contenido = (pagina.extract_text() or "").strip()
                if not contenido:
                    raise ValueError(
                        f"la página {numero} no tiene texto extraíble; "
                        "prepará una versión con OCR o en .md/.txt"
                    )
                paginas.append(f"Página {numero}\n{contenido}")
            texto = "\n\n".join(paginas)
        except PyPdfError as exc:
            raise ValueError(f"PDF ilegible: {exc}") from exc
    if not texto:
        raise ValueError("el archivo no contiene texto")
    return texto
