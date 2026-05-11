#!/usr/bin/env python3
"""
observabilidade.py — Dashboard de observabilidade do Grupo Servopa
SPA com sidebar por loja e abas por área de negócio.

Uso:
  python3 mocks/gerar_mock.py   # gera dados mock
  python3 observabilidade.py    # gera dashboard_observabilidade.html
"""

import json
from datetime import datetime
from pathlib import Path

DATA_PATH   = Path(__file__).parent / "logs" / "stores_data.json"
OUTPUT_PATH = Path(__file__).parent / "dashboard_observabilidade.html"


# ── Dados ────────────────────────────────────────────────────────────────────

def load_data():
    if not DATA_PATH.exists():
        return None
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _avg(lst):
    return sum(lst) / len(lst) if lst else 0


def calc_consolidated(stores):
    def _sum(key, *path):
        val = stores
        for p in path:
            val = [v[p] for v in val]
        return sum(v[key] for v in val)

    s = stores
    fat     = sum(x["financeiro"]["faturamento"] for x in s)
    custo   = sum(x["financeiro"]["custo"] for x in s)
    margem  = fat - custo
    respond = sum(x["cx"]["pesquisas_respondidas"] for x in s)
    prom    = sum(x["cx"]["promotores"] for x in s)
    detr    = sum(x["cx"]["detratores"] for x in s)
    neut    = sum(x["cx"]["neutros"] for x in s)
    vend    = sum(x["vendas"]["total_mes"] for x in s)
    meta    = sum(x["vendas"]["meta_mes"] for x in s)

    # Funil agregado
    funil_keys = ["Leads","Contactados","Qualificados","Test Drive","Proposta","Vendidos"]
    funil = {k: sum(x["leads"]["funil"].get(k, 0) for x in s) for k in funil_keys}

    # Canal agregado
    all_canais = {}
    for x in s:
        for canal, v in x["leads"]["por_canal"].items():
            all_canais[canal] = all_canais.get(canal, 0) + v

    # Série semanal agregada
    serie = [sum(x["leads"]["serie_semanal"][i] for x in s) for i in range(8)]

    # Top modelos (sum across all brands, top 8)
    all_models = {}
    for x in s:
        for m, v in x["vendas"]["por_modelo"].items():
            all_models[m] = all_models.get(m, 0) + v
    top_models = dict(sorted(all_models.items(), key=lambda kv: kv[1], reverse=True)[:8])

    all_est = {}
    for x in s:
        for m, v in x["estoque"]["por_modelo"].items():
            all_est[m] = all_est.get(m, 0) + v
    top_est = dict(sorted(all_est.items(), key=lambda kv: kv[1], reverse=True)[:8])

    leads_total = sum(x["leads"]["total"] for x in s)

    return {
        "id": "grupo", "name": "Grupo Servopa", "city": "Sul do Brasil", "uf": "", "brand": "",
        "leads": {
            "total": leads_total,
            "por_canal": all_canais,
            "taxa_contato": round(_avg([x["leads"]["taxa_contato"] for x in s]), 1),
            "tme_resposta_h": round(_avg([x["leads"]["tme_resposta_h"] for x in s]), 1),
            "funil": funil,
            "serie_semanal": serie,
        },
        "vendas": {
            "total_mes": vend, "meta_mes": meta,
            "novos":        sum(x["vendas"]["novos"] for x in s),
            "seminovos":    sum(x["vendas"]["seminovos"] for x in s),
            "venda_direta": sum(x["vendas"]["venda_direta"] for x in s),
            "atingimento": round(vend / meta * 100, 1) if meta else 0,
            "ticket_medio": int(fat / vend) if vend else 0,
            "faturamento": fat,
            "faturamento_novos":     sum(x["vendas"]["faturamento_novos"] for x in s),
            "faturamento_seminovos": sum(x["vendas"]["faturamento_seminovos"] for x in s),
            "faturamento_vd":        sum(x["vendas"]["faturamento_vd"] for x in s),
            "por_modelo": top_models,
            "vendedores": [],
            "ciclo_medio_dias": int(_avg([x["vendas"]["ciclo_medio_dias"] for x in s])),
        },
        "cx": {
            "nps_geral":      int(_avg([x["cx"]["nps_geral"] for x in s])),
            "nps_negociacao": int(_avg([x["cx"]["nps_negociacao"] for x in s])),
            "nps_test_drive": int(_avg([x["cx"]["nps_test_drive"] for x in s])),
            "nps_entrega":    int(_avg([x["cx"]["nps_entrega"] for x in s])),
            "pesquisas_total":      sum(x["cx"]["pesquisas_total"] for x in s),
            "pesquisas_respondidas": respond,
            "taxa_resposta": round(respond / sum(x["cx"]["pesquisas_total"] for x in s) * 100, 1),
            "promotores": prom, "neutros": neut, "detratores": detr,
            "reclamacoes_total":   sum(x["cx"]["reclamacoes_total"] for x in s),
            "reclamacoes_abertas": sum(x["cx"]["reclamacoes_abertas"] for x in s),
            "tma_dias": round(_avg([x["cx"]["tma_dias"] for x in s]), 1),
        },
        "estoque": {
            "total": sum(x["estoque"]["total"] for x in s),
            "por_modelo": top_est,
            "dias_medio": int(_avg([x["estoque"]["dias_medio"] for x in s])),
            "criticos_60d": sum(x["estoque"]["criticos_60d"] for x in s),
            "giro_mensal": round(vend / max(1, sum(x["estoque"]["total"] for x in s)), 2),
        },
        "pos_venda": {
            "os_abertas":      sum(x["pos_venda"]["os_abertas"] for x in s),
            "os_fechadas_mes": sum(x["pos_venda"]["os_fechadas_mes"] for x in s),
            "csat":            round(_avg([x["pos_venda"]["csat"] for x in s]), 1),
            "receita_servicos": sum(x["pos_venda"]["receita_servicos"] for x in s),
            "receita_pecas":    sum(x["pos_venda"]["receita_pecas"] for x in s),
        },
        "financeiro": {
            "faturamento": fat, "meta_faturamento": sum(x["financeiro"]["meta_faturamento"] for x in s),
            "custo": custo, "margem": margem,
            "pct_margem": round(margem / fat * 100, 1) if fat else 0,
        },
    }


