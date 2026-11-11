# MedTrack

A simple web app that helps users organize their medications and track daily doses.

Built with Django + PostgreSQL for MGT 656.

## Status

Sprint 1 walking skeleton: Django project, accounts (sign up / log in / log out), seed command,
health check, base layout, and placeholder routes for the A/B test page and MedTrack features.

## Layout

```
manage.py              Django command entry point (created by startproject)
requirements.txt       Python dependencies
.env.example           Environment variable names (no real secrets; copy to .env)
render.yaml / build.sh Render deployment config (added in Sprint 1)

config/                Project settings, root URLs, WSGI entry point
accounts/              Sign up, log in, log out; seed command for demo accounts
abtest/                A/B test page and /stats endpoint
meds/                  MedTrack features: medications, schedules, dose log, weekly AI summary
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

## Where to add things

| You are working on | Put it here | Already wired up |
|---|---|---|
| A/B test page | `abtest/views.py` (`page`, `stats`), `abtest/models.py`, `templates/abtest/page.html`, `abtest/tests.py` | Routes `/<hash>/` and `/<hash>/stats`; `settings.ABTEST_HASH`, `settings.TEAM_MEMBERS` |
| Medication features | `meds/models.py`, `meds/views.py`, `meds/urls.py`, `templates/meds/` | `/` is the logged-in home page (`home` view) |
| AI weekly summary | `meds/ai.py` only | `call_openrouter()` with timeout and `AIUnavailable` errors; tests mock it |
| Demo data | a `seed(stdout)` function in your app, listed in `EXTRA_SEEDERS` in `accounts/management/commands/seed.py` | Grader accounts |
| Pages | `{% extends "base.html" %}` and fill `{% block content %}` | Bootstrap 5, nav bar, log out button |
| Settings / secrets | environment variables; add new names to `.env.example` | `config/settings.py` |

## Rules

- Work on a branch, open a pull request with `Closes #<issue>`, get one teammate's review before merging.
- Never commit `.env`, passwords or API keys.
- Change the database only through migrations (`python manage.py makemigrations`).
- Tests never call OpenRouter or any other outside service; mock them.
- GitHub Actions runs `python manage.py test` against Postgres on every pull request.

## Deploy (Render + Neon)

`render.yaml` defines the staging web service. Render runs `build.sh` (install, collectstatic, migrate, seed)
and starts `gunicorn` on `$PORT`. Set `DATABASE_URL` (Neon), `SEED_ADMIN_PASSWORD`, `SEED_MEMBER_PASSWORD`
in the Render dashboard. Health check: `/healthz`.
