"""Extração de tabelas com pdfplumber e serialização JSON/CSV/Excel."""
import csv
import io
import json

import pdfplumber


def _normalize_cell(text: str | None) -> str:
    """Colapsa runs de espaço/quebra em um único espaço e apara as bordas."""
    return " ".join((text or "").split())


def extract_tables(path: str, engine: str = "pdfplumber") -> list[dict]:
    """Extrai todas as tabelas do PDF. Lista vazia se não houver tabela.

    Cada item: {"page": int (1-based), "table_index": int, "rows": list[list]}.
    `engine="pymupdf"` = alta fidelidade (célula via bbox + normalização de
    espaçamento); qualquer outro valor cai no padrão `pdfplumber`.
    """
    if engine == "pymupdf":
        return _extract_pymupdf(path)
    result: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            for j, table in enumerate(page.extract_tables()):
                if table:
                    result.append({"page": i + 1, "table_index": j, "rows": table})
    return result


def _extract_pymupdf(path: str) -> list[dict]:
    """Alta fidelidade: texto de cada célula pelo bbox (`get_textbox`) + normalização.

    Evita o glifo-a-glifo espaçado que o pdfplumber gera em planilhas com
    letter-spacing largo (ex.: `3 8 , 0 0` → `38,00`).
    """
    import pymupdf

    result: list[dict] = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc):
            for j, table in enumerate(page.find_tables().tables):
                rows = [
                    [_normalize_cell(page.get_textbox(cb) if cb else "") for cb in row.cells]
                    for row in table.rows
                ]
                if rows:
                    result.append({"page": i + 1, "table_index": j, "rows": rows})
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
