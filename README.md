# PlanejaDocs

Conversor de documentos PDF da Secretaria Municipal de Saúde para Markdown estruturado, com extração de tabelas, OCR para escalas escaneadas e interface web. Foco principal: documentos da Unidade de Planejamento.

## Visão Geral

O PlanejaDocs converte PDFs (relatórios de gestão, contratos, prestações de conta, escalas de trabalho) em Markdown limpo e dados estruturados (JSON/CSV/Excel), prontos para uso com IA generativa, Obsidian e sistemas internos. Desenvolvido com **spec-driven development**: todo comportamento é definido por especificação antes da implementação.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.10+ · FastAPI · PyMuPDF4LLM · pdfplumber · RapidOCR (OCR, CPU) |
| Frontend | React · JavaScript · Vite |
| Dados | JSON · CSV · Excel (pandas/openpyxl) |
| Qualidade | pytest · ruff · openapi (spec-first) |

## Arquitetura
```text
┌─────────────────────────────┐
│      Frontend (React)       │
│  upload + visualização .md  │
└──────────────┬──────────────┘
               │ HTTP (REST)
┌──────────────▼──────────────┐
│        Backend (FastAPI)    │
│  /convert  /tables  /health │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│       Núcleo (Python)       │
│  detector → extractor →     │
│  tables → ocr → output      │
└─────────────────────────────┘
```

## Spec-Driven Development (como trabalhar)

Regra: **especificação primeiro, código depois.** Todo recurso segue este fluxo:

1. **Escrever a spec** em `specs/<recurso>.md` (comportamento esperado, entradas, saídas, erros).
2. **Definir o contrato OpenAPI** em `specs/openapi.yaml` (endpoints e schemas).
3. **Gerar testes** a partir da spec (TDD).
4. **Implementar** até os testes passarem.
5. **Documentar** mudanças na spec antes de codificar.

Isso permite que Cursor/Claude Code executem com contexto claro, sem adivinhar comportamento.

## Escopo do MVP

| Recurso | Status |
|---|---|
| Upload de PDF via web | MVP |
| Detecção automática nativo vs escaneado | MVP |
| Conversão PDF → Markdown | MVP |
| Extração de tabelas (JSON/CSV/Excel) | MVP |
| OCR para escalas escaneadas (~5%) | MVP |
| Visualização do Markdown no front | MVP |
| Exportação para Obsidian | Pós-MVP |
| Chunking para IA generativa | Pós-MVP |
| Autenticação e permissões | Pós-MVP |

## Estrutura de Diretórios
```text
planejadocs/
├── README.md
├── specs/
│   ├── convert.md          # Spec do fluxo de conversão
│   └── openapi.yaml        # Contrato da API
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py         # FastAPI
│   │   ├── schemas.py      # Pydantic
│   │   ├── routes.py       # Endpoints
│   │   └── core/
│   │       ├── detector.py
│   │       ├── extractor.py
│   │       ├── table_extractor.py
│   │       ├── ocr_engine.py
│   │       └── output.py
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── api.js          # Cliente HTTP
│       └── components/
└── examples/
```

## Setup

Instale as dependências uma vez:

```powershell
# Backend (Python 3.10+)
cd backend
pip install -e ".[dev]"
cd ..
# Frontend
cd frontend
npm install
cd ..
```

### Rodar tudo de uma vez (backend + frontend)

Na raiz do projeto (Windows / PowerShell):

```powershell
./run.ps1
```

Sobe o backend em `http://localhost:8000` e o frontend em `http://localhost:5173`
(o Vite faz proxy de `/convert`, `/themes`, `/health` para o backend). `Ctrl+C`
encerra os dois. Abra `http://localhost:5173` no navegador.

### Ou separadamente (dois terminais)

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload
# terminal 2
cd frontend && npm run dev
```

## Uso da API
```bash
# Converter PDF
curl -X POST http://localhost:8000/convert \
  -F "file=@relatorio_gestao.pdf"

# Resposta
{
  "markdown": "# Título...",
  "tables": [...],
  "metadata": {"type": "native", "pages": 77}
}
```

## Onde ficam as extrações

Toda importação é organizada **por tema** (a interface sempre pede o tema antes de converter). Ao informar um `tema`, a conversão é gravada em:

```text
<PDF2MD_OUTPUT_DIR>/<tema>/
├── <arquivo>.md              # markdown convertido
├── <arquivo>.tables.json     # tabelas (se houver)
└── <arquivo>.tables.csv
```

- Raiz configurável via `PDF2MD_OUTPUT_DIR` (padrão `./output`).
- O nome da pasta é normalizado (minúsculas, sem acento, espaços→`_`) para evitar temas duplicados — ex.: `Prestações de Conta` → `prestacoes_de_conta`.
- `GET /themes` lista os temas já criados; a UI usa isso para sugerir temas existentes.
- Sem `tema`, nada é persistido (o `/convert` só devolve o JSON).
- A pasta `output/` é ignorada pelo git (contém conteúdo derivado de documentos sensíveis).

## Pontos de Integração

- **API estável**: contratos Pydantic + OpenAPI versionados (semver).
- **Config por env vars**: `PDF2MD_OCR_ENGINE`, `PDF2MD_MAX_PAGES`, etc.
- **Erros padronizados**: códigos consistentes (ex: `PDF2MD_001` = arquivo corrompido).
- **Idempotência**: mesmo PDF gera o mesmo resultado (hash como chave).

## Riscos e Limitações

- Fidelidade ~90-95% em tabelas complexas (merged cells podem falhar).
- OCR sem GPU é lento (~5-10s/página) — aceitável para 5% dos casos.
- Licença AGPL do PyMuPDF: avaliar antes de distribuir como código fechado.
- Documentos > 50MB ou 500 páginas exigem processamento assíncrono (pós-MVP).

## Fluxo de Desenvolvimento Recomendado

1. Escrever `specs/convert.md` (comportamento do conversor).
2. Definir `specs/openapi.yaml` (contrato da API).
3. Implementar núcleo backend com TDD (detector → extractor → tables → ocr).
4. Expor endpoints FastAPI.
5. Construir frontend React consumindo a API.
6. Validar com documentos reais da Unidade de Planejamento.