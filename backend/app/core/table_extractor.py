"""Extração de tabelas com pdfplumber e serialização JSON/CSV/Excel."""
import csv
import io
import json

import pdfplumber


def extract_tables(path: str) -> list[dict]:
    """Extrai todas as tabelas do PDF. Lista vazia se não houver tabela.

    Cada item: {"page": int (1-based), "table_index": int, "rows": list[list]}.
    """
    result: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            for j, table in enumerate(page.extract_tables()):
                if table:
                    result.append({"page": i + 1, "table_index": j, "rows": table})
    return result


def tables_to_json(tables: list[dict]) -> str:
    return json.dumps(tables, ensure_ascii=False, indent=2)


def tables_to_csv(tables: list[dict]) -> str:
    """Concatena as tabelas em texto CSV (tabelas separadas por linha em branco)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for t in tables:
        writer.writerows(t["rows"])
        writer.writerow([])
    return buf.getvalue()


def _write_excel(tables: list[dict], target) -> None:
    """Escreve as tabelas em `target` (caminho ou buffer). 1 planilha por tabela."""
    import pandas as pd

    with pd.ExcelWriter(target, engine="openpyxl") as writer:
        for i, t in enumerate(tables):
            rows = t["rows"]
            if not rows:
                continue
            df = pd.DataFrame(rows[1:], columns=rows[0])
            df.to_excel(writer, sheet_name=f"tabela_{i + 1}", index=False)


def save_excel(tables: list[dict], out_path: str) -> None:
    """Salva as tabelas em .xlsx, uma planilha por tabela (1ª linha = cabeçalho)."""
    _write_excel(tables, out_path)


def tables_to_excel_bytes(tables: list[dict]) -> bytes:
    """Serializa as tabelas em .xlsx e retorna os bytes (sem tocar o disco)."""
    buf = io.BytesIO()
    _write_excel(tables, buf)
    return buf.getvalue()
