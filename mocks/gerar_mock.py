#!/usr/bin/env python3
"""
Gera stores_data.json com KPIs realistas das 48 lojas reais do Grupo Servopa.

Base: Lojas_Grupo_Servopa.md (período 02/01/2026 a 30/04/2026, 4 meses)
Volumes mensais = total de NFs em 4 meses / 4

Cobre: leads, vendas (Novos/Seminovos/Venda Direta), CX, estoque, pós-venda, financeiro.

Uso: python3 mocks/gerar_mock.py
"""

import json
import random
from pathlib import Path
from datetime import datetime

OUT = Path(__file__).parent.parent / "logs" / "stores_data.json"


# ── Estrutura real das lojas ─────────────────────────────────────────────────
# (id, name, brand, bandeira, city, uf, nfs_4m, vn_4m, vu_4m, vd_4m)
# Volumes são em 4 meses — divide-se por 4 para média mensal

STORES_RAW = [
    # AUDI (2)
    ("plaza-alto-xv",     "PLAZA ALTO XV",            "AUDI", "Plaza",     "Curitiba","PR",            213,  43, 134,  36),
    ("plaza-maringa",     "PLAZA MARINGA",            "AUDI", "Plaza",     "Maringá","PR",              47,   9,  30,   8),
    # BYD (9)
    ("byd-ctba",          "BYD CURITIBA",             "BYD",  "BYD",       "Curitiba","PR",            867, 408, 295, 164),
    ("byd-lda",           "BYD LONDRINA",             "BYD",  "BYD",       "Londrina","PR",            568, 393, 124,  51),
    ("byd-mariot",        "BYD MARIO TOURINHO",       "BYD",  "BYD",       "Curitiba","PR",            535, 332, 198,   5),
    ("byd-mga",           "BYD MARINGA",              "BYD",  "BYD",       "Maringá","PR",             503, 311, 146,  46),
    ("byd-cwb-c",         "BYD CASCAVEL",             "BYD",  "BYD",       "Cascavel","PR",            352, 234,  77,  41),
    ("byd-pg",            "BYD PONTA GROSSA",         "BYD",  "BYD",       "Ponta Grossa","PR",        258, 174,  82,   2),
    ("byd-sjp",           "BYD SÃO JOSÉ DOS PINHAIS", "BYD",  "BYD",       "São José dos Pinhais","PR",229, 171,  55,   3),
    ("byd-portao",        "BYD PORTÃO",               "BYD",  "BYD",       "Curitiba","PR",            205, 126,  59,  20),
    ("byd-umuarama",      "BYD AUTOPLUS UMUARAMA",    "BYD",  "AutoPlus",  "Umuarama","PR",            156,  80,  76,   0),
    # GAC (3)
    ("gac-ctba",          "GAC CURITIBA",             "GAC",  "GAC",       "Curitiba","PR",            282, 150, 125,   7),
    ("gac-lda",           "GAC LONDRINA",             "GAC",  "GAC",       "Londrina","PR",             82,  45,  33,   4),
    ("gac-mga",           "GAC MARINGA",              "GAC",  "GAC",       "Maringá","PR",              70,  38,  31,   1),
    # HARLEY (3)
    ("freedom-ctba",      "FREEDOM CURITIBA (The One)","HARLEY-DAVIDSON","Freedom","Curitiba","PR",    127,  49,  78,   0),
    ("harley-rp",         "HARLEY RIBEIRÃO PRETO",    "HARLEY-DAVIDSON","Harley", "Ribeirão Preto","SP", 42,  28,  14,   0),
    ("freedom-lda",       "FREEDOM LONDRINA (Red Wheel)","HARLEY-DAVIDSON","Freedom","Londrina","PR",   32,  18,  14,   0),
    # HYUNDAI (8) — HMB
    ("carway-ipiranga",   "CARWAY IPIRANGA",          "HMB - Hyundai","Carway","Porto Alegre","RS",    547, 271, 272,   4),
    ("sevec-marechal",    "SEVEC MARECHAL",           "HMB - Hyundai","Sevec", "Curitiba","PR",        373, 213, 159,   1),
    ("sevec-bernardes",   "SEVEC ARTHUR BERNARDES",   "HMB - Hyundai","Sevec", "Curitiba","PR",        368, 198, 168,   2),
    ("carway-canoas",     "CARWAY CANOAS",            "HMB - Hyundai","Carway","Canoas","RS",          183,  93,  85,   5),
    ("carway-nh",         "CARWAY NOVO HAMBURGO",     "HMB - Hyundai","Carway","Novo Hamburgo","RS",   162,  89,  72,   1),
    ("carway-bento",      "CARWAY BENTO GONÇALVES",   "HMB - Hyundai","Carway","Bento Gonçalves","RS", 106,  53,  52,   1),
    ("carway-sfran",      "CARWAY S. FRANCISCO",      "HMB - Hyundai","Carway","Porto Alegre","RS",      9,   0,   9,   0),
    ("carway-gravatai",   "CARWAY GRAVATAÍ",          "HMB - Hyundai","Carway","Gravataí","RS",          3,   0,   3,   0),
    # HONDA (4) — Prixx
    ("prixx-mariot",      "PRIXX MARIO TOURINHO",     "HONDA","Prixx",    "Curitiba","PR",             499, 255, 198,  46),
    ("prixx-lda",         "PRIXX LONDRINA",           "HONDA","Prixx",    "Londrina","PR",             288, 135,  90,  63),
    ("prixx-mga",         "PRIXX MARINGÁ",            "HONDA","Prixx",    "Maringá","PR",              269,  93,  86,  90),
    ("prixx-sjp",         "PRIXX SÃO JOSÉ",           "HONDA","Prixx",    "São José dos Pinhais","PR", 191,  68,  94,  29),
    # PEUGEOT-CITROEN (5) — Dijon
    ("dijon-ipiranga",    "DIJON IPIRANGA",           "PEUGEOT-CITROEN","Dijon","Porto Alegre","RS",   339,  57, 173, 109),
    ("dijon-edu",         "DIJON EDU CHAVES",         "PEUGEOT-CITROEN","Dijon","Porto Alegre","RS",   151,  21,  76,  54),
    ("dijon-nh",          "DIJON NOVO HAMBURGO",      "PEUGEOT-CITROEN","Dijon","Novo Hamburgo","RS",   68,  13,  32,  23),
    ("dijon-canoas",      "DIJON CANOAS",             "PEUGEOT-CITROEN","Dijon","Canoas","RS",          39,   4,  20,  15),
    ("dijon-ce",          "DIJON CITROEN CEARÁ",      "PEUGEOT-CITROEN","Dijon","Fortaleza","CE",       28,   0,  28,   0),
    # TRIUMPH (2) — Mavesul
    ("mavesul-mariot",    "MAVESUL MARIO TOURINHO",   "TRIUMPH","Mavesul","Curitiba","PR",             196, 162,  34,   0),
    ("mavesul-lda",       "MAVESUL LONDRINA",         "TRIUMPH","Mavesul","Londrina","PR",              83,  65,  18,   0),
    # VOLVO (2) — Vecodil
    ("vecodil-ctba",      "VECODIL CURITIBA",         "VOLVO","Vecodil", "Curitiba","PR",              302,   0, 189, 113),
    ("vecodil-cwb",       "VECODIL CASCAVEL",         "VOLVO","Vecodil", "Cascavel","PR",               34,   0,  17,  17),
    # VW (8) — Servopa
    ("servopa-matriz",    "SERVOPA MATRIZ (Rockfeller)","VW - VOLKSWAGEN","Servopa","Curitiba","PR",  1546, 440, 511, 595),
    ("servopa-mga",       "SERVOPA MARINGÁ",          "VW - VOLKSWAGEN","Servopa","Maringá","PR",      591, 176, 211, 204),
    ("servopa-mariot",    "SERVOPA MARIO TOURINHO",   "VW - VOLKSWAGEN","Servopa","Curitiba","PR",     523, 325, 175,  23),
    ("servopa-pinh",      "SERVOPA PINHEIRINHO",      "VW - VOLKSWAGEN","Servopa","Curitiba","PR",     392, 157, 202,  33),
    ("servopa-pg",        "SERVOPA PONTA GROSSA",     "VW - VOLKSWAGEN","Servopa","Ponta Grossa","PR", 316, 122, 141,  53),
    ("servopa-png",       "SERVOPA PARANAGUÁ",        "VW - VOLKSWAGEN","Servopa","Paranaguá","PR",    302, 155, 140,   7),
    ("servopa-marechal",  "SERVOPA MARECHAL",         "VW - VOLKSWAGEN","Servopa","Curitiba","PR",     128,  49,  79,   0),
    ("servopa-pnv",       "SERVOPA PARANAVAÍ",        "VW - VOLKSWAGEN","Servopa","Paranavaí","PR",    103,  60,  21,  22),
    # VWC — Caminhões (2)
    ("vwc-ctba",          "CAMINHÕES CURITIBA",       "VWC","Servopa Caminhões","Curitiba","PR",       501, 172,   6, 323),
    ("vwc-cambe",         "CAMINHÕES CAMBÉ",          "VWC","Servopa Caminhões","Cambé","PR",           67,  61,   4,   2),
]


