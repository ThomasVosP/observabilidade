"""
Constrói logs/stores_data.json a partir do Supabase (em vez do mock).

Áreas com dados reais (queries no Supabase):
  - vendas (raw.notas_fiscais)
  - cx     (raw.pesquisas)
  - financeiro (raw.notas_fiscais)

Áreas ainda em mock (mas proporcionais ao volume real):
  - leads     (5-10x vendas, conforme conversão típica)
  - estoque   (0.8-1.5x vendas mensais)
  - pos_venda (proporcional ao faturamento)

Uso:
  python3 -m pipelines.dashboard.build_from_db
  python3 -m pipelines.dashboard.build_from_db --periodo 2026-03  # mês específico
"""

from __future__ import annotations
import argparse
import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from pipelines.shared.db_loader import get_conn

OUT = Path(__file__).parent.parent.parent / "logs" / "stores_data.json"

DEFAULT_PERIODO = "2026-04"  # último mês com dados completos

# Para gerar mock proporcional reproduzível
random.seed(42)


# ── Queries ──────────────────────────────────────────────────────────────────

def fetch_lojas(cur) -> list[dict]:
    cur.execute("""
        SELECT loja_id, nome, marca, bandeira, cidade, uf
        FROM dim.lojas
        ORDER BY marca, nome
    """)
    cols = ["id", "name", "brand", "bandeira", "city", "uf"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetch_vendas_agregado(cur, periodo_inicio, periodo_fim) -> dict:
    """Métricas agregadas de NFs por loja."""
    cur.execute("""
        SELECT
          loja_id,
          COUNT(*) FILTER (WHERE grupo_operacao='VN') AS novos,
          COUNT(*) FILTER (WHERE grupo_operacao='VU') AS seminovos,
          COUNT(*) FILTER (WHERE grupo_operacao='VD') AS venda_direta,
          COUNT(*) AS total_mes,
          SUM(faturamento)::bigint AS faturamento,
          SUM(faturamento) FILTER (WHERE grupo_operacao='VN')::bigint AS fat_novos,
          SUM(faturamento) FILTER (WHERE grupo_operacao='VU')::bigint AS fat_seminovos,
          SUM(faturamento) FILTER (WHERE grupo_operacao='VD')::bigint AS fat_vd,
          SUM(custo_compra)::bigint AS custo,
          SUM(margem)::bigint AS margem,
          AVG(dias_em_estoque)::int AS dias_estoque,
          (SUM(faturamento) / NULLIF(COUNT(*),0))::int AS ticket_medio
        FROM raw.notas_fiscais
        WHERE loja_id IS NOT NULL
          AND data_venda >= %s AND data_venda < %s
        GROUP BY loja_id
    """, [periodo_inicio, periodo_fim])
    cols = ["loja_id","novos","seminovos","venda_direta","total_mes","faturamento",
            "fat_novos","fat_seminovos","fat_vd","custo","margem","dias_estoque","ticket_medio"]
    return {row[0]: dict(zip(cols, row)) for row in cur.fetchall()}


def fetch_por_modelo(cur, periodo_inicio, periodo_fim) -> dict:
    """Top modelos por loja."""
    cur.execute("""
        SELECT loja_id, modelo, COUNT(*) AS qtd
        FROM raw.notas_fiscais
        WHERE loja_id IS NOT NULL AND modelo IS NOT NULL
          AND data_venda >= %s AND data_venda < %s
        GROUP BY loja_id, modelo
        ORDER BY loja_id, qtd DESC
    """, [periodo_inicio, periodo_fim])
    result = defaultdict(dict)
    for loja_id, modelo, qtd in cur.fetchall():
        if len(result[loja_id]) < 8:  # top 8 por loja
            result[loja_id][modelo] = qtd
    return dict(result)


def fetch_top_vendedores(cur, periodo_inicio, periodo_fim) -> dict:
    """Top 10 vendedores por loja (NFs, sem meta — não temos)."""
    cur.execute("""
        SELECT loja_id, vendedor, COUNT(*) AS vendas
        FROM raw.notas_fiscais
        WHERE loja_id IS NOT NULL AND vendedor IS NOT NULL
          AND data_venda >= %s AND data_venda < %s
        GROUP BY loja_id, vendedor
        ORDER BY loja_id, vendas DESC
    """, [periodo_inicio, periodo_fim])
    result = defaultdict(list)
    for loja_id, nome, vendas in cur.fetchall():
        if len(result[loja_id]) < 10:
            result[loja_id].append({"nome": nome, "vendas": vendas})
    return dict(result)


def fetch_cx(cur, periodo_inicio, periodo_fim) -> dict:
    """NPS e satisfação por loja."""
    cur.execute("""
        SELECT
          loja_id,
          AVG(nps_geral)::numeric(4,1) AS nps_geral,
          AVG(nps_processo_compra)::numeric(4,1) AS nps_processo,
          AVG(nps_test_drive)::numeric(4,1) AS nps_td,
          AVG(nps_entrega)::numeric(4,1) AS nps_entrega,
          COUNT(*) AS pesquisas_total,
          COUNT(*) FILTER (WHERE status='CONCLUIDO') AS respondidas,
          COUNT(*) FILTER (WHERE classificacao='Promotor') AS promotores,
          COUNT(*) FILTER (WHERE classificacao='Neutro')   AS neutros,
          COUNT(*) FILTER (WHERE classificacao='Detrator') AS detratores,
          AVG(dias_conclusao)::numeric(4,1) AS tma_dias
        FROM raw.pesquisas
        WHERE loja_id IS NOT NULL
          AND data_inclusao >= %s AND data_inclusao < %s
        GROUP BY loja_id
    """, [periodo_inicio, periodo_fim])
    cols = ["loja_id","nps_geral","nps_processo","nps_td","nps_entrega",
            "pesquisas_total","respondidas","promotores","neutros","detratores","tma_dias"]
    return {row[0]: dict(zip(cols, row)) for row in cur.fetchall()}


# ── Builders ─────────────────────────────────────────────────────────────────

def _num(v, default=0):
    """Converte Decimal/None para int/float Python serializável."""
    if v is None:
        return default
    return float(v) if isinstance(v, (float,)) else (int(v) if isinstance(v, int) else float(v))


def build_vendas(loja_id: str, v: dict | None) -> dict:
    if not v:
        # Loja sem vendas no período — estrutura vazia
        return {
            "total_mes": 0, "novos": 0, "seminovos": 0, "venda_direta": 0,
            "meta_mes": 1, "atingimento": 0.0, "ticket_medio": 0, "faturamento": 0,
            "faturamento_novos": 0, "faturamento_seminovos": 0, "faturamento_vd": 0,
            "por_modelo": {}, "vendedores": [], "ciclo_medio_dias": 0,
        }
    total = v["total_mes"] or 0
    # Meta: sem fonte real ainda. Usa volume + 10% como proxy.
    meta = max(1, int(total * 1.10))
    return {
        "total_mes": total,
        "novos": v["novos"] or 0,
        "seminovos": v["seminovos"] or 0,
        "venda_direta": v["venda_direta"] or 0,
        "meta_mes": meta,
        "atingimento": round(total / meta * 100, 1) if meta else 0.0,
        "ticket_medio": v["ticket_medio"] or 0,
        "faturamento": v["faturamento"] or 0,
        "faturamento_novos":     v["fat_novos"] or 0,
        "faturamento_seminovos": v["fat_seminovos"] or 0,
        "faturamento_vd":        v["fat_vd"] or 0,
        "por_modelo": {},        # preenchido fora
        "vendedores": [],        # preenchido fora
        "ciclo_medio_dias": v["dias_estoque"] or 0,
    }


def build_cx(loja_id: str, c: dict | None) -> dict:
    if not c:
        return {
            "nps_geral": 0, "nps_negociacao": 0, "nps_test_drive": 0, "nps_entrega": 0,
            "pesquisas_total": 0, "pesquisas_respondidas": 0, "taxa_resposta": 0,
            "promotores": 0, "neutros": 0, "detratores": 0,
            "reclamacoes_total": 0, "reclamacoes_abertas": 0, "tma_dias": 0,
        }
    total = c["pesquisas_total"] or 0
    respond = c["respondidas"] or 0
    return {
        "nps_geral":      float(c["nps_geral"] or 0) * 10,  # escala 0-100 conforme dashboard
        "nps_negociacao": float(c["nps_processo"] or 0) * 10,
        "nps_test_drive": float(c["nps_td"] or 0) * 10,
        "nps_entrega":    float(c["nps_entrega"] or 0) * 10,
        "pesquisas_total":       total,
        "pesquisas_respondidas": respond,
        "taxa_resposta": round(respond / total * 100, 1) if total else 0,
        "promotores": c["promotores"] or 0,
        "neutros":    c["neutros"] or 0,
        "detratores": c["detratores"] or 0,
        # Reclamações ainda não migradas — fica em 0 até pipeline reclamações
        "reclamacoes_total":   0,
        "reclamacoes_abertas": 0,
        "tma_dias": float(c["tma_dias"] or 0),
    }


def build_financeiro(v: dict | None) -> dict:
    if not v or not v["faturamento"]:
        return {"faturamento": 0, "meta_faturamento": 1, "custo": 0, "margem": 0, "pct_margem": 0}
    fat = v["faturamento"]
    custo = v["custo"] or 0
    margem = v["margem"] or 0
    return {
        "faturamento": fat,
        "meta_faturamento": int(fat * 1.10),         # proxy
        "custo": custo,
        "margem": margem,
        "pct_margem": round(margem / fat * 100, 1) if fat else 0,
    }


# ── Mock proporcional para áreas sem pipeline real ───────────────────────────

def mock_leads(total_vendas: int, rng: random.Random) -> dict:
    """Funil proporcional: ~7x vendas em leads, ~12% conversão final."""
    if total_vendas == 0:
        return {"total": 0, "por_canal": {}, "taxa_contato": 0, "tme_resposta_h": 0,
                "funil": {}, "serie_semanal": [0]*8}
    leads = max(10, int(total_vendas / rng.uniform(0.10, 0.16)))
    contactados  = int(leads * rng.uniform(0.70, 0.88))
    qualificados = int(contactados * rng.uniform(0.55, 0.72))
    test_drive   = int(qualificados * rng.uniform(0.45, 0.65))
    proposta     = int(test_drive * rng.uniform(0.60, 0.80))
    canais = {
        "Digital":   int(leads * 0.5),
        "Indicação": int(leads * 0.22),
        "Loja":      int(leads * 0.18),
    }
    canais["Outros"] = max(0, leads - sum(canais.values()))
    return {
        "total": leads,
        "por_canal": canais,
        "taxa_contato": round(contactados / leads * 100, 1),
        "tme_resposta_h": round(rng.uniform(1.5, 5.0), 1),
        "funil": {
            "Leads": leads, "Contactados": contactados,
            "Qualificados": qualificados, "Test Drive": test_drive,
            "Proposta": proposta, "Vendidos": total_vendas,
        },
        "serie_semanal": [max(3, int(leads / 4 * rng.gauss(1.0, 0.22))) for _ in range(8)],
    }


def mock_estoque(total_vendas: int, modelos_reais: dict, rng: random.Random) -> dict:
    """Estoque proxy: 0.8-1.5x vendas, distribuído entre modelos reais."""
    if total_vendas == 0:
        return {"total": 0, "por_modelo": {}, "dias_medio": 0, "criticos_60d": 0, "giro_mensal": 0}
    total_est = max(3, int(total_vendas * rng.uniform(0.8, 1.5)))
    por_modelo = {m: max(1, int(qtd * rng.uniform(0.6, 1.4))) for m, qtd in modelos_reais.items()}
    return {
        "total": total_est,
        "por_modelo": por_modelo,
        "dias_medio": int(rng.gauss(44, 14)),
        "criticos_60d": int(rng.uniform(0, 6)),
        "giro_mensal": round(total_vendas / max(1, total_est), 2),
    }


def mock_pos_venda(faturamento: int, rng: random.Random) -> dict:
    if faturamento == 0:
        return {"os_abertas": 0, "os_fechadas_mes": 0, "csat": 0,
                "receita_servicos": 0, "receita_pecas": 0}
    return {
        "os_abertas":      max(0, int(rng.gauss(22, 8))),
        "os_fechadas_mes": max(0, int(rng.gauss(175, 45))),
        "csat": round(max(4.0, min(10.0, rng.gauss(8.1, 0.9))), 1),
        "receita_servicos": int(faturamento * rng.gauss(0.030, 0.005)),
        "receita_pecas":    int(faturamento * rng.gauss(0.016, 0.003)),
    }


# ── Orquestrador ─────────────────────────────────────────────────────────────

def _periodo_to_intervalo(periodo: str) -> tuple:
    ano, mes = periodo.split("-")
    inicio = datetime(int(ano), int(mes), 1)
    fim = datetime(int(ano) + (1 if int(mes) == 12 else 0),
                   (int(mes) % 12) + 1, 1)
    return inicio, fim


def build(periodo: str = DEFAULT_PERIODO) -> dict:
    inicio, fim = _periodo_to_intervalo(periodo)
    print(f"📥 Lendo dados do Supabase para período {periodo} ({inicio.date()} a {fim.date()})...")

    conn = get_conn()
    cur = conn.cursor()

    lojas         = fetch_lojas(cur)
    vendas_db     = fetch_vendas_agregado(cur, inicio, fim)
    modelos_db    = fetch_por_modelo(cur, inicio, fim)
    vendedores_db = fetch_top_vendedores(cur, inicio, fim)
    cx_db         = fetch_cx(cur, inicio, fim)

    print(f"   • {len(lojas)} lojas")
    print(f"   • {sum(v['total_mes'] for v in vendas_db.values())} NFs no período")
    print(f"   • {sum(c['pesquisas_total'] for c in cx_db.values())} pesquisas no período")

    stores = []
    for loja in lojas:
        lid = loja["id"]
        rng = random.Random(hash(lid))  # reproduzível por loja

        v_real = vendas_db.get(lid)
        c_real = cx_db.get(lid)
        modelos = modelos_db.get(lid, {})
        vendedores_raw = vendedores_db.get(lid, [])

        vendas = build_vendas(lid, v_real)
        vendas["por_modelo"] = modelos
        total = vendas["total_mes"]

        # Vendedores: adicionar "meta" proxy (= avg do top vendedor + 10%)
        if vendedores_raw:
            top_meta = max(int(vendedores_raw[0]["vendas"] * 0.9), 1)
            vendas["vendedores"] = [
                {"nome": vd["nome"], "vendas": vd["vendas"], "meta": top_meta}
                for vd in vendedores_raw
            ]

        cx = build_cx(lid, c_real)
        financeiro = build_financeiro(v_real)

        store = {
            **loja,
            "nfs_4m": None,           # campo legado (mock); cálculo descontinuado
            "leads":     mock_leads(total, rng),
            "vendas":    vendas,
            "cx":        cx,
            "estoque":   mock_estoque(total, modelos, rng),
            "pos_venda": mock_pos_venda(financeiro["faturamento"], rng),
            "financeiro": financeiro,
        }
        stores.append(store)

    conn.close()

    return {
        "generated_at": datetime.now().isoformat(),
        "periodo": periodo,
        "fonte": "supabase",
        "fontes_reais": ["vendas", "cx", "financeiro"],
        "fontes_mock":  ["leads", "estoque", "pos_venda"],
        "stores": stores,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--periodo", default=DEFAULT_PERIODO, help="YYYY-MM (default: 2026-04)")
    args = ap.parse_args()

    payload = build(args.periodo)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    total_v = sum(s["vendas"]["total_mes"] for s in payload["stores"])
    total_f = sum(s["financeiro"]["faturamento"] for s in payload["stores"])
    total_p = sum(s["cx"]["pesquisas_total"] for s in payload["stores"])

    print(f"\n💾 {OUT}")
    print(f"   Lojas:         {len(payload['stores'])}")
    print(f"   Vendas (mês):  {total_v:,}".replace(",", "."))
    print(f"   Faturamento:   R$ {total_f:,.0f}".replace(",", "."))
    print(f"   Pesquisas:     {total_p:,}".replace(",", "."))


if __name__ == "__main__":
    main()
