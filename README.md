# 🔍 WebScan Pro — Website Analysis Tool

Analyse any website for SEO, security, technology stack, and infrastructure — free, no API keys required.

## Features
- **SEO**: Title, meta, H1/H2, canonical, structured data, links, images
- **Security**: SSL certificate, 7 security headers with scoring
- **Tech Detection**: 50+ frameworks, CMS, analytics, hosting providers
- **Infrastructure**: Full DNS records, IP addresses, nameservers

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/website-analyzer.git
cd website-analyzer
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud
1. Push repo to GitHub (must be public)
2. Go to share.streamlit.io
3. Select repo, branch `main`, file `app.py`
4. Click Deploy

## GitHub Actions Setup
Add a secret `TARGET_URLS` with value:
```json
["https://yoursite.com", "https://competitor.com"]
```
The workflow runs every Monday at 9 AM UTC and saves reports to `reports/`.