# ── CSS ──────────────────────────────────────────────────────────────────────

CSS = """
:root{--ok:#22c55e;--warn:#f59e0b;--err:#ef4444;--unk:#94a3b8;
  --bg:#f1f5f9;--card:#fff;--border:#e2e8f0;
  --text:#1e293b;--muted:#64748b;
  --sb:#0f172a;--sbtext:#cbd5e1;--sbact:#2563eb}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  background:var(--bg);color:var(--text);height:100vh;overflow:hidden}

/* App shell */
.app{display:grid;grid-template-columns:240px 1fr;height:100vh}

/* ── Sidebar ── */
.sidebar{background:var(--sb);display:flex;flex-direction:column;overflow:hidden}

.sb-logo{padding:16px 16px 12px;border-bottom:1px solid #ffffff10}
.sb-logo strong{display:block;color:#fff;font-size:.9rem;font-weight:700;letter-spacing:-.01em}
.sb-logo span{font-size:.68rem;color:#ffffff44}

/* Store picker */
.sb-picker{padding:10px 12px;border-bottom:1px solid #ffffff10;position:relative}
.picker-btn{width:100%;background:#ffffff12;border:1px solid #ffffff18;border-radius:7px;
  color:#fff;font-size:.8rem;padding:7px 10px;display:flex;align-items:center;
  justify-content:space-between;cursor:pointer;gap:6px;text-align:left}
.picker-btn:hover{background:#ffffff1e}
.picker-btn .store-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.picker-btn .arrow{opacity:.5;font-size:.7rem;flex-shrink:0}
.picker-dropdown{position:absolute;left:12px;right:12px;top:calc(100% - 2px);
  background:#1e293b;border:1px solid #ffffff18;border-radius:7px;
  box-shadow:0 8px 24px rgba(0,0,0,.4);z-index:100;display:none;max-height:320px;
  overflow:hidden;flex-direction:column}
.picker-dropdown.open{display:flex}
.picker-search{padding:8px 10px;border-bottom:1px solid #ffffff10;flex-shrink:0}
.picker-search input{width:100%;background:#ffffff10;border:none;border-radius:5px;
  color:#fff;font-size:.78rem;padding:5px 8px;outline:none}
.picker-search input::placeholder{color:#ffffff44}
.picker-list{overflow-y:auto;flex:1}
.picker-list::-webkit-scrollbar{width:3px}
.picker-list::-webkit-scrollbar-thumb{background:#ffffff22}
.picker-group{padding:5px 10px 2px;font-size:.62rem;font-weight:700;
  color:#ffffff33;text-transform:uppercase;letter-spacing:.07em}
.picker-item{padding:6px 10px 6px 18px;font-size:.78rem;color:var(--sbtext);
  cursor:pointer;display:flex;align-items:center;gap:7px}
.picker-item:hover{background:#ffffff0e;color:#fff}
.picker-item.active{color:#fff;font-weight:600}
.picker-item.grupo{padding-left:10px;font-weight:600;color:#fff;border-bottom:1px solid #ffffff10;margin-bottom:4px}

/* ── Area nav ── */
.sb-nav{flex:1;overflow-y:auto;padding:10px 8px}
.sb-nav::-webkit-scrollbar{width:3px}
.sb-nav::-webkit-scrollbar-thumb{background:#ffffff18;border-radius:2px}
.nav-area{display:flex;align-items:center;gap:10px;padding:9px 12px;
  font-size:.82rem;font-weight:500;color:var(--sbtext);cursor:pointer;
  border-radius:7px;transition:background .12s;user-select:none}
.nav-area:hover{background:#ffffff0d;color:#fff}
.nav-area.active{background:var(--sbact);color:#fff;font-weight:600}
.nav-area .ico{font-size:1rem;width:20px;text-align:center;flex-shrink:0}

/* ── Main ── */
.main-wrap{display:flex;flex-direction:column;overflow:hidden;background:var(--bg)}
.main-hdr{background:var(--card);border-bottom:1px solid var(--border);
  padding:16px 28px;flex-shrink:0;display:flex;align-items:baseline;gap:10px}
#area-title{font-size:1.05rem;font-weight:700}
#store-sub{font-size:.78rem;color:var(--muted)}
#content{flex:1;overflow-y:auto;padding:24px 28px}
#content::-webkit-scrollbar{width:6px}
#content::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:3px}

/* ── KPI cards ── */
.kpis{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:12px;margin-bottom:20px}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
.kv{font-size:1.7rem;font-weight:800;line-height:1.1}
.ku{font-size:.9rem;font-weight:500}
.kl{font-size:.73rem;color:var(--muted);margin-top:3px}
.ks{font-size:.7rem;color:var(--muted);margin-top:2px}
.kpi.ok .kv{color:var(--ok)} .kpi.warn .kv{color:var(--warn)} .kpi.err .kv{color:var(--err)}

/* Section title within a tab */
.sec-title{font-size:.78rem;font-weight:700;color:var(--muted);text-transform:uppercase;
  letter-spacing:.05em;margin:20px 0 12px;padding-top:8px;border-top:1px solid var(--border)}

/* ── Charts ── */
.charts-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.ccard{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 20px}
.ccard h3{font-size:.78rem;font-weight:700;color:var(--muted);text-transform:uppercase;
  letter-spacing:.05em;margin-bottom:14px}
.ccard-full{grid-column:1/-1}

/* ── Table ── */
.rtable{width:100%;border-collapse:collapse;font-size:.8rem}
.rtable th{padding:7px 10px;text-align:left;font-size:.7rem;color:var(--muted);
  text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--border)}
.rtable td{padding:8px 10px;border-bottom:1px solid #f1f5f9}
.rtable tr:last-child td{border-bottom:none}

/* ── Brand heat table (consolidated) ── */
.heat-table{width:100%;border-collapse:collapse;font-size:.82rem;margin-top:16px}
.heat-table th{padding:8px 12px;text-align:left;font-size:.7rem;color:var(--muted);
  text-transform:uppercase;letter-spacing:.04em;background:#f8fafc;border-bottom:1px solid var(--border)}
.heat-table td{padding:9px 12px;border-bottom:1px solid #f1f5f9}
.heat-table tr:last-child td{border-bottom:none}
.heat-table tr:hover td{background:#f8fafc}
.brand-link{color:inherit;text-decoration:none;font-weight:600;cursor:pointer}
.brand-link:hover{color:#2563eb}

/* ── Status badges ── */
.badge{display:inline-block;font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:8px}
.badge.ok{background:#dcfce7;color:#15803d} .badge.warn{background:#fef9c3;color:#854d0e}
.badge.err{background:#fee2e2;color:#b91c1c}
.ok-badge{color:var(--ok);font-weight:700} .warn-badge{color:var(--warn);font-weight:700}
.err-badge{color:var(--err);font-weight:700}

/* ── Alert bar ── */
.alert{padding:10px 14px;border-radius:8px;font-size:.8rem;font-weight:500;margin-bottom:16px}
.alert.ok{background:#dcfce7;color:#15803d;border:1px solid #bbf7d0}
.alert.warn{background:#fef9c3;color:#854d0e;border:1px solid #fde68a}

/* Responsive */
@media(max-width:900px){
  .app{grid-template-columns:1fr}
  .sidebar{display:none}
  .charts-row{grid-template-columns:1fr}
}
"""


