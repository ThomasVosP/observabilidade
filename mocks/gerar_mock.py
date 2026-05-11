#!/usr/bin/env python3
"""
Gera dados mock realistas para o dashboard de observabilidade.
Simula 30 dias de histórico de execuções de pipelines do Grupo Servopa.

Uso: python mocks/gerar_mock.py
"""

import json
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

LOGS_PATH = Path(__file__).parent.parent / "logs" / "pipeline_runs.json"

BRANDS_CONFIG = {
    "BYD":            {"pipelines": ["pesquisas", "reclamacoes", "vendas"], "volume": 350, "interval_h": 24},
    "VW":             {"pipelines": ["pesquisas", "vendas"],                "volume": 280, "interval_h": 24},
    "Audi":           {"pipelines": ["pesquisas", "vendas"],                "volume": 120, "interval_h": 24},
    "Volvo":          {"pipelines": ["pesquisas", "vendas"],                "volume": 90,  "interval_h": 48},
    "Hyundai":        {"pipelines": ["pesquisas", "vendas"],                "volume": 200, "interval_h": 24},
    "Honda":          {"pipelines": ["pesquisas", "vendas"],                "volume": 160, "interval_h": 24},
    "Peugeot":        {"pipelines": ["pesquisas", "vendas"],                "volume": 110, "interval_h": 48},
    "Citroën":        {"pipelines": ["pesquisas", "vendas"],                "volume": 95,  "interval_h": 48},
    "GAC":            {"pipelines": ["pesquisas", "vendas"],                "volume": 70,  "interval_h": 48},
    "Harley-Davidson":{"pipelines": ["pesquisas", "vendas"],                "volume": 40,  "interval_h": 48},
    "Triumph":        {"pipelines": ["pesquisas", "vendas"],                "volume": 30,  "interval_h": 48},
    "Consórcio":      {"pipelines": ["contratos", "renovacoes"],            "volume": 180, "interval_h": 24},
}

ERROR_MESSAGES = [
    "Timeout na conexão com a API Syonet (30s)",
    "HTTP 429: Rate limit excedido — aguardando 60s",
    "HTTP 500: Erro interno no servidor da fonte",
    "Credencial expirada: token inválido",
    "Falha ao conectar ao BigQuery: quota excedida",
    "Campo obrigatório ausente: 'chassi' nulo em 8 registros",
    "Erro de schema: coluna 'nps_geral' esperava INT64, recebeu STRING",
    "Conexão recusada pela API Apollo Linx",
]

WARNING_MESSAGES = [
    "3 registros rejeitados por CPF inválido",
    "Taxa de rejeição acima do limite (2.1%)",
    "Dados atrasados: última atualização da fonte há 26h",
    "Duplicatas ignoradas: 5 registros com evento já existente",
    "NPS ACESS não numérico em 12 registros — convertido para NULL",
]


def generate_run(marca: str, pipeline: str, started_at: datetime, config: dict) -> dict:
    # Inject some brands with chronic issues for realism
    error_prone = marca in ("GAC", "Triumph")
    warning_prone = marca in ("Peugeot", "Citroën", "Volvo")

    weights = [0.80, 0.12, 0.08] if error_prone else \
              [0.86, 0.10, 0.04] if warning_prone else \
              [0.92, 0.06, 0.02]

    status = random.choices(["success", "warning", "error"], weights=weights)[0]

    base_vol = config["volume"]
    jitter = random.gauss(1.0, 0.12)
    records = max(0, int(base_vol * jitter)) if status != "error" else 0

    rejected = random.randint(0, max(1, int(records * 0.02))) if status == "success" else 0
    loaded = records - rejected

    duration = max(10, int(random.gauss(130, 40)))
    finished_at = started_at + timedelta(seconds=duration)

    error_msg = None
    if status == "error":
        error_msg = random.choice(ERROR_MESSAGES)
    elif status == "warning":
        error_msg = random.choice(WARNING_MESSAGES)

    return {
        "run_id": str(uuid.uuid4()),
        "marca": marca,
        "fonte": "syonet" if pipeline in ("pesquisas", "reclamacoes") else "apollo",
        "pipeline": pipeline,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "status": status,
        "records_extracted": records,
        "records_loaded": loaded,
        "records_rejected": rejected,
        "error_message": error_msg,
        "duration_seconds": duration,
    }


def generate_all_runs(days: int = 30) -> list:
    now = datetime.now().replace(second=0, microsecond=0)
    runs = []

    for marca, config in BRANDS_CONFIG.items():
        interval_h = config["interval_h"]
        for pipeline in config["pipelines"]:
            # Simulate a daily/bi-daily schedule with some gaps
            t = now - timedelta(days=days)

            # Align to a consistent daily hour per pipeline (08:00–10:00)
            base_hour = 8 + hash(f"{marca}{pipeline}") % 3
            t = t.replace(hour=base_hour, minute=random.randint(0, 30))

            while t <= now:
                # Randomly skip a run to simulate outages (~5% chance for most, 15% for unstable)
                skip_chance = 0.15 if marca in ("GAC", "Triumph", "Harley-Davidson") else 0.05
                if random.random() > skip_chance:
                    runs.append(generate_run(marca, pipeline, t, config))
                t += timedelta(hours=interval_h)

    # Sort chronologically
    runs.sort(key=lambda r: r["started_at"])
    return runs


def main():
    random.seed(42)  # reproducible mock data
    LOGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    runs = generate_all_runs(days=30)
    with open(LOGS_PATH, "w", encoding="utf-8") as f:
        json.dump(runs, f, ensure_ascii=False, indent=2)

    # Summary
    from collections import Counter
    status_counts = Counter(r["status"] for r in runs)
    brands_seen = len(set(r["marca"] for r in runs))
    total_records = sum(r["records_loaded"] for r in runs if r["status"] == "success")

    print(f"Mock gerado em: {LOGS_PATH}")
    print(f"  Total de execuções: {len(runs)}")
    print(f"  Marcas: {brands_seen}")
    print(f"  ✓ Sucesso: {status_counts['success']}")
    print(f"  ⚠ Warning: {status_counts['warning']}")
    print(f"  ✗ Erro:    {status_counts['error']}")
    print(f"  Registros carregados (30d): {total_records:,}")


if __name__ == "__main__":
    main()
