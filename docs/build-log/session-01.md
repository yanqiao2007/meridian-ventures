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

## Later prompts in session 01 (verbatim summaries of the researcher's bug reports and requests)
- Bug report: facilitator password and session-code inputs not accepting typing. Cause: `onkeydown` property handlers returned `false` for non-Enter keys, cancelling keystrokes. Fixed with `addEventListener`; regression test `tests/test_static.py`. (My first browser test used `fill()`, which bypasses key events, so it missed this.)
- Request: dev-only way to test four seats on one laptop. Implemented `DEVELOPMENT_MODE` and `?dev_player=P1..P4` (per-identity localStorage seat key); tests `tests/test_dev_mode.py`, including a four-tab real-Chrome test with dev on and off.
- Bug report: facilitator password "limited to 5 characters". Not reproducible: no `maxlength` on that input; only the session-code field has it (likely typed into the wrong page or a cached page). Added regression tests; no code change.
- Request: record the manual QA milestone, tag v0.2.

## Manual QA milestone (researcher, 2026-10-11)
The researcher personally verified: facilitator login and session creation; four dev identities P1–P4; all four roles fill; private role information loads; 3-minute quiet reading; automatic transition to Board Open; board controls unlock; legal chip/staff actions work; state syncs across tabs; facilitator sees live state.
Automated tests: 26 passing. Tagged `v0.2-round1-multiplayer-qa`.

## Human interventions (additions)
- Researcher reported three bugs found by hands-on testing (typing blocked, dev-testing need, password length), and performed the manual QA above.
- Researcher ran `/export` twice; the first run mangled the filename because the argument included extra text.
