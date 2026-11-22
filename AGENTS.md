# AGENTS.md — Coding Agent Operating Manual

> Give this file to your coding agent and check that it is using these instructions. Keep the stack, commands, and ground rules current.

## 1. Project Overview
- **What this repo builds:** Broadway Concierge, a show recommender for first-time and budget-conscious theatergoers. Code applies hard limits (budget, kids' ages, dealbreakers) first; AI only ranks what is left.
- **Primary user & core workflow:** [See the living PRD in `docs/index.html`]
- **Tech stack:** Python 3 + Streamlit + Anthropic API (local app); plain JavaScript single-page web app in `web/` built into `docs/app/index.html`; hand-built catalog in `data/shows.json`.

## 2. Commands
- **Install dependencies:** `pip install -U -r requirements.txt`
- **Audit dependencies:** `pip install pip-audit` then `pip-audit -r requirements.txt` (no npm packages: the web app has no `package.json`). Fix high-severity findings by raising the minimum version in `requirements.txt`, then rerun the tests.
- **Run locally:** `streamlit run streamlit_app.py` (needs `ANTHROPIC_API_KEY` in `.env`); web app: open `docs/app/index.html`
- **Run deterministic tests:** `python test_recommender.py`, `node web/test_core.js` and `python tests/test_rate_limit_streamlit.py` (clicks Find 30 times with a fake Claude; costs nothing)
- **Rebuild the web app after editing `data/shows.json` or `web/`:** `python web/build.py`. It also refreshes the Content Security Policy in both pages (`web/csp.py`). Rerun it after editing any `<script>` in `docs/index.html` too, or the edited script is blocked. Never use inline `onclick=`/`onsubmit=` handlers; add listeners in a script instead.
- **Run model evals:** `[e.g., python tests/eval.py]`

## 3. Non-Negotiable Engineering Rules
1. **Plan before coding:** Before touching multiple files, propose a brief plan and wait for approval.
2. **Small batches:** Make small, focused changes that can be reviewed and explained by a human in a single Pull Request.
3. **Explainability:** Avoid unnecessary abstractions or dependencies. Help the human builder understand the main components, what changed, why it matters, what could break, and how it was checked.
4. **Verify changes:** Run relevant checks. For a reproducible logic bug, use a failing test to demonstrate the fix when practical. Record manual checks and known limitations; follow the selected Build 4 evaluation track.
5. **Zero secrets in code:** Never hardcode API keys, tokens, or credentials. Always read from environment variables (`.env`) and update `.env.example` when new variables are needed.
6. **Stop when looping:** If a fix fails twice in a row, stop, summarize what failed, and ask the human before trying a third approach.

## 4. Deploy
- **Web app + product page (live):** GitHub Pages serves the `docs/` folder on `main`.
  - App: https://building-with-ai-f26.github.io/cb5646-broadway-recommender/app/
  - Product page: https://building-with-ai-f26.github.io/cb5646-broadway-recommender/
- **To deploy a change:** run `python web/build.py` (if `web/` or `data/shows.json` changed), run both test commands, then merge the PR to `main`. Pages republishes in 1-2 minutes. No other deploy step.
- **Never commit secrets.** The web app needs no API key. The PostHog project token (`phc_`) is public by design; the personal API key (`phx_`) and `ANTHROPIC_API_KEY` must never be in the repo.
- **Streamlit app:** local only (`streamlit run streamlit_app.py` with `.env`). It is not publicly deployed, because a public Claude app would spend my API key. If that changes, use Streamlit Community Cloud with the key in its Secrets settings and a spend limit set in the Anthropic Console.
- **Spending caps and rate limits:** the Claude Console account has a hard $10/month spend limit (set Nov 21; Settings → Limits). Keep it on. The Streamlit app allows 10 Claude requests per visitor per 10 minutes and 60 per hour for everyone (`RateLimiter` in `app.py`, settings in `.env.example`); blocked requests show a "try again" message and never call Claude. The web app calls no paid API and writes to no database, so it needs no limit.
- **Weekly catalog update:** a scheduled task runs Mondays 6:58 AM ET, updates `data/shows.json`, rebuilds, tests and merges only if the tests pass.

## 5. Ask Me First (protect production)
`main` is production: merging to it publishes the live site. GitHub branch protection requires a pull request for every change to `main` (no direct or force pushes, no bypass). Before running any of these, stop, say exactly what will happen, and wait for a clear "yes" from me in chat. A "yes" covers that one action only.
- **Merging to `main`** (`gh pr merge`, the GitHub merge API, or `git push` to `main`). The only standing exception is the Monday catalog task above, and only for `data/shows.json`, the rebuilt `docs/app/index.html` and the refreshed security policy line in `docs/index.html`, with all tests passing.
- **Rewriting or deleting history:** `git push --force` / `-f`, `git reset --hard`, `git rebase` on a pushed branch, `git clean`, `git branch -D`, deleting a remote branch.
- **Deleting files or folders** (`rm -rf`, removing anything under `docs/` or `data/`).
- **Repo or hosting settings:** deleting or renaming the repo, changing GitHub Pages settings, branch protection, or collaborators.
- **Analytics data:** deleting or editing anything in PostHog (events, persons, insights, dashboards), or changing project settings.
- **Scheduled tasks:** creating, changing, pausing or deleting them.
- **Secrets:** reading, printing, copying or changing `.env` or any API key.

These rules are also enforced for Claude Code in `.claude/settings.json` (`permissions.ask`).

**Backups:** there is no database. Every version of the code, catalog and live site is kept in git history on GitHub, so any change can be reverted. PostHog keeps the analytics events; export them as CSV from PostHog's SQL editor before any risky analytics change.