# ── JavaScript SPA ────────────────────────────────────────────────────────────

JS = r"""
const COLORS=['#1a56db','#7c3aed','#0891b2','#16a34a','#ea580c','#dc2626','#f59e0b','#0d9488'];
const chartInst={};
let activeStore='grupo', activeArea='overview';

const fmt=n=>new Intl.NumberFormat('pt-BR').format(Math.round(n));
const fmtC=n=>'R$ '+fmt(n);
const fmtP=n=>n.toFixed(1)+'%';
const hc=(v,ok,warn)=>v>=ok?'ok':v>=warn?'warn':'err';
const npsScore=cx=>cx.pesquisas_respondidas>0?Math.round((cx.promotores-cx.detratores)/cx.pesquisas_respondidas*100):0;

function storeHealth(s){
  const atg=s.vendas.atingimento,nps=npsScore(s.cx),mg=s.financeiro.pct_margem;
  if(atg<75||nps<10||mg<5) return'err';
  if(atg<90||nps<30||mg<8) return'warn';
  return'ok';
}

function destroyCharts(){
  Object.values(chartInst).forEach(c=>{try{c.destroy()}catch(e){}});
  Object.keys(chartInst).forEach(k=>delete chartInst[k]);
}
function mkChart(id,cfg){
  const el=document.getElementById(id);if(!el)return;
  if(chartInst[id])chartInst[id].destroy();
  chartInst[id]=new Chart(el.getContext('2d'),cfg);
}

// ── Store picker ──────────────────────────────────────────────────────────────
function buildPicker(){
  const list=document.getElementById('picker-list');
  list.innerHTML=`<div class="picker-item grupo active" data-id="grupo" onclick="selectStore('grupo')">🏢 Grupo Servopa</div>`;
  const brands={};
  DB.stores.forEach(s=>(brands[s.brand]=brands[s.brand]||[]).push(s));
  Object.entries(brands).forEach(([brand,stores])=>{
    list.innerHTML+=`<div class="picker-group">${brand}</div>`;
    stores.forEach(s=>{
      const h=storeHealth(s);
      list.innerHTML+=`<div class="picker-item" data-id="${s.id}" onclick="selectStore('${s.id}')">
        <span class="nav-dot dot-${h}"></span>${s.name}
      </div>`;
    });
  });
}

function togglePicker(){
  const dd=document.getElementById('picker-dd');
  dd.classList.toggle('open');
  if(dd.classList.contains('open')) document.getElementById('picker-input').focus();
}

function filterPicker(q){
  q=q.toLowerCase();
  document.querySelectorAll('.picker-item:not(.grupo)').forEach(el=>{
    el.style.display=(q===''||el.textContent.toLowerCase().includes(q))?'':'none';
  });
  document.querySelectorAll('.picker-group').forEach(g=>{
    const vis=[...g.nextElementSibling?[]:[]];
    let sib=g.nextElementSibling;
    let anyVis=false;
    while(sib&&!sib.classList.contains('picker-group')){
      if(sib.style.display!=='none') anyVis=true;
      sib=sib.nextElementSibling;
    }
    g.style.display=anyVis||q===''?'':'none';
  });
}

document.addEventListener('click',e=>{
  if(!e.target.closest('.sb-picker')) document.getElementById('picker-dd').classList.remove('open');
});

// ── Area navigation ───────────────────────────────────────────────────────────
const AREAS=[
  ['overview',   '🏠', 'Visão Geral'],
  ['pipeline',   '🔀', 'Pipeline de Vendas'],
  ['vendas',     '🚗', 'Vendas Geradas'],
  ['cx',         '⭐', 'CX & Satisfação'],
  ['estoque',    '📦', 'Estoque'],
  ['pos-venda',  '🔧', 'Pós-Venda'],
  ['financeiro', '💰', 'Financeiro'],
];

function buildNav(){
  const nav=document.getElementById('sidebar-nav');
  nav.innerHTML=AREAS.map(([id,ico,label])=>`
    <div class="nav-area ${id==='overview'?'active':''}" data-area="${id}" onclick="selectArea('${id}')">
      <span class="ico">${ico}</span>${label}
    </div>`).join('');
}

function selectArea(area){
  activeArea=area;
  document.querySelectorAll('.nav-area').forEach(el=>
    el.classList.toggle('active',el.dataset.area===area));
  const label=AREAS.find(a=>a[0]===area)?.[2]||area;
  document.getElementById('area-title').textContent=label;
  renderArea(area);
}

function selectStore(id){
  activeStore=id;
  document.getElementById('picker-dd').classList.remove('open');
  document.getElementById('picker-input').value='';
  filterPicker('');
  document.querySelectorAll('.picker-item').forEach(el=>
    el.classList.toggle('active',el.dataset.id===id));
  const s=getStore(id);
  document.getElementById('picker-btn-label').textContent=s.name;
  let sub='';
  if(s.city&&s.uf) sub=s.city+', '+s.uf;
  if(s.brand&&s.bandeira&&s.bandeira!==s.brand) sub+=' · '+s.brand+' / bandeira '+s.bandeira;
  else if(s.brand) sub+=' · '+s.brand;
  document.getElementById('store-sub').textContent=sub;
  renderArea(activeArea);
}

function getStore(id){
  if(id==='grupo') return DB.consolidated;
  return DB.stores.find(s=>s.id===id);
}

function renderArea(area){
  destroyCharts();
  const s=getStore(activeStore);
  const el=document.getElementById('content');
  switch(area){
    case'overview':  el.innerHTML=renderOverview(s);    break;
    case'pipeline':  el.innerHTML=renderLeads(s.leads); break;
    case'vendas':    el.innerHTML=renderVendas(s);      break;
    case'cx':        el.innerHTML=renderCX(s.cx);       break;
    case'estoque':   el.innerHTML=renderEstoque(s);     break;
    case'pos-venda': el.innerHTML=renderPosVenda(s.pos_venda); break;
    case'financeiro':el.innerHTML=renderFinanceiro(s.financeiro); break;
  }
  requestAnimationFrame(()=>initCharts(area,s));
}

// ── KPI helper ───────────────────────────────────────────────────────────────
function kpi(label,val,cls='',sub=''){
  return`<div class="kpi ${cls}"><div class="kv">${val}</div>
    <div class="kl">${label}</div>${sub?`<div class="ks">${sub}</div>`:''}</div>`;
}

// ── Render: Overview ─────────────────────────────────────────────────────────
function renderOverview(s){
  const isGrupo=activeStore==='grupo';
  if(isGrupo) return renderConsolidadoOverview(s);
  const nps=npsScore(s.cx), atg=s.vendas.atingimento, mg=s.financeiro.pct_margem;
  return`
  <div class="kpis">
    ${kpi('Vendas do mês',s.vendas.total_mes+'<span class="ku"> un</span>',hc(atg,95,80),`Meta ${s.vendas.meta_mes} · ${fmtP(atg)}`)}
    ${kpi('NPS',nps,hc(nps,50,20),`${s.cx.promotores}P · ${s.cx.neutros}N · ${s.cx.detratores}D`)}
    ${kpi('Faturamento',fmtC(s.financeiro.faturamento),hc(s.financeiro.faturamento/s.financeiro.meta_faturamento*100,95,80),`Meta ${fmtC(s.financeiro.meta_faturamento)}`)}
    ${kpi('Margem %',fmtP(mg),hc(mg,10,7),fmtC(s.financeiro.margem))}
    ${kpi('Recl. abertas',s.cx.reclamacoes_abertas,s.cx.reclamacoes_abertas<=3?'ok':'warn',`Total mês: ${s.cx.reclamacoes_total}`)}
    ${kpi('Estoque',s.estoque.total+'<span class="ku"> un</span>','',s.estoque.dias_medio+'d médio · '+s.estoque.criticos_60d+' críticos')}
  </div>
  <div class="charts-row">
    <div class="ccard"><h3>Funil de Vendas</h3><canvas id="ch-ov-funil" height="180"></canvas></div>
    <div class="ccard"><h3>NPS — Composição</h3><canvas id="ch-ov-nps" height="180"></canvas></div>
  </div>`;
}

function renderConsolidadoOverview(s){
  const nps=npsScore(s.cx);
  const rows=DB.stores.map(st=>{
    const h=storeHealth(st), an=npsScore(st.cx), at=st.vendas.atingimento;
    return`<tr>
      <td><span class="brand-link" onclick="selectStore('${st.id}')">${st.name}</span></td>
      <td>${st.city}, ${st.uf}</td>
      <td>${st.vendas.total_mes} / ${st.vendas.meta_mes}</td>
      <td class="${hc(at,95,80)+'-badge'}">${fmtP(at)}</td>
      <td class="${hc(an,50,20)+'-badge'}">${an}</td>
      <td class="${hc(st.financeiro.pct_margem,10,7)+'-badge'}">${fmtP(st.financeiro.pct_margem)}</td>
      <td><span class="badge ${h}">${h==='ok'?'✓ OK':h==='warn'?'⚠ Alerta':'✗ Atenção'}</span></td>
    </tr>`;
  }).join('');
  return`
  <div class="kpis">
    ${kpi('Total Vendas',fmt(s.vendas.total_mes)+'<span class="ku"> un</span>',hc(s.vendas.atingimento,95,80),`Ating. ${fmtP(s.vendas.atingimento)}`)}
    ${kpi('NPS Médio',nps,hc(nps,50,20),`${s.cx.promotores}P · ${s.cx.neutros}N · ${s.cx.detratores}D`)}
    ${kpi('Faturamento Total',fmtC(s.financeiro.faturamento),'',`Meta ${fmtC(s.financeiro.meta_faturamento)}`)}
    ${kpi('Margem Grupo',fmtP(s.financeiro.pct_margem),hc(s.financeiro.pct_margem,10,7),fmtC(s.financeiro.margem))}
    ${kpi('Estoque Total',fmt(s.estoque.total)+'<span class="ku"> un</span>','',s.estoque.criticos_60d+' veíc. >60d')}
    ${kpi('Recl. Abertas',fmt(s.cx.reclamacoes_abertas),s.cx.reclamacoes_abertas<20?'ok':'warn',`Total mês: ${fmt(s.cx.reclamacoes_total)}`)}
  </div>
  <div class="ccard">
    <h3>Ranking de Lojas</h3>
    <table class="heat-table">
      <thead><tr><th>Loja</th><th>Cidade</th><th>Vendas/Meta</th><th>Ating.</th><th>NPS</th><th>Margem</th><th>Status</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  </div>`;
}

// ── Render: Leads ─────────────────────────────────────────────────────────────
function renderLeads(l){
  return`
  <div class="kpis">
    ${kpi('Total de Leads',fmt(l.total))}
    ${kpi('Taxa de Contato',fmtP(l.taxa_contato),hc(l.taxa_contato,75,60))}
    ${kpi('TME Resposta',l.tme_resposta_h+'h',hc(8-l.tme_resposta_h,4,2))}
    ${kpi('Convertidos',l.funil['Vendidos']+'<span class="ku"> un</span>','',fmtP(l.funil['Vendidos']/l.total*100)+' do total')}
  </div>
  <div class="charts-row">
    <div class="ccard"><h3>Funil de Leads</h3><canvas id="ch-leads-funil" height="220"></canvas></div>
    <div class="ccard"><h3>Origem dos Leads</h3><canvas id="ch-leads-canal" height="220"></canvas></div>
  </div>
  <div class="ccard ccard-full"><h3>Leads por Semana — últimas 8 semanas</h3>
    <canvas id="ch-leads-serie" height="110"></canvas></div>`;
}

// ── Render: Vendas ─────────────────────────────────────────────────────────────
function renderVendas(s){
  const v=s.vendas;
  const rows=v.vendedores.slice(0,10).map(vd=>{
    const at=vd.meta>0?vd.vendas/vd.meta*100:0;
    return`<tr><td>${vd.nome}</td><td>${vd.vendas}</td><td>${vd.meta}</td>
      <td class="${hc(at,100,80)+'-badge'}">${fmtP(at)}</td></tr>`;
  }).join('');
  const tbl=v.vendedores.length>0
    ?`<table class="rtable"><thead><tr><th>Vendedor</th><th>Vendas</th><th>Meta</th><th>Ating.</th></tr></thead><tbody>${rows}</tbody></table>`
    :'<p style="color:var(--muted);font-size:.82rem">Visão consolidada — sem ranking individual.</p>';
  return`
  <div class="kpis">
    ${kpi('Vendas Totais',fmt(v.total_mes)+'<span class="ku"> un</span>',hc(v.atingimento,95,80),'Meta: '+fmt(v.meta_mes))}
    ${kpi('Atingimento',fmtP(v.atingimento),hc(v.atingimento,95,80))}
    ${kpi('Faturamento',fmtC(v.faturamento))}
    ${kpi('Ticket Médio',fmtC(v.ticket_medio))}
    ${kpi('Ciclo Médio',v.ciclo_medio_dias+'<span class="ku">d</span>')}
  </div>

  <h3 class="sec-title">Composição das Vendas</h3>
  <div class="kpis">
    ${kpi('🆕 Novos (VN)',fmt(v.novos)+'<span class="ku"> un</span>','',fmtP(v.novos/v.total_mes*100)+' do total · '+fmtC(v.faturamento_novos))}
    ${kpi('🔄 Seminovos (VU)',fmt(v.seminovos)+'<span class="ku"> un</span>','',fmtP(v.seminovos/v.total_mes*100)+' do total · '+fmtC(v.faturamento_seminovos))}
    ${kpi('🚛 Venda Direta (VD)',fmt(v.venda_direta)+'<span class="ku"> un</span>','',fmtP(v.venda_direta/v.total_mes*100)+' do total · '+fmtC(v.faturamento_vd))}
  </div>

  <div class="charts-row">
    <div class="ccard"><h3>Mix Vendas — Novos / Seminovos / VD</h3><canvas id="ch-vnd-mix" height="200"></canvas></div>
    <div class="ccard"><h3>Vendas por Modelo</h3><canvas id="ch-vnd-mod" height="200"></canvas></div>
  </div>
  <div class="ccard ccard-full" style="margin-top:16px"><h3>Ranking de Vendedores</h3>${tbl}</div>`;
}

// ── Render: CX ────────────────────────────────────────────────────────────────
function renderCX(cx){
  const nps=npsScore(cx);
  return`
  <div class="kpis">
    ${kpi('NPS',nps,hc(nps,50,20))}
    ${kpi('NPS Negociação',cx.nps_negociacao,hc(cx.nps_negociacao,50,20))}
    ${kpi('NPS Test Drive',cx.nps_test_drive,hc(cx.nps_test_drive,50,20))}
    ${kpi('NPS Entrega',cx.nps_entrega,hc(cx.nps_entrega,50,20))}
    ${kpi('Taxa de Resposta',fmtP(cx.taxa_resposta),hc(cx.taxa_resposta,70,50))}
    ${kpi('TMA',cx.tma_dias+'d',hc(6-cx.tma_dias,3,1))}
    ${kpi('Recl. abertas',cx.reclamacoes_abertas,cx.reclamacoes_abertas<=3?'ok':'warn',`Total: ${cx.reclamacoes_total}`)}
    ${kpi('Respondidas',cx.pesquisas_respondidas+'<span class="ku"> / '+cx.pesquisas_total+'</span>')}
  </div>
  <div class="charts-row">
    <div class="ccard"><h3>Composição NPS</h3><canvas id="ch-cx-comp" height="200"></canvas></div>
    <div class="ccard"><h3>NPS por Etapa</h3><canvas id="ch-cx-etapas" height="200"></canvas></div>
  </div>`;
}

// ── Render: Estoque ───────────────────────────────────────────────────────────
function renderEstoque(s){
  const e=s.estoque;
  const alrt=e.criticos_60d>0
    ?`<div class="alert warn">⚠ ${e.criticos_60d} veículo(s) com mais de 60 dias parado(s) — ação necessária</div>`
    :'<div class="alert ok">✓ Nenhum veículo com mais de 60 dias parado</div>';
  return`
  <div class="kpis">
    ${kpi('Estoque Total',e.total+'<span class="ku"> un</span>')}
    ${kpi('Dias Médio',e.dias_medio+'d',hc(90-e.dias_medio,45,20))}
    ${kpi('Giro Mensal',e.giro_mensal+'x',hc(e.giro_mensal,0.8,0.5))}
    ${kpi('>60 dias parado',e.criticos_60d+'<span class="ku"> un</span>',e.criticos_60d===0?'ok':'warn')}
  </div>
  ${alrt}
  <div class="ccard"><h3>Estoque por Modelo</h3><canvas id="ch-est-mod" height="200"></canvas></div>`;
}

// ── Render: Pós-Venda ─────────────────────────────────────────────────────────
function renderPosVenda(pv){
  return`
  <div class="kpis">
    ${kpi('OS Abertas',pv.os_abertas,pv.os_abertas<=20?'ok':'warn')}
    ${kpi('OS Fechadas (mês)',fmt(pv.os_fechadas_mes))}
    ${kpi('CSAT',pv.csat.toFixed(1)+'/10',hc(pv.csat,8,6.5))}
    ${kpi('Receita Serviços',fmtC(pv.receita_servicos))}
    ${kpi('Receita Peças',fmtC(pv.receita_pecas))}
    ${kpi('Receita Total',fmtC(pv.receita_servicos+pv.receita_pecas))}
  </div>
  <div class="charts-row">
    <div class="ccard"><h3>Receita Pós-Venda</h3><canvas id="ch-pv-rev" height="200"></canvas></div>
    <div class="ccard"><h3>OS — Abertas vs Fechadas</h3><canvas id="ch-pv-os" height="200"></canvas></div>
  </div>`;
}

// ── Render: Financeiro ────────────────────────────────────────────────────────
function renderFinanceiro(f){
  const atg=f.faturamento/f.meta_faturamento*100;
  return`
  <div class="kpis">
    ${kpi('Faturamento',fmtC(f.faturamento),hc(atg,95,80))}
    ${kpi('Meta',fmtC(f.meta_faturamento))}
    ${kpi('Atingimento',fmtP(atg),hc(atg,95,80))}
    ${kpi('Custo Total',fmtC(f.custo))}
    ${kpi('Margem Bruta',fmtC(f.margem),hc(f.pct_margem,10,7))}
    ${kpi('% Margem',fmtP(f.pct_margem),hc(f.pct_margem,10,7))}
  </div>
  <div class="ccard"><h3>Faturamento · Custo · Margem</h3>
    <canvas id="ch-fin" height="160"></canvas></div>`;
}

// ── Chart init ────────────────────────────────────────────────────────────────
function initCharts(area,s){
  switch(area){
    case'overview':
      if(activeStore!=='grupo'){
        const f=s.vendas.funil;
        mkChart('ch-ov-funil',{type:'bar',
          data:{labels:Object.keys(f),datasets:[{data:Object.values(f),
            backgroundColor:'#1a56db99',borderColor:'#1a56db',borderWidth:1}]},
          options:{indexAxis:'y',plugins:{legend:{display:false}},
            scales:{x:{grid:{color:'#f1f5f9'}},y:{grid:{display:false}}}}});
        mkChart('ch-ov-nps',{type:'doughnut',
          data:{labels:['Promotores','Neutros','Detratores'],
            datasets:[{data:[s.cx.promotores,s.cx.neutros,s.cx.detratores],
              backgroundColor:['#22c55e','#94a3b8','#ef4444'],borderWidth:0}]},
          options:{cutout:'65%',plugins:{legend:{position:'bottom',labels:{boxWidth:12}}}}});
      }
      break;
    case'pipeline':{
      const l=s.leads;
      mkChart('ch-leads-funil',{type:'bar',
        data:{labels:Object.keys(l.funil),datasets:[{data:Object.values(l.funil),
          backgroundColor:COLORS[0]+'99',borderColor:COLORS[0],borderWidth:1}]},
        options:{indexAxis:'y',plugins:{legend:{display:false}},
          scales:{x:{grid:{color:'#f1f5f9'}},y:{grid:{display:false}}}}});
      mkChart('ch-leads-canal',{type:'doughnut',
        data:{labels:Object.keys(l.por_canal),datasets:[{data:Object.values(l.por_canal),
          backgroundColor:COLORS,borderWidth:0}]},
        options:{cutout:'55%',plugins:{legend:{position:'bottom',labels:{boxWidth:12}}}}});
      const weeks=l.serie_semanal.map((_,i)=>'S'+(i+1));
      mkChart('ch-leads-serie',{type:'line',
        data:{labels:weeks,datasets:[{label:'Leads',data:l.serie_semanal,
          borderColor:COLORS[0],backgroundColor:COLORS[0]+'22',fill:true,tension:.35,pointRadius:3}]},
        options:{plugins:{legend:{display:false}},
          scales:{x:{grid:{display:false}},y:{grid:{color:'#f1f5f9'}}}}});
      break;}
    case'vendas':{
      const v=s.vendas;
      mkChart('ch-vnd-mix',{type:'doughnut',
        data:{labels:['Novos','Seminovos','Venda Direta'],
          datasets:[{data:[v.novos,v.seminovos,v.venda_direta],
            backgroundColor:['#1a56db','#7c3aed','#0891b2'],borderWidth:0}]},
        options:{cutout:'60%',plugins:{legend:{position:'bottom',labels:{boxWidth:12}}}}});
      mkChart('ch-vnd-mod',{type:'bar',
        data:{labels:Object.keys(s.vendas.por_modelo),
          datasets:[{data:Object.values(s.vendas.por_modelo),
            backgroundColor:COLORS.map(c=>c+'cc'),borderWidth:0,borderRadius:4}]},
        options:{plugins:{legend:{display:false}},
          scales:{x:{grid:{display:false}},y:{grid:{color:'#f1f5f9'}}}}});
      break;}
    case'cx':{
      const cx=s.cx;
      mkChart('ch-cx-comp',{type:'doughnut',
        data:{labels:['Promotores','Neutros','Detratores'],
          datasets:[{data:[cx.promotores,cx.neutros,cx.detratores],
            backgroundColor:['#22c55e','#94a3b8','#ef4444'],borderWidth:0}]},
        options:{cutout:'60%',plugins:{legend:{position:'bottom',labels:{boxWidth:12}}}}});
      mkChart('ch-cx-etapas',{type:'bar',
        data:{labels:['Geral','Negociação','Test Drive','Entrega'],
          datasets:[{data:[cx.nps_geral,cx.nps_negociacao,cx.nps_test_drive,cx.nps_entrega],
            backgroundColor:['#1a56db','#7c3aed','#0891b2','#16a34a'],borderWidth:0,borderRadius:4}]},
        options:{plugins:{legend:{display:false}},
          scales:{x:{grid:{display:false}},y:{max:100,grid:{color:'#f1f5f9'}}}}});
      break;}
    case'estoque':
      mkChart('ch-est-mod',{type:'bar',
        data:{labels:Object.keys(s.estoque.por_modelo),
          datasets:[{data:Object.values(s.estoque.por_modelo),
            backgroundColor:COLORS.map(c=>c+'cc'),borderWidth:0,borderRadius:4}]},
        options:{plugins:{legend:{display:false}},
          scales:{x:{grid:{display:false}},y:{grid:{color:'#f1f5f9'}}}}});
      break;
    case'pos-venda':{
      const pv=s.pos_venda;
      mkChart('ch-pv-rev',{type:'doughnut',
        data:{labels:['Serviços','Peças'],
          datasets:[{data:[pv.receita_servicos,pv.receita_pecas],
            backgroundColor:['#1a56db','#7c3aed'],borderWidth:0}]},
        options:{cutout:'55%',plugins:{legend:{position:'bottom',labels:{boxWidth:12}}}}});
      mkChart('ch-pv-os',{type:'bar',
        data:{labels:['OS Abertas','OS Fechadas'],
          datasets:[{data:[pv.os_abertas,pv.os_fechadas_mes],
            backgroundColor:['#f59e0b','#22c55e'],borderWidth:0,borderRadius:4}]},
        options:{plugins:{legend:{display:false}},
          scales:{x:{grid:{display:false}},y:{grid:{color:'#f1f5f9'}}}}});
      break;}
    case'financeiro':{
      const f=s.financeiro;
      mkChart('ch-fin',{type:'bar',
        data:{labels:['Faturamento','Custo Total','Margem Bruta'],
          datasets:[{data:[f.faturamento,f.custo,f.margem],
            backgroundColor:['#1a56db','#ef4444','#22c55e'],borderWidth:0,borderRadius:4}]},
        options:{plugins:{legend:{display:false}},
          scales:{x:{grid:{display:false}},
            y:{grid:{color:'#f1f5f9'},
              ticks:{callback:v=>v>=1e6?'R$'+(v/1e6).toFixed(1)+'M':v>=1e3?'R$'+(v/1e3).toFixed(0)+'K':'R$'+v}}}}});
      break;}
  }
}

document.addEventListener('DOMContentLoaded',()=>{
  buildPicker();
  buildNav();
  selectStore('grupo');
  selectArea('overview');
});
"""


