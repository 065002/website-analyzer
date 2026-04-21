"""
app.py
Streamlit dashboard for the Website Analysis Tool.
"""

import json
import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="WebScan Pro — Website Analyser",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background-color: #0d0f14; color: #e8eaf0; }

.hero-title {
    font-size: 3rem; font-weight: 800; letter-spacing: -1px;
    background: linear-gradient(135deg, #4ff7c0 0%, #7b6ff5 60%, #ff6b9d 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.25rem;
}
.hero-sub {
    color: #7c8197; font-family: 'Space Mono', monospace;
    font-size: 0.85rem; letter-spacing: 0.08em;
    text-transform: uppercase; margin-bottom: 2rem;
}
.score-card {
    background: linear-gradient(135deg, #151821 0%, #1c2030 100%);
    border: 1px solid #2a2f45; border-radius: 16px;
    padding: 1.5rem; text-align: center;
}
.score-number { font-size: 4rem; font-weight: 800; font-family: 'Space Mono', monospace; line-height: 1; }
.score-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; color: #7c8197; margin-top: 0.5rem; }
.score-good { color: #4ff7c0; }
.score-mid  { color: #ffcc4d; }
.score-bad  { color: #ff6b6b; }

.metric-card {
    background: #151821; border: 1px solid #2a2f45;
    border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 0.5rem;
}
.metric-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #7c8197; }
.metric-value { font-size: 1.1rem; font-weight: 700; color: #e8eaf0; margin-top: 2px; }

.badge {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600; margin: 2px 3px;
    font-family: 'Space Mono', monospace;
}
.badge-green  { background: #0d2b20; color: #4ff7c0; border: 1px solid #1a5c40; }
.badge-red    { background: #2b0d0d; color: #ff6b6b; border: 1px solid #5c1a1a; }
.badge-yellow { background: #2b240d; color: #ffcc4d; border: 1px solid #5c4a1a; }
.badge-blue   { background: #0d1a2b; color: #6eb5ff; border: 1px solid #1a3a5c; }
.badge-purple { background: #1a0d2b; color: #c06bff; border: 1px solid #3d1a5c; }

.section-header {
    font-size: 1.1rem; font-weight: 700; color: #e8eaf0;
    border-left: 3px solid #4ff7c0; padding-left: 0.75rem;
    margin: 1.25rem 0 0.75rem;
}
.issue-row {
    background: #1c0d0d; border: 1px solid #3d1a1a; border-radius: 8px;
    padding: 0.6rem 0.9rem; margin-bottom: 0.4rem;
    font-size: 0.88rem; color: #ff9a9a;
}
.win-row {
    background: #0d1c14; border: 1px solid #1a3d26; border-radius: 8px;
    padding: 0.6rem 0.9rem; margin-bottom: 0.4rem;
    font-size: 0.88rem; color: #7dffc0;
}
div[data-testid="stTextInput"] input {
    background: #151821 !important; border: 1px solid #2a2f45 !important;
    color: #e8eaf0 !important; border-radius: 10px !important;
    font-family: 'Space Mono', monospace !important;
}
div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #4ff7c0, #7b6ff5) !important;
    color: #0d0f14 !important; font-weight: 700 !important;
    border: none !important; border-radius: 10px !important;
    padding: 0.55rem 2rem !important; font-family: 'Syne', sans-serif !important;
    font-size: 1rem !important; width: 100%;
}
</style>
""", unsafe_allow_html=True)

from scripts.analyzer import analyze_website


def score_color_class(score: int) -> str:
    if score >= 70:
        return "score-good"
    if score >= 40:
        return "score-mid"
    return "score-bad"


def render_badge(text: str, kind: str = "blue") -> str:
    return f'<span class="badge badge-{kind}">{text}</span>'


def render_tech_badges(items: list, kind: str = "blue") -> str:
    if not items:
        return '<span style="color:#7c8197;font-size:0.85rem;">None detected</span>'
    return " ".join(render_badge(item, kind) for item in items)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">🔍 WebScan Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Technical · SEO · Security · Infrastructure Analysis</p>', unsafe_allow_html=True)

col_input, col_btn = st.columns([5, 1])
with col_input:
    url_input = st.text_input("", placeholder="https://example.com",
                               label_visibility="collapsed", key="url_field")
with col_btn:
    analyse_clicked = st.button("Analyse →")

st.markdown("---")

if analyse_clicked and url_input.strip():
    with st.spinner("🔬 Running full analysis — this takes 10–25 seconds…"):
        report = analyze_website(url_input.strip())

    meta        = report.get("meta", {})
    seo         = report.get("seo", {})
    tech        = report.get("technologies", {})
    ssl_info    = report.get("ssl", {})
    sec_headers = report.get("security_headers", {})
    dns         = report.get("dns", {})
    recs        = report.get("recommendations", {})
    overall     = meta.get("overall_score", 0)

    # ── Top summary ────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        cls = score_color_class(overall)
        st.markdown(f"""<div class="score-card">
            <div class="score-number {cls}">{overall}</div>
            <div class="score-label">Health Score</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Load Time</div>
            <div class="metric-value">{seo.get('load_time_seconds', '—')} s</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Page Size</div>
            <div class="metric-value">{seo.get('page_size_kb', '—')} KB</div></div>""", unsafe_allow_html=True)
    with c4:
        ssl_ok   = ssl_info.get("valid", False)
        ssl_days = ssl_info.get("days_remaining", "—")
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">SSL Certificate</div>
            <div class="metric-value">{'✔ Valid' if ssl_ok else '✘ Invalid'} · {ssl_days}d</div></div>""", unsafe_allow_html=True)
    with c5:
        sec_score = sec_headers.get("score", 0)
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Security Score</div>
            <div class="metric-value {score_color_class(sec_score)}">{sec_score} / 100</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_seo, tab_tech, tab_sec, tab_infra, tab_recs, tab_raw = st.tabs(
        ["📄 SEO", "⚙️ Tech Stack", "🔒 Security", "🌐 Infrastructure", "💡 Recommendations", "{ } Raw Report"]
    )

    # ── SEO Tab ────────────────────────────────────────────────────────────
    with tab_seo:
        if seo.get("error"):
            st.error(f"SEO analysis failed: {seo['error']}")
        else:
            st.markdown('<p class="section-header">On-Page Signals</p>', unsafe_allow_html=True)
            df_rows = [
                ("Title Tag",        seo.get("title", "—"),                           f"{seo.get('title_length',0)} chars",  "30–60 chars"),
                ("Meta Description", (seo.get("meta_description") or "—")[:80],       f"{seo.get('meta_description_length',0)} chars", "120–160 chars"),
                ("H1 Tags",          str(seo.get("h1_count", 0)),                     seo.get("h1_count", 0),                "Exactly 1"),
                ("H2 Tags",          str(seo.get("h2_count", 0)),                     seo.get("h2_count", 0),                "≥ 1"),
                ("Canonical URL",    "✔ Present" if seo.get("canonical_url") else "✘ Missing", "—", "Required"),
                ("Structured Data",  f"{seo.get('structured_data_count', 0)} block(s)", seo.get("structured_data_count",0), "≥ 1"),
                ("Images w/ Alt",    f"{seo.get('images_with_alt',0)} / {seo.get('total_images',0)}", "—", "100%"),
            ]
            st.dataframe(pd.DataFrame(df_rows, columns=["Check", "Value", "Count", "Ideal"]),
                         use_container_width=True, hide_index=True)

            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown('<p class="section-header">Title Tag</p>', unsafe_allow_html=True)
                st.code(seo.get("title") or "(none)", language=None)
                st.markdown('<p class="section-header">Meta Description</p>', unsafe_allow_html=True)
                st.code(seo.get("meta_description") or "(none)", language=None)
                st.markdown('<p class="section-header">Canonical URL</p>', unsafe_allow_html=True)
                st.code(seo.get("canonical_url") or "(none)", language=None)
            with col_r:
                st.markdown('<p class="section-header">H1 Tags</p>', unsafe_allow_html=True)
                for h in seo.get("h1_tags", []):
                    st.code(h, language=None)
                if not seo.get("h1_tags"):
                    st.warning("No H1 tags found")
                st.markdown('<p class="section-header">H2 Tags (first 5)</p>', unsafe_allow_html=True)
                for h in seo.get("h2_tags", [])[:5]:
                    st.code(h, language=None)

            st.markdown('<p class="section-header">Links & Images</p>', unsafe_allow_html=True)
            lc1, lc2, lc3, lc4 = st.columns(4)
            lc1.metric("Internal Links",      seo.get("internal_links", 0))
            lc2.metric("External Links",      seo.get("external_links", 0))
            lc3.metric("Total Images",        seo.get("total_images", 0))
            lc4.metric("Images Missing Alt",  seo.get("images_missing_alt", 0))

            if seo.get("structured_data"):
                st.markdown('<p class="section-header">JSON-LD Structured Data</p>', unsafe_allow_html=True)
                for i, sd in enumerate(seo["structured_data"]):
                    with st.expander(f"Block {i+1}: {sd.get('@type', 'Unknown')}"):
                        st.json(sd)

    # ── Tech Stack Tab ─────────────────────────────────────────────────────
    with tab_tech:
        if tech.get("error"):
            st.error(f"Tech detection failed: {tech['error']}")
        else:
            st.markdown('<p class="section-header">Detected Technologies</p>', unsafe_allow_html=True)
            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown("**Frontend Frameworks**")
                st.markdown(render_tech_badges(tech.get("frontend", []), "purple"), unsafe_allow_html=True)
                st.markdown("**CMS / Platform**")
                st.markdown(render_tech_badges(tech.get("cms", []), "blue"), unsafe_allow_html=True)
                st.markdown("**Backend / Language**")
                st.markdown(render_tech_badges(tech.get("backend", []), "yellow"), unsafe_allow_html=True)
            with tc2:
                st.markdown("**Analytics Tools**")
                st.markdown(render_tech_badges(tech.get("analytics", []), "green"), unsafe_allow_html=True)
                st.markdown("**Hosting Provider**")
                st.markdown(render_tech_badges(tech.get("hosting", []), "blue"), unsafe_allow_html=True)
                st.markdown("**CDN**")
                st.markdown(render_tech_badges(tech.get("cdn", []), "purple"), unsafe_allow_html=True)

            st.markdown('<p class="section-header">Server Info</p>', unsafe_allow_html=True)
            sc1, sc2 = st.columns(2)
            sc1.metric("Server",      tech.get("server", "Unknown"))
            sc2.metric("Powered By",  tech.get("powered_by") or "—")
            with st.expander("Raw Response Headers"):
                st.json(tech.get("raw_headers", {}))

    # ── Security Tab ───────────────────────────────────────────────────────
    with tab_sec:
        sec_col1, sec_col2 = st.columns([1, 2])
        with sec_col1:
            st.markdown('<p class="section-header">SSL Certificate</p>', unsafe_allow_html=True)
            if ssl_info.get("error"):
                st.error(ssl_info["error"])
            else:
                if ssl_info.get("valid"):
                    st.success("✔ Valid SSL Certificate")
                else:
                    st.error("✘ Invalid SSL")
                st.metric("Issuer", ssl_info.get("issuer", "—"))
                st.metric("Expiry", ssl_info.get("expiry_date", "—"))
                days = ssl_info.get("days_remaining", 0)
                if days is not None:
                    if days < 30:
                        st.warning(f"⚠ Expires in {days} days!")
                    else:
                        st.info(f"ℹ {days} days remaining")

        with sec_col2:
            st.markdown('<p class="section-header">HTTP Security Headers</p>', unsafe_allow_html=True)
            if sec_headers.get("error"):
                st.error(sec_headers["error"])
            else:
                for key, info in sec_headers.get("headers_found", {}).items():
                    st.markdown(
                        f'<span class="badge badge-green">✔ {info["label"]}</span> '
                        f'<span style="font-size:0.8rem;color:#7c8197">{info["description"]}</span>',
                        unsafe_allow_html=True)
                for key, info in sec_headers.get("headers_missing", {}).items():
                    st.markdown(
                        f'<span class="badge badge-red">✘ {info["label"]}</span> '
                        f'<span style="font-size:0.8rem;color:#7c8197">{info["description"]}</span>',
                        unsafe_allow_html=True)

    # ── Infrastructure Tab ─────────────────────────────────────────────────
    with tab_infra:
        st.markdown('<p class="section-header">DNS Records</p>', unsafe_allow_html=True)
        if dns.get("error") and "NXDOMAIN" in dns.get("error", ""):
            st.error(dns["error"])
        else:
            dns_rows = []
            for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]:
                for r in dns.get(rtype, []):
                    dns_rows.append({"Type": rtype, "Record": r})
            if dns_rows:
                st.dataframe(pd.DataFrame(dns_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No DNS records retrieved")

            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown("**IP Addresses**")
                for ip in dns.get("ip_addresses", []):
                    st.code(ip, language=None)
            with dc2:
                st.markdown("**Nameservers**")
                for ns in dns.get("nameservers", []):
                    st.code(ns, language=None)

    # ── Recommendations Tab ────────────────────────────────────────────────
    with tab_recs:
        critical = recs.get("critical_issues", [])
        wins     = recs.get("quick_wins", [])

        st.markdown('<p class="section-header">🔴 Critical Issues</p>', unsafe_allow_html=True)
        if critical:
            for issue in critical:
                st.markdown(f'<div class="issue-row">⚠ {issue}</div>', unsafe_allow_html=True)
        else:
            st.success("No critical issues found — great work!")

        st.markdown('<p class="section-header">✅ Quick Wins</p>', unsafe_allow_html=True)
        if wins:
            for win in wins:
                st.markdown(f'<div class="win-row">→ {win}</div>', unsafe_allow_html=True)
        else:
            st.info("No quick wins identified — site looks well optimised!")

    # ── Raw Report Tab ─────────────────────────────────────────────────────
    with tab_raw:
        st.markdown('<p class="section-header">Full JSON Report</p>', unsafe_allow_html=True)
        json_str = json.dumps(report, indent=2, default=str)
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                label="⬇ Download JSON",
                data=json_str,
                file_name=f"webscan_{meta.get('domain','report')}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
            )
        with dl2:
            flat = {
                "url": meta.get("analysed_url"), "domain": meta.get("domain"),
                "overall_score": meta.get("overall_score"), "timestamp": meta.get("timestamp"),
                **{k: v for k, v in seo.items() if not isinstance(v, (list, dict))},
                "ssl_valid": ssl_info.get("valid"), "ssl_days_remaining": ssl_info.get("days_remaining"),
                "security_score": sec_headers.get("score"),
            }
            st.download_button(
                label="⬇ Download CSV",
                data=pd.DataFrame([flat]).to_csv(index=False),
                file_name=f"webscan_{meta.get('domain','report')}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
        with st.expander("View raw JSON", expanded=False):
            st.json(report)

elif analyse_clicked and not url_input.strip():
    st.warning("Please enter a URL to analyse.")
else:
    st.markdown("""
<div style="text-align:center;padding:3rem 0;color:#7c8197;">
    <div style="font-size:4rem;margin-bottom:1rem;">🌐</div>
    <p style="font-size:1.1rem;font-weight:600;color:#b0b5cc;">Enter any URL above and click Analyse</p>
    <p style="font-size:0.85rem;margin-top:0.5rem;">
        Checks SEO tags · SSL validity · Security headers · DNS records · Technology stack
    </p>
</div>
""", unsafe_allow_html=True)
