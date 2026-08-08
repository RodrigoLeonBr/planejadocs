import { describe, expect, it } from "vitest";

import { formatDuration, tableBody, tableColumns, typeLabel } from "./format.js";

describe("formatDuration", () => {
  it("mostra travessão quando nulo", () => {
    expect(formatDuration(null)).toBe("—");
  });
  it("converte ms em segundos", () => {
    expect(formatDuration(4200)).toBe("4.2s");
  });
});

describe("typeLabel", () => {
  it("mapeia escaneado e nativo", () => {
    expect(typeLabel("scanned")).toBe("Escaneado (OCR)");
    expect(typeLabel("native")).toBe("Nativo");
  });
});

describe("tabelas", () => {
  const rows = [
    ["A", "B"],
    ["1", "2"],
    ["3", "4"],
  ];
  it("separa cabeçalho e corpo", () => {
    expect(tableColumns(rows)).toEqual(["A", "B"]);
    expect(tableBody(rows)).toEqual([
      ["1", "2"],
      ["3", "4"],
    ]);
  });
  it("lida com vazio e uma linha só", () => {
    expect(tableColumns([])).toEqual([]);
    expect(tableBody([["só cabeçalho"]])).toEqual([]);
  });
});
