"""
app.py  ·  WebScan Pro — Website & Competitor Analysis Dashboard
"""

import json
import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="WebScan Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
.stApp {
    background: #080b12;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(56,189,248,0.08) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 90% 80%, rgba(139,92,246,0.06) 0%, transparent 50%);
    color: #e2e8f0;
    min-height: 100vh;
}

/* ── Animated hero ── */
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 20px rgba(56,189,248,0.2); }
    50%       { box-shadow: 0 0 40px rgba(56,189,248,0.4), 0 0 80px rgba(139,92,246,0.2); }
}
@keyframes scanline {
    0%   { transform: translateY(-100%); }
    100% { transform: translateY(100vh); }
}

.hero-wrap {
    text-align: center;
    padding: 3rem 1rem 2rem;
    animation: fadeUp 0.7s ease both;
}
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #38bdf8;
    margin-bottom: 1rem;
    opacity: 0.8;
}
.hero-title {
    font-size: clamp(2.4rem, 5vw, 4rem);
    font-weight: 900;
    line-height: 1.05;
    background: linear-gradient(135deg, #e0f2fe 0%, #38bdf8 35%, #818cf8 65%, #c084fc 100%);
    background-size: 200% 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 5s ease infinite;
    margin-bottom: 0.75rem;
}
.hero-sub {
    font-size: 1rem;
    font-weight: 400;
    color: #64748b;
    letter-spacing: 0.02em;
    max-width: 520px;
    margin: 0 auto 2rem;
}

/* ── Input area ── */
.input-shell {
    background: linear-gradient(135deg, rgba(15,23,42,0.9), rgba(30,41,59,0.9));
    border: 1px solid rgba(56,189,248,0.2);
    border-radius: 20px;
    padding: 1.75rem 2rem;
    margin-bottom: 2rem;
    backdrop-filter: blur(12px);
    animation: fadeUp 0.7s 0.2s ease both;
    animation-fill-mode: backwards;
}
.input-label {
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #38bdf8;
    margin-bottom: 0.5rem;
}

/* ── Streamlit widget overrides ── */
div[data-testid="stTextInput"] input {
    background: rgba(15,23,42,0.8) !important;
    border: 1px solid rgba(100,116,139,0.3) !important;
    color: #e2e8f0 !important;
    border-radius: 12px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.9rem !important;
    padding: 0.65rem 1rem !important;
    transition: border-color 0.2s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: rgba(56,189,248,0.6) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.1) !important;
}
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
    color: #fff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.5rem !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.92rem !important;
    width: 100% !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.2s, transform 0.15s !important;
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* ── Score cards ── */
.score-card {
    background: linear-gradient(135deg, rgba(15,23,42,0.95), rgba(30,41,59,0.9));
    border: 1px solid rgba(100,116,139,0.2);
    border-radius: 16px;
    padding: 1.25rem 1rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, border-color 0.2s;
}
.score-card:hover { transform: translateY(-2px); border-color: rgba(56,189,248,0.3); }
.score-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--accent, linear-gradient(90deg, #38bdf8, #818cf8));
}
.score-num {
    font-family: 'DM Mono', monospace;
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1;
    color: var(--score-color, #e2e8f0);
}
.score-lbl {
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #475569;
    margin-top: 0.4rem;
    font-weight: 500;
}
.score-sub {
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 0.2rem;
    font-family: 'DM Mono', monospace;
}
.score-good { --score-color: #34d399; }
.score-mid  { --score-color: #fbbf24; }
.score-bad  { --score-color: #f87171; }

/* ── Stat pills ── */
.stat-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin: 0.5rem 0;
}
.stat-pill {
    background: rgba(30,41,59,0.8);
    border: 1px solid rgba(100,116,139,0.2);
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 0.75rem;
    font-family: 'DM Mono', monospace;
    color: #94a3b8;
}
.stat-pill span { color: #e2e8f0; font-weight: 500; }

/* ── Section headers ── */
.sec-head {
    font-size: 0.7rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #38bdf8;
    border-left: 2px solid #38bdf8;
    padding-left: 0.6rem;
    margin: 1.5rem 0 0.75rem;
}

/* ── Badges ── */
.badge {
    display: inline-flex; align-items: center;
    padding: 3px 10px; border-radius: 6px;
    font-size: 0.72rem; font-weight: 600; margin: 2px;
    font-family: 'DM Mono', monospace; letter-spacing: 0.04em;
}
.bg-cyan   { background: rgba(56,189,248,0.1);  color: #38bdf8;  border: 1px solid rgba(56,189,248,0.25); }
.bg-purple { background: rgba(139,92,246,0.1);  color: #a78bfa;  border: 1px solid rgba(139,92,246,0.25); }
.bg-green  { background: rgba(52,211,153,0.1);  color: #34d399;  border: 1px solid rgba(52,211,153,0.25); }
.bg-amber  { background: rgba(251,191,36,0.1);  color: #fbbf24;  border: 1px solid rgba(251,191,36,0.25); }
.bg-rose   { background: rgba(248,113,113,0.1); color: #f87171;  border: 1px solid rgba(248,113,113,0.25); }
.bg-slate  { background: rgba(100,116,139,0.1); color: #94a3b8;  border: 1px solid rgba(100,116,139,0.2); }

/* ── Issue / win rows ── */
.issue-row {
    background: rgba(239,68,68,0.06);
    border-left: 3px solid #ef4444;
    border-radius: 0 8px 8px 0;
    padding: 0.55rem 0.9rem;
    margin-bottom: 0.4rem;
    font-size: 0.85rem;
    color: #fca5a5;
    line-height: 1.4;
}
.win-row {
    background: rgba(52,211,153,0.06);
    border-left: 3px solid #34d399;
    border-radius: 0 8px 8px 0;
    padding: 0.55rem 0.9rem;
    margin-bottom: 0.4rem;
    font-size: 0.85rem;
    color: #6ee7b7;
    line-height: 1.4;
}

/* ── Divider ── */
.divider {
    border: none;
    border-top: 1px solid rgba(100,116,139,0.12);
    margin: 1.5rem 0;
}

/* ── Competitor winner tag ── */
.winner-tag {
    display: inline-block;
    background: linear-gradient(135deg, #0ea5e9, #6366f1);
    color: #fff;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'DM Mono', monospace;
    vertical-align: middle;
    margin-left: 6px;
}

/* ── Tab styling ── */
button[data-baseweb="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
}

/* ── Comparison table ── */
.comp-table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
.comp-table th {
    background: rgba(15,23,42,0.9);
    color: #64748b;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.6rem 0.8rem;
    text-align: left;
    border-bottom: 1px solid rgba(100,116,139,0.15);
}
.comp-table td {
    padding: 0.55rem 0.8rem;
    border-bottom: 1px solid rgba(100,116,139,0.08);
    color: #cbd5e1;
    vertical-align: middle;
}
.comp-table tr:hover td { background: rgba(30,41,59,0.5); }
.comp-table .best { color: #34d399; font-weight: 700; }
.comp-table .worst { color: #f87171; }

/* ── Landing empty state ── */
.empty-state {
    text-align: center;
    padding: 4rem 1rem;
    animation: fadeUp 0.6s ease both;
}
.empty-icon {
    font-size: 3.5rem;
    margin-bottom: 1rem;
    filter: grayscale(0.3);
}
.empty-title { font-size: 1.1rem; font-weight: 600; color: #475569; margin-bottom: 0.5rem; }
.empty-desc  { font-size: 0.85rem; color: #334155; max-width: 400px; margin: 0 auto; }

/* ── Plotly chart container ── */
.chart-wrap {
    background: rgba(15,23,42,0.7);
    border: 1px solid rgba(100,116,139,0.15);
    border-radius: 16px;
    padding: 0.5rem;
    margin-bottom: 1rem;
}

/* ── Mode toggle pills ── */
.mode-label {
    font-size: 0.7rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

from scripts.analyzer import analyze_website
from scripts.competitor_analyzer import run_competitor_analysis

# ── Plotly theme helper ────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
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
    xaxis=dict(gridcolor="rgba(100,116,139,0.1)", zerolinecolor="rgba(100,116,139,0.15)"),
    yaxis=dict(gridcolor="rgba(100,116,139,0.1)", zerolinecolor="rgba(100,116,139,0.15)"),
)
COLORS = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24", "#f87171", "#fb923c"]


# ── Utility helpers ────────────────────────────────────────────────────────────

def score_cls(s):
    return "score-good" if s >= 70 else ("score-mid" if s >= 40 else "score-bad")

def badge(text, kind="cyan"):
    return f'<span class="badge bg-{kind}">{text}</span>'

def tech_badges(items, kind="cyan"):
    if not items:
        return '<span style="color:#334155;font-size:0.8rem;">None detected</span>'
    return "".join(badge(i, kind) for i in items)

def render_score_card(value, label, sub="", accent="linear-gradient(90deg,#38bdf8,#818cf8)"):
    cls = score_cls(int(value)) if isinstance(value, (int, float)) else ""
    return f"""
    <div class="score-card" style="--accent:{accent}">
        <div class="score-num {cls}">{value}</div>
        <div class="score-lbl">{label}</div>
        {'<div class="score-sub">' + sub + '</div>' if sub else ''}
    </div>"""

def make_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 13, "color": "#94a3b8", "family": "Outfit"}},
        number={"font": {"size": 32, "color": color, "family": "DM Mono"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#334155", "tickfont": {"size": 9}},
            "bar":  {"color": color, "thickness": 0.25},
            "bgcolor": "rgba(30,41,59,0.6)",
            "bordercolor": "rgba(100,116,139,0.15)",
            "steps": [
                {"range": [0,  40], "color": "rgba(248,113,113,0.08)"},
                {"range": [40, 70], "color": "rgba(251,191,36,0.08)"},
                {"range": [70,100], "color": "rgba(52,211,153,0.08)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 2},
                "thickness": 0.8,
                "value": value,
            },
        },
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=200, margin=dict(l=20, r=20, t=30, b=10))
    return fig


def make_radar(radar_data):
    dims = [d["dimension"] for d in radar_data[0]["dimensions"]]
    fig = go.Figure()
    for i, site in enumerate(radar_data):
        vals = [d["normalised"] for d in site["dimensions"]]
        vals.append(vals[0])  # close polygon
        fig.add_trace(go.Scatterpolar(
            r=vals,
            theta=dims + [dims[0]],
            fill="toself",
            name=site["domain"],
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            fillcolor=COLORS[i % len(COLORS)].replace("#", "rgba(") + ",0.08)" if "#" in COLORS[i] else COLORS[i],
            opacity=0.9,
        ))
    fig.update_layout(
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
        polar=dict(
            bgcolor="rgba(15,23,42,0.6)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont={"size": 8}, gridcolor="rgba(100,116,139,0.15)"),
            angularaxis=dict(tickfont={"size": 10}, gridcolor="rgba(100,116,139,0.1)"),
        ),
        height=400,
        title=dict(text="Capability Radar", font=dict(size=13, color="#64748b"), x=0.5),
    )
    return fig


def make_bar_comparison(comparison, metrics_to_show):
    domains = list(next(iter(comparison.values()))["values"].keys())
    fig = go.Figure()
    for i, domain in enumerate(domains):
        x_labels, y_vals = [], []
        for key in metrics_to_show:
            x_labels.append(comparison[key]["label"])
            y_vals.append(comparison[key]["values"].get(domain, 0) or 0)
        fig.add_trace(go.Bar(
            name=domain, x=x_labels, y=y_vals,
            marker_color=COLORS[i % len(COLORS)],
            marker_line_width=0,
            opacity=0.85,
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="group",
        height=360,
        title=dict(text="Head-to-Head Metrics", font=dict(size=13, color="#64748b"), x=0),
        bargap=0.25, bargroupgap=0.08,
    )
    return fig


def make_score_hbar(sites):
    domains = [s["domain"] for s in sites]
    scores  = [s.get("overall_score", 0) for s in sites]
    colors  = [("#34d399" if s >= 70 else "#fbbf24" if s >= 40 else "#f87171") for s in scores]
    fig = go.Figure(go.Bar(
        x=scores, y=domains, orientation="h",
        marker=dict(color=colors, line_width=0),
        text=scores, textposition="outside",
        textfont=dict(family="DM Mono", size=13, color="#e2e8f0"),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=max(180, len(sites) * 60),
        title=dict(text="Overall Health Score", font=dict(size=13, color="#64748b"), x=0),
        xaxis=dict(range=[0, 115], gridcolor="rgba(100,116,139,0.1)"),
        margin=dict(l=10, r=60, t=40, b=20),
    )
    return fig


def make_treemap_tech(tech_comparison):
    labels, parents, values, colors_list = ["Tech Stack"], [""], [0], ["#080b12"]
    color_map = {
        "frontend": "#38bdf8", "cms": "#a78bfa",
        "analytics": "#34d399", "hosting": "#fbbf24", "cdn": "#fb923c",
    }
    for domain, cats in tech_comparison.items():
        labels.append(domain); parents.append("Tech Stack"); values.append(0); colors_list.append("#1e293b")
        for cat, items in cats.items():
            if cat == "server" or not items:
                continue
            for item in items:
                labels.append(item); parents.append(domain); values.append(1)
                colors_list.append(color_map.get(cat, "#64748b"))
    if len(labels) <= 2:
        return None
    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents,
        marker=dict(colors=colors_list, line=dict(width=1, color="#080b12")),
        textfont=dict(family="Outfit", size=12),
        hovertemplate="<b>%{label}</b><extra></extra>",
    ))
    fig.update_layout(
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis","yaxis")},
        height=340,
        title=dict(text="Technology Landscape", font=dict(size=13, color="#64748b"), x=0),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-eyebrow">⚡ Real-time web intelligence</div>
    <div class="hero-title">WebScan Pro</div>
    <div class="hero-sub">Technical · SEO · Security · Competitor Analysis<br>Instant insights for any website</div>
</div>
""", unsafe_allow_html=True)

# ── Input panel ───────────────────────────────────────────────────────────────
with st.container():
    st.markdown('<div class="input-shell">', unsafe_allow_html=True)

    mode_col, _ = st.columns([2, 5])
    with mode_col:
        st.markdown('<div class="mode-label">Analysis Mode</div>', unsafe_allow_html=True)
        mode = st.radio("", ["Single Site", "Competitor Analysis"],
                        horizontal=True, label_visibility="collapsed")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    if mode == "Single Site":
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown('<div class="input-label">Website URL</div>', unsafe_allow_html=True)
            url_input = st.text_input("url", placeholder="https://yoursite.com",
                                      label_visibility="collapsed", key="single_url")
        with c2:
            st.markdown("<div style='height:1.65rem'></div>", unsafe_allow_html=True)
            go_btn = st.button("Analyse →", key="go_single")
        comp_urls = []

    else:
        st.markdown('<div class="input-label">Your Site + Up to 3 Competitors</div>', unsafe_allow_html=True)
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            url1 = st.text_input("", placeholder="🏠  Your site — https://yoursite.com",
                                  label_visibility="collapsed", key="cu1")
        with r1c2:
            url2 = st.text_input("", placeholder="🥊  Competitor 1 — https://competitor1.com",
                                  label_visibility="collapsed", key="cu2")
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            url3 = st.text_input("", placeholder="🥊  Competitor 2 (optional)",
                                  label_visibility="collapsed", key="cu3")
        with r2c2:
            url4 = st.text_input("", placeholder="🥊  Competitor 3 (optional)",
                                  label_visibility="collapsed", key="cu4")
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        go_btn = st.button("Run Competitor Analysis →", key="go_comp")
        comp_urls = [u for u in [url1, url2, url3, url4] if u.strip()]
        url_input = url1

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  SINGLE SITE ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════

if go_btn and mode == "Single Site" and url_input.strip():
    with st.spinner("🔬 Scanning website — please wait 10–25 seconds…"):
        report = analyze_website(url_input.strip())

    meta        = report.get("meta", {})
    seo         = report.get("seo", {})
    tech        = report.get("technologies", {})
    ssl_info    = report.get("ssl", {})
    sec_headers = report.get("security_headers", {})
    dns         = report.get("dns", {})
    recs        = report.get("recommendations", {})
    overall     = meta.get("overall_score", 0)
    sec_score   = sec_headers.get("score", 0)

    # ── Gauges row ────────────────────────────────────────────────────────
    st.markdown("### 📊 Health Overview")
    g1, g2, g3, g4 = st.columns(4)
    gauge_color = lambda s: "#34d399" if s >= 70 else ("#fbbf24" if s >= 40 else "#f87171")
    with g1:
        st.plotly_chart(make_gauge(overall, "Overall Score", gauge_color(overall)),
                        use_container_width=True, config={"displayModeBar": False})
    with g2:
        st.plotly_chart(make_gauge(sec_score, "Security Score", gauge_color(sec_score)),
                        use_container_width=True, config={"displayModeBar": False})
    with g3:
        load = seo.get("load_time_seconds", 0) or 0
        load_norm = max(0, 100 - int(load * 20))
        st.plotly_chart(make_gauge(load_norm, "Speed Score", gauge_color(load_norm)),
                        use_container_width=True, config={"displayModeBar": False})
    with g4:
        seo_checks = sum([
            1 if seo.get("title") else 0,
            1 if seo.get("meta_description") else 0,
            1 if seo.get("h1_count", 0) == 1 else 0,
            1 if seo.get("canonical_url") else 0,
            1 if seo.get("structured_data_count", 0) > 0 else 0,
        ])
        seo_pct = int(seo_checks / 5 * 100)
        st.plotly_chart(make_gauge(seo_pct, "SEO Completeness", gauge_color(seo_pct)),
                        use_container_width=True, config={"displayModeBar": False})

    # ── Key metrics pill row ───────────────────────────────────────────────
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-pill">Load: <span>{seo.get('load_time_seconds','—')}s</span></div>
        <div class="stat-pill">Size: <span>{seo.get('page_size_kb','—')} KB</span></div>
        <div class="stat-pill">Words: <span>{seo.get('word_count','—')}</span></div>
        <div class="stat-pill">Internal links: <span>{seo.get('internal_links','—')}</span></div>
        <div class="stat-pill">External links: <span>{seo.get('external_links','—')}</span></div>
        <div class="stat-pill">Images: <span>{seo.get('total_images','—')}</span></div>
        <div class="stat-pill">Missing alt: <span>{seo.get('images_missing_alt','—')}</span></div>
        <div class="stat-pill">SSL: <span>{'✔' if ssl_info.get('valid') else '✘'} {ssl_info.get('days_remaining','—')}d</span></div>
        <div class="stat-pill">Sec headers: <span>{sec_headers.get('found_count',0)}/{sec_headers.get('total_checked',7)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Main tabs ─────────────────────────────────────────────────────────
    t_seo, t_tech, t_sec, t_infra, t_recs, t_raw = st.tabs([
        "📄  SEO Analysis", "⚙️  Tech Stack", "🔒  Security",
        "🌐  Infrastructure", "💡  Recommendations", "{ }  Raw Data"
    ])

    # SEO ─────────────────────────────────────────────────────────────────
    with t_seo:
        if seo.get("error"):
            st.error(seo["error"])
        else:
            # Visual SEO bar chart
            seo_items = {
                "Title Tag":        min(seo.get("title_length", 0) / 60 * 100, 100),
                "Meta Description": min(seo.get("meta_description_length", 0) / 160 * 100, 100),
                "H1 Tag":           100 if seo.get("h1_count") == 1 else (50 if seo.get("h1_count", 0) > 1 else 0),
                "H2 Tags":          min(seo.get("h2_count", 0) * 20, 100),
                "Canonical URL":    100 if seo.get("canonical_url") else 0,
                "Structured Data":  min(seo.get("structured_data_count", 0) * 50, 100),
                "Image Alt Text":   max(0, 100 - (seo.get("images_missing_alt", 0) /
                                    max(seo.get("total_images", 1), 1) * 100)),
            }
            bar_colors = ["#34d399" if v >= 70 else ("#fbbf24" if v >= 40 else "#f87171")
                          for v in seo_items.values()]
            seo_fig = go.Figure(go.Bar(
                x=list(seo_items.values()), y=list(seo_items.keys()),
                orientation="h",
                marker=dict(color=bar_colors, line_width=0),
                text=[f"{v:.0f}%" for v in seo_items.values()],
                textposition="outside",
                textfont=dict(family="DM Mono", size=11),
            ))
            seo_fig.update_layout(
                **PLOTLY_LAYOUT,
                height=300,
                xaxis=dict(range=[0, 120], gridcolor="rgba(100,116,139,0.08)"),
                title=dict(text="SEO Signal Scores", font=dict(size=13, color="#64748b"), x=0),
            )
            st.plotly_chart(seo_fig, use_container_width=True, config={"displayModeBar": False})

            # Details grid
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

    # Tech Stack ───────────────────────────────────────────────────────────
    with t_tech:
        if tech.get("error"):
            st.error(tech["error"])
        else:
            tc1, tc2 = st.columns(2)
            cats = [
                ("Frontend Frameworks", "frontend", "cyan"),
                ("CMS / Platform",      "cms",      "purple"),
                ("Backend / Language",  "backend",  "amber"),
                ("Analytics Tools",     "analytics","green"),
                ("Hosting Provider",    "hosting",  "cyan"),
                ("CDN",                 "cdn",      "purple"),
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
            sc3.metric("Content-Type", tech.get("content_type", "—")[:40])

            with st.expander("Raw Response Headers"):
                st.json(tech.get("raw_headers", {}))

    # Security ─────────────────────────────────────────────────────────────
    with t_sec:
        s1, s2 = st.columns([1, 2])
        with s1:
            st.markdown('<p class="sec-head">SSL Certificate</p>', unsafe_allow_html=True)
            if ssl_info.get("error"):
                st.error(ssl_info["error"])
            else:
                if ssl_info.get("valid"):
                    st.success("✔ Valid SSL Certificate")
                else:
                    st.error("✘ Invalid / Missing SSL")
                st.metric("Issuer", ssl_info.get("issuer", "—"))
                st.metric("Expires", ssl_info.get("expiry_date", "—"))
                days = ssl_info.get("days_remaining")
                if days is not None:
                    if days < 14:
                        st.error(f"🚨 Expires in {days} days — renew immediately!")
                    elif days < 30:
                        st.warning(f"⚠ Expires in {days} days")
                    else:
                        st.info(f"ℹ {days} days remaining")
        with s2:
            st.markdown('<p class="sec-head">HTTP Security Headers</p>', unsafe_allow_html=True)
            if not sec_headers.get("error"):
                # Horizontal score bar
                sec_fig = go.Figure(go.Bar(
                    x=[sec_headers.get("score", 0)],
                    y=["Score"],
                    orientation="h",
                    marker=dict(
                        color=gauge_color(sec_headers.get("score", 0)),
                        line_width=0,
                    ),
                    text=[f"{sec_headers.get('score',0)}/100"],
                    textposition="outside",
                    textfont=dict(family="DM Mono", size=14),
                ))
                sec_fig.update_layout(
                    **PLOTLY_LAYOUT, height=100,
                    xaxis=dict(range=[0, 120]),
                    margin=dict(l=10, r=60, t=10, b=10),
                )
                st.plotly_chart(sec_fig, use_container_width=True, config={"displayModeBar": False})

                for key, info in sec_headers.get("headers_found", {}).items():
                    st.markdown(
                        f'{badge("✔  " + info["label"], "green")} '
                        f'<span style="font-size:0.78rem;color:#475569">{info["description"]}</span>',
                        unsafe_allow_html=True)
                for key, info in sec_headers.get("headers_missing", {}).items():
                    st.markdown(
                        f'{badge("✘  " + info["label"], "rose")} '
                        f'<span style="font-size:0.78rem;color:#475569">{info["description"]}</span>',
                        unsafe_allow_html=True)

    # Infrastructure ───────────────────────────────────────────────────────
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

    # Recommendations ──────────────────────────────────────────────────────
    with t_recs:
        critical = recs.get("critical_issues", [])
        wins     = recs.get("quick_wins", [])
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown('<p class="sec-head">🔴 Critical Issues</p>', unsafe_allow_html=True)
            if critical:
                for issue in critical:
                    st.markdown(f'<div class="issue-row">⚠ {issue}</div>', unsafe_allow_html=True)
            else:
                st.success("No critical issues found!")
        with rc2:
            st.markdown('<p class="sec-head">✅ Quick Wins</p>', unsafe_allow_html=True)
            if wins:
                for win in wins:
                    st.markdown(f'<div class="win-row">→ {win}</div>', unsafe_allow_html=True)
            else:
                st.info("Site looks well optimised!")

    # Raw Data ─────────────────────────────────────────────────────────────
    with t_raw:
        json_str = json.dumps(report, indent=2, default=str)
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("⬇ Download JSON", data=json_str,
                file_name=f"webscan_{meta.get('domain','report')}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json")
        with dl2:
            flat = {"url": meta.get("analysed_url"), "domain": meta.get("domain"),
                    "overall_score": meta.get("overall_score"), "timestamp": meta.get("timestamp"),
                    **{k: v for k, v in seo.items() if not isinstance(v, (list, dict))},
                    "ssl_valid": ssl_info.get("valid"), "ssl_days_remaining": ssl_info.get("days_remaining"),
                    "security_score": sec_headers.get("score")}
            st.download_button("⬇ Download CSV",
                data=pd.DataFrame([flat]).to_csv(index=False),
                file_name=f"webscan_{meta.get('domain','report')}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv")
        with st.expander("View raw JSON"):
            st.json(report)


# ════════════════════════════════════════════════════════════════════════════════
#  COMPETITOR ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════

elif go_btn and mode == "Competitor Analysis" and len(comp_urls) >= 2:
    with st.spinner(f"🔬 Analysing {len(comp_urls)} sites in parallel — please wait 20–40 seconds…"):
        comp_report = run_competitor_analysis(comp_urls)

    sites      = comp_report["sites"]
    comparison = comp_report["comparison"]
    winner     = comp_report["winner"]
    radar_data = comp_report["radar_data"]
    tech_comp  = comp_report["tech_comparison"]
    primary    = sites[0]["domain"] if sites else ""

    st.markdown("## 🏆 Competitor Intelligence Report")

    # ── Score leaderboard ─────────────────────────────────────────────────
    st.markdown('<p class="sec-head">Overall Health Scores</p>', unsafe_allow_html=True)
    st.plotly_chart(make_score_hbar(sites), use_container_width=True,
                    config={"displayModeBar": False})

    # ── Score cards per site ──────────────────────────────────────────────
    cols = st.columns(len(sites))
    accents = [
        "linear-gradient(90deg,#38bdf8,#818cf8)",
        "linear-gradient(90deg,#a78bfa,#f472b6)",
        "linear-gradient(90deg,#34d399,#0ea5e9)",
        "linear-gradient(90deg,#fbbf24,#f87171)",
    ]
    for i, (col, site) in enumerate(zip(cols, sites)):
        with col:
            ssl_ok   = site.get("ssl", {}).get("valid", False)
            ssl_days = site.get("ssl", {}).get("days_remaining", "—")
            is_primary = site["domain"] == primary
            label = f"{'🏠 ' if is_primary else '🥊 '}{site['domain']}"
            st.markdown(render_score_card(
                site.get("overall_score", 0), label,
                f"SSL {'✔' if ssl_ok else '✘'}  ·  {ssl_days}d remaining",
                accents[i % len(accents)]
            ), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Radar + grouped bar ───────────────────────────────────────────────
    if len(radar_data) >= 2:
        rad_col, bar_col = st.columns([1, 1])
        with rad_col:
            st.plotly_chart(make_radar(radar_data), use_container_width=True,
                            config={"displayModeBar": False})
        with bar_col:
            st.plotly_chart(make_bar_comparison(comparison, [
                "overall_score", "security_score",
                "security_headers_found", "structured_data_count",
            ]), use_container_width=True, config={"displayModeBar": False})

    # ── Detailed comparison table ─────────────────────────────────────────
    st.markdown('<p class="sec-head">Full Metrics Comparison</p>', unsafe_allow_html=True)
    domains = [s["domain"] for s in sites]
    lower_better = {"load_time_seconds", "page_size_kb", "images_missing_alt"}

    table_html = '<table class="comp-table"><thead><tr><th>Metric</th>'
    for d in domains:
        is_you = d == primary
        table_html += f'<th>{"🏠 " if is_you else "🥊 "}{d}</th>'
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
        table_html += f'<tr><td style="color:#64748b;font-family:\'DM Mono\',monospace;font-size:0.78rem">{row["label"]}</td>'
        best_domain = winner.get(key)
        for d in domains:
            val = row["values"].get(d, "—")
            if val == 1 and key in ("has_canonical", "has_meta_description"):
                val = "✔"
            elif val == 0 and key in ("has_canonical", "has_meta_description"):
                val = "✘"
            is_best  = (d == best_domain)
            is_worst = (val not in ("✔", "✘")) and (len(domains) > 1) and isinstance(val, (int, float)) and all(
                (val <= row["values"].get(od, val)) if key not in lower_better else (val >= row["values"].get(od, val))
                for od in domains if od != d
            )
            cls = "best" if is_best else ("worst" if is_worst else "")
            table_html += f'<td class="{cls}">{val}{"  ★" if is_best else ""}</td>'
        table_html += "</tr>"
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

    # ── Technology landscape treemap ──────────────────────────────────────
    st.markdown('<p class="sec-head">Technology Landscape</p>', unsafe_allow_html=True)
    treemap = make_treemap_tech(tech_comp)
    if treemap:
        st.plotly_chart(treemap, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No technology data available for treemap")

    # ── Side-by-side tech badges ──────────────────────────────────────────
    st.markdown('<p class="sec-head">Technology Stack Breakdown</p>', unsafe_allow_html=True)
    tech_cols = st.columns(len(sites))
    for col, site in zip(tech_cols, sites):
        d    = site["domain"]
        tc   = tech_comp.get(d, {})
        with col:
            st.markdown(f"**{d}**")
            for cat_label, cat_key, col_kind in [
                ("Frontend", "frontend", "cyan"), ("CMS", "cms", "purple"),
                ("Analytics", "analytics", "green"), ("Hosting", "hosting", "amber"),
            ]:
                items = tc.get(cat_key, [])
                if items:
                    st.markdown(f"<small style='color:#475569'>{cat_label}</small><br>" +
                                tech_badges(items, col_kind), unsafe_allow_html=True)

    # ── Per-site recommendations ──────────────────────────────────────────
    st.markdown('<p class="sec-head">Site-by-Site Recommendations</p>', unsafe_allow_html=True)
    rec_tabs = st.tabs([f"{'🏠' if s['domain']==primary else '🥊'} {s['domain']}" for s in sites])
    for tab, site in zip(rec_tabs, sites):
        with tab:
            recs = site.get("recommendations", {})
            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown('<p class="sec-head">Critical Issues</p>', unsafe_allow_html=True)
                issues = recs.get("critical_issues", [])
                if issues:
                    for issue in issues:
                        st.markdown(f'<div class="issue-row">⚠ {issue}</div>', unsafe_allow_html=True)
                else:
                    st.success("No critical issues!")
            with rc2:
                st.markdown('<p class="sec-head">Quick Wins</p>', unsafe_allow_html=True)
                wins = recs.get("quick_wins", [])
                if wins:
                    for win in wins:
                        st.markdown(f'<div class="win-row">→ {win}</div>', unsafe_allow_html=True)
                else:
                    st.info("Looking good!")

    # ── Download ──────────────────────────────────────────────────────────
    st.markdown('<p class="sec-head">Export</p>', unsafe_allow_html=True)
    json_str = json.dumps(comp_report, indent=2, default=str)
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button("⬇ Full JSON Report", data=json_str,
            file_name=f"competitor_analysis_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json")
    with dl2:
        rows = [{
            "domain": s["domain"], "url": s["url"],
            "overall_score": s.get("overall_score"),
            "security_score": s.get("security_headers", {}).get("score"),
            "load_time": s.get("seo", {}).get("load_time_seconds"),
            "page_size_kb": s.get("seo", {}).get("page_size_kb"),
            "ssl_valid": s.get("ssl", {}).get("valid"),
            "ssl_days": s.get("ssl", {}).get("days_remaining"),
        } for s in sites]
        st.download_button("⬇ Summary CSV",
            data=pd.DataFrame(rows).to_csv(index=False),
            file_name=f"competitor_summary_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv")

elif go_btn and mode == "Competitor Analysis" and len(comp_urls) < 2:
    st.warning("Please enter at least 2 URLs (your site + 1 competitor) for competitor analysis.")

elif go_btn and mode == "Single Site" and not url_input.strip():
    st.warning("Please enter a URL to analyse.")

# ── Empty state ───────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🌐</div>
        <div class="empty-title">Enter a URL above and click Analyse</div>
        <div class="empty-desc">
            Get instant insights on SEO, security headers, SSL, DNS, technology stack,
            and actionable recommendations — or compare up to 4 sites head-to-head.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature pills
    st.markdown("""
    <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:0.5rem;margin-top:1rem;">
        <span class="badge bg-cyan">SEO Analysis</span>
        <span class="badge bg-purple">Tech Detection</span>
        <span class="badge bg-green">SSL Check</span>
        <span class="badge bg-amber">Security Headers</span>
        <span class="badge bg-slate">DNS Records</span>
        <span class="badge bg-rose">Competitor Analysis</span>
    </div>
    """, unsafe_allow_html=True)
