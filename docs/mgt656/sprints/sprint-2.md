# Sprint 2: Development

## Sprint goal

Ship the first MedTrack features to a separate production environment: users can add and manage their medications, and an AI feature fills the form from a prescription label.

## What shipped

- **Add a medication and see my list** ([issue #12](https://github.com/Calm-Light/CalmLight/issues/12), [PR #15](https://github.com/Calm-Light/CalmLight/pull/15)): form with validation (dose > 0, end date not before start date) and the "My medications" list.
- **Smart add with AI** ([issue #16](https://github.com/Calm-Light/CalmLight/issues/16), [PR #17](https://github.com/Calm-Light/CalmLight/pull/17)): paste label text, the server asks OpenRouter for structured JSON and pre-fills the form; the user checks and saves. Per-user daily limit on AI calls.
- **Lint in CI** ([issue #18](https://github.com/Calm-Light/CalmLight/issues/18), [PR #19](https://github.com/Calm-Light/CalmLight/pull/19)): ruff runs on every pull request next to the tests.
- **Edit, stop and delete medications** ([issue #20](https://github.com/Calm-Light/CalmLight/issues/20), [PR #34](https://github.com/Calm-Light/CalmLight/pull/34)): stopped medications move to "Past medications" and can be restarted.
- **Sign up with email** ([issue #9](https://github.com/Calm-Light/CalmLight/issues/9), [PR #35](https://github.com/Calm-Light/CalmLight/pull/35)): duplicate emails rejected; friendly 404 and 500 pages.
- **Smart add fixes** found while testing on staging: clearer route and unit rules in the prompt ([PR #36](https://github.com/Calm-Light/CalmLight/pull/36)), and no more 502 page when the AI answers slowly ([PR #38](https://github.com/Calm-Light/CalmLight/pull/38)).
- **Production** is live with its own Neon database at https://calm-light-production.onrender.com and deploys only by a manual step after staging is checked. `technical.md` and the README describe the setup ([PR #37](https://github.com/Calm-Light/CalmLight/pull/37)).

## What works on staging

At https://calm-light-staging.onrender.com: sign up / log in / log out; add a medication by hand or with AI fill; current and past medications; edit, stop, restart and delete; the A/B test page; `/healthz`. Penelope tested all of these on staging. One AI fill showed a 502 page instead of our error message, because a slow AI answer hit the server's 30-second limit; [PR #38](https://github.com/Calm-Light/CalmLight/pull/38) fixed it. After deploying `36932ab` to production, Penelope repeated the main flows there in Safari on a laptop and a phone, and everything worked.

## Working with our agents

The agent's AI fill passed all tests but showed a dose of 500 as "5E+2" in the form. Jennifer found it while reviewing [PR #17](https://github.com/Calm-Light/CalmLight/pull/17) on staging. The tests only compared numbers, not what the user sees, so we fixed the display and added a test that checks the page shows `value="500"`. Lesson: for anything the user reads, test the rendered page, not only the value.

## Backlog changes for next sprint

- Main goal for Sprint 3: the daily dose checklist. View today's schedule ([issue #24](https://github.com/Calm-Light/CalmLight/issues/24)), mark a dose as taken or missed ([issue #25](https://github.com/Calm-Light/CalmLight/issues/25)), see intake history ([issue #26](https://github.com/Calm-Light/CalmLight/issues/26)).
- Also planned: prevent duplicate medications ([issue #30](https://github.com/Calm-Light/CalmLight/issues/30)), reset password ([issue #31](https://github.com/Calm-Light/CalmLight/issues/31)).
- Closed: login/logout ([issue #10](https://github.com/Calm-Light/CalmLight/issues/10), done in Sprint 1), the medication list ([issue #23](https://github.com/Calm-Light/CalmLight/issues/23), shipped in PR #15), and a duplicate of smart add ([issue #22](https://github.com/Calm-Light/CalmLight/issues/22)).
- Later: reminders ([issue #27](https://github.com/Calm-Light/CalmLight/issues/27)), AI explainer ([issue #28](https://github.com/Calm-Light/CalmLight/issues/28)), weekly AI summary ([issue #29](https://github.com/Calm-Light/CalmLight/issues/29)), delete account ([issue #32](https://github.com/Calm-Light/CalmLight/issues/32)), export ([issue #33](https://github.com/Calm-Light/CalmLight/issues/33)), health profile ([issue #11](https://github.com/Calm-Light/CalmLight/issues/11)).
