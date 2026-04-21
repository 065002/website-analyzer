"""
app.py — WebScan Pro | Website Analysis Tool
=============================================
Paste this ENTIRE file as your app.py (replaces existing content).
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import re
import time
import socket
import ssl
import whois
import datetime
from urllib.parse import urlparse, urljoin
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="WebScan Pro — Website Analysis Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 10px;
        padding: 16px 20px;
        margin: 6px 0;
        border-left: 4px solid #4F8EF7;
    }
    .score-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }
    .good  { background:#1a3a2e; color:#4FD18E; }
    .warn  { background:#3a2e1a; color:#F7C948; }
    .bad   { background:#3a1a1a; color:#F76B6B; }
    div[data-testid="stTabs"] button { font-size: 15px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════════════════════════════

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ════════════════════════════════════════════════════════════════════
# SHARED HELPERS
# ════════════════════════════════════════════════════════════════════

def safe_get(url: str, timeout: int = 12):
    """Fetch URL safely. Returns (response, load_ms) or (None, None)."""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        t0 = time.time()
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r, round((time.time() - t0) * 1000)
    except Exception:
        return None, None


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


def score_color(score: int) -> str:
    if score >= 70: return "#4FD18E"
    if score >= 40: return "#F7C948"
    return "#F76B6B"


def badge(text, cls):
    return f'<span class="score-badge {cls}">{text}</span>'


# ════════════════════════════════════════════════════════════════════
# ── TAB 1: WEBSITE ANALYSIS ─────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════

def get_ssl_info(hostname: str) -> dict:
    try:
        ctx = ssl.create_default_context()
        conn = ctx.wrap_socket(socket.socket(), server_hostname=hostname)
        conn.settimeout(5)
        conn.connect((hostname, 443))
        cert = conn.getpeercert()
        conn.close()
        exp = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days_left = (exp - datetime.datetime.utcnow()).days
        return {"valid": True, "expires": exp.strftime("%Y-%m-%d"), "days_left": days_left}
    except Exception:
        return {"valid": False, "expires": "N/A", "days_left": 0}


def analyze_website(url: str) -> dict:
    result = {
        "url": url, "reachable": False, "status": None, "load_ms": None,
        "title": "", "title_len": 0, "meta_desc": "", "meta_desc_len": 0,
        "h1": [], "h2_count": 0, "h3_count": 0,
        "word_count": 0, "img_count": 0, "img_no_alt": 0,
        "internal_links": 0, "external_links": 0, "broken_links": 0,
        "has_canonical": False, "has_og": False, "has_schema": False,
        "has_sitemap": False, "has_robots": False,
        "https": url.startswith("https"), "ssl": {},
        "technologies": [], "error": None,
    }

    resp, ms = safe_get(url)
    result["load_ms"] = ms
    if resp is None:
        result["error"] = "Could not reach the URL"
        return result

    result["reachable"] = True
    result["status"] = resp.status_code
    if resp.status_code != 200:
        result["error"] = f"HTTP {resp.status_code}"
        return result

    # SSL
    parsed = urlparse(url)
    if parsed.scheme == "https":
        result["ssl"] = get_ssl_info(parsed.netloc)

    soup = BeautifulSoup(resp.text, "html.parser")
    domain = parsed.netloc

    # Basic SEO
    t = soup.find("title")
    if t:
        result["title"] = t.get_text(strip=True)
        result["title_len"] = len(result["title"])
    m = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if m and m.get("content"):
        result["meta_desc"] = m["content"].strip()
        result["meta_desc_len"] = len(result["meta_desc"])

    result["h1"] = [h.get_text(strip=True) for h in soup.find_all("h1")]
    result["h2_count"] = len(soup.find_all("h2"))
    result["h3_count"] = len(soup.find_all("h3"))

    body = soup.find("body")
    if body:
        result["word_count"] = len(body.get_text(separator=" ").split())

    imgs = soup.find_all("img")
    result["img_count"] = len(imgs)
    result["img_no_alt"] = sum(1 for i in imgs if not i.get("alt", "").strip())

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and domain not in href:
            result["external_links"] += 1
        else:
            result["internal_links"] += 1

    result["has_canonical"] = bool(soup.find("link", rel="canonical"))
    result["has_og"] = bool(soup.find("meta", property=re.compile("^og:", re.I)))
    result["has_schema"] = bool(soup.find("script", type="application/ld+json"))

    # Robots / sitemap
    rb, _ = safe_get(f"{url.rstrip('/')}/robots.txt", timeout=5)
    result["has_robots"] = rb is not None and rb.status_code == 200
    sm, _ = safe_get(f"{url.rstrip('/')}/sitemap.xml", timeout=5)
    result["has_sitemap"] = sm is not None and sm.status_code == 200

    # Tech detection (basic)
    html_raw = resp.text.lower()
    techs = []
    if "wp-content" in html_raw: techs.append("WordPress")
    if "shopify" in html_raw: techs.append("Shopify")
    if "gatsby" in html_raw: techs.append("Gatsby")
    if "next.js" in html_raw or "__next" in html_raw: techs.append("Next.js")
    if "react" in html_raw: techs.append("React")
    if "vue" in html_raw: techs.append("Vue.js")
    if "jquery" in html_raw: techs.append("jQuery")
    if "bootstrap" in html_raw: techs.append("Bootstrap")
    if "google-analytics" in html_raw or "gtag" in html_raw: techs.append("Google Analytics")
    if "cloudflare" in resp.headers.get("server", "").lower(): techs.append("Cloudflare")
    result["technologies"] = techs

    return result


def compute_seo_score(r: dict) -> dict:
    scores = {}
    # On-Page (30)
    op = 0
    if 40 <= r["title_len"] <= 65: op += 10
    elif r["title_len"] > 0: op += 5
    if 120 <= r["meta_desc_len"] <= 160: op += 10
    elif r["meta_desc_len"] > 0: op += 5
    if len(r["h1"]) == 1: op += 10
    elif len(r["h1"]) > 0: op += 5
    scores["On-Page"] = op

    # Technical (30)
    tc = 0
    if r["https"]: tc += 8
    if r["has_canonical"]: tc += 7
    if r["has_schema"]: tc += 5
    if r["has_robots"]: tc += 5
    if r["has_sitemap"]: tc += 5
    scores["Technical"] = tc

    # Content (20)
    ct = 0
    if r["word_count"] >= 1500: ct += 12
    elif r["word_count"] >= 800: ct += 8
    elif r["word_count"] > 0: ct += 4
    if r["h2_count"] >= 3: ct += 4
    if r["img_count"] > 0 and r["img_no_alt"] / r["img_count"] < 0.3: ct += 4
    scores["Content"] = ct

    # Performance (10)
    lt = r["load_ms"] or 9999
    if lt < 1000: scores["Performance"] = 10
    elif lt < 2000: scores["Performance"] = 7
    elif lt < 3500: scores["Performance"] = 4
    else: scores["Performance"] = 1

    # Social (10)
    sx = 0
    if r["has_og"]: sx += 5
    if r["external_links"] >= 3: sx += 3
    if r["internal_links"] >= 5: sx += 2
    scores["Social"] = sx

    scores["Overall"] = sum(scores.values())
    return scores


def render_website_analysis():
    st.markdown("## 🔍 Website Analysis")
    st.markdown("Get a full SEO, security, content & technical audit of any webpage.")

    url_in = st.text_input("Enter Website URL", placeholder="https://example.com", key="wa_url")
    if not st.button("🚀 Analyse Website", key="wa_btn", use_container_width=True):
        return

    url = normalize_url(url_in)
    with st.spinner("Scanning website…"):
        r = analyze_website(url)
        scores = compute_seo_score(r)

    if r.get("error") and not r["reachable"]:
        st.error(f"❌ {r['error']}")
        return

    overall = scores["Overall"]
    col = score_color(overall)

    # ── Score banner ──
    st.markdown(
        f"""<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);
        border-left:5px solid {col};border-radius:8px;padding:18px 24px;margin:12px 0'>
        <h2 style='margin:0;color:{col}'>Overall SEO Score: {overall}/100</h2>
        <p style='color:#aaa;margin:4px 0 0'>{url} &nbsp;|&nbsp; 
        Status: {r["status"]} &nbsp;|&nbsp; Load: {r["load_ms"]}ms</p></div>""",
        unsafe_allow_html=True,
    )

    # ── Gauge ──
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=overall,
        gauge={"axis": {"range": [0, 100]},
               "bar": {"color": col},
               "steps": [{"range": [0,40],"color":"#2a1a1a"},
                          {"range": [40,70],"color":"#2a2a1a"},
                          {"range": [70,100],"color":"#1a2a1a"}]},
        title={"text": "SEO Score"},
    ))
    fig_gauge.update_layout(height=260, template="plotly_dark",
                            margin=dict(t=30,b=0,l=0,r=0))

    # ── Category bar ──
    cats = ["On-Page","Technical","Content","Performance","Social"]
    max_map = {"On-Page":30,"Technical":30,"Content":20,"Performance":10,"Social":10}
    pct = [round(scores[c]/max_map[c]*100) for c in cats]
    fig_bar = px.bar(x=cats, y=pct, color=pct,
                     color_continuous_scale=["#F76B6B","#F7C948","#4FD18E"],
                     range_color=[0,100], text=[f"{p}%" for p in pct],
                     title="Score by Category (%)")
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(coloraxis_showscale=False, height=300,
                          template="plotly_dark", showlegend=False,
                          yaxis_range=[0,120])

    c1, c2 = st.columns([1,1.5])
    with c1: st.plotly_chart(fig_gauge, use_container_width=True)
    with c2: st.plotly_chart(fig_bar, use_container_width=True)

    # ── Detail tabs ──
    t1,t2,t3,t4,t5 = st.tabs(["📝 On-Page","⚙️ Technical","📄 Content","🔒 Security","🛠 Tech Stack"])

    with t1:
        col1, col2, col3 = st.columns(3)
        col1.metric("Title Length", f"{r['title_len']} chars",
                    "✅ Good" if 40<=r['title_len']<=65 else "⚠️ Adjust")
        col2.metric("Meta Desc Length", f"{r['meta_desc_len']} chars",
                    "✅ Good" if 120<=r['meta_desc_len']<=160 else "⚠️ Adjust")
        col3.metric("H1 Tags", len(r["h1"]),
                    "✅ Good" if len(r["h1"])==1 else "⚠️ Should be 1")
        st.markdown(f"**Title:** {r['title']}")
        st.markdown(f"**Meta Description:** {r['meta_desc']}")
        if r["h1"]: st.markdown(f"**H1 Content:** {r['h1'][0]}")
        col4, col5 = st.columns(2)
        col4.metric("H2 Tags", r["h2_count"])
        col5.metric("H3 Tags", r["h3_count"])
        st.metric("Canonical Tag", "✅ Present" if r["has_canonical"] else "❌ Missing")
        st.metric("OG Tags", "✅ Present" if r["has_og"] else "❌ Missing")

    with t2:
        cols = st.columns(3)
        checks = [
            ("HTTPS", r["https"]),
            ("Canonical", r["has_canonical"]),
            ("Schema Markup", r["has_schema"]),
            ("robots.txt", r["has_robots"]),
            ("sitemap.xml", r["has_sitemap"]),
            ("OG Tags", r["has_og"]),
        ]
        for i,(name,val) in enumerate(checks):
            with cols[i%3]:
                st.markdown(f"{'✅' if val else '❌'} **{name}**")
        st.metric("Page Load Time", f"{r['load_ms']} ms",
                  "⚡ Fast" if (r['load_ms'] or 9999)<2000 else "🐢 Slow")

    with t3:
        col1, col2, col3 = st.columns(3)
        col1.metric("Word Count", r["word_count"])
        col2.metric("Images", r["img_count"])
        col3.metric("Images Missing Alt", r["img_no_alt"],
                    "✅ Good" if r["img_no_alt"]==0 else "⚠️ Fix alt tags")
        col4, col5 = st.columns(2)
        col4.metric("Internal Links", r["internal_links"])
        col5.metric("External Links", r["external_links"])

    with t4:
        if r["ssl"]:
            ssl_d = r["ssl"]
            if ssl_d.get("valid"):
                days = ssl_d["days_left"]
                c = "#4FD18E" if days > 30 else "#F76B6B"
                st.markdown(
                    f"<div style='border-left:4px solid {c};padding:12px;background:#1a1a2e;border-radius:6px'>"
                    f"🔒 <strong>SSL Certificate Valid</strong><br>"
                    f"Expires: {ssl_d['expires']} ({days} days remaining)</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.error("❌ SSL Certificate invalid or not found")
        else:
            st.warning("⚠️ Site is not using HTTPS")

    with t5:
        if r["technologies"]:
            for tech in r["technologies"]:
                st.markdown(f"🔧 **{tech}**")
        else:
            st.info("No common technologies detected")


# ════════════════════════════════════════════════════════════════════
# ── TAB 2: COMPETITOR ANALYSIS ──────────────────────────────────────
# ════════════════════════════════════════════════════════════════════

def extract_competitor_metrics(url: str) -> dict:
    m = {
        "url": url, "load_ms": None, "status": None,
        "title_len": 0, "meta_desc_len": 0,
        "h1_count": 0, "h2_count": 0, "word_count": 0,
        "img_count": 0, "img_with_alt": 0,
        "internal_links": 0, "external_links": 0,
        "has_canonical": False, "has_og": False,
        "has_schema": False, "https": url.startswith("https"),
        "error": None,
    }
    resp, ms = safe_get(url)
    m["load_ms"] = ms
    if resp is None:
        m["error"] = "Unreachable"; return m
    m["status"] = resp.status_code
    if resp.status_code != 200:
        m["error"] = f"HTTP {resp.status_code}"; return m

    soup = BeautifulSoup(resp.text, "html.parser")
    domain = urlparse(url).netloc

    t = soup.find("title")
    if t: m["title_len"] = len(t.get_text(strip=True))
    d = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if d and d.get("content"): m["meta_desc_len"] = len(d["content"].strip())

    m["h1_count"] = len(soup.find_all("h1"))
    m["h2_count"] = len(soup.find_all("h2"))

    body = soup.find("body")
    if body: m["word_count"] = len(body.get_text(separator=" ").split())

    imgs = soup.find_all("img")
    m["img_count"] = len(imgs)
    m["img_with_alt"] = sum(1 for i in imgs if i.get("alt","").strip())

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and domain not in href:
            m["external_links"] += 1
        else:
            m["internal_links"] += 1

    m["has_canonical"] = bool(soup.find("link", rel="canonical"))
    m["has_og"] = bool(soup.find("meta", property=re.compile("^og:", re.I)))
    m["has_schema"] = bool(soup.find("script", type="application/ld+json"))
    return m


def score_competitor(m: dict) -> dict:
    s = {}
    op = 0
    if 40<=m["title_len"]<=65: op+=10
    elif m["title_len"]>0: op+=5
    if 120<=m["meta_desc_len"]<=160: op+=10
    elif m["meta_desc_len"]>0: op+=5
    if m["h1_count"]==1: op+=10
    elif m["h1_count"]>0: op+=5
    s["On-Page SEO"] = op

    ct = 0
    if m["word_count"]>=1000: ct+=15
    elif m["word_count"]>=500: ct+=10
    elif m["word_count"]>0: ct+=5
    if m["h2_count"]>=2: ct+=5
    if m["img_count"]>0 and m["img_with_alt"]/m["img_count"]>=0.8: ct+=5
    s["Content"] = ct

    tc = 0
    if m["https"]: tc+=8
    if m["has_canonical"]: tc+=7
    if m["has_schema"]: tc+=5
    s["Technical"] = tc

    lt = m["load_ms"] or 9999
    if lt<1000: s["Performance"]=10
    elif lt<2000: s["Performance"]=7
    elif lt<3500: s["Performance"]=4
    else: s["Performance"]=1

    sx = 0
    if m["has_og"]: sx+=5
    if m["internal_links"]>=5: sx+=5
    s["Social & UX"] = sx

    max_m = {"On-Page SEO":30,"Content":25,"Technical":20,"Performance":10,"Social & UX":10}
    s["Overall"] = sum(s[k] for k in max_m)
    return s


def render_competitor_analysis():
    st.markdown("## 🏆 Competitor Analysis")
    st.markdown("Compare your website against up to **4 competitors** across SEO, content, and technical signals.")

    with st.form("comp_form"):
        your_url = st.text_input("🌐 Your Website URL", placeholder="https://yoursite.com")
        st.markdown("**Competitor URLs**")
        c1 = st.text_input("Competitor 1", placeholder="https://competitor1.com")
        c2 = st.text_input("Competitor 2", placeholder="https://competitor2.com")
        c3 = st.text_input("Competitor 3", placeholder="https://competitor3.com")
        c4 = st.text_input("Competitor 4", placeholder="https://competitor4.com")
        go = st.form_submit_button("🔍 Run Competitor Analysis", use_container_width=True)

    if not go: return

    raw = [your_url, c1, c2, c3, c4]
    urls = [normalize_url(u.strip()) for u in raw if u.strip()]
    if len(urls) < 2:
        st.warning("Enter your URL and at least one competitor.")
        return

    all_m, all_s = {}, {}
    prog = st.progress(0, "Analysing…")
    for i, url in enumerate(urls):
        label = "Your Site" if i == 0 else f"Competitor {i}"
        prog.progress((i+1)/len(urls), f"Fetching {url}…")
        m = extract_competitor_metrics(url)
        all_m[label] = m
        all_s[label] = score_competitor(m)
        time.sleep(0.2)
    prog.empty()

    # ── Overall bar chart ──
    sites = list(all_s.keys())
    overall = [all_s[s]["Overall"] for s in sites]
    colors = ["#4F8EF7","#F76B6B","#4FD18E","#F7C948","#A44FF7"]
    fig_bar = px.bar(x=sites, y=overall, color=sites,
                     color_discrete_sequence=colors,
                     text=overall, title="Overall SEO Score Comparison",
                     labels={"x":"","y":"Score /95"})
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(showlegend=False, height=360,
                          template="plotly_dark", yaxis_range=[0,115])
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Radar chart ──
    cats = ["On-Page SEO","Content","Technical","Performance","Social & UX"]
    max_map = {"On-Page SEO":30,"Content":25,"Technical":20,"Performance":10,"Social & UX":10}
    fig_radar = go.Figure()
    for idx,(label,sc) in enumerate(all_s.items()):
        pct = [round(sc.get(c,0)/max_map[c]*100) for c in cats]
        fig_radar.add_trace(go.Scatterpolar(
            r=pct+[pct[0]], theta=cats+[cats[0]],
            fill="toself", name=label,
            line=dict(color=colors[idx%len(colors)]), opacity=0.65,
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100])),
        title="Category Radar", height=440, template="plotly_dark",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # ── Metrics table ──
    st.markdown("### 📊 Full Metrics Table")
    rows = []
    for label, m in all_m.items():
        s = all_s[label]
        rows.append({
            "Site": label, "Score": f"{s['Overall']}/95",
            "Load (ms)": m["load_ms"] or "N/A",
            "Title Len": m["title_len"], "Meta Desc Len": m["meta_desc_len"],
            "H1": m["h1_count"], "H2": m["h2_count"],
            "Words": m["word_count"],
            "HTTPS": "✅" if m["https"] else "❌",
            "Canonical": "✅" if m["has_canonical"] else "❌",
            "Schema": "✅" if m["has_schema"] else "❌",
            "OG Tags": "✅" if m["has_og"] else "❌",
        })
    st.dataframe(pd.DataFrame(rows).set_index("Site"), use_container_width=True)

    # ── Gap analysis ──
    st.markdown("### 🎯 Gap Analysis — vs Best Competitor")
    best = max([k for k in all_s if k!="Your Site"],
               key=lambda k: all_s[k]["Overall"], default=None)
    if best and "Your Site" in all_m:
        ys = all_m["Your Site"]; bs = all_m[best]
        gaps = []
        if ys["title_len"]<40 or ys["title_len"]>65:
            gaps.append(f"📝 Title length ({ys['title_len']} chars) — aim for 40–65 chars")
        if ys["meta_desc_len"]<120 or ys["meta_desc_len"]>160:
            gaps.append(f"📝 Meta description ({ys['meta_desc_len']} chars) — aim for 120–160 chars")
        if ys["h1_count"]!=1:
            gaps.append(f"🏷️ You have {ys['h1_count']} H1 tags — use exactly 1")
        if ys["word_count"] < bs["word_count"]*0.7:
            gaps.append(f"📄 Word count ({ys['word_count']}) vs {best} ({bs['word_count']}) — expand content")
        if not ys["has_schema"] and bs["has_schema"]:
            gaps.append(f"🔗 Schema markup missing — {best} has it")
        if not ys["has_canonical"]:
            gaps.append("🔗 Canonical tag missing — add to prevent duplicate content issues")
        if not ys["has_og"] and bs["has_og"]:
            gaps.append(f"📣 Open Graph tags missing — {best} has them for better social sharing")
        if (ys["load_ms"] or 0) > (bs["load_ms"] or 0)*1.3:
            gaps.append(f"⚡ Load time ({ys['load_ms']}ms) slower than {best} ({bs['load_ms']}ms)")

        if gaps:
            for g in gaps:
                st.warning(g)
        else:
            st.success("🎉 Your site is on par with or better than the top competitor!")


# ════════════════════════════════════════════════════════════════════
# ── TAB 3: AI VISIBILITY ────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════

def check_structured_data(soup) -> dict:
    res = {"present": False, "types": [], "count": 0, "valid": 0}
    scripts = soup.find_all("script", type="application/ld+json")
    res["count"] = len(scripts)
    for s in scripts:
        try:
            data = json.loads(s.string or "{}")
            t = data.get("@type","Unknown")
            res["types"] += t if isinstance(t,list) else [t]
            res["valid"] += 1
            res["present"] = True
        except Exception:
            pass
    microdata = soup.find_all(attrs={"itemscope":True})
    if microdata:
        res["present"] = True
        for el in microdata:
            t = el.get("itemtype","")
            if t: res["types"].append(t.split("/")[-1])
    return res


def check_eeat(soup, url: str) -> dict:
    r = {
        "has_author": False, "has_about": False, "has_contact": False,
        "has_privacy": False, "has_terms": False, "has_date": False,
        "has_citations": False, "https": url.startswith("https"),
    }
    author_tags = [
        soup.find("meta", attrs={"name": re.compile("author", re.I)}),
        soup.find(class_=re.compile("author|byline|writer", re.I)),
        soup.find(attrs={"itemprop":"author"}),
    ]
    r["has_author"] = any(a for a in author_tags)

    links = [a.get("href","").lower() for a in soup.find_all("a", href=True)]
    texts = [a.get_text(strip=True).lower() for a in soup.find_all("a", href=True)]
    r["has_about"]   = any("about"   in l or "about"   in t for l,t in zip(links,texts))
    r["has_contact"] = any("contact" in l or "contact" in t for l,t in zip(links,texts))
    r["has_privacy"] = any("privacy" in l for l in links)
    r["has_terms"]   = any("terms"   in l or "tos"     in l for l in links)

    r["has_date"] = any([
        soup.find("meta", attrs={"property":"article:published_time"}),
        soup.find("time"),
        soup.find(attrs={"itemprop":"datePublished"}),
    ])

    domain = urlparse(url).netloc
    outbound = [a for a in soup.find_all("a", href=True)
                if a["href"].startswith("http") and domain not in a["href"]]
    r["has_citations"] = len(outbound) >= 3
    return r


def check_snippet_signals(soup) -> dict:
    res = {
        "has_faq_schema": False, "has_howto_schema": False,
        "has_ol": False, "has_ul": False, "has_table": False,
        "has_concise": False, "has_definition": False,
        "q_headings": 0,
    }
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "{}")
            t = str(data.get("@type","")).lower()
            if "faq" in t: res["has_faq_schema"] = True
            if "howto" in t: res["has_howto_schema"] = True
        except Exception:
            pass

    res["has_ol"] = bool(soup.find("ol"))
    res["has_ul"] = bool(soup.find("ul"))
    res["has_table"] = bool(soup.find("table"))

    qwords = ["what","how","why","when","who","which","where","is ","are ","can "]
    res["q_headings"] = sum(
        1 for h in soup.find_all(["h1","h2","h3","h4"])
        if any(h.get_text(strip=True).lower().startswith(q) for q in qwords)
    )

    body = soup.find("body")
    if body:
        ft = body.get_text(separator=" ")[:300].lower()
        res["has_definition"] = any(x in ft for x in ["is a ","is an ","refers to","defined as"])
    for p in soup.find_all("p")[:10]:
        wc = len(p.get_text().split())
        if 20<=wc<=80:
            res["has_concise"] = True; break
    return res


def compute_ai_score(sd, eeat, fs, word_count, headings, media) -> dict:
    scores = {}

    # Structured Data /25
    sd_s = 0
    if sd["present"]: sd_s += 12
    sd_s += min(sd["count"]*4, 8)
    hv = {"FAQPage","HowTo","Article","NewsArticle","Product","Review"}
    sd_s += min(sum(2 for t in sd["types"] if t in hv), 5)
    scores["Structured Data"] = min(sd_s, 25)

    # E-E-A-T /30
    flags = [eeat["https"], eeat["has_author"], eeat["has_date"],
             eeat["has_about"], eeat["has_contact"],
             eeat["has_privacy"], eeat["has_terms"], eeat["has_citations"]]
    scores["E-E-A-T"] = min(sum(4 for f in flags if f), 30)

    # Snippet Readiness /25
    fs_s = 0
    if fs["has_faq_schema"]: fs_s += 8
    if fs["has_howto_schema"]: fs_s += 7
    if fs["has_ol"] or fs["has_ul"]: fs_s += 4
    if fs["has_table"]: fs_s += 3
    if fs["q_headings"]>=2: fs_s += 3
    elif fs["q_headings"]==1: fs_s += 1
    if fs["has_concise"]: fs_s += 3
    if fs["has_definition"]: fs_s += 2
    scores["Snippet Readiness"] = min(fs_s, 25)

    # Content Depth /20
    cq = 0
    if word_count>=2000: cq+=10
    elif word_count>=1000: cq+=7
    elif word_count>=400: cq+=4
    if headings>=5: cq+=5
    elif headings>=2: cq+=3
    if media>=3: cq+=5
    elif media>=1: cq+=3
    scores["Content Depth"] = min(cq, 20)

    scores["Overall"] = sum(scores.values())
    return scores


def render_ai_visibility():
    st.markdown("## 🤖 AI Visibility Score")
    st.markdown(
        "Check how likely your page is to appear in **Google AI Overviews** — "
        "scored across Structured Data, E-E-A-T, Snippet Readiness, and Content Depth."
    )

    with st.expander("ℹ️ What is AI Visibility?"):
        st.markdown("""
