import { afterEach, describe, expect, it, vi } from "vitest";

import { convertPdf, downloadTables } from "./api.js";

afterEach(() => vi.restoreAllMocks());

function mockFetch() {
  const spy = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal("fetch", spy);
  return spy;
}

function sentForm(spy) {
  return spy.mock.calls[0][1].body;
}

describe("convertPdf", () => {
  it("envia o motor de tabela escolhido", async () => {
    const spy = mockFetch();
    await convertPdf(new File(["x"], "a.pdf"), { tema: "t", tableEngine: "pymupdf" });
    expect(sentForm(spy).get("table_engine")).toBe("pymupdf");
  });

  it("usa pdfplumber por padrão", async () => {
    const spy = mockFetch();
    await convertPdf(new File(["x"], "a.pdf"), { tema: "t" });
    expect(sentForm(spy).get("table_engine")).toBe("pdfplumber");
  });
});

describe("downloadTables", () => {
  it("faz POST das tabelas com o formato e baixa .xlsx", async () => {
    const spy = vi.fn().mockResolvedValue({ ok: true, blob: async () => new Blob() });
    vi.stubGlobal("fetch", spy);
    vi.stubGlobal("URL", { createObjectURL: () => "blob:x", revokeObjectURL: () => {} });
    const anchor = { click: vi.fn() };
    vi.stubGlobal("document", { createElement: () => anchor });

    await downloadTables([{ rows: [["a"]] }], "excel", "doc");

    const [url, opts] = spy.mock.calls[0];
    expect(url).toBe("/tables/download?format=excel");
    expect(JSON.parse(opts.body).tables).toHaveLength(1);
    expect(anchor.click).toHaveBeenCalled();
  });
});
