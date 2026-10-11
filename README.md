# Meridian Ventures

A browser-based research game for studying **shared leadership and leadership succession in teams**.

## Research purpose
Four people form the investment committee of a fictional venture fund, Meridian Ventures. **There is no chair.** All four have equal authority, each leads a different staff unit (Sourcing, Diligence, Portfolio Management, Fund Management), and each holds private information the others need. The game creates a *need* for leadership behavior without *assigning* it, so researchers can observe how leadership is distributed and how it shifts over rounds, including when a member is removed and a successor joins. The four succeed or fail together; the software never designates a leader, sets a speaking order, gives anyone sign-off, or scores roles separately.

The game is a digital version of a tested paper pilot (`source/Meridian_Round1_Paper_Pilot_V1.pdf`). The study design is three rounds.

## Status (honest summary)
**A Round 1 multiplayer prototype works locally.** It has been checked by the researcher by hand and by automated tests (26 passing). **The study itself has not been run and nothing here has been validated as a research instrument.**

## Interfaces
Five browser interfaces: one **facilitator console** (`/facilitator`) and **four participant seats** (`/`), each on its own device.

## Implemented
- Facilitator console: create a session, see seats and live board, start the round, freeze the board, replace a participant between rounds (role history kept), export data.
- Participant seats: join with a 5-character session code, seeded random role assignment, private role page (first opening is logged), shared live board and legend.
- Round 1 rules enforced from `content/round_1.json`: exact funding only, pipeline investment only at the top of the range, no chips on scouting companies, counters only on their own row, at most 2 per company, a shared pool of 3 counters per type, no spending chips that aren't in the bank.
- Round timing: 3-minute quiet reading (board locked), open discussion, automatic freeze at 20:00, early finish only when all four agree (any board change resets the votes).
- Live sync over WebSockets; sessions survive a server restart.
- Research logging: timestamped, pseudonymous-ID event log (board changes with before/after, private-page first opens, round start/freeze/early-finish votes, final board). Export to long-format CSV for R. No keystrokes, mouse movement or dwell time are recorded.

## NOT implemented yet
- **Round 2 and Round 3** (only placeholder files in `content/`).
- **The between-rounds outcome engine** (reveals, refunds, payment owed, companies leaving, lost deals, profit outcomes, support load). Its parameters are undefined; see `docs/open_questions.md`. No outcome math has been invented.
- **AI-generated staff responses** (Anthropic API, cached/offline mode, validation). `ANTHROPIC_API_KEY` in `.env.example` is only a placeholder.
- Advancing from Round 1 to the next round (the button reports that it is unavailable).
- Production deployment (the code is built to be deployable, but nothing has been deployed).

## Tech stack
Python 3, FastAPI, WebSockets, SQLite, plain HTML/CSS/JavaScript (ES modules, no build step). Tests: pytest, plus Playwright with Chrome for a few browser tests (skipped if unavailable).

## Install and run locally
```
git clone <this repository> && cd meridian-ventures
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # optional; set FACILITATOR_PASSWORD
python run.py
```
Open `http://localhost:8000/facilitator`. If `FACILITATOR_PASSWORD` is unset, a random one is printed in the terminal. Players open `http://<host>:8000/` and enter the session code. Tests: `python -m pytest` (browser tests additionally need `pip install playwright` and Google Chrome).

## Testing all four seats on one laptop (development only)
Start with `DEVELOPMENT_MODE=true python run.py`. Then open four tabs of the same browser:
`/?dev_player=P1`, `/?dev_player=P2`, `/?dev_player=P3`, `/?dev_player=P4`, enter the session code in each. Each tab keeps its own seat; roles are still assigned by the normal seeded random logic. Outside development mode `dev_player` is ignored and a device keeps one seat per session. **Never enable it in a deployed environment.**

## Configuration
All via environment variables (see `.env.example`): `HOST`, `PORT`, `DATABASE_PATH`, `CONTENT_DIR`, `ROUND_SECONDS`, `READING_SECONDS`, `ALLOWED_ORIGINS`, `FACILITATOR_PASSWORD`, `DEVELOPMENT_MODE`. Run behind HTTPS in production (the WebSocket scheme follows automatically) and keep the database on a persistent volume.

## Data and privacy
Participants are identified only by pseudonymous IDs. `.env`, `data/` and exports are gitignored. Use synthetic test sessions only during development; participant data must never be committed.

## Where the documentation lives
- `docs/decisions.md`: each design decision, who made it, and why
- `docs/build-log/session-NN.md`: per-session build log (prompts, changes, errors, human interventions)
- `docs/metrics.csv`: per-session build metrics
- `docs/open_questions.md`: unresolved rules and parameters blocking later rounds
- `docs/prompts/00_kickoff.md`: the original project brief, verbatim
- `docs/transcripts/`: exported session transcripts
- `CLAUDE.md`: project rules for the AI coding assistant
- `source/`: the original brief, paper pilot PDF, and content JSON
