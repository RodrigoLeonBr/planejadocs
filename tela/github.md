repo: RodrigoLeonBr/planejadocs
branch: main
path: (frontend not yet in repo — built from scratch against specs/openapi.yaml)

## Last sync
date: 2026-08-08T21:12:46Z

### Updated in this project
- Built initial frontend (PlanejaDocs.dc.html) as a Design Component, modeled on the /convert, /convert/tables, /health contract in specs/openapi.yaml and backend/app/schemas.py.
- Applied the Nocturne design system (attached in-project) for all styling.
- Repo currently has no frontend/ directory — this is the first implementation, not a recreation of existing UI.

## Screen map
| Screen (in PlanejaDocs.dc.html) | Repo source |
|---|---|
| Upload | specs/openapi.yaml `/convert` request schema |
| Fila/histórico | schemas.py `DocumentMetadata`, `ConvertResponse` |
| Markdown gerado | schemas.py `ConvertResponse.markdown` |
| Comparar PDF ↔ MD | specs/convert.md fidelity requirement |
| Tabelas extraídas | `/convert/tables`, `TablesResponse` |
| Configurações | specs/convert.md error codes & OCR rules |