Google's **AI Overviews** cite pages that show:
- 📋 **Structured Data** — JSON-LD schemas (FAQPage, HowTo, Article…)
- 🎓 **E-E-A-T** — Experience, Expertise, Authority, Trust signals
- 🎯 **Snippet Readiness** — concise answers, Q&A headings, lists, tables
- 📄 **Content Depth** — comprehensive, well-structured, media-rich content
        """)

    url_in = st.text_input("🌐 URL to check", placeholder="https://yoursite.com/page", key="ai_url")
    if not st.button("🔍 Check AI Visibility", key="ai_btn", use_container_width=True):
        return

    url = normalize_url(url_in)
    with st.spinner("Fetching and analysing…"):
        resp, _ = safe_get(url)
        if resp is None or resp.status_code != 200:
            st.error("❌ Could not fetch the page.")
            return
        soup = BeautifulSoup(resp.text, "html.parser")

        sd    = check_structured_data(soup)
        eeat  = check_eeat(soup, url)
        fs    = check_snippet_signals(soup)

        body  = soup.find("body")
        wc    = len(body.get_text(separator=" ").split()) if body else 0
        hdgs  = len(soup.find_all(["h1","h2","h3"]))
        media = len(soup.find_all(["img","video","iframe"]))

        scores = compute_ai_score(sd, eeat, fs, wc, hdgs, media)

    overall = scores["Overall"]
    if overall>=75: label,emoji,col="High AI Visibility","🟢","#4FD18E"
    elif overall>=50: label,emoji,col="Moderate AI Visibility","🟡","#F7C948"
    elif overall>=25: label,emoji,col="Low AI Visibility","🟠","#F79648"
    else: label,emoji,col="Very Low AI Visibility","🔴","#F76B6B"

    # Banner
    st.markdown(
        f"""<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);
        border-left:5px solid {col};border-radius:8px;padding:18px 24px;margin:12px 0'>
        <h2 style='margin:0;color:{col}'>{emoji} {label}</h2>
        <p style='margin:4px 0 0;color:#aaa'>Score: 
        <strong style='color:white;font-size:22px'>{overall}/100</strong>
        &nbsp;|&nbsp; {url}</p></div>""",
        unsafe_allow_html=True,
    )

    # Gauge + category bar
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=overall,
        gauge={"axis":{"range":[0,100]},
               "bar":{"color":col},
               "steps":[{"range":[0,25],"color":"#2a1a1a"},
                         {"range":[25,50],"color":"#2a2a1a"},
                         {"range":[50,75],"color":"#1a2a1a"},
                         {"range":[75,100],"color":"#1a2a1a"}]},
        title={"text":"AI Visibility"},
    ))
    fig_g.update_layout(height=280, template="plotly_dark",
                        margin=dict(t=30,b=0,l=0,r=0))

    cats = ["Structured Data","E-E-A-T","Snippet Readiness","Content Depth"]
    max_m = {"Structured Data":25,"E-E-A-T":30,"Snippet Readiness":25,"Content Depth":20}
    pct = [round(scores.get(c,0)/max_m[c]*100) for c in cats]
    bar_colors = ["#4F8EF7" if p>=70 else "#F7C948" if p>=40 else "#F76B6B" for p in pct]
    fig_b = go.Figure(go.Bar(x=cats, y=pct, marker_color=bar_colors,
                             text=[f"{p}%" for p in pct], textposition="outside"))
    fig_b.update_layout(title="Category Breakdown (%)", yaxis_range=[0,120],
                        height=300, template="plotly_dark")

    c1, c2 = st.columns([1,1.6])
    with c1: st.plotly_chart(fig_g, use_container_width=True)
    with c2: st.plotly_chart(fig_b, use_container_width=True)

    # Detail tabs
    st1, st2, st3, st4 = st.tabs(["🔗 Structured Data","🎓 E-E-A-T","🎯 Snippets","📄 Content"])

    with st1:
        st.metric("Schema Blocks", sd["count"])
        if sd["types"]:
            st.success(f"Types found: **{', '.join(set(sd['types']))}**")
            hv = {"FAQPage","HowTo","Article","NewsArticle"}
            good = [t for t in sd["types"] if t in hv]
            if good: st.info(f"✅ High-value schema: **{', '.join(set(good))}**")
            else: st.warning("⚠️ Add FAQPage or HowTo schema for maximum AI visibility")
        else:
            st.error("❌ No structured data found — this is the #1 thing to fix")
        st.markdown("**Quick FAQPage JSON-LD template:**")
        st.code('{\n  "@context": "https://schema.org",\n  "@type": "FAQPage",\n'
                '  "mainEntity": [{\n    "@type": "Question",\n'
                '    "name": "Your question here?",\n'
                '    "acceptedAnswer": {"@type":"Answer","text":"Your answer."}\n  }]\n}',
                language="json")

    with st2:
        signals = {
            "HTTPS": eeat["https"], "Author Attribution": eeat["has_author"],
            "Publication Date": eeat["has_date"], "About Page": eeat["has_about"],
            "Contact Page": eeat["has_contact"], "Privacy Policy": eeat["has_privacy"],
            "Terms of Service": eeat["has_terms"], "Outbound Citations (3+)": eeat["has_citations"],
        }
        cols = st.columns(2)
        for i,(name,val) in enumerate(signals.items()):
            with cols[i%2]:
                st.markdown(f"{'✅' if val else '❌'} **{name}**")
        missing = [k for k,v in signals.items() if not v]
        if missing:
            st.warning(f"Missing: **{', '.join(missing)}**")
        else:
            st.success("🎉 All E-E-A-T signals detected!")

    with st3:
        checks = {
            "FAQ Schema": fs["has_faq_schema"], "HowTo Schema": fs["has_howto_schema"],
            "Numbered Lists": fs["has_ol"], "Bullet Lists": fs["has_ul"],
            "Tables": fs["has_table"], "Concise Answer Paragraphs": fs["has_concise"],
            "Definition-Style Intro": fs["has_definition"],
        }
        cols = st.columns(2)
        for i,(name,val) in enumerate(checks.items()):
            with cols[i%2]:
                st.markdown(f"{'✅' if val else '❌'} **{name}**")
        st.metric("Question-Phrased Headings", fs["q_headings"])
        if fs["q_headings"]<2:
            st.info("💡 Tip: Rephrase headings as questions — e.g. 'How does X work?' — AI loves them")

    with st4:
        col1,col2,col3 = st.columns(3)
        col1.metric("Word Count", wc)
        col2.metric("Headings", hdgs)
        col3.metric("Media Elements", media)
        depth = "Comprehensive" if wc>=2000 else "Moderate" if wc>=1000 else "Basic" if wc>=400 else "Shallow"
        st.metric("Content Depth", depth)
        if wc<1000: st.warning("📄 Expand content to 1000+ words for better AI citation chances")
        if media<2: st.info("🖼️ Add more images/video — rich media improves quality signals")

    # Roadmap
    st.markdown("---")
    st.markdown("### 🚀 Improvement Roadmap")
    roadmap = []
    if scores["Structured Data"]<18:
        roadmap.append(("🔗 Add FAQPage or HowTo JSON-LD schema","High Impact","#F76B6B"))
    if scores["E-E-A-T"]<20:
        roadmap.append(("🎓 Add author bio, dates, About/Contact pages","High Impact","#F76B6B"))
    if not fs["has_faq_schema"]:
        roadmap.append(("❓ Convert Q&A sections into FAQ schema","High Impact","#F76B6B"))
    if fs["q_headings"]<2:
        roadmap.append(("🏷️ Rephrase 2–3 headings as questions","Medium Impact","#F7C948"))
    if not eeat["has_citations"]:
        roadmap.append(("🔗 Add 3+ outbound links to authoritative sources","Medium Impact","#F7C948"))
    if wc<1000:
        roadmap.append(("📝 Expand content to 1000+ words","Medium Impact","#F7C948"))
    if not fs["has_concise"]:
        roadmap.append(("📌 Add concise 40–80 word answer paragraphs near page top","Medium Impact","#F7C948"))
    if not eeat["has_author"]:
        roadmap.append(("👤 Add visible author with credentials","Low Impact","#4FD18E"))
    if media<2:
        roadmap.append(("🖼️ Add more images or video","Low Impact","#4FD18E"))

    if roadmap:
        for action,impact,c in roadmap:
            st.markdown(
                f"<div style='border-left:4px solid {c};padding:8px 14px;margin:6px 0;"
                f"background:#1a1a2e;border-radius:4px'><strong>{action}</strong>"
                f"<span style='color:{c};font-size:12px;float:right'>{impact}</span></div>",
                unsafe_allow_html=True,
            )
    else:
        st.success("🎉 Your page implements most AI visibility best practices!")


# ════════════════════════════════════════════════════════════════════
# ── SIDEBAR + MAIN APP ───────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("## 🔍 WebScan Pro")
        st.markdown("*Website Analysis Tool*")
        st.markdown("---")
        st.markdown("### Features")
        st.markdown("✅ SEO Audit\n\n✅ Competitor Analysis\n\n✅ AI Visibility Score\n\n✅ Security Check\n\n✅ Tech Stack Detection")
        st.markdown("---")
        st.markdown("**No API keys required**")
        st.markdown("Built with Streamlit 🎈")

    # Header
    st.markdown(
        "<h1 style='text-align:center'>🔍 WebScan Pro</h1>"
        "<p style='text-align:center;color:#888;font-size:16px'>"
        "Website Analysis Tool — SEO • Competitor • AI Visibility</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Website Analysis",
        "🏆 Competitor Analysis",
        "🤖 AI Visibility",
    ])

    with tab1:
        render_website_analysis()

    with tab2:
        render_competitor_analysis()

    with tab3:
        render_ai_visibility()


if __name__ == "__main__":
    main()
