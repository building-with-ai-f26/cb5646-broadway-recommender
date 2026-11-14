"""Optional PostHog analytics for the Streamlit app (server side).

Reads POSTHOG_PROJECT_TOKEN and POSTHOG_HOST from the environment or .env.
With no token set, track() does nothing, so the app works exactly as before.
Only choices and counts are sent, never the text a visitor typed.
"""
import os
import uuid

from dotenv import load_dotenv

load_dotenv()
_client = None
_tried = False


def _get_client():
    global _client, _tried
    if _tried:
        return _client
    _tried = True
    token = os.environ.get("POSTHOG_PROJECT_TOKEN", "").strip()
    host = os.environ.get("POSTHOG_HOST", "").strip() or "https://us.i.posthog.com"
    if not token:
        return None
    try:
        from posthog import Posthog
        _client = Posthog(token, host=host)
    except Exception:
        _client = None  # analytics must never break the app
    return _client


def new_visitor_id():
    """Anonymous random id for one browser session. No names or emails."""
    return str(uuid.uuid4())


def track(visitor_id, event, **props):
    ph = _get_client()
    if ph is None:
        return
    try:
        ph.capture(event, distinct_id=visitor_id, properties={"source": "streamlit", **props})
        ph.flush()
    except Exception:
        pass
