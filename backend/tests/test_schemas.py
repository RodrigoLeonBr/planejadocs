"""Testes dos schemas Pydantic (espelham specs/openapi.yaml)."""
import pytest
from pydantic import ValidationError

from app.schemas import (
    ConvertResponse,
    DocumentMetadata,
    ErrorResponse,
    HealthResponse,
    SavedOutput,
    TablesResponse,
    ThemesResponse,
)


def test_health_response():
    h = HealthResponse(status="ok", version="0.1.0", timestamp="2026-01-01T00:00:00Z")
    assert h.status == "ok"


def test_health_rejects_bad_status():
    with pytest.raises(ValidationError):
        HealthResponse(status="broken", version="0.1.0", timestamp="x")


def test_document_metadata_optional_fields_default_none():
    m = DocumentMetadata(source="a.pdf", type="native", pages=10)
    assert m.duration_ms is None
    assert m.ocr is None


def test_document_metadata_rejects_bad_type():
    with pytest.raises(ValidationError):
        DocumentMetadata(source="a.pdf", type="imagem", pages=1)


def test_convert_response_requires_markdown_and_metadata():
    meta = DocumentMetadata(source="a.pdf", type="native", pages=1)
    r = ConvertResponse(markdown="# oi", metadata=meta)
    assert r.tables is None
    with pytest.raises(ValidationError):
        ConvertResponse(markdown="# oi")  # falta metadata


def test_convert_response_output_opcional():
    meta = DocumentMetadata(source="a.pdf", type="native", pages=1)
    r = ConvertResponse(markdown="# oi", metadata=meta)
    assert r.output is None
    saved = SavedOutput(tema="contratos", dir="/o/contratos", markdown="/o/c/a.md")
    r2 = ConvertResponse(markdown="# oi", metadata=meta, output=saved)
    assert r2.output.tema == "contratos"
    assert r2.output.tables_json is None


def test_themes_response():
    t = ThemesResponse(themes=["contratos", "escalas"])
    assert t.themes == ["contratos", "escalas"]


def test_tables_response():
    t = TablesResponse(tables=[{"page": 1}], format="json", count=1)
    assert t.count == 1
    with pytest.raises(ValidationError):
        TablesResponse(tables=[], format="pdf", count=0)  # format inválido


def test_error_response_requires_code_and_message():
    e = ErrorResponse(code="PDF2MD_001", message="boom")
    assert e.details is None
    with pytest.raises(ValidationError):
        ErrorResponse(code="PDF2MD_001")  # falta message
