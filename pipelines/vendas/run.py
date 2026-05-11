"""Pipeline Vendas (Notas Fiscais) — entrypoint."""

from __future__ import annotations
import sys
import json
import time
from collections import Counter
from pathlib import Path

from pipelines.vendas.extractor import extrair
from pipelines.vendas.transformer import transformar


def _fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(part: int, total: int) -> str:
    return f"{part/total*100:.1f}%" if total else "n/a"


def run(xlsx_path: Path, dry_run_only: bool = False) -> None:
    print(f"📥 Pipeline Vendas — fonte: {xlsx_path.name}\n")
    t0 = time.time()

    # ── Extração + Transformação combinadas (volume permite single-pass) ────
    nfs: list[dict] = []
    descartadas = 0
    empresas_nao_mapeadas = Counter()
    por_periodo = Counter()
    chassis_duplicados = Counter()

    for r in extrair(xlsx_path):
        nf = transformar(r)
        if nf is None:
            descartadas += 1
            continue
        nfs.append(nf)
        por_periodo[r["__periodo__"]] += 1
        if not nf["loja_id"] and nf["nome_empresa_nf"]:
            empresas_nao_mapeadas[nf["nome_empresa_nf"]] += 1
        if nf["chassi"]:
            chassis_duplicados[nf["chassi"]] += 1

    total = len(nfs)
    print(f"   Por período:")
    for p, q in sorted(por_periodo.items()):
        print(f"     • {p}  {_fmt_int(q):>7}")
    print(f"     ────────────────")
    print(f"     • Total {_fmt_int(total):>7}")
    if descartadas:
        print(f"   ⚠ {descartadas} linhas descartadas")

    # Grupo Operação
    print(f"\n   Grupo de Operação:")
    por_op = Counter(n["grupo_operacao"] for n in nfs)
    for op, q in por_op.most_common():
        print(f"     • {op or '(NULO)':<5s} {_fmt_int(q):>7}  {_fmt_pct(q, total)}")

    # Financeiro
    fat = sum(n["faturamento"] or 0 for n in nfs)
    custo = sum(n["custo_compra"] or 0 for n in nfs)
    margem = sum(n["margem"] or 0 for n in nfs)
    print(f"\n   Financeiro (4 meses):")
    print(f"     • Faturamento total:  {_fmt_brl(fat)}")
    print(f"     • Custo total:        {_fmt_brl(custo)}")
    print(f"     • Margem bruta:       {_fmt_brl(margem)}")
    if fat:
        print(f"     • % Margem média:     {margem/fat*100:.2f}%")
        print(f"     • Ticket médio:       {_fmt_brl(fat/total)}")

    # Lojas
    mapeadas = sum(1 for n in nfs if n["loja_id"])
    print(f"\n   Lojas mapeadas: {_fmt_int(mapeadas)}/{_fmt_int(total)} ({_fmt_pct(mapeadas, total)})")
    if empresas_nao_mapeadas:
        print(f"   ⚠ Empresas NF NÃO mapeadas ({len(empresas_nao_mapeadas)} valores únicos):")
        for empresa, qtd in empresas_nao_mapeadas.most_common(50):
            print(f"     • {empresa!r}  ({_fmt_int(qtd)} NFs)")

    # NF duplicadas
    dups = sum(1 for c in chassis_duplicados.values() if c > 1)
    if dups:
        print(f"\n   ℹ Chassis aparecendo em múltiplas NFs: {dups} (esperado em VU/VD)")

    elapsed = time.time() - t0
    print(f"\n   ⏱ Transformação concluída em {elapsed:.1f}s")

    if dry_run_only:
        print(f"\n[dry-run-only] Nenhum dado gravado.")
        return

    # Serializa para o agente consumir
    out_dir = Path(__file__).parent.parent.parent / "logs" / "vendas_payload"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "notas_fiscais.json"

    def _ser(o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        return str(o)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(nfs, f, ensure_ascii=False, default=_ser)

    print(f"\n💾 Payload gerado:")
    print(f"   ✓ {out_file.relative_to(out_dir.parent.parent)} ({_fmt_int(total)} NFs)")
    print(f"\n   Para fazer o load: rode o agente com 'confirmar upsert Vendas'.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Uso: python3 -m pipelines.vendas.run <xlsx> [--dry-run-only]")
        sys.exit(1)
    xlsx = Path(args[0])
    dry = "--dry-run-only" in args
    run(xlsx, dry_run_only=dry)
