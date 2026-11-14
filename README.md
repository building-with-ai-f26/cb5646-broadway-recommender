# [Broadway Concierge]

> **One-line pitch:** [Broadway Concierge helps new and experienced theatergoers find the right show for their group, matched to their taste, budget and schedule, and flags ticket scams before they pay.]

- **Builder:** [Ciara Butler] (`@ciaralbutler`)
- **Pod:** [Pod 13]
- **Product Page & Living PRD:** [[(https://building-with-ai-f26.github.io/cb5646-broadway-recommender/)]
- **App:** [web version](https://building-with-ai-f26.github.io/cb5646-broadway-recommender/app/) (once deployed from `docs/`); the Streamlit app runs locally with `streamlit run streamlit_app.py`. Add the final cloud URL in Build 5.

## Start here: Build 1

**Due Monday, November 9 at noon, New York time.** No class November 3; keep building that week.

1. Join the [class organization](https://github.com/building-with-ai-f26), then use this template to create a **public** repo named `<netid>-<project-slug>`. Ask Christian or Hew if the organization is missing from the owner list.
2. Set up Git and one coding agent during the week of October 27. Follow the [Icerynk setup guide](https://www.icerynk.com/c/fa26-tech-gb-2160-dm2-f2/content/pre-class-setup-github-openrouter-your-coding-agent).
3. Publish [`docs/index.html`](./docs/index.html): **Settings → Pages → Deploy from a branch → main → /docs → Save**. When deployment finishes, open `https://building-with-ai-f26.github.io/<your-repo-name>/`.
4. Fill in PRD v1: a reachable user, their painful before/after workflow, one core workflow, and three non-goals.
5. Build a rough local prototype. Add a screenshot or GIF and an honest Build 1 log to the Product Page, including progress, learning, problems, costs, and hours.
6. Push meaningful commits on **at least two separate days each week outside class**, including the November 3 break.
7. Submit your **Product Page URL and repository URL in Icerynk**. Come ready to demo the prototype in two minutes on November 10.

Create your PostHog account in Week 1. Install it on the Product Page and local app in **Build 2**, then verify events. The Product Page is public from Build 1; the app can stay local through Week 4.

## Repository map

| File / folder | Purpose |
| --- | --- |
| [`docs/index.html`](./docs/index.html) | Required public pitch, living PRD, and weekly build log. Update with actual work and evidence. |
| [`Intent.md`](./Intent.md), [`Plan.md`](./Plan.md), [`journal/`](./journal/) | Optional drafting aids. No duplicate submission is required. |
| [`AGENTS.md`](./AGENTS.md) | Local run commands, project context, and agent rules. Build 2 onward. |
| [`tests/`](./tests/) | Verification guidance. Build 4 offers Track A domain evals **or** Track B user replays. |
| [`SPONSOR_MEMO.md`](./SPONSOR_MEMO.md) | One-page recommendation backed by actual usage, full costs, and risks. Due December 14 at noon. |

[Icerynk](https://www.icerynk.com/c/fa26-tech-gb-2160-dm2-f2/content) holds the assignment instructions and submissions.

## Local setup

Clone **your own repository** and ask your coding agent to document the exact install and run commands here and in `AGENTS.md`.

```bash
git clone https://github.com/building-with-ai-f26/<your-repo-name>.git
cd <your-repo-name>
```

If your app needs API keys, use a local environment file such as `.env`. Keep private keys out of source code, browser code, screenshots, and commits. The template ignores `.env`; `.env.example` contains placeholders only.

## Analytics (PostHog)
The web app and product page send anonymous usage events to PostHog (US cloud). The app sends choices and counts only, never the text a person types. Events: `question_answered`, `quick_start_clicked`, `price_slider_used`, `picks_shown`, `different_picks_clicked`, `picks_copied`, `start_over_clicked`, plus automatic pageviews.

To build the app with analytics, put `POSTHOG_PROJECT_TOKEN` and `POSTHOG_HOST` in `.env` (names are in `.env.example`) and run `python web/build.py`. With no token the app builds and runs normally and sends nothing. The project token is public by design; never use a personal API key (`phx_...`).

### Streamlit app analytics
`streamlit_app.py` also sends PostHog events from the server (`app_opened`, `picks_shown`, `find_clicked_empty`, `recommend_failed`) through `analytics.py`, using the same `POSTHOG_PROJECT_TOKEN` and `POSTHOG_HOST` from `.env`. Each browser session gets a random anonymous id. Typed text is never sent, only `text_length`. With no token set it does nothing.
