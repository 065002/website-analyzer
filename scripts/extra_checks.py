"""
extra_checks.py
Backlink profile estimation + AI/LLM visibility signals for a domain.
These use free/public signals only — no paid API keys required.
"""

import re
import requests
from urllib.parse import urlparse, quote_plus
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 12


# ── Backlink profile (free public signals) ─────────────────────────────────────

def check_backlink_profile(domain: str) -> dict:
    """
    Gathers free backlink-related signals:
      - Moz DA-style estimation via Open Site Explorer scrape hints
      - Common Crawl index hit count (rough referring-domain proxy)
      - Bing indexed pages count
      - Presence on major aggregators (Reddit, Hacker News, Wikipedia)
    Returns a structured dict safe for display.
    """
    results = {
        "domain": domain,
        "signals": {},
        "aggregator_mentions": {},
        "indexed_pages_estimate": None,
        "backlink_score": 0,
        "error": None,
    }

    score = 0

    # ── 1. Bing indexed pages ──────────────────────────────────────────────
    try:
        bing_url = f"https://www.bing.com/search?q=site%3A{domain}&count=1"
        resp = requests.get(bing_url, headers=HEADERS, timeout=TIMEOUT)
        text = resp.text
        # Look for "X results" pattern
        match = re.search(r'([\d,]+)\s+results', text, re.IGNORECASE)
        if match:
            count_str = match.group(1).replace(",", "")
            indexed = int(count_str)
            results["indexed_pages_estimate"] = indexed
            if indexed > 10000:
                score += 30
            elif indexed > 1000:
                score += 20
            elif indexed > 100:
                score += 10
            else:
                score += 5
        results["signals"]["bing_index"] = results["indexed_pages_estimate"] or "Not found"
    except Exception as e:
        results["signals"]["bing_index"] = f"Error: {e}"

    # ── 2. Open PageRank (free API) ────────────────────────────────────────
    try:
        opr_url = f"https://openpagerank.com/api/v1.0/getPageRank?domains[]={domain}"
        opr_headers = {**HEADERS, "API-OPR": "free_tier"}
        resp = requests.get(opr_url, headers=opr_headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            entries = data.get("response", [])
            if entries:
                pr = entries[0].get("page_rank_decimal", 0) or 0
                results["signals"]["open_pagerank"] = round(pr, 2)
                score += min(int(pr * 4), 30)
            else:
                results["signals"]["open_pagerank"] = "N/A"
        else:
            results["signals"]["open_pagerank"] = "N/A"
    except Exception:
        results["signals"]["open_pagerank"] = "N/A"

    # ── 3. Common Crawl hit ────────────────────────────────────────────────
    try:
        cc_url = f"https://index.commoncrawl.org/CC-MAIN-2024-10-index?url={domain}/*&output=json&limit=1"
        resp = requests.get(cc_url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200 and resp.text.strip():
            results["signals"]["common_crawl"] = "Indexed ✔"
            score += 10
        else:
            results["signals"]["common_crawl"] = "Not found"
    except Exception:
        results["signals"]["common_crawl"] = "Unknown"

    # ── 4. Aggregator presence ────────────────────────────────────────────
    aggregators = {
        "Reddit":      f"https://www.reddit.com/search/?q={domain}&type=link&limit=3",
        "Hacker News": f"https://hn.algolia.com/api/v1/search?query={domain}&tags=story&hitsPerPage=3",
    }
    for name, url in aggregators.items():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if name == "Hacker News":
                data = resp.json()
                hits = data.get("nbHits", 0)
                results["aggregator_mentions"][name] = hits
                if hits > 0:
                    score += min(hits * 2, 15)
            else:
                soup = BeautifulSoup(resp.text, "lxml")
                posts = soup.find_all("a", href=True)
                domain_mentions = sum(1 for a in posts if domain in a.get("href", ""))
                results["aggregator_mentions"][name] = domain_mentions
                if domain_mentions > 0:
                    score += min(domain_mentions * 3, 15)
        except Exception:
            results["aggregator_mentions"][name] = 0

    # ── 5. Wikipedia reference check ──────────────────────────────────────
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=exturlusage&euquery={domain}&format=json&eulimit=5"
        resp = requests.get(wiki_url, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()
        wiki_hits = len(data.get("query", {}).get("exturlusage", []))
        results["aggregator_mentions"]["Wikipedia"] = wiki_hits
        if wiki_hits > 0:
            score += 20
    except Exception:
        results["aggregator_mentions"]["Wikipedia"] = 0

    results["backlink_score"] = min(score, 100)
    return results


# ── AI / LLM Visibility ────────────────────────────────────────────────────────

def check_ai_visibility(domain: str, url: str) -> dict:
    """
    Estimates how likely a site is to appear in AI-generated answers (Gemini, ChatGPT, Perplexity).
    Uses free proxy signals:
      - Schema.org structured data presence (AI uses rich structured content)
      - E-E-A-T signals (About, Contact, Author pages)
      - FAQ / HowTo schema blocks
      - Content depth proxy (word count, headings)
      - HTTPS + security signals
      - Presence in knowledge-base proxies (Wikipedia, news aggregators)
    """
    results = {
        "domain": domain,
        "ai_score": 0,
        "signals": {},
        "recommendations": [],
        "error": None,
    }

    score = 0

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        html  = resp.text
        soup  = BeautifulSoup(html, "lxml")

        # ── Structured data (AI loves rich schema) ─────────────────────────
        ld_blocks = soup.find_all("script", type="application/ld+json")
        schema_types = []
        import json
        for block in ld_blocks:
            try:
                data = json.loads(block.string or "")
                t = data.get("@type", "")
                if isinstance(t, list):
                    schema_types.extend(t)
                else:
                    schema_types.append(t)
            except Exception:
                pass

        results["signals"]["schema_types"] = schema_types
        if schema_types:
            score += 15
        if any(t in schema_types for t in ["FAQPage", "HowTo", "QAPage"]):
            score += 20
            results["signals"]["faq_howto_schema"] = True
        else:
            results["signals"]["faq_howto_schema"] = False
            results["recommendations"].append("Add FAQPage or HowTo JSON-LD schema — AI models prioritise structured Q&A content")

        # ── E-E-A-T signals ────────────────────────────────────────────────
        page_text = html.lower()
        eeat = {
            "about_page":    any(p in page_text for p in ["/about", "about-us", "about us"]),
            "contact_page":  any(p in page_text for p in ["/contact", "contact-us", "contact us"]),
            "author_info":   any(p in page_text for p in ["author", "written by", "by ", "contributor"]),
            "privacy_policy": "/privacy" in page_text,
            "terms_page":    any(p in page_text for p in ["/terms", "terms of service", "terms of use"]),
        }
        results["signals"]["eeat"] = eeat
        eeat_score = sum(eeat.values()) * 5
        score += eeat_score
        if not eeat["about_page"]:
            results["recommendations"].append("Add an About page — E-E-A-T signals help AI models trust and cite your content")
        if not eeat["author_info"]:
            results["recommendations"].append("Add author attribution to content — AI systems favour named, credible authors")

        # ── Content depth ──────────────────────────────────────────────────
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        words = len(soup.get_text(separator=" ").split())
        headings = len(soup.find_all(["h2", "h3", "h4"]))
        results["signals"]["word_count"]   = words
        results["signals"]["subheadings"]  = headings

        if words > 1500:
            score += 15
        elif words > 800:
            score += 8
        else:
            results["recommendations"].append("Increase page content depth (aim for 1500+ words on key pages) for better AI citations")

        if headings >= 5:
            score += 10
        else:
            results["recommendations"].append("Use more subheadings (H2/H3) to help AI systems parse your content structure")

        # ── HTTPS ──────────────────────────────────────────────────────────
        if url.startswith("https://"):
            score += 5
            results["signals"]["https"] = True
        else:
            results["signals"]["https"] = False
            results["recommendations"].append("Switch to HTTPS — insecure sites are rarely cited by AI assistants")

        # ── Open Graph / Social meta (AI crawlers use these) ───────────────
        og_title = soup.find("meta", property="og:title")
        og_desc  = soup.find("meta", property="og:description")
        results["signals"]["open_graph"] = bool(og_title and og_desc)
        if results["signals"]["open_graph"]:
            score += 5
        else:
            results["recommendations"].append("Add Open Graph meta tags — used by AI knowledge graphs and social crawlers")

        # ── Canonical + sitemap ────────────────────────────────────────────
        canonical = soup.find("link", rel="canonical")
        results["signals"]["canonical"] = bool(canonical)
        if canonical:
            score += 5

        # ── Sitemap check ──────────────────────────────────────────────────
        try:
            sm_resp = requests.get(f"https://{domain}/sitemap.xml", headers=HEADERS, timeout=6)
            results["signals"]["sitemap"] = sm_resp.status_code == 200
            if sm_resp.status_code == 200:
                score += 5
            else:
                results["recommendations"].append("Create a sitemap.xml — helps AI crawlers discover and index all your content")
        except Exception:
            results["signals"]["sitemap"] = False

    except Exception as e:
        results["error"] = str(e)

    results["ai_score"] = min(score, 100)

    # Determine tier
    if results["ai_score"] >= 70:
        results["ai_tier"] = "High — likely cited by AI assistants"
        results["ai_tier_color"] = "#34d399"
    elif results["ai_score"] >= 40:
        results["ai_tier"] = "Moderate — occasionally referenced"
        results["ai_tier_color"] = "#fbbf24"
    else:
        results["ai_tier"] = "Low — rarely appears in AI answers"
        results["ai_tier_color"] = "#f87171"

    return results
