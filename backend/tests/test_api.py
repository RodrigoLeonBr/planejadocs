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


def test_convert_tables(client, table_pdf):
    resp = client.post("/convert/tables", files=_upload(table_pdf, "table.pdf"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["format"] == "json"
    assert body["tables"][0]["rows"][0] == ["Nome", "Valor"]
