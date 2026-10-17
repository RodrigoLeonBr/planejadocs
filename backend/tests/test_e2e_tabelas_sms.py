"""Validação End-to-End do pipeline modernizado com as 4 tabelas reais da SMS."""
import re
from pathlib import Path

import pytest

from app.core.table_extractor import consolidate_tables, extract_tables, tables_to_csv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


@pytest.mark.parametrize(
    "filename, expected_min_rows",
    [
        ("TABELA DE VALORES 01-08-2024 atualizada site.pdf", 1500),
        ("Tabela de Valores 01.04.2026.pdf", 1500),
        ("Tabela de Valores e Procedimentos Cismetro  12-2025 (1).pdf", 1500),
        ("tabela de serviços 12-2024 (1).pdf", 1500),
    ],
)
def test_e2e_tabela_sms_integridade(filename, expected_min_rows):
    pdf_path = ROOT_DIR / filename
    if not pdf_path.exists():
        pytest.skip(f"PDF {filename} não encontrado na raiz.")

    # Extrai tabelas usando o novo motor padrão pymupdf
    raw_tables = extract_tables(str(pdf_path), engine="pymupdf")
    assert len(raw_tables) > 0

    consolidated = consolidate_tables(raw_tables)
    assert len(consolidated) >= 1

    # Total de linhas de dados consolidadas
    total_rows = sum(len(t["rows"]) for t in consolidated)
    assert total_rows >= expected_min_rows, f"Esperava ao menos {expected_min_rows} linhas, obteve {total_rows}"

    # Valida formato CSV SQL e pt-BR
    csv_sql = tables_to_csv(consolidated, format="sql")
    csv_br = tables_to_csv(consolidated, format="pt_br")

    assert len(csv_sql) > 1000
    assert len(csv_br) > 1000

    # Verifica ausência de espaços intra-dígitos e integridade das colunas financeiras
    for table in consolidated:
        rows = table["rows"]
        if not rows or len(rows) < 2:
            continue
        header = rows[0]
        valor_indices = [
            i for i, h in enumerate(header)
            if any(kw in (h or "").upper() for kw in ["VALOR", "TOTAL", "PRECO", "PREÇO"])
        ]
        for row in rows[1:]:
            for idx in valor_indices:
                if idx < len(row):
                    cell = str(row[idx] or "").strip()
                    if cell and cell.upper() not in ["VALOR", "TOTAL", "PRECO", "PREÇO"]:
                        assert not re.search(r"\d\s+[\.,]\s*\d", cell), f"Espaço intra-dígito encontrado no valor '{cell}'"
                        assert re.match(r"^\d+(\.\d{2})?$", cell), f"Valor financeiro fora do padrão SQL: '{cell}'"
