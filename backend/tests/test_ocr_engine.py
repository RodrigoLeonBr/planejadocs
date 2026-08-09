"""Testes do motor de OCR (spec convert.md: PDF2MD_004)."""
import pytest

from app.core import ocr_engine
from app.core.ocr_engine import ocr_scanned_pdf
from app.errors import PDF2MDError


def test_ocr_sucesso_retorna_texto(monkeypatch):
    monkeypatch.setattr(ocr_engine, "_run_ocr", lambda p: "# Escala\ntexto OCR")
    assert ocr_scanned_pdf("qualquer.pdf") == "# Escala\ntexto OCR"


def test_dependencia_ausente_erro_004(monkeypatch):
    def sem_marker(p):
        raise ImportError("No module named 'marker'")

    monkeypatch.setattr(ocr_engine, "_run_ocr", sem_marker)
    with pytest.raises(PDF2MDError) as exc:
        ocr_scanned_pdf("qualquer.pdf")
    assert exc.value.code == "PDF2MD_004"


def test_falha_do_engine_erro_004(monkeypatch):
    def boom(p):
        raise RuntimeError("surya crashed")

    monkeypatch.setattr(ocr_engine, "_run_ocr", boom)
    with pytest.raises(PDF2MDError) as exc:
        ocr_scanned_pdf("qualquer.pdf")
    assert exc.value.code == "PDF2MD_004"


def test_latin_count_pontua_orientacao():
    # orientação certa: texto latino legível; errada: OCR alucina CJK
    certa = ["Sarah Alves", "PERIODO", "21/12/2025"]
    errada = ["市 口 品", "口口口"]
    assert ocr_engine._latin_count(certa) > ocr_engine._latin_count(errada)
    assert ocr_engine._latin_count(None) == 0
