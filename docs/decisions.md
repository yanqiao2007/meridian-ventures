# Design decisions
| # | Decision | By | Why |
|---|---|---|---|
| 1 | FastAPI + WebSockets + SQLite | Researcher (kickoff) | Specified; fits the scale of 4 players per session. |
| 2 | Build Round 1 multiplayer now, defer outcome engine and AI messages | Researcher (this session's prompt) | Milestone scope. |
| 3 | Idempotent "set" operations (fund/unfund exact amount, set counters 0–2) | Claude | Enforces "exact funding" and converges under concurrent clicks. |
| 4 | Counter type fixed by row | Claude | Paper rule; makes wrong-row placement impossible. |
| 5 | Board locked during reading period; early-finish votes reset on any board change | Claude | Matches paper run-sheet; assumption, see open question 8. |
| 6 | Random seeded role assignment; pseudonymous IDs; no names collected | Claude | Paper uses random seats; privacy rules. |
| 7 | Facilitator password via env (random printed if unset); settings via env; relative URLs | Claude | Deployment readiness. |
| 8 | Session state snapshotted to SQLite, events append-only long format | Claude | Restart-safe, R-friendly export. |
| 9 | Owed-3-chips only warns, never blocks | Claude | Paper allows missed payment. |
| 10 | `DEVELOPMENT_MODE` with `?dev_player=P1..P4`: seat stored per identity in browser storage; ignored unless the server reports dev mode | Researcher (need), Claude (design) | Lets one laptop hold four seats without touching production flow or role assignment. |
| 11 | Key handlers use `addEventListener`, never `on*` properties; enforced by a test | Claude | Handler returning `false` had cancelled all typing. |
| 12 | Session-code field limited to 5 characters; facilitator password unlimited; both tested | Researcher (requirement), Claude | Codes are 5 chars; passwords are arbitrary. |
| 13 | Round 1 multiplayer accepted after manual QA; Round 2, outcome engine and AI messages deferred pending answers to docs/open_questions.md | Researcher | Milestone scope. |
