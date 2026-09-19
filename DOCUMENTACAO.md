# PlanejaDocs — Documentação Central e Guia Operacional

> **Nota:** Este arquivo é a fonte única de consulta rápida e documentação operacional do projeto. Qualquer nova alteração arquitetural, dependência ou procedimento deve ser atualizada aqui.

---

## 1. Visão Geral

O **PlanejaDocs** é uma solução para conversão de documentos PDF da Secretaria Municipal de Saúde (SMS) em **Markdown estruturado** e dados tabulares (**JSON, CSV e Excel**). Ele é desenhado para alimentar sistemas internos, bases de conhecimento (Obsidian) e modelos de IA generativa com texto limpo e tabelas com alta fidelidade.

- **Metodologia:** *Spec-Driven Development* (especificação e contratos definidos em `specs/` antes da implementação).
- **Idioma:** Toda especificação, mensagens de erro e docstrings são mantidos em **Português**.
- **Segurança de Dados:** Documentos da SMS contêm dados sensíveis; os diretórios `arquivos/` e `output/` são estritamente ignorados pelo `.gitignore`. **Nunca utilize `git add -A`**.

---

## 2. Arquitetura do Sistema

```text
┌────────────────────────────────────────────────────────┐
│               Frontend (React 18 + Vite)               │
│               http://localhost:5173                    │
│   • Upload com tema obrigatório                        │
│   • Escolha de motor de tabela (pdfplumber / pymupdf)   │
│   • Visualizador de Markdown renderizado               │
│   • Download de tabelas (JSON / CSV / Excel)           │
│   • Navegador de extrações salvas                      │
└───────────────────────────┬────────────────────────────┘
                            │ Proxy Vite (/convert, /themes, /health, /tables)
┌───────────────────────────▼────────────────────────────┐
│                Backend (FastAPI + Uvicorn)             │
│                http://localhost:8000                   │
│   • POST /convert          • POST /convert/tables      │
│   • GET  /themes           • GET  /themes/{tema}       │
│   • GET  /themes/{tema}/{name}   • GET /health         │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│               Pipeline Núcleo (Python)                 │
│                                                        │
│ 1. detector.py        -> Densidade de chars (>50/pág)  │
│                          Nativo vs Escaneado           │
│ 2. extractor.py       -> PyMuPDF4LLM (sem OCR nativo)  │
│ 3. ocr_engine.py      -> RapidOCR (CPU/ONNX) p/ escaneados
│ 4. table_extractor.py -> pdfplumber (rápido) ou        │
│                          PyMuPDF (alta fidelidade)     │
│ 5. storage.py         -> Persistência por slug do tema │
│                          em output/<tema>/             │
│ 6. output.py          -> Monta JSON unificado          │
└────────────────────────────────────────────────────────┘
```

---

## 3. Estrutura do Repositório

```text
planejadocs/
├── DOCUMENTACAO.md           # [ESTE ARQUIVO] Documentação central única
├── README.md                 # Visão geral pública do repositório
├── CLAUDE.md                 # Diretrizes de desenvolvimento para agentes de IA
├── run.ps1                   # Script único de inicialização (Backend + Frontend)
├── specs/
│   ├── convert.md            # Especificação funcional do fluxo de conversão
│   └── openapi.yaml          # Contrato OpenAPI (fonte da verdade dos endpoints)
├── backend/
│   ├── pyproject.toml        # Dependências e configurações do backend (pytest, ruff)
│   ├── app/
│   │   ├── main.py           # Aplicação FastAPI, rotas e tratamento de erros
│   │   ├── schemas.py        # Modelos Pydantic (espelho do openapi.yaml)
│   │   ├── errors.py         # Códigos padronizados (PDF2MD_001 a 005)
│   │   └── core/
│   │       ├── detector.py   # Detecção nativo vs escaneado
│   │       ├── extractor.py  # Conversão de PDF nativo para Markdown
│   │       ├── ocr_engine.py # OCR para escaneados (RapidOCR via CPU)
│   │       ├── table_extractor.py # Extração de tabelas (pdfplumber e PyMuPDF)
│   │       ├── storage.py    # Gerenciamento de pastas por tema no output/
│   │       └── output.py     # Agregação do payload de resposta
│   ├── tests/                # 69 testes automatizados (pytest)
│   └── mcp_server.py         # Servidor MCP (FastMCP) para uso direto por IA
├── frontend/
│   ├── package.json          # Dependências do React/Vite
│   ├── vite.config.js        # Configuração com proxy para a porta 8000
│   └── src/
│       ├── App.jsx           # Componente principal e views (Upload, Markdown, Tabelas, Histórico)
│       ├── api.js            # Cliente HTTP (fetch)
│       ├── api.test.js       # Testes do cliente HTTP
│       ├── format.js         # Formatadores e tratadores de dados
│       └── format.test.js    # Testes unitários de formatação
├── arquivos/                 # [GITIGNORED] Documentos PDF de entrada / testes locais
└── output/                   # [GITIGNORED] Saídas convertidas organizadas por tema
```

---

## 4. Ambiente de Execução e Particularidades

