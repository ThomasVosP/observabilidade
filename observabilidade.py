#!/usr/bin/env python3
"""
observabilidade.py — Dashboard de observabilidade dos pipelines CX/CS
Grupo Servopa | Todas as marcas

Uso:
  python mocks/gerar_mock.py   # gera dados mock (primeiro uso)
  python observabilidade.py    # gera dashboard_observabilidade.html
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

LOGS_PATH = Path(__file__).parent / "logs" / "pipeline_runs.json"
OUTPUT_PATH = Path(__file__).parent / "dashboard_observabilidade.html"

FRESHNESS_WARN_H = 25
FRESHNESS_ERR_H  = 49

BRAND_ORDER = [
    "BYD", "VW", "Audi", "Volvo", "Hyundai", "Honda",
    "Peugeot", "Citroën", "GAC", "Harley-Davidson", "Triumph", "Consórcio",
]

CHART_COLORS = [
    "#1a56db", "#7c3aed", "#0891b2", "#16a34a",
    "#ea580c", "#dc2626", "#f59e0b", "#0d9488",
]


# ---------------------------------------------------------------------------
# Data loading & metrics
# ---------------------------------------------------------------------------

def load_runs() -> list:
    if not LOGS_PATH.exists():
        return []
    with open(LOGS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _dt(s):
    return datetime.fromisoformat(s) if s else None


def calc_brand_status(runs: list, now: datetime) -> dict:
    by_brand = defaultdict(list)
    for r in runs:
        by_brand[r["marca"]].append(r)

    result = {}
    for marca, brand_runs in by_brand.items():
        brand_runs.sort(key=lambda x: x["started_at"], reverse=True)
        last = brand_runs[0]
        last_dt = _dt(last["started_at"])
        hours_since = (now - last_dt).total_seconds() / 3600

        if last["status"] == "error" or hours_since > FRESHNESS_ERR_H:
            status = "error"
        elif last["status"] == "warning" or hours_since > FRESHNESS_WARN_H:
            status = "warning"
        else:
            status = "success"

        # Latest status per pipeline
        by_pipe = defaultdict(list)
        for r in brand_runs:
            by_pipe[r["pipeline"]].append(r)
        pipe_status = {p: runs_p[0]["status"] for p, runs_p in by_pipe.items()}

        cutoff_24h = now - timedelta(hours=24)
        records_24h = sum(
            r["records_loaded"]
            for r in brand_runs
            if _dt(r["started_at"]) > cutoff_24h and r["status"] == "success"
        )

        runs_ok_30d = [r for r in brand_runs if r["status"] == "success"]
        success_rate = round(len(runs_ok_30d) / len(brand_runs) * 100, 1) if brand_runs else 0

        result[marca] = {
            "status": status,
            "last_run_at": last["started_at"],
            "last_status": last["status"],
            "hours_since": round(hours_since, 1),
            "pipelines": pipe_status,
            "records_24h": records_24h,
            "total_runs_30d": len(brand_runs),
            "success_rate_30d": success_rate,
        }
    return result


def calc_kpis(runs: list, brand_status: dict, now: datetime) -> dict:
    cutoff_24h = now - timedelta(hours=24)
    runs_24h = [r for r in runs if _dt(r["started_at"]) > cutoff_24h]

    healthy = sum(1 for v in brand_status.values() if v["status"] == "success")
    warning = sum(1 for v in brand_status.values() if v["status"] == "warning")
    error   = sum(1 for v in brand_status.values() if v["status"] == "error")

    success_24h = [r for r in runs_24h if r["status"] == "success"]
    rate_24h = round(len(success_24h) / len(runs_24h) * 100, 1) if runs_24h else 0

    total_pipelines = sum(len(v["pipelines"]) for v in brand_status.values())

    return {
        "total_brands":      len(brand_status),
        "total_pipelines":   total_pipelines,
        "healthy_brands":    healthy,
        "warning_brands":    warning,
        "error_brands":      error,
        "runs_24h":          len(runs_24h),
        "success_rate_24h":  rate_24h,
        "records_24h":       sum(r["records_loaded"] for r in success_24h),
        "records_7d":        sum(
            r["records_loaded"] for r in runs
            if _dt(r["started_at"]) > now - timedelta(days=7) and r["status"] == "success"
        ),
    }


def calc_volume_series(runs: list, now: datetime, days: int = 7) -> dict:
    cutoff = now - timedelta(days=days)
    recent = [r for r in runs if _dt(r["started_at"]) > cutoff and r["status"] == "success"]

    by_date_brand = defaultdict(lambda: defaultdict(int))
    for r in recent:
        date = _dt(r["started_at"]).strftime("%Y-%m-%d")
        by_date_brand[date][r["marca"]] += r["records_loaded"]

    dates = [
        (now - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days, -1, -1)
    ]

    brand_totals = defaultdict(int)
    for dd in by_date_brand.values():
        for marca, vol in dd.items():
            brand_totals[marca] += vol

    top_brands = sorted(brand_totals, key=lambda m: brand_totals[m], reverse=True)[:6]

    datasets = [
        {"label": m, "data": [by_date_brand[d].get(m, 0) for d in dates]}
        for m in top_brands
    ]
    return {"labels": dates, "datasets": datasets}


def calc_error_log(runs: list, now: datetime, limit: int = 20) -> list:
    cutoff = now - timedelta(days=7)
    errors = [
        r for r in runs
        if r["status"] in ("error", "warning") and _dt(r["started_at"]) > cutoff
    ]
    errors.sort(key=lambda x: x["started_at"], reverse=True)
    return errors[:limit]


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def _fmt_dt(s) -> str:
    if not s:
        return "—"
    return _dt(s).strftime("%d/%m %H:%M")


def _fmt_since(h) -> str:
    if h is None:
        return "—"
    if h < 1:
        return f"{int(h * 60)}min atrás"
    if h < 24:
        return f"{h:.1f}h atrás"
    return f"{h / 24:.1f}d atrás"


def _fmt_num(n: int) -> str:
    return f"{n:,}".replace(",", ".")


STATUS_CSS   = {"success": "ok",   "warning": "warn", "error": "err", "unknown": "unk"}
STATUS_ICON  = {"success": "✓",    "warning": "⚠",    "error": "✗",   "unknown": "?"}
STATUS_LABEL = {"success": "Saudável", "warning": "Alerta", "error": "Erro", "unknown": "?"}


def _brand_cards_html(brand_status: dict) -> str:
    parts = []
    for marca in BRAND_ORDER:
        if marca not in brand_status:
            continue
        b = brand_status[marca]
        css   = STATUS_CSS.get(b["status"], "unk")
        icon  = STATUS_ICON.get(b["status"], "?")
        label = STATUS_LABEL.get(b["status"], "?")

        pipes = "".join(
            f'<span class="pipe {STATUS_CSS.get(s, "unk")}">{p}</span>'
            for p, s in b["pipelines"].items()
        )
        records = _fmt_num(b["records_24h"])
        rate    = b["success_rate_30d"]

        parts.append(f"""
  <div class="brand {css}">
    <div class="brand-top">
      <span class="brand-name">{marca}</span>
      <span class="sbadge {css}">{icon} {label}</span>
    </div>
    <div class="brand-meta">
      <span>Último run: {_fmt_dt(b['last_run_at'])}</span>
      <span>{_fmt_since(b['hours_since'])}</span>
    </div>
    <div class="brand-rec">{records} reg. hoje &nbsp;·&nbsp; {rate}% sucesso (30d)</div>
    <div class="brand-pipes">{pipes}</div>
  </div>""")

    return "\n".join(parts)


def _error_rows_html(error_log: list) -> str:
    if not error_log:
        return '<tr><td colspan="6" class="no-err">Nenhum erro nos últimos 7 dias ✓</td></tr>'

    rows = []
    for e in error_log[:15]:
        css = "rerr" if e["status"] == "error" else "rwarn"
        icon = STATUS_ICON.get(e["status"], "?")
        msg  = e.get("error_message") or "—"
        rows.append(f"""  <tr class="{css}">
    <td>{_fmt_dt(e['started_at'])}</td>
    <td>{e['marca']}</td>
    <td>{e['pipeline']}</td>
    <td>{icon} {e['status'].upper()}</td>
    <td class="msg">{msg}</td>
    <td>{_fmt_num(e['records_extracted'])}</td>
  </tr>""")

    return "\n".join(rows)


def generate_html(db: dict) -> str:
    kpis        = db["kpis"]
    brand_status = db["brands"]
    now_str     = _dt(db["generated_at"]).strftime("%d/%m/%Y às %H:%M")
    db_json     = json.dumps(db, ensure_ascii=False)

    # Health header badge
    if kpis["error_brands"] > 0:
        hc = "#ef4444"
        ht = f"{kpis['error_brands']} marca(s) com erro"
    elif kpis["warning_brands"] > 0:
        hc = "#f59e0b"
        ht = f"{kpis['warning_brands']} marca(s) com alerta"
    else:
        hc = "#22c55e"
        ht = "Todos os pipelines saudáveis"

    brand_cards = _brand_cards_html(brand_status)
    error_rows  = _error_rows_html(db["error_log"])

    # KPI rate color
    rate = kpis["success_rate_24h"]
    rate_cls = "ok" if rate >= 90 else "warn" if rate >= 75 else "err"

    # Chart colors as JS array literal
    colors_js = "[" + ", ".join(f'"{c}"' for c in CHART_COLORS) + "]"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Observabilidade — Grupo Servopa</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{
  --ok:#22c55e; --warn:#f59e0b; --err:#ef4444; --unk:#94a3b8;
  --bg:#f1f5f9; --card:#fff; --border:#e2e8f0;
  --text:#1e293b; --muted:#64748b; --hdr:#0f172a;
  --rad:10px;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text)}}

/* Header */
header{{background:var(--hdr);color:#fff;padding:18px 32px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}}
.h-title{{font-size:1.15rem;font-weight:700;letter-spacing:-.02em}}
.h-sub{{color:#94a3b8;font-size:.82rem;flex:1}}
.hbadge{{padding:4px 14px;border-radius:20px;font-size:.78rem;font-weight:600;
  background:{hc}22;color:{hc};border:1px solid {hc}55}}

/* Layout */
main{{max-width:1440px;margin:0 auto;padding:24px 32px}}
section{{margin-bottom:32px}}
h2{{font-size:.78rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px}}

/* KPIs */
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:12px}}
.kpi{{background:var(--card);border:1px solid var(--border);border-radius:var(--rad);padding:16px 18px}}
.kv{{font-size:1.85rem;font-weight:800;line-height:1}}
.kl{{font-size:.75rem;color:var(--muted);margin-top:3px}}
.kpi.ok .kv{{color:var(--ok)}} .kpi.warn .kv{{color:var(--warn)}} .kpi.err .kv{{color:var(--err)}}

/* Brand grid */
.brands{{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:14px}}
.brand{{background:var(--card);border:1px solid var(--border);border-radius:var(--rad);
  padding:15px;border-left:4px solid var(--border);transition:box-shadow .15s}}
.brand:hover{{box-shadow:0 4px 14px rgba(0,0,0,.09)}}
.brand.ok{{border-left-color:var(--ok)}} .brand.warn{{border-left-color:var(--warn)}} .brand.err{{border-left-color:var(--err)}}
.brand-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}}
.brand-name{{font-weight:700;font-size:.93rem}}
.sbadge{{font-size:.7rem;font-weight:600;padding:2px 8px;border-radius:10px}}
.sbadge.ok{{background:#dcfce7;color:#15803d}} .sbadge.warn{{background:#fef9c3;color:#854d0e}} .sbadge.err{{background:#fee2e2;color:#b91c1c}}
.brand-meta{{font-size:.72rem;color:var(--muted);display:flex;justify-content:space-between;margin-bottom:5px}}
.brand-rec{{font-size:.78rem;font-weight:600;margin-bottom:8px;color:var(--text)}}
.brand-pipes{{display:flex;gap:4px;flex-wrap:wrap}}
.pipe{{font-size:.67rem;padding:2px 7px;border-radius:5px;font-weight:600}}
.pipe.ok{{background:#dcfce7;color:#15803d}} .pipe.warn{{background:#fef9c3;color:#854d0e}} .pipe.err{{background:#fee2e2;color:#b91c1c}}

/* Charts row */
.charts-row{{display:grid;grid-template-columns:2fr 1fr;gap:18px}}
.ccard{{background:var(--card);border:1px solid var(--border);border-radius:var(--rad);padding:20px}}
.ccard h2{{margin-bottom:16px}}

/* Error table */
.etable-wrap{{background:var(--card);border:1px solid var(--border);border-radius:var(--rad);overflow:hidden}}
.etable-hdr{{padding:14px 18px;border-bottom:1px solid var(--border)}}
table{{width:100%;border-collapse:collapse;font-size:.8rem}}
th{{padding:8px 12px;text-align:left;font-size:.7rem;color:var(--muted);text-transform:uppercase;
  letter-spacing:.04em;background:#f8fafc;border-bottom:1px solid var(--border)}}
td{{padding:9px 12px;border-bottom:1px solid #f1f5f9;vertical-align:top}}
tr:last-child td{{border-bottom:none}}
tr.rerr td:first-child{{border-left:3px solid var(--err)}} tr.rwarn td:first-child{{border-left:3px solid var(--warn)}}
.msg{{max-width:340px;color:var(--muted)}}
.no-err{{text-align:center;padding:24px;color:var(--ok);font-weight:600}}

/* Footer */
footer{{text-align:center;padding:24px;font-size:.75rem;color:var(--muted)}}

@media(max-width:768px){{
  main{{padding:16px}} .charts-row{{grid-template-columns:1fr}}
  header{{padding:14px 16px}}
}}
</style>
</head>
<body>

<header>
  <div>
    <div class="h-title">Observabilidade de Pipelines</div>
    <div class="h-sub">Grupo Servopa &nbsp;·&nbsp; Atualizado em {now_str}</div>
  </div>
  <div class="hbadge">{ht}</div>
</header>

<main>

  <section>
    <h2>Resumo Geral</h2>
    <div class="kpis">
      <div class="kpi"><div class="kv">{kpis['total_brands']}</div><div class="kl">Marcas monitoradas</div></div>
      <div class="kpi ok"><div class="kv">{kpis['healthy_brands']}</div><div class="kl">Saudáveis</div></div>
      <div class="kpi {'warn' if kpis['warning_brands'] else ''}"><div class="kv">{kpis['warning_brands']}</div><div class="kl">Com alerta</div></div>
      <div class="kpi {'err' if kpis['error_brands'] else ''}"><div class="kv">{kpis['error_brands']}</div><div class="kl">Com erro</div></div>
      <div class="kpi"><div class="kv">{kpis['runs_24h']}</div><div class="kl">Execuções (24h)</div></div>
      <div class="kpi {rate_cls}"><div class="kv">{kpis['success_rate_24h']}%</div><div class="kl">Taxa de sucesso (24h)</div></div>
      <div class="kpi"><div class="kv">{_fmt_num(kpis['records_24h'])}</div><div class="kl">Registros hoje</div></div>
      <div class="kpi"><div class="kv">{_fmt_num(kpis['records_7d'])}</div><div class="kl">Registros (7 dias)</div></div>
    </div>
  </section>

  <section>
    <h2>Status por Marca</h2>
    <div class="brands">
{brand_cards}
    </div>
  </section>

  <section>
    <div class="charts-row">
      <div class="ccard">
        <h2>Volume de Registros — últimos 7 dias</h2>
        <canvas id="volChart" height="220"></canvas>
      </div>
      <div class="ccard">
        <h2>Saúde das Marcas</h2>
        <canvas id="statusChart" height="220"></canvas>
      </div>
    </div>
  </section>

  <section>
    <div class="etable-wrap">
      <div class="etable-hdr"><h2 style="margin:0">Erros e Alertas — últimos 7 dias</h2></div>
      <table>
        <thead>
          <tr><th>Horário</th><th>Marca</th><th>Pipeline</th><th>Status</th><th>Mensagem</th><th>Registros</th></tr>
        </thead>
        <tbody>
{error_rows}
        </tbody>
      </table>
    </div>
  </section>

</main>

<footer>Grupo Servopa &nbsp;·&nbsp; Sistema de Observabilidade CX/CS &nbsp;·&nbsp; {now_str}</footer>

<script>
const DB = {db_json};
const COLORS = {colors_js};

// Volume stacked bar
(function() {{
  const ctx = document.getElementById('volChart').getContext('2d');
  const vs = DB.volume_series;
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: vs.labels.map(d => {{ const [,m,day] = d.split('-'); return day+'/'+m; }}),
      datasets: vs.datasets.map((ds, i) => ({{
        label: ds.label, data: ds.data,
        backgroundColor: COLORS[i % COLORS.length] + 'cc',
        borderColor: COLORS[i % COLORS.length], borderWidth: 1,
      }}))
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 12, font: {{ size: 11 }} }} }} }},
      scales: {{
        x: {{ stacked: true, grid: {{ display: false }} }},
        y: {{ stacked: true, grid: {{ color: '#f1f5f9' }}, ticks: {{ font: {{ size: 11 }} }} }}
      }}
    }}
  }});
}})();

// Status donut
(function() {{
  const ctx = document.getElementById('statusChart').getContext('2d');
  const k = DB.kpis;
  new Chart(ctx, {{
    type: 'doughnut',
    data: {{
      labels: ['Saudável', 'Alerta', 'Erro'],
      datasets: [{{ data: [k.healthy_brands, k.warning_brands, k.error_brands],
        backgroundColor: ['#22c55e', '#f59e0b', '#ef4444'], borderWidth: 0 }}]
    }},
    options: {{
      responsive: true, cutout: '68%',
      plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 12, font: {{ size: 11 }} }} }} }}
    }}
  }});
}})();
</script>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    now = datetime.now()
    runs = load_runs()

    if not runs:
        print("Nenhum dado em logs/pipeline_runs.json.")
        print("Execute primeiro: python mocks/gerar_mock.py")
        return

    brand_status = calc_brand_status(runs, now)
    kpis         = calc_kpis(runs, brand_status, now)
    volume_series = calc_volume_series(runs, now)
    error_log    = calc_error_log(runs, now)

    db = {
        "generated_at": now.isoformat(),
        "kpis": kpis,
        "brands": brand_status,
        "volume_series": volume_series,
        "error_log": error_log,
    }

    html = generate_html(db)
    OUTPUT_PATH.write_text(html, encoding="utf-8")

    print(f"Dashboard gerado: {OUTPUT_PATH}")
    print(f"  Marcas: {kpis['total_brands']}  |  "
          f"Saudáveis: {kpis['healthy_brands']}  |  "
          f"Alertas: {kpis['warning_brands']}  |  "
          f"Erros: {kpis['error_brands']}")
    print(f"  Taxa de sucesso (24h): {kpis['success_rate_24h']}%")
    print(f"  Registros hoje: {_fmt_num(kpis['records_24h'])}")


if __name__ == "__main__":
    main()
