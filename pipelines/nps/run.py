"""
Pipeline NPS — entrypoint.

Uso:
  python3 -m pipelines.nps.run data/raw/Dados\\ Jan-Abril\\ 2026.xlsx
  python3 -m pipelines.nps.run <arquivo.xlsx> --dry-run-only   (não pede confirmação)
"""

from __future__ import annotations
import sys
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from pipelines.nps.extractor import extrair
from pipelines.nps.transformer import transformar


def _fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _fmt_pct(part: int, total: int) -> str:
    return f"{part/total*100:.1f}%" if total else "n/a"


def run(xlsx_path: Path, dry_run_only: bool = False) -> None:
    print(f"📥 Pipeline NPS — fonte: {xlsx_path.name}\n")
    t0 = time.time()

    # ── Fase 1: Extração ────────────────────────────────────────────────────
    rows = list(extrair(xlsx_path))
    por_tipo = Counter(r["__tipo__"] for r in rows)
    print(f"   Extraídas {_fmt_int(len(rows))} pesquisas:")
    for tipo, qtd in por_tipo.items():
        print(f"     • {tipo:<10s} {_fmt_int(qtd)}")

    # ── Fase 2: Transformação ───────────────────────────────────────────────
    pesquisas: list[dict] = []
    respostas: list[tuple[int, list[dict]]] = []  # (evento, lista de respostas)
    descartadas = 0
    empresas_nao_mapeadas = Counter()

    for r in rows:
        p, resps = transformar(r)
        if p is None:
            descartadas += 1
            continue
        pesquisas.append(p)
        respostas.append((p["evento"], resps))
        if not p["loja_id"] and p["empresa_syonet"]:
            empresas_nao_mapeadas[p["empresa_syonet"]] += 1

    total = len(pesquisas)
    print(f"\n🔄 Transformação:")
    if descartadas:
        print(f"   ⚠ {descartadas} linhas descartadas (Evento ausente)")

    # Status
    print(f"\n   Status:")
    for status, qtd in Counter(p["status"] for p in pesquisas).most_common():
        print(f"     • {status or '(NULO)':<12s} {_fmt_int(qtd):>7}  {_fmt_pct(qtd, total)}")

    # Marca
    print(f"\n   Marca:")
    for marca, qtd in Counter(p["marca"] for p in pesquisas).most_common():
        print(f"     • {marca or '(NULO)':<22s} {_fmt_int(qtd):>7}  {_fmt_pct(qtd, total)}")

    # Tipo
    print(f"\n   Tipo:")
    for tipo, qtd in Counter(p["tipo"] for p in pesquisas).most_common():
        print(f"     • {tipo:<12s} {_fmt_int(qtd):>7}  {_fmt_pct(qtd, total)}")

    # Lojas
    mapeadas = sum(1 for p in pesquisas if p["loja_id"])
    print(f"\n   Lojas mapeadas: {_fmt_int(mapeadas)}/{_fmt_int(total)} ({_fmt_pct(mapeadas, total)})")
    if empresas_nao_mapeadas:
        print(f"   ⚠ Empresas NÃO mapeadas ({len(empresas_nao_mapeadas)} valores únicos):")
        for empresa, qtd in empresas_nao_mapeadas.most_common():
            print(f"     • {empresa!r}  ({_fmt_int(qtd)} linhas)")

    # NPS
    com_nps = [p for p in pesquisas if p["nps_geral"] is not None]
    if com_nps:
        prom = sum(1 for p in com_nps if p["classificacao"] == "Promotor")
        neut = sum(1 for p in com_nps if p["classificacao"] == "Neutro")
        detr = sum(1 for p in com_nps if p["classificacao"] == "Detrator")
        media = sum(p["nps_geral"] for p in com_nps) / len(com_nps)
        nps_score = (prom - detr) / len(com_nps) * 100
        print(f"\n   NPS Geral (sobre {_fmt_int(len(com_nps))} pesquisas com nota):")
        print(f"     • Nota média:  {media:.1f}")
        print(f"     • NPS Score:   {nps_score:+.1f}")
        print(f"     • Promotores:  {_fmt_int(prom):>5}  {_fmt_pct(prom, len(com_nps))}")
        print(f"     • Neutros:     {_fmt_int(neut):>5}  {_fmt_pct(neut, len(com_nps))}")
        print(f"     • Detratores:  {_fmt_int(detr):>5}  {_fmt_pct(detr, len(com_nps))}")

    # Cobertura de conceitos
    print(f"\n   Cobertura de conceitos canônicos:")
    for c in ("nps_geral", "nps_processo_compra", "nps_test_drive", "nps_acessorios", "nps_entrega", "resposta_aberta"):
        cov = sum(1 for p in pesquisas if p[c] is not None)
        print(f"     • {c:<22s} {_fmt_int(cov):>7}  {_fmt_pct(cov, total)}")

    total_respostas_raw = sum(len(r) for _, r in respostas)
    print(f"\n   Respostas Q&A para gravar em raw: {_fmt_int(total_respostas_raw)}")

    elapsed = time.time() - t0
    print(f"\n   ⏱ Transformação concluída em {elapsed:.1f}s")

    if dry_run_only:
        print(f"\n[dry-run-only] Nenhum dado foi gravado.")
        return

    # ── Fase 3: Load ────────────────────────────────────────────────────────
    print(f"\n💾 Pronto para upsert no Supabase:")
    print(f"     • raw.pesquisas:              {_fmt_int(total)}")
    print(f"     • raw.pesquisas_respostas_raw: {_fmt_int(total_respostas_raw)}")
    print(f"\n   Para executar o load: rode o agente com 'confirmar upsert NPS'.")
    print(f"   Este script gera os payloads em JSON para o agente enviar via MCP.\n")

    # Serializa para o agente consumir
    out_dir = Path(__file__).parent.parent.parent / "logs" / "nps_payload"
    out_dir.mkdir(parents=True, exist_ok=True)

    pesquisas_out = out_dir / "pesquisas.json"
    respostas_out = out_dir / "respostas.json"

    # Serializa datetimes
    def _ser(o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        return str(o)

    with open(pesquisas_out, "w", encoding="utf-8") as f:
        json.dump(pesquisas, f, ensure_ascii=False, default=_ser)

    flat_respostas = []
    for evento, resps in respostas:
        for r in resps:
            flat_respostas.append({"evento": evento, **r})
    with open(respostas_out, "w", encoding="utf-8") as f:
        json.dump(flat_respostas, f, ensure_ascii=False, default=_ser)

    print(f"   ✓ {pesquisas_out.relative_to(out_dir.parent.parent)} ({_fmt_int(total)} linhas)")
    print(f"   ✓ {respostas_out.relative_to(out_dir.parent.parent)} ({_fmt_int(len(flat_respostas))} linhas)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Uso: python3 -m pipelines.nps.run <xlsx_path> [--dry-run-only]")
        sys.exit(1)
    xlsx = Path(args[0])
    dry = "--dry-run-only" in args
    run(xlsx, dry_run_only=dry)
