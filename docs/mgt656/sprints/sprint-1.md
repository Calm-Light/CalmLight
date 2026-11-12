# Sprint 1: Walking skeleton

## Sprint goal

Deploy a Django and PostgreSQL walking skeleton of MedTrack to staging with user accounts, seeded grader accounts, a public A/B page with live stats, and an initial team backlog.

## What shipped

- Deployed the Django skeleton with signup, login and logout, an idempotent grader-account seed command, a database health check, and automated tests that run against PostgreSQL ([issue #4](https://github.com/Calm-Light/CalmLight/issues/4), [PR #3](https://github.com/Calm-Light/CalmLight/pull/3)).
- Added success messages and field-specific errors so users can tell whether signup, login, or logout succeeded ([issue #5](https://github.com/Calm-Light/CalmLight/issues/5), [PR #6](https://github.com/Calm-Light/CalmLight/pull/6)).
- Added a public A/B page that keeps each visitor’s assigned button, records one impression and at most one click per visitor, and reports which button has the higher click rate ([issue #7](https://github.com/Calm-Light/CalmLight/issues/7), [PR #8](https://github.com/Calm-Light/CalmLight/pull/8)).
- Added all four members’ course nicknames and GitHub usernames to `team.yaml` ([issue #2](https://github.com/Calm-Light/CalmLight/issues/2), [PR #1](https://github.com/Calm-Light/CalmLight/pull/1)).

## What works on staging

We confirmed the following on [MedTrack staging](https://calm-light-staging.onrender.com):

- Signup, login, and logout work and show clear feedback. Entering a wrong password displays an error.
- Both grader accounts can log in. The admin account sees the **Admin** link; the member account does not.
- The [public A/B page](https://calm-light-staging.onrender.com/d2480e0/) lists our four nicknames and shows exactly one button labeled `kudos` or `thanks`. Clicking it records a click, and the [stats endpoint](https://calm-light-staging.onrender.com/d2480e0/stats) updates live.
- The [health check](https://calm-light-staging.onrender.com/healthz) returns `OK`, confirming that the app can reach PostgreSQL.

## Working with our agents

The agent generated the account forms, feedback messages, and tests. On staging, we found that signup errors looked like ordinary password guidance, making it hard to tell why signup failed. We changed the form to highlight errors and show password guidance only when there is no error.

## Backlog changes for next sprint

We set up four sprint iterations in the team GitHub Project and added four user stories for Sprint 2: [email signup (#9)](https://github.com/Calm-Light/CalmLight/issues/9), [login and logout (#10)](https://github.com/Calm-Light/CalmLight/issues/10), [health profile (#11)](https://github.com/Calm-Light/CalmLight/issues/11), and [adding medications (#12)](https://github.com/Calm-Light/CalmLight/issues/12).
