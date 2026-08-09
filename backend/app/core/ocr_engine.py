"""OCR para PDFs escaneados via RapidOCR (ONNX, CPU). Import lazy.

Usado em ~5% dos casos (escalas/demonstrativos escaneados). Cada página é
rasterizada e reconhecida; qualquer falha vira PDF2MD_004. Leve e sem GPU
(~1s/página), sem binário externo.
"""
import os
import re

import pymupdf

from ..errors import ocr_failed

OCR_DPI = int(os.getenv("PDF2MD_OCR_DPI", "200"))

_engine = None


def _latin_count(txts) -> int:
    """Nº de chars latinos/dígitos reconhecidos — orientação errada alucina CJK."""
    return sum(len(re.findall(r"[A-Za-z0-9]", t)) for t in (txts or ()))


def _ocr_page(engine, page, rot: int):
    """Rasteriza a página (rotacionada `rot` graus) e roda o OCR."""
    m = pymupdf.Matrix(OCR_DPI / 72, OCR_DPI / 72).prerotate(rot)
    return engine(page.get_pixmap(matrix=m).tobytes("png"))


def _detect_rotation(engine, page):
    """Escolhe a rotação (0/90/180/270) com mais texto latino na 1ª página.

    Escaneados às vezes vêm deitados (ex.: escalas de plantão em paisagem);
    sem isso o OCR lê a grade de lado e vira lixo. Devolve (rot, resultado_pg0).
    # ponytail: assume orientação uniforme no doc (detecta na pg0, aplica a todas);
    # se algum scan misturar orientações por página, detectar por página.
    """
    best = (0, None, -1)
    for rot in (0, 90, 180, 270):
        res = _ocr_page(engine, page, rot)
        score = _latin_count(res.txts)
        if score > best[2]:
            best = (rot, res, score)
    return best[0], best[1]


def _get_engine():
    """Carrega o RapidOCR uma vez (a inicialização é cara) e reaproveita.

    Modelo de reconhecimento LATIN: os docs da SMS são só português (script
    latino). O modelo chinês padrão alucina ideogramas (口/品/中) nas células
    de 1 char (D/F/BH/8h) das grades; o LATIN elimina isso.
    """
    global _engine
    if _engine is None:
        from rapidocr import LangRec, RapidOCR

        _engine = RapidOCR(params={"Rec.lang_type": LangRec.LATIN})
    return _engine


def _run_ocr(path: str) -> str:
    """Roda o OCR página a página e devolve markdown. Glue da dependência opcional.

    # ponytail: não coberto por teste (requer os modelos ONNX do RapidOCR);
    # validar num PDF escaneado real quando a dependência estiver instalada.
    """
    engine = _get_engine()
    doc = pymupdf.open(path)
    try:
        blocks = []
        rot, first = _detect_rotation(engine, doc[0])
        for i, page in enumerate(doc):
            result = first if i == 0 else _ocr_page(engine, page, rot)
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
