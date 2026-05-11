"""
Faz o load completo de NPS + Vendas no Supabase em uma única passada.
Usa psycopg2 + execute_values (idempotente via ON CONFLICT).

Uso: python3 -m pipelines.load_all
"""

from __future__ import annotations
import json
import time
from datetime import datetime
from pathlib import Path

from pipelines.shared.db_loader import get_conn, upsert, count

ROOT = Path(__file__).parent.parent

PESQUISAS_JSON = ROOT / "logs" / "nps_payload" / "pesquisas.json"
RESPOSTAS_JSON = ROOT / "logs" / "nps_payload" / "respostas.json"
NFS_JSON       = ROOT / "logs" / "vendas_payload" / "notas_fiscais.json"

PESQUISAS_COLS = [
    "evento", "tipo", "marca", "empresa_syonet", "loja_id",
    "status", "origem", "cliente", "email", "telefone",
    "chassi", "modelo", "placa", "vendedor", "operador",
    "data_inclusao", "data_conclusao", "dias_conclusao",
    "reclamacao_evento",
    "nps_geral", "nps_processo_compra", "nps_test_drive",
    "nps_acessorios", "nps_acessorios_obs", "nps_entrega",
    "resposta_aberta", "classificacao", "arquivo_origem",
]

RESPOSTAS_COLS = ["evento", "ordem", "pergunta", "resposta", "motivo"]

NF_COLS = [
    "nf_numero", "nome_empresa_nf", "empresa_codigo", "loja_id",
    "grupo_operacao", "data_venda", "dias_em_estoque", "fluxo_operacao",
    "fisico_juridico", "cpf_cnpj", "nome_cliente", "genero",
    "bairro", "cidade", "uf", "cpf_vendedor", "vendedor",
    "chassi", "placa", "modelo", "volume", "volume_dev",
    "faturamento", "custo_compra", "vlr_bonus", "lb_def", "pct_lb_def",
    "margem", "pct_margem", "vlr_icm", "vlr_pis_cofins", "vlr_ipi",
    "val_impostos", "vlr_modalidade", "vlr_preco_publico", "vlr_desconto",
    "arquivo_origem",
]


def _to_dt(s):
    """Converte ISO string → datetime para psycopg2."""
    if s is None:
        return None
    if isinstance(s, str):
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return s


def _to_date(s):
    dt = _to_dt(s)
    return dt.date() if dt else None


def _prep_pesquisas(rows: list[dict]) -> list[dict]:
    for r in rows:
        r["data_inclusao"]  = _to_dt(r.get("data_inclusao"))
        r["data_conclusao"] = _to_dt(r.get("data_conclusao"))
    return rows


def _prep_nfs(rows: list[dict]) -> list[dict]:
    for r in rows:
        r["data_venda"] = _to_date(r.get("data_venda"))
    return rows


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def main():
    t0 = time.time()
    print("🔌 Conectando no Supabase...")
    conn = get_conn()
    print(f"   ✓ Conectado.\n")

    # ── NPS Pesquisas ────────────────────────────────────────────────────────
    print("📥 Carregando raw.pesquisas...")
    t = time.time()
    with open(PESQUISAS_JSON, encoding="utf-8") as f:
        pesquisas = _prep_pesquisas(json.load(f))
    n = upsert(conn, "raw", "pesquisas", pesquisas, PESQUISAS_COLS, pk="evento")
    print(f"   ✓ {_fmt(n)} pesquisas em {time.time()-t:.1f}s")

    # ── NPS Respostas Raw ────────────────────────────────────────────────────
    print("\n📥 Carregando raw.pesquisas_respostas_raw...")
    t = time.time()
    with open(RESPOSTAS_JSON, encoding="utf-8") as f:
        respostas = json.load(f)
    n = upsert(conn, "raw", "pesquisas_respostas_raw", respostas, RESPOSTAS_COLS,
               pk=("evento", "ordem"))
    print(f"   ✓ {_fmt(n)} respostas em {time.time()-t:.1f}s")

    # ── Vendas NFs ───────────────────────────────────────────────────────────
    print("\n📥 Carregando raw.notas_fiscais...")
    t = time.time()
    with open(NFS_JSON, encoding="utf-8") as f:
        nfs = _prep_nfs(json.load(f))
    n = upsert(conn, "raw", "notas_fiscais", nfs, NF_COLS,
               pk=("nome_empresa_nf", "nf_numero", "chassi"))
    print(f"   ✓ {_fmt(n)} NFs em {time.time()-t:.1f}s")

    # ── Validação ────────────────────────────────────────────────────────────
    print("\n🔍 Validação:")
    for schema, table in [
        ("dim", "lojas"),
        ("raw", "pesquisas"),
        ("raw", "pesquisas_respostas_raw"),
        ("raw", "notas_fiscais"),
    ]:
        c = count(conn, schema, table)
        print(f"   {schema}.{table:<26s} {_fmt(c):>10}")

    conn.close()
    print(f"\n✅ Load concluído em {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
