# Meridian Ventures (Round 1 multiplayer)

    python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
    cp .env.example .env     # set FACILITATOR_PASSWORD (otherwise one is printed at startup)
    python run.py

Open `/facilitator` (creates a session and shows the code). Four players open `/` (on the same network use the host's IP) and enter the code. Roles are assigned at random (seeded). Start the round once all four seats are filled.
Tests: `python -m pytest`. Exports: facilitator console buttons (events CSV in long format, final boards CSV).

Deployment notes: single process (in-memory sockets, SQLite state at `DATABASE_PATH`); run behind HTTPS (wss is automatic). Use a persistent volume for the DB. Configure `PORT`, `HOST`, `ALLOWED_ORIGINS`, `FACILITATOR_PASSWORD`.
Not built yet: between-rounds outcome engine, AI staff messages (see `docs/open_questions.md`).
