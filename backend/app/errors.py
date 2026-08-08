"""Códigos de erro padronizados (spec convert.md)."""


class PDF2MDError(Exception):
    """Erro base do PlanejaDocs, com código padronizado e status HTTP."""

    def __init__(
        self,
        code: str,
        message: str,
        http_status: int = 500,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details
        super().__init__(message)


def corrupt_file() -> PDF2MDError:
    return PDF2MDError("PDF2MD_001", "Arquivo corrompido ou ilegível.", 400)


def file_too_large() -> PDF2MDError:
    return PDF2MDError("PDF2MD_002", "Arquivo excede 50 MB.", 413)


def too_many_pages() -> PDF2MDError:
    return PDF2MDError("PDF2MD_003", "Arquivo excede 500 páginas.", 400)


def ocr_failed() -> PDF2MDError:
    return PDF2MDError(
        "PDF2MD_004", "OCR falhou. Verifique a dependência marker-pdf.", 500
    )


def not_a_pdf() -> PDF2MDError:
    return PDF2MDError("PDF2MD_005", "Formato não suportado. Envie um PDF.", 400)
