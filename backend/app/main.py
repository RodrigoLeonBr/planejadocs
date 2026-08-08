"""FastAPI app - implementa o contrato specs/openapi.yaml."""
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

from .core.output import build_convert_response
from .core.table_extractor import extract_tables
from .errors import PDF2MDError, file_too_large
from .schemas import ConvertResponse, ErrorResponse, HealthResponse, TablesResponse

VERSION = "0.1.0"
MAX_FILE_SIZE = int(os.getenv("PDF2MD_MAX_FILE_SIZE_MB", "50")) * 1024 * 1024

app = FastAPI(
    title="PlanejaDocs API",
    version=VERSION,
    description="Conversor de PDFs da Secretaria Municipal de Saúde para Markdown.",
)


@app.exception_handler(PDF2MDError)
async def pdf2md_error_handler(request, exc: PDF2MDError):
    body = ErrorResponse(code=exc.code, message=exc.message, details=exc.details)
    return JSONResponse(status_code=exc.http_status, content=body.model_dump())


def _save_temp(content: bytes, filename: str | None) -> str:
    """Salva o upload num arquivo temporário preservando o sufixo. Retorna o caminho."""
    if len(content) > MAX_FILE_SIZE:
        raise file_too_large()
    suffix = Path(filename or "").suffix
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return path


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version=VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/convert", response_model=ConvertResponse)
async def convert_pdf(
    file: UploadFile = File(...),
    extract_tables: bool = Form(True),
    output_format: str = Form("markdown"),
):
    """Converte um PDF para Markdown. Não-PDF -> PDF2MD_005, >50MB -> PDF2MD_002."""
    path = _save_temp(await file.read(), file.filename)
    try:
        result = build_convert_response(path, extract_tables)
    finally:
        os.remove(path)
    return ConvertResponse(**result)


@app.post("/convert/tables", response_model=TablesResponse)
async def convert_tables(
    file: UploadFile = File(...),
    format: str = Form("json"),
):
    """Extrai apenas as tabelas de um PDF."""
    path = _save_temp(await file.read(), file.filename)
    try:
        tables = extract_tables(path)
    finally:
        os.remove(path)
    return TablesResponse(tables=tables, format=format, count=len(tables))
