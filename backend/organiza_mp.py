"""Organiza os PDFs de arquivos/mp em pastas por tema e converte pra .md.

Uso pontual (não faz parte do app). Temas = as 6 categorias do e-mail do MP.
Roda o pipeline do core direto e grava em output/mp/<tema>/.
"""
import sys
import time
from pathlib import Path

from app.core.output import build_convert_response
from app.core.storage import save_extraction

SRC = Path(r"E:\xampp\htdocs\planejadocs\arquivos\mp")
OUT = r"E:\xampp\htdocs\planejadocs\output\mp"

# (tema, [substrings no nome do arquivo]). Ordem importa: primeiro match vence.
RULES = [
    ("06 - Integral Nutri", ["integral_nutri"]),
    ("05 - Empresa SOUL", ["soul", "comunicado_va", "comunicado_de_alteracao"]),
    ("01 - Seguranca e Saude do Trabalho", [
        "pgr", "ltcat", "laudo", "aet_", "pcmso", "avcb", "epis"]),
    ("03 - Contratos", [
        "projeto_", "acessibilidade", "rrt_", "beneficios", "termo_aditivo"]),
    ("04 - Trabalhista e RH", [
        "holerite", "banco_de_horas", "folha_ponto", "escalas_",
        "dimensionamento", "contratados_enfermagem", "absenteismo",
        "reajustes", "manual_colaborador"]),
]


def tema_de(nome: str) -> str:
    low = nome.lower()
    for tema, subs in RULES:
        if any(s in low for s in subs):
            return tema
    return "99 - Outros"


def main():
    files = sorted(SRC.iterdir())
    pdfs = [f for f in files if f.suffix.lower() == ".pdf"]
    outros = [f for f in files if f.suffix.lower() != ".pdf"]

    print(f"{len(pdfs)} PDFs, {len(outros)} nao-PDF (pulados)\n")
    for f in outros:
        print(f"  PULADO (nao-PDF): {f.name} -> {tema_de(f.name)}")
    print()

    ok, fail = 0, 0
    for i, f in enumerate(pdfs, 1):
        tema = tema_de(f.name)
        t0 = time.time()
        try:
            r = build_convert_response(str(f), extract_tables_flag=True)
            save_extraction(OUT, tema, f.name, r["markdown"], r["tables"] or [])
            dt = time.time() - t0
            ntab = len(r["tables"] or [])
            print(f"[{i}/{len(pdfs)}] OK {dt:5.1f}s tab={ntab:<3} {tema} :: {f.name}")
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(pdfs)}] ERRO {f.name}: {type(e).__name__}: {e}")
            fail += 1

    print(f"\nFim: {ok} ok, {fail} erros. Saida: {OUT}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
