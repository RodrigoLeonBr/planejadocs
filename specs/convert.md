# Spec: Conversão de PDF para Markdown

## Resumo
Endpoint e biblioteca que convertem PDFs em Markdown estruturado, com detecção automática de tipo (nativo vs. escaneado), extração de tabelas e OCR para escalas escaneadas.

## Comportamento Esperado

### Entrada
- Arquivo PDF (até 50 MB, até 500 páginas).
- Opções opcionais de conversão.

### Saída
- Markdown do conteúdo.
- Tabelas extraídas (JSON/CSV/Excel).
- Metadados (tipo, páginas, tempo de processamento).

## Fluxo de Conversão

1. Recebe o PDF.
2. Detecta tipo: `native` (texto selecionável) ou `scanned` (imagem).
3. Se `native` → extrai markdown com PyMuPDF4LLM.
4. Se `scanned` → aplica OCR com Marker (Surya).
5. Extrai tabelas com pdfplumber (se solicitado).
6. Monta resultado: markdown + tabelas + metadados.

## Regras de Detecção de Tipo

| Condição | Tipo |
|---|---|
| Média de caracteres por página > 50 | `native` |
| Média de caracteres por página ≤ 50 | `scanned` |

## Regras de Negócio

- **Imagens**: descartadas por padrão (config `write_images=false`).
- **Tabelas**: extraídas por padrão; podem ser desativadas. Dois motores de extração selecionáveis por requisição via `table_engine`:
  - `pdfplumber` (padrão): rápido; comportamento histórico. Preserva o texto bruto das células (inclusive quebras internas).
  - `pymupdf` (alta fidelidade): extrai o texto de cada célula pelo seu bounding box (`page.get_textbox`) e normaliza o espaçamento (colapsa runs de espaço/quebra em um único espaço). Corrige o glifo-a-glifo espaçado que o `pdfplumber` gera em algumas planilhas (ex.: valor `3 8 , 0 0` → `38,00`; `A TIVIDADE` → `ATIVIDADE`). Recomendado quando a integridade dos valores/números importa. `table_engine` inválido → cai no padrão `pdfplumber`.
- **OCR**: usado apenas quando o PDF é escaneado (~5% dos casos — escalas de trabalho).
- **Chunking**: desligado por padrão; ativado por configuração.
- **Download direto de planilha**: `POST /tables/download?format=csv|excel` recebe as tabelas já retornadas por `/convert` (corpo `{tables:[...]}`) e devolve o arquivo (`.csv` ou `.xlsx`) sem exigir tema/persistência. Corpo sem tabelas → 404. Permite baixar a planilha na tela de resultado logo após converter.
- **Tema e persistência**: a UI sempre pede um **tema** antes de cada importação. Se `tema` for informado no `/convert`, a extração é gravada em `<PDF2MD_OUTPUT_DIR>/<tema>/` — `<arquivo>.md` mais `<arquivo>.tables.json` e `.tables.csv` quando há tabelas. Sem `tema`, nada é persistido (comportamento anterior). O nome da pasta é normalizado (minúsculas, sem acento, espaços→`_`) para evitar temas duplicados; `GET /themes` lista os temas existentes.

## Erros Padronizados

| Código | Situação |
|---|---|
| `PDF2MD_001` | Arquivo corrompido ou ilegível |
| `PDF2MD_002` | Arquivo excede 50 MB |
| `PDF2MD_003` | Arquivo excede 500 páginas |
| `PDF2MD_004` | OCR falhou (dependência `marker-pdf` ausente) |
| `PDF2MD_005` | Formato não suportado (não é PDF) |

## Critérios de Aceite

- [ ] PDF nativo → markdown fiel ao original.
- [ ] PDF escaneado → OCR retorna texto legível.
- [ ] Tabelas extraídas corretamente em JSON/CSV/Excel.
- [ ] Metadados retornados (tipo, páginas, tempo).
- [ ] Erros retornam código padronizado.
- [ ] Mesmo PDF gera o mesmo resultado (idempotência).