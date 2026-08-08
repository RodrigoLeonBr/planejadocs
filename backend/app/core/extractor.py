"""Extração principal de markdown com PyMuPDF4LLM (spec convert.md)."""
import os
import time
from pathlib import Path

import pymupdf4llm

from ..errors import not_a_pdf, too_many_pages
from .detector import count_pages, detect_document_type

MAX_PAGES = int(os.getenv("PDF2MD_MAX_PAGES", "500"))
WRITE_IMAGES = os.getenv("PDF2MD_WRITE_IMAGES", "false").lower() == "true"


def convert_to_markdown(path: str, write_images: bool = WRITE_IMAGES) -> dict:
    """Converte PDF para markdown. Retorna dict com markdown + metadados.

    Levanta PDF2MDError: PDF2MD_005 (não é PDF), PDF2MD_003 (excede páginas).
    PDFs escaneados são delegados ao OCR (ocr_engine).
    """
    p = Path(path)
    if p.suffix.lower() != ".pdf":
        raise not_a_pdf()

    pages = count_pages(str(p))
    if pages > MAX_PAGES:
        raise too_many_pages()

    start = time.perf_counter()
    doc_type = detect_document_type(str(p))

    if doc_type == "scanned":
        from .ocr_engine import ocr_scanned_pdf

        md = ocr_scanned_pdf(str(p))
        ocr_engine = "marker"
    else:
        md = pymupdf4llm.to_markdown(
            str(p), write_images=write_images, page_chunks=False
        )
        ocr_engine = None

    duration_ms = int((time.perf_counter() - start) * 1000)

    return {
        "markdown": md,
        "metadata": {
            "source": p.name,
            "type": doc_type,
            "pages": pages,
            "duration_ms": duration_ms,
            "ocr": ocr_engine,
        },
    }
