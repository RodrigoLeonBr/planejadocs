# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

**Implemented — MVP backend + frontend (spec-driven, TDD).** The **web-service** framing was chosen (`backend/app/`), not the `pdf2md` library variant. Phases 1–7 done: backend pipeline + FastAPI API (37 pytest) and a React/Vite frontend (5 vitest). Validated against 31 real SMS PDFs.

Layout:
- `specs/convert.md`, `specs/openapi.yaml` — source of truth (behavior, detection rules, `PDF2MD_001..005`, API contract). Spec-first: update these before changing behavior.
- `backend/` — FastAPI app (`app/main.py`, `app/schemas.py`, `app/errors.py`, `app/core/*`), tests in `backend/tests/`.
- `frontend/` — Vite + React (`src/App.jsx`, `src/api.js`, `src/format.js`), consumes the API via dev proxy.
- `arquivos/` — real SMS PDFs for local validation. **Sensitive; gitignored; never commit.** Do not `git add -A` (it swept them in once; history had to be scrubbed).
- Reference-only, not part of the app: `estruturabackend.txt`, `Projeto_Conversor_PDF.txt` (code skeletons), `tela/` (design mockup — a proprietary "Design Component" framework, not React; used only as the visual base for the real frontend).

## What this project does

Converts PDFs (management reports, contracts, work schedules) from a municipal health department (SMS) into structured Markdown + extracted tables (JSON/CSV/Excel). Documents are in **Portuguese** — keep specs, docstrings, and error messages in Portuguese to match existing code.

## Architecture

Core pipeline (`backend/app/core/`), run in order:
1. **detector.py** — `detect_document_type()`: `native` vs `scanned` by avg chars/page (threshold 50; `>50` = native). Uses `import pymupdf` (the `fitz` alias is deprecated — do not use it, it warns).
2. **extractor.py** — native → `pymupdf4llm.to_markdown(..., use_ocr=OCRMode.NEVER)`. Scanned → delegates to `ocr_engine`. Guards run in order: not-`.pdf` → `PDF2MD_005`, pages > `MAX_PAGES` → `PDF2MD_003`.
3. **table_extractor.py** — `extract_tables()` (pdfplumber) → list of `{page, table_index, rows}`; `tables_to_json` / `tables_to_csv` / `save_excel`.
4. **ocr_engine.py** — scanned via `marker-pdf` behind the `_run_marker` seam (lazy import). Any failure (dep missing or engine error) → `PDF2MD_004`. Optional dep, **not installed** by default. Current marker API (confirmed): `PdfConverter(create_model_dict())(path)` then `text_from_rendered(rendered)` → `(text, ext, images)`.
5. **output.py** — `build_convert_response()` assembles markdown + tables + metadata.

API (`app/main.py`): `/health`, `/convert`, `/convert/tables`. `PDF2MDError` → JSON `ErrorResponse` via exception handler. Uploads use `tempfile.mkstemp` (not `/tmp/…`, which breaks on the Windows host). `schemas.py` (Pydantic) mirrors `openapi.yaml` exactly.

Config via env vars: `PDF2MD_MAX_PAGES` (500), `PDF2MD_MAX_FILE_SIZE_MB` (50), `PDF2MD_WRITE_IMAGES` (false).

## Dependencies & versions (validated 2026-08-08 on Python 3.13.14 / Node 22.13)

Installed versions differ from the loose `pyproject`/`package.json` ranges — these are what's actually tested here:

| Backend | Ver | | Frontend | Ver |
|---|---|---|---|---|
| fastapi | 0.138.2 | | react / react-dom | 18.3.1 |
| uvicorn | 0.40.0 | | react-markdown | 9.1.0 |
| pydantic | 2.12.5 | | remark-gfm | 4.0.1 |
| pymupdf / pymupdf4llm | 1.28.2 | | vite | 5.4.21 |
| pdfplumber | 0.11.9 | | @vitejs/plugin-react | 4.7.0 |
| pandas | 2.2.2 | | vitest | 2.1.9 |
| openpyxl | 3.1.5 | | | |
| ruff | 0.16.2 · pytest 9.1.1 | | | |

Gotchas:
- **pymupdf4llm 1.28 ships embedded RapidOCR** (transitive: `rapidocr` 3.8.1, `onnxruntime` 1.20.1) and auto-OCRs image pages by default (`OCRMode.SELECT_KEEP_OLD`) — slow and noisy even on native PDFs. `extractor.py` forces `use_ocr=OCRMode.NEVER` to keep native = text-only. Do not remove that.
- The `>=0.0.18` pin some skeletons show is wrong; the real API is 1.28.x (`from pymupdf4llm.ocr import OCRMode`).
- **marker-pdf on CPU is ~1–5 min/page** and downloads ~1 GB of models on first run. Expected for the ~5% scanned docs; keep the OCR path lazy/optional.
- **Large native docs are slow** synchronously (e.g. 218 pages ≈ 205 s) and would exceed default HTTP client timeouts — async processing (README "pós-MVP") matters sooner than planned.
- Frontend `npm audit` flags are **dev-only** (esbuild/vite dev server); production deps = 0 vulns. Don't force `vite@8`.

## Commands

```bash
# Backend (Python 3.10+; 3.13 works)
cd backend
pip install -e ".[dev]"            # add [ocr] for marker-pdf (heavy, optional)
uvicorn app.main:app --reload      # http://localhost:8000
pytest                             # all tests
pytest tests/test_api.py::test_health   # single test
ruff check .                       # lint (B008 ignored — FastAPI File/Form idiom)

# Frontend (React + Vite)
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /convert & /health to :8000
npm run test       # vitest
npm run build
```

## Conventions

- Spec-first + TDD: write/adjust `specs/*` and the failing test before implementation; watch it fail, then make it pass. Every phase ends green + ruff clean + a conventional commit (`feat:`/`fix:`/…).
- Stage explicitly (`git add <paths>`), never `git add -A` — see `arquivos/`.
- PyMuPDF is AGPL — review licensing before any closed-source distribution.
