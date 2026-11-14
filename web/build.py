"""Build the single-file web app: python web/build.py

Inlines data/shows.json and web/recommender.js into web/template.html and writes
docs/app/index.html. The output has no external code, so it works as a published page
(and on GitHub Pages once docs/ is deployed). Re-run this after editing shows.json.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
def read_env(name):
    """Read a setting from the environment, falling back to the repo's .env file (not committed)."""
    if os.environ.get(name):
        return os.environ[name].strip()
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            key, _, value = line.partition("=")
            if key.strip() == name and value.strip():
                return value.strip().strip("\"'")
    return ""


shows = json.loads((ROOT / "data" / "shows.json").read_text())["shows"]

template = (ROOT / "web" / "template.html").read_text()
core = (ROOT / "web" / "recommender.js").read_text()
catalog = json.dumps(shows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

# PostHog analytics: the project token is public by design (it can only send events), but it still
# comes from POSTHOG_PROJECT_TOKEN / POSTHOG_HOST instead of being typed into the template.
# With no token the page builds and runs normally, it just sends nothing.
token, host = read_env("POSTHOG_PROJECT_TOKEN"), read_env("POSTHOG_HOST")
if token and host:
    posthog = json.dumps({"token": token, "host": host}, separators=(",", ":"))
else:
    posthog = "null"
    print("WARNING: POSTHOG_PROJECT_TOKEN variable required by PostHog is missing or un-configured, "
          "this causes events to be silently missed. This warning stops appearing once "
          "POSTHOG_PROJECT_TOKEN and POSTHOG_HOST are configured.")

assert all(m in template for m in ("/*__CATALOG__*/null", "/*__CORE__*/", "/*__POSTHOG__*/null"))
page = (template.replace("/*__CATALOG__*/null", catalog)
        .replace("/*__POSTHOG__*/null", posthog)
        .replace("/*__CORE__*/", core.replace("</script", "<\\/script")))

out = ROOT / "docs" / "app" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(page)
print(f"wrote {out.relative_to(ROOT)} ({len(page) / 1024:.0f} KB, {len(shows)} shows)")
