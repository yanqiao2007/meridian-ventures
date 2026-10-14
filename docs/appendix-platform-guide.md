# Appendix: Meridian Ventures Platform and Game Guide

*Step-by-step operating guide for the Round 1 prototype*

---

## 0. Scope and Evidence Basis

This guide describes only what exists in the repository at commit `4da6f12` ("README for faculty review"). Where the README, the build log and the code disagree, the code is treated as authoritative and the disagreement is flagged in Appendix A.

Three statements apply throughout:

- **The game has not been validated as a research instrument.** It is a digital adaptation of a paper pilot (`source/Meridian_Round1_Paper_Pilot_V1.pdf`). No study has been run on the platform.
- **Testing to date is limited to automated tests and one local manual QA pass by the researcher.** The automated suite has 26 tests (23 run without a browser; 3 are browser tests that need Playwright and Google Chrome and are skipped otherwise). The manual QA is recorded in `docs/build-log/session-01.md` and used four browser tabs on one machine in development mode. No external participants have used the platform, and no multi-device or internet-hosted test is documented.
- **Only Round 1 exists.** Rounds 2 and 3 are placeholders, and there is no between-round outcome engine (Section 12).

Code references used below: `app/config.py` (settings), `app/game.py` (session state machine), `app/rules.py` (board rules), `app/content.py` (content loading), `app/store.py` (SQLite storage and event schema), `app/main.py` (routes), `app/static/` (browser interfaces), `content/round_1.json` (all Round 1 numbers and text).

---

## 1. Overview

### 1.1 What Meridian Ventures is

Meridian Ventures is a browser-based team exercise. Four people act as the investment committee of a fictional venture fund. In Round 1 they share a board of twelve companies, a bank of 12 chips and three pools of staff counters, and they decide together where to place them. A 20-minute timer runs the round.

### 1.2 What it is designed to study

The project studies **shared leadership over time** (`CLAUDE.md`, `README.md`, `docs/prompts/00_kickoff.md`). The design intent is that the game creates a *need* for leadership behaviour without *assigning* it:

- All four members have equal authority; there is no chair.
- Each member leads a different staff unit and holds private information the others need.
- The software never designates a leader, sets a speaking order, gives any role sign-off, or scores roles separately. These are standing project rules (`CLAUDE.md`).

The intended full study has three rounds, including the removal of one member and the arrival of a successor. Only Round 1 is built; the replacement mechanic exists in the facilitator console but nothing follows it (Section 12).

### 1.3 The five interfaces

| Interface | URL | Who uses it | File |
|---|---|---|---|
| Facilitator console | `/facilitator` | One facilitator (password-protected) | `app/static/facilitator.html`, `facilitator.js` |
| Join page | `/` | Each participant, to enter a session code | `app/static/index.html` |
| Participant seat (×4) | `/play?code=XXXXX` | One per committee member; reached automatically after joining | `app/static/play.html`, `play.js` |

Strictly, there are five *screens in use during a session*: one facilitator console and four participant seats. Each participant seat is the same page (`/play`); what differs is the role the server assigned and the private information it sends.

### 1.4 Implemented versus not implemented

**Implemented (Round 1 only)**

- Facilitator console: create a session, see seats and the live board, start the round, freeze the board, replace a participant, export two CSV files.
- Participant flow: join with a 5-character code, seeded random role assignment, private role page, shared live board with legend.
- Board rule enforcement (Section 7), a 3-minute quiet-reading phase, automatic freeze at 20:00, and unanimous early finish.
- Live synchronisation over WebSockets (`/ws/{code}`).
- Persistence in SQLite; sessions and the event log survive a server restart.
- A pseudonymous, timestamped event log and CSV export.
- `DEVELOPMENT_MODE` for one-laptop testing.

**Not implemented**

- Round 2 and Round 3 (`content/round_2.json` and `round_3.json` are placeholders).
- The between-round outcome engine (reveals, refunds, payments, companies leaving, profit outcomes, support load). Its parameters are undefined (`docs/open_questions.md`); no outcome math has been invented.
- AI-generated staff responses. `ANTHROPIC_API_KEY` in `.env.example` is a placeholder only; nothing in `app/` reads it.
- Advancing beyond Round 1. The "Advance to next round" button exists but always returns an error message.
- Production deployment. The code reads all settings from the environment and uses relative URLs, but nothing has been deployed or load-tested.

---

## 2. Before Running the Game

### 2.1 Prerequisites

- Python 3 with `venv` and `pip`. The README does not state a minimum version; this guide's commands were checked on Python 3.13.
- Git (to clone).
- A current desktop browser for each participant and the facilitator.
- Optional, tests only: `pip install playwright` and Google Chrome, for the browser-based tests.

### 2.2 Obtain the code

```bash
git clone <repository-url> meridian-ventures
cd meridian-ventures
```

Alternatively, download the repository as a ZIP from GitHub and unzip it. The git tags `v0.1-round1-playable` and `v0.2-round1-multiplayer-qa` mark the Round 1 milestones. To reproduce the QA-tested state, fetch the tags and check out the latter:

