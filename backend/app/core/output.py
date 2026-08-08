"""Monta a resposta final a partir do resultado da extração."""
from .extractor import convert_to_markdown
from .table_extractor import extract_tables


def build_convert_response(path: str, extract_tables_flag: bool = True) -> dict:
    result = convert_to_markdown(path)
    tables = extract_tables(path) if extract_tables_flag else None
    return {
        "markdown": result["markdown"],
        "tables": tables,
        "metadata": result["metadata"],
    }
