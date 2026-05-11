#!/usr/bin/env python3
"""
Gera stores_data.json com KPIs realistas de todas as lojas do Grupo Servopa.
Cobre: leads, vendas, CX, estoque, pós-venda e financeiro.

Uso: python3 mocks/gerar_mock.py
"""

import json
import random
from pathlib import Path

OUT = Path(__file__).parent.parent / "logs" / "stores_data.json"

# ── Definição das lojas ───────────────────────────────────────────────────────

STORES = [
    # BYD
    {"id": "byd-ctba",   "name": "BYD Curitiba",              "brand": "BYD",             "city": "Curitiba",       "uf": "PR"},
    {"id": "byd-lda",    "name": "BYD Londrina",               "brand": "BYD",             "city": "Londrina",       "uf": "PR"},
    {"id": "byd-fpolis", "name": "BYD Florianópolis",          "brand": "BYD",             "city": "Florianópolis",  "uf": "SC"},
    {"id": "byd-poa",    "name": "BYD Porto Alegre",           "brand": "BYD",             "city": "Porto Alegre",   "uf": "RS"},
    # VW
    {"id": "vw-ctba",    "name": "VW Curitiba Centro",         "brand": "VW",              "city": "Curitiba",       "uf": "PR"},
    {"id": "vw-ctba-s",  "name": "VW Curitiba Sul",            "brand": "VW",              "city": "Curitiba",       "uf": "PR"},
    {"id": "vw-lda",     "name": "VW Londrina",                "brand": "VW",              "city": "Londrina",       "uf": "PR"},
    {"id": "vw-mge",     "name": "VW Maringá",                 "brand": "VW",              "city": "Maringá",        "uf": "PR"},
    {"id": "vw-fpolis",  "name": "VW Florianópolis",           "brand": "VW",              "city": "Florianópolis",  "uf": "SC"},
    {"id": "vw-poa",     "name": "VW Porto Alegre",            "brand": "VW",              "city": "Porto Alegre",   "uf": "RS"},
    {"id": "vw-caxias",  "name": "VW Caxias do Sul",           "brand": "VW",              "city": "Caxias do Sul",  "uf": "RS"},
    # Audi
    {"id": "audi-ctba",  "name": "Audi Curitiba",              "brand": "Audi",            "city": "Curitiba",       "uf": "PR"},
    {"id": "audi-poa",   "name": "Audi Porto Alegre",          "brand": "Audi",            "city": "Porto Alegre",   "uf": "RS"},
    {"id": "audi-fpolis","name": "Audi Florianópolis",         "brand": "Audi",            "city": "Florianópolis",  "uf": "SC"},
    # Volvo
    {"id": "volvo-ctba", "name": "Volvo Curitiba",             "brand": "Volvo",           "city": "Curitiba",       "uf": "PR"},
    {"id": "volvo-poa",  "name": "Volvo Porto Alegre",         "brand": "Volvo",           "city": "Porto Alegre",   "uf": "RS"},
    # Hyundai
    {"id": "hyu-ctba",   "name": "Hyundai Curitiba",           "brand": "Hyundai",         "city": "Curitiba",       "uf": "PR"},
    {"id": "hyu-lda",    "name": "Hyundai Londrina",           "brand": "Hyundai",         "city": "Londrina",       "uf": "PR"},
    {"id": "hyu-fpolis", "name": "Hyundai Florianópolis",      "brand": "Hyundai",         "city": "Florianópolis",  "uf": "SC"},
    {"id": "hyu-poa",    "name": "Hyundai Porto Alegre",       "brand": "Hyundai",         "city": "Porto Alegre",   "uf": "RS"},
    # Honda
    {"id": "honda-ctba", "name": "Honda Curitiba",             "brand": "Honda",           "city": "Curitiba",       "uf": "PR"},
    {"id": "honda-fpolis","name": "Honda Florianópolis",       "brand": "Honda",           "city": "Florianópolis",  "uf": "SC"},
    {"id": "honda-poa",  "name": "Honda Porto Alegre",         "brand": "Honda",           "city": "Porto Alegre",   "uf": "RS"},
    # Peugeot
    {"id": "peu-ctba",   "name": "Peugeot Curitiba",           "brand": "Peugeot",         "city": "Curitiba",       "uf": "PR"},
    {"id": "peu-poa",    "name": "Peugeot Porto Alegre",       "brand": "Peugeot",         "city": "Porto Alegre",   "uf": "RS"},
    # Citroën
    {"id": "cit-ctba",   "name": "Citroën Curitiba",           "brand": "Citroën",         "city": "Curitiba",       "uf": "PR"},
    {"id": "cit-fpolis", "name": "Citroën Florianópolis",      "brand": "Citroën",         "city": "Florianópolis",  "uf": "SC"},
    # GAC
    {"id": "gac-ctba",   "name": "GAC Curitiba",               "brand": "GAC",             "city": "Curitiba",       "uf": "PR"},
    {"id": "gac-poa",    "name": "GAC Porto Alegre",           "brand": "GAC",             "city": "Porto Alegre",   "uf": "RS"},
    # Harley-Davidson
    {"id": "hd-ctba",    "name": "Harley-Davidson Curitiba",   "brand": "Harley-Davidson", "city": "Curitiba",       "uf": "PR"},
    {"id": "hd-poa",     "name": "Harley-Davidson Porto Alegre","brand": "Harley-Davidson","city": "Porto Alegre",   "uf": "RS"},
    # Triumph
    {"id": "tri-ctba",   "name": "Triumph Curitiba",           "brand": "Triumph",         "city": "Curitiba",       "uf": "PR"},
    # Consórcio
    {"id": "cons-pr",    "name": "Consórcio Paraná",           "brand": "Consórcio",       "city": "Curitiba",       "uf": "PR"},
    {"id": "cons-sc",    "name": "Consórcio Santa Catarina",   "brand": "Consórcio",       "city": "Florianópolis",  "uf": "SC"},
    {"id": "cons-rs",    "name": "Consórcio Rio Grande do Sul","brand": "Consórcio",       "city": "Porto Alegre",   "uf": "RS"},
]