```bash
git fetch --tags
git checkout v0.2-round1-multiplayer-qa
```

The tag points to commit `537ec85`. The only later commit (`4da6f12`) changed `README.md` and `.gitignore`, not application code or content (`git diff 537ec85 4da6f12 --stat`).

### 2.3 Create and activate a virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
. .venv/bin/activate
```

Windows (PowerShell) — *not tested in this project; the repository documents macOS/Linux commands only*:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

`.venv/` is gitignored.

### 2.4 Install requirements

```bash
pip install -r requirements.txt
```

`requirements.txt` installs `fastapi`, `uvicorn[standard]`, `python-dotenv`, plus `pytest` and `httpx` (the last two are only needed to run tests).

### 2.5 Configuration (environment variables)

All settings are read in `app/config.py`. They can be supplied by the shell or by a `.env` file in the repository root (loaded by `python-dotenv`; real shell variables take precedence over `.env`).

| Variable | Default | Meaning |
|---|---|---|
| `FACILITATOR_PASSWORD` | random, printed at startup | Password for `/facilitator` and all facilitator API calls |
| `HOST` | `0.0.0.0` | Network interface the server binds to |
| `PORT` | `8000` | TCP port |
| `DATABASE_PATH` | `data/meridian.sqlite3` (under the repository root) | SQLite file holding sessions and events |
| `CONTENT_DIR` | `content` | Folder containing `round_N.json` |
| `ROUND_SECONDS` | `1200` | Total round length (20 min) |
| `READING_SECONDS` | `180` | Length of the quiet-reading phase at the start of the round (3 min) |
| `ALLOWED_ORIGINS` | empty (same-origin only) | Comma-separated origins permitted for cross-origin use |
| `DEVELOPMENT_MODE` | off | Enables test identities (Section 9). Accepts `1`, `true` or `yes`, case-insensitive |
| `ANTHROPIC_API_KEY` | placeholder | Reserved; **not used by any current code** |

To create a `.env`:

```bash
cp .env.example .env
```

Then **edit `FACILITATOR_PASSWORD` in `.env`**. The example file ships with the value `change-me`; copying it without editing leaves that well-known value as the live password (see Appendix A, item 3). `.env` is gitignored; never commit it.

Changing `ROUND_SECONDS` or `READING_SECONDS` alters the stimulus. The values in `.env.example` (1200 and 180) match the rules text shown to participants ("Round length 20 minutes: 3 minutes private reading…"); other values will make that text inaccurate.

### 2.6 How facilitator passwords work

- If `FACILITATOR_PASSWORD` is set (shell or `.env`), that value is the password.
- If it is unset or empty, the server generates a random one on each start and prints it in the terminal (`Facilitator password (no FACILITATOR_PASSWORD set): …`). It changes every time the server restarts.
- The password is checked on every facilitator request via the `X-Facilitator-Key` HTTP header, and for the facilitator WebSocket via a `key` query parameter.
- The facilitator's browser keeps the password in `sessionStorage` for that tab (cleared when the tab closes).
- The password is **not** the session code. The session code is a separate 5-character value that participants use to join (Section 4.3).
- Traffic is plain HTTP when run locally. Over a shared network, the password and all game traffic are unencrypted. Production use would require HTTPS (not yet configured or tested).

### 2.7 Privacy and data notes

These rules come from `CLAUDE.md` and the implementation:

- Participants are identified only by randomly generated pseudonymous IDs (e.g., `P3F9A1C`). No names, emails, IP addresses or accounts are collected by the application.
- Runtime data lives in `data/` (the SQLite file). `data/`, `*.sqlite3`, `*.db`, `.env` and `exports/` are gitignored.
- **Do not commit participant data to the repository, and do not paste it into any AI tool.** Use synthetic sessions only during development.
- The SQLite file also stores each seat's access token (a bearer credential). Treat the file as confidential.
- The participants' private role pages are plain text in `content/round_1.json` in the repository, so anyone with repository access can read all four.

---

## 3. Starting the Platform

### 3.1 Commands

From the repository root, with the virtual environment active:

```bash
python run.py
```

With a chosen password (shell variable, one run only):

```bash
FACILITATOR_PASSWORD='my-long-passphrase' python run.py
```

Development mode (testing only, Section 9):

```bash
DEVELOPMENT_MODE=true python run.py
```

### 3.2 What a successful start looks like

The terminal prints a banner, then Uvicorn's startup lines. With no password configured:

```text
  Facilitator password (no FACILITATOR_PASSWORD set): uQVk6VmMfDpK

  Open http://localhost:8000/facilitator   (players join at http://<this-machine-ip>:8000/)

INFO:     Started server process [454]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

If `DEVELOPMENT_MODE` is on, an extra line reads `DEVELOPMENT_MODE on: open /?dev_player=P1 .. P4 in four tabs (never enable in production).` The first line (password) is omitted when you set `FACILITATOR_PASSWORD` yourself. The process stays in the foreground; leave that terminal open.

A quick health check: `http://localhost:8000/healthz` returns `{"ok":true}`.

### 3.3 URLs