# Configuração por marca: modelos + ticket médio
BRAND_CFG = {
    "AUDI":            (["A3","Q3","A4","Q5","Q7"],                            280_000),
    "BYD":             (["Dolphin","Atto 3","Seal","Han","Tan","Song Plus"],   185_000),
    "GAC":             (["GS3","GS5","GS8","Emkoo"],                           160_000),
    "HARLEY-DAVIDSON": (["Sportster","Softail","Touring","CVO"],                95_000),
    "HMB - Hyundai":   (["HB20","Creta","Tucson","Santa Fe","Kona"],           110_000),
    "HONDA":           (["Civic","HR-V","CR-V","City","Accord"],               120_000),
    "PEUGEOT-CITROEN": (["208","2008","3008","C3","C4 Cactus","C5 Aircross"],  125_000),
    "TRIUMPH":         (["Street Triple","Bonneville","Tiger","Speed Triple"],  85_000),
    "VOLVO":           (["XC40","XC60","XC90","S60","V60"],                    380_000),
    "VW - VOLKSWAGEN": (["Polo","T-Cross","Nivus","Taos","Tiguan","Amarok"],    95_000),
    "VWC":             (["Constellation","Delivery","Meteor","e-Delivery"],    250_000),
}

# Ticket médio diferente por tipo (Novos > Seminovos, VD intermediário)
TICKET_FACTOR = {"novos": 1.00, "seminovos": 0.62, "venda_direta": 0.92}

