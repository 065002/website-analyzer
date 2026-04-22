"""
app.py  ·  WebScan Pro — Website & Competitor Analysis Dashboard
Bug fixes: PLOTLY_LAYOUT conflict resolved by using a helper function instead of **unpacking.
New: 3D charts, backlink signals, AI visibility scoring.
"""

import json
import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="WebScan Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

.stApp {
    background: #060910;
    background-image:
        radial-gradient(ellipse 90% 60% at 50% -5%,  rgba(56,189,248,0.07) 0%, transparent 55%),
        radial-gradient(ellipse 60% 50% at 95% 85%,  rgba(139,92,246,0.06) 0%, transparent 50%),
        radial-gradient(ellipse 50% 40% at 5%  70%,  rgba(52,211,153,0.04) 0%, transparent 45%);
    color: #e2e8f0;
    min-height: 100vh;
}

@keyframes gradientShift {
    0%,100% { background-position: 0% 50%; }
    50%      { background-position: 100% 50%; }
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.6; }
}

/* Hero */
.hero-wrap { text-align:center; padding:2.5rem 1rem 1.5rem; animation:fadeUp .6s ease both; }
.hero-eyebrow {
    font-family:'DM Mono',monospace; font-size:0.68rem; letter-spacing:.28em;
    text-transform:uppercase; color:#38bdf8; margin-bottom:.8rem; opacity:.75;
}
.hero-title {
    font-size:clamp(2.2rem,5vw,3.8rem); font-weight:900; line-height:1.05;
    background:linear-gradient(135deg,#e0f2fe 0%,#38bdf8 30%,#818cf8 60%,#c084fc 100%);
    background-size:200% 200%; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    animation:gradientShift 6s ease infinite; margin-bottom:.6rem;
}
.hero-sub { font-size:.95rem; color:#4b5563; max-width:500px; margin:0 auto 1.5rem; line-height:1.6; }

/* Input shell */
.input-shell {
    background:linear-gradient(135deg,rgba(15,23,42,.92),rgba(30,41,59,.88));
    border:1px solid rgba(56,189,248,.18); border-radius:20px;
    padding:1.5rem 1.75rem; margin-bottom:1.5rem;
    backdrop-filter:blur(16px);
}
.input-label {
    font-family:'DM Mono',monospace; font-size:.68rem; letter-spacing:.16em;
    text-transform:uppercase; color:#38bdf8; margin-bottom:.4rem;
}

/* Streamlit overrides */
div[data-testid="stTextInput"] input {
    background:rgba(15,23,42,.85) !important; border:1px solid rgba(100,116,139,.28) !important;
    color:#e2e8f0 !important; border-radius:10px !important;
    font-family:'DM Mono',monospace !important; font-size:.88rem !important;
    padding:.6rem .95rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color:rgba(56,189,248,.55) !important;
    box-shadow:0 0 0 3px rgba(56,189,248,.08) !important;
}
div[data-testid="stButton"] > button {
    background:linear-gradient(135deg,#0ea5e9,#6366f1) !important;
    color:#fff !important; font-weight:700 !important; border:none !important;
    border-radius:10px !important; padding:.6rem 1.4rem !important;
    font-family:'Outfit',sans-serif !important; font-size:.9rem !important;
    width:100% !important; letter-spacing:.02em !important;
}
div[data-testid="stButton"] > button:hover { opacity:.88 !important; }

/* Score cards */
.score-card {
    background:linear-gradient(135deg,rgba(15,23,42,.95),rgba(30,41,59,.88));
    border:1px solid rgba(100,116,139,.18); border-radius:14px;
    padding:1.1rem .9rem; text-align:center; position:relative; overflow:hidden;
    transition:transform .2s,border-color .2s;
}
.score-card:hover { transform:translateY(-3px); border-color:rgba(56,189,248,.3); }
.score-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:var(--accent,linear-gradient(90deg,#38bdf8,#818cf8));
}
.score-num  { font-family:'DM Mono',monospace; font-size:2.4rem; font-weight:700; line-height:1; color:var(--score-color,#e2e8f0); }
.score-lbl  { font-size:.65rem; letter-spacing:.13em; text-transform:uppercase; color:#475569; margin-top:.35rem; font-weight:600; }
.score-sub  { font-size:.74rem; color:#64748b; margin-top:.18rem; font-family:'DM Mono',monospace; }
.score-good { --score-color:#34d399; }
.score-mid  { --score-color:#fbbf24; }
.score-bad  { --score-color:#f87171; }

/* Stat pills */
.stat-row   { display:flex; gap:.4rem; flex-wrap:wrap; margin:.4rem 0; }
.stat-pill  {
    background:rgba(30,41,59,.75); border:1px solid rgba(100,116,139,.18);
    border-radius:999px; padding:3px 11px; font-size:.73rem;
    font-family:'DM Mono',monospace; color:#94a3b8;
}
.stat-pill span { color:#e2e8f0; font-weight:600; }

/* Section headers */
.sec-head {
    font-size:.68rem; font-family:'DM Mono',monospace; letter-spacing:.2em;
    text-transform:uppercase; color:#38bdf8; border-left:2px solid #38bdf8;
    padding-left:.55rem; margin:1.4rem 0 .65rem;
}

/* Badges */
.badge {
    display:inline-flex; align-items:center; padding:2px 9px; border-radius:5px;
    font-size:.7rem; font-weight:600; margin:2px; font-family:'DM Mono',monospace; letter-spacing:.04em;
}
.bg-cyan   { background:rgba(56,189,248,.1);  color:#38bdf8;  border:1px solid rgba(56,189,248,.22); }
.bg-purple { background:rgba(139,92,246,.1);  color:#a78bfa;  border:1px solid rgba(139,92,246,.22); }
.bg-green  { background:rgba(52,211,153,.1);  color:#34d399;  border:1px solid rgba(52,211,153,.22); }
.bg-amber  { background:rgba(251,191,36,.1);  color:#fbbf24;  border:1px solid rgba(251,191,36,.22); }
.bg-rose   { background:rgba(248,113,113,.1); color:#f87171;  border:1px solid rgba(248,113,113,.22); }
.bg-slate  { background:rgba(100,116,139,.1); color:#94a3b8;  border:1px solid rgba(100,116,139,.18); }
.bg-teal   { background:rgba(45,212,191,.1);  color:#2dd4bf;  border:1px solid rgba(45,212,191,.22); }

/* Issue / win rows */
.issue-row {
    background:rgba(239,68,68,.05); border-left:3px solid #ef4444;
    border-radius:0 8px 8px 0; padding:.5rem .85rem; margin-bottom:.35rem;
    font-size:.83rem; color:#fca5a5; line-height:1.45;
}
.win-row {
    background:rgba(52,211,153,.05); border-left:3px solid #34d399;
    border-radius:0 8px 8px 0; padding:.5rem .85rem; margin-bottom:.35rem;
    font-size:.83rem; color:#6ee7b7; line-height:1.45;
}

/* Divider */
.divider { border:none; border-top:1px solid rgba(100,116,139,.1); margin:1.25rem 0; }

/* Comparison table */
.comp-table { width:100%; border-collapse:collapse; font-size:.82rem; }
.comp-table th {
    background:rgba(15,23,42,.9); color:#64748b; font-family:'DM Mono',monospace;
    font-size:.66rem; letter-spacing:.1em; text-transform:uppercase;
    padding:.55rem .75rem; text-align:left; border-bottom:1px solid rgba(100,116,139,.14);
}
.comp-table td { padding:.5rem .75rem; border-bottom:1px solid rgba(100,116,139,.07); color:#cbd5e1; }
.comp-table tr:hover td { background:rgba(30,41,59,.45); }
.comp-table .best  { color:#34d399; font-weight:700; }
.comp-table .worst { color:#f87171; }

/* AI visibility card */
.ai-card {
    background:linear-gradient(135deg,rgba(15,23,42,.95),rgba(17,24,39,.9));
    border:1px solid rgba(56,189,248,.15); border-radius:14px; padding:1.2rem;
    position:relative; overflow:hidden;
}
.ai-card::after {
    content:'🤖'; position:absolute; right:1rem; top:50%; transform:translateY(-50%);
    font-size:2.5rem; opacity:.08;
}

/* Backlink card */
.bl-card {
    background:linear-gradient(135deg,rgba(15,23,42,.95),rgba(17,24,39,.9));
    border:1px solid rgba(139,92,246,.15); border-radius:14px; padding:1.2rem;
}

/* Empty state */
.empty-state { text-align:center; padding:3.5rem 1rem; }
.empty-icon  { font-size:3rem; margin-bottom:.85rem; }
.empty-title { font-size:1rem; font-weight:600; color:#475569; margin-bottom:.4rem; }
.empty-desc  { font-size:.83rem; color:#334155; max-width:380px; margin:0 auto; }

.mode-label {
    font-family:'DM Mono',monospace; font-size:.68rem; letter-spacing:.16em;
    text-transform:uppercase; color:#475569; margin-bottom:.35rem;
}
button[data-baseweb="tab"] {
    font-family:'Outfit',sans-serif !important; font-size:.8rem !important;
    font-weight:600 !important; letter-spacing:.03em !important;
}
</style>
""", unsafe_allow_html=True)

from scripts.analyzer import analyze_website
from scripts.competitor_analyzer import run_competitor_analysis
from scripts.extra_checks import check_backlink_profile, check_ai_visibility

# ── Plotly helpers — NO **PLOTLY_LAYOUT unpacking to avoid key conflicts ───────
COLORS = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24", "#f87171", "#fb923c", "#2dd4bf"]

def _base_layout(**overrides):
    """Returns a clean Plotly layout dict. Pass overrides as kwargs — no conflict."""
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, sans-serif", color="#94a3b8", size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            bgcolor="rgba(15,23,42,0.8)",
            bordercolor="rgba(100,116,139,0.2)",
            borderwidth=1,
            font=dict(size=11),
        ),
    )
    layout.update(overrides)
    return layout

def _xy_layout(**overrides):
    """Base layout with x/y grid axes included."""
    layout = _base_layout(**overrides)
    layout["xaxis"] = overrides.get("xaxis", dict(gridcolor="rgba(100,116,139,0.1)", zerolinecolor="rgba(100,116,139,0.12)"))
    layout["yaxis"] = overrides.get("yaxis", dict(gridcolor="rgba(100,116,139,0.1)", zerolinecolor="rgba(100,116,139,0.12)"))
    return layout


def gauge_color(s):
    return "#34d399" if s >= 70 else ("#fbbf24" if s >= 40 else "#f87171")


def score_cls(s):
    return "score-good" if s >= 70 else ("score-mid" if s >= 40 else "score-bad")


def badge(text, kind="cyan"):
    return f'<span class="badge bg-{kind}">{text}</span>'


def tech_badges(items, kind="cyan"):
    if not items:
        return '<span style="color:#334155;font-size:.8rem;">None detected</span>'
    return "".join(badge(i, kind) for i in items)


def render_score_card(value, label, sub="", accent="linear-gradient(90deg,#38bdf8,#818cf8)"):
    cls    = score_cls(int(value)) if isinstance(value, (int, float)) else ""
    sub_html = f'<div class="score-sub">{sub}</div>' if sub else ""
    return f"""<div class="score-card" style="--accent:{accent}">
        <div class="score-num {cls}">{value}</div>
        <div class="score-lbl">{label}</div>{sub_html}</div>"""


# ── Chart builders ─────────────────────────────────────────────────────────────

def make_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 12, "color": "#94a3b8", "family": "Outfit"}},
        number={"font": {"size": 30, "color": color, "family": "DM Mono"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#334155", "tickfont": {"size": 8}},
            "bar":  {"color": color, "thickness": 0.22},
            "bgcolor": "rgba(30,41,59,0.5)",
            "bordercolor": "rgba(100,116,139,0.12)",
            "steps": [
                {"range": [0,  40], "color": "rgba(248,113,113,0.07)"},
                {"range": [40, 70], "color": "rgba(251,191,36,0.07)"},
                {"range": [70,100], "color": "rgba(52,211,153,0.07)"},
            ],
            "threshold": {"line": {"color": color, "width": 2}, "thickness": 0.8, "value": value},
        },
    ))
    fig.update_layout(**_base_layout(margin=dict(l=15, r=15, t=28, b=8), height=195))
    return fig


def make_3d_score_bar(sites):
    """3-D cylinder-style bar for overall scores."""
    domains = [s["domain"] for s in sites]
    scores  = [s.get("overall_score", 0) for s in sites]
    colors  = [gauge_color(s) for s in scores]

    fig = go.Figure()
    for i, (d, sc, c) in enumerate(zip(domains, scores, colors)):
        fig.add_trace(go.Bar(
            name=d, x=[d], y=[sc],
            marker=dict(color=c, line=dict(color=c, width=1),
                        pattern=dict(shape="", solidity=0.85)),
            text=[f"<b>{sc}</b>"], textposition="outside",
            textfont=dict(family="DM Mono", size=14, color="#e2e8f0"),
            width=0.45,
        ))
    fig.update_layout(
        **_xy_layout(
            height=320,
            title=dict(text="Overall Health Scores", font=dict(size=13, color="#64748b"), x=0),
            yaxis=dict(range=[0, 115], gridcolor="rgba(100,116,139,0.1)"),
            showlegend=False,
            margin=dict(l=10, r=20, t=44, b=30),
        )
    )
    return fig
def hex_to_rgba(hex_color, alpha=0.08):
    try:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except:
        return "rgba(100,116,139,0.2)"  

def make_radar(radar_data):
    dims = [d["dimension"] for d in radar_data[0]["dimensions"]]
    fig  = go.Figure()
    for i, site in enumerate(radar_data):
        vals = [d["normalised"] for d in site["dimensions"]] + \
               [site["dimensions"][0]["normalised"]]
        color = COLORS[i % len(COLORS)]
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=dims + [dims[0]],
            fill="toself", name=site["domain"],
            line=dict(color=color, width=2),
            fillcolor=hex_to_rgba(color)
        ))
    fig.update_layout(
        **_base_layout(
            height=400,
            title=dict(text="Capability Radar", font=dict(size=13, color="#64748b"), x=0.5),
            margin=dict(l=20, r=20, t=50, b=20),
        ),
        polar=dict(
            bgcolor="rgba(15,23,42,0.55)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont={"size": 8},
                            gridcolor="rgba(100,116,139,0.14)"),
            angularaxis=dict(tickfont={"size": 10}, gridcolor="rgba(100,116,139,0.1)"),
        ),
    )
    return fig


def make_3d_surface(sites, comparison):
    """3-D surface plot comparing sites across 6 key metrics."""
    metric_keys = [
        "overall_score", "security_score", "structured_data_count",
        "security_headers_found", "word_count", "ssl_days_remaining",
    ]
    metric_labels = ["Overall", "Security", "Struct.Data", "Sec.Headers", "Words", "SSL Days"]

    domains = [s["domain"] for s in sites]
    z_data  = []
    for mk in metric_keys:
        row = []
        for d in domains:
            val = comparison.get(mk, {}).get("values", {}).get(d, 0) or 0
            row.append(val)
        z_data.append(row)

    # Normalise each metric row to 0-100
    for i, row in enumerate(z_data):
        max_v = max(row) if max(row) > 0 else 1
        z_data[i] = [round(v / max_v * 100, 1) for v in row]

    fig = go.Figure(go.Surface(
        z=z_data,
        x=list(range(len(domains))),
        y=list(range(len(metric_labels))),
        colorscale=[
            [0.0, "#0f172a"], [0.3, "#1e3a5f"],
            [0.6, "#0ea5e9"], [0.8, "#818cf8"], [1.0, "#34d399"],
        ],
        showscale=True,
        colorbar=dict(
            thickness=12, len=0.6,
            tickfont=dict(size=9, color="#64748b"),
            title=dict(text="Score", font=dict(size=10, color="#64748b")),
        ),
        opacity=0.88,
        contours=dict(
            x=dict(show=True, color="rgba(255,255,255,0.06)", width=1),
            y=dict(show=True, color="rgba(255,255,255,0.06)", width=1),
            z=dict(show=True, color="rgba(255,255,255,0.04)", width=1),
        ),
       ))

    layout = _base_layout(
        height=440,
        title=dict(text="3D Metric Landscape", font=dict(size=13, color="#64748b"), x=0.5),
        margin=dict(l=10, r=10, t=50, b=10),
    )

    fig.update_layout(**layout)

    return fig
    scene=dict(
            bgcolor="rgba(6,9,16,0.0)",
            xaxis=dict(
                tickvals=list(range(len(domains))), ticktext=domains,
                tickfont=dict(size=9, color="#64748b"),
                gridcolor="rgba(100,116,139,0.12)", zerolinecolor="rgba(100,116,139,0.1)",
                title="",
            ),
            yaxis=dict(
                tickvals=list(range(len(metric_labels))), ticktext=metric_labels,
                tickfont=dict(size=9, color="#64748b"),
                gridcolor="rgba(100,116,139,0.12)", zerolinecolor="rgba(100,116,139,0.1)",
                title="",
            ),
            zaxis=dict(
                range=[0, 110], tickfont=dict(size=8, color="#64748b"),
                gridcolor="rgba(100,116,139,0.12)", title="Score",
                titlefont=dict(size=9, color="#64748b"),
            ),
            camera=dict(eye=dict(x=1.6, y=-1.6, z=1.1)),
        )
    return fig


def make_bar_comparison(comparison, metrics_to_show):
    domains = list(next(iter(comparison.values()))["values"].keys())
    fig = go.Figure()
    for i, domain in enumerate(domains):
        x_labels = [comparison[k]["label"] for k in metrics_to_show]
        y_vals   = [comparison[k]["values"].get(domain, 0) or 0 for k in metrics_to_show]
        fig.add_trace(go.Bar(
            name=domain, x=x_labels, y=y_vals,
            marker_color=COLORS[i % len(COLORS)],
            marker_line_width=0, opacity=0.85,
        ))
    fig.update_layout(
        **_xy_layout(
            barmode="group", height=340,
            title=dict(text="Head-to-Head Metrics", font=dict(size=13, color="#64748b"), x=0),
            bargap=0.22, bargroupgap=0.07,
            margin=dict(l=10, r=10, t=44, b=30),
        )
    )
    return fig


def make_treemap_tech(tech_comparison):
    labels = ["Tech Stack"]; parents = [""]; values = [0]; colors_list = ["#060910"]
    color_map = {
        "frontend": "#38bdf8", "cms": "#a78bfa",
        "analytics": "#34d399", "hosting": "#fbbf24", "cdn": "#fb923c",
    }
    for domain, cats in tech_comparison.items():
        labels.append(domain); parents.append("Tech Stack")
        values.append(0); colors_list.append("#1e293b")
        for cat, items in cats.items():
            if cat == "server" or not items:
                continue
            for item in items:
                labels.append(item); parents.append(domain)
                values.append(1); colors_list.append(color_map.get(cat, "#64748b"))
    if len(labels) <= 2:
        return None
    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents,
        marker=dict(colors=colors_list, line=dict(width=1, color="#060910")),
        textfont=dict(family="Outfit", size=11),
        hovertemplate="<b>%{label}</b><extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(
            height=320,
            title=dict(text="Technology Landscape", font=dict(size=13, color="#64748b"), x=0),
            margin=dict(l=8, r=8, t=40, b=8),
        )
    )
    return fig


def make_seo_hbar(seo_items: dict):
    bar_colors = ["#34d399" if v >= 70 else ("#fbbf24" if v >= 40 else "#f87171") for v in seo_items.values()]
    fig = go.Figure(go.Bar(
        x=list(seo_items.values()), y=list(seo_items.keys()),
        orientation="h",
        marker=dict(color=bar_colors, line_width=0),
        text=[f"{v:.0f}%" for v in seo_items.values()],
        textposition="outside",
        textfont=dict(family="DM Mono", size=10),
    ))
    fig.update_layout(
        **_xy_layout(
            height=290,
            xaxis=dict(range=[0, 125], gridcolor="rgba(100,116,139,0.08)"),
            title=dict(text="SEO Signal Scores", font=dict(size=13, color="#64748b"), x=0),
            margin=dict(l=10, r=60, t=40, b=10),
        )
    )
    return fig


def make_sec_score_bar(score: int, color: str):
    fig = go.Figure(go.Bar(
        x=[score], y=["Security Score"],
        orientation="h",
        marker=dict(color=color, line_width=0),
        text=[f"{score}/100"], textposition="outside",
        textfont=dict(family="DM Mono", size=13),
    ))
    fig.update_layout(
        **_xy_layout(
            height=95,
            xaxis=dict(range=[0, 125]),
            margin=dict(l=8, r=55, t=8, b=8),
        )
    )
    return fig


def make_ai_radar(ai_data: dict):
    """Spider chart showing AI visibility signal breakdown."""
    keys    = ["schema_present", "faq_howto", "eeat_score", "content_depth", "https_ok", "open_graph", "sitemap_ok"]
    labels  = ["Schema", "FAQ/HowTo", "E-E-A-T", "Content", "HTTPS", "OG Tags", "Sitemap"]
    signals = ai_data.get("signals", {})
    eeat    = signals.get("eeat", {})

    vals = [
        100 if signals.get("schema_types") else 0,
        100 if signals.get("faq_howto_schema") else 0,
        sum(eeat.values()) / max(len(eeat), 1) * 100 if eeat else 0,
        min(signals.get("word_count", 0) / 15, 100),
        100 if signals.get("https") else 0,
        100 if signals.get("open_graph") else 0,
        100 if signals.get("sitemap") else 0,
    ]
    vals_closed = vals + [vals[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure(go.Scatterpolar(
        r=vals_closed, theta=labels_closed,
        fill="toself", name="AI Visibility",
        line=dict(color="#38bdf8", width=2),
        fillcolor="rgba(56,189,248,0.08)",
    ))
    fig.update_layout(
        **_base_layout(
            height=340,
            title=dict(text="AI Visibility Signals", font=dict(size=13, color="#64748b"), x=0.5),
            margin=dict(l=20, r=20, t=50, b=20),
        ),
        polar=dict(
            bgcolor="rgba(15,23,42,0.55)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont={"size": 8},
                            gridcolor="rgba(100,116,139,0.14)"),
            angularaxis=dict(tickfont={"size": 10}, gridcolor="rgba(100,116,139,0.1)"),
        ),
    )
    return fig


def make_backlink_donut(bl_data: dict):
    mentions = bl_data.get("aggregator_mentions", {})
    labels   = list(mentions.keys())
    values   = [max(v, 0) for v in mentions.values()]
    if not any(v > 0 for v in values):
        return None
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=COLORS[:len(labels)], line=dict(color="#060910", width=2)),
        textfont=dict(family="DM Mono", size=10),
    ))
    fig.update_layout(
        **_base_layout(
            height=300,
            title=dict(text="Mentions by Platform", font=dict(size=13, color="#64748b"), x=0.5),
            margin=dict(l=10, r=10, t=50, b=10),
        )
    )
    return fig


def make_score_waterfall(seo, sec_headers):
    """Waterfall showing how score is built up component by component."""
    components = {
        "Title Tag":        15 if 30 <= seo.get("title_length", 0) <= 60 else (8 if seo.get("title_length", 0) > 0 else 0),
        "Meta Description": 15 if 120 <= seo.get("meta_description_length", 0) <= 160 else (8 if seo.get("meta_description_length", 0) > 0 else 0),
        "H1 Tag":           15 if seo.get("h1_count", 0) == 1 else (8 if seo.get("h1_count", 0) > 1 else 0),
        "H2 Tags":          10 if seo.get("h2_count", 0) > 0 else 0,
        "Canonical URL":    10 if seo.get("canonical_url") else 0,
        "Structured Data":  10 if seo.get("structured_data_count", 0) > 0 else 0,
        "Image Alt Text":   15 if seo.get("images_missing_alt", 0) == 0 else (8 if seo.get("images_missing_alt", 0) / max(seo.get("total_images", 1), 1) < 0.2 else 0),
        "Load Speed":       10 if seo.get("load_time_seconds", 99) < 2 else (5 if seo.get("load_time_seconds", 99) < 4 else 0),
    }
    labels = list(components.keys())
    values = list(components.values())

    colors = ["#34d399" if v >= 10 else ("#fbbf24" if v > 0 else "#f87171") for v in values]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=colors, line_width=0),
        text=[f"+{v}" if v > 0 else "0" for v in values],
        textposition="outside",
        textfont=dict(family="DM Mono", size=10),
    ))
    fig.update_layout(
        **_xy_layout(
            height=300,
            title=dict(text="Score Breakdown by Component", font=dict(size=13, color="#64748b"), x=0),
            yaxis=dict(range=[0, 20], gridcolor="rgba(100,116,139,0.1)"),
            margin=dict(l=10, r=10, t=44, b=60),
            xaxis=dict(tickangle=-30, gridcolor="rgba(100,116,139,0.08)"),
        )
    )
    return fig


# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-eyebrow">⚡ Real-time web intelligence</div>
    <div class="hero-title">WebScan Pro</div>
    <div class="hero-sub">SEO · Security · Competitors · AI Visibility · Backlinks<br>Full-stack analysis for any website</div>
</div>
""", unsafe_allow_html=True)

# ── INPUT PANEL ───────────────────────────────────────────────────────────────
st.markdown('<div class="input-shell">', unsafe_allow_html=True)

mode_col, _ = st.columns([3, 5])
with mode_col:
    st.markdown('<div class="mode-label">Analysis Mode</div>', unsafe_allow_html=True)
    mode = st.radio("", ["Single Site", "Competitor Analysis"], horizontal=True, label_visibility="collapsed")

st.markdown("<div style='height:.85rem'></div>", unsafe_allow_html=True)

if mode == "Single Site":
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown('<div class="input-label">Website URL</div>', unsafe_allow_html=True)
        url_input = st.text_input("url", placeholder="https://yoursite.com", label_visibility="collapsed", key="single_url")
    with c2:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        go_btn = st.button("Analyse →", key="go_single")
    comp_urls = []

else:
    st.markdown('<div class="input-label">Your Site + Up to 3 Competitors</div>', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        url1 = st.text_input("", placeholder="🏠  Your site — https://yoursite.com", label_visibility="collapsed", key="cu1")
    with r1c2:
        url2 = st.text_input("", placeholder="🥊  Competitor 1", label_visibility="collapsed", key="cu2")
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        url3 = st.text_input("", placeholder="🥊  Competitor 2 (optional)", label_visibility="collapsed", key="cu3")
    with r2c2:
        url4 = st.text_input("", placeholder="🥊  Competitor 3 (optional)", label_visibility="collapsed", key="cu4")
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    go_btn    = st.button("Run Competitor Analysis →", key="go_comp")
    comp_urls = [u for u in [url1, url2, url3, url4] if u.strip()]
    url_input = url1 if url1 else ""

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<hr class='divider'>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  SINGLE SITE ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════

if go_btn and mode == "Single Site" and url_input.strip():

    with st.spinner("🔬 Running full analysis — 15–30 seconds…"):
        report    = analyze_website(url_input.strip())
        from urllib.parse import urlparse
        _domain   = urlparse(url_input.strip() if url_input.strip().startswith("http") else "https://" + url_input.strip()).netloc.replace("www.", "")
        bl_data   = check_backlink_profile(_domain)
        ai_data   = check_ai_visibility(_domain, url_input.strip() if url_input.strip().startswith("http") else "https://" + url_input.strip())

    meta        = report.get("meta", {})
    seo         = report.get("seo", {})
    tech        = report.get("technologies", {})
    ssl_info    = report.get("ssl", {})
    sec_headers = report.get("security_headers", {})
    dns         = report.get("dns", {})
    recs        = report.get("recommendations", {})
    overall     = meta.get("overall_score", 0)
    sec_score   = sec_headers.get("score", 0)

    # ── Gauge row ─────────────────────────────────────────────────────────
    st.markdown("### 📊 Health Overview")
    g1, g2, g3, g4, g5 = st.columns(5)

    with g1:
        st.plotly_chart(make_gauge(overall, "Overall Score", gauge_color(overall)), use_container_width=True, config={"displayModeBar": False})
    with g2:
        st.plotly_chart(make_gauge(sec_score, "Security", gauge_color(sec_score)), use_container_width=True, config={"displayModeBar": False})
    with g3:
        load      = seo.get("load_time_seconds", 0) or 0
        load_norm = max(0, 100 - int(load * 20))
        st.plotly_chart(make_gauge(load_norm, "Speed", gauge_color(load_norm)), use_container_width=True, config={"displayModeBar": False})
    with g4:
        seo_checks = sum([
            1 if seo.get("title") else 0,
            1 if seo.get("meta_description") else 0,
            1 if seo.get("h1_count", 0) == 1 else 0,
            1 if seo.get("canonical_url") else 0,
            1 if seo.get("structured_data_count", 0) > 0 else 0,
        ])
        seo_pct = int(seo_checks / 5 * 100)
        st.plotly_chart(make_gauge(seo_pct, "SEO", gauge_color(seo_pct)), use_container_width=True, config={"displayModeBar": False})
    with g5:
        ai_score = ai_data.get("ai_score", 0)
        st.plotly_chart(make_gauge(ai_score, "AI Visibility", gauge_color(ai_score)), use_container_width=True, config={"displayModeBar": False})

    # ── Stat pills ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-pill">Load <span>{seo.get('load_time_seconds','—')}s</span></div>
        <div class="stat-pill">Size <span>{seo.get('page_size_kb','—')} KB</span></div>
        <div class="stat-pill">Words <span>{seo.get('word_count','—')}</span></div>
        <div class="stat-pill">Int. links <span>{seo.get('internal_links','—')}</span></div>
        <div class="stat-pill">Ext. links <span>{seo.get('external_links','—')}</span></div>
        <div class="stat-pill">Images <span>{seo.get('total_images','—')}</span></div>
        <div class="stat-pill">Alt missing <span>{seo.get('images_missing_alt','—')}</span></div>
        <div class="stat-pill">SSL <span>{'✔' if ssl_info.get('valid') else '✘'} {ssl_info.get('days_remaining','—')}d</span></div>
        <div class="stat-pill">Sec headers <span>{sec_headers.get('found_count',0)}/{sec_headers.get('total_checked',7)}</span></div>
        <div class="stat-pill">Backlink score <span>{bl_data.get('backlink_score',0)}/100</span></div>
        <div class="stat-pill">AI score <span>{ai_score}/100</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────
    t_seo, t_tech, t_sec, t_infra, t_ai, t_bl, t_recs, t_raw = st.tabs([
        "📄 SEO", "⚙️ Tech Stack", "🔒 Security",
        "🌐 Infrastructure", "🤖 AI Visibility", "🔗 Backlinks",
        "💡 Recommendations", "{ } Raw",
    ])

    # ── SEO ───────────────────────────────────────────────────────────────
    with t_seo:
        if seo.get("error"):
            st.error(seo["error"])
        else:
            seo_items = {
                "Title Tag":        min(seo.get("title_length", 0) / 60 * 100, 100),
                "Meta Description": min(seo.get("meta_description_length", 0) / 160 * 100, 100),
                "H1 Tag":           100 if seo.get("h1_count") == 1 else (50 if seo.get("h1_count", 0) > 1 else 0),
                "H2 Tags":          min(seo.get("h2_count", 0) * 20, 100),
                "Canonical URL":    100 if seo.get("canonical_url") else 0,
                "Structured Data":  min(seo.get("structured_data_count", 0) * 50, 100),
                "Image Alt Text":   max(0, 100 - (seo.get("images_missing_alt", 0) / max(seo.get("total_images", 1), 1) * 100)),
            }
            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(make_seo_hbar(seo_items), use_container_width=True, config={"displayModeBar": False})
            with col_b:
                st.plotly_chart(make_score_waterfall(seo, sec_headers), use_container_width=True, config={"displayModeBar": False})

            c_l, c_r = st.columns(2)
            with c_l:
                st.markdown('<p class="sec-head">Page Metadata</p>', unsafe_allow_html=True)
                st.markdown(f"**Title** `({seo.get('title_length',0)} chars)`")
                st.code(seo.get("title") or "(none)", language=None)
                st.markdown(f"**Meta Description** `({seo.get('meta_description_length',0)} chars)`")
                st.code(seo.get("meta_description") or "(none)", language=None)
                st.markdown("**Canonical URL**")
                st.code(seo.get("canonical_url") or "(none)", language=None)
                st.markdown("**Robots Meta**")
                st.code(seo.get("robots_meta") or "(none)", language=None)
            with c_r:
                st.markdown('<p class="sec-head">Headings</p>', unsafe_allow_html=True)
                st.markdown(f"**H1 Tags** — {seo.get('h1_count',0)} found")
                for h in seo.get("h1_tags", [])[:3]:
                    st.code(h, language=None)
                st.markdown(f"**H2 Tags** — {seo.get('h2_count',0)} found")
                for h in seo.get("h2_tags", [])[:4]:
                    st.code(h, language=None)

            if seo.get("structured_data"):
                st.markdown('<p class="sec-head">JSON-LD Structured Data</p>', unsafe_allow_html=True)
                for i, sd in enumerate(seo["structured_data"]):
                    with st.expander(f"Block {i+1} — {sd.get('@type','Unknown')}"):
                        st.json(sd)

    # ── Tech Stack ────────────────────────────────────────────────────────
    with t_tech:
        if tech.get("error"):
            st.error(tech["error"])
        else:
            tc1, tc2 = st.columns(2)
            cats = [
                ("Frontend Frameworks", "frontend",  "cyan"),
                ("CMS / Platform",      "cms",       "purple"),
                ("Backend / Language",  "backend",   "amber"),
                ("Analytics Tools",     "analytics", "green"),
                ("Hosting Provider",    "hosting",   "cyan"),
                ("CDN",                 "cdn",       "purple"),
            ]
            for i, (label, key, color) in enumerate(cats):
                col = tc1 if i % 2 == 0 else tc2
                with col:
                    st.markdown(f'<p class="sec-head">{label}</p>', unsafe_allow_html=True)
                    st.markdown(tech_badges(tech.get(key, []), color), unsafe_allow_html=True)
            st.markdown('<p class="sec-head">Server Details</p>', unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Server",       tech.get("server", "Unknown"))
            sc2.metric("Powered By",   tech.get("powered_by") or "—")
            sc3.metric("Content-Type", (tech.get("content_type") or "—")[:40])
            with st.expander("Raw Response Headers"):
                st.json(tech.get("raw_headers", {}))

    # ── Security ──────────────────────────────────────────────────────────
    with t_sec:
        s1, s2 = st.columns([1, 2])
        with s1:
            st.markdown('<p class="sec-head">SSL Certificate</p>', unsafe_allow_html=True)
            if ssl_info.get("error"):
                st.error(ssl_info["error"])
            else:
                st.success("✔ Valid SSL") if ssl_info.get("valid") else st.error("✘ Invalid SSL")
                st.metric("Issuer",  ssl_info.get("issuer", "—"))
                st.metric("Expires", ssl_info.get("expiry_date", "—"))
                days = ssl_info.get("days_remaining")
                if days is not None:
                    if days < 14:
                        st.error(f"🚨 Expires in {days} days!")
                    elif days < 30:
                        st.warning(f"⚠ {days} days left")
                    else:
                        st.info(f"ℹ {days} days remaining")
        with s2:
            st.markdown('<p class="sec-head">HTTP Security Headers</p>', unsafe_allow_html=True)
            if not sec_headers.get("error"):
                st.plotly_chart(
                    make_sec_score_bar(sec_headers.get("score", 0), gauge_color(sec_headers.get("score", 0))),
                    use_container_width=True, config={"displayModeBar": False},
                )
                for key, info in sec_headers.get("headers_found", {}).items():
                    st.markdown(
                        f'{badge("✔  " + info["label"], "green")} '
                        f'<span style="font-size:.76rem;color:#475569">{info["description"]}</span>',
                        unsafe_allow_html=True,
                    )
                for key, info in sec_headers.get("headers_missing", {}).items():
                    st.markdown(
                        f'{badge("✘  " + info["label"], "rose")} '
                        f'<span style="font-size:.76rem;color:#475569">{info["description"]}</span>',
                        unsafe_allow_html=True,
                    )

    # ── Infrastructure ────────────────────────────────────────────────────
    with t_infra:
        st.markdown('<p class="sec-head">DNS Records</p>', unsafe_allow_html=True)
        dns_rows = []
        for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]:
            for r in dns.get(rtype, []):
                dns_rows.append({"Type": rtype, "Record": r})
        if dns_rows:
            st.dataframe(pd.DataFrame(dns_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No DNS records retrieved")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.markdown("**IP Addresses**")
            for ip in dns.get("ip_addresses", []):
                st.code(ip, language=None)
        with dc2:
            st.markdown("**Nameservers**")
            for ns in dns.get("nameservers", []):
                st.code(ns, language=None)
        with dc3:
            st.markdown("**Mail Servers**")
            for mx in dns.get("mail_servers", []):
                st.code(mx, language=None)

    # ── AI Visibility ─────────────────────────────────────────────────────
    with t_ai:
        tier_color = ai_data.get("ai_tier_color", "#fbbf24")
        st.markdown(f"""
        <div class="ai-card">
            <div style="font-size:.68rem;font-family:'DM Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:#475569;margin-bottom:.3rem;">AI Visibility Score</div>
            <div style="font-size:2.8rem;font-weight:700;font-family:'DM Mono',monospace;color:{tier_color}">{ai_data.get('ai_score',0)}<span style="font-size:1rem;color:#475569">/100</span></div>
            <div style="font-size:.85rem;color:{tier_color};margin-top:.3rem;">{ai_data.get('ai_tier','—')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

        ai_col1, ai_col2 = st.columns([1, 1])
        with ai_col1:
            st.plotly_chart(make_ai_radar(ai_data), use_container_width=True, config={"displayModeBar": False})
        with ai_col2:
            st.markdown('<p class="sec-head">Signal Breakdown</p>', unsafe_allow_html=True)
            signals = ai_data.get("signals", {})
            eeat    = signals.get("eeat", {})

            checks = [
                ("Schema.org Structured Data", bool(signals.get("schema_types")), "green", "rose"),
                ("FAQ / HowTo Schema",          signals.get("faq_howto_schema", False), "green", "rose"),
                ("HTTPS Enabled",               signals.get("https", False), "green", "rose"),
                ("Open Graph Tags",             signals.get("open_graph", False), "green", "amber"),
                ("Sitemap.xml",                 signals.get("sitemap", False), "green", "amber"),
                ("About Page",                  eeat.get("about_page", False), "green", "amber"),
                ("Contact Page",                eeat.get("contact_page", False), "green", "amber"),
                ("Author Info",                 eeat.get("author_info", False), "green", "slate"),
                ("Privacy Policy",              eeat.get("privacy_policy", False), "green", "slate"),
            ]
            for label, passed, ok_kind, fail_kind in checks:
                kind = ok_kind if passed else fail_kind
                icon = "✔" if passed else "✘"
                st.markdown(f'{badge(f"{icon}  {label}", kind)}', unsafe_allow_html=True)

            st.markdown('<p class="sec-head">Content Signals</p>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="stat-row">
                <div class="stat-pill">Words <span>{signals.get('word_count','—')}</span></div>
                <div class="stat-pill">Subheadings <span>{signals.get('subheadings','—')}</span></div>
                <div class="stat-pill">Schema blocks <span>{len(signals.get('schema_types',[]))}</span></div>
            </div>
            """, unsafe_allow_html=True)

        if ai_data.get("recommendations"):
            st.markdown('<p class="sec-head">🤖 AI Optimisation Recommendations</p>', unsafe_allow_html=True)
            for rec in ai_data["recommendations"]:
                st.markdown(f'<div class="win-row">→ {rec}</div>', unsafe_allow_html=True)

        st.markdown('<p class="sec-head">Detected Schema Types</p>', unsafe_allow_html=True)
        schema_types = ai_data.get("signals", {}).get("schema_types", [])
        if schema_types:
            st.markdown(" ".join(badge(t, "teal") for t in schema_types), unsafe_allow_html=True)
        else:
            st.info("No JSON-LD schema detected — adding schema significantly improves AI citation likelihood")

    # ── Backlinks ─────────────────────────────────────────────────────────
    with t_bl:
        bl_score = bl_data.get("backlink_score", 0)
        st.markdown(f"""
        <div class="bl-card">
            <div style="font-size:.68rem;font-family:'DM Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:#475569;margin-bottom:.3rem;">Backlink Authority Score</div>
            <div style="font-size:2.8rem;font-weight:700;font-family:'DM Mono',monospace;color:{gauge_color(bl_score)}">{bl_score}<span style="font-size:1rem;color:#475569">/100</span></div>
            <div style="font-size:.82rem;color:#64748b;margin-top:.2rem;">Based on public index signals · No paid API required</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

        bl_col1, bl_col2 = st.columns([1, 1])
        with bl_col1:
            st.markdown('<p class="sec-head">Public Index Signals</p>', unsafe_allow_html=True)
            signals_display = {
                "Bing Indexed Pages":  bl_data.get("signals", {}).get("bing_index", "—"),
                "Open PageRank Score": bl_data.get("signals", {}).get("open_pagerank", "—"),
                "Common Crawl":        bl_data.get("signals", {}).get("common_crawl", "—"),
            }
            for label, val in signals_display.items():
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:.4rem 0;'
                    f'border-bottom:1px solid rgba(100,116,139,.08);font-size:.84rem">'
                    f'<span style="color:#64748b">{label}</span>'
                    f'<span style="color:#e2e8f0;font-family:\'DM Mono\',monospace">{val}</span></div>',
                    unsafe_allow_html=True,
                )

        with bl_col2:
            donut = make_backlink_donut(bl_data)
            if donut:
                st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown('<p class="sec-head">Aggregator Mentions</p>', unsafe_allow_html=True)
                mentions = bl_data.get("aggregator_mentions", {})
                for platform, count in mentions.items():
                    color = "green" if count > 0 else "slate"
                    st.markdown(f'{badge(f"{platform}: {count}", color)}', unsafe_allow_html=True)

        st.markdown('<p class="sec-head">Platform Mentions</p>', unsafe_allow_html=True)
        mentions = bl_data.get("aggregator_mentions", {})
        m1, m2, m3 = st.columns(3)
        for col, (platform, count) in zip([m1, m2, m3], mentions.items()):
            color = "#34d399" if count > 0 else "#f87171"
            col.markdown(
                f'<div style="text-align:center;background:rgba(30,41,59,.7);border:1px solid rgba(100,116,139,.15);'
                f'border-radius:10px;padding:.8rem"><div style="font-size:1.5rem;color:{color};font-family:\'DM Mono\',monospace;font-weight:700">{count}</div>'
                f'<div style="font-size:.7rem;color:#475569;text-transform:uppercase;letter-spacing:.1em">{platform}</div></div>',
                unsafe_allow_html=True,
            )

        st.info(
            "💡 For deep backlink data (referring domains, anchor texts, toxic links), "
            "integrate Ahrefs, Semrush, or Moz APIs. These free signals give a solid directional estimate.",
            icon=None,
        )

    # ── Recommendations ───────────────────────────────────────────────────
    with t_recs:
        critical = recs.get("critical_issues", [])
        wins     = recs.get("quick_wins", [])
        ai_recs  = ai_data.get("recommendations", [])
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown('<p class="sec-head">🔴 Critical Issues</p>', unsafe_allow_html=True)
            if critical:
                for issue in critical:
                    st.markdown(f'<div class="issue-row">⚠ {issue}</div>', unsafe_allow_html=True)
            else:
                st.success("No critical issues!")
        with rc2:
            st.markdown('<p class="sec-head">✅ Quick Wins</p>', unsafe_allow_html=True)
            if wins:
                for win in wins:
                    st.markdown(f'<div class="win-row">→ {win}</div>', unsafe_allow_html=True)
            else:
                st.info("Site looks well optimised!")

        if ai_recs:
            st.markdown('<p class="sec-head">🤖 AI Visibility Improvements</p>', unsafe_allow_html=True)
            for rec in ai_recs:
                st.markdown(f'<div class="win-row">→ {rec}</div>', unsafe_allow_html=True)

    # ── Raw ───────────────────────────────────────────────────────────────
    with t_raw:
        full_data = {**report, "backlink_data": bl_data, "ai_visibility": ai_data}
        json_str  = json.dumps(full_data, indent=2, default=str)
        dl1, dl2  = st.columns(2)
        with dl1:
            st.download_button(
                "⬇ Download JSON", data=json_str,
                file_name=f"webscan_{meta.get('domain','report')}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
            )
        with dl2:
            flat = {
                "url": meta.get("analysed_url"), "domain": meta.get("domain"),
                "overall_score": meta.get("overall_score"), "timestamp": meta.get("timestamp"),
                **{k: v for k, v in seo.items() if not isinstance(v, (list, dict))},
                "ssl_valid": ssl_info.get("valid"), "ssl_days": ssl_info.get("days_remaining"),
                "security_score": sec_headers.get("score"),
                "ai_score": ai_data.get("ai_score"),
                "backlink_score": bl_data.get("backlink_score"),
            }
            st.download_button(
                "⬇ Download CSV",
                data=pd.DataFrame([flat]).to_csv(index=False),
                file_name=f"webscan_{meta.get('domain','report')}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
        with st.expander("View raw JSON"):
            st.json(full_data)


# ════════════════════════════════════════════════════════════════════════════════
#  COMPETITOR ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════

elif go_btn and mode == "Competitor Analysis" and len(comp_urls) >= 2:

    with st.spinner(f"🔬 Analysing {len(comp_urls)} sites in parallel — 25–50 seconds…"):
        comp_report = run_competitor_analysis(comp_urls)

    sites      = comp_report["sites"]
    comparison = comp_report["comparison"]
    winner     = comp_report["winner"]
    radar_data = comp_report["radar_data"]
    tech_comp  = comp_report["tech_comparison"]
    primary    = sites[0]["domain"] if sites else ""

    st.markdown("## 🏆 Competitor Intelligence Report")

    # Leaderboard bar
    st.markdown('<p class="sec-head">Overall Health Scores</p>', unsafe_allow_html=True)
    # Score cards
    accents = [
        "linear-gradient(90deg,#38bdf8,#818cf8)",
        "linear-gradient(90deg,#a78bfa,#f472b6)",
        "linear-gradient(90deg,#34d399,#0ea5e9)",
        "linear-gradient(90deg,#fbbf24,#f87171)",
    ]
    cols = st.columns(len(sites))
    for i, (col, site) in enumerate(zip(cols, sites)):
        with col:
            ssl_ok   = site.get("ssl", {}).get("valid", False)
            ssl_days = site.get("ssl", {}).get("days_remaining", "—")
            label    = f"{'🏠 ' if site['domain']==primary else '🥊 '}{site['domain']}"
            st.markdown(render_score_card(
                site.get("overall_score", 0), label,
                f"SSL {'✔' if ssl_ok else '✘'} · {ssl_days}d",
                accents[i % len(accents)],
            ), unsafe_allow_html=True)

    st.markdown("<div style='height:.85rem'></div>", unsafe_allow_html=True)

    # 3D surface + radar
    surf_col, rad_col = st.columns(2)
    with surf_col:
        st.plotly_chart(make_3d_surface(sites, comparison), use_container_width=True, config={"displayModeBar": False})
    with rad_col:
        if len(radar_data) >= 2:
            st.plotly_chart(make_radar(radar_data), use_container_width=True, config={"displayModeBar": False})

    # Grouped bar
    st.plotly_chart(
        make_bar_comparison(comparison, ["overall_score", "security_score", "security_headers_found", "structured_data_count", "word_count"]),
        use_container_width=True, config={"displayModeBar": False},
    )

    # Full metrics table
    st.markdown('<p class="sec-head">Full Metrics Comparison</p>', unsafe_allow_html=True)
    domains      = [s["domain"] for s in sites]
    lower_better = {"load_time_seconds", "page_size_kb", "images_missing_alt"}

    table_html = '<table class="comp-table"><thead><tr><th>Metric</th>'
    for d in domains:
        table_html += f'<th>{"🏠 " if d==primary else "🥊 "}{d}</th>'
    table_html += "</tr></thead><tbody>"

    show_metrics = [
        "overall_score", "security_score", "load_time_seconds", "page_size_kb",
        "word_count", "internal_links", "external_links", "h1_count", "h2_count",
        "structured_data_count", "security_headers_found", "ssl_days_remaining",
        "has_canonical", "has_meta_description", "images_missing_alt",
    ]
    for key in show_metrics:
        if key not in comparison:
            continue
        row = comparison[key]
        table_html += f'<tr><td style="color:#64748b;font-family:\'DM Mono\',monospace;font-size:.76rem">{row["label"]}</td>'
        best_domain = winner.get(key)
        for d in domains:
            val = row["values"].get(d, "—")
            if key in ("has_canonical", "has_meta_description"):
                val = "✔" if val == 1 else "✘"
            is_best  = d == best_domain
            is_worst = (
                val not in ("✔", "✘") and len(domains) > 1 and isinstance(val, (int, float))
                and all(
                    (val <= row["values"].get(od, val)) if key not in lower_better
                    else (val >= row["values"].get(od, val))
                    for od in domains if od != d
                )
            )
            cls  = "best" if is_best else ("worst" if is_worst else "")
            star = "  ★" if is_best else ""
            table_html += f'<td class="{cls}">{val}{star}</td>'
        table_html += "</tr>"
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

    # Treemap
    st.markdown('<p class="sec-head">Technology Landscape</p>', unsafe_allow_html=True)
    treemap = make_treemap_tech(tech_comp)
    if treemap:
        st.plotly_chart(treemap, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No technology data for treemap")

    # Tech badges
    st.markdown('<p class="sec-head">Technology Stack Breakdown</p>', unsafe_allow_html=True)
    tech_cols = st.columns(len(sites))
    for col, site in zip(tech_cols, sites):
        d  = site["domain"]
        tc = tech_comp.get(d, {})
        with col:
            st.markdown(f"**{d}**")
            for cat_label, cat_key, col_kind in [
                ("Frontend", "frontend", "cyan"), ("CMS", "cms", "purple"),
                ("Analytics", "analytics", "green"), ("Hosting", "hosting", "amber"),
            ]:
                items = tc.get(cat_key, [])
                if items:
                    st.markdown(
                        f"<small style='color:#475569'>{cat_label}</small><br>" + tech_badges(items, col_kind),
                        unsafe_allow_html=True,
                    )

    # Per-site recommendations
    st.markdown('<p class="sec-head">Site-by-Site Recommendations</p>', unsafe_allow_html=True)
    rec_tabs = st.tabs([f"{'🏠' if s['domain']==primary else '🥊'} {s['domain']}" for s in sites])
    for tab, site in zip(rec_tabs, sites):
        with tab:
            site_recs = site.get("recommendations", {})
            rc1, rc2  = st.columns(2)
            with rc1:
                st.markdown('<p class="sec-head">Critical Issues</p>', unsafe_allow_html=True)
                for issue in site_recs.get("critical_issues", []):
                    st.markdown(f'<div class="issue-row">⚠ {issue}</div>', unsafe_allow_html=True)
                if not site_recs.get("critical_issues"):
                    st.success("No critical issues!")
            with rc2:
                st.markdown('<p class="sec-head">Quick Wins</p>', unsafe_allow_html=True)
                for win in site_recs.get("quick_wins", []):
                    st.markdown(f'<div class="win-row">→ {win}</div>', unsafe_allow_html=True)
                if not site_recs.get("quick_wins"):
                    st.info("Looking good!")

    # Export
    st.markdown('<p class="sec-head">Export</p>', unsafe_allow_html=True)
    comp_json = json.dumps(comp_report, indent=2, default=str)
    edl1, edl2 = st.columns(2)
    with edl1:
        st.download_button(
            "⬇ Full JSON Report", data=comp_json,
            file_name=f"competitor_analysis_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
        )
    with edl2:
        csv_rows = [{
            "domain": s["domain"], "url": s["url"],
            "overall_score": s.get("overall_score"),
            "security_score": s.get("security_headers", {}).get("score"),
            "load_time": s.get("seo", {}).get("load_time_seconds"),
            "page_size_kb": s.get("seo", {}).get("page_size_kb"),
            "ssl_valid": s.get("ssl", {}).get("valid"),
            "ssl_days": s.get("ssl", {}).get("days_remaining"),
        } for s in sites]
        st.download_button(
            "⬇ Summary CSV",
            data=pd.DataFrame(csv_rows).to_csv(index=False),
            file_name=f"competitor_summary_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )


# ── Validation warnings ───────────────────────────────────────────────────────

elif go_btn and mode == "Competitor Analysis" and len(comp_urls) < 2:
    st.warning("Please enter at least 2 URLs for competitor analysis.")

elif go_btn and mode == "Single Site" and not url_input.strip():
    st.warning("Please enter a URL to analyse.")

# ── Empty state ───────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🌐</div>
        <div class="empty-title">Enter a URL above and click Analyse</div>
        <div class="empty-desc">
            SEO · Security · Tech Detection · SSL · DNS · AI Visibility · Backlink Signals · Competitor Analysis
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:.4rem;margin-top:.85rem;">
        <span class="badge bg-cyan">SEO Analysis</span>
        <span class="badge bg-purple">Tech Detection</span>
        <span class="badge bg-green">SSL Check</span>
        <span class="badge bg-amber">Security Headers</span>
        <span class="badge bg-slate">DNS Records</span>
        <span class="badge bg-rose">Competitor Analysis</span>
        <span class="badge bg-teal">AI Visibility</span>
        <span class="badge bg-purple">Backlink Signals</span>
        <span class="badge bg-cyan">3D Charts</span>
    </div>
    """, unsafe_allow_html=True)
