# Sprint 2: Development

## Sprint goal

Ship the first MedTrack features to a separate production environment: users can add and manage their medications, and an AI feature fills the form from a prescription label.

## What shipped

- **Add a medication and see my list** ([issue #12](https://github.com/Calm-Light/CalmLight/issues/12), [PR #15](https://github.com/Calm-Light/CalmLight/pull/15)): model, form with validation (dose > 0, end date not before start date), "My medications" list, demo data for the member account.
- **Smart add with AI** ([issue #16](https://github.com/Calm-Light/CalmLight/issues/16), [PR #17](https://github.com/Calm-Light/CalmLight/pull/17)): paste label text, the server asks OpenRouter for structured JSON and pre-fills the form; the user checks and saves. Per-user daily limit on AI calls.
- **Lint in CI** ([issue #18](https://github.com/Calm-Light/CalmLight/issues/18), [PR #19](https://github.com/Calm-Light/CalmLight/pull/19)): ruff runs on every pull request next to the tests.
- **Edit, stop and delete medications** ([issue #20](https://github.com/Calm-Light/CalmLight/issues/20), [PR #34](https://github.com/Calm-Light/CalmLight/pull/34)): stopped medications move to "Past medications" and can be restarted.
- **Sign up with email** ([issue #9](https://github.com/Calm-Light/CalmLight/issues/9), [PR #35](https://github.com/Calm-Light/CalmLight/pull/35)): email + password, duplicate emails rejected; friendly 404 and 500 pages.
- **Smart add fix** ([PR #36](https://github.com/Calm-Light/CalmLight/pull/36)): found while testing on staging. The AI left the route empty for "by mouth" and asked users to "fill in" a field that already showed a default. The prompt now explains routes and spray/drop units, and defaulted fields say "Please check".
- `technical.md`: first version, covering our three technical-challenge items and our testing strategy ([PR #37](https://github.com/Calm-Light/CalmLight/pull/37)). The README now describes both Render services, and the member demo account has one stopped medication so graders can see Past medications.
- **Smart add timeout fix** ([PR #38](https://github.com/Calm-Light/CalmLight/pull/38)): found while testing on staging. A slow AI answer no longer ends in a 502 page; AI call times are logged; clearer dose error.

## For graders

- Log in at https://calm-light-production.onrender.com/login (staging: https://calm-light-staging.onrender.com/login). The first load can take up to a minute while the free Render service wakes up.
- Accounts: `admin@example.com` (sees the Admin button) and `member@example.com`. Passwords are in the grader notes we submitted, not in the repo.
- The member account has three current demo medications and one stopped one (amoxicillin) under Past medications.
- AI fill: *Add medication* → paste label text, e.g. `Metformin 500 mg tablet. Take 1 tablet by mouth twice daily with meals.` → *Fill in the form*. It uses the course's OpenRouter key with the model `google/gemini-2.5-flash-lite`, and each user has a daily limit on AI fills; if it says "AI fill isn't available right now", the manual form still works.
- A/B test page: `/d2480e0/` and `/d2480e0/stats`.

## What works on staging

Staging: https://calm-light-staging.onrender.com

Penelope tested on staging on Nov 18 (steps 1–4 and 6 of our test plan): sign-up and login (including email in capital letters, duplicate email, wrong password), adding by hand with validation errors for dose 0 and end date before start date, AI fill (metformin and fluticasone filled correctly, nothing saved until Save, counter goes down), edit / stop / restart / delete, the 404 page, `/healthz` and the A/B page all worked.

What did not work: one AI fill returned a 502 error page instead of the "AI fill isn't available" message, and the failed call still counted toward the daily limit. Retrying worked. The cause: the app waited up to 30 seconds for the AI, and gunicorn also stops a request after 30 seconds by default, so a slow answer ended in Render's 502 page. Fixed in [PR #38](https://github.com/Calm-Light/CalmLight/pull/38) (merged Nov 18): gunicorn now gives each request 60 seconds, so a slow AI answer ends in our own "AI fill isn't available" message; each AI call's time is logged; and the dose error now says "Dose must be more than 0." (checked on staging after the merge). We kept counting failed calls toward the limit, because every call uses the shared AI key's budget. [TODO: after a few days of AI fills, check the Render logs for `WORKER TIMEOUT`.]

## Production deployment and testing

- Production URL: https://calm-light-production.onrender.com
- Separate production database: yes, its own Neon database (staging has another). Production deploys only by a manual step on Render, after staging is checked.
- Release deployed: `36932ab` (merge of [PR #38](https://github.com/Calm-Light/CalmLight/pull/38)), which includes every change merged from [PR #15](https://github.com/Calm-Light/CalmLight/pull/15) to [PR #38](https://github.com/Calm-Light/CalmLight/pull/38)

Final production checks (Penelope, Nov 18):
- Both grader accounts can log in: worked
- Add medication and My medications list, plus edit / stop / restart / delete: worked
- Sign up and log in: worked
- Laptop usability: worked (Safari)
- Phone usability: worked (Safari); buttons easy to tap, nothing cut off
- AI Smart Add: worked (course OpenRouter key, model `google/gemini-2.5-flash-lite`)
- Public A/B page and stats: worked
- A/B test rows cleared after testing: done

## Working with our agents

- **What worked:** we wrote acceptance criteria in each issue and gave them to the agent as the spec. It wrote the feature and the tests together, and the PR descriptions list what the agent produced and what we changed.
- **What didn't, and what we changed:** the agent's AI fill passed all tests but showed a dose of 500 as "5E+2" in the form. Jennifer found it while reviewing [PR #17](https://github.com/Calm-Light/CalmLight/pull/17) on staging. The tests only compared numbers, not what the user sees, so we fixed the display and added a test that checks the page shows `value="500"`. Lesson: for anything the user reads, test the rendered page, not only the value.

## Backlog changes for next sprint

- Closed login/logout ([issue #10](https://github.com/Calm-Light/CalmLight/issues/10)), which was already implemented in Sprint 1, and view my medication list ([issue #23](https://github.com/Calm-Light/CalmLight/issues/23)), which shipped with [PR #15](https://github.com/Calm-Light/CalmLight/pull/15).
- Consolidated AI Smart Add work under [issue #16](https://github.com/Calm-Light/CalmLight/issues/16); [issue #22](https://github.com/Calm-Light/CalmLight/issues/22) was closed as a duplicate.
- Main goal for Sprint 3: the daily dose checklist. View today's schedule ([issue #24](https://github.com/Calm-Light/CalmLight/issues/24)), mark a dose as taken or missed ([issue #25](https://github.com/Calm-Light/CalmLight/issues/25)), see intake history ([issue #26](https://github.com/Calm-Light/CalmLight/issues/26)).
- Also planned: prevent duplicate medications ([issue #30](https://github.com/Calm-Light/CalmLight/issues/30)), reset password ([issue #31](https://github.com/Calm-Light/CalmLight/issues/31)), and use the AI timings logged since [PR #38](https://github.com/Calm-Light/CalmLight/pull/38) to choose how long to wait for the AI (and add a hard overall deadline if `WORKER TIMEOUT` still shows up in the logs).
- Later: reminders ([issue #27](https://github.com/Calm-Light/CalmLight/issues/27)), AI explainer ([issue #28](https://github.com/Calm-Light/CalmLight/issues/28)), weekly AI summary ([issue #29](https://github.com/Calm-Light/CalmLight/issues/29)), delete account ([issue #32](https://github.com/Calm-Light/CalmLight/issues/32)), export ([issue #33](https://github.com/Calm-Light/CalmLight/issues/33)), health profile ([issue #11](https://github.com/Calm-Light/CalmLight/issues/11)).
