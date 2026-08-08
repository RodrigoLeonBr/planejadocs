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
  { extractTables = true, outputFormat = "markdown" } = {},
) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("extract_tables", String(extractTables));
  fd.append("output_format", outputFormat);
  return post("/convert", fd);
}
