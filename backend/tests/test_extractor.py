"""Testes do extrator de markdown (spec convert.md)."""
import pymupdf
import pytest

from app.core import ocr_engine
from app.core.extractor import convert_to_markdown
from app.errors import PDF2MDError


def test_native_pdf_gera_markdown(native_pdf):
    result = convert_to_markdown(str(native_pdf))
    assert "Relatório de gestão" in result["markdown"]
    assert result["metadata"]["type"] == "native"
    assert result["metadata"]["pages"] == 1
    assert result["metadata"]["source"] == "native.pdf"
    assert result["metadata"]["duration_ms"] >= 0
    assert result["metadata"]["ocr"] is None


def test_escaneado_delega_ao_ocr(scanned_pdf, monkeypatch):
    monkeypatch.setattr(ocr_engine, "_run_marker", lambda p: "# Escala\ntexto OCR")
    result = convert_to_markdown(str(scanned_pdf))
    assert result["markdown"] == "# Escala\ntexto OCR"
    assert result["metadata"]["type"] == "scanned"
    assert result["metadata"]["ocr"] == "marker"


def test_nao_pdf_retorna_erro_005(tmp_path):
    txt = tmp_path / "doc.txt"
    txt.write_text("não é pdf")
    with pytest.raises(PDF2MDError) as exc:
        convert_to_markdown(str(txt))
    assert exc.value.code == "PDF2MD_005"


def test_excede_max_paginas_retorna_erro_003(tmp_path):
    path = tmp_path / "grande.pdf"
    doc = pymupdf.open()
    for _ in range(501):
        doc.new_page()
    doc.save(path)
    doc.close()
    with pytest.raises(PDF2MDError) as exc:
        convert_to_markdown(str(path))
    assert exc.value.code == "PDF2MD_003"
