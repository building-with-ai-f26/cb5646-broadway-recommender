"""Build the single-file web app: python web/build.py

Inlines data/shows.json and web/recommender.js into web/template.html and writes
docs/app/index.html. The output has no external code, so it works as a published page
(and on GitHub Pages once docs/ is deployed). Re-run this after editing shows.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
shows = json.loads((ROOT / "data" / "shows.json").read_text())["shows"]

template = (ROOT / "web" / "template.html").read_text()
core = (ROOT / "web" / "recommender.js").read_text()
catalog = json.dumps(shows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

assert "/*__CATALOG__*/null" in template and "/*__CORE__*/" in template
page = template.replace("/*__CATALOG__*/null", catalog).replace("/*__CORE__*/", core.replace("</script", "<\\/script"))

out = ROOT / "docs" / "app" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(page)
print(f"wrote {out.relative_to(ROOT)} ({len(page) / 1024:.0f} KB, {len(shows)} shows)")
