// Helpers puros de formatação/derivação para a UI.

export function formatDuration(ms) {
  if (ms == null) return "—";
  return `${(ms / 1000).toFixed(1)}s`;
}

export function typeLabel(type) {
  return type === "scanned" ? "Escaneado (OCR)" : "Nativo";
}

// Tabelas do backend vêm como {rows: [[...cabeçalho], ...linhas]}.
export function tableColumns(rows) {
  return rows && rows.length ? rows[0] : [];
}

export function tableBody(rows) {
  return rows && rows.length > 1 ? rows.slice(1) : [];
}
