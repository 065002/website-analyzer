"""
analyzer.py
Main orchestrator: calls all analysis modules and compiles a single report.
"""

import sys
import json
import datetime
from urllib.parse import urlparse

from scripts.seo_extractor import extract_seo_data
from scripts.tech_detector import detect_technologies
from scripts.security_checker import (
    check_ssl_certificate,
    check_security_headers,
    check_dns_records,
)


def normalize_url(url: str) -> str:
    """Ensures the URL has a scheme (defaults to https)."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def extract_domain(url: str) -> str:
    """Returns the domain without www prefix."""
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def calculate_overall_score(seo_data: dict, security_headers: dict) -> int:
    """
    Returns overall health score 0-100.
    Weighted: 60% SEO, 40% security.
    """
    if seo_data.get("error"):
        seo_score = 0
    else:
        seo_points = 0

        title_len = seo_data.get("title_length", 0)
        if 30 <= title_len <= 60:
            seo_points += 15
        elif title_len > 0:
            seo_points += 8

        desc_len = seo_data.get("meta_description_length", 0)
        if 120 <= desc_len <= 160:
            seo_points += 15
        elif desc_len > 0:
            seo_points += 8

        h1_count = seo_data.get("h1_count", 0)
        if h1_count == 1:
            seo_points += 15
        elif h1_count > 1:
            seo_points += 8

        if seo_data.get("h2_count", 0) > 0:
            seo_points += 10

        if seo_data.get("canonical_url"):
            seo_points += 10

        if seo_data.get("structured_data_count", 0) > 0:
            seo_points += 10

        total_imgs = seo_data.get("total_images", 0)
        missing_alt = seo_data.get("images_missing_alt", 0)
        if total_imgs == 0 or missing_alt == 0:
            seo_points += 15
        elif missing_alt / max(total_imgs, 1) < 0.2:
            seo_points += 8

        load_time = seo_data.get("load_time_seconds", 99)
        if load_time < 2:
            seo_points += 10
        elif load_time < 4:
            seo_points += 5

        seo_score = min(round((seo_points / 100) * 100), 100)

    security_score = security_headers.get("score", 0) if not security_headers.get("error") else 0
    overall = round(0.6 * seo_score + 0.4 * security_score)
    return max(0, min(100, overall))


def identify_critical_issues(seo_data: dict, security_headers: dict) -> list:
    """Returns list of high-priority problems."""
    issues = []

    if seo_data.get("error"):
        issues.append(f"SEO data could not be fetched: {seo_data['error']}")
        return issues

    if not seo_data.get("title"):
        issues.append("Missing <title> tag — critical for SEO and user experience")
    elif seo_data.get("title_length", 0) > 70:
        issues.append(f"Title tag too long ({seo_data['title_length']} chars) — truncated in search results")

    if not seo_data.get("meta_description"):
        issues.append("Missing meta description — reduces click-through rate from search results")

    if seo_data.get("h1_count", 0) == 0:
        issues.append("No H1 tag found — critical for on-page SEO")
    elif seo_data.get("h1_count", 0) > 1:
        issues.append(f"Multiple H1 tags ({seo_data['h1_count']}) — should have exactly one")

    if seo_data.get("images_missing_alt", 0) > 5:
        issues.append(f"{seo_data['images_missing_alt']} images missing alt text — accessibility and SEO issue")

    if security_headers.get("error"):
        issues.append(f"Security header check failed: {security_headers['error']}")
    elif security_headers.get("score", 100) < 30:
        issues.append("Very poor security header score (<30) — site vulnerable to common web attacks")

    if not security_headers.get("https_enabled", True):
        issues.append("Site not using HTTPS — insecure and penalised by search engines")

    if "content-security-policy" in security_headers.get("headers_missing", {}):
        issues.append("Missing Content-Security-Policy header — vulnerable to XSS attacks")

    return issues


def identify_quick_wins(seo_data: dict) -> list:
    """Returns list of easy improvements."""
    wins = []

    if seo_data.get("error"):
        return wins

    desc_len = seo_data.get("meta_description_length", 0)
    if 0 < desc_len < 120:
        wins.append(f"Expand meta description to 120–160 characters (currently {desc_len})")
    elif desc_len > 160:
        wins.append(f"Shorten meta description to 120–160 characters (currently {desc_len})")

    title_len = seo_data.get("title_length", 0)
    if 0 < title_len < 30:
        wins.append(f"Expand title tag to 30–60 characters (currently {title_len})")

    if not seo_data.get("canonical_url"):
        wins.append("Add a canonical URL tag to prevent duplicate content issues")

    if seo_data.get("structured_data_count", 0) == 0:
        wins.append("Add JSON-LD structured data to improve rich snippet eligibility")

    missing_alt = seo_data.get("images_missing_alt", 0)
    if 0 < missing_alt <= 5:
        wins.append(f"Add alt text to {missing_alt} image(s) for better accessibility and SEO")

    if seo_data.get("h2_count", 0) == 0:
        wins.append("Add H2 subheadings to improve content structure and keyword relevance")

    return wins


def analyze_website(url: str) -> dict:
    """
    Runs all analysis modules and returns a compiled report.
    """
    url = normalize_url(url)
    domain = extract_domain(url)
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    seo_data = extract_seo_data(url)
    tech_data = detect_technologies(url)
    ssl_data = check_ssl_certificate(domain)
    security_headers = check_security_headers(url)
    dns_data = check_dns_records(domain)

    overall_score = calculate_overall_score(seo_data, security_headers)
    critical_issues = identify_critical_issues(seo_data, security_headers)
    quick_wins = identify_quick_wins(seo_data)

    return {
        "meta": {
            "analysed_url": url,
            "domain": domain,
            "timestamp": timestamp,
            "overall_score": overall_score,
        },
        "seo": seo_data,
        "technologies": tech_data,
        "ssl": ssl_data,
        "security_headers": security_headers,
        "dns": dns_data,
        "recommendations": {
            "critical_issues": critical_issues,
            "quick_wins": quick_wins,
        },
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.analyzer <URL>")
        sys.exit(1)
    target_url = sys.argv[1]
    print(f"Analysing: {target_url}\n", flush=True)
    report = analyze_website(target_url)
    print(json.dumps(report, indent=2, default=str))
