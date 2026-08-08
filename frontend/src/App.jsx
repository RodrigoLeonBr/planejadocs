import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { convertPdf, getThemes } from "./api.js";
import { formatDuration, tableBody, tableColumns, typeLabel } from "./format.js";

const ACCENT = "#9184d9";
const BORDER = "1px solid rgba(233,233,237,0.10)";
const CARD = "#232532";

const NAV = [
  { key: "upload", label: "Novo documento" },
  { key: "markdown", label: "Markdown gerado" },
  { key: "tables", label: "Tabelas extraídas" },
];

export default function App() {
  const [view, setView] = useState("upload");
  const [result, setResult] = useState(null); // { markdown, tables, metadata, name }
  const [extractTables, setExtractTables] = useState(true);
  const [tema, setTema] = useState("");
  const [themes, setThemes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getThemes().then(setThemes);
  }, []);

  async function handleFile(file) {
    if (!file) return;
    if (!tema.trim()) {
      setError({ message: "Informe o tema antes de importar o documento." });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await convertPdf(file, { extractTables, tema });
      setResult({ ...data, name: file.name });
      getThemes().then(setThemes); // atualiza sugestões com o tema novo
      setView("markdown");
    } catch (e) {
      setError({ code: e.code, message: e.message });
    } finally {
      setLoading(false);
    }
  }

  const hasResult = Boolean(result);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar view={view} setView={setView} hasResult={hasResult} />
      <main
        style={{
          flex: 1,
          minWidth: 0,
          padding: "22px 32px",
          display: "flex",
          flexDirection: "column",
          gap: 17,
        }}
      >
        {view === "upload" && (
          <UploadView
            extractTables={extractTables}
            setExtractTables={setExtractTables}
            tema={tema}
            setTema={setTema}
            themes={themes}
            onFile={handleFile}
            loading={loading}
            error={error}
          />
        )}
        {view === "markdown" && <MarkdownView result={result} />}
        {view === "tables" && <TablesView result={result} />}
      </main>
    </div>
  );
}

function Sidebar({ view, setView, hasResult }) {
  return (
    <aside
      style={{
        width: 240,
        flex: "none",
        display: "flex",
        flexDirection: "column",
        padding: "17px 12px",
        borderRight: BORDER,
        gap: 22,
      }}
    >
      <div>
        <div style={{ fontWeight: 500, fontSize: 18, letterSpacing: "-0.01em" }}>
          PlanejaDocs
        </div>
        <div style={{ fontSize: 11, color: "rgba(233,233,237,0.5)", marginTop: 2 }}>
          Unidade de Planejamento · SMS
        </div>
      </div>
      <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {NAV.map((n) => {
          const disabled = n.key !== "upload" && !hasResult;
          const active = view === n.key;
          return (
            <button
              key={n.key}
              disabled={disabled}
              onClick={() => setView(n.key)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 9,
                padding: "8px 9px",
                borderRadius: 8,
                border: "none",
                background: "transparent",
                textAlign: "left",
                cursor: disabled ? "not-allowed" : "pointer",
                fontSize: 14,
                color: disabled
                  ? "rgba(233,233,237,0.3)"
                  : active
                    ? ACCENT
                    : "#e9e9ed",
              }}
            >
              <span
                style={{
                  width: 5,
                  height: 5,
                  borderRadius: "50%",
                  flex: "none",
                  background: active ? ACCENT : "transparent",
                }}
              />
              {n.label}
            </button>
          );
        })}
      </nav>
      <div
        style={{
          marginTop: "auto",
          fontSize: 11,
          color: "rgba(233,233,237,0.4)",
          padding: "0 9px",
        }}
      >
        v0.1.0 · API local
      </div>
    </aside>
  );
}

