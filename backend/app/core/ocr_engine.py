"""OCR para PDFs escaneados via RapidOCR (ONNX, CPU). Import lazy.

Usado em ~5% dos casos (escalas/demonstrativos escaneados). Cada página é
rasterizada e reconhecida; qualquer falha vira PDF2MD_004. Leve e sem GPU
(~1s/página), sem binário externo.
"""
import os

from ..errors import ocr_failed

OCR_DPI = int(os.getenv("PDF2MD_OCR_DPI", "200"))

_engine = None


def _get_engine():
    """Carrega o RapidOCR uma vez (a inicialização é cara) e reaproveita."""
    global _engine
    if _engine is None:
        from rapidocr import RapidOCR

        _engine = RapidOCR()
    return _engine


def _run_ocr(path: str) -> str:
    """Roda o OCR página a página e devolve markdown. Glue da dependência opcional.

    # ponytail: não coberto por teste (requer os modelos ONNX do RapidOCR);
    # validar num PDF escaneado real quando a dependência estiver instalada.
    """
    import pymupdf

    engine = _get_engine()
    doc = pymupdf.open(path)
    try:
        blocks = []
        for i, page in enumerate(doc):
            png = page.get_pixmap(dpi=OCR_DPI).tobytes("png")
            result = engine(png)
            texto = "\n\n".join(result.txts or ())
            blocks.append(f"## Página {i + 1}\n\n{texto}".rstrip())
        return "\n\n".join(blocks)
    finally:
        doc.close()


def ocr_scanned_pdf(path: str) -> str:
    """Converte um PDF escaneado em markdown via OCR. Levanta PDF2MD_004 em falha."""
    try:
        return _run_ocr(path)
    except Exception as e:
        raise ocr_failed() from e
