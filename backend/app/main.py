"""FastAPI app - implementa o contrato specs/openapi.yaml."""
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from .core.output import build_convert_response
from .core.storage import (
    list_extractions,
    list_themes,
    read_extraction,
    save_extraction,
    slug_theme,
)
from .core.table_extractor import (
    extract_tables,
    tables_to_csv,
    tables_to_excel_bytes,
    tables_to_json,
)

_DOWNLOAD_FORMATS = {
    "json": ("application/json", "tables.json", lambda t: tables_to_json(t).encode()),
    "csv": ("text/csv; charset=utf-8", "tables.csv", lambda t: tables_to_csv(t).encode()),
    "excel": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "tables.xlsx",
        tables_to_excel_bytes,
    ),
}
from .errors import PDF2MDError, file_too_large
from .schemas import (
    ConvertResponse,
    ErrorResponse,
    ExtractionContent,
    ExtractionList,
    HealthResponse,
    TablesResponse,
    ThemesResponse,
)

VERSION = "0.1.0"
MAX_FILE_SIZE = int(os.getenv("PDF2MD_MAX_FILE_SIZE_MB", "50")) * 1024 * 1024
OUTPUT_ROOT = os.getenv("PDF2MD_OUTPUT_DIR", "./output")

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
    tema: str | None = Form(None),
):
    """Converte um PDF para Markdown. Não-PDF -> PDF2MD_005, >50MB -> PDF2MD_002.

    Se `tema` for informado, persiste a extração em <PDF2MD_OUTPUT_DIR>/<tema>/.
    """
    path = _save_temp(await file.read(), file.filename)
    try:
        result = build_convert_response(path, extract_tables)
    finally:
        os.remove(path)

    if tema and tema.strip():
        result["output"] = save_extraction(
            OUTPUT_ROOT,
            tema,
            file.filename or "documento.pdf",
            result["markdown"],
            result["tables"] or [],
        )
    return ConvertResponse(**result)


@app.get("/themes", response_model=ThemesResponse)
async def get_themes():
    """Lista os temas já criados (pastas de extração)."""
    return ThemesResponse(themes=list_themes(OUTPUT_ROOT))


@app.get("/themes/{tema}", response_model=ExtractionList)
async def get_extractions(tema: str):
    """Lista as extrações salvas de um tema."""
    return ExtractionList(
        tema=slug_theme(tema), extractions=list_extractions(OUTPUT_ROOT, tema)
    )


@app.get("/themes/{tema}/{name}", response_model=ExtractionContent)
async def get_extraction(tema: str, name: str):
    """Lê uma extração salva (markdown + tabelas)."""
    data = read_extraction(OUTPUT_ROOT, tema, name)
    if data is None:
        raise HTTPException(status_code=404, detail="Extração não encontrada.")
    return ExtractionContent(name=name, markdown=data["markdown"], tables=data["tables"])


@app.get("/themes/{tema}/{name}/download")
async def download_tables(tema: str, name: str, format: str = "json"):
    """Baixa as tabelas de uma extração em JSON, CSV ou Excel."""
    fmt = _DOWNLOAD_FORMATS.get(format)
    if fmt is None:
        raise HTTPException(status_code=400, detail="Formato inválido.")
    data = read_extraction(OUTPUT_ROOT, tema, name)
    if data is None or not data["tables"]:
        raise HTTPException(status_code=404, detail="Sem tabelas para download.")
    media, ext, serialize = fmt
    stem = Path(name).name
    return Response(
        content=serialize(data["tables"]),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{stem}.{ext}"'},
    )


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