function UploadView({
  extractTables,
  setExtractTables,
  tema,
  setTema,
  themes,
  onFile,
  loading,
  error,
}) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const hasTema = tema.trim().length > 0;

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    onFile(e.dataTransfer.files?.[0]);
  }

  return (
    <div>
      <h1 style={h1Style}>Novo documento</h1>
      <p style={subtitleStyle}>
        Escolha um tema e envie um PDF para converter em Markdown estruturado.
      </p>

      <div style={{ maxWidth: 560, marginBottom: 17 }}>
        <label
          htmlFor="tema"
          style={{ display: "block", fontSize: 13, marginBottom: 6 }}
        >
          Tema <span style={{ color: ACCENT }}>*</span>
          <span style={{ color: "rgba(233,233,237,0.5)", fontSize: 12 }}>
            {" "}
            — organiza a extração em pastas
          </span>
        </label>
        <input
          id="tema"
          list="temas-existentes"
          value={tema}
          onChange={(e) => setTema(e.target.value)}
          placeholder="ex: Contratos, Prestações de Conta, Relatórios…"
          style={{
            width: "100%",
            boxSizing: "border-box",
            minHeight: 38,
            padding: "8px 11px",
            fontSize: 14,
            color: "#e9e9ed",
            background: "#161826",
            border: `1px solid ${hasTema ? "rgba(233,233,237,0.16)" : ACCENT}`,
            borderRadius: 8,
          }}
        />
        <datalist id="temas-existentes">
          {themes.map((t) => (
            <option key={t} value={t} />
          ))}
        </datalist>
      </div>

      <label
        onDragOver={(e) => {
          e.preventDefault();
          if (hasTema && !loading) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        style={{
          display: "block",
          border: `1.5px dashed ${dragging ? ACCENT : "rgba(233,233,237,0.22)"}`,
          borderRadius: 14,
          padding: "40px 24px",
          textAlign: "center",
          cursor: loading ? "wait" : hasTema ? "pointer" : "not-allowed",
          background: dragging ? "rgba(145,132,217,0.05)" : "#1b1e2c",
          opacity: hasTema ? 1 : 0.55,
          maxWidth: 560,
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          disabled={loading || !hasTema}
          onChange={(e) => {
            onFile(e.target.files?.[0]);
            e.target.value = "";
          }}
          style={{ display: "none" }}
        />
        <div style={{ fontSize: 14, marginBottom: 4 }}>
          {loading
            ? "Convertendo…"
            : hasTema
              ? "Arraste um PDF aqui ou clique para escolher"
              : "Informe o tema acima para habilitar o envio"}
        </div>
        <div style={{ fontSize: 12, color: "rgba(233,233,237,0.5)" }}>
          Relatórios, contratos, prestações de conta, escalas · até 50&nbsp;MB
        </div>
      </label>

      <div
        style={{
          marginTop: 17,
          border: BORDER,
          borderRadius: 8,
          padding: 12,
          maxWidth: 560,
        }}
      >
        <div style={sectionLabelStyle}>Opções de conversão</div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span style={{ fontSize: 13 }}>Extrair tabelas (pdfplumber)</span>
          <button
            onClick={() => setExtractTables((v) => !v)}
            aria-pressed={extractTables}
            style={{
              width: 36,
              height: 20,
              borderRadius: 10,
              border: "none",
              background: extractTables ? ACCENT : "#3f424d",
              position: "relative",
              cursor: "pointer",
            }}
          >
            <span
              style={{
                width: 16,
                height: 16,
                borderRadius: "50%",
                background: "#e9e9ed",
                position: "absolute",
                top: 2,
                left: extractTables ? 18 : 2,
                transition: "left .15s",
              }}
            />
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            marginTop: 17,
            maxWidth: 560,
            border: "1px solid #4a2a2f",
            background: "#2a1e22",
            borderRadius: 8,
            padding: "12px 14px",
            fontSize: 13,
            color: "#f2c6cc",
          }}
        >
          {error.code ? `${error.code} — ` : ""}
          {error.message}
        </div>
      )}
    </div>
  );
}

