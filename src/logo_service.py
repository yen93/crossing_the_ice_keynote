"""Best-guess client logo URL(s), with no network call of our own.

This mirrors the Uncharted Ice / Interactive Keynote automations'
logo_service.py, which learned the hard way (see their AS_BUILT docs) that
self-validating a guessed domain breaks in a network-restricted sandbox: each
probe host either died or 301-redirected to an unpredictable,
un-allowlistable sharded host.

This version makes no outbound call at all: it builds candidate logo URLs and
returns them unvalidated. Those URLs are only ever fetched by Slides'
replaceImage, server-side on Google's own infrastructure when
slides_rewriter.py applies them — never by this process — so they work
regardless of this process's network access (and need no sandbox egress
allow-listing).

Domain resolution, best first:
  1. An explicit client website written on the demo-notes page (most reliable).
  2. The domain of a client contact email (skipping generic mail providers).
  3. A slug guessed from the organisation name (the weakest signal — this is
     what mis-fired "Saliba Estate Managers" -> "salibaestatemanagers.com.au"
     when the real domain was "saliba.com.au", so it's the last resort).

For each resolved domain we emit, in priority order, a real-logo CDN URL
(logo.dev, only when LOGODEV_TOKEN is set — it returns an actual brand logo)
followed by a Google favicon URL (keyless, always available, but only an
icon). slides_rewriter tries them in order until one actually places, so a
dead or wrong URL falls through to the next instead of leaving the previous
client's logo in place. Every URL here is still an unverified guess — callers
must flag the result for human review rather than treat it as a confirmed
match."""

import re

import config

_SUFFIXES = re.compile(
    r"\b(pty|ltd|limited|llc|inc|incorporated|corp|corporation|company|co|group)\b",
    re.IGNORECASE,
)
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_SCHEME_RE = re.compile(r"^[a-z]+://", re.IGNORECASE)

CANDIDATE_TLDS = [".com.au", ".com", ".co"]

# Mailboxes on these hosts tell us nothing about the client's own domain.
_GENERIC_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "yahoo.com", "yahoo.com.au", "icloud.com", "me.com", "aol.com",
    "bigpond.com", "bigpond.net.au", "optusnet.com.au", "internode.on.net",
    "proton.me", "protonmail.com",
}


def _clean_domain(raw: str) -> str:
    """Normalises a website/domain string to a bare host: strips scheme, any
    path/query, a leading 'www.', and surrounding whitespace. Returns '' if
    nothing usable remains."""
    if not raw:
        return ""
    value = _SCHEME_RE.sub("", raw.strip())
    value = value.split("/")[0].split("?")[0].split("#")[0]
    value = value.strip().lower().lstrip("@")
    if value.startswith("www."):
        value = value[4:]
    # A bare host needs at least one dot (e.g. "saliba.com.au").
    return value if "." in value else ""


def _domain_from_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    domain = email.rsplit("@", 1)[1].strip().lower()
    domain = _clean_domain(domain)
    if not domain or domain in _GENERIC_EMAIL_DOMAINS:
        return ""
    return domain


def _guessed_domains(client_org: str) -> list[str]:
    name = _SUFFIXES.sub("", (client_org or "").lower())
    slug = _NON_ALNUM.sub("", name)
    if not slug:
        return []
    return [f"{slug}{tld}" for tld in CANDIDATE_TLDS]


def _resolve_domains(ocr_fields: dict) -> list[str]:
    """Returns candidate domains, most-reliable first, de-duplicated."""
    domains: list[str] = []

    website = _clean_domain(ocr_fields.get("client_website", ""))
    if website:
        domains.append(website)

    email_domain = _domain_from_email(ocr_fields.get("contact_email", ""))
    if email_domain:
        domains.append(email_domain)

    domains.extend(_guessed_domains(ocr_fields.get("client_org", "")))

    seen = set()
    ordered = []
    for domain in domains:
        if domain and domain not in seen:
            seen.add(domain)
            ordered.append(domain)
    return ordered


def _logo_urls_for_domain(domain: str) -> list[str]:
    urls = []
    if config.LOGODEV_TOKEN:
        # logo.dev returns a real brand logo for the domain (falling back to a
        # generated monogram); served via CDN, fetched server-side by Slides.
        urls.append(
            f"https://img.logo.dev/{domain}?token={config.LOGODEV_TOKEN}&size=256&format=png"
        )
    urls.append(f"https://www.google.com/s2/favicons?domain={domain}&sz=256")
    return urls


def find_logo_url(ocr_fields: dict) -> dict:
    """Returns {logo_urls, domain} where logo_urls is a priority-ordered list
    of candidate image URLs for slides_rewriter to try until one places, and
    domain is the best-guess primary domain (or None when the notes give us
    nothing to work with — no website, no usable email, and an org name with
    no alphanumeric characters). Never raises. Every URL is an unverified
    guess, not a confirmed match — callers should flag it for human review."""
    domains = _resolve_domains(ocr_fields)
    if not domains:
        return {"logo_urls": [], "domain": None}

    logo_urls = []
    for domain in domains:
        logo_urls.extend(_logo_urls_for_domain(domain))

    return {"logo_urls": logo_urls, "domain": domains[0]}
