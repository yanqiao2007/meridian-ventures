# Kickoff prompt: Meridian Ventures digital build

Attached: `Meridian_Round1_Paper_Pilot_V1.1_Short.pdf` (the tested paper version of Round 1) and `meridian_round1_content.json` (the same content as structured data). Treat the JSON as the source of truth for numbers and text; use the PDF to see layout and intent.

## What we're building

A simple web app that turns the attached paper game into a digital, three-round version for a lab experiment on **shared leadership over time**. Four participants form an investment committee at a fictional venture fund, Meridian Ventures. There is no chair: all four have equal authority, each leads a different staff unit, and each holds private information the others need. The research question is how leadership gets distributed and shifts across rounds. The game must create the *need* for leadership behavior without *assigning* it. Never add features that designate a leader, set a speaking order, give one role final sign-off, or score roles separately. The four succeed or fail together.

## Requirements

**Players and screens**
- Four players, each on their own device, plus a facilitator console. Players join a session with a code and are assigned a role (Sourcing, Diligence, Portfolio Management, Fund Management).
- Every player sees the same live shared board (companies, chips, counters, bank, timer) and the legend. Each player also sees only their own private page.
- Anyone can place, move or remove any chip or counter. Changes appear for everyone in real time.
- The facilitator console starts and ends rounds, shows the timer, freezes the board, and advances to the next round. It can also replace a participant in a role between rounds (the study removes one member after Round 2 and adds a successor), keeping the role's history.

**Round 1 rules** come exactly from the JSON (`rules`, `staff`, `currency`). Enforce them in the interface: exact funding amounts only, no partial or overfunding, pipeline investment only at the top of the range, no chips on scouting companies, counters only on their allowed row, at most 2 counters per company, can't spend chips you don't have.

**Between rounds (the outcome engine)**
- When a round freezes, an engine computes the next round's starting state:
  - reveals from research and scout counters
  - refunds
  - the 3-chip payment owed
  - owned companies that leave (no chips and no support)
  - lost time-sensitive deals
  - scouted companies moving into the pipeline
  - profit outcomes
  - new support load (Wayfarer)
- Rounds 2 and 3 are not designed yet. Build the engine so round content (new companies, events, private pages) loads from config files, and put Round 2 and 3 placeholders in that format.
- **Do not invent outcome math.** Where a rule is not specified (for example, how much support improves profit odds, or how profit realization is randomized), stop and ask me. Propose options, and put every parameter in one config file. Any randomness must use a seed stored per session, so a run can be reproduced.

**AI-generated staff responses**
- Between rounds, each staff unit "reports back" to its leader in short, realistic messages: scouts on scouted companies, researchers on researched ones, support staff on companies they helped. Generate the wording with the Anthropic API.
- The engine decides every fact and number. The model only writes prose around facts it is given and must never invent or change a number. Validate each response against the facts passed in, and fall back to a template message if validation fails.
- The stimulus must be comparable across teams:
  - pin an exact model ID and set temperature to 0
  - cache responses by a hash of (company, action, facts)
  - include a script that pre-generates the cache before data collection
  - add an offline mode that serves only cached or template text, so reviewers can run the app without a key
- Read the key from an environment variable: `ANTHROPIC_API_KEY=<REDACTED>` in a `.env` file that is gitignored, with a `.env.example` containing the placeholder. Never hard-code or log the key.
- Participants are told up front that staff messages are simulated.

**Research data**
- Log with timestamps:
  - every board change (who, what, before and after)
  - when each private page and staff message was first opened
  - round start, freeze and early-finish confirmations
  - the final board each round
  - every LLM prompt and response
- Do not log keystrokes, mouse movement or dwell time.
- Export to CSV per session, in tidy long format, for analysis in R.
- Participant data never goes into the repo or to any AI tool. Use pseudonymous IDs, keep data folders gitignored, and use only synthetic test sessions during development.

**Stack and repo**
- Python backend; use FastAPI with WebSockets and SQLite unless you have a strong reason otherwise, and say why.
- A plain, clean front end.
- Must run locally with one documented command.
- Write tests for the rules and the engine.
- The repo will be public, so reviewers must be able to clone it and run it.

## Documentation for the journal appendix (required from the first session)

This build is evidence for a methods paper on how researchers can build custom research games with Claude Code. Its full history must go straight into a technical appendix and the public GitHub repo. From this session on:

1. Create `CLAUDE.md` with these project rules, and save this prompt verbatim as `docs/prompts/00_kickoff.md`.
2. Keep `docs/build-log/session-NN.md` for every session, with:
   - date, start and end time, and goal
   - every prompt I typed, verbatim
   - what you did and which files changed
   - errors and how they were fixed
   - **every human intervention**: hand edits, overrides of your suggestions, decisions I made
   - open questions
3. Keep `docs/decisions.md` recording each design decision, who made it (researcher or Claude), and why.
4. Keep `docs/metrics.csv` with one row per session: minutes, number of prompts, number of human interventions, whether the build ran, and tests passing.
5. Commit after each completed task with a descriptive message. Tag milestones (for example `v0.1-round1-playable`).
6. At the end of each session, remind me to run `/export docs/transcripts/session-NN.txt` and commit the transcript.

## This session

Don't write app code yet. First:
1. set up the repo skeleton and documentation files listed above
2. propose the architecture, data model and file structure
3. list every rule or parameter that is ambiguous or missing, as numbered questions for me

Then wait for my answers. The first coding milestone after that is Round 1 fully playable by four browsers on one laptop, with the facilitator console, logging and the frozen-board export.
