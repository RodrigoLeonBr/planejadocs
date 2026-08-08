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
def table_pdf(tmp_path):
    """PDF nativo com uma tabela 3x2 desenhada (linhas que pdfplumber detecta)."""
    path = tmp_path / "table.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    cols = [50, 200, 350]
    rows = [100, 130, 160, 190]
    for y in rows:
        page.draw_line((cols[0], y), (350, y))
    for x in [*cols, 350]:
        page.draw_line((x, rows[0]), (x, rows[-1]))
    cells = [["Nome", "Valor"], ["UBS A", "100"], ["UBS B", "200"]]
    for r, row in enumerate(cells):
        for c, val in enumerate(row):
            page.insert_text((cols[c] + 5, rows[r] + 20), val, fontsize=10)
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
