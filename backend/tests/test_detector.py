"""Testes do detector de tipo (spec convert.md: > 50 chars/página = native)."""
from app.core.detector import count_pages, detect_document_type, is_native_pdf


def test_is_native_pdf_true(native_pdf):
    assert is_native_pdf(str(native_pdf)) is True


def test_is_native_pdf_false(scanned_pdf):
    assert is_native_pdf(str(scanned_pdf)) is False


def test_detect_native(native_pdf):
    assert detect_document_type(str(native_pdf)) == "native"


def test_detect_scanned(scanned_pdf):
    assert detect_document_type(str(scanned_pdf)) == "scanned"


def test_threshold_boundary(native_pdf):
    """Threshold configurável: exigir muito texto força classificar como scanned."""
    assert detect_document_type(str(native_pdf), min_chars_per_page=100000) == "scanned"


def test_count_pages(native_pdf):
    assert count_pages(str(native_pdf)) == 1
