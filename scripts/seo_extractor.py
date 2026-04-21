"""
seo_extractor.py
Extracts SEO-related data from a given URL.
"""

import time
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

TIMEOUT = 15


def extract_seo_data(url: str) -> dict:
    """
    Fetches a webpage and extracts comprehensive SEO data.
    Returns a dictionary with all extracted data, or 'error' key on failure.
    """
    try:
        start_time = time.time()
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        load_time = round(time.time() - start_time, 3)
        response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "lxml")

        # Title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Meta tags
        meta_description = None
        meta_keywords = None
        robots_meta = None

        for meta in soup.find_all("meta"):
            name = (meta.get("name") or meta.get("property") or "").lower()
            content = meta.get("content", "")
            if name == "description":
                meta_description = content
            elif name == "keywords":
                meta_keywords = content
            elif name == "robots":
                robots_meta = content

        # Headings
        h1_tags = [tag.get_text(strip=True) for tag in soup.find_all("h1")]
        h2_tags = [tag.get_text(strip=True) for tag in soup.find_all("h2")]

        # Canonical URL
        canonical_tag = soup.find("link", rel="canonical")
        canonical_url = canonical_tag["href"] if canonical_tag and canonical_tag.get("href") else None

        # JSON-LD Structured Data
        structured_data = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                structured_data.append(data)
            except (json.JSONDecodeError, TypeError):
                pass

        # Internal vs External Links
        parsed_base = urlparse(url)
        base_domain = parsed_base.netloc.lower()
        internal_links = 0
        external_links = 0

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            absolute = urljoin(url, href)
            parsed = urlparse(absolute)
            if parsed.netloc.lower() == base_domain:
                internal_links += 1
            else:
                external_links += 1

        # Images & Alt Text
        all_images = soup.find_all("img")
        images_with_alt = sum(1 for img in all_images if img.get("alt", "").strip())
        images_missing_alt = len(all_images) - images_with_alt

        # Word Count
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()
        visible_text = soup.get_text(separator=" ", strip=True)
        word_count = len(visible_text.split())

        # Page Size
        page_size_kb = round(len(response.content) / 1024, 2)

        return {
            "url": url,
            "final_url": response.url,
            "status_code": response.status_code,
            "load_time_seconds": load_time,
            "page_size_kb": page_size_kb,
            "title": title,
            "title_length": len(title) if title else 0,
            "meta_description": meta_description,
            "meta_description_length": len(meta_description) if meta_description else 0,
            "meta_keywords": meta_keywords,
            "robots_meta": robots_meta,
            "h1_tags": h1_tags,
            "h1_count": len(h1_tags),
            "h2_tags": h2_tags,
            "h2_count": len(h2_tags),
            "canonical_url": canonical_url,
            "structured_data": structured_data,
            "structured_data_count": len(structured_data),
            "internal_links": internal_links,
            "external_links": external_links,
            "total_images": len(all_images),
            "images_with_alt": images_with_alt,
            "images_missing_alt": images_missing_alt,
            "word_count": word_count,
        }

    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {TIMEOUT}s", "url": url}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {e}", "url": url}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error: {e}", "url": url}
    except Exception as e:
        return {"error": f"Unexpected error in SEO extraction: {e}", "url": url}
