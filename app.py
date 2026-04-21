import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ─────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WebScan Pro",
    page_icon="🔍",
    layout="wide"
)

# ─────────────────────────────────────────────────────────
# GLOBAL PLOTLY LAYOUT (SAFE)
# ─────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8"),
)

# ─────────────────────────────────────────────────────────
# SAFE GAUGE FUNCTION
# ─────────────────────────────────────────────────────────
def make_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        number={"font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
        }
    ))

    layout = PLOTLY_LAYOUT.copy()
    layout["margin"] = dict(l=20, r=20, t=30, b=10)

    fig.update_layout(**layout, height=200)
    return fig

# ─────────────────────────────────────────────────────────
# UI HEADER
# ─────────────────────────────────────────────────────────
st.title("🔍 WebScan Pro")
st.caption("SEO • Tech • Security • Insights")

# ─────────────────────────────────────────────────────────
# INPUT
# ─────────────────────────────────────────────────────────
mode = st.radio("Select Mode", ["Single Site", "Competitor Analysis"])

if mode == "Single Site":
    url = st.text_input("Enter Website URL", placeholder="https://example.com")
    run = st.button("Analyse")

else:
    url1 = st.text_input("Your Site")
    url2 = st.text_input("Competitor 1")
    run = st.button("Run Analysis")

# ─────────────────────────────────────────────────────────
# SINGLE SITE OUTPUT
# ─────────────────────────────────────────────────────────
if run and mode == "Single Site" and url:

    st.subheader("📊 Health Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.plotly_chart(make_gauge(75, "Overall Score", "#34d399"), use_container_width=True)

    with col2:
        st.plotly_chart(make_gauge(60, "Security", "#fbbf24"), use_container_width=True)

    with col3:
        st.plotly_chart(make_gauge(80, "Performance", "#34d399"), use_container_width=True)

    with col4:
        st.plotly_chart(make_gauge(70, "SEO", "#34d399"), use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────
    # SEO BAR GRAPH (FIXED)
    # ─────────────────────────────────────────
    seo_scores = {
        "Title Tag": 80,
        "Meta Description": 60,
        "H1 Tag": 100,
        "Images Alt": 90,
        "Structured Data": 50
    }

    fig = go.Figure(go.Bar(
        x=list(seo_scores.values()),
        y=list(seo_scores.keys()),
        orientation="h"
    ))

    layout = PLOTLY_LAYOUT.copy()
    layout["title"] = dict(text="SEO Signal Scores", x=0)

    fig.update_layout(**layout, height=300)

    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────
# COMPETITOR (BASIC VERSION)
# ─────────────────────────────────────────────────────────
elif run and mode == "Competitor Analysis" and url1 and url2:

    st.subheader("🏆 Competitor Comparison")

    data = pd.DataFrame({
        "Metric": ["SEO", "Performance", "Security"],
        url1: [70, 80, 60],
        url2: [60, 75, 70]
    })

    fig = px.bar(data, x="Metric", y=[url1, url2], barmode="group")

    layout = PLOTLY_LAYOUT.copy()
    layout["title"] = dict(text="Comparison", x=0)

    fig.update_layout(**layout)

    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────
else:
    st.info("Enter a URL and click Analyse to begin.")
