"""Testes da persistência por tema (spec convert.md)."""
import json

from app.core.storage import list_themes, save_extraction, slug_theme


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
