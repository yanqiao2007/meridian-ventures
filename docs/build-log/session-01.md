# Session 01 (2026-10-11)
**Goal:** Round 1 multiplayer playable locally (overrode kickoff's "no code yet").

## Prompts (verbatim)
1. "Read these three files in this project first: 1. 00_kickoff_prompt.md 2. meridian_round1_content.json 3. Meridian_Round1_Paper_Pilot_V1.pdf — Actually create/edit the files, run the app, run the tests, fix errors, and keep going until Round 1 works locally. Do not just tell me what code I should write. Long-term requirement: this will eventually be deployed as a real multiplayer web application where a facilitator and four participants can connect from separate devices over the internet. Build the local version in a deployment-ready way and do not hard-code assumptions that only work on my laptop. Do not deploy yet; first finish the local Round 1 multiplayer milestone."

## Done
App in `app/`, UI in `app/static/`, content in `content/`, tests in `tests/`, docs. Input files moved to `source/`.
## Errors fixed
- Reading→open transition not pushed to clients (ticker only broadcast on freeze): now broadcasts on phase change.
- Errors triggered an extra state broadcast; now only on success.
- Export `seq` was global; now per session.
- No Node installed: Python-only stack, UI is plain ES modules.
## Verification
18 pytest tests pass; Playwright-driven Chrome run with 1 facilitator + 4 players confirmed sync, rule toasts, freeze, CSV export, no console errors.
## Human interventions
Scope override of the kickoff (build now instead of asking questions first). No hand edits.
## Open questions
See `docs/open_questions.md`. Reminder: run `/export docs/transcripts/session-01.txt` and commit it.