# ── HTML ──────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Observabilidade — Grupo Servopa</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>__CSS__</style>
</head>
<body>
<div class="app">

  <aside class="sidebar">
    <div class="sb-logo">
      <strong>Grupo Servopa</strong>
      <span>Observabilidade · __PERIODO__</span>
    </div>

    <!-- Store picker -->
    <div class="sb-picker">
      <div class="picker-btn" onclick="togglePicker()">
        <span class="store-name" id="picker-btn-label">Grupo Servopa</span>
        <span class="arrow">▼</span>
      </div>
      <div class="picker-dropdown" id="picker-dd">
        <div class="picker-search">
          <input id="picker-input" type="text" placeholder="Buscar loja..."
            oninput="filterPicker(this.value)">
        </div>
        <div class="picker-list" id="picker-list"></div>
      </div>
    </div>

    <!-- Area nav -->
    <div class="sb-nav" id="sidebar-nav"></div>
  </aside>

  <div class="main-wrap">
    <div class="main-hdr">
      <h1 id="area-title">Visão Geral</h1>
      <span id="store-sub"></span>
    </div>
    <div id="content"></div>
  </div>

</div>

<script>
const DB = __DB__;
__JS__
</script>
</body>
</html>"""


# ── Generate ──────────────────────────────────────────────────────────────────

def generate_html(data: dict) -> str:
    stores = data["stores"]
    consolidated = calc_consolidated(stores)
    periodo = data.get("periodo", datetime.now().strftime("%Y-%m"))

    db = {"stores": stores, "consolidated": consolidated}
    db_json = json.dumps(db, ensure_ascii=False)

    return (HTML_TEMPLATE
            .replace("__CSS__", CSS)
            .replace("__PERIODO__", periodo)
            .replace("__DB__", db_json)
            .replace("__JS__", JS))


def main():
    data = load_data()
    if not data:
        print("Nenhum dado em logs/stores_data.json")
        print("Execute: python3 mocks/gerar_mock.py")
        return

    html = generate_html(data)
    OUTPUT_PATH.write_text(html, encoding="utf-8")

    stores = data["stores"]
    total_v = sum(s["vendas"]["total_mes"] for s in stores)
    total_f = sum(s["financeiro"]["faturamento"] for s in stores)
    print(f"Dashboard: {OUTPUT_PATH}")
    print(f"  Lojas:        {len(stores)}")
    print(f"  Total vendas: {total_v:,} un".replace(",", "."))
    print(f"  Faturamento:  R$ {total_f:,.0f}".replace(",", "."))


if __name__ == "__main__":
    main()
