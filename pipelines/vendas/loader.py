"""Gera batches SQL para Vendas a partir do payload do dry-run."""

from __future__ import annotations
import json
from pathlib import Path

from pipelines.shared.sql_batch import gerar_upsert_sql

PAYLOAD_DIR = Path(__file__).parent.parent.parent / "logs" / "vendas_payload"
SQL_DIR     = Path(__file__).parent.parent.parent / "logs" / "vendas_sql"

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


def main(batch_size: int = 100):
    SQL_DIR.mkdir(parents=True, exist_ok=True)
    for f in SQL_DIR.glob("*.sql"):
        f.unlink()

    with open(PAYLOAD_DIR / "notas_fiscais.json", encoding="utf-8") as f:
        nfs = json.load(f)

    print(f"NFs: {len(nfs)} linhas → batches de {batch_size}")
    for i, sql in enumerate(gerar_upsert_sql(
        "raw", "notas_fiscais", nfs, NF_COLS, pk="nf_numero", batch_size=batch_size,
    ), start=1):
        out = SQL_DIR / f"nfs_{i:03d}.sql"
        out.write_text(sql, encoding="utf-8")
        print(f"  ✓ {out.name} ({len(sql)//1024} KB)")

    print(f"\nSQLs em: {SQL_DIR}")


if __name__ == "__main__":
    main()
