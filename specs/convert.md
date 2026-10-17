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
  - `pymupdf` (padrão / alta fidelidade): extração nativa via `table.extract()` com normalização de espaçamento. Evita letter-spacing largo (ex.: `3 8 , 0 0` → `38.00`) e elimina sobreposições/duplicações verticais de células. Recomendado para máxima performance (~0.25s/pág) e fidelidade numérica/estrutural.
  - `pdfplumber` (legado / fallback): extrai através de vetorização de linhas. Útil em PDFs com linhas de grade bem demarcadas onde PyMuPDF não identifique a grade.
  - `table_engine` inválido → cai no padrão `pymupdf`.
- **Consolidação Multi-Páginas**: tabelas consecutivas com o mesmo número de colunas distribuídas por múltiplas páginas (comum em relatórios e tabelas de credenciamento SMS) são unificadas automaticamente em uma única estrutura, evitando fragmentação e prevenindo que a primeira linha de dados de páginas subsequentes seja descartada como falso cabeçalho.
- **Higienização Financeira e Numérica**: colunas identificadas como monetárias/valores (`VALOR`, `TOTAL`, etc.) passam por sanitização automática: remoção de prefixos (`R$`), eliminação de espaços intra-dígitos e formatação estrita com 2 casas decimais.
- **Formatos de Download e Exportação**:
  - `csv` (padrão SQL/banco): delimitador vírgula (`,`), casas decimais com ponto (`38.00`), codificação UTF-8 pura. Pronto para `LOAD DATA INFILE`, scripts Python/Pandas e Laravel.
  - `csv_ptbr` (padrão Excel Brasil): delimitador ponto-e-vírgula (`;`), casas decimais com vírgula (`38,00`), codificação UTF-8 com BOM (`utf-8-sig`).
  - `excel`: arquivo `.xlsx` com células numéricas tipadas como `float`, cabeçalho estilizado e painel congelado.
  - `json`: estrutura JSON compatível com a API.
- **OCR**: usado apenas quando o PDF é escaneado (~5% dos casos — escalas de trabalho).
- **Chunking**: desligado por padrão; ativado por configuração.
- **Download direto de planilha**: `POST /tables/download?format=csv|csv_ptbr|excel` recebe as tabelas já retornadas por `/convert` (corpo `{tables:[...]}`) e devolve o arquivo sem exigir tema/persistência. Corpo sem tabelas → 404. Permite baixar a planilha na tela de resultado logo após converter.
- **Tema e persistência**: a UI sempre pede um **tema** antes de cada importação. Se `tema` for informado no `/convert`, a extração é gravada em `<PDF2MD_OUTPUT_DIR>/<tema>/` — `<arquivo>.md` mais `<arquivo>.tables.json`, `.tables.csv`, `.tables.pt_br.csv` e `.tables.xlsx` quando há tabelas. Sem `tema`, nada é persistido. O nome da pasta é normalizado (minúsculas, sem acento, espaços→`_`); `GET /themes` lista os temas existentes.

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