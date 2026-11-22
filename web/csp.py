"""Content Security Policy for the published pages: python web/build.py adds it to both.

The policy only lets a page run its own inline scripts (each allowed by its exact SHA-256
hash, so any injected or edited script is blocked), PostHog's analytics scripts, and Google
Fonts. GitHub Pages can't send security headers, so it goes in a <meta> tag.
"""
import base64
import hashlib
import re

POSTHOG_ASSETS = "https://us-assets.i.posthog.com"
POSTHOG_API = "https://us.i.posthog.com"
INLINE_SCRIPT = re.compile(r"<script>(.*?)</script>", re.S)
CSP_META = re.compile(r'<meta http-equiv="Content-Security-Policy" content="[^"]*">|<!--__CSP__-->')


def script_hashes(html):
    return ["'sha256-" + base64.b64encode(hashlib.sha256(body.encode()).digest()).decode() + "'"
            for body in INLINE_SCRIPT.findall(html)]


def policy(html):
    return "; ".join([
        "default-src 'self'",
        "script-src 'self' " + " ".join(script_hashes(html)) + f" {POSTHOG_ASSETS}",
        f"connect-src 'self' {POSTHOG_API} {POSTHOG_ASSETS}",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src https://fonts.gstatic.com",
        "img-src 'self' data: blob:",
        "worker-src 'self' blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ])


def add_csp(html):
    """Insert or refresh the CSP <meta> tag. Hashes are taken after every other change to the page."""
    assert CSP_META.search(html), "page needs a <!--__CSP__--> marker or an existing CSP meta tag"
    tag = f'<meta http-equiv="Content-Security-Policy" content="{policy(CSP_META.sub("", html))}">'
    return CSP_META.sub(lambda _: tag, html, count=1)