BRAND_CFG = {
    #              modelos                                        meta  ticket
    "BYD":             (["Dolphin","Atto 3","Seal","Han","Tan"],        50, 185_000),
    "VW":              (["Polo","T-Cross","Nivus","Taos","Tiguan"],     80,  95_000),
    "Audi":            (["A3","Q3","A4","Q5","Q7"],                     25, 280_000),
    "Volvo":           (["XC40","XC60","XC90","S60"],                   12, 380_000),
    "Hyundai":         (["HB20","Creta","Tucson","Santa Fe"],           70, 110_000),
    "Honda":           (["Civic","HR-V","CR-V","City"],                 65, 120_000),
    "Peugeot":         (["208","2008","3008","508"],                     40, 130_000),
    "Citroën":         (["C3","C4 Cactus","C5 Aircross"],               35, 115_000),
    "GAC":             (["GS3","GS5","GS8"],                            20, 160_000),
    "Harley-Davidson": (["Sportster","Softail","Touring","CVO"],        15,  95_000),
    "Triumph":         (["Street Triple","Bonneville","Tiger"],         10,  85_000),
    "Consórcio":       (["Auto","Moto","Imóvel"],                       30,  50_000),
}

SELLER_NAMES = [
    "Ana Lima","Bruno Costa","Carlos Silva","Daniela Rocha","Eduardo Santos",
    "Fernanda Alves","Gabriel Souza","Helena Pires","Ivan Moraes","Juliana Neves",
    "Leonardo Faria","Mariana Lopes",
]


