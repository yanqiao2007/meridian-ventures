# Meridian Ventures: project rules

Research game on **shared leadership over time**. Four equal committee members, no chair.
- Never add features that designate a leader, set speaking order, give one role sign-off, or score roles separately.
- Content in `content/round_N.json` is the source of truth for numbers and text (`source/` holds the original kickoff, JSON and paper PDF).
- **Do not invent outcome math.** Ask the researcher; put every parameter in one config file; any randomness uses the per-session seed.
- Never hard-code the API key; `.env` is gitignored. Never log keystrokes, mouse movement or dwell time.
- No participant data in the repo or to any AI tool. Synthetic sessions only. `data/` is gitignored.
- Deployment-ready: all settings via env (`app/config.py`), URLs relative, WebSocket scheme from `location`.
- Documentation duties: `docs/build-log/session-NN.md` (verbatim prompts, files changed, errors, human interventions, open questions), `docs/decisions.md`, `docs/metrics.csv`; commit per task, tag milestones; remind the researcher to run `/export docs/transcripts/session-NN.txt`.
- Kickoff prompt saved verbatim at `docs/prompts/00_kickoff.md`.
