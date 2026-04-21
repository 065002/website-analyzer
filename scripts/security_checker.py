"""
security_checker.py
Checks SSL certificate validity, HTTP security headers, and DNS records.
"""

import ssl
import socket
import datetime
import requests

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

TIMEOUT = 15

SECURITY_HEADERS = {
    "strict-transport-security": {
        "label": "HSTS",
        "weight": 20,
        "description": "Forces HTTPS and protects against downgrade attacks.",
    },
    "content-security-policy": {
        "label": "Content-Security-Policy",
        "weight": 25,
        "description": "Prevents XSS, clickjacking, and code-injection attacks.",
    },
    "x-frame-options": {
        "label": "X-Frame-Options",
        "weight": 15,
        "description": "Prevents the page from being embedded in iframes.",
    },
    "x-content-type-options": {
        "label": "X-Content-Type-Options",
        "weight": 15,
        "description": "Prevents MIME-type sniffing by browsers.",
    },
    "referrer-policy": {
        "label": "Referrer-Policy",
        "weight": 10,
        "description": "Controls referrer information included with requests.",
    },
    "permissions-policy": {
        "label": "Permissions-Policy",
        "weight": 10,
        "description": "Controls which browser features the page can use.",
    },
    "x-xss-protection": {
        "label": "X-XSS-Protection",
        "weight": 5,
        "description": "Legacy XSS filter header.",
    },
}


def check_ssl_certificate(domain: str) -> dict:
    """
    Connects to domain:443 and retrieves SSL certificate details.
    Returns validity status, issuer, expiry date, and days remaining.
    """
    try:
        ctx = ssl.create_default_context()
        conn = ctx.wrap_socket(
            socket.create_connection((domain, 443), timeout=TIMEOUT),
            server_hostname=domain,
        )
        cert = conn.getpeercert()
        conn.close()

        expiry_str = cert.get("notAfter", "")
        expiry_date = datetime.datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z") if expiry_str else None
        now = datetime.datetime.utcnow()
        days_remaining = (expiry_date - now).days if expiry_date else None

        issuer_dict = dict(x[0] for x in cert.get("issuer", []))
        issuer = issuer_dict.get("organizationName", issuer_dict.get("commonName", "Unknown"))

        subject_dict = dict(x[0] for x in cert.get("subject", []))
        subject = subject_dict.get("commonName", "Unknown")

        san_list = []
        for san_type, san_value in cert.get("subjectAltName", []):
            if san_type == "DNS":
                san_list.append(san_value)

        return {
            "valid": True,
            "issuer": issuer,
            "subject": subject,
            "expiry_date": expiry_date.strftime("%Y-%m-%d") if expiry_date else "Unknown",
            "days_remaining": days_remaining,
            "san_count": len(san_list),
            "sans": san_list[:10],
        }

    except ssl.SSLCertVerificationError as e:
        return {"valid": False, "error": f"SSL verification failed: {e}"}
    except ssl.SSLError as e:
        return {"valid": False, "error": f"SSL error: {e}"}
    except socket.timeout:
        return {"valid": False, "error": f"Connection timed out after {TIMEOUT}s"}
    except ConnectionRefusedError:
        return {"valid": False, "error": "Port 443 refused — site may not support HTTPS"}
    except Exception as e:
        return {"valid": False, "error": f"SSL check failed: {e}"}


def check_security_headers(url: str) -> dict:
    """
    Fetches the URL and evaluates HTTP security headers.
    Returns headers found/missing and a security score (0-100).
    """
    try:
        response = requests.head(
            url,
            headers={"User-Agent": "Mozilla/5.0 SecurityScanner/1.0"},
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        if response.status_code in (405, 501):
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 SecurityScanner/1.0"},
                timeout=TIMEOUT,
                allow_redirects=True,
            )

        resp_headers = {k.lower(): v for k, v in response.headers.items()}
        found = {}
        missing = {}
        earned_weight = 0
        total_weight = sum(h["weight"] for h in SECURITY_HEADERS.values())

        for header_key, meta in SECURITY_HEADERS.items():
            if header_key in resp_headers:
                found[header_key] = {
                    "label": meta["label"],
                    "value": resp_headers[header_key],
                    "description": meta["description"],
                    "weight": meta["weight"],
                }
                earned_weight += meta["weight"]
            else:
                missing[header_key] = {
                    "label": meta["label"],
                    "description": meta["description"],
                    "weight": meta["weight"],
                }

        score = round((earned_weight / total_weight) * 100)
        https_used = url.startswith("https://")
        hsts_value = resp_headers.get("strict-transport-security", "")

        return {
            "score": score,
            "https_enabled": https_used,
            "headers_found": found,
            "headers_missing": missing,
            "found_count": len(found),
            "missing_count": len(missing),
            "total_checked": len(SECURITY_HEADERS),
            "raw_security_headers": {k: resp_headers[k] for k in SECURITY_HEADERS if k in resp_headers},
        }

    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {TIMEOUT}s", "score": 0}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {e}", "score": 0}
    except Exception as e:
        return {"error": f"Security header check failed: {e}", "score": 0}


def check_dns_records(domain: str) -> dict:
    """
    Looks up A, AAAA, MX, TXT, NS, CNAME records using dnspython.
    Returns dictionary of record types with their values.
    """
    if not DNS_AVAILABLE:
        return {"error": "dnspython not installed — DNS lookups unavailable"}

    results = {}
    record_types = ["A", "AAAA", "MX", "TXT", "NS", "CNAME"]

    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 10

    for rtype in record_types:
        try:
            answers = resolver.resolve(domain, rtype)
            results[rtype] = [str(rdata) for rdata in answers]
        except dns.resolver.NoAnswer:
            results[rtype] = []
        except dns.resolver.NXDOMAIN:
            results[rtype] = []
            results["error"] = f"Domain '{domain}' does not exist"
            break
        except dns.exception.Timeout:
            results[rtype] = ["Timeout"]
        except Exception as e:
            results[rtype] = [f"Error: {e}"]

    results["ip_addresses"] = results.get("A", [])
    results["ipv6_addresses"] = results.get("AAAA", [])
    results["nameservers"] = results.get("NS", [])
    results["mail_servers"] = results.get("MX", [])

    return results
