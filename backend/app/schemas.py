"""Schemas Pydantic - espelham o contrato specs/openapi.yaml."""
from typing import Any, Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    timestamp: str


class DocumentMetadata(BaseModel):
    source: str
    type: Literal["native", "scanned"]
    pages: int
    duration_ms: int | None = None
    ocr: str | None = None


class SavedOutput(BaseModel):
    tema: str
    dir: str
    markdown: str
    tables_json: str | None = None
    tables_csv: str | None = None


class ConvertResponse(BaseModel):
    markdown: str
    tables: list[dict[str, Any]] | None = None
    metadata: DocumentMetadata
    output: SavedOutput | None = None


class ThemesResponse(BaseModel):
    themes: list[str]


class TablesResponse(BaseModel):
    tables: list[dict[str, Any]]
    format: Literal["json", "csv", "excel"]
    count: int


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