def gen_store(store: dict, seed: int) -> dict:
    rng = random.Random(seed)
    brand = store["brand"]
    models, meta, ticket = BRAND_CFG[brand]

    perf = max(0.55, min(1.30, rng.gauss(0.95, 0.13)))

    # ── Leads ────────────────────────────────────────────────────────────────
    tx_conv = rng.uniform(0.10, 0.20)
    leads = max(20, int(meta / tx_conv * perf))
    contactados  = int(leads     * rng.uniform(0.68, 0.88))
    qualificados = int(contactados * rng.uniform(0.52, 0.72))
    test_drive   = int(qualificados * rng.uniform(0.42, 0.65))
    proposta     = int(test_drive * rng.uniform(0.55, 0.80))
    vendidos     = max(1, int(meta * perf))

    canais = {
        "Digital":   int(leads * rng.uniform(0.42, 0.58)),
        "Indicação": int(leads * rng.uniform(0.18, 0.28)),
        "Loja":      int(leads * rng.uniform(0.14, 0.22)),
    }
    canais["Outros"] = max(0, leads - sum(canais.values()))
    serie = [max(3, int(leads / 4 * rng.gauss(1.0, 0.22))) for _ in range(8)]

    # ── Vendas ───────────────────────────────────────────────────────────────
    faturamento = vendidos * ticket * rng.gauss(1.0, 0.04)

    rem = vendidos
    por_modelo = {}
    for m in models[:-1]:
        v = max(0, int(rem * rng.uniform(0.12, 0.38)))
        por_modelo[m] = v
        rem -= v
    por_modelo[models[-1]] = max(0, rem)

    n_sell = max(3, int(meta / 8))
    sellers = []
    for i in range(n_sell):
        sv = max(0, int(rng.gauss(vendidos / n_sell, vendidos / n_sell * 0.35)))
        sellers.append({"nome": SELLER_NAMES[i % len(SELLER_NAMES)], "vendas": sv, "meta": max(1, int(meta / n_sell))})

    # ── CX ───────────────────────────────────────────────────────────────────
    nps_g  = max(0, min(100, int(rng.gauss(66, 16))))
    nps_neg = max(0, min(100, nps_g + int(rng.gauss(-6, 9))))
    nps_td  = max(0, min(100, nps_g + int(rng.gauss(9, 7))))
    nps_ent = max(0, min(100, nps_g + int(rng.gauss(4, 8))))

    pesquisas = vendidos
    respond   = int(pesquisas * rng.uniform(0.58, 0.84))
    prom = int(respond * rng.uniform(0.38, 0.65))
    detr = int(respond * rng.uniform(0.04, 0.22))
    neut = max(0, respond - prom - detr)
    recl = max(0, int(rng.gauss(vendidos * 0.09, 2)))
    recl_ab = max(0, int(recl * rng.uniform(0.18, 0.55)))

    # ── Estoque ──────────────────────────────────────────────────────────────
    est_total = max(5, int(meta * rng.uniform(0.75, 1.85)))
    rem = est_total
    por_mod_est = {}
    for m in models[:-1]:
        v = max(0, int(rem * rng.uniform(0.10, 0.35)))
        por_mod_est[m] = v
        rem -= v
    por_mod_est[models[-1]] = max(0, rem)

    # ── Pós-Venda ────────────────────────────────────────────────────────────
    os_ab    = max(0, int(rng.gauss(22, 8)))
    os_fech  = max(0, int(rng.gauss(175, 45)))
    csat     = round(max(4.0, min(10.0, rng.gauss(8.1, 0.9))), 1)
    rec_serv = max(0, int(faturamento * rng.gauss(0.030, 0.005)))
    rec_pec  = max(0, int(faturamento * rng.gauss(0.016, 0.003)))

    # ── Financeiro ───────────────────────────────────────────────────────────
    custo   = faturamento * rng.gauss(0.882, 0.018)
    margem  = faturamento - custo
    pct_mg  = margem / faturamento * 100 if faturamento else 0

    return {
        "leads": {
            "total": leads,
            "por_canal": canais,
            "taxa_contato": round(contactados / leads * 100, 1),
            "tme_resposta_h": round(max(0.5, rng.gauss(3.1, 1.6)), 1),
            "funil": {
                "Leads": leads, "Contactados": contactados,
                "Qualificados": qualificados, "Test Drive": test_drive,
                "Proposta": proposta, "Vendidos": vendidos,
            },
            "serie_semanal": serie,
        },
        "vendas": {
            "total_mes": vendidos,
            "meta_mes": meta,
            "atingimento": round(vendidos / meta * 100, 1),
            "ticket_medio": int(ticket * rng.gauss(1.0, 0.05)),
            "faturamento": int(faturamento),
            "por_modelo": por_modelo,
            "vendedores": sellers,
            "ciclo_medio_dias": max(5, int(rng.gauss(21, 6))),
        },
        "cx": {
            "nps_geral": nps_g,
            "nps_negociacao": nps_neg,
            "nps_test_drive": nps_td,
            "nps_entrega": nps_ent,
            "pesquisas_total": pesquisas,
            "pesquisas_respondidas": respond,
            "taxa_resposta": round(respond / pesquisas * 100, 1) if pesquisas else 0,
            "promotores": prom,
            "neutros": neut,
            "detratores": detr,
            "reclamacoes_total": recl,
            "reclamacoes_abertas": recl_ab,
            "tma_dias": round(max(0.5, rng.gauss(3.4, 1.3)), 1),
        },
        "estoque": {
            "total": est_total,
            "por_modelo": por_mod_est,
            "dias_medio": max(5, int(rng.gauss(44, 14))),
            "criticos_60d": int(rng.uniform(0, 6)),
            "giro_mensal": round(vendidos / max(1, est_total), 2),
        },
        "pos_venda": {
            "os_abertas": os_ab,
            "os_fechadas_mes": os_fech,
            "csat": csat,
            "receita_servicos": rec_serv,
            "receita_pecas": rec_pec,
        },
        "financeiro": {
            "faturamento": int(faturamento),
            "meta_faturamento": meta * ticket,
            "custo": int(custo),
            "margem": int(margem),
            "pct_margem": round(pct_mg, 1),
        },
    }


def main():
    random.seed(42)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    stores_out = []
    for i, store in enumerate(STORES):
        data = gen_store(store, seed=i * 7 + 13)
        stores_out.append({**store, **data})

    payload = {
        "generated_at": datetime.now().isoformat(),
        "periodo": datetime.now().strftime("%Y-%m"),
        "stores": stores_out,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    total_v = sum(s["vendas"]["total_mes"] for s in stores_out)
    total_f = sum(s["financeiro"]["faturamento"] for s in stores_out)
    print(f"Gerado: {OUT}")
    print(f"  Lojas:           {len(stores_out)}")
    print(f"  Total vendas:    {total_v:,} unidades".replace(",", "."))
    print(f"  Total fat.:      R$ {total_f:,.0f}".replace(",", "."))


if __name__ == "__main__":
    main()
