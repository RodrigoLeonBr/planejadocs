"""OCR para PDFs escaneados via Marker (Surya). Import lazy; lento em CPU.

Usado em ~5% dos casos (escalas de trabalho escaneadas). Qualquer falha
(dependência ausente ou erro do engine) vira PDF2MD_004.
"""
from ..errors import ocr_failed


def _run_marker(path: str) -> str:
    """Roda o Marker e devolve o markdown. Import lazy da dependência opcional.

    # ponytail: glue contra a API do marker-pdf 1.x, não coberto por teste
    # (requer a dependência + modelos). Validar quando marker for instalado.
    """
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    converter = PdfConverter(artifact_dict=create_model_dict())
    rendered = converter(path)
    text, _, _ = text_from_rendered(rendered)
    return text


def ocr_scanned_pdf(path: str) -> str:
    """Converte um PDF escaneado em markdown via OCR. Levanta PDF2MD_004 em falha."""
    try:
        return _run_marker(path)
    except Exception as e:
        raise ocr_failed() from e
