"""Fixtures compartilhadas: PDFs de teste gerados em memória."""
import pymupdf
import pytest


@pytest.fixture
def native_pdf(tmp_path):
    """PDF nativo: página com texto selecionável (> 50 chars/página)."""
    path = tmp_path / "native.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    rect = pymupdf.Rect(50, 50, 545, 800)
    page.insert_textbox(
        rect, "Relatório de gestão da Secretaria Municipal de Saúde. " * 10, fontsize=11
    )
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def scanned_pdf(tmp_path):
    """PDF 'escaneado': página em branco, sem texto (<= 50 chars/página)."""
    path = tmp_path / "scanned.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(path)
    doc.close()
    return path
