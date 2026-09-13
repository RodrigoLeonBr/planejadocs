// Cliente HTTP da API PlanejaDocs. Erros do backend (PDF2MD_*) viram Error
// com .code preenchido para a UI exibir a mensagem padronizada.

async function post(path, formData) {
  const resp = await fetch(path, { method: "POST", body: formData });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const err = new Error(data.message || `Erro ${resp.status}`);
    err.code = data.code;
    throw err;
  }
  return data;
}

export function convertPdf(
  file,
  {
    extractTables = true,
    outputFormat = "markdown",
    tema = "",
    tableEngine = "pdfplumber",
  } = {},
) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("extract_tables", String(extractTables));
  fd.append("output_format", outputFormat);
  fd.append("table_engine", tableEngine);
  if (tema.trim()) fd.append("tema", tema.trim());
  return post("/convert", fd);
}

// Baixa as tabelas já convertidas (em memória) como .csv ou .xlsx, sem salvar.
export async function downloadTables(tables, format, filename) {
  const resp = await fetch(`/tables/download?format=${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tables }),
  });
  if (!resp.ok) throw new Error(`Erro ${resp.status}`);
  const blob = await resp.blob();
  const ext = format === "excel" ? "xlsx" : "csv";
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename || "tabelas"}.${ext}`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function getThemes() {
  const resp = await fetch("/themes");
  if (!resp.ok) return [];
  const data = await resp.json().catch(() => ({}));
  return data.themes || [];
}

export async function getExtractions(tema) {
  const resp = await fetch(`/themes/${encodeURIComponent(tema)}`);
  if (!resp.ok) return [];
  const data = await resp.json().catch(() => ({}));
  return data.extractions || [];
}

export async function getExtraction(tema, name) {
  const resp = await fetch(
    `/themes/${encodeURIComponent(tema)}/${encodeURIComponent(name)}`,
  );
  if (!resp.ok) throw new Error(`Erro ${resp.status}`);
  return resp.json();
}
