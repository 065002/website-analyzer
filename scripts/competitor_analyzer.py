"""
competitor_analyzer.py
Runs analysis on multiple URLs and produces side-by-side comparison data.
"""

import concurrent.futures
from scripts.seo_extractor import extract_seo_data
from scripts.tech_detector import detect_technologies
from scripts.security_checker import (
    check_ssl_certificate,
    check_security_headers,
    check_dns_records,
)
from scripts.analyzer import (
    normalize_url,
    extract_domain,
    calculate_overall_score,
    identify_critical_issues,
    identify_quick_wins,
)


def analyze_single(url: str) -> dict:
    """Full analysis for one URL — used inside thread pool."""
    url = normalize_url(url)
    domain = extract_domain(url)

    seo_data        = extract_seo_data(url)
    tech_data       = detect_technologies(url)
    ssl_data        = check_ssl_certificate(domain)
    security_headers = check_security_headers(url)
    dns_data        = check_dns_records(domain)

    overall_score   = calculate_overall_score(seo_data, security_headers)
    critical_issues = identify_critical_issues(seo_data, security_headers)
    quick_wins      = identify_quick_wins(seo_data)

    return {
        "url": url,
        "domain": domain,
        "overall_score": overall_score,
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


def run_competitor_analysis(urls: list[str], max_workers: int = 4) -> dict:
    """
    Analyses multiple URLs in parallel and builds comparison data.

    Args:
        urls: List of URLs (first = primary site, rest = competitors).
        max_workers: Thread pool size (keep ≤ 4 to avoid rate-limiting).

    Returns:
        {
          "sites": [ {...site_report}, ... ],
          "comparison": { metric: {url: value, ...}, ... },
          "winner": { metric: url, ... },
          "radar_data": [...],          # for plotly radar chart
          "bar_data":   {...},          # for plotly grouped bar
        }
    """
    results = []

    # Parallel fetch — much faster than sequential
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(analyze_single, u): u for u in urls}
        for future in concurrent.futures.as_completed(future_map):
            try:
                results.append(future.result())
            except Exception as exc:
                url = future_map[future]
                results.append({
                    "url": url,
                    "domain": extract_domain(normalize_url(url)),
                    "overall_score": 0,
                    "error": str(exc),
                })

    # Re-order to match input order
    url_order = [normalize_url(u) for u in urls]
    results.sort(key=lambda r: url_order.index(r["url"]) if r["url"] in url_order else 999)

    # ── Build comparison table ─────────────────────────────────────────────
    comparison = {}
    metrics = [
        ("overall_score",             "Overall Score",          lambda r: r.get("overall_score", 0)),
        ("security_score",            "Security Score",         lambda r: r.get("security_headers", {}).get("score", 0)),
        ("load_time_seconds",         "Load Time (s)",          lambda r: r.get("seo", {}).get("load_time_seconds", 0)),
        ("page_size_kb",              "Page Size (KB)",         lambda r: r.get("seo", {}).get("page_size_kb", 0)),
        ("word_count",                "Word Count",             lambda r: r.get("seo", {}).get("word_count", 0)),
        ("internal_links",            "Internal Links",         lambda r: r.get("seo", {}).get("internal_links", 0)),
        ("external_links",            "External Links",         lambda r: r.get("seo", {}).get("external_links", 0)),
        ("images_missing_alt",        "Images Missing Alt",     lambda r: r.get("seo", {}).get("images_missing_alt", 0)),
        ("structured_data_count",     "Structured Data Blocks", lambda r: r.get("seo", {}).get("structured_data_count", 0)),
        ("security_headers_found",    "Security Headers Found", lambda r: r.get("security_headers", {}).get("found_count", 0)),
        ("h1_count",                  "H1 Count",               lambda r: r.get("seo", {}).get("h1_count", 0)),
        ("h2_count",                  "H2 Count",               lambda r: r.get("seo", {}).get("h2_count", 0)),
        ("ssl_days_remaining",        "SSL Days Remaining",     lambda r: r.get("ssl", {}).get("days_remaining", 0) or 0),
        ("has_canonical",             "Has Canonical URL",      lambda r: 1 if r.get("seo", {}).get("canonical_url") else 0),
        ("has_meta_description",      "Has Meta Description",   lambda r: 1 if r.get("seo", {}).get("meta_description") else 0),
    ]

    for key, label, extractor in metrics:
        comparison[key] = {
            "label": label,
            "values": {r["domain"]: extractor(r) for r in results},
        }

    # ── Determine winner per metric (higher = better, except load_time / page_size / images_missing_alt) ──
    lower_is_better = {"load_time_seconds", "page_size_kb", "images_missing_alt"}
    winner = {}
    for key, data in comparison.items():
        vals = data["values"]
        if not vals:
            continue
        if key in lower_is_better:
            winner[key] = min(vals, key=lambda d: vals[d] if vals[d] is not None else float("inf"))
        else:
            winner[key] = max(vals, key=lambda d: vals[d] if vals[d] is not None else -1)

    # ── Radar chart data (normalised 0-100 per dimension) ─────────────────
    radar_dimensions = [
        ("overall_score",          "Overall Score",     False),
        ("security_score",         "Security",          False),
        ("structured_data_count",  "Structured Data",   False),
        ("security_headers_found", "Sec. Headers",      False),
        ("load_time_seconds",      "Speed",             True),   # inverted
        ("page_size_kb",           "Page Weight",       True),   # inverted
        ("has_canonical",          "Canonical",         False),
        ("has_meta_description",   "Meta Desc.",        False),
    ]

    def _normalize(key, val, invert, all_vals):
        """Normalise a value to 0-100 given the range of all values."""
        all_clean = [v for v in all_vals if v is not None]
        if not all_clean:
            return 0
        lo, hi = min(all_clean), max(all_clean)
        if hi == lo:
            return 100
        norm = (val - lo) / (hi - lo) * 100
        return round(100 - norm if invert else norm, 1)

    radar_data = []
    for r in results:
        dims = []
        for key, label, invert in radar_dimensions:
            raw_val = comparison[key]["values"].get(r["domain"], 0) or 0
            all_vals = list(comparison[key]["values"].values())
            dims.append({
                "dimension": label,
                "raw": raw_val,
                "normalised": _normalize(key, raw_val, invert, all_vals),
            })
        radar_data.append({"domain": r["domain"], "url": r["url"], "dimensions": dims})

    # ── Technology comparison ──────────────────────────────────────────────
    tech_comparison = {}
    for r in results:
        tech = r.get("technologies", {})
        tech_comparison[r["domain"]] = {
            "frontend":  tech.get("frontend", []),
            "cms":       tech.get("cms", []),
            "analytics": tech.get("analytics", []),
            "hosting":   tech.get("hosting", []),
            "cdn":       tech.get("cdn", []),
            "server":    tech.get("server", "Unknown"),
        }

    return {
        "sites":            results,
        "comparison":       comparison,
        "winner":           winner,
        "radar_data":       radar_data,
        "tech_comparison":  tech_comparison,
    }
