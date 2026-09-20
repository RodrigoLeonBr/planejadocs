"""Extração de tabelas com pdfplumber e serialização JSON/CSV/Excel."""
import csv
import io
import json
import re

import pdfplumber


def _normalize_cell(text: str | None) -> str:
    """Colapsa runs de espaço/quebra em um único espaço e apara as bordas."""
    return " ".join((text or "").split())


def parse_financial_value(val_str: str | None) -> str:
    """Extrai valor numérico financeiro com 2 casas decimais e separador ponto (ex: '38.00').

    Remove prefixos monetários (R$, $), espaços entre dígitos ('3 8 , 0 0' -> 38.00)
    e normaliza separadores decimais e de milhares. Retorna '' se nulo ou inválido.
    """
    if val_str is None:
        return ""
    s = str(val_str).strip()
    if not s:
        return ""

    # Remove prefixo monetário
    s = re.sub(r"^[R$r$\s]+", "", s).strip()
    s = re.sub(r"[R$r$]+", "", s).strip()
    # Elimina espaços entre dígitos ou pontuação (ex: '3 8 , 0 0' -> '38,00', '1 . 1 0 0' -> '1.100')
    s = re.sub(r"(?<=[0-9.,])\s+(?=[0-9.,])", "", s).strip()
    if not s:
        return ""

    # Caso com vírgula decimal brasileira: '1.100,00' ou '38,00' ou '3 1 3 ,44'
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s:
        parts = s.split(".")
        if len(parts) > 2:
            s = "".join(parts[:-1]) + "." + parts[-1]

    # Remove quaisquer caracteres restantes estranhos
    s = re.sub(r"[^\d.-]", "", s)
    if not s or s == "-" or s == ".":
        return ""

    try:
        fval = float(s)
        return f"{fval:.2f}"
    except ValueError:
        return ""


def clean_table_financial_values(rows: list[list[str]]) -> list[list[str]]:
    """Identifica colunas de valores monetários e padroniza seus valores com 2 casas decimais."""
    if not rows or len(rows) < 2:
        return rows

    header = rows[0]
    financial_keywords = {"VALOR", "TOTAL", "PREÇO", "PRECO", "CUSTO", "TETO", "REPASSE", "UNITÁRIO", "UNITARIO"}
    financial_col_indices = set()

    for idx, col_name in enumerate(header):
        normalized_name = (col_name or "").upper().strip()
        if any(kw in normalized_name for kw in financial_keywords):
            financial_col_indices.add(idx)

    if not financial_col_indices:
        for idx in range(len(header)):
            matches = 0
            non_empty = 0
            for r in rows[1:]:
                if idx < len(r) and r[idx].strip():
                    non_empty += 1
                    cleaned = parse_financial_value(r[idx])
                    if cleaned:
                        matches += 1
            if non_empty > 0 and (matches / non_empty) >= 0.7:
                financial_col_indices.add(idx)

    if not financial_col_indices:
        return rows

    cleaned_rows = [header]
    for row in rows[1:]:
        new_row = list(row)
        for idx in financial_col_indices:
            if idx < len(new_row):
                parsed = parse_financial_value(new_row[idx])
                if parsed:
                    new_row[idx] = parsed
        cleaned_rows.append(new_row)

    return cleaned_rows



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
    """Alta fidelidade: extração de tabelas via PyMuPDF com normalização de espaçamento.

    Evita o glifo-a-glifo espaçado que o pdfplumber gera em planilhas com
    letter-spacing largo (ex.: `3 8 , 0 0` → `38,00`) e sobreposição vertical de células.
    """
    import pymupdf

    result: list[dict] = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc):
            for j, table in enumerate(page.find_tables().tables):
                rows = [
                    [_normalize_cell(cell) for cell in row]
                    for row in table.extract()
                ]
                if rows:
                    result.append({"page": i + 1, "table_index": j, "rows": rows})
    return result


