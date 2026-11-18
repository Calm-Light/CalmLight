# MedTrack

A simple web app that helps users organize their medications and track daily doses.

Built with Django + PostgreSQL for MGT 656.

## Status

Sprint 2: sign up and log in with email; add, edit, stop, restart and delete medications, with current and
past medications on the home page; "smart add" fills the medication form from pasted label text with AI
(OpenRouter), with a per-user daily limit; friendly 404 and 500 pages; A/B test page; CI runs lint and tests.
Staging: https://calm-light-staging.onrender.com · Production: https://calm-light-production.onrender.com
Next (Sprint 3): today's dose checklist (mark taken or missed) and intake history.

## Layout

```
manage.py              Django command entry point (created by startproject)
requirements.txt       Python dependencies
.env.example           Environment variable names (no real secrets; copy to .env)
build.sh               Render build step: install, collectstatic, migrate, seed
gunicorn.conf.py       gunicorn settings (worker timeout 60 s, longer than the AI wait)

config/                Project settings, root URLs, WSGI entry point
accounts/              Sign up, log in, log out; seed command for demo accounts
abtest/                A/B test page and /stats endpoint
meds/                  Medications (add, edit, stop, delete), AI smart add (meds/ai.py), demo data (meds/seed.py)
templates/             HTML templates (base layout, login, A/B page, meds pages)
static/                CSS, images, a little JS

docs/mgt656/           Course documents (team.yaml, sprint reports, technical.md, retrospective.md)
```

## Run locally

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`: keep `DEBUG=True`, set any two passwords for `SEED_ADMIN_PASSWORD` and `SEED_MEMBER_PASSWORD`.
Leave `DATABASE_URL` empty to use a local SQLite file, or paste a Postgres URL.

```
python manage.py migrate
python manage.py seed
python manage.py runserver
```

Open http://127.0.0.1:8000/login/ and log in as `member@example.com` or `admin@example.com`.

Run the tests: `python manage.py test`

Run the linter (same check as CI): `pip install ruff==0.15.7` once, then `ruff check .` (`ruff check . --fix` fixes import order and similar issues).

## Where to add things

| You are working on | Put it here | Already wired up |
|---|---|---|
| A/B test page | `abtest/views.py` (`page`, `stats`), `abtest/models.py`, `templates/abtest/page.html`, `abtest/tests.py` | Routes `/<hash>/` and `/<hash>/stats`; `settings.ABTEST_HASH`, `settings.TEAM_MEMBERS` |
| Medication features | `meds/models.py`, `meds/views.py`, `meds/urls.py`, `templates/meds/` | `/` is the logged-in home page (`home` view) |
| AI features | `meds/ai.py` (smart add: `parse_label`) | `call_openrouter()` with timeout and `AIUnavailable` errors; `AIRequest` daily limit; tests mock it |
| Demo data | a `seed(stdout)` function in your app, listed in `EXTRA_SEEDERS` in `accounts/management/commands/seed.py` | Grader accounts |
| Pages | `{% extends "base.html" %}` and fill `{% block content %}` | Bootstrap 5, nav bar, log out button |
| Settings / secrets | environment variables; add new names to `.env.example` | `config/settings.py` |

## Rules

- Work on a branch, open a pull request with `Closes #<issue>`, get one teammate's review before merging.
- Never commit `.env`, passwords or API keys.
- Change the database only through migrations (`python manage.py makemigrations`).
- Tests never call OpenRouter or any other outside service; mock them.
- GitHub Actions runs `ruff check .` and `python manage.py test` (against Postgres) on every pull request.

## Deploy (Render + Neon)

Two Render web services, set up in the Render dashboard, each with its own Neon database:

- **staging** (`calm-light-staging`): deploys automatically on every merge to `main`.
- **production** (`calm-light-production`): auto-deploy is off. After checking a change on staging, click
  *Manual Deploy → Deploy latest commit* on Render.

Both use build command `./build.sh` (install, collectstatic, migrate, seed), start command
`gunicorn config.wsgi --bind 0.0.0.0:$PORT --log-file -`, and health check path `/healthz`.
Environment variables (names in `.env.example`): `SECRET_KEY`, `DEBUG=False`, `DATABASE_URL` (Neon),
`SEED_ADMIN_PASSWORD`, `SEED_MEMBER_PASSWORD`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `AI_DAILY_LIMIT`.
