# Sprint 1: Walking skeleton

## Sprint goal
Deploy a Django and PostgreSQL walking skeleton of MedTrack to staging, with user accounts, seeded grader accounts, a public A/B page and live stats, and an initial team backlog.

## What shipped
Django skeleton with signup, login/logout, environment-based settings, an idempotent seed command, health check, Bootstrap layout, Postgres CI tests, and Render deployment configuration (issue #4, PR #3).
Clear success and error messages for login, signup, and logout (issue #5, PR #6).
Public A/B page with persistent random assignment, one impression and at most one click per visitor, and live click-rate statistics (issue #7, PR #8).
Team member information in team.yaml (issue #2, PR #1).

## What works on staging
The team reports checking the skeleton and account feedback on staging, including invalid-password errors and login/logout messages. The A/B implementation has 36 reported passing tests and local checks of persistent assignment, duplicate-click prevention, and live stats. Its public page and stats endpoint are provided for staging verification; confirmation of those checks is pending.

## Working with our agents
The agent generated the account forms, feedback messages, and tests. During staging testing, the team found signup errors difficult to distinguish from password guidance. They changed the forms to highlight errors and show password guidance only when no error is present.

## Backlog changes for next sprint
