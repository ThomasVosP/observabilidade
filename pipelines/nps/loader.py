"""
Gera os batches SQL para carga no Supabase a partir dos payloads JSON do dry-run.

Uso:
  python3 -m pipelines.nps.loader   # imprime batches em logs/nps_sql/{NNN}.sql
"""

from __future__ import annotations
import json
from pathlib import Path

from pipelines.shared.sql_batch import gerar_upsert_sql

PAYLOAD_DIR = Path(__file__).parent.parent.parent / "logs" / "nps_payload"
SQL_DIR     = Path(__file__).parent.parent.parent / "logs" / "nps_sql"

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


def main(batch_size: int = 100):
    SQL_DIR.mkdir(parents=True, exist_ok=True)
    # Limpa SQLs antigos
    for f in SQL_DIR.glob("*.sql"):
        f.unlink()

    # ── Pesquisas ────────────────────────────────────────────────────────────
    with open(PAYLOAD_DIR / "pesquisas.json", encoding="utf-8") as f:
        pesquisas = json.load(f)

    print(f"Pesquisas: {len(pesquisas)} linhas → batches de {batch_size}")
    for i, sql in enumerate(gerar_upsert_sql(
        "raw", "pesquisas", pesquisas, PESQUISAS_COLS, pk="evento", batch_size=batch_size
    ), start=1):
        out = SQL_DIR / f"pesquisas_{i:03d}.sql"
        out.write_text(sql, encoding="utf-8")
        print(f"  ✓ {out.name} ({len(sql)//1024} KB)")

    # ── Respostas raw ────────────────────────────────────────────────────────
    with open(PAYLOAD_DIR / "respostas.json", encoding="utf-8") as f:
        respostas = json.load(f)

    print(f"\nRespostas: {len(respostas)} linhas → batches de {batch_size * 2}")
    for i, sql in enumerate(gerar_upsert_sql(
        "raw", "pesquisas_respostas_raw", respostas, RESPOSTAS_COLS,
        pk=("evento", "ordem"), batch_size=batch_size * 2,
    ), start=1):
        out = SQL_DIR / f"respostas_{i:03d}.sql"
        out.write_text(sql, encoding="utf-8")
        print(f"  ✓ {out.name} ({len(sql)//1024} KB)")

    print(f"\nSQLs gerados em: {SQL_DIR}")


if __name__ == "__main__":
    main()