def consolidate_tables(tables: list[dict]) -> list[dict]:
    """Consolida tabelas contínuas de páginas consecutivas que possuem a mesma estrutura."""
    if not tables:
        return []

    consolidated = []
    current = None

    for t in tables:
        rows = t["rows"]
        if not rows:
            continue

        col_count = len(rows[0])
        page = t["page"]

        if current is None:
            current = {
                "page": page,
                "table_index": t["table_index"],
                "header": rows[0],
                "rows": [r for r in rows],
                "last_page": page,
                "col_count": col_count,
            }
        else:
            is_consecutive = (page == current["last_page"] + 1) or (page == current["last_page"])
            same_cols = (col_count == current["col_count"])

            if is_consecutive and same_cols:
                if rows[0] == current["header"]:
                    data_rows = rows[1:]
                else:
                    data_rows = rows
                current["rows"].extend(data_rows)
                current["last_page"] = page
            else:
                consolidated.append({
                    "page": current["page"],
                    "table_index": current["table_index"],
                    "rows": current["rows"],
                })
                current = {
                    "page": page,
                    "table_index": t["table_index"],
                    "header": rows[0],
                    "rows": [r for r in rows],
                    "last_page": page,
                    "col_count": col_count,
                }

    if current is not None:
        consolidated.append({
            "page": current["page"],
            "table_index": current["table_index"],
            "rows": current["rows"],
        })

    return consolidated


def tables_to_json(tables: list[dict]) -> str:
    return json.dumps(tables, ensure_ascii=False, indent=2)


def tables_to_csv(tables: list[dict], format: str = "sql") -> str:
    """Concatena as tabelas em texto CSV (tabelas separadas por linha em branco).

    `format="sql"`: separador vírgula (,), números com ponto decimal (padrão SQL / banco de dados).
    `format="pt_br"`: separador ponto-e-vírgula (;), números com vírgula decimal (padrão Excel Brasil).
    """
    buf = io.StringIO()
    delimiter = ";" if format == "pt_br" else ","
    writer = csv.writer(buf, delimiter=delimiter)
    for t in consolidate_tables(tables):
        rows = t["rows"]
        if format == "pt_br":
            converted_rows = []
            for r in rows:
                new_row = []
                for cell in r:
                    cell_str = str(cell) if cell is not None else ""
                    if re.match(r"^-?\d+\.\d{2}$", cell_str):
                        new_row.append(cell_str.replace(".", ","))
                    else:
                        new_row.append(cell_str)
                converted_rows.append(new_row)
            writer.writerows(converted_rows)
        else:
            writer.writerows(rows)
        writer.writerow([])
    return buf.getvalue()


def _write_excel(tables: list[dict], target) -> None:
    """Escreve as tabelas em `target` (caminho ou buffer). 1 planilha por tabela.

    Células com valores decimais (ex: 38.00) são convertidas para float com máscara #,##0.00.
    """
    import pandas as pd

    with pd.ExcelWriter(target, engine="openpyxl") as writer:
        for i, t in enumerate(consolidate_tables(tables)):
            rows = t["rows"]
            if not rows:
                continue
            df = pd.DataFrame(rows[1:], columns=rows[0])
            sheet_name = f"tabela_{i + 1}"
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            ws = writer.sheets[sheet_name]
            for col_idx in range(1, len(rows[0]) + 1):
                for row_idx in range(2, len(rows) + 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    val = cell.value
                    if isinstance(val, str) and re.match(r"^-?\d+\.\d{2}$", val):
                        try:
                            cell.value = float(val)
                            cell.number_format = "#,##0.00"
                        except (ValueError, TypeError):
                            pass



def save_excel(tables: list[dict], out_path: str) -> None:
    """Salva as tabelas em .xlsx, uma planilha por tabela (1ª linha = cabeçalho)."""
    _write_excel(tables, out_path)


def tables_to_excel_bytes(tables: list[dict]) -> bytes:
    """Serializa as tabelas em .xlsx e retorna os bytes (sem tocar o disco)."""
    buf = io.BytesIO()
    _write_excel(tables, buf)
    return buf.getvalue()
