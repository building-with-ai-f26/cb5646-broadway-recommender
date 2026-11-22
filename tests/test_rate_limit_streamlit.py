"""Clicks "Find my shows" 30 times in the real Streamlit app and checks the rate limit kicks in.
Claude is replaced by a fake, so this costs nothing. Run: python tests/test_rate_limit_streamlit.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app  # noqa: E402
import analytics  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

calls = []


def fake_recommend(text, **kw):
    calls.append(text)
    return {"picks": [], "message": "fake picks", "assumptions": ""}


app.recommend_shows = fake_recommend          # no paid Claude calls
analytics.track = lambda *a, **k: None         # no analytics events from the test

at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
at.run()
at.text_area[0].set_value("Date night, something funny under $150")
statuses = []
for i in range(30):
    at.button[0].click()   # "Find my shows"
    at.run()
    warned = [w.value for w in at.warning if "try again" in w.value]
    statuses.append("429" if warned else "200")

first_block = statuses.index("429") + 1 if "429" in statuses else None
print("Results:", " ".join(statuses))
print(f"Claude (fake) was called {len(calls)} times; first blocked request: #{first_block}")
if warned:
    print("Message shown:", warned[0])
ok = len(calls) == app.RATE_PER_VISITOR and statuses[:app.RATE_PER_VISITOR] == ["200"] * app.RATE_PER_VISITOR \
    and all(s == "429" for s in statuses[app.RATE_PER_VISITOR:])
print("PASS rate limit in Streamlit" if ok else "FAIL rate limit in Streamlit")
sys.exit(0 if ok else 1)
