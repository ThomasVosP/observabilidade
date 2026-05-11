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
:root{
  --ok:#30d158; --warn:#ff9f0a; --err:#ff453a; --unk:#86868b;
  --bg:#fbfbfd; --card:#ffffff; --border:#ececef; --border-soft:#f5f5f7;
  --text:#1d1d1f; --muted:#86868b; --muted-2:#6e6e73;
  --accent:#0071e3; --accent-soft:#0071e314;
  --sb:#1d1d1f; --sb-2:#2a2a2c; --sbtext:#a1a1a6; --sbact:#0071e3;
  --r-sm:8px; --r-md:12px; --r-lg:16px;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  font-family:-apple-system,"SF Pro Text",BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  font-size:14px;line-height:1.5;color:var(--text);background:var(--bg);
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
  letter-spacing:-.005em;overflow:hidden;
}

/* App shell */
.app{display:grid;grid-template-columns:248px 1fr;height:100vh}

/* ─────────── Sidebar ─────────── */
.sidebar{background:var(--sb);display:flex;flex-direction:column;overflow:hidden}

.sb-logo{padding:22px 20px 16px;border-bottom:1px solid #ffffff0d}
.sb-logo strong{display:block;color:#fff;font-size:.95rem;font-weight:600;letter-spacing:-.015em}
.sb-logo span{display:block;font-size:.72rem;color:#86868b;margin-top:2px;font-weight:400}

/* Store picker */
.sb-picker{padding:14px 14px 12px;border-bottom:1px solid #ffffff0d;position:relative}
.picker-btn{width:100%;background:#ffffff0e;border:1px solid #ffffff14;
  border-radius:var(--r-sm);color:#fff;font-size:.82rem;font-weight:500;
  padding:9px 12px;display:flex;align-items:center;justify-content:space-between;
  cursor:pointer;gap:6px;text-align:left;transition:background .15s,border-color .15s;
  font-family:inherit;letter-spacing:-.005em}
.picker-btn:hover{background:#ffffff18;border-color:#ffffff22}
.picker-btn .store-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.picker-btn .arrow{opacity:.45;font-size:.65rem;flex-shrink:0}
.picker-dropdown{position:absolute;left:14px;right:14px;top:calc(100% - 4px);
  background:#2a2a2c;border:1px solid #ffffff14;border-radius:var(--r-md);
  box-shadow:0 12px 32px rgba(0,0,0,.5),0 0 0 1px rgba(255,255,255,.04);
  z-index:100;display:none;max-height:340px;overflow:hidden;flex-direction:column}
.picker-dropdown.open{display:flex}
.picker-search{padding:10px 12px;border-bottom:1px solid #ffffff0d;flex-shrink:0}
.picker-search input{width:100%;background:#ffffff10;border:none;border-radius:6px;
  color:#fff;font-size:.8rem;padding:7px 10px;outline:none;font-family:inherit}
.picker-search input::placeholder{color:#86868b}
.picker-search input:focus{background:#ffffff18}
.picker-list{overflow-y:auto;flex:1;padding:6px 0}
.picker-list::-webkit-scrollbar{width:0}
.picker-group{padding:10px 14px 4px;font-size:.66rem;font-weight:600;
  color:#86868b;text-transform:uppercase;letter-spacing:.06em}
.picker-item{padding:8px 14px 8px 22px;font-size:.82rem;color:var(--sbtext);
  cursor:pointer;display:flex;align-items:center;gap:8px;transition:background .12s}
.picker-item:hover{background:#ffffff0d;color:#fff}
.picker-item.active{color:#fff;font-weight:500;background:#ffffff10}
.picker-item.grupo{padding-left:14px;font-weight:500;color:#fff;
  border-bottom:1px solid #ffffff0d;margin-bottom:4px}

/* Area nav */
.sb-nav{flex:1;overflow-y:auto;padding:14px 10px}
.sb-nav::-webkit-scrollbar{width:0}
.nav-area{display:flex;align-items:center;gap:12px;padding:11px 14px;
  font-size:.85rem;font-weight:500;color:var(--sbtext);cursor:pointer;
  border-radius:var(--r-sm);transition:background .15s,color .15s;user-select:none;
  margin-bottom:2px;letter-spacing:-.005em}
.nav-area:hover{background:#ffffff0d;color:#fff}
.nav-area.active{background:var(--sbact);color:#fff;font-weight:500}
.nav-area .ico{font-size:1rem;width:18px;text-align:center;flex-shrink:0;opacity:.9}

/* ─────────── Main ─────────── */
.main-wrap{display:flex;flex-direction:column;overflow:hidden;background:var(--bg)}
.main-hdr{background:transparent;border-bottom:1px solid var(--border);
  padding:28px 40px 22px;flex-shrink:0}
#area-title{font-size:1.55rem;font-weight:600;letter-spacing:-.022em;color:var(--text)}
#store-sub{display:block;font-size:.82rem;color:var(--muted);margin-top:4px;font-weight:400}

#content{flex:1;overflow-y:auto;padding:32px 40px 48px}
#content::-webkit-scrollbar{width:8px}
#content::-webkit-scrollbar-thumb{background:#d2d2d7;border-radius:4px}
#content::-webkit-scrollbar-thumb:hover{background:#a1a1a6}

/* ─────────── KPI cards ─────────── */
.kpis{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));
  gap:14px;margin-bottom:24px}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:var(--r-lg);
  padding:22px 24px;transition:border-color .15s}
.kpi:hover{border-color:#d2d2d7}
.kv{font-size:1.95rem;font-weight:600;line-height:1.15;letter-spacing:-.025em;
  color:var(--text)}
.ku{font-size:.95rem;font-weight:400;color:var(--muted);margin-left:2px}
.kl{font-size:.78rem;color:var(--muted);margin-top:6px;font-weight:500;letter-spacing:-.003em}
.ks{font-size:.74rem;color:var(--muted-2);margin-top:4px;font-weight:400}
.kpi.ok .kv{color:var(--ok)} .kpi.warn .kv{color:var(--warn)} .kpi.err .kv{color:var(--err)}

/* Section title */
.sec-title{font-size:1.05rem;font-weight:600;color:var(--text);letter-spacing:-.015em;
  margin:36px 0 16px;text-transform:none}

/* ─────────── Chart cards ─────────── */
.charts-row{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}
.ccard{background:var(--card);border:1px solid var(--border);border-radius:var(--r-lg);
  padding:26px 28px}
.ccard h3{font-size:.95rem;font-weight:600;color:var(--text);letter-spacing:-.012em;
  margin-bottom:22px;text-transform:none}
.ccard-full{grid-column:1/-1}

/* ─────────── Tables ─────────── */
.rtable{width:100%;border-collapse:collapse;font-size:.85rem}
.rtable th{padding:12px 14px;text-align:left;font-size:.72rem;color:var(--muted);
  font-weight:500;letter-spacing:.02em;border-bottom:1px solid var(--border);
  text-transform:uppercase}
.rtable td{padding:14px;border-bottom:1px solid var(--border-soft);color:var(--text)}
.rtable tr:last-child td{border-bottom:none}
.rtable tr:hover td{background:#fafafa}

.heat-table{width:100%;border-collapse:collapse;font-size:.86rem;margin-top:14px}
.heat-table th{padding:12px 16px;text-align:left;font-size:.72rem;color:var(--muted);
  font-weight:500;letter-spacing:.02em;border-bottom:1px solid var(--border);
  text-transform:uppercase}
.heat-table td{padding:14px 16px;border-bottom:1px solid var(--border-soft)}
.heat-table tr:last-child td{border-bottom:none}
.heat-table tr:hover td{background:#fafafa}
.brand-link{color:var(--text);text-decoration:none;font-weight:500;cursor:pointer;
  transition:color .15s}
.brand-link:hover{color:var(--accent)}

/* ─────────── Status indicators ─────────── */
.badge{display:inline-flex;align-items:center;gap:5px;font-size:.74rem;font-weight:500;
  padding:3px 10px;border-radius:20px;letter-spacing:-.005em}
.badge.ok{background:#30d15815;color:#1f8a3a}
.badge.warn{background:#ff9f0a15;color:#b86b00}
.badge.err{background:#ff453a15;color:#c8362e}

.ok-badge{color:var(--ok);font-weight:600}
.warn-badge{color:var(--warn);font-weight:600}
.err-badge{color:var(--err);font-weight:600}

.nav-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.dot-ok{background:var(--ok)} .dot-warn{background:var(--warn)} .dot-err{background:var(--err)}

/* ─────────── Alerts ─────────── */
.alert{padding:14px 18px;border-radius:var(--r-md);font-size:.85rem;font-weight:500;
  margin-bottom:20px;letter-spacing:-.005em;border:1px solid transparent}
.alert.ok{background:#30d15810;color:#1f8a3a;border-color:#30d15825}
.alert.warn{background:#ff9f0a10;color:#b86b00;border-color:#ff9f0a25}

/* ─────────── Responsive ─────────── */
@media(max-width:980px){
  .app{grid-template-columns:1fr}
  .sidebar{display:none}
  .charts-row{grid-template-columns:1fr}
  .main-hdr,#content{padding-left:24px;padding-right:24px}
}
"""


# ── JavaScript SPA ────────────────────────────────────────────────────────────

JS = r"""
// Apple System Colors palette — soft, harmonious
const COLORS=['#0071e3','#5e5ce6','#34c759','#ff9f0a','#ff375f','#64d2ff','#bf5af2','#ffd60a'];
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
              backgroundColor:['#30d158','#86868b','#ff453a'],borderWidth:0}]},
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
            backgroundColor:['#0071e3','#5e5ce6','#34c759'],borderWidth:0}]},
        options:{cutout:'60%',plugins:{legend:{position:'bottom',labels:{boxWidth:12,padding:14,font:{size:12}}}}}});
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
            backgroundColor:['#30d158','#86868b','#ff453a'],borderWidth:0}]},
        options:{cutout:'60%',plugins:{legend:{position:'bottom',labels:{boxWidth:12}}}}});
      mkChart('ch-cx-etapas',{type:'bar',
        data:{labels:['Geral','Negociação','Test Drive','Entrega'],
          datasets:[{data:[cx.nps_geral,cx.nps_negociacao,cx.nps_test_drive,cx.nps_entrega],
            backgroundColor:['#0071e3','#5e5ce6','#34c759','#ff9f0a'],borderWidth:0,borderRadius:6}]},
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
            backgroundColor:['#0071e3','#5e5ce6'],borderWidth:0}]},
        options:{cutout:'55%',plugins:{legend:{position:'bottom',labels:{boxWidth:12,padding:14,font:{size:12}}}}}});
      mkChart('ch-pv-os',{type:'bar',
        data:{labels:['OS Abertas','OS Fechadas'],
          datasets:[{data:[pv.os_abertas,pv.os_fechadas_mes],
            backgroundColor:['#ff9f0a','#30d158'],borderWidth:0,borderRadius:6}]},
        options:{plugins:{legend:{display:false}},
          scales:{x:{grid:{display:false}},y:{grid:{color:'#f1f5f9'}}}}});
      break;}
    case'financeiro':{
      const f=s.financeiro;
      mkChart('ch-fin',{type:'bar',
        data:{labels:['Faturamento','Custo Total','Margem Bruta'],
          datasets:[{data:[f.faturamento,f.custo,f.margem],
            backgroundColor:['#0071e3','#ff453a','#30d158'],borderWidth:0,borderRadius:6}]},
        options:{plugins:{legend:{display:false}},
          scales:{x:{grid:{display:false}},
            y:{grid:{color:'#f1f5f9'},
              ticks:{callback:v=>v>=1e6?'R$'+(v/1e6).toFixed(1)+'M':v>=1e3?'R$'+(v/1e3).toFixed(0)+'K':'R$'+v}}}}});
      break;}
  }
}

// Chart.js global defaults — Apple-style
Chart.defaults.font.family='-apple-system,"SF Pro Text",BlinkMacSystemFont,sans-serif';
Chart.defaults.font.size=12;
Chart.defaults.color='#86868b';
Chart.defaults.borderColor='#f5f5f7';
Chart.defaults.plugins.tooltip.backgroundColor='#1d1d1f';
Chart.defaults.plugins.tooltip.padding=10;
Chart.defaults.plugins.tooltip.cornerRadius=8;
Chart.defaults.plugins.tooltip.titleFont={weight:'600'};
Chart.defaults.plugins.tooltip.bodyFont={weight:'400'};
Chart.defaults.plugins.legend.labels.padding=14;

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