function MarkdownView({ result }) {
  const meta = result.metadata;
  const items = [
    { k: "Arquivo", v: result.name || meta.source },
    { k: "Tipo", v: typeLabel(meta.type) },
    { k: "Páginas", v: String(meta.pages) },
    { k: "Tabelas extraídas", v: String(result.tables?.length ?? 0) },
    { k: "Tempo de processamento", v: formatDuration(meta.duration_ms) },
    ...(meta.ocr ? [{ k: "Motor OCR", v: meta.ocr }] : []),
    ...(result.output
      ? [
          { k: "Tema", v: result.output.tema },
          { k: "Salvo em", v: result.output.dir },
        ]
      : []),
  ];

  return (
    <div>
      <h1 style={h1Style}>Markdown gerado</h1>
      <p style={subtitleStyle}>
        Conversão fiel ao original — texto, títulos e tabelas preservados.
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 220px",
          gap: 17,
          alignItems: "start",
        }}
      >
        <div
          className="md"
          style={{
            background: CARD,
            borderRadius: 8,
            padding: "24px 28px",
            boxShadow: "0 0 0 1px #3f424d",
            maxHeight: "70vh",
            overflow: "auto",
          }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {result.markdown}
          </ReactMarkdown>
        </div>
        <div
          style={{
            background: CARD,
            borderRadius: 8,
            padding: 12,
            boxShadow: "0 0 0 1px #3f424d",
          }}
        >
          <div style={sectionLabelStyle}>Metadados</div>
          {items.map((m) => (
            <div
              key={m.k}
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 8,
                padding: "6px 0",
                borderBottom: "1px solid rgba(233,233,237,0.08)",
                fontSize: 12,
              }}
            >
              <span style={{ color: "rgba(233,233,237,0.55)" }}>{m.k}</span>
              <span style={{ textAlign: "right" }}>{m.v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function TablesView({ result }) {
  const tables = result.tables || [];
  return (
    <div>
      <h1 style={h1Style}>Tabelas extraídas</h1>
      <p style={subtitleStyle}>
        {tables.length} tabela(s) extraída(s) deste documento.
      </p>
      {tables.length === 0 && (
        <div style={{ fontSize: 13, color: "rgba(233,233,237,0.4)" }}>
          Nenhuma tabela encontrada.
        </div>
      )}
      {tables.map((t, i) => {
        const cols = tableColumns(t.rows);
        const body = tableBody(t.rows);
        return (
          <div
            key={`${t.page}-${t.table_index}-${i}`}
            style={{
              background: CARD,
              borderRadius: 8,
              boxShadow: "0 0 0 1px #3f424d",
              padding: 17,
              marginBottom: 17,
              overflow: "auto",
            }}
          >
            <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 11 }}>
              Página {t.page} · tabela {t.table_index + 1}
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr>
                  {cols.map((c, j) => (
                    <th key={j} style={thStyle}>
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {body.map((row, r) => (
                  <tr key={r} style={{ borderBottom: "1px solid rgba(233,233,237,0.08)" }}>
                    {row.map((cell, c) => (
                      <td key={c} style={{ padding: 7 }}>
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}

const h1Style = {
  fontWeight: 500,
  fontSize: 26,
  margin: "0 0 4px",
  letterSpacing: "-0.015em",
};
const subtitleStyle = {
  fontSize: 13,
  color: "rgba(233,233,237,0.55)",
  margin: "0 0 20px",
};
const sectionLabelStyle = {
  fontSize: 10,
  letterSpacing: "0.1em",
  textTransform: "uppercase",
  color: ACCENT,
  marginBottom: 9,
};
const thStyle = {
  textAlign: "left",
  fontSize: 11,
  letterSpacing: "0.06em",
  textTransform: "uppercase",
  color: "rgba(233,233,237,0.6)",
  padding: 7,
  borderBottom: "1px solid rgba(233,233,237,0.16)",
  fontWeight: 500,
};
