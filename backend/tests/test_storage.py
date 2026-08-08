"""Testes da persistência por tema (spec convert.md)."""
import json

from app.core.storage import (
    list_extractions,
    list_themes,
    read_extraction,
    save_extraction,
    slug_theme,
)


def test_slug_normaliza_e_evita_duplicados():
    assert slug_theme("Contratos 2024") == "contratos_2024"
    assert slug_theme("Prestações de Conta") == "prestacoes_de_conta"
    assert slug_theme("  Contratos  ") == "contratos"  # mesmo tema que 'Contratos'
    assert slug_theme("") == "outros"
    assert slug_theme("!!!") == "outros"


def test_save_com_tabelas(tmp_path):
    tables = [{"page": 1, "table_index": 0, "rows": [["A", "B"], ["1", "2"]]}]
    out = save_extraction(str(tmp_path), "Relatórios", "loa 2024.pdf", "# LOA", tables)
    assert out["tema"] == "relatorios"
    md = tmp_path / "relatorios" / "loa 2024.md"
    assert md.read_text(encoding="utf-8") == "# LOA"
    tj = tmp_path / "relatorios" / "loa 2024.tables.json"
    assert json.loads(tj.read_text(encoding="utf-8")) == tables
    assert (tmp_path / "relatorios" / "loa 2024.tables.csv").exists()
    assert "A,B" in (tmp_path / "relatorios" / "loa 2024.tables.csv").read_text(
        encoding="utf-8"
    )


def test_save_sem_tabelas_nao_cria_arquivos_de_tabela(tmp_path):
    out = save_extraction(str(tmp_path), "Ofícios", "of.pdf", "# Ofício", [])
    assert (tmp_path / "oficios" / "of.md").exists()
    assert not (tmp_path / "oficios" / "of.tables.json").exists()
    assert "tables_json" not in out


def test_list_themes(tmp_path):
    assert list_themes(str(tmp_path)) == []
    save_extraction(str(tmp_path), "Contratos", "a.pdf", "x", [])
    save_extraction(str(tmp_path), "Escalas", "b.pdf", "y", [])
    assert list_themes(str(tmp_path)) == ["contratos", "escalas"]


def test_list_extractions(tmp_path):
    assert list_extractions(str(tmp_path), "Contratos") == []
    save_extraction(str(tmp_path), "Contratos", "b.pdf", "x", [])
    save_extraction(str(tmp_path), "Contratos", "a.pdf", "y", [])
    assert list_extractions(str(tmp_path), "Contratos") == ["a", "b"]  # ordenado


def test_read_extraction(tmp_path):
    tables = [{"page": 1, "table_index": 0, "rows": [["A"], ["1"]]}]
    save_extraction(str(tmp_path), "Relatórios", "loa 2024.pdf", "# LOA", tables)
    got = read_extraction(str(tmp_path), "Relatórios", "loa 2024")
    assert got["markdown"] == "# LOA"
    assert got["tables"] == tables


def test_read_extraction_inexistente_retorna_none(tmp_path):
    assert read_extraction(str(tmp_path), "x", "nada") is None


def test_read_extraction_bloqueia_path_traversal(tmp_path):
    save_extraction(str(tmp_path), "Contratos", "a.pdf", "seguro", [])
    save_extraction(str(tmp_path), "Outros", "secret.pdf", "sensível", [])
    # traversal p/ outro tema é neutralizado -> não escapa da pasta do tema
    assert read_extraction(str(tmp_path), "Contratos", "../outros/secret") is None
