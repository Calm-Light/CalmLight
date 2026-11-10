# MedTrack

A simple web app that helps users organize their medications and track daily doses.

Built with Django + PostgreSQL for MGT 656.

## Status

Repository skeleton only. Folders are empty placeholders (`.gitkeep`); application code is added during Sprint 1.

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

Instructions will be added once the Django project is set up.
