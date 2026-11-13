# AGENTS.md — Coding Agent Operating Manual

> Give this file to your coding agent and check that it is using these instructions. Keep the stack, commands, and ground rules current.

## 1. Project Overview
- **What this repo builds:** Broadway Concierge, a show recommender for first-time and budget-conscious theatergoers. Code applies hard limits (budget, kids' ages, dealbreakers) first; AI only ranks what is left.
- **Primary user & core workflow:** [See the living PRD in `docs/index.html`]
- **Tech stack:** Python 3 + Streamlit + Anthropic API (local app); plain JavaScript single-page web app in `web/` built into `docs/app/index.html`; hand-built catalog in `data/shows.json`.

## 2. Commands
- **Install dependencies:** `pip install -r requirements.txt`
- **Run locally:** `streamlit run streamlit_app.py` (needs `ANTHROPIC_API_KEY` in `.env`); web app: open `docs/app/index.html`
- **Run deterministic tests:** `python test_recommender.py` and `node web/test_core.js`
- **Rebuild the web app after editing `data/shows.json` or `web/`:** `python web/build.py`
- **Run model evals:** `[e.g., python tests/eval.py]`

## 3. Non-Negotiable Engineering Rules
1. **Plan before coding:** Before touching multiple files, propose a brief plan and wait for approval.
2. **Small batches:** Make small, focused changes that can be reviewed and explained by a human in a single Pull Request.
3. **Explainability:** Avoid unnecessary abstractions or dependencies. Help the human builder understand the main components, what changed, why it matters, what could break, and how it was checked.
4. **Verify changes:** Run relevant checks. For a reproducible logic bug, use a failing test to demonstrate the fix when practical. Record manual checks and known limitations; follow the selected Build 4 evaluation track.
5. **Zero secrets in code:** Never hardcode API keys, tokens, or credentials. Always read from environment variables (`.env`) and update `.env.example` when new variables are needed.
6. **Stop when looping:** If a fix fails twice in a row, stop, summarize what failed, and ask the human before trying a third approach.