SELLER_NAMES = [
    "Ana Lima","Bruno Costa","Carlos Silva","Daniela Rocha","Eduardo Santos",
    "Fernanda Alves","Gabriel Souza","Helena Pires","Ivan Moraes","Juliana Neves",
    "Leonardo Faria","Mariana Lopes","Paulo Henrique","Renata Carvalho",
]


def gen_store_data(s_raw: tuple, seed: int) -> dict:
    """s_raw: (id, name, brand, bandeira, city, uf, nfs_4m, vn_4m, vu_4m, vd_4m)"""
    sid, name, brand, bandeira, city, uf, nfs_4m, vn_4m, vu_4m, vd_4m = s_raw
    rng = random.Random(seed)
    models, ticket_base = BRAND_CFG[brand]

    # Volumes mensais (média dos 4 meses)
    vn_mes = round(vn_4m / 4, 1)
    vu_mes = round(vu_4m / 4, 1)
    vd_mes = round(vd_4m / 4, 1)
    total_mes = vn_mes + vu_mes + vd_mes

    # Volume mensal arredondado para inteiros (mix realista)
    vn = max(0, int(round(vn_mes)))
    vu = max(0, int(round(vu_mes)))
    vd = max(0, int(round(vd_mes)))
    total = vn + vu + vd

    # Meta: 10–15% acima do volume real
    meta = max(1, int(total * rng.uniform(1.05, 1.18)))

    # ── Vendas ───────────────────────────────────────────────────────────────
    fat_novos    = vn * ticket_base * TICKET_FACTOR["novos"]    * rng.gauss(1.0, 0.04)
    fat_seminov  = vu * ticket_base * TICKET_FACTOR["seminovos"] * rng.gauss(1.0, 0.04)
    fat_vd       = vd * ticket_base * TICKET_FACTOR["venda_direta"] * rng.gauss(1.0, 0.04)
    faturamento  = fat_novos + fat_seminov + fat_vd
    ticket_medio = int(faturamento / total) if total else 0

    # Mix por modelo (distribui o total entre modelos)
    rem = total
    por_modelo = {}
    for m in models[:-1]:
        v = max(0, int(rem * rng.uniform(0.10, 0.36)))
        por_modelo[m] = v
        rem -= v
    por_modelo[models[-1]] = max(0, rem)

    # Vendedores
    n_sell = max(2, min(12, int(total / 6) + 1))
    sellers = []
    for i in range(n_sell):
        sv = max(0, int(rng.gauss(total / n_sell, total / n_sell * 0.35)))
        sellers.append({
            "nome": SELLER_NAMES[(seed + i) % len(SELLER_NAMES)],
            "vendas": sv,
            "meta": max(1, int(meta / n_sell)),
        })

    # ── Leads / Pipeline ─────────────────────────────────────────────────────
    tx_conv = rng.uniform(0.10, 0.20)
    leads = max(10, int(total / max(0.05, tx_conv) * rng.gauss(1.0, 0.10)))
    contactados  = int(leads        * rng.uniform(0.68, 0.88))
    qualificados = int(contactados  * rng.uniform(0.52, 0.72))
    test_drive   = int(qualificados * rng.uniform(0.42, 0.65))
    proposta     = int(test_drive   * rng.uniform(0.55, 0.80))

    canais = {
        "Digital":   int(leads * rng.uniform(0.42, 0.58)),
        "Indicação": int(leads * rng.uniform(0.18, 0.28)),
        "Loja":      int(leads * rng.uniform(0.14, 0.22)),
    }
    canais["Outros"] = max(0, leads - sum(canais.values()))
    serie = [max(3, int(leads / 4 * rng.gauss(1.0, 0.22))) for _ in range(8)]

    # ── CX ───────────────────────────────────────────────────────────────────
    nps_g   = max(0, min(100, int(rng.gauss(66, 16))))
    nps_neg = max(0, min(100, nps_g + int(rng.gauss(-6, 9))))
    nps_td  = max(0, min(100, nps_g + int(rng.gauss(9, 7))))
    nps_ent = max(0, min(100, nps_g + int(rng.gauss(4, 8))))

    pesquisas = total
    respond   = int(pesquisas * rng.uniform(0.58, 0.84))
    prom = int(respond * rng.uniform(0.38, 0.65))
    detr = int(respond * rng.uniform(0.04, 0.22))
    neut = max(0, respond - prom - detr)
    recl    = max(0, int(rng.gauss(total * 0.09, 2)))
    recl_ab = max(0, int(recl * rng.uniform(0.18, 0.55)))

    # ── Estoque ──────────────────────────────────────────────────────────────
    est_total = max(3, int(total * rng.uniform(0.75, 1.85)))
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
        "id": sid, "name": name, "brand": brand, "bandeira": bandeira,
        "city": city, "uf": uf,
        "nfs_4m": nfs_4m,

        "leads": {
            "total": leads,
            "por_canal": canais,
            "taxa_contato":   round(contactados / leads * 100, 1),
            "tme_resposta_h": round(max(0.5, rng.gauss(3.1, 1.6)), 1),
            "funil": {
                "Leads": leads, "Contactados": contactados,
                "Qualificados": qualificados, "Test Drive": test_drive,
                "Proposta": proposta, "Vendidos": total,
            },
            "serie_semanal": serie,
        },
        "vendas": {
            "total_mes": total,
            "novos": vn,
            "seminovos": vu,
            "venda_direta": vd,
            "meta_mes": meta,
            "atingimento": round(total / meta * 100, 1),
            "ticket_medio": ticket_medio,
            "faturamento": int(faturamento),
            "faturamento_novos":     int(fat_novos),
            "faturamento_seminovos": int(fat_seminov),
            "faturamento_vd":        int(fat_vd),
            "por_modelo": por_modelo,
            "vendedores": sellers,
            "ciclo_medio_dias": max(5, int(rng.gauss(21, 6))),
        },
        "cx": {
            "nps_geral":      nps_g,
            "nps_negociacao": nps_neg,
            "nps_test_drive": nps_td,
            "nps_entrega":    nps_ent,
            "pesquisas_total":       pesquisas,
            "pesquisas_respondidas": respond,
            "taxa_resposta": round(respond / pesquisas * 100, 1) if pesquisas else 0,
            "promotores": prom, "neutros": neut, "detratores": detr,
            "reclamacoes_total":   recl,
            "reclamacoes_abertas": recl_ab,
            "tma_dias": round(max(0.5, rng.gauss(3.4, 1.3)), 1),
        },
        "estoque": {
            "total": est_total,
            "por_modelo": por_mod_est,
            "dias_medio": max(5, int(rng.gauss(44, 14))),
            "criticos_60d": int(rng.uniform(0, 6)),
            "giro_mensal": round(total / max(1, est_total), 2),
        },
        "pos_venda": {
            "os_abertas":      os_ab,
            "os_fechadas_mes": os_fech,
            "csat": csat,
            "receita_servicos": rec_serv,
            "receita_pecas":    rec_pec,
        },
        "financeiro": {
            "faturamento":      int(faturamento),
            "meta_faturamento": int(meta * ticket_medio if ticket_medio else faturamento * 1.1),
            "custo": int(custo),
            "margem": int(margem),
            "pct_margem": round(pct_mg, 1),
        },
    }


def main():
    random.seed(42)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    stores_out = [gen_store_data(s, seed=i * 11 + 7) for i, s in enumerate(STORES_RAW)]

    payload = {
        "generated_at": datetime.now().isoformat(),
        "periodo": "2026-04",  # mês mais recente (Abr/2026)
        "periodo_base_meses": 4,
        "stores": stores_out,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Resumo
    total_v = sum(s["vendas"]["total_mes"] for s in stores_out)
    total_n = sum(s["vendas"]["novos"] for s in stores_out)
    total_u = sum(s["vendas"]["seminovos"] for s in stores_out)
    total_d = sum(s["vendas"]["venda_direta"] for s in stores_out)
    total_f = sum(s["financeiro"]["faturamento"] for s in stores_out)
    brands  = len(set(s["brand"] for s in stores_out))

    print(f"Gerado: {OUT}")
    print(f"  Lojas:         {len(stores_out)}")
    print(f"  Marcas:        {brands}")
    print(f"  Total mensal:  {total_v} un  (Novos: {total_n} · Seminovos: {total_u} · VD: {total_d})")
    print(f"  Faturamento:   R$ {total_f:,.0f}".replace(",", "."))


if __name__ == "__main__":
    main()