| Purpose | URL |
|---|---|
| Facilitator | `http://localhost:8000/facilitator` |
| Participants (join page) | `http://<host-address>:8000/` |

### 3.4 Who can reach `localhost`

`localhost` (and `127.0.0.1`) always means "this computer". The facilitator URL above works only in a browser on the machine running the server. Participants on other devices cannot use `localhost`.

By default the server binds to `0.0.0.0` (all network interfaces), so another device **on the same local network** can connect using the host machine's LAN IP address, e.g. `http://192.168.1.20:8000/`, provided no firewall blocks port 8000. Devices on other networks (including the internet) cannot reach it unless the app is deployed or deliberately exposed; no deployment has been performed. Network reachability across devices has not been tested in the documented QA.

---

## 4. Facilitator Setup

### 4.1 Log in

1. Open `http://localhost:8000/facilitator`.
2. Enter the facilitator password and press **Enter** (button) or the Return key.
3. A wrong password shows "Wrong password."

### 4.2 Create a session

**Logging in creates a new session automatically.** There is no "New session" button. When the page has no remembered session in that browser tab, a successful login calls `POST /api/sessions` and a fresh session appears.

Important consequences (from `facilitator.js`):

- The tab remembers its session code in `sessionStorage`. Refreshing the same tab returns to the same session.
- Closing the tab, or opening the console in a new tab or browser, creates a **different new session**. There is no console feature to list or resume earlier sessions.
- Keep the facilitator tab open for the duration of a session. If it is lost, the participants' session is still alive on the server, but the console has no way to re-attach to it (Appendix A, item 5).

### 4.3 Find the session code

The code appears at the top of the console under **Session → Code:**, in large type, next to the join address. It is 5 characters drawn from `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (the letters I and O and the digits 0 and 1 are excluded). Give this code to the four participants. It is not case-sensitive for participants.

### 4.4 What the console shows

- **Session panel:** the code, the join address (derived from the browser's location, so it shows `http://localhost:8000/` when you used `localhost`; substitute your LAN address for remote participants), the round number, and the status (`lobby`, `reading`, `open`, `frozen`; if frozen, the reason: `timer`, `facilitator` or `early_finish`).
- **Timer** (top right): counts down from 20:00 while running. Blank when not running.
- **Board:** the live shared board, showing only company names with the chips and counters currently placed. It does not show company descriptions.
- **Seats panel:** each of the four roles, with the participant's pseudonymous ID or "vacant".
- **Status panel:** chips remaining in the bank, and "Early-finish agreement: N of 4".

The console does **not** show participants' private pages, a connection indicator, the events log, or counter-pool totals.

### 4.5 Facilitator controls

