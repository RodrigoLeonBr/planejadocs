backend/
├── pyproject.toml
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + rotas
│   ├── schemas.py           # Pydantic (espelha o OpenAPI)
│   ├── errors.py            # Códigos de erro padronizados
│   └── core/
│       ├── __init__.py
│       ├── detector.py      # Nativo vs escaneado
│       ├── extractor.py     # PyMuPDF4LLM → markdown
│       ├── table_extractor.py  # pdfplumber → tabelas
│       ├── ocr_engine.py    # Marker p/ escaneados
│       └── output.py        # Monta resposta
└── tests/
    ├── conftest.py
    └── test_api.py