### Detalhe Crítico de Python no Windows
O ambiente possui duas instalações do Python:
1. **Python 3.12** (`C:\Users\...\Programs\Python\Python312\python.exe`):
   - É o alvo padrão do alias genérico `python`, mas **NÃO possui os pacotes do projeto instalados**.
2. **Python 3.13** (`C:\Users\...\Microsoft\WindowsApps\python3.exe`):
   - **É onde todas as bibliotecas do projeto estão instaladas** (FastAPI, Uvicorn, PyMuPDF4LLM, RapidOCR, pdfplumber, pytest, etc.).
   - Deve ser executado chamando **`python3`** (ou `uvicorn` diretamente).

### Node.js / Frontend
- Node **v22.13+** e npm **11.4+**.
- Dependências já instaladas em `frontend/node_modules`.

---

## 5. Como Iniciar o Projeto

### Opção A: Inicialização Automática (Recomendada)
Na raiz do projeto (`planejadocs/`), abra o PowerShell e execute:
Certifique-se de estar na pasta raiz do projeto no PowerShell:
```powershell
./run.ps1
cd E:\xampp\htdocs\planejadocs
.\run.ps1
```
> **Nota de Solução de Problemas:**
> - Se receber erro de *ObjectNotFound* (`O termo './run.ps1' não é reconhecido`), confirme seu diretório com `pwd` ou `Get-Location` e navegue até a raiz (`cd E:\xampp\htdocs\planejadocs`).
> - Se receber erro de política de execução (*ExecutionPolicy*), execute:
>   `powershell -ExecutionPolicy Bypass -File .\run.ps1` ou `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

*O `run.ps1` detecta automaticamente o executável `python3` com `uvicorn`, inicia o backend na porta 8000, o frontend na porta 5173, e ao pressionar `Ctrl + C` finaliza ambos os processos de forma limpa.*

### Opção B: Inicialização Manual (Dois Terminais)

**Terminal 1 — Backend:**
```powershell
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```
- API ativa em: `http://localhost:8000`
- Documentação interativa Swagger: `http://localhost:8000/docs`

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```
- Interface Web acessível em: `http://localhost:5173`

---

## 6. Como Executar Testes e Validação

### Testes do Backend (69 testes)
```powershell
cd backend
python3 -m pytest
```

### Testes do Frontend (8 testes vitest)
```powershell
cd frontend
npm run test
```

### Linter (Ruff)
```powershell
cd backend
python3 -m ruff check .
```

---

## 7. Regras de Negócio e Funcionalidades

### 1. Organização Obrigatória por Tema
- Antes de converter um PDF pela interface ou API, o usuário **deve informar um tema** (ex.: `Contratos`, `Relatórios de Gestão`, `Prestação de Contas`).
- O backend normaliza o tema para formato slug (minúsculas, remove acentos, espaços viram `_`) via `slug_theme()`.
- Os arquivos são salvos em:
  ```text
  output/<slug_tema>/
  ├── <nome_arquivo>.md
  ├── <nome_arquivo>.tables.json   # se houver tabelas
  └── <nome_arquivo>.tables.csv    # se houver tabelas
  ```
- O frontend possui preenchimento assistido com histórico dos temas já criados (`GET /themes`).

### 2. Motores de Tabela Disponíveis
- **`pdfplumber` (Padrão / Rápido):** Ótimo para a grande maioria das tabelas convencionais.
- **`pymupdf` (Alta Fidelidade):** Extrai células por bounding box (`get_textbox`) e normaliza espaçamentos. Imprescindível para planilhas com letter-spacing largo (evita que números como `38,00` virem `3 8 , 0 0`).

### 3. OCR Inteligente para Documentos Escaneados
- Documentos nativos são processados via `PyMuPDF4LLM` com `use_ocr=OCRMode.NEVER` para máxima velocidade.
- Documentos escaneados (densidade média < 50 caracteres/página) acionam automaticamente o **RapidOCR** (ONNX Runtime em CPU), sem dependência de placas de vídeo ou serviços externos.

---

## 8. Códigos de Erro Padronizados

| Código | Descrição | Status HTTP | Causa Provável |
|---|---|---|---|
| `PDF2MD_001` | Arquivo corrompido ou ilegível | 422 | PDF quebrado ou senha de proteção ativa |
| `PDF2MD_002` | Arquivo excede o tamanho limite | 413 | PDF maior que `PDF2MD_MAX_FILE_SIZE_MB` (padrão 50MB) |
| `PDF2MD_003` | Documento excede o limite de páginas | 422 | PDF com mais de `PDF2MD_MAX_PAGES` (padrão 500 páginas) |
| `PDF2MD_004` | Falha no processamento de OCR | 422 | Erro interno no motor RapidOCR ao rasterizar página |
| `PDF2MD_005` | Formato não suportado | 415 | Extensão ou MIME type diferente de `.pdf` |

---

## 9. Histórico de Alterações e Manutenção

| Data | Responsável | Descrição da Alteração |
|---|---|---|
| 18/09/2026 | Antigravity | • Correção no `run.ps1` com auto-detecção de `python3` para compatibilidade no Windows.<br>• Criação do `DOCUMENTACAO.md` como fonte única de verdade.<br>• Validação completa de 69 testes no backend e 8 no frontend. |

