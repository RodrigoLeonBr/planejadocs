"""Persistência das extrações organizada por tema (spec convert.md).

Estrutura: <output_root>/<tema>/<arquivo>.md (+ .tables.json/.tables.csv).
O nome da pasta é normalizado para evitar temas duplicados.
"""
import json
import re
import unicodedata
from pathlib import Path

from .table_extractor import tables_to_csv


def slug_theme(tema: str) -> str:
    """Normaliza o tema em nome de pasta: minúsculas, sem acento, espaços->_."""
    s = unicodedata.normalize("NFKD", tema).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s or "outros"


def list_themes(output_root: str) -> list[str]:
    root = Path(output_root)
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def save_extraction(
    output_root: str,
    tema: str,
    source_name: str,
    markdown: str,
    tables: list[dict],
) -> dict:
    """Grava markdown (e tabelas, se houver) na pasta do tema. Retorna os caminhos."""
    slug = slug_theme(tema)
    folder = Path(output_root) / slug
    folder.mkdir(parents=True, exist_ok=True)
    stem = Path(source_name).stem

    md_path = folder / f"{stem}.md"
    md_path.write_text(markdown, encoding="utf-8")
    out = {"tema": slug, "dir": str(folder), "markdown": str(md_path)}

    if tables:
        json_path = folder / f"{stem}.tables.json"
        json_path.write_text(
            json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        csv_path = folder / f"{stem}.tables.csv"
        csv_path.write_text(tables_to_csv(tables), encoding="utf-8")
        out["tables_json"] = str(json_path)
        out["tables_csv"] = str(csv_path)

    return out
