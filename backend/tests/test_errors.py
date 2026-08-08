"""Testes dos códigos de erro padronizados (spec convert.md)."""
import pytest

from app.errors import (
    PDF2MDError,
    corrupt_file,
    file_too_large,
    not_a_pdf,
    ocr_failed,
    too_many_pages,
)


def test_error_carries_code_message_status():
    err = PDF2MDError("PDF2MD_999", "boom", 418, {"k": "v"})
    assert err.code == "PDF2MD_999"
    assert err.message == "boom"
    assert err.http_status == 418
    assert err.details == {"k": "v"}
    assert isinstance(err, Exception)
    assert str(err) == "boom"


@pytest.mark.parametrize(
    "factory, code, status",
    [
        (corrupt_file, "PDF2MD_001", 400),
        (file_too_large, "PDF2MD_002", 413),
        (too_many_pages, "PDF2MD_003", 400),
        (ocr_failed, "PDF2MD_004", 500),
        (not_a_pdf, "PDF2MD_005", 400),
    ],
)
def test_factories_match_spec(factory, code, status):
    err = factory()
    assert isinstance(err, PDF2MDError)
    assert err.code == code
    assert err.http_status == status
    assert err.message  # mensagem não vazia
