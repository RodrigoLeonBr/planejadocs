"""Testes de integração da API (cobrem critérios de aceite da spec)."""
import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _upload(path, name):
    with open(path, "rb") as f:
        return {"file": (name, f.read(), "application/pdf")}


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"]


def test_convert_native(client, native_pdf):
    resp = client.post("/convert", files=_upload(native_pdf, "native.pdf"))
    assert resp.status_code == 200
    body = resp.json()
    assert "Relatório de gestão" in body["markdown"]
    assert body["metadata"]["type"] == "native"
    assert isinstance(body["tables"], list)


def test_convert_nao_pdf_retorna_005(client):
    resp = client.post(
        "/convert", files={"file": ("doc.txt", b"nao e pdf", "text/plain")}
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "PDF2MD_005"


def test_convert_arquivo_grande_retorna_002(client, native_pdf, monkeypatch):
    monkeypatch.setattr(main, "MAX_FILE_SIZE", 10)  # 10 bytes
    resp = client.post("/convert", files=_upload(native_pdf, "native.pdf"))
    assert resp.status_code == 413
    assert resp.json()["code"] == "PDF2MD_002"


def test_convert_com_tema_persiste(client, native_pdf, tmp_path, monkeypatch):
    out_root = tmp_path / "out"
    monkeypatch.setattr(main, "OUTPUT_ROOT", str(out_root))
    with open(native_pdf, "rb") as f:
        resp = client.post(
            "/convert",
            files={"file": ("relatorio.pdf", f.read(), "application/pdf")},
            data={"tema": "Relatórios de Gestão"},
        )
    assert resp.status_code == 200
    out = resp.json()["output"]
    assert out["tema"] == "relatorios_de_gestao"
    assert (out_root / "relatorios_de_gestao" / "relatorio.md").exists()


def test_convert_sem_tema_nao_persiste(client, native_pdf, tmp_path, monkeypatch):
    out_root = tmp_path / "out"
    monkeypatch.setattr(main, "OUTPUT_ROOT", str(out_root))
    with open(native_pdf, "rb") as f:
        resp = client.post(
            "/convert", files={"file": ("x.pdf", f.read(), "application/pdf")}
        )
    assert resp.json()["output"] is None
    assert not out_root.exists()


def test_themes_lista_temas(client, native_pdf, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT_ROOT", str(tmp_path / "out"))
    with open(native_pdf, "rb") as f:
        content = f.read()
    client.post(
        "/convert",
        files={"file": ("a.pdf", content, "application/pdf")},
        data={"tema": "Contratos"},
    )
    resp = client.get("/themes")
    assert resp.status_code == 200
    assert resp.json()["themes"] == ["contratos"]


def test_lista_extracoes_do_tema(client, native_pdf, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT_ROOT", str(tmp_path / "out"))
    with open(native_pdf, "rb") as f:
        content = f.read()
    client.post(
        "/convert",
        files={"file": ("relatorio.pdf", content, "application/pdf")},
        data={"tema": "Contratos"},
    )
    resp = client.get("/themes/Contratos")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tema"] == "contratos"
    assert body["extractions"] == ["relatorio"]


def test_le_extracao_salva(client, native_pdf, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT_ROOT", str(tmp_path / "out"))
    with open(native_pdf, "rb") as f:
        client.post(
            "/convert",
            files={"file": ("relatorio.pdf", f.read(), "application/pdf")},
            data={"tema": "Contratos"},
        )
    resp = client.get("/themes/Contratos/relatorio")
    assert resp.status_code == 200
    assert "Relatório de gestão" in resp.json()["markdown"]


def test_le_extracao_inexistente_404(client, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT_ROOT", str(tmp_path / "out"))
    resp = client.get("/themes/contratos/nada")
    assert resp.status_code == 404


def _convert_table_pdf_com_tema(client, table_pdf, out_root, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT_ROOT", str(out_root))
    with open(table_pdf, "rb") as f:
        client.post(
            "/convert",
            files={"file": ("tabela.pdf", f.read(), "application/pdf")},
            data={"tema": "Financeiro"},
        )


@pytest.mark.parametrize(
    "fmt, ctype",
    [
        ("json", "application/json"),
        ("csv", "text/csv"),
        (
            "excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    ],
)
def test_download_tabelas(client, table_pdf, tmp_path, monkeypatch, fmt, ctype):
    out_root = tmp_path / "out"
    _convert_table_pdf_com_tema(client, table_pdf, out_root, monkeypatch)
    resp = client.get(f"/themes/Financeiro/tabela/download?format={fmt}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(ctype)
    assert "attachment" in resp.headers["content-disposition"]
    assert len(resp.content) > 0


def test_download_sem_tabelas_404(client, native_pdf, tmp_path, monkeypatch):
    out_root = tmp_path / "out"
    monkeypatch.setattr(main, "OUTPUT_ROOT", str(out_root))
    with open(native_pdf, "rb") as f:
        client.post(
            "/convert",
            files={"file": ("semtab.pdf", f.read(), "application/pdf")},
            data={"tema": "Financeiro"},
        )
    resp = client.get("/themes/Financeiro/semtab/download?format=json")
    assert resp.status_code == 404


def test_convert_tables(client, table_pdf):
    resp = client.post("/convert/tables", files=_upload(table_pdf, "table.pdf"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["format"] == "json"
    assert body["tables"][0]["rows"][0] == ["Nome", "Valor"]
