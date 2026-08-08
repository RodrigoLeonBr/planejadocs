# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

**Greenfield / spec-only.** No code exists yet — only specs and reference skeletons. Before writing code, read the specs; they are the source of truth.

Files present:
- `README.md` — project overview, stack, directory layout, setup commands (all aspirational until code exists).
- `convert.md` — spec of the conversion flow: behavior, detection rules, error codes, acceptance criteria.
- `openapi.yaml` — API contract (`/health`, `/convert`, `/convert/tables`) + Pydantic-mirroring schemas.
- `esqueleto.md` — target backend directory tree.
- `estruturabackend.txt` — full backend code skeleton (FastAPI web-service variant), pasted as reference, not yet extracted to files.
- `Projeto_Conversor_PDF.txt` — full code skeleton for `pdf2md`, the reusable library/CLI variant (content duplicated twice in the file).

Note: `README.md`/`esqueleto.md` describe a **web service** under `backend/` (package `app`, endpoints, temp-file upload). `Projeto_Conversor_PDF.txt` describes a **reusable library** under `src/pdf2md/` with library + CLI + optional API. These are two framings of the same core. Confirm which target is intended before scaffolding — do not build both.

## What this project does

PlanejaDocs converts PDFs (management reports, contracts, work schedules) from a municipal health department into structured Markdown + extracted tables (JSON/CSV/Excel). Documents are in Portuguese; keep specs, docstrings, and error messages in Portuguese to match existing files.

## Architecture (from specs)

Core pipeline, run in order:
1. **detector** — `detect_document_type()` classifies `native` vs `scanned` by average chars/page (threshold 50; `>50` = native). Uses PyMuPDF (`fitz`).
2. **extractor** — native PDFs → Markdown via `pymupdf4llm.to_markdown()`. Scanned → delegates to OCR.
3. **table_extractor** — tables via `pdfplumber.extract_tables()`.
4. **ocr_engine** — scanned PDFs via `marker-pdf` (Surya). Optional dependency; import lazily and raise the standardized error if missing. Slow on CPU (~5–10s/page); expected for ~5% of docs (work schedules).
5. **output** — assembles `markdown` + `tables` + `metadata`.

Error handling: standardized codes `PDF2MD_001`..`PDF2MD_005` (corrupt, >50MB, >500 pages, OCR failed, not-a-PDF). See `convert.md` for the mapping to HTTP status.

Config via env vars (`PDF2MD_*`): `MAX_PAGES` (500), `MAX_FILE_SIZE_MB` (50), `WRITE_IMAGES` (false by default in service), `OCR_ENGINE` (marker), `MIN_CHARS` (50).

## Workflow: spec-driven development

Rule from `README.md`: **spec first, code second.** For any feature:
1. Write/update the spec in `convert.md` (or a new `specs/<feature>.md`).
2. Update the contract in `openapi.yaml`.
3. Generate tests from the spec (TDD).
4. Implement until tests pass.

Keep `schemas.py` (Pydantic) mirroring `openapi.yaml` exactly.

## Commands (once backend scaffolded)

```bash
# Backend (Python 3.10+)
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -e ".[dev]"          # add [ocr] for marker-pdf
uvicorn app.main:app --reload    # serves on http://localhost:8000

pytest                           # all tests
pytest tests/test_api.py::test_health   # single test
ruff check .                     # lint

# Frontend (React + Vite), once created
cd frontend && npm install && npm run dev
```

## Environment notes

- Windows host (`E:\xampp\htdocs\planejadocs`), PowerShell shell. The skeleton code writes temp uploads to `/tmp/...` (POSIX) — this will fail on Windows; use `tempfile.NamedTemporaryFile`/`tempfile.gettempdir()` when extracting that code.
- PyMuPDF is AGPL — review licensing before any closed-source distribution.
