"""Detecta se o PDF é nativo (texto selecionável) ou escaneado (imagem).

Regra da spec (convert.md): média de caracteres por página > 50 => native.
"""
import pymupdf

MIN_CHARS_PER_PAGE = 50


def is_native_pdf(path: str, min_chars_per_page: int = MIN_CHARS_PER_PAGE) -> bool:
    """True se o PDF tem texto selecionável suficiente (não é só imagem)."""
    doc = pymupdf.open(path)
    try:
        total_chars = sum(len(page.get_text().strip()) for page in doc)
        pages = max(doc.page_count, 1)
    finally:
        doc.close()
    return (total_chars / pages) > min_chars_per_page


def detect_document_type(
    path: str, min_chars_per_page: int = MIN_CHARS_PER_PAGE
) -> str:
    """Retorna 'native' ou 'scanned'."""
    return "native" if is_native_pdf(path, min_chars_per_page) else "scanned"


def count_pages(path: str) -> int:
    doc = pymupdf.open(path)
    try:
        return doc.page_count
    finally:
        doc.close()