| Control | Enabled when | What it does |
|---|---|---|
| **Start round** | Status is `lobby` and all four seats are filled | Starts the clock; the quiet-reading phase begins; logs `round_started` |
| **Freeze board** | Status is `running` | After a confirmation dialog, ends the round immediately (reason `facilitator`) and logs the final board |
| **Advance to next round** | Status is `frozen` | **Does nothing useful.** It shows an error message: advancing needs the between-rounds outcome engine, which is not built |
| **Export events CSV** | Always | Downloads `<CODE>_events.csv` |
| **Export final boards CSV** | Always | Downloads `<CODE>_final_boards.csv` |
| **Replace** (per seat) | Seat filled and round not running | After a confirmation dialog, vacates that seat (the old participant's ID is kept in the log as `player_removed`); a new participant who joins is assigned the vacant role |

The facilitator cannot place chips or counters, cannot edit the board, cannot pause or resume the clock, and cannot change the seed from the interface. (The seed can be supplied through the API as `POST /api/sessions?seed=N`; the console does not expose this.)

---

## 5. Participant Setup

### 5.1 Joining

1. Each participant opens the join page (`http://<host-address>:8000/`).
2. They type the 5-character session code and press **Join** (or Return).
3. The server assigns a seat and the browser opens `/play?code=XXXXX`.

Errors shown on the join page include "Session not found." (wrong code) and "This session is full." (four seats taken).

Joining is possible while the session is in the lobby, and also later if a seat has been vacated by the facilitator.

### 5.2 Role assignment

Roles are assigned by the server, not chosen by participants. Each join picks one of the still-vacant roles pseudo-randomly, using a generator seeded by the session's seed and the number of assignments so far (`app/game.py`, `Session.join`). Consequently:

- The same seed with the same join order yields the same role sequence (verified by `test_role_assignment_reproducible_by_seed`).
- The seed is stored per session and recorded in the event log (`session_created` and `round_started`).
- Nobody can choose a role, and the first person to join has no special status.

Each participant also receives a pseudonymous ID of the form `P` + six hexadecimal characters.

### 5.3 The four roles

| Role | Staff the role's private page describes | Private page content (summary) |
|---|---|---|
| **Sourcing** | Scouts (3 visits) | Knowledge of the five scouting companies, plus remarks about Fieldnote and Kestrel |
| **Diligence** | Research team (3 jobs) | Knowledge of Solvanta, Fieldnote, Nimbus Kitchens, Wayfarer Care, and a risk about Kestrel |
| **Portfolio Management** | Support team (3 counters) | Knowledge of the owned companies, Nimbus, Wayfarer, and two scouting companies |
| **Fund Management** | None ("no staff to send out this round") | The bank, the 3-chip obligation, and cash positions of owned companies |

The software treats all roles identically. The staff counters are **committee-wide pools**; any member can place any counter, regardless of whose unit it belongs to (Section 7.3). The role affects only which private page the participant sees.

### 5.4 Private information

- Each participant has one private page, delivered only to their own connection. It is unavailable in the lobby ("Available when the round starts") and becomes available once the facilitator starts the round.
- The page is hidden behind an **Open private page** button. Pressing it reveals the text and logs a `private_page_opened` event once per participant per round. The page then stays open for that browser session; reloading the page re-hides it, and a further press does not create another log entry.
- The page tells participants to share its contents "in your own words". The software provides no sharing mechanism; communication happens outside the platform (spoken discussion).
- Other participants' private pages are never sent to your browser. Content flagged as reveal data, engine notes and "coded facts" in `content/round_1.json` is also never sent to any participant (`RoundContent.public`, tested by `test_public_content_hides_reveals`).

### 5.5 What participants can and cannot see

**Can see:** the three-row board (company name, line of business, descriptive summary, and the numbers in Section 7.1); chips and counters currently placed; the bank; counters left in each pool; the timer; the phase label; their own role and ID; the early-finish agreement count; the rules legend, the partners' mandate and the profit-band table; their own private page.

**Cannot see:** other participants' private pages, other participants' IDs or roles, the event log, the reveal data and engine notes, or any outcome (none are computed).

### 5.6 The shared board

The board has three rows — **Owned**, **Pipeline**, **Scouting** — of company cards. Each card shows the company name, line of business, a one-line cost/profit description, a summary paragraph, the placed chips (gold circles labelled `$1M`) and counters (square tokens labelled by type: S = support, green; R = research, blue; S = scout, purple), and its controls:

- A **Put N chips** / **Remove N chips** button (owned and pipeline cards only).
- A counter type label with **−** and **+** buttons.

The right-hand side panel shows Bank & staff, Finish early, the participant's private page and the Legend. Any participant can use any control at any time the board is open. All changes appear on all screens in near real time.

---

## 6. Running Round 1: Chronological Walkthrough

**Before you begin:** the server is running (Section 3) and you have logged into the console, so a session code is showing (Section 4).

1. **Distribute the code.** Give the 5-character code and the join address to four participants.
2. **All four join.** Each participant opens the join page, enters the code and presses Join. The Seats panel on the console fills as they arrive. Participants see a waiting screen ("Waiting for facilitator"); the board is visible but all controls are disabled, and the private page reads "Available when the round starts".
3. **Facilitator starts the round.** **Start round** is enabled only when all four seats are filled. Pressing it starts the 20:00 clock for everyone and logs `round_started`.
4. **Quiet reading (3:00).** For the first `READING_SECONDS` (default 180), the status shows *Quiet reading*. Participants can open their private pages and read the board; **all board controls and the early-finish button are disabled**, and the server rejects any attempt to change the board ("The board opens after the quiet reading period."). The software does not enforce silence; "quiet" is an instruction to participants (the legend says "3 minutes private reading, then open discussion").
5. **Board opens automatically.** When the reading period ends, the status changes to *Board open* on all screens without any action. The timer, which started at 20:00, reads about 17:00 at this point.
6. **Discussion and shared decisions.** Participants discuss (verbally; the platform has no chat) and place or remove chips and counters on the shared board. Anyone can change anything; there is no approval step.
7. **Chip allocation.** On an owned or pipeline card, a participant presses **Put N chips**. Exactly the card's amount is placed; the button then reads **Remove N chips**. Rules are in Section 7.2. An illegal action produces a red message at the bottom of the screen and no change.
8. **Staff-counter allocation.** On any card, **+** adds one counter of the row's type and **−** removes one. Rules are in Section 7.3.
9. **Live synchronisation.** Every accepted change is sent to the server, saved and pushed to all four participants and the facilitator. The bank and the "counters left" display update everywhere. The same action from two people converges (the operations are idempotent "set" operations, so two people clicking "Put 2 chips" simultaneously yield 2 chips, not 4).
10. **Early finish (optional).** In the *Finish early* panel, each participant can press **I agree to finish** (and **Withdraw agreement** to retract). The panel shows "N of 4 agree"; the console shows the same count. When all four agree, the board freezes with reason `early_finish`. **Any accepted change to the board clears every vote**, so participants must re-agree after any change.
11. **Facilitator freeze (optional).** At any time while running, the facilitator can press **Freeze board** and confirm. The board freezes with reason `facilitator`. Note that this can be done during the reading phase too.
12. **Automatic end.** If neither of the above occurs, the server freezes the board when the clock reaches 0:00 (reason `timer`). The server checks the clock every 0.5 seconds, so the freeze may occur up to about half a second late.
13. **After the freeze.** All participants see "The board is frozen. Whatever is on it is the committee's decision." The board and early-finish controls are disabled. The server writes a `round_frozen` event and one `final_board` event per company plus one for the bank. The facilitator then exports the data (Section 8).
14. **Advancing.** Pressing **Advance to next round** only displays an error. The session ends at this point; Round 2 does not exist.

---

## 7. Round 1 Game Rules (as Implemented)

All numbers come from `content/round_1.json`. Rules are of two kinds, and it is important not to confuse them:

- **Enforced by the software** (the board will not allow the action): Sections 7.2–7.5.
- **Displayed to participants as text but not computed** (no code calculates consequences): Section 7.6.

### 7.1 Companies

**Owned companies** (these cost chips to fund; a card shows "Needs N chips · estimated profit $XM")

| Company | Line | Chips needed | Estimated profit |
|---|---|---|---|
| Brightloom | School scheduling software | 2 | $2M |
| Harbor & Pine | Refillable cleaning products | 2 | $2M |
| Kestrel Diagnostics | At-home blood-test kits | 3 | $2M |

**Pipeline companies** (a card shows "Asking $L–HM · invest now: H chips · profit unknown")

| Company | Line | Asking range | Chips to invest |
|---|---|---|---|
| Nimbus Kitchens | Online ordering for restaurants | $3–5M | 5 |
| Solvanta | Recycles electric-car batteries | $4–8M | 8 |
| Wayfarer Care | Books in-home help for older adults | $2–4M | 4 |
| Fieldnote | Voice notes app for farmers | $4–6M | 6 |

**Scouting companies** (a card shows "Price and profit unknown · no chips")

Quillmark (Invoicing for freelancers), Frostline (Sensors for cold shipments), Sprigly (Countertop herb kits), Tandem Tutors (Peer tutoring for college students), Murmur (App-based hearing tests).

Each company also carries a descriptive summary paragraph, shown to everyone.

### 7.2 Chip rules (enforced)

- One chip represents $1M (`currency.chip_value_usd_millions`). The committee starts with **12 chips** in the bank.
- **Owned companies:** funded with *exactly* the chips shown (2, 2 or 3) or none. There is no partial funding and no overfunding; the control is a single on/off toggle.
- **Pipeline companies:** invest only the *top of the asking range* (5, 8, 4 or 6 chips) or none.
- **Scouting companies:** no chips are allowed ("Scouting companies cannot take chips.").
- **Bank constraint:** a toggle on is rejected if the chips left in the bank are fewer than the cost ("Not enough chips in the bank (N left, M needed)."). Chips cannot be overspent. Removing chips returns them to the bank.
- The bank equals 12 minus all chips on the board. (Arithmetic from the table above: funding all three owned companies uses 7 chips.)

### 7.3 Staff-counter rules (enforced)

- There are three counter types, fixed by the row of the company:

| Row | Counter type | Pool size |
|---|---|---|
| Owned | Support | 3 |
| Pipeline | Research | 3 |
| Scouting | Scout | 3 |

- A counter can only go on a company in its own row (the type is not selectable; wrong placement is impossible).
- **At most 2 counters on any one company** (`staff.max_counters_per_company`). Exceeding this is rejected ("At most 2 counters on one company.").
- **Shared pool:** the three counters of each type are shared by the whole committee. Adding a counter when the pool is empty is rejected ("No support counters left.", etc.).
- Counters may be added and removed freely while the board is open; removing returns them to the pool.
- No role restriction: although the private pages are written from each role's point of view, the software lets any member place any counter. Fund Management has no staff described, but can still place counters.

### 7.4 Timing and board access (enforced)

- Total round length `ROUND_SECONDS` = 1200 s. The first `READING_SECONDS` = 180 s is the reading phase, during which the board is locked. The board is open from 3:00 elapsed (17:00 remaining) until freeze.
- The board is also locked before the round starts and after it freezes.
- A frozen board cannot be reopened.

### 7.5 Early finish (enforced)

Early finish succeeds only when all four seated participants have an active vote; any accepted board change clears all votes; votes can be withdrawn; votes are only accepted while the board is open.

### 7.6 Rules shown as text but *not* computed

The legend lists ten rules from `rules` in the JSON, and the private pages describe consequences. The software displays them but calculates nothing from them. Specifically, the following have **no implementation**:

- Whether support raises the chance an owned company realizes its estimated profit.
- An owned company with no chips and no support "leaving Meridian for good".
- Research counters revealing exact prices and profit bands; scout counters revealing price ranges and moving companies into the pipeline.
- Refunds when a company is both invested in and researched.
- The 3-chip payment owed next round. The only implemented effect is a **warning**, visible to everyone, when the bank falls below 3 ("Bank is below the 3 chips Meridian owes next round (missed payment)."). It never blocks any action, and no payment is processed.
- Profit outcomes, lost deals (e.g., Nimbus, Quillmark), co-investor effects, regulatory risk, or Wayfarer's recurring support need.
- Any score, rating, or judgement on "value created, resilience, and opportunities" (the partners' mandate is shown as text only).

The reveal data (`reveal_*` fields), `engine_notes_from_private_pages` and `coded_facts` in the JSON are loaded for future use but never sent to participants and never acted on.

---

## 8. Data Collection and Exports

### 8.1 What is stored

Two things are stored in the SQLite file (`app/store.py`): a **session snapshot** (code, seed, round, status, start time, board, seats and tokens, early-finish votes, which private pages were opened) and an **append-only event log**.

### 8.2 Events logged

| `event_type` | When | Key fields |
|---|---|---|
| `session_created` | Facilitator logs in with no session | `detail`: seed |
| `player_joined` | Participant joins | participant ID, role |
| `player_removed` | Facilitator uses Replace | participant ID, role; `detail`: role history kept |
| `round_started` | Start round | `detail`: reading seconds, round seconds, seed |
| `private_page_opened` | First press of "Open private page" per participant per round | participant ID, role |
| `board_change` | Any accepted chip or counter change | participant ID, role; `subject` = company ID; `field` = `chips`, `support_counters`, `research_counters` or `scout_counters`; `before`; `after` |
| `early_finish_vote` | A vote that changes (agree or withdraw) | participant ID, role; `after` = True/False |
| `round_frozen` | Any freeze | `subject` = `timer`, `facilitator` or `early_finish` |
| `final_board` | At freeze | One row per company (`after` = `chips|counters`; `detail` has row, chips, counters, counter type) and one for the bank (`subject` = `bank`) |

Rejected actions (illegal moves) are **not** logged. Actions that produce no change (e.g., pressing "Put chips" on an already funded company) are not logged either. Facilitator button presses other than start/freeze/replace are not logged. Each event carries a UTC timestamp (millisecond precision) and the round number.

### 8.3 Pseudonymous IDs

Participant IDs are random (`P` + 6 hex characters, e.g. `P3F9A1C`), created at join time. They are not linked to any real-world identity inside the platform. Linking an ID to a person (e.g., via a seating list) is outside the software and is the researcher's responsibility.

In development mode, the labels `P1`–`P4` are browser-side seat labels only and are **never sent to the server or logged** (Section 9).

### 8.4 What is NOT recorded

No keystrokes, mouse movement, scrolling, clicks beyond the actions above, or dwell time (`CLAUDE.md`, enforced by design). No names, emails, IP addresses, device information or audio/video. Spoken discussion is not captured by the platform at all; the event log therefore records *board actions*, not the conversation. The HTTP server's own terminal log (Uvicorn) prints request lines including client IP addresses and URLs; this is console output and is not saved by the application unless you redirect it.

### 8.5 Exporting

Both exports are available as buttons in the facilitator console, which downloads through the browser:

- **Export events CSV** → `<CODE>_events.csv` (all events for the session).
- **Export final boards CSV** → `<CODE>_final_boards.csv` (only `final_board` rows).

Export is possible at any time, including mid-round. Both files use the columns:

```text
session_code, seq, ts_utc, round, participant_id, role, event_type, subject, field, before, after, detail
```

`detail` is a JSON string. `before`/`after` are text. Note: `seq` is a per-session running number *within each export* (the final-boards file therefore renumbers from 1 and its `seq` does not match the same rows' `seq` in the events file).

Equivalent command-line retrieval (replace `ABCDE` and the password):

```bash
curl -H "X-Facilitator-Key: <password>" -o ABCDE_events.csv \
  http://localhost:8000/api/sessions/ABCDE/export/events.csv
```

### 8.6 Where runtime data lives, and why it must not be committed

By default everything is written to `data/meridian.sqlite3` in the repository folder (override with `DATABASE_PATH`). The folder is created on first start. It is gitignored along with `.env` and `exports/`, so a normal `git add .` skips them. Runtime data must never be committed because (a) it is research data about participants and belongs under your ethics/data-management procedures, not in a code repository that may be public, (b) it contains seat tokens that grant access to live sessions, and (c) the project rule is that no participant data enters the repository or any AI tool (`CLAUDE.md`). Save exports outside the repository, or into the gitignored `exports/` folder.

---

## 9. Researcher Testing Mode

### 9.1 What it is

`DEVELOPMENT_MODE` lets one researcher hold all four participant seats on a single computer. Ordinarily, a browser remembers one seat per session code, so opening the join page four times in one browser would return the same seat each time. In development mode, the seat is remembered per test identity.

### 9.2 How to use it

1. Start the server with development mode on:

   ```bash
   DEVELOPMENT_MODE=true python run.py
   ```

   or set `DEVELOPMENT_MODE=true` in `.env`.
2. Log into `/facilitator` in one tab and note the session code.
3. In the **same browser**, open four more tabs:

   ```text
   http://localhost:8000/?dev_player=P1
   http://localhost:8000/?dev_player=P2
   http://localhost:8000/?dev_player=P3
   http://localhost:8000/?dev_player=P4
   ```

4. In each tab, enter the session code and press Join. A "Development mode" box with a dropdown (P1–P4) also appears on the join page and is preselected from the URL. Each tab's top bar shows a `DEV P1`–`DEV P4` pill.
5. Proceed as in Section 6. Switch between tabs to act as each participant.

### 9.3 Behaviour to be aware of

- **`P1` does not mean Sourcing.** Role assignment is unchanged: still seeded random, still server-side. `P1`–`P4` only name the browser storage slot. Check each tab's role pill.
- Reloading a tab restores the same seat (the token is in that tab's storage slot).
- Outside development mode, the `dev_player` parameter is ignored (the page asks the server via `/api/config`), and a given browser keeps exactly one seat per session code.
- Test identities exist only in the browser. The server and event log see ordinary random IDs (`P` + hex).

### 9.4 Production warning

**`DEVELOPMENT_MODE` must never be enabled in a production study.** It defeats the one-device-one-seat assumption: one person could hold several seats and see every private page, which invalidates the information structure the game depends on. Sessions run in development mode should be treated as test data and excluded from any analysis. Before a study, confirm `http://<host>:8000/api/config` returns `{"development_mode":false}`.

---

## 10. Ending and Restarting

### 10.1 Stopping the server

Click the terminal running `python run.py` and press **Ctrl + C**. The Uvicorn log shows "Shutting down" … "Finished server process". Closing the terminal window also stops it.

### 10.2 Restarting

```bash
cd meridian-ventures
. .venv/bin/activate
python run.py
```

Use the same `DATABASE_PATH` (the default if you did not set one) and run from the same repository. If you did not set `FACILITATOR_PASSWORD`, a **new random password** is printed.

### 10.3 What persists across a restart

- All sessions: code, seed, status (lobby/running/frozen), start time, the board, seats and their tokens, early-finish votes, which private pages were opened.
- The full event log.
- Participants' browsers: the seat token is in each browser's `localStorage`, so reloading the join or play page restores the same seat. The browser's WebSocket reconnects automatically every ~1.5 seconds.

This is covered by an automated test (`test_sessions_survive_restart`) but not by the documented manual QA, and a restart *during a live multi-participant session* has not been rehearsed.

### 10.4 What does not persist

- The generated facilitator password (if unset).
- The facilitator tab's remembered password and session (browser `sessionStorage`): if the facilitator tab was closed, a fresh login creates a *new* session instead of reattaching.
- Open network connections and anything in flight when the server stopped.
- **The clock is wall-clock based.** The round's start time is stored, so time spent with the server down still counts against the 20 minutes. If the deadline passes while the server is down, the round freezes (reason `timer`) shortly after the server restarts. Treat a mid-round restart as a disruption to that session's data. (This follows from the code in `Session.remaining`/`tick`; it has not been separately tested.)

### 10.5 Saved code versus a live session

Git/GitHub holds only the **code and content**: `app/`, `content/`, `docs/`, tests. A running session lives in the server's memory and in `data/meridian.sqlite3`, neither of which is in Git. Consequently: pushing or pulling code does not move, back up or restore sessions; deleting `data/` deletes all sessions and logs; and starting the server on a different machine begins with an empty database. Back up `data/meridian.sqlite3` (outside the repository) and export the CSVs after every session. Changing `content/round_1.json` or the code while a session exists changes what the restarted server shows for that session, so do not edit them between sessions of the same study.

---

## 11. Troubleshooting

| Symptom | Cause and remedy |
|---|---|
| Browser says "localhost refused to connect" / "This site can't be reached" | The server is not running, or you used the wrong port. Check the terminal shows `Uvicorn running on http://0.0.0.0:8000`; if you set `PORT`, use that port. Restart with `python run.py`. |
| `address already in use` on startup (`[Errno 48]` on macOS, `[Errno 98]` on Linux; port 8000) | Another process (often an earlier server instance) holds the port. Stop the older one (Ctrl+C in its terminal), or start on another port: `PORT=8001 python run.py` and use `:8001` in all URLs. |
| "Wrong password." at the facilitator login | The password does not match `FACILITATOR_PASSWORD`. If you never set it, the password was printed in the terminal at the **most recent** start and changes at each restart. If you copied `.env.example` unedited, the password is `change-me`. A `.env` value containing `#` needs quotes. Shell variables override `.env`. |
| Participant is asked for a "session code" and the facilitator thinks that's the password | They are different: the **session code** (5 characters, shown on the console, used on the join page) versus the **facilitator password** (used only on `/facilitator`). Participants never need the password. |
| "Session not found." on joining | The code was mistyped (I/O/0/1 are never used), or the server was started with a different `DATABASE_PATH`/folder so that session does not exist. |
| "This session is full." | Four seats are taken. Outside development mode, a *second browser* or private window on the same device uses a second seat; ask the facilitator to **Replace** the surplus seat (only possible when the round is not running). |
| Page does not respond to code changes or looks outdated | The browser cached an old copy of the page or scripts. Do a hard refresh (Cmd+Shift+R on macOS, Ctrl+Shift+R on Windows/Linux). This was suspected in an earlier report of a "5-character password limit"; the facilitator password input has no length limit and only the session-code field is capped at 5 (`test_maxlength_only_on_session_code`). |
| Several tabs open the same participant outside development mode | Expected. The seat token is stored per session code in the browser's `localStorage`, so all tabs in that browser share one seat. For genuinely separate participants use separate devices (or separate browser profiles). To test alone, use development mode. |
| In development mode, a tab shows a different role than expected | Roles are random; `P1`–`P4` are not roles. See Section 9.3. |
| Dev tab keeps joining the "wrong" seat | Each of `P1`–`P4` has its own slot per session code. Use the matching `?dev_player=` URL, or the dropdown, consistently. |
| Participant sees "Your seat is no longer active" | The server closed their connection because the seat or session no longer exists. The browser discards its stored seat; return to the join page. Behaviour of an already-open page after the facilitator replaces its seat was not verified (Appendix A, item 9). |
| Start round is greyed out | Not all four seats are filled, or the round has already started. |
| Board buttons are greyed out | The round has not started, is in the quiet-reading phase, or is frozen. |
| Red message "Not enough chips in the bank" / "No … counters left" / "At most 2 counters" | The action violates a board rule (Section 7); nothing changed. |
| "Advance to next round" shows an error | Expected; not implemented (Section 12). |
| Other devices cannot open the join page | Participants cannot use `localhost`. Use the host's LAN IP, make sure all devices are on the same network, and allow port 8000 through the host firewall. |
| Facilitator console shows a session you did not intend | Logging in from a tab with no remembered session creates a new session each time. Close unneeded consoles; there is no delete function. |

---

## 12. Current Limitations

The following are **not implemented**:

- **Round 2** and **Round 3** (placeholders only).
- **The between-round outcome engine** (reveals, refunds, payment owed, companies leaving, lost deals, profit outcomes, support load, scoring). Its parameters have not been specified by the researcher (`docs/open_questions.md`).
- **AI-generated staff responses.** No code calls the Anthropic API.
- **Production deployment.** Nothing has been deployed; HTTPS, hosting, backups and multi-session load behaviour are untested.
- **Advancing beyond Round 1.** A session ends at its first freeze.

Additional limitations of the current prototype:

- No pause or resume; freeze is final.
- No console feature to list, resume or delete sessions; no seed field in the console.
- No in-app chat, voice or recording.
- The facilitator console is read-only with respect to the board and has no live log view.
- Participant replacement exists but cannot be followed by a second round.
- The game is not validated as a research instrument; testing is limited to automated tests and local manual QA by the researcher.

---

## 13. Suggested Appendix Formatting Notes

- Cite this appendix by section number (e.g., "Appendix X, Section 7.3") in the main text.
- Sections 6 and 7 are the portions most useful as stand-alone excerpts for readers who want to replicate the stimulus.
- The command blocks in Sections 2, 3, 9 and 10 can be reproduced verbatim.
- Cite the repository state (commit hash or tag) alongside the guide, since the guide describes a specific build.

---

## Appendix A. Documentation Discrepancies and Cautions

These are points where the README, build log or `.env.example` differ from, or do not fully reflect, the code.

1. **Test count.** README says "26 passing". In an environment without Playwright/Chrome, 23 pass and 3 browser tests are skipped (26 collected). The README figure is accurate only where Chrome is installed.
2. **Replace "between rounds".** README and kickoff say participants are replaced between rounds. The code permits Replace whenever the round is not running (lobby or frozen), not only after a freeze.
3. **`.env.example` password.** `cp .env.example .env` sets `FACILITATOR_PASSWORD=change-me`. The README describes the copy as optional and says a random password is generated if unset; that applies only if the variable is absent or empty.
4. **`.env.example` database path.** The example `DATABASE_PATH=data/meridian.sqlite3` is relative to the working directory, while the built-in default is relative to the repository root. They coincide only if the server is started from the repository root.
5. **Facilitator session handling.** README says the facilitator can "create a session", but the UI has no create button: a session is created as a side effect of logging in from a tab with no remembered session, and cannot be resumed from another tab.
6. **"Advance" button.** README lists it as unavailable; the button is visible and enabled when frozen but only returns an error.
7. **Build-log tag.** `docs/build-log/session-01.md` refers to the tag `v0.2-round1-multiplayer-qa`. It exists on the remote (`origin`) but not in a fresh clone's local tag list unless fetched (`git fetch --tags`).
8. **`ANTHROPIC_API_KEY`.** Present in `.env.example` but unused.
9. **Participant removal behaviour.** The documented QA did not exercise the Replace flow in a browser; the exact message a removed participant's open page shows was not verified for this guide. Automated test `test_replace_between_rounds_only_and_keeps_history` covers the server side only.

## Appendix B. Source Files Consulted

`README.md`, `CLAUDE.md`, `.env.example`, `.gitignore`, `requirements.txt`, `run.py`, `app/*.py`, `app/static/*`, `content/round_1.json` (and the Round 2/3 placeholders), `tests/*.py`, `docs/decisions.md`, `docs/open_questions.md`, `docs/metrics.csv`, `docs/build-log/session-01.md`, `docs/prompts/00_kickoff.md`.

The startup output in Section 3.2 was captured by running `python run.py` in a fresh virtual environment. The remaining behaviour was read from the code and cross-checked against the automated tests; the gameplay flow was not re-run in a browser for this guide.
