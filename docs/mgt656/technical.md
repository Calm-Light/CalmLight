# Technical challenge and testing strategy

MedTrack is a Django 5.2 + PostgreSQL app on Render (app) and Neon (database).
Staging: https://calm-light-staging.onrender.com · Production: https://calm-light-production.onrender.com

## Technical-challenge items

### 1. Delivery: CI, CD with a manual promote step, and a health check

- **What:** every pull request and every push to `main` runs two GitHub Actions jobs: **lint** (ruff, pinned version) and **test** (Django tests against a real Postgres 16 service, plus `manage.py check` and a check that no migration is missing). Merging to `main` deploys **staging** automatically. **Production** has auto-deploy turned off; we promote by clicking *Manual Deploy* on Render after the change has been checked on staging. Staging and production have separate Neon databases. Each deploy runs `build.sh`: install, `collectstatic`, `migrate`, `seed`.
- **Health check:** `GET /healthz` runs `SELECT 1` and returns `{"status": "ok"}` (200), or 503 if the database does not answer, so Render can tell a running process from a working app.
- **Files and PRs:** `.github/workflows/tests.yml`, `ruff.toml`, `build.sh`, `config/views.py` (`healthz`), `config/tests.py`. PR #3 (CI, healthz, Render), #19 (lint).
- **See it working:** the *Checks* tab on any pull request shows **lint** and **test**; https://calm-light-production.onrender.com/healthz.
- **Known gap:** GitHub does not let a free organization protect branches on a private repo, so a red check does not technically block the merge button. Our rule is that only green pull requests are merged, and reviewers check the status before approving. We will ask whether the repo can be made public so we can turn on branch protection.

### 2. AI: structured LLM output that drives the app ("smart add")

- **What:** on *Add medication*, the user can paste the text from a prescription label. The server sends only that text to OpenRouter and asks for JSON that must match a schema (`response_format` = `json_schema`, `strict`): name, dose amount, unit, route, times per day, meal timing, each allowed to be `null`. The answer pre-fills the medication form. **Nothing is saved until the user checks the form and clicks Save.**
- **Not trusting the model:** `clean_label_fields` checks every value again in code (unit, route, frequency and meal timing must be one of our choices; dose must be a positive number) and drops anything else. Fields the model left empty or got wrong are listed to the user ("Please fill in: dose, unit"). Route and meal timing have a default in the form, so when the model leaves them empty they are listed as "Please check" instead. The prompt tells the model to return `null` rather than guess, and spells out how to read routes ("by mouth" = oral) and units for sprays, drops and insulin.
- **Failure handling:** missing key, network error, 30-second timeout, error response, empty reply or non-JSON reply all raise `AIUnavailable`; the user sees "AI fill isn't available right now" and the manual form still works. Failures are logged to stdout.
- **Privacy:** only the pasted label text is sent (no name, email or other medications), and the form reminds users not to paste personal details. Calls are made from the server; the browser never sees the key.
- **Files and PRs:** `meds/ai.py` (`parse_label`, `clean_label_fields`, `call_openrouter`, `LABEL_SCHEMA`), `meds/views.py` (`medication_fill`), `templates/meds/medication_form.html`. PR #17, #36 (prompt rules for route and units).
- **See it working:** log in as the member account → *Add medication* → paste `Metformin 500 mg tablet. Take 1 tablet by mouth twice daily with meals.` → *Fill in the form*.
- **How we chose the model:** the free tier on OpenRouter, so it costs nothing (the whole account gets 50 free requests a day, which is why we also have item 3). We tried three free models on the same real-style labels. One returned "2 mg" for a nasal spray; we picked `nvidia/nemotron-3.5-super-vl:free`, which leaves a field empty when unsure. The model is an environment variable (`OPENROUTER_MODEL`), so we can switch without a code change.

### 3. AI: per-user daily usage limit

- **What:** each AI call is stored as an `AIRequest` row (user, feature, succeeded, time). A user gets `AI_DAILY_LIMIT` calls per day (environment variable, default 20, counted from local midnight, America/New_York). The page shows how many are left and disables the button at zero; the server refuses extra calls even if the button is bypassed. Admins can see all AI requests in `/admin/`.
- **Why:** an AI key has a fixed budget; one user (or a script) should not be able to spend it for everyone.
- **Files and PRs:** `meds/models.py` (`AIRequest.used_today`), `meds/views.py`, `meds/migrations/0002_airequest.py`, `config/settings.py` (`AI_DAILY_LIMIT`). PR #17.
- **See it working:** the "N AI fills left today" line under the AI box goes down after each fill.

## Testing strategy

| Level | What we test | Where |
|---|---|---|
| Unit | AI output cleaning (valid values kept, invalid values dropped, odd types, whole-number doses shown as plain digits), prompt and schema sent to OpenRouter, JSON parsing, A/B preferred-variant rule, medication rules (dose > 0, end date not before start date), current vs. past medications (stopped, or end date passed) | `meds/tests.py`, `abtest/tests.py` |
| View / integration (Django test client + real Postgres) | Every page and form: login required, a user only sees their own medications and gets a 404 when editing, stopping, restarting or deleting someone else's, changes only on POST, stop and restart keep the planned end date, validation errors shown, AI fill pre-fills but saves nothing, daily limit (including per user), signup and login with email (stored lower case, duplicate emails rejected in any capitalization, seeded accounts still log in), 404 and 500 pages, seed command is safe to run twice, A/B impressions and clicks counted once per visitor, `/stats` JSON, `/healthz` with the database up and down | `accounts/tests.py`, `meds/tests.py`, `abtest/tests.py`, `config/tests.py` |
| Static | ruff lint; `manage.py check`; no missing migrations | CI |
| Manual | After each merge, the reviewer tries the new story on staging (desktop and phone); before a production deploy we repeat the main flows on staging, then check production | PR checklists |

**What we mock:** every call to OpenRouter (`requests.post` or `call_openrouter`), so tests never use the network, never spend credits and give the same result every run. We mock a database failure only in the `/healthz` test. The database itself is not mocked: tests run against Postgres in CI, the same database we use in production.

**What we don't test automatically, and why:**
- The real model's answers: they change between runs and models, and the course rules say tests must not call the real LLM. We check a few real labels by hand when we change the prompt or model, and the code-side validation limits what a bad answer can do.
- Layout on phones and real-browser behavior: checked by hand on staging. End-to-end browser tests are a possible later item.
- Render and Neon configuration: checked by `/healthz` and by trying the deployed app after each deploy.
