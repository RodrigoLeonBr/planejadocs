"""Servidor MCP - expõe o pipeline PlanejaDocs pro Claude Code.

Reusa o core direto (sem HTTP). Ferramentas: converter PDF gravando o
Markdown na pasta de qualquer projeto, e ler/listar o que já foi extraído.

Registro:
    claude mcp add planejadocs -- python E:\\xampp\\htdocs\\planejadocs\\backend\\mcp_server.py

Requer `pip install -e ".[mcp]"` (traz o fastmcp).
"""
from fastmcp import FastMCP

from app.core.output import build_convert_response
from app.core.storage import (
    list_extractions,
    list_themes,
    read_extraction,
    save_extraction,
)

mcp = FastMCP("planejadocs")


@mcp.tool()
def pdf_to_md(pdf_path: str, dest_dir: str, tema: str = "outros") -> dict:
    """Converte um PDF para Markdown + tabelas e grava em dest_dir/<tema>/.

    Retorna os caminhos gravados (.md e, se houver tabelas, .tables.json/.csv).
    """
    r = build_convert_response(pdf_path, extract_tables_flag=True)
    return save_extraction(dest_dir, tema, pdf_path, r["markdown"], r["tables"] or [])


@mcp.tool()
def list_themes_in(dest_dir: str) -> list[str]:
    """Lista os temas (subpastas) já existentes em dest_dir."""
    return list_themes(dest_dir)


@mcp.tool()
def list_extractions_in(dest_dir: str, tema: str) -> list[str]:
    """Lista os nomes das extrações salvas de um tema em dest_dir."""
    return list_extractions(dest_dir, tema)


@mcp.tool()
def read_md(dest_dir: str, tema: str, name: str) -> dict | None:
    """Lê uma extração salva (markdown + tabelas). None se não existir."""
    return read_extraction(dest_dir, tema, name)


if __name__ == "__main__":
    mcp.run()
