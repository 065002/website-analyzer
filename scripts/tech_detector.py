"""
tech_detector.py
Detects technologies used on a website by analysing HTML and HTTP headers.
"""

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 15

FRONTEND_SIGNATURES = {
    "React": ["react", "react-dom", "_reactFiber", "__REACT_DEVTOOLS_GLOBAL_HOOK__", "data-reactroot"],
    "Vue.js": ["vue.js", "vue.min.js", "__vue__", "data-v-", "Vue.config"],
    "Angular": ["angular", "ng-version", "ng-app", "ng-controller", "[_nghost"],
    "Next.js": ["__NEXT_DATA__", "_next/static", "next/dist"],
    "Nuxt.js": ["__nuxt", "__NUXT__", "_nuxt/"],
    "Svelte": ["__svelte", "svelte-"],
    "jQuery": ["jquery", "jQuery"],
    "Bootstrap": ["bootstrap.css", "bootstrap.min.css", "bootstrap.js"],
    "Tailwind CSS": ["tailwind", "tw-"],
}

CMS_SIGNATURES = {
    "WordPress": ["wp-content", "wp-includes", "wp-json", "/wp-login", "wordpress"],
    "Shopify": ["cdn.shopify.com", "Shopify.theme", "myshopify.com"],
    "Wix": ["wix.com", "wixstatic.com", "_wixCssModules"],
    "Squarespace": ["squarespace.com", "squarespace-cdn.com"],
    "Drupal": ["drupal.js", "Drupal.settings", "/sites/default/files"],
    "Joomla": ["joomla", "/components/com_", "/modules/mod_"],
    "Webflow": ["webflow.com", "webflow.js", "w-webflow-badge"],
    "Ghost": ["ghost.io", "content/themes", "ghost/"],
    "Magento": ["mage/cookies", "Magento_", "mage-messages"],
    "PrestaShop": ["prestashop", "/themes/classic"],
}

ANALYTICS_SIGNATURES = {
    "Google Analytics (GA4)": ["gtag('config'", "googletagmanager.com/gtag", "G-"],
    "Google Analytics (UA)": ["google-analytics.com/analytics.js", "ga('create'", "UA-"],
    "Google Tag Manager": ["googletagmanager.com/gtm.js", "GTM-"],
    "Facebook Pixel": ["connect.facebook.net/en_US/fbevents.js", "fbq('init'"],
    "Hotjar": ["static.hotjar.com", "hj('", "hjid:"],
    "Mixpanel": ["cdn.mxpnl.com", "mixpanel.track", "mixpanel.init"],
    "Segment": ["cdn.segment.com", "analytics.load(", "analytics.page("],
    "Heap": ["cdn.heapanalytics.com", "heap.load("],
    "Intercom": ["intercom.io", "window.intercomSettings"],
    "HubSpot": ["js.hs-scripts.com", "js.hsforms.net"],
    "Crisp": ["client.crisp.chat", "CRISP_WEBSITE_ID"],
    "Tawk.to": ["tawk.to", "Tawk_API"],
}

HOSTING_SIGNATURES = {
    "Vercel": ["x-vercel-id", "vercel.com", ".vercel.app"],
    "Netlify": ["x-nf-request-id", "netlify.com", ".netlify.app"],
    "AWS CloudFront": ["cloudfront.net", "x-amz-cf-id"],
    "Cloudflare": ["cf-ray", "cloudflare", "cf-cache-status"],
    "GitHub Pages": ["github.io"],
    "Firebase": ["firebaseapp.com", "web.app"],
    "Heroku": ["heroku.com", "herokuapp.com"],
    "Vercel": ["x-vercel-id", ".vercel.app"],
    "Google Cloud": ["googleusercontent.com", "appspot.com"],
    "Azure": ["azurewebsites.net", "azure.com"],
    "WP Engine": ["wpengine.com"],
    "Kinsta": ["kinsta.com", "kinstacdn.com"],
}


def _search_signatures(haystack: str, signatures: dict) -> list:
    found = []
    haystack_lower = haystack.lower()
    for tech, patterns in signatures.items():
        for pattern in patterns:
            if pattern.lower() in haystack_lower:
                found.append(tech)
                break
    return found


def detect_technologies(url: str) -> dict:
    """
    Detects technologies used on a website.
    Returns dict with keys: frontend, cms, analytics, hosting, backend, cdn, server.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        html = response.text
        response_headers = {k.lower(): v for k, v in response.headers.items()}
        headers_str = " ".join(f"{k}: {v}" for k, v in response_headers.items())
        full_content = html + " " + headers_str

        frontend = _search_signatures(full_content, FRONTEND_SIGNATURES)
        cms = _search_signatures(full_content, CMS_SIGNATURES)
        analytics = _search_signatures(full_content, ANALYTICS_SIGNATURES)
        hosting = _search_signatures(full_content, HOSTING_SIGNATURES)

        server = response_headers.get("server", "Unknown")
        powered_by = response_headers.get("x-powered-by", None)

        backend_hints = []
        if powered_by:
            backend_hints.append(powered_by)
        if "php" in full_content.lower():
            backend_hints.append("PHP")
        if "asp.net" in headers_str.lower():
            backend_hints.append("ASP.NET")
        if "csrfmiddlewaretoken" in html.lower():
            backend_hints.append("Django (Python)")
        if "laravel" in full_content.lower():
            backend_hints.append("Laravel (PHP)")

        cdn_hints = []
        if "cf-ray" in response_headers:
            cdn_hints.append("Cloudflare")
        if "x-amz-cf-id" in response_headers:
            cdn_hints.append("AWS CloudFront")
        if "x-nf-request-id" in response_headers:
            cdn_hints.append("Netlify CDN")
        if "x-vercel-id" in response_headers:
            cdn_hints.append("Vercel Edge Network")

        return {
            "frontend": list(set(frontend)),
            "cms": list(set(cms)),
            "analytics": list(set(analytics)),
            "hosting": list(set(hosting)),
            "backend": list(set(backend_hints)),
            "cdn": list(set(cdn_hints)),
            "server": server,
            "powered_by": powered_by,
            "content_type": response_headers.get("content-type", "Unknown"),
            "raw_headers": dict(response.headers),
        }

    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {TIMEOUT}s"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {e}"}
    except Exception as e:
        return {"error": f"Technology detection failed: {e}"}
