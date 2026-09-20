"""Testes do extrator de tabelas (spec convert.md)."""
import io
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.core.table_extractor import (
    _normalize_cell,
    clean_table_financial_values,
    extract_tables,
    parse_financial_value,
    save_excel,
    tables_to_csv,
    tables_to_excel_bytes,
    tables_to_json,
)


def test_extrai_tabela(table_pdf):
    tables = extract_tables(str(table_pdf))
    assert len(tables) == 1
    t = tables[0]
    assert t["page"] == 1
    assert t["table_index"] == 0
    assert t["rows"] == [["Nome", "Valor"], ["UBS A", "100"], ["UBS B", "200"]]


def test_normalize_cell_colapsa_espacos():
    assert _normalize_cell("  ATIVIDADE   EDUCATIVA \n GRUPO ") == "ATIVIDADE EDUCATIVA GRUPO"
    assert _normalize_cell("38,00") == "38,00"
    assert _normalize_cell(None) == ""


def test_extrai_tabela_motor_pymupdf(table_pdf):
    tables = extract_tables(str(table_pdf), engine="pymupdf")
    assert len(tables) == 1
    assert tables[0]["rows"] == [["Nome", "Valor"], ["UBS A", "100"], ["UBS B", "200"]]


def test_motor_invalido_cai_no_padrao(table_pdf):
    padrao = extract_tables(str(table_pdf))
    assert extract_tables(str(table_pdf), engine="inexistente") == padrao


# PDF real da tabela de valores (untracked); pula quando ausente.
_TABELA_VALORES = (
    Path(__file__).resolve().parents[2] / "TabeladeValores01.04.2026.pdf"
)


@pytest.mark.skipif(
    not _TABELA_VALORES.exists(), reason="PDF TabeladeValores ausente"
)
def test_pymupdf_valor_limpo_e_acento_no_pdf_real(tmp_path):
    # Fatia só a 1ª página (onde está a linha 38,00) — o doc tem 63 páginas e
    # extrair todas leva minutos.
    import pymupdf

    src = pymupdf.open(str(_TABELA_VALORES))
    p1 = tmp_path / "pagina1.pdf"
    out = pymupdf.open()
    out.insert_pdf(src, from_page=0, to_page=0)
    out.save(p1)
    out.close()
    src.close()

    linha = extract_tables(str(p1), engine="pymupdf")[0]["rows"][1]
    assert linha[2] == "38,00"  # valor sem glifo-a-glifo espaçado
    assert "ORIENTAÇÃO" in linha[1]  # acento preservado
    # pdfplumber (padrão) estraga o valor nesta planilha:
    padrao = extract_tables(str(p1))[0]["rows"][1]
    assert padrao[2] != "38,00"


def test_sem_tabela_retorna_lista_vazia(native_pdf):
    assert extract_tables(str(native_pdf)) == []


def test_tables_to_json(table_pdf):
    tables = extract_tables(str(table_pdf))
    parsed = json.loads(tables_to_json(tables))
    assert parsed == tables


def test_tables_to_csv(table_pdf):
    tables = extract_tables(str(table_pdf))
    csv_text = tables_to_csv(tables)
    assert "Nome,Valor" in csv_text
    assert "UBS A,100" in csv_text


def test_tables_to_excel_bytes(table_pdf):
    tables = extract_tables(str(table_pdf))
    data = tables_to_excel_bytes(tables)
    assert isinstance(data, bytes) and len(data) > 0
    wb = load_workbook(io.BytesIO(data))
    assert wb.active["A1"].value == "Nome"


def test_save_excel(table_pdf, tmp_path):
    tables = extract_tables(str(table_pdf))
    out = tmp_path / "tabelas.xlsx"
    save_excel(tables, str(out))
    assert out.exists()
    wb = load_workbook(out)
    ws = wb.active
    assert ws["A1"].value == "Nome"
    assert ws["B3"].value == "200"


def test_consolidate_multi_page_tables(tmp_path):
    # Simula 2 páginas da mesma tabela (página 2 continua sem cabeçalho)
    t1 = {"page": 1, "table_index": 0, "rows": [["Cod", "Nome"], ["01", "Item A"]]}
    t2 = {"page": 2, "table_index": 0, "rows": [["02", "Item B"], ["03", "Item C"]]}
    
    csv_text = tables_to_csv([t1, t2])
    assert "Cod,Nome" in csv_text
    assert "01,Item A" in csv_text
    assert "02,Item B" in csv_text
    assert "03,Item C" in csv_text
    assert csv_text.count("Cod,Nome") == 1

    out = tmp_path / "multi.xlsx"
    save_excel([t1, t2], str(out))
    wb = load_workbook(out)
    assert len(wb.sheetnames) == 1
    ws = wb.active
    assert ws["A1"].value == "Cod"
    assert ws["A2"].value == "01"
    assert ws["A3"].value == "02"
    assert ws["A4"].value == "03"


def test_parse_financial_value():
    assert parse_financial_value("R$ 33,34") == "33.34"
    assert parse_financial_value("3 8 , 0 0") == "38.00"
    assert parse_financial_value("1 . 1 0 0,00") == "1100.00"
    assert parse_financial_value("4 . 6 5 0 , 0 5") == "4650.05"
    assert parse_financial_value("3 1 3 ,44") == "313.44"
    assert parse_financial_value("150,00") == "150.00"
    assert parse_financial_value(None) == ""
    assert parse_financial_value("") == ""


def test_clean_table_financial_values():
    header = ["Código", "Procedimento", "Valor"]
    r1 = ["01", "Consulta", "R$ 33,34"]
    r2 = ["02", "Exame", "3 8 , 0 0"]
    cleaned = clean_table_financial_values([header, r1, r2])
    assert cleaned[1][2] == "33.34"
    assert cleaned[2][2] == "38.00"


def test_tables_to_csv_pt_br():
    t = [{"page": 1, "table_index": 0, "rows": [["Cod", "Valor"], ["01", "38.00"]]}]
    csv_ptbr = tables_to_csv(t, format="pt_br")
    assert "Cod;Valor" in csv_ptbr
    assert "01;38,00" in csv_ptbr


def test_excel_numeric_typing(tmp_path):
    t = [{"page": 1, "table_index": 0, "rows": [["Cod", "Valor"], ["01", "38.00"]]}]
    out = tmp_path / "typed.xlsx"
    save_excel(t, str(out))
    wb = load_workbook(out)
    ws = wb.active
    assert ws["B2"].value == 38.0
    assert ws["B2"].number_format == "#,##0.00"